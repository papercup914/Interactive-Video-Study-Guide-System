import os
import json
import asyncio
import time
import math
from pydub import AudioSegment
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

def _split_audio_if_needed(audio_path: str, max_size_mb: int = 20) -> List[str]:
    """오디오 파일이 max_size_mb를 초과하면 분할하여 임시 파일 경로 목록을 반환합니다."""
    file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
    if file_size_mb <= max_size_mb:
        return [audio_path]
        
    print(f"오디오 크기가 {file_size_mb:.2f}MB로 제한({max_size_mb}MB)을 초과하여 분할합니다.")
    audio = AudioSegment.from_file(audio_path)
    
    # 20MB 제한을 위해 파일 용량 비율로 길이를 나눔
    num_chunks = math.ceil(file_size_mb / max_size_mb)
    chunk_length_ms = len(audio) // num_chunks
    
    chunk_paths = []
    base_name = os.path.splitext(audio_path)[0]
    
    for i in range(num_chunks):
        start_ms = i * chunk_length_ms
        # 마지막 청크는 끝까지
        end_ms = (i + 1) * chunk_length_ms if i < num_chunks - 1 else len(audio)
        
        chunk = audio[start_ms:end_ms]
        chunk_path = f"{base_name}_part{i}.mp3"
        chunk.export(chunk_path, format="mp3")
        chunk_paths.append(chunk_path)
        
    return chunk_paths

def process_audio(audio_path: str, provider: str) -> str:
    """
    선택된 Provider에 맞게 오디오를 처리하여 텍스트 대본(Transcript)을 반환합니다.
    로컬에 이미 캐시된 대본이 있으면 API를 호출하지 않고 캐시를 반환합니다.
    """
    url_hash = os.path.splitext(os.path.basename(audio_path))[0]
    data_dir = "backend/data"
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
        
        chunk_paths = _split_audio_if_needed(audio_path, max_size_mb=20)
        
        for chunk_path in chunk_paths:
            with open(chunk_path, "rb") as audio_file:
                transcript_response = client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file, 
                    response_format="text"
                )
            transcript += transcript_response + " "
            
            # 분할 생성된 임시 파일 삭제 (원본은 유지)
            if chunk_path != audio_path:
                try:
                    os.remove(chunk_path)
                except:
                    pass
    else:
        # Gemini 멀티모달 오디오 분석
        client = get_gemini_client()
        uploaded_file = client.files.upload(file=audio_path)
        
        # ACTIVE 상태가 될 때까지 폴링 대기
        while uploaded_file.state.name == "PROCESSING":
            print(f"Gemini 오디오 처리 중 대기... (상태: {uploaded_file.state.name})")
            time.sleep(3)
            uploaded_file = client.files.get(name=uploaded_file.name)
            
        if uploaded_file.state.name == "FAILED":
            raise Exception("Gemini 파일 업로드 처리 실패")
            
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
    cache_file = os.path.join("backend/data", f"{url_hash}_outline_{preset_suffix}.json")
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

