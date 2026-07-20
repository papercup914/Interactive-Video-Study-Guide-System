import os
import json
import asyncio
from google import genai
import openai
from typing import List, Any

def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "여기에_GEMINI_API_키를_입력하세요":
        raise ValueError("GEMINI_API_KEY 환경 변수가 설정되지 않았습니다.")
    return genai.Client(api_key=api_key)

def get_openai_client(provider: str = None):
    api_key = None
    if provider == "glm-5.2":
        api_key = os.getenv("GLM_API_KEY", api_key)
    elif provider == "nvidia/nemotron-3-ultra-550b-a55b":
        api_key = os.getenv("NEMOTRON_3_ULTRA_API_KEY")
    elif os.getenv("OPENAI_API_KEY") and os.getenv("OPENAI_API_KEY") != "여기에_OPENAI_API_키를_입력하세요":
        api_key = os.getenv("OPENAI_API_KEY")
    else:
        # 새로 추가된 NVIDIA 모델들을 위해 GLM_API_KEY나 NEMOTRON_3_ULTRA_API_KEY를 공용으로 사용
        nv_key = os.getenv("NEMOTRON_3_ULTRA_API_KEY") or os.getenv("GLM_API_KEY")
        if nv_key and nv_key.startswith("nvapi-"):
            api_key = nv_key
            
    if not api_key:
        raise ValueError(f"{provider if provider else 'OpenAI'} 모델을 위한 API_KEY 환경 변수가 설정되지 않았습니다. .env 파일을 확인해주세요.")
    
    # API 키가 NVIDIA 형식(nvapi-)인 경우 기본 Base URL 설정
    base_url = os.getenv("OPENAI_BASE_URL")
    if not base_url and api_key.startswith("nvapi-"):
        base_url = "https://integrate.api.nvidia.com/v1"
        
    return openai.Client(api_key=api_key, base_url=base_url)

def process_audio(audio_path: str, provider: str) -> str:
    """
    선택된 Provider에 맞게 오디오를 처리하여 텍스트 대본(Transcript)을 반환합니다.
    로컬에 이미 캐시된 대본이 있으면 API를 호출하지 않고 캐시를 반환합니다.
    """
    url_hash = os.path.splitext(os.path.basename(audio_path))[0]
    data_dir = "data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        
    cache_file = os.path.join(data_dir, f"{url_hash}_transcript.txt")
    if os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            return f.read()

    transcript = ""
    # OpenAI 계열 (Whisper) 우선 시도
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key and openai_key != "여기에_OPENAI_API_키를_입력하세요" and provider != "Google Gemini":
        client = get_openai_client("OpenAI (GPT-4o)")
        with open(audio_path, "rb") as audio_file:
            transcript_response = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file, 
                response_format="text"
            )
        transcript = transcript_response
    else:
        # Gemini 멀티모달 오디오 분석
        client = get_gemini_client()
        uploaded_file = client.files.upload(file=audio_path)
        response = client.models.generate_content(
            model=os.getenv("SELECTED_GEMINI_VERSION", "gemini-3.1-flash-lite"),
            contents=[uploaded_file, "Please provide a complete and highly accurate transcription of this audio in its original language. Do not summarize, format, or skip any parts. Return ONLY the transcribed text."]
        )
        transcript = response.text

    with open(cache_file, "w", encoding="utf-8") as f:
        f.write(transcript)
        
    return transcript

def generate_outline(context_data: str, provider: str, url_hash: str, length_preset: str = "아주 상세하게") -> List[str]:
    """
    오디오 컨텍스트를 분석하여 상세 목차를 생성하고 로컬에 캐시합니다.
    """
    preset_suffix = "summary" if length_preset == "핵심 요약" else ("normal" if length_preset == "적당한 설명" else "detailed")
    cache_file = os.path.join("data", f"{url_hash}_outline_{preset_suffix}.json")
    if os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)

    if length_preset == "핵심 요약":
        outline_instruction = "전체 내용을 단 3~5개의 핵심 챕터로 굵직하게 요약해서 묶어줘."
    elif length_preset == "적당한 설명":
        outline_instruction = "전체 내용을 7~10개 내외의 적절한 분량의 챕터로 나누어줘."
    else:
        outline_instruction = "전체 내용을 생략 없이 방대한 분량의 학습 문서로 만들 수 있도록 챕터별로 아주 잘게 쪼개야 해."

    prompt = f"""
    주어진 내용(오디오 또는 스크립트)을 분석하여 학습용 목차(Outline)를 작성해줘.
    {outline_instruction}
    각 목차 항목은 번호나 기호 없이 새로운 줄에 제목만 하나씩 작성해줘. (예: 데이터베이스의 이해)
    """
    
    if provider == "Google Gemini":
        client = get_gemini_client()
        response = client.models.generate_content(
            model=os.getenv("SELECTED_GEMINI_VERSION", "gemini-3.1-flash-lite"),
            contents=[context_data, prompt]
        )
        outline_raw = response.text
    else:
        target_model = "gpt-4o" if provider == "OpenAI (GPT-4o)" else provider
        client = get_openai_client(provider)
        response = client.chat.completions.create(
            model=target_model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"다음은 영상 스크립트 내용입니다:\n\n{context_data}"}
            ]
        )
        outline_raw = response.choices[0].message.content
        
    sections = []
    for line in outline_raw.split("\n"):
        clean_line = line.strip().lstrip('1234567890.-*# ')
        if clean_line:
            sections.append(clean_line)
            
    if not sections:
        sections = ["전체 내용 요약"]
        
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(sections, f, ensure_ascii=False)
        
    return sections

