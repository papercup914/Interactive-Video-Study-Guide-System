import os
import json
import asyncio
import time
import math
from pydub import AudioSegment
from google import genai
from google.genai import types
import openai
from typing import List, Any
from tenacity import retry, stop_after_attempt, wait_exponential
from pydantic import BaseModel, Field

def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "여기에_GEMINI_API_키를_입력하세요":
        raise ValueError("GEMINI_API_KEY 환경 변수가 설정되지 않았습니다.")
    return genai.Client(api_key=api_key)

_gemini_cache_map = {}

def get_or_create_document_cache(file_name: str, model_id: str):
    """
    Creates an explicit Context Cache for a large uploaded file.
    This reduces input token costs by 75%+ for subsequent queries.
    """
    if file_name in _gemini_cache_map:
        return _gemini_cache_map[file_name]
        
    client = get_gemini_client()
    uploaded_file = client.files.get(name=file_name)
    
    from google.genai import types
    cache = client.caches.create(
        model=model_id,
        config=types.CreateCachedContentConfig(
            contents=[uploaded_file],
            ttl="3600s",
            display_name=f"cache_{file_name}"
        )
    )
    _gemini_cache_map[file_name] = cache.name
    print(f"[Gemini Cache] Explicit Context Cache created: {cache.name}")
    return cache.name