async def async_generate_chapter_content(section_title: str, context_data: str, provider: str, chunk_index: int, total_chunks: int, length_preset: str = "아주 상세하게", analogy_preset: str = "풍부한 비유", learner_profile: str = "", url_hash: str = "") -> str:
    """
    전체 스크립트를 LLM에 전달하여 챕터 내용에 해당하는 부분을 스스로 찾아서 작성하도록 합니다. (정확도 우선)
    """
    import hashlib
    
    # 캐시 키 생성 (모든 조건이 동일할 때만 캐시 히트)
    cache_key_raw = f"{url_hash}_{section_title}_{provider}_{length_preset}_{analogy_preset}_{learner_profile}"
    cache_hash = hashlib.md5(cache_key_raw.encode('utf-8')).hexdigest()
    cache_dir = "backend/data/cache_chapters"
    os.makedirs(cache_dir, exist_ok=True)
    cache_file = os.path.join(cache_dir, f"{cache_hash}.txt")
    
    if os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            return f.read()

    chunked_context = context_data
    
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
    당신은 영상 내용을 기반으로 학습 가이드를 작성하는 튜터입니다.
    제공된 [전체 스크립트]를 문맥적으로 분석하여, 다음 챕터 제목(또는 주제)에 해당하는 내용을 찾아 챕터 본문을 작성해줘.
    챕터 제목은 스크립트의 특정 부분을 요약한 것이므로, 정확히 같은 단어가 없더라도 의미상 관련된 내용을 찾아야 해.
    단, 전체 스크립트를 아무리 살펴봐도 해당 주제와 관련된 내용이 아예 존재하지 않을 때만 예외적으로 "해당 내용을 영상에서 찾을 수 없습니다."라고 출력해.
    
    챕터 제목: {section_title}
    
    <PERSONA_DIRECTIVE>
    당신은 무미건조한 AI가 아닙니다. 아래의 [학습자 프로필]에 100% 빙의하여 맞춤형 튜터로 행동하십시오.
    
    [학습자 프로필]
    {learner_profile if learner_profile else "일반적인 성인 학습자"}
    
    1. 어조 강제: 학습자 프로필에 명시된 '원하는 튜터 어조'를 본문 전체에 걸쳐 철저하게 유지하십시오.
    2. 비유 강제: 어려운 개념을 설명할 때는 반드시 프로필에 명시된 '주요 관심사'와 관련된 메타포(비유)를 하나 이상 들어 설명하십시오. 
    3. 눈높이 강제: '학습 목표'와 '연령대/직업'에 맞추어 전문 용어의 사용 수준과 설명의 깊이를 조절하십시오.
    </PERSONA_DIRECTIVE>
    
    프롬프트 가이드라인:
    - {analogy_instruction}
    - 개념 돋보기 박스(Markdown 인용구 > 문법 사용)를 만들어 핵심을 짚어줘라.
    - {length_instruction}
    - [중요] 챕터 본문 작성이 끝난 후, 가장 마지막에 학습자의 이해도를 점검할 수 있는 객관식 퀴즈 1~2개와 심화 학습을 위한 서술형 토론 주제 1개를 출제하세요.
      퀴즈는 반드시 아래와 같이 JSON 배열을 `<quiz></quiz>` 태그로 감싸는 정확한 형식으로만 출력해야 합니다 (모든 오답에 대한 개별 해설 포함 필수):
      <quiz>
      [
        {{
          "question": "첫 번째 객관식 퀴즈 질문",
          "options": ["보기1", "보기2", "보기3", "보기4"],
          "answerIndex": 0,
          "feedback": [
            "보기1(정답)에 대한 튜터 어조의 상세한 해설",
            "보기2(오답)가 틀린 이유에 대한 친절한 해설",
            "보기3(오답)가 틀린 이유 해설",
            "보기4(오답)가 틀린 이유 해설"
          ]
        }}
      ]
      </quiz>
      <discussion topic="여기에 심화 학습을 유도하는 서술형 토론 주제를 하나 작성" />
    """
    
    loop = asyncio.get_event_loop()
    
    def _call_api():
        max_retries = 5
        base_delay = 5
        
        for attempt in range(max_retries):
            try:
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
                            {"role": "user", "content": f"다음은 분석할 원본 영상 전체 스크립트입니다:\n\n{chunked_context}"}
                        ]
                    )
                    return response.choices[0].message.content
            except Exception as e:
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    import time
                    print(f"API Error ({e}). Retrying in {delay} seconds... (Attempt {attempt+1}/{max_retries})")
                    time.sleep(delay)
                else:
                    print(f"API Error ({e}). Max retries reached.")
                    raise e

    result = await loop.run_in_executor(None, _call_api)
    
    with open(cache_file, "w", encoding="utf-8") as f:
        f.write(result)
        
    return result

def generate_answer(selected_text: str, context: str, question: str, provider: str, learner_profile: str = "") -> str:
    """
    본문 컨텍스트를 바탕으로 사용자가 선택한 특정 텍스트에 대한 질문에 답변을 생성합니다.
    """
    prompt = f"""
    당신은 학습자의 질문에 답하는 1:1 맞춤형 AI 튜터입니다.
    사용자가 문서 학습 중 특정 단어나 문장을 선택하여 질문을 남겼습니다.
    
    [전체 문맥 (배경 지식 참고용)]: 
    {context}
    
    [사용자가 선택한 텍스트 (집중 분석 대상)]: 
    "{selected_text}"
    
    [사용자의 질문]: 
    {question}
    
    <PERSONA_DIRECTIVE>
    당신은 무미건조한 AI가 아닙니다. 아래의 [학습자 프로필]에 100% 빙의하여 답변하십시오.
    
    [학습자 프로필]
    {learner_profile if learner_profile else "일반적인 성인 학습자"}
    
    1. 어조 강제: 명시된 '원하는 튜터 어조'를 철저하게 유지하십시오.
    2. 비유 강제: 이해를 돕기 위해 반드시 프로필의 '주요 관심사'에 빗대어 찰떡같은 비유를 하나 들어주세요.
    3. 눈높이 강제: '학습 목표'와 '연령대/직업'에 맞추어 어휘를 선택하십시오.
    </PERSONA_DIRECTIVE>
    
    지시사항:
    1. 전체 문맥을 요약하지 마세요. 사용자의 질문은 오직 **[사용자가 선택한 텍스트]**에 관한 것입니다.
    2. 선택된 단어/문장의 정의, 역할, 이유 등을 전체 문맥에 비추어 정확하게 설명하세요.
    3. **(중요)** "안녕하세요", "좋은 질문입니다" 같은 인사말이나 불필요한 서론을 절대 쓰지 마세요. 곧바로 답변(본론)부터 시작하세요.
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