async def async_generate_chapter_content(section_title: str, context_data: str, provider: str, chunk_index: int, total_chunks: int, length_preset: str = "아주 상세하게", analogy_preset: str = "풍부한 비유") -> str:
    """
    전체 스크립트를 n등분하여, 현재 챕터에 해당하는 특정 청크(Chunk)만 LLM에 전달하는 토큰 다이어트 비동기 함수.
    """
    # 텍스트 청킹(Chunking) 로직 (문장 또는 띄어쓰기 단위 분할을 단순화하여 길이 비례로 분할)
    chunk_length = len(context_data) // total_chunks
    start_idx = chunk_index * chunk_length
    end_idx = start_idx + chunk_length if chunk_index < total_chunks - 1 else len(context_data)
    
    # 문장 중간에서 잘리지 않도록 약간의 오버랩(전후 문맥) 추가
    safe_start = max(0, start_idx - 500)
    safe_end = min(len(context_data), end_idx + 500)
    chunked_context = context_data[safe_start:safe_end]
    
    if length_preset == "핵심 요약":
        length_instruction = "전체적인 흐름만 파악할 수 있도록 3~5문장 내외로 아주 간결하게 핵심만 요약해라."
    elif length_preset == "적당한 설명":
        length_instruction = "너무 길지 않게, 핵심 내용을 포함하여 적절한 분량으로 설명해라."
    else:
        length_instruction = "절대 내용을 요약하지 말고 최대한 친절하고 길게 풀어서 작성해라."

    if analogy_preset == "비유 없이 담백하게":
        analogy_instruction = "비유를 배제하고 전문 용어를 살려 담백하고 객관적으로 설명해라."
    elif analogy_preset == "적절한 비유 추가":
        analogy_instruction = "이해하기 어려운 개념이 나올 때만 가벼운 비유를 하나 정도 추가해라."
    else:
        analogy_instruction = "어려운 기술 용어나 복잡한 개념이 등장할 때마다 일상적인 비유(요리, 식당, 교통 등)를 먼저 제시해라."

    system_prompt = f"""
    당신은 영상 내용을 기반으로 친절하고 전문적인 학습 가이드를 작성하는 튜터입니다.
    영상 내용 중 다음 챕터 제목에 해당하는 내용을 바탕으로 챕터 본문을 작성해줘.
    
    챕터 제목: {section_title}
    
    프롬프트 가이드라인:
    - {analogy_instruction}
    - 개념 돋보기 박스(Markdown 인용구 > 문법 사용)를 만들어 핵심을 짚어줘라.
    - {length_instruction}
    """
    
    # 비동기 실행을 위해 이벤트 루프의 run_in_executor 활용
    loop = asyncio.get_event_loop()
    
    def _call_api():
        if provider == "Google Gemini":
            client = get_gemini_client()
            response = client.models.generate_content(
                model=os.getenv("SELECTED_GEMINI_VERSION", "gemini-3.1-flash-lite"),
                contents=[chunked_context, system_prompt]
            )
            return response.text
        else:
            target_model = "gpt-4o" if provider == "OpenAI (GPT-4o)" else provider
            client = get_openai_client(provider)
            response = client.chat.completions.create(
                model=target_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"다음은 분석할 원본 영상 스크립트 특정 구간(Chunk)입니다:\n\n{chunked_context}"}
                ]
            )
            return response.choices[0].message.content

    return await loop.run_in_executor(None, _call_api)

def generate_answer(context: str, question: str, provider: str) -> str:
    """
    본문 컨텍스트를 바탕으로 사용자의 질문에 대한 답변을 생성합니다.
    """
    prompt = f"""
    현재 학습 중인 문서의 내용:
    {context}
    
    사용자의 질문:
    {question}
    
    위 문서 내용을 바탕으로 사용자의 질문에 매우 쉽고 친절하게 답변해줘. 
    이해를 돕기 위해 새로운 일상적 비유를 하나 들어서 설명하면 더욱 좋아.
    """
    
    if provider == "Google Gemini":
        client = get_gemini_client()
        response = client.models.generate_content(
            model=os.getenv("SELECTED_GEMINI_VERSION", "gemini-3.1-flash-lite"),
            contents=[prompt]
        )
        return response.text
    else:
        target_model = "gpt-4o" if provider == "OpenAI (GPT-4o)" else provider
        client = get_openai_client(provider)
        response = client.chat.completions.create(
            model=target_model,
            messages=[
                {"role": "system", "content": "당신은 본문 내용을 바탕으로 독자의 질문에 친절하게 답변하는 AI 튜터입니다."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