def get_openai_client(provider: str = None):
    api_key = None
    base_url = os.getenv("OPENAI_BASE_URL")
    
    if provider == "cerebras/gpt-oss-120b":
        api_key = os.getenv("CEREBRAS_API_KEY")
        if not api_key:
            raise ValueError("CEREBRAS_API_KEY 환경 변수가 설정되지 않았습니다. .env 파일을 확인해주세요.")
        # Cerebras API is OpenAI compatible, so we can use the OpenAI client by pointing to their endpoint
        base_url = "https://api.cerebras.ai/v1"
    elif provider == "glm-5.2":
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
    OpenAI Whisper 호출 실패(크레딧 부족, Quota 초과, 네트워크 에러 등) 시 자동으로 Gemini 멀티모달 오디오 변환으로 Fallback 처리합니다.
    """
    if not audio_path or not os.path.exists(audio_path):
        raise ValueError(f"오디오 파일이 존재하지 않거나 잘못된 경로입니다: {audio_path}")

    url_hash = os.path.splitext(os.path.basename(audio_path))[0]
    data_dir = "backend/data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)
        
    cache_file = os.path.join(data_dir, f"{url_hash}_transcript.txt")
    if os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            cached_text = f.read()
            if cached_text and cached_text.strip():
                return cached_text

    transcript = ""
    whisper_done = False

    # OpenAI 계열 (Whisper) 우선 시도
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key and openai_key != "여기에_OPENAI_API_키를_입력하세요" and provider != "Google Gemini":
        try:
            client = get_openai_client("OpenAI (GPT-4o)")
            chunk_paths = _split_audio_if_needed(audio_path, max_size_mb=20)
            temp_transcript = ""
            
            for chunk_path in chunk_paths:
                with open(chunk_path, "rb") as audio_file:
                    transcript_response = client.audio.transcriptions.create(
                        model="whisper-1", 
                        file=audio_file, 
                        response_format="text"
                    )
                temp_transcript += transcript_response + " "
                
                # 분할 생성된 임시 파일 삭제 (원본은 유지)
                if chunk_path != audio_path:
                    try:
                        os.remove(chunk_path)
                    except Exception:
                        pass
            
            if temp_transcript.strip():
                transcript = temp_transcript.strip()
                whisper_done = True
        except Exception as e:
            print(f"[Warning] OpenAI Whisper 변환 실패 ({e}). Gemini 멀티모달 오디오 변환으로 자동 Fallback합니다.")

    if not whisper_done:
        # Gemini 멀티모달 오디오 분석
        try:
            client = get_gemini_client()
            uploaded_file = client.files.upload(file=audio_path)
            
            # ACTIVE 상태가 될 때까지 폴링 대기
            while uploaded_file.state.name == "PROCESSING":
                print(f"Gemini 오디오 처리 중 대기... (상태: {uploaded_file.state.name})")
                time.sleep(3)
                uploaded_file = client.files.get(name=uploaded_file.name)
                
            if uploaded_file.state.name == "FAILED":
                raise Exception("Gemini 파일 업로드 처리 실패")
                
            @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=2, min=4, max=30))
            def _call_gemini_audio():
                return client.models.generate_content(
                    model=os.getenv("SELECTED_GEMINI_VERSION", "gemini-3.1-flash-lite"),
                    contents=[uploaded_file, "Please provide a complete and highly accurate transcription of this audio in its original language. Do not summarize, format, or skip any parts. Return ONLY the transcribed text."]
                )

            response = _call_gemini_audio()
            if response and response.text:
                transcript = response.text
            else:
                raise Exception("Gemini 오디오 변환 결과 텍스트가 비어있습니다.")
        except Exception as e:
            print(f"Gemini API error during audio processing: {e}")
            raise Exception(f"오디오 변환(Whisper 및 Gemini Fallback) 처리에 실패했습니다: {e}")

    with open(cache_file, "w", encoding="utf-8") as f:
        f.write(transcript)
        
    return transcript


def generate_outline(context_data: str, provider: str, url_hash: str, length_preset: str = "아주 상세하게", force_refresh: bool = False) -> List[str]:
    """
    오디오 컨텍스트를 분석하여 상세 목차를 생성하고 로컬에 캐시합니다.
    """
    preset_suffix = "summary" if length_preset == "핵심 요약" else ("normal" if length_preset == "적당한 설명" else "detailed")
    cache_file = os.path.join("backend/data", f"{url_hash}_outline_{preset_suffix}.json")
    if not force_refresh and os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)

    char_count = len(context_data)
    
    if length_preset == "핵심 요약":
        target_chapters = max(3, min(5, char_count // 10000))
        outline_instruction = f"전체 내용을 {target_chapters}개의 핵심 챕터로 굵직하게 요약해서 묶어줘."
    elif length_preset == "적당한 설명":
        target_chapters = max(5, min(12, char_count // 5000))
        outline_instruction = f"전체 내용을 {target_chapters}개 내외의 적절한 분량의 챕터로 나누어줘."
    else:
        target_chapters = max(7, min(20, char_count // 2500))
        outline_instruction = f"전체 내용의 디테일을 놓치지 않으면서도, 인지적 과부하가 오지 않도록 전체 흐름을 정확히 {target_chapters}개의 챕터로 나누어 세분화해줘. 각 챕터는 독립적이고 논리적인 하나의 큰 주제를 다루어야 해."

    sections = []
    
    # If this is from a document (PDF/Web), do NOT generate an artificial outline.
    # Just parse the existing Markdown headers, or return a single section.
    # We can detect this if url_hash corresponds to a document (length_preset could be '문서 원본 번역')
    # Or we can just add a parameter `is_document=False`. For now let's check `length_preset`.
    if length_preset == "문서 원본 번역":
        # 만약 원본 텍스트 길이가 충분히 짧다면 분할하지 않고 한 번에 번역 (API 호출 횟수 최적화 및 속도 향상)
        # Jina AI 파싱 시 UI 요소 등으로 인해 텍스트 길이가 길게(3~4만 자) 측정될 수 있으므로 임계값을 50,000자로 상향
        if len(context_data) < 50000:
            return ["전체 문서"]
            
        for line in context_data.split("\n"):
            # 너무 잘게 쪼개져 수십 개의 챕터가 생성되는 것을 방지하기 위해 #, ## 레벨까지만 목차로 추출
            if line.startswith("# ") or line.startswith("## "):
                clean_header = line.lstrip("# ").strip()
                if clean_header and clean_header not in sections:
                    sections.append(clean_header)
        if not sections:
            sections = ["전체 문서"]
        return sections

    prompt = f"""
    주어진 내용(오디오 또는 스크립트)을 분석하여 학습용 목차(Outline)를 작성해줘.
    {outline_instruction}
    각 목차 항목은 번호나 기호 없이 새로운 줄에 제목만 하나씩 작성해줘. (예: 데이터베이스의 이해)
    """
    
    class OutlineSchema(BaseModel):
        sections: List[str] = Field(description="목차 항목들의 리스트 (기호나 번호 없이 순수 제목만 포함)")

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=2, min=4, max=30))
    def _call_gemini_outline():
        client = get_gemini_client()
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=OutlineSchema,
            temperature=0.2
        )
        if context_data.startswith("GEMINI_FILE_URI::"):
            file_name = context_data.split("::")[1]
            uploaded_file = client.files.get(name=file_name)
            contents_payload = [uploaded_file, prompt]
        else:
            contents_payload = [context_data, prompt]
            
        response = client.models.generate_content(
            model=os.getenv("SELECTED_GEMINI_VERSION", "gemini-3.1-flash-lite"),
            contents=contents_payload,
            config=config
        )
        return response.text

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=2, min=4, max=30))
    def _call_openai_outline(target_provider="OpenAI (GPT-4o)"):
        target_model = target_provider
        if target_provider == "OpenAI (GPT-4o)":
            target_model = "gpt-4o"
        elif target_provider == "cerebras/gpt-oss-120b":
            target_model = "gpt-oss-120b"
            
        client = get_openai_client(target_provider)
        response = client.chat.completions.create(
            model=target_model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"다음은 영상 스크립트 내용입니다:\n\n{context_data}"}
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "outline_schema",
                    "schema": OutlineSchema.model_json_schema()
                }
            }
        )
        return response.choices[0].message.content

    if provider == "Google Gemini":
        try:
            outline_raw = _call_gemini_outline()
        except Exception as e:
            print(f"[Harness Fallback] Gemini failed outline generation: {e}. Switching to Fallback.")
            outline_raw = _call_openai_outline("OpenAI (GPT-4o)")
    else:
        outline_raw = _call_openai_outline(provider)
        
    try:
        parsed_json = json.loads(outline_raw)
        raw_sections = parsed_json.get("sections", [])
    except Exception as e:
        print(f"[Harness Error] Failed to parse structured output: {e}")
        raw_sections = []
        
    for line in raw_sections:
        clean_line = line.strip().lstrip('1234567890.-*# ')
        if clean_line:
            sections.append(clean_line)
            
    if not sections:
        sections = ["전체 내용 요약"]
        
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(sections, f, ensure_ascii=False)
        
    return sections

async def async_generate_chapter_content(section_title: str, context_data: str, provider: str, chunk_index: int, total_chunks: int, length_preset: str = "아주 상세하게", analogy_preset: str = "풍부한 비유", learner_profile: str = "", url_hash: str = "", tutor_persona: dict = None, force_refresh: bool = False) -> str:
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
    
    if not force_refresh and os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            return f.read()

    chunked_context = context_data
    

    
    if length_preset == "문서 원본 번역":
        # Document translation mode: 1:1 translation keeping markdown images intact
        system_prompt = f"""
        당신은 전문 번역가입니다. 
        제공된 원본 문서(마크다운 형태)에서 챕터 제목 '{section_title}' 부분에 해당하는 내용(하위 섹션 포함)을 추출한 뒤,
        그 내용을 완벽하게 한국어로 1:1 번역하여 출력하세요.
        
        [매우 중요] 
        - 문서에 포함된 표(Table) 형태나 마크다운 이미지 태그(예: `![caption](url)`)는 절대 수정하거나 삭제하지 말고 제자리에 그대로 유지하십시오.
        - 내용을 임의로 요약하거나 가르치는 듯한 말투를 쓰지 마십시오. 오직 원문을 한국어로 직역(Professional Translation)만 하십시오.
        - 만약 '{section_title}'이 "전체 문서"라면 제공된 원본 전체를 처음부터 끝까지 빠짐없이 번역하십시오.
        """
    else:
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
    
        tutor_directive = ""
        if tutor_persona:
            tutor_role = tutor_persona.get("role", "전문 튜터")
            tutor_tone = tutor_persona.get("tone", "친절하고 명확하게")
            tutor_focus = tutor_persona.get("focus_areas", "핵심 내용 설명")
            
            tutor_directive = f"""
            [AI 튜터 페르소나 (강제 적용)]
            역할(Role): {tutor_role}
            어조(Tone): {tutor_tone}
            집중 영역(Focus Areas): {tutor_focus}
            
            지시사항: 당신은 단순한 AI가 아니라 위의 '역할(Role)'을 수행하는 전문가입니다. 본문 전체의 문체와 내용 전개를 이 '어조(Tone)'와 '집중 영역'에 완벽히 맞추십시오.
            """
        else:
            tutor_directive = "당신은 영상 내용을 기반으로 학습 가이드를 작성하는 튜터입니다."

        system_prompt = f"""
        {tutor_directive}
        
        제공된 [전체 스크립트]를 문맥적으로 분석하여, 다음 챕터 제목(또는 주제)에 해당하는 내용을 찾아 챕터 본문을 작성해줘.
        챕터 제목은 스크립트의 특정 부분을 요약한 것이므로, 정확히 같은 단어가 없더라도 의미상 관련된 내용을 찾아야 해.
        단, 전체 스크립트를 아무리 살펴봐도 해당 주제와 관련된 내용이 아예 존재하지 않을 때만 예외적으로 "해당 내용을 영상에서 찾을 수 없습니다."라고 출력해.
        
        챕터 제목: {section_title}
        
        <PERSONA_DIRECTIVE>
        당신은 무미건조한 AI가 아닙니다. 위에서 부여된 [AI 튜터 페르소나]와 아래의 [학습자 프로필]을 결합하여 완벽한 맞춤형 지도를 수행하십시오.
        
        [학습자 프로필]
        {learner_profile if learner_profile else "일반적인 성인 학습자"}
        
        1. 어조 강제: 튜터 페르소나의 '어조'와 학습자 프로필의 '원하는 튜터 어조'를 조화롭게 섞어 본문 전체에 걸쳐 철저하게 유지하십시오.
        2. 비유 강제: 어려운 개념을 설명할 때는 반드시 프로필에 명시된 '주요 관심사'와 관련된 메타포(비유)를 하나 이상 들어 설명하십시오. 
        3. 눈높이 강제: '학습 목표'와 '연령대/직업'에 맞추어 전문 용어의 사용 수준과 설명의 깊이를 조절하십시오.
        4. 표현 현지화 강제: '24/7', 'ASAP' 등 영어식 표현이나 약어는 원문을 그대로 쓰지 말고 문맥에 맞게 자연스러운 한국어(예: '일주일 24시간 내내', '연중무휴' 등)로 번역하여 사용하십시오.
        </PERSONA_DIRECTIVE>
        
        프롬프트 가이드라인:
        - {analogy_instruction}
        - 핵심 인사이트 박스(Markdown 인용구 > 문법 사용)를 만들어 핵심을 짚어줘라.
        - {length_instruction}
        - [중요: 적응형 인지 라우팅 체계 및 인터랙티브 학습 장치 생성]
        챕터 본문 작성이 끝난 후, 이 챕터의 핵심 지식 성격을 분석하여 다음 4가지 인지 영역 중 하나로 분류하고, 해당 영역에 맞는 특수한 인터랙티브 태그를 **정확히 하나만** 가장 마지막에 출력하세요. (기존의 객관식 퀴즈나 토론 주제는 출력하지 마세요)
        
        [치명적 주의사항]
        - 반드시 XML 형태의 여는 태그와 닫는 태그(예: <feynman> ... </feynman>)로 전체 JSON을 감싸야 합니다!
        - 태그 안에 띄어쓰기를 절대 넣지 마세요. (정상: <feynman>, 오류: < feynman >)
        - 태그 없이 JSON 텍스트만 덩그러니 출력하면 시스템 파서 에러가 발생하여 서비스가 중단됩니다.

        1. 개념 이해 (CONCEPT): 원리, 이유, 복잡한 메커니즘을 다루는 챕터.
        <feynman>
        {{
          "tag_team_scenario": "학습자와 AI가 한 팀이 되어 관련 지식이 전혀 없는 초보자(예: 중학생, 비전공자 등)에게 이 개념을 쉽게 설명하는 흥미로운 상황 제시",
          "target_persona": "설명을 들을 가상의 초보자 특징 (예: '중력을 처음 배우는 초등학생')",
          "initial_ai_message": "AI가 먼저 사고 실험 파트너로서 대화를 시작하며 반자동 완성을 유도하는 문장 (예: '자, 이 학생에게 중력을 설명해보자. 중력은 보이지 않는 끈과 같은데, 왜냐하면...')",
          "concept_summary": "사용자가 도저히 모를 때(SOS) 즉시 보여줄 아주 쉽고 완벽한 1문단짜리 비유적 정답 요약"
        }}
        </feynman>

        2. 논리/수학/알고리즘 (LOGIC): 단계별 증명, 코드의 흐름, 수학적 도출을 다루는 챕터.
        <steptracer>
        {{
          "scenario": "풀어야 할 문제 상황이나 코드 스니펫",
          "steps": [
            {{"question": "이 루프를 한 번 돌고 나면 변수 x의 값은 무엇이 될까요?", "answer": "x는 5가 됩니다. 왜냐하면..."}},
            {{"question": "다음 단계는?", "answer": "..."}}
          ]
        }}
        </steptracer>

        3. 단순 암기 (MEMORY): 연도, 사실관계, 용어의 정의 등 논리적 설명보다 단순 기억이 필요한 챕터.
        <mnemonic>
        {{
          "story": "학습자의 관심사나 아주 기상천외한 요소(Bizarre)를 활용하여 이 사실을 평생 잊지 않게 만들어주는 짧고 강렬한 연상기억법 스토리",
          "flashcards": [
            {{"q": "앞면 질문", "a": "뒷면 정답"}},
            {{"q": "앞면 질문", "a": "뒷면 정답"}}
          ]
        }}
        </mnemonic>

        4. 절차적/시각적 작업 (PROCEDURE): 툴 사용법, 매듭 묶는 법, 요리 순서 등 행동 지침이 필요한 챕터.
        <procedure>
        {{
          "checklists": [
            {{"step": 1, "action": "매직 봉 툴을 선택한다", "hint": "화면 좌측 도구 모음에 있습니다"}},
            {{"step": 2, "action": "...", "hint": "..."}}
          ]
        }}
        </procedure>

        반드시 4가지 중 현재 챕터에 가장 적합한 1가지만 골라 정확한 JSON 구조로 태그를 감싸서 출력하세요. 태그의 시작과 끝이 명확해야 합니다.
    """
    
    loop = asyncio.get_event_loop()
    
    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=2, min=4, max=30))
    def _call_gemini_with_retry():
        client = get_gemini_client()
        if chunked_context.startswith("GEMINI_FILE_URI::"):
            file_name = chunked_context.split("::")[1]
            model_id = os.getenv("SELECTED_GEMINI_VERSION", "gemini-3.1-flash-lite")
            
            try:
                # Context Caching 적용 (Option B)
                cache_name = get_or_create_document_cache(file_name, model_id)
                from google.genai import types
                response = client.models.generate_content(
                    model=model_id,
                    contents=[system_prompt], # System prompt is passed per chapter
                    config=types.GenerateContentConfig(
                        cached_content=cache_name
                    )
                )
                return response.text
            except Exception as cache_e:
                print(f"[Gemini Cache] Failed to use explicit cache: {cache_e}. Falling back to normal upload.")
                uploaded_file = client.files.get(name=file_name)
                contents_payload = [uploaded_file, system_prompt]
                response = client.models.generate_content(
                    model=model_id,
                    contents=contents_payload
                )
                return response.text
        else:
            contents_payload = [chunked_context, system_prompt]
            
            response = client.models.generate_content(
                model=os.getenv("SELECTED_GEMINI_VERSION", "gemini-3.1-flash-lite"),
                contents=contents_payload
            )
            return response.text

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=2, min=4, max=30))
    def _call_openai_with_retry(target_provider="OpenAI (GPT-4o)"):
        target_model = target_provider
        if target_provider == "OpenAI (GPT-4o)":
            target_model = "gpt-4o"
        elif target_provider == "cerebras/gpt-oss-120b":
            target_model = "gpt-oss-120b"
            
        client = get_openai_client(target_provider)
        response = client.chat.completions.create(
            model=target_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"다음은 분석할 원본 영상 전체 스크립트입니다:\n\n{chunked_context}"}
            ]
        )
        return response.choices[0].message.content

    def _call_api():
        if provider == "Google Gemini":
            try:
                return _call_gemini_with_retry()
            except Exception as e:
                print(f"[Harness Fallback] Gemini failed after retries: {e}. Switching to Fallback model (GPT-4o).")
                # Fallback to GPT-4o
                return _call_openai_with_retry("OpenAI (GPT-4o)")
        else:
            return _call_openai_with_retry(provider)

    result = await loop.run_in_executor(None, _call_api)
    
    with open(cache_file, "w", encoding="utf-8") as f:
        f.write(result)
        
    return result

def generate_answer(selected_text: str, context: str, question: str, provider: str, learner_profile: str = "") -> str:
    """
    본문 컨텍스트를 바탕으로 사용자가 선택한 특정 텍스트에 대한 질문에 답변을 생성합니다.
    """
    prompt = f"""
    당신은 학습자의 질문에 답하는 1:1 맞춤형 사고 확장 파트너입니다.
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
    
    1. 어조 강제: 명시된 '원하는 어조'를 철저하게 유지하십시오.
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
        target_model = provider
        if provider == "OpenAI (GPT-4o)":
            target_model = "gpt-4o"
        elif provider == "cerebras/gpt-oss-120b":
            target_model = "gpt-oss-120b"
            
        client = get_openai_client(provider)
        response = client.chat.completions.create(
            model=target_model,
            messages=[
                {"role": "system", "content": "당신은 본문 내용을 바탕으로 독자의 질문에 친절하게 답변하는 사고 파트너입니다."},
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
            target_model = provider
            if provider == "OpenAI (GPT-4o)":
                target_model = "gpt-4o"
            elif provider == "cerebras/gpt-oss-120b":
                target_model = "gpt-oss-120b"
            
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

def profile_content(context_data: str, provider: str) -> dict:
    """
    Analyzes the beginning of the transcript to dynamically profile the content type 
    and recommend optimal generation settings.
    """
    sample_text = context_data[:5000] if len(context_data) > 5000 else context_data
    
    prompt = f"""
    You are an expert AI content profiler. Analyze the following transcript sample and determine its content type, information density, and target audience.
    Based on your analysis, choose the most appropriate settings for generating a study guide.

    Output MUST be a valid JSON object without any markdown formatting. Use this EXACT schema:
    {{
        "length_preset": "핵심 요약" | "적당한 설명" | "아주 상세하게",
        "analogy_preset": "비유 없이 담백하게" | "적절한 비유 추가" | "풍부한 비유",
        "profile_message": "A short, friendly Korean message explaining your decision (e.g., '💡 AI가 전문적인 IT 강의로 인식하여 비유 없이 상세하게 정리합니다.')",
        "tutor_persona": {{
            "role": "The specific role the AI should take (e.g., '문학 평론가', 'IT 시니어 개발자', '열정적인 동기부여 강사', '중립적인 토론 진행자')",
            "tone": "The tone of voice (e.g., '전문적이고 냉철하게', '친절하고 비유를 섞어서', '학술적이고 객관적으로')",
            "focus_areas": "What to focus on based on content type (e.g., '핵심 쟁점과 논거 분석', '실무 적용 가능한 코드 스니펫', '저자의 의도와 문맥 해석')"
        }}
    }}

    Transcript Sample:
    {sample_text}
    """
    
    try:
        if provider == "Google Gemini":
            client = get_gemini_client()
            response = client.models.generate_content(
                model=os.getenv("SELECTED_GEMINI_VERSION", "gemini-3.1-flash-lite"),
                contents=[prompt]
            )
            raw_text = response.text.strip()
        else:
            client = get_openai_client(provider)
            target_model = "gpt-4o-mini" if provider == "OpenAI (GPT-4o)" else provider
            response = client.chat.completions.create(
                model=target_model,
                messages=[
                    {"role": "system", "content": "Output valid JSON only."},
                    {"role": "user", "content": prompt}
                ]
            )
            raw_text = response.choices[0].message.content.strip()
            
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.startswith("```"):
            raw_text = raw_text[3:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
            
        return json.loads(raw_text.strip())
    except Exception as e:
        print(f"Profiling failed: {str(e)}")
        return {
            "length_preset": "적당한 설명",
            "analogy_preset": "적절한 비유 추가",
            "profile_message": "💡 영상 길이에 맞는 기본 설정으로 정리했습니다."
        }