def translate_title(title: str, provider: str) -> str:
    """
    원본 영상의 제목이 외국어인 경우 한국어로 적절히 번역합니다.
    이미 한국어인 경우 원본을 그대로 반환합니다.
    """
    prompt = f"""
    당신은 전문 번역가입니다. 다음 유튜브 영상 제목을 확인하고, 
    만약 제목이 한국어가 아니라면(영어 등 외국어라면) 가장 자연스러운 한국어로 번역해주세요.
    이미 한국어거나 한국어가 주로 포함되어 있다면 원본을 그대로 출력하세요.
    다른 군더더기 말 없이 오직 "최종 제목" 텍스트만 출력하세요.
    
    원본 제목: "{title}"
    """
    
    try:
        if provider == "Google Gemini":
            client = get_gemini_client()
            response = client.models.generate_content(
                model=os.getenv("SELECTED_GEMINI_VERSION", "gemini-3.1-flash-lite"),
                contents=[prompt]
            )
            return response.text.strip().strip('"')
        else:
            target_model = "gpt-4o" if provider == "OpenAI (GPT-4o)" else provider
            client = get_openai_client(provider)
            response = client.chat.completions.create(
                model=target_model,
                messages=[
                    {"role": "system", "content": "오직 번역된 제목 텍스트만 반환합니다."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content.strip().strip('"')
    except Exception as e:
        print(f"Title translation failed: {str(e)}")
        return title # 실패 시 원본 반환

def extract_image_keyword(title: str, provider: str) -> str:
    """
    제목을 기반으로 사진 검색에 사용할 핵심 영문 키워드 1-2개를 추출합니다.
    """
    prompt = f"""
    You are an expert image researcher. Analyze the following video title and output EXACTLY ONE OR TWO English keywords that best represent its visual theme.
    These keywords will be used to search Unsplash for a high-quality background photo.
    Do not output anything else, no explanations, no quotes. Just the keywords in English.
    
    Video Title: "{title}"
    """
    
    try:
        if provider == "Google Gemini":
            client = get_gemini_client()
            response = client.models.generate_content(
                model=os.getenv("SELECTED_GEMINI_VERSION", "gemini-3.1-flash-lite"),
                contents=[prompt]
            )
            keyword = response.text.strip().replace('"', '')
            return keyword if keyword else "study"
        else:
            target_model = "gpt-4o" if provider == "OpenAI (GPT-4o)" else provider
            client = get_openai_client(provider)
            response = client.chat.completions.create(
                model=target_model,
                messages=[
                    {"role": "system", "content": "Output only English keywords for image search."},
                    {"role": "user", "content": prompt}
                ]
            )
            keyword = response.choices[0].message.content.strip().replace('"', '')
            return keyword if keyword else "study"
    except Exception as e:
        print(f"Keyword extraction failed: {str(e)}")
        return "study"
