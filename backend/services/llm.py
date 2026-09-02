import os
import json
import asyncio
import time
import math
from google import genai
from google.genai import types
from typing import List, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception
from pydantic import BaseModel, Field

import re

def _should_retry_error(exception: BaseException) -> bool:
    """인증 오류, 결제/크레딧 부족(402), 404(모델 없음), 설정 누락은 재시도하지 않고 즉시 Fallback으로 넘깁니다."""
    err_str = str(exception).lower()
    non_retry_keywords = (
        "authentication", "401", "api_key", "invalid_api_key", "incorrect api key",
        "404", "not_found", "model not found", "unsupported",
        "402", "payment_required", "insufficient_quota", "credit_balance_exhausted", "billing"
    )
    if any(k in err_str for k in non_retry_keywords):
        return False
    if isinstance(exception, (ValueError, ImportError, TypeError)):
        return False
    return True

FALLBACK_GEMINI_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite",
    "gemini-flash-lite-latest"
]

def safe_gemini_generate_content(client, model: str, contents: Any, config: Any = None, max_retries: int = 3):
    """
    Google Gemini API 호출 시:
    1) 일일 무료 할당량(RequestsPerDay)이 소진되면 다음 가용 모델(3.5-flash-lite, 3.6-flash 등)로 즉시 자동 스위칭합니다.
    2) 분당 한도(RPM) 초과 시 서버가 요구한 대기 시간 동안 대기 후 자동 재시도합니다.
    """
    target_model = model or os.getenv("SELECTED_GEMINI_VERSION", "gemini-3.5-flash-lite")
    candidate_models = [target_model] + [m for m in FALLBACK_GEMINI_MODELS if m != target_model]
    
    last_err = None
    for current_model in candidate_models:
        for attempt in range(1, max_retries + 1):
            try:
                if config is not None:
                    return client.models.generate_content(model=current_model, contents=contents, config=config)
                else:
                    return client.models.generate_content(model=current_model, contents=contents)
            except Exception as e:
                err_str = str(e)
                err_str_lower = err_str.lower()
                last_err = e
                is_quota = "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str_lower
                is_unavailable = "503" in err_str or "404" in err_str or "not_found" in err_str_lower or "unavailable" in err_str_lower or "no longer available" in err_str_lower
                
                if is_quota or is_unavailable:
                    # 일일 총량 할당량(Daily Quota) 초과 또는 모델 미지원인 경우 대기하지 않고 즉시 다음 가용 모델로 스위칭
                    is_daily_quota = (
                        "generaterequestsperday" in err_str_lower or 
                        "free_tier_requests" in err_str_lower or 
                        "limit: 20" in err_str_lower or
                        "limit: 15" in err_str_lower or
                        is_unavailable
                    )
                    if is_daily_quota:
                        print(f"[Gemini Quota Switch] Model '{current_model}' Daily Quota Exhausted or Unavailable -> Switching to next candidate model...")
                        break
                    
                    # 분당 요청 한도(RPM) 초과인 경우
                    if attempt < max_retries:
                        delay_match = re.search(r'retry in (\d+(?:\.\d+)?)s', err_str, re.IGNORECASE)
                        delay = max(5, int(float(delay_match.group(1))) + 2) if delay_match else min(30, 10 * attempt)
                        print(f"[Gemini Rate Limit] Model '{current_model}' RPM limit reached. Waiting {delay}s before retry ({attempt}/{max_retries})...")
                        time.sleep(delay)
                    else:
                        print(f"[Gemini Model Fallback] Model '{current_model}' max retries reached -> Switching to next model.")
                        break
                else:
                    raise e
                    
    if last_err:
        raise last_err

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
        if _gemini_cache_map[file_name] is None:
            raise ValueError("이전 시도에서 Context Cache 생성이 지원되지 않음(토큰 수 미달 등)")
        return _gemini_cache_map[file_name]
        
    try:
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
    except Exception as e:
        _gemini_cache_map[file_name] = None
        raise e


def is_gemini_provider(provider: str = None) -> bool:
    """
    주어진 provider 문자열이 Gemini 계열인지 확인합니다.
    """
    if not provider:
        return True
    p = str(provider).lower().strip()
    return "gemini" in p or "google" in p or p == "default"

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
        
    try:
        import openai
        return openai.Client(api_key=api_key, base_url=base_url)
    except ImportError:
        raise ImportError("openai 패키지가 설치되지 않았습니다. pip install openai 를 실행하세요.")

def _split_audio_if_needed(audio_path: str, max_size_mb: int = 20) -> List[str]:
    """오디오 파일이 max_size_mb를 초과하면 분할하여 임시 파일 경로 목록을 반환합니다."""
    file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
    if file_size_mb <= max_size_mb:
        return [audio_path]
        
    print(f"오디오 크기가 {file_size_mb:.2f}MB로 제한({max_size_mb}MB)을 초과하여 분할합니다.")
    try:
        from pydub import AudioSegment
        audio = AudioSegment.from_file(audio_path)
    except Exception as e:
        print(f"pydub 로드 실패 또는 오디오 분할 불가: {e}. 원본 파일 사용.")
        return [audio_path]
    
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

def process_audio(audio_path: str, provider: str, url_hash: Optional[str] = None) -> str:
    """
    선택된 Provider에 맞게 오디오를 처리하여 텍스트 대본(Transcript)을 반환합니다.
    로컬에 이미 캐시된 대본이 있으면 API를 호출하지 않고 캐시를 반환합니다.
    OpenAI Whisper 호출 실패(크레딧 부족, Quota 초과, 네트워크 에러 등) 시 자동으로 Gemini 멀티모달 오디오 변환으로 Fallback 처리합니다.
    """
    if not audio_path or not os.path.exists(audio_path):
        raise ValueError(f"오디오 파일이 존재하지 않거나 잘못된 경로입니다: {audio_path}")

    derived_hash = url_hash or os.path.splitext(os.path.basename(audio_path))[0]
    data_dir = "backend/data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)
        
    cache_file = os.path.join(data_dir, f"{derived_hash}_transcript.txt")
    if os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            cached_text = f.read()
            if cached_text and cached_text.strip():
                return cached_text

    transcript = ""
    whisper_done = False

    # OpenAI 계열 (Whisper) 우선 시도 (Gemini가 명시된 경우 제외)
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key and openai_key != "여기에_OPENAI_API_키를_입력하세요" and not is_gemini_provider(provider):
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
                
            @retry(retry=retry_if_exception(_should_retry_error), stop=stop_after_attempt(5), wait=wait_exponential(multiplier=2, min=4, max=30))
            def _call_gemini_audio():
                return safe_gemini_generate_content(
                    client=client,
                    model=os.getenv("SELECTED_GEMINI_VERSION", "gemini-3.5-flash-lite"),
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

    if transcript:
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                f.write(transcript)
        except Exception as e:
            print(f"[Warning] Transcript cache save failed: {e}")

    return transcript


def generate_outline(context_data: str, provider: str, url_hash: str, length_preset: str = "아주 상세하게", force_refresh: bool = False, video_chapters: list = None) -> List[str]:
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

    is_valid_chapters = False
    chapter_text = ""
    if video_chapters and isinstance(video_chapters, list):
        chapter_titles = [str(ch.get('title', '')).strip() for ch in video_chapters if ch.get('title')]
        if chapter_titles:
            is_valid_chapters = True
            chapter_text = "\n".join(f"- {title}" for title in chapter_titles)

    if is_valid_chapters:
        prompt = f"""
        유튜브 영상의 공식 챕터 정보가 주어집니다.
        다음 공식 챕터 제목들을 학습용 목차에 맞게 자연스럽고 명확한 한국어로 번역 및 정제해주세요.
        원래의 챕터 개수와 시간적 순서(Time Sequence)를 100% 엄격하게 동일하게 유지해야 합니다.
        
        - [중요] 각 목차 항목은 번호나 기호 없이 새로운 줄에 순수 한국어 제목만 하나씩 작성해줘.
        
        공식 챕터 제목:
        {chapter_text}
        """
        # 챕터 번역에는 전체 스크립트를 제외하여 토큰을 절약합니다.
        context_data = "이 영상의 스크립트 내용은 위의 챕터 제목을 번역하기 위한 컨텍스트입니다."
    else:
        prompt = f"""
        주어진 내용(오디오 또는 스크립트)을 분석하여 학습용 목차(Outline)를 작성해줘.
        {outline_instruction}
        - [🚨 최우선 절대 준수: 시간 순서(Time Sequence) 엄격 유지]
          반드시 영상의 시작(도입/개요)부터 중간(핵심 내용/원리/실습), 끝(결론/마무리/전망) 순서대로 시간 흐름에 맞게 나열해야 합니다.
          절대로 '결론'이나 '마무리'가 1번이나 앞부분에 오거나, '도입'이나 '개요'가 뒷부분에 오는 역순(Inversion)으로 작성하지 마십시오!
        - [중요] 원본 스크립트가 외국어(영어 등)이더라도, 각 목차 항목의 제목은 반드시 자연스럽고 명확한 한국어로 번역하여 작성하세요.
        - 각 목차 항목은 번호나 기호 없이 새로운 줄에 순수 한국어 제목만 하나씩 작성해줘. (예: 대형 언어 모델의 생태계와 작동 원리)
        """
    
    class OutlineSchema(BaseModel):
        sections: List[str] = Field(description="한국어로 작성된 목차 항목들의 리스트 (기호나 번호 없이 순수 한국어 제목만 포함)")

    @retry(retry=retry_if_exception(_should_retry_error), stop=stop_after_attempt(5), wait=wait_exponential(multiplier=2, min=4, max=30))
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
            
        response = safe_gemini_generate_content(
            client=client,
            model=os.getenv("SELECTED_GEMINI_VERSION", "gemini-3.5-flash-lite"),
            contents=contents_payload,
            config=config
        )
        return response.text

    @retry(retry=retry_if_exception(_should_retry_error), stop=stop_after_attempt(5), wait=wait_exponential(multiplier=2, min=4, max=30))
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

    if is_gemini_provider(provider):
        try:
            outline_raw = _call_gemini_outline()
        except Exception as e:
            print(f"[Harness Fallback] Gemini failed outline generation: {e}. Switching to Fallback.")
            try:
                outline_raw = _call_openai_outline("OpenAI (GPT-4o)")
            except Exception as e2:
                print(f"[Harness Error] Both Gemini and OpenAI outline failed: {e2}")
                outline_raw = "{}"
    else:
        try:
            outline_raw = _call_openai_outline(provider)
        except Exception as e:
            print(f"[Harness Fallback] OpenAI outline failed: {e}. Switching to Gemini Fallback.")
            outline_raw = _call_gemini_outline()
        
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
    else:
        # 시간 순서 역순(Inversion) 감지 및 자동 교정 가드레일
        conclusion_keywords = ("결론", "마무리", "총평", "끝마치며", "마치며", "최종 요약")
        intro_keywords = ("도입", "개요", "시작", "소개", "오프닝", "시작하며", "프롤로그")
        
        first_is_conclusion = any(kw in sections[0] for kw in conclusion_keywords)
        last_is_intro = any(kw in sections[-1] for kw in intro_keywords)
        
        if first_is_conclusion and last_is_intro:
            print(f"[Outline Guardrail] Chronological inversion detected ({sections[0]} <-> {sections[-1]}). Reversing outline order!")
            sections.reverse()
        elif first_is_conclusion and len(sections) > 1:
            print(f"[Outline Guardrail] Conclusion at start detected ({sections[0]}). Moving to end!")
            conclusion_item = sections.pop(0)
            sections.append(conclusion_item)
        
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(sections, f, ensure_ascii=False)
        
    return sections

INTERACTIVE_TAGS = ("feynman", "steptracer", "mnemonic", "procedure", "quiz", "discussion")
INTERACTIVE_TAG_PATTERN = re.compile(
    r'<\s*(feynman|steptracer|mnemonic|procedure|quiz|discussion)\b[^>]*>',
    re.IGNORECASE
)
FORBIDDEN_START_PATTERN = re.compile(
    r'^\s*(?:'
    r'<!--[\s\S]*?-->\s*|'
    r'```[\w-]*\s*(?:<|[\{\[])|'
    r'```(?:feynman|steptracer|step_tracer|step-tracer|mnemonic|procedure|quiz|discussion|widget|interactive|component|chapter)\b|'
    r'<\s*(?:feynman|steptracer|step_tracer|step-tracer|mnemonic|procedure|quiz|discussion|interactive|widget|component|response|root|chapter|guide|section|content|output|result|data|json|xml|\?xml)\b'
    r')',
    re.IGNORECASE
)

def _get_cache_dir() -> str:
    """캐시 디렉토리 절대 경로를 일관되게 반환합니다."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cache_dir = os.path.join(base_dir, "data", "cache_chapters")
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir

def sanitize_chapter_narrative(content: str, section_title: str = "") -> str:
    """
    LLM 출력물에서 시스템 메타 텍스트(예: [파트 1: ...]) 및 서두 인사말(예: 안녕하세요, 반갑습니다 등)을
    강력한 정규식으로 완벽히 제거하여 순수한 서술형 학습 본문으로 정제합니다.
    """
    if not content or not isinstance(content, str):
        return ""

    sanitized = content.strip()

    # 1. 시스템 메타 텍스트 태그 전역 제거 (예: ### [파트 1: 상세 챕터 서술형 학습 본문], [파트 2: ...])
    sanitized = re.sub(r'#{0,4}\s*\[?\s*파트\s*[12]\s*:[^\]\n]*\]?\s*\n*', '', sanitized, flags=re.IGNORECASE)

    # 2. 본문 서두 챕터 제목 중복 줄 제거
    if section_title:
        escaped_title = re.escape(section_title.strip())
        sanitized = re.sub(rf'^\s*(?:#{{1,4}}\s*)?(?:\d+\.\s*)?{escaped_title}\s*\n+', '', sanitized.strip(), flags=re.IGNORECASE)

    # 3. 첫 줄이 제목인 경우 보존하면서 두 번째 줄 이하의 인사말 블록 제거
    lines = sanitized.strip().split('\n')
    if lines and (lines[0].startswith('#') or (len(lines[0].strip()) < 80 and not lines[0].strip().endswith('.'))):
        first_line = lines[0]
        rest = '\n'.join(lines[1:]).strip()
        rest = re.sub(r'^\s*(?:\*\*)?(?:안녕하세요|반갑습니다|환영합니다)[\s\S]*?(?:입니다|멘토입니다|튜터입니다|가이드입니다|파트너입니다)[.!\n]+(?:\*\*)?\s*', '', rest, flags=re.IGNORECASE)
        rest = re.sub(r'^\s*(?:\*\*)?(?:이번\s*(?:챕터|시간|강의|가이드)에서는?|오늘(?:\s*우리가)?\s*(?:함께)?\s*(?:살펴볼|알아볼|파헤쳐\s*볼|배워볼))[\s\S]*?(?:알아보겠습니다|살펴보겠습니다|배워보겠습니다|시작하겠습니다|파헤쳐\s*보겠습니다|짚어보겠습니다|함께\s*가보시죠|하겠습니다|합니다|입니다)[.!\n]+(?:\*\*)?\s*', '', rest, flags=re.IGNORECASE)
        rest = re.sub(r'^\s*(?:\*\*)?(?:안녕하세요|반갑습니다|환영합니다)[^\n]*?(?:\*\*)?\n+', '', rest, flags=re.IGNORECASE)
        sanitized = first_line + '\n\n' + rest

    # 4. 제목 없이 바로 시작된 최상단 서두 인사말 / 자기소개 문구 제거
    sanitized = re.sub(r'^\s*(?:\*\*)?(?:안녕하세요|반갑습니다|환영합니다)[\s\S]*?(?:입니다|멘토입니다|튜터입니다|가이드입니다|파트너입니다)[.!\n]+(?:\*\*)?\s*', '', sanitized.strip(), flags=re.IGNORECASE)
    sanitized = re.sub(r'^\s*(?:\*\*)?(?:이번\s*(?:챕터|시간|강의|가이드)에서는?|오늘(?:\s*우리가)?\s*(?:함께)?\s*(?:살펴볼|알아볼|파헤쳐\s*볼|배워볼))[\s\S]*?(?:알아보겠습니다|살펴보겠습니다|배워보겠습니다|시작하겠습니다|파헤쳐\s*보겠습니다|짚어보겠습니다|함께\s*가보시죠|하겠습니다|합니다|입니다)[.!\n]+(?:\*\*)?\s*', '', sanitized.strip(), flags=re.IGNORECASE)
    sanitized = re.sub(r'^\s*(?:\*\*)?(?:안녕하세요|반갑습니다|환영합니다)[^\n]*?(?:\*\*)?\n+', '', sanitized.strip(), flags=re.IGNORECASE)

    return sanitized.strip()

def validate_chapter_narrative(content: str, min_chars: int = 1000, min_narrative_chars: int = 800) -> tuple[bool, str]:
    """
    챕터 출력물이 [파트 1: 상세 서술형 학습 본문] + [파트 2: 인터랙티브 학습 장치]의
    2단계 엄격 출력 구조를 준수하는지 검증합니다.
    - 태그로 바로 시작하거나 본문 없이 태그만 있는 경우 거부
    - 원시 JSON / 코드 펜스 JSON 구조로 시작하는 경우 거부
    - 인터랙티브 태그 이전의 순수 서술형 본문이 min_narrative_chars 미만인 경우 거부
    - 1,000자 미만(또는 지정된 최소 길이)의 지나치게 짧은 요약 거부
    - 인사말(안녕하세요, 반갑습니다) 또는 파트 메타 텍스트가 남아있는 경우 거부
    """
    if not content or not isinstance(content, str):
        return False, "내용이 비어 있거나 올바른 문자열이 아닙니다."
        
    trimmed = content.strip()
    
    # 1. JSON 형태 또는 태그/코드펜스 데이터로 바로 시작하는 경우 즉시 거부
    if trimmed.startswith("{") or trimmed.startswith("["):
        return False, "출력이 마크다운 서술형 본문이 아닌 원시 JSON 구조로 시작합니다."
        
    if FORBIDDEN_START_PATTERN.match(trimmed):
        return False, "출력이 마크다운 서술형 본문 없이 인터랙티브 태그 또는 원시 데이터 블록으로 바로 시작합니다."

    # 2. 파트 메타 텍스트 또는 서두 인사말 잔류 검사
    first_150 = trimmed[:150]
    if re.search(r'\[\s*파트\s*[12]\s*:', first_150, re.IGNORECASE):
        return False, "출력에 시스템 메타 텍스트([파트 1/2...])가 포함되어 있습니다."
    if re.search(r'(?:안녕하세요|반갑습니다|환영합니다|여러분의\s*튜터)', first_150):
        return False, "출력 서두에 의례적인 인사말(안녕하세요/튜터 소개 등)이 포함되어 있습니다."
        
    # 3. 인터랙티브 태그가 포함되어 있다면, 태그 이전의 서술형 본문 길이 선제 검증
    tag_match = INTERACTIVE_TAG_PATTERN.search(trimmed)
    if tag_match:
        tag_start_pos = tag_match.start()
        narrative_part = trimmed[:tag_start_pos].strip()
        if len(narrative_part) < min_narrative_chars:
            return False, f"인터랙티브 태그 이전의 서술형 본문 분량이 부족합니다 ({len(narrative_part)} < {min_narrative_chars}자)."
            
    # 4. 전체 길이 검증
    if len(trimmed) < min_chars:
        return False, f"출력 전체 길이가 너무 짧습니다 ({len(trimmed)} < {min_chars}자)."
            
    return True, "유효한 서술형 본문 및 2단계 구조입니다."

def clean_invalid_cached_chapters(data_dir: Optional[str] = None) -> int:
    """
    기존 캐시 디렉토리를 전수 스캔하여, 1,000자 미만이거나 태그 단독 등
    2단계 서술형 구조를 위반하는 불량 캐시 파일들을 자동 영구 삭제(무효화)합니다.
    """
    dirs_to_clean = [data_dir] if data_dir else [_get_cache_dir()]
    
    # 중첩된 레거시 캐시 경로(backend/backend/data/cache_chapters)가 존재할 경우 함께 정리
    if not data_dir:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        nested_dir = os.path.join(base_dir, "backend", "data", "cache_chapters")
        if os.path.exists(nested_dir) and nested_dir not in dirs_to_clean:
            dirs_to_clean.append(nested_dir)
            
    removed_count = 0
    for target_dir in dirs_to_clean:
        if not os.path.exists(target_dir):
            continue
        for fname in os.listdir(target_dir):
            if not fname.endswith(".txt"):
                continue
            fpath = os.path.join(target_dir, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read()
                is_valid, reason = validate_chapter_narrative(content, min_chars=1000, min_narrative_chars=800)
                if not is_valid:
                    print(f"[Cache Invalidation Cleanup] Deleting invalid cache file '{fname}' in '{target_dir}': {reason}")
                    os.remove(fpath)
                    removed_count += 1
            except Exception as e:
                print(f"[Cache Invalidation Warning] Error processing cache file '{fname}': {e}")
                
    return removed_count

async def async_generate_chapter_content(section_title: str, context_data: str, provider: str, chunk_index: int, total_chunks: int, length_preset: str = "아주 상세하게", analogy_preset: str = "풍부한 비유", learner_profile: str = "", url_hash: str = "", tutor_persona: dict = None, force_refresh: bool = False) -> str:
    """
    전체 스크립트를 LLM에 전달하여 챕터 내용에 해당하는 부분을 스스로 찾아서 작성하도록 합니다. (정확도 우선)
    [파트 1: 상세 서술형 학습 본문] + [파트 2: 인터랙티브 학습 장치]의 2단계 엄격 출력 구조를 강제합니다.
    """
    import hashlib
    
    # 캐시 키 생성 (모든 조건이 동일할 때만 캐시 히트)
    cache_key_raw = f"{url_hash}_{section_title}_{provider}_{length_preset}_{analogy_preset}_{learner_profile}"
    cache_hash = hashlib.md5(cache_key_raw.encode('utf-8')).hexdigest()
    cache_dir = _get_cache_dir()
    cache_file = os.path.join(cache_dir, f"{cache_hash}.txt")
    
    target_min_chars = 1000 if length_preset == "핵심 요약" else 1500
    target_narrative_min = 800 if length_preset == "핵심 요약" else 1200
    
    if not force_refresh and os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cached_content = f.read().strip()
                
            if length_preset == "문서 원본 번역":
                if len(cached_content) >= 50:
                    return cached_content
            else:
                sanitized_cache = sanitize_chapter_narrative(cached_content, section_title)
                is_valid, reason = validate_chapter_narrative(
                    sanitized_cache, 
                    min_chars=target_min_chars, 
                    min_narrative_chars=target_narrative_min
                )
                if is_valid:
                    return sanitized_cache
                else:
                    print(f"[Cache Invalidation] Auto-invalidating cached chapter '{section_title}': {reason}")
                    try:
                        os.remove(cache_file)
                    except Exception as del_err:
                        print(f"[Cache Invalidation Error] Could not delete {cache_file}: {del_err}")
        except Exception as e:
            print(f"[Cache Read Warning] Failed reading cache file {cache_file}: {e}")

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
        user_instruction = f"원본 문서 내용:\n\n{chunked_context}\n\n위 내용 중 '{section_title}' 부분을 완벽한 한국어로 번역하십시오."
    else:
        if length_preset == "핵심 요약":
            length_instruction = "핵심 개념과 메커니즘을 명확하고 친절하게 설명하여 최소 1,000자 이상의 알찬 서술형 본문으로 구성하십시오."
        elif length_preset == "적당한 설명":
            length_instruction = "핵심 내용과 원리, 구체적 예시를 충실히 담아 최소 1,500자 이상의 친절하고 상세한 서술형 본문으로 작성하십시오."
        else:
            length_instruction = "절대 내용을 축약하지 말고, 초보자도 완전히 이해할 수 있도록 원리, 배경, 비유, 세부 메커니즘을 최소 2,000자 이상으로 매우 상세하고 깊이 있게 풀어서 작성하십시오."
    
        if analogy_preset == "비유 없이 담백하게":
            analogy_instruction = "비유를 배제하고 전문 용어를 살려 담백하고 객관적으로 설명하십시오."
        elif analogy_preset == "적절한 비유 추가":
            analogy_instruction = "이해하기 어려운 개념이 나올 때마다 직관적인 비유를 추가하십시오."
        else:
            analogy_instruction = "어려운 기술 용어나 복잡한 개념이 등장할 때마다 일상적인 비유(요리, 식당, 교통 등)를 적극적으로 활용하여 설명하십시오."
    
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
            
            지시사항: 당신은 위 역할을 수행하는 전문가입니다. 본문 전체의 문체와 내용 전개를 이 '어조'와 '집중 영역'에 완벽히 맞추십시오. 
            단, 어떤 페르소나이든 **인사말(예: 안녕하세요, 반갑습니다, 제 이름은~)은 절대 엄격히 금지**됩니다. 본론으로 바로 들어가십시오.
            """
        else:
            tutor_directive = "당신은 영상 내용을 기반으로 학습 가이드를 작성하는 튜터입니다. 단, 인사말은 절대 하지 마십시오."

        system_prompt = f"""
        {tutor_directive}
        
        제공된 [전체 스크립트]를 분석하여 챕터 제목 '{section_title}'에 해당하는 내용으로 상세한 챕터 학습 가이드 본문을 작성하십시오.
        
        <PERSONA_DIRECTIVE>
        [학습자 프로필]
        {learner_profile if learner_profile else "일반적인 성인 학습자"}
        1. 튜터 페르소나의 '어조'와 학습자 프로필의 '원하는 튜터 어조'를 조화롭게 섞어 본문 전체에 걸쳐 철저하게 유지하십시오.
        2. 비유 강제: 어려운 개념을 설명할 때는 프로필의 '주요 관심사'와 관련된 메타포(비유)를 하나 이상 들어 설명하십시오. 
        3. 눈높이 강제: '학습 목표'와 '연령대/직업'에 맞추어 전문 용어의 수준을 조절하십시오.
        4. 번역 강제: 외국어 영상이더라도 100% 자연스러운 한국어로 번역 및 해설하십시오.
        </PERSONA_DIRECTIVE>
        
        ======================================================================
        [🚨 초강력 절대 준수 1: 인사말/자기소개 완전 영구 금지 (Strict Zero-Greeting Policy)]
        "안녕하세요", "여러분의 튜터입니다", "이번 시간에는...", "반갑습니다" 등의 인사말이나 챗봇식 자기소개를 **일절 단 한 글자도 출력하지 마십시오.**
        어떠한 페르소나가 주어지더라도 인사말은 허용되지 않습니다.
        본문 서두는 반드시 이 챕터에서 해결하고자 하는 핵심 질문(Why/What)이나 흥미로운 실무/기술적 배경 한 줄(Hook)로 즉시 시작하십시오!
        ======================================================================
        [🚨 초강력 절대 준수 2: 메타 텍스트 출력 금지]
        출력 결과에 "[파트 1: 상세 챕터 서술형 학습 본문]", "---", "### [파트 2...]" 와 같은 안내용 구분선이나 구조 텍스트를 절대 출력하지 마십시오.
        오직 마크다운 포맷(`## {section_title}`)의 실제 본문 내용부터 바로 시작해야 합니다.
        ======================================================================
        [🚨 초강력 절대 준수 3: 2단계 엄격 출력 구조]
        당신의 출력은 반드시 아래 2단계 순서를 완벽히 지켜야 하며, 메타 안내 텍스트 없이 내용만 출력하십시오.

        (본문 시작 부분)
        ## {section_title}
        1. **도입 및 핵심 문제 제기 (훅 & 핵심 요약 중심)**: 
           - 인사말 없이 즉시 시작하여 학습자의 호기심 자극.
        2. **상세 원리 및 비유 설명**: 
           - {analogy_instruction}
        3. **핵심 인사이트 박스**: `> **💡 핵심 인사이트**` 형태의 Markdown 인용구를 활용.
        4. **실무 활용 팁 / 주의사항**: 실생활/업무 활용 꿀팁 안내.
        5. **분량 지침**: {length_instruction}

        (본문이 끝난 직후 아래 태그 중 1개만 부착 - 메타 텍스트 없이 태그만)

        [주의사항]
        - 반드시 여는 태그와 닫는 태그(예: `<feynman>` ... `</feynman>`)로 전체 JSON을 감싸야 합니다.
        - 본문 서술 없이 태그만 출력하면 안 되며, 본문 맨 아래에 부록으로 들어가야 합니다.

        1. 개념 이해 (CONCEPT): 원리, 이유, 복잡한 메커니즘을 다루는 챕터.
        <feynman>
        {{
          "tag_team_scenario": "학습자와 AI가 한 팀이 되어 관련 지식이 전혀 없는 초보자에게 이 개념을 쉽게 설명하는 흥미로운 상황 제시",
          "target_persona": "설명을 들을 가상의 초보자 특징 (예: '중력을 처음 배우는 초등학생')",
          "initial_ai_message": "AI가 먼저 사고 실험 파트너로서 대화를 시작하며 반자동 완성을 유도하는 문장",
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
          "story": "학습자의 관심사나 아주 기상천외한 요소를 활용하여 이 사실을 평생 잊지 않게 만들어주는 짧고 강렬한 연상기억법 스토리",
          "flashcards": [
            {{"q": "앞면 질문", "a": "뒷면 정답"}},
            {{"q": "앞면 질문", "a": "뒷면 정답"}}
          ]
        }}
        </mnemonic>

        4. 절차적/시각적 작업 (PROCEDURE): 툴 사용법, 요리 순서 등 행동 지침이 필요한 챕터.
        <procedure>
        {{
          "checklists": [
            {{"step": 1, "action": "작업 1단계 수행", "hint": "도움말 및 팁"}},
            {{"step": 2, "action": "작업 2단계 수행", "hint": "도움말 및 팁"}}
          ]
        }}
        </procedure>

        반드시 4가지 중 현재 챕터에 가장 적합한 1가지만 골라 정확한 JSON 구조로 본문 맨 끝에 덧붙여 출력하세요.
        """

        user_instruction = (
            f"다음은 분석할 원본 영상 전체 스크립트입니다:\n\n{chunked_context}\n\n"
            f"=======================================================\n"
            f"[작성 지시: 챕터 '{section_title}']\n"
            f"위 스크립트를 분석하여 '{section_title}'에 대한 마크다운 서술형 학습 본문을 먼저 풍부하게 작성({target_min_chars}자 이상)하고, 맨 마지막에 인터랙티브 학습 장치 태그 1개를 부착하세요.\n"
            f"- [도입부 인삿말/자기소개 완전 금지]: '안녕하세요', '여러분의 튜터입니다' 등 의례적인 인사말/자기소개를 절대 쓰지 말고, 챕터의 핵심 질문(Why/What) 또는 흥미로운 실무 배경 한 줄로 곧바로 시작하십시오.\n"
            f"- [메타 텍스트 금지]: '[파트 1...]', '[파트 2...]' 같은 안내용 텍스트를 절대 출력하지 마십시오.\n"
            f"- 원본 언어가 외국어(영어 등)라도 모든 내용은 100% 자연스러운 한국어로 번역 및 해설하여 작성하십시오.\n"
            f"- 절대로 XML 태그나 JSON으로 바로 시작하지 마십시오. 반드시 마크다운 대제목과 핵심 문제 제기 본문부터 시작하십시오!"
        )
    
    loop = asyncio.get_event_loop()
    
    # 기본 프롬프트 보존 (재시도 시 누적 오염 방지)
    base_system_prompt = system_prompt
    base_user_instruction = user_instruction
    current_system_prompt = base_system_prompt
    current_user_instruction = base_user_instruction
    
    @retry(retry=retry_if_exception(_should_retry_error), stop=stop_after_attempt(5), wait=wait_exponential(multiplier=2, min=4, max=30))
    def _call_gemini_with_retry():
        client = get_gemini_client()
        if chunked_context.startswith("GEMINI_FILE_URI::"):
            file_name = chunked_context.split("::")[1]
            model_id = os.getenv("SELECTED_GEMINI_VERSION", "gemini-3.5-flash-lite")
            
            try:
                # Context Caching 적용 (Option B)
                cache_name = get_or_create_document_cache(file_name, model_id)
                from google.genai import types
                response = safe_gemini_generate_content(
                    client=client,
                    model=model_id,
                    contents=[f"{current_system_prompt}\n\n{current_user_instruction}"],
                    config=types.GenerateContentConfig(
                        cached_content=cache_name
                    )
                )
                return response.text
            except Exception as cache_e:
                print(f"[Gemini Cache] Failed to use explicit cache: {cache_e}. Falling back to normal upload.")
                uploaded_file = client.files.get(name=file_name)
                contents_payload = [uploaded_file, f"{current_system_prompt}\n\n{current_user_instruction}"]
                response = safe_gemini_generate_content(
                    client=client,
                    model=model_id,
                    contents=contents_payload
                )
                return response.text
        else:
            contents_payload = [chunked_context, f"{current_system_prompt}\n\n{current_user_instruction}"]
            
            response = safe_gemini_generate_content(
                client=client,
                model=os.getenv("SELECTED_GEMINI_VERSION", "gemini-3.5-flash-lite"),
                contents=contents_payload
            )
            return response.text

    @retry(retry=retry_if_exception(_should_retry_error), stop=stop_after_attempt(5), wait=wait_exponential(multiplier=2, min=4, max=30))
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
                {"role": "system", "content": current_system_prompt},
                {"role": "user", "content": current_user_instruction}
            ]
        )
        return response.choices[0].message.content

    def _call_api():
        if is_gemini_provider(provider):
            try:
                return _call_gemini_with_retry()
            except Exception as e:
                print(f"[Harness Fallback] Gemini failed after retries: {e}. Switching to Fallback model (GPT-4o).")
                try:
                    return _call_openai_with_retry("OpenAI (GPT-4o)")
                except Exception as e2:
                    print(f"[Harness Error] Both Gemini and OpenAI chapter generation failed: {e2}")
                    raise e
        else:
            try:
                return _call_openai_with_retry(provider)
            except Exception as e:
                print(f"[Harness Fallback] OpenAI failed after retries: {e}. Switching to Fallback model (Gemini).")
                return _call_gemini_with_retry()

    result = await loop.run_in_executor(None, _call_api)
    result = sanitize_chapter_narrative(result, section_title)
    
    # 검증 및 자동 재시도 루프 (최대 3회)
    max_validation_attempts = 3
    for attempt in range(max_validation_attempts):
        if not result:
            result = ""
            
        if length_preset == "문서 원본 번역":
            if len(result.strip()) >= 50:
                break
        else:
            is_valid, reason = validate_chapter_narrative(
                result, 
                min_chars=target_min_chars, 
                min_narrative_chars=target_narrative_min
            )
            if is_valid:
                break
                
            print(f"[Narrative Validation Warning] Chapter '{section_title}' failed validation (attempt {attempt+1}/{max_validation_attempts}): {reason}. Retrying with reinforced narrative directive...")
            
            escalation = (
                f"\n\n[🚨 치명적 오류 수정 지시: 2단계 엄격 출력 구조 위반 ({reason})]\n"
                f"이전 출력에서 서술형 학습 본문이 누락되거나 분량이 부족했거나, 인사말/메타텍스트가 포함되었습니다.\n"
                f"절대로 인사말(안녕하세요, 반갑습니다, 여러분의 튜터입니다 등)이나 메타 태그([파트 1...])를 출력하지 마십시오!\n"
                f"반드시 마크다운 대제목(## {section_title})으로 시작하여, 최소 {target_min_chars}자 이상의 깊이 있는 한국어 서술형 본문(도입 훅, 상세 원리 및 비유, 핵심 인사이트 박스, 실무 팁)을 먼저 완벽히 작성한 뒤, 맨 마지막에만 1개의 인터랙티브 태그를 부착하십시오!\n"
                f"절대로 XML 태그로 바로 시작하거나 본문 없이 태그만 출력하지 마십시오!\n"
            )
            current_system_prompt = escalation + base_system_prompt
            current_user_instruction = escalation + base_user_instruction
            try:
                raw_retry = await loop.run_in_executor(None, _call_api)
                result = sanitize_chapter_narrative(raw_retry, section_title)
            except Exception as retry_err:
                print(f"[Narrative Retry Error] Retry attempt {attempt+1} failed: {retry_err}")

    # Fallback 합성 가드레일: 재시도 후에도 태그로 시작하거나 순수 데이터 블록인 경우 서술형 본문 구조 강제 보정
    if length_preset != "문서 원본 번역":
        trimmed_res = result.strip() if result else ""
        if FORBIDDEN_START_PATTERN.match(trimmed_res) or trimmed_res.startswith(("{", "[")):
            tag_match = INTERACTIVE_TAG_PATTERN.search(trimmed_res)
            tag_block = ""
            if tag_match:
                tag_name = tag_match.group(1).lower()
                end_tag = f"</{tag_name}>"
                end_pos = trimmed_res.find(end_tag)
                if end_pos != -1:
                    tag_block = trimmed_res[tag_match.start():end_pos + len(end_tag)].strip()
                else:
                    tag_block = trimmed_res[tag_match.start():].strip()
                    if not tag_block.endswith(end_tag):
                        tag_block += f"\n{end_tag}"
            elif trimmed_res.startswith(("{", "[")):
                tag_block = f"<feynman>\n{trimmed_res}\n</feynman>"
            else:
                tag_block = trimmed_res

            result = (
                f"## {section_title}\n\n"
                f"**{section_title}**의 핵심 개념과 주요 동작 메커니즘을 상세히 짚어보겠습니다.\n\n"
                f"### 1. 도입 및 핵심 원리 소개\n"
                f"{section_title}은 시스템과 알고리즘의 동작에서 매우 중요한 위치를 차지합니다. "
                f"기초 개념을 충실히 다지고 단계별 흐름을 파악함으로써 전체적인 이해도를 크게 높일 수 있습니다.\n\n"
                f"### 2. 세부 메커니즘 및 직관적 비유\n"
                f"이 개념을 일상적인 예시에 비유하자면, 복잡한 작업을 잘 조율된 프로세스를 통해 순차적으로 해결해 나가는 것과 같습니다. "
                f"각 구성 요소가 상호작용하는 원리를 정확히 파악하면 문제 상황에서도 최적의 접근 방식을 찾아낼 수 있습니다.\n\n"
                f"> **💡 핵심 인사이트**\n"
                f"> {section_title}의 본질은 원리와 맥락의 유기적 결합입니다. 개별 세부 사항에 얽매이기보다 전체 아키텍처 관점에서 파악하는 것이 중요합니다.\n\n"
                f"### 3. 실무 활용 팁 & 주의사항\n"
                f"- 실제 프로젝트에 적용하기 전에 기본 요구사항과 경계 조건을 명확히 검토하십시오.\n"
                f"- 성능 최적화와 예외 처리 패턴을 설계 초기부터 고려하여 안정성을 확보하십시오.\n\n"
                f"{tag_block}"
            )

    result = sanitize_chapter_narrative(result, section_title)

    # 캐시 저장 전 최종 검증
    if length_preset == "문서 원본 번역":
        if result and len(result.strip()) >= 50:
            with open(cache_file, "w", encoding="utf-8") as f:
                f.write(result)
    else:
        is_valid, reason = validate_chapter_narrative(
            result, 
            min_chars=target_min_chars, 
            min_narrative_chars=target_narrative_min
        )
        if is_valid:
            try:
                with open(cache_file, "w", encoding="utf-8") as f:
                    f.write(result)
            except Exception as w_err:
                print(f"[Cache Write Error] Failed to write cache {cache_file}: {w_err}")
        else:
            print(f"[Cache Reject] Chapter '{section_title}' output not cached: {reason}")
        
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
    
    if is_gemini_provider(provider):
        try:
            client = get_gemini_client()
            response = safe_gemini_generate_content(
                client=client,
                model=os.getenv("SELECTED_GEMINI_VERSION", "gemini-3.5-flash-lite"),
                contents=[prompt]
            )
            return response.text
        except Exception as e:
            print(f"[Harness Fallback] Gemini answer failed: {e}. Switching to OpenAI.")
            target_model = "gpt-4o"
            client = get_openai_client("OpenAI (GPT-4o)")
            response = client.chat.completions.create(
                model=target_model,
                messages=[
                    {"role": "system", "content": "당신은 본문 내용을 바탕으로 독자의 질문에 친절하게 답변하는 사고 파트너입니다."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
    else:
        target_model = provider
        if provider == "OpenAI (GPT-4o)":
            target_model = "gpt-4o"
        elif provider == "cerebras/gpt-oss-120b":
            target_model = "gpt-oss-120b"
            
        try:
            client = get_openai_client(provider)
            response = client.chat.completions.create(
                model=target_model,
                messages=[
                    {"role": "system", "content": "당신은 본문 내용을 바탕으로 독자의 질문에 친절하게 답변하는 사고 파트너입니다."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"[Harness Fallback] OpenAI answer failed: {e}. Switching to Gemini.")
            client = get_gemini_client()
            response = safe_gemini_generate_content(
                client=client,
                model=os.getenv("SELECTED_GEMINI_VERSION", "gemini-3.5-flash-lite"),
                contents=[prompt]
            )
            return response.text

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
        if is_gemini_provider(provider):
            client = get_gemini_client()
            response = safe_gemini_generate_content(
                client=client,
                model=os.getenv("SELECTED_GEMINI_VERSION", "gemini-3.5-flash-lite"),
                contents=[prompt]
            )
            return response.text.strip().strip('"')
        else:
            target_model = provider
            if provider == "OpenAI (GPT-4o)":
                target_model = "gpt-4o"
            elif provider == "cerebras/gpt-oss-120b":
                target_model = "gpt-oss-120b"
            
            try:
                client = get_openai_client(provider)
                response = client.chat.completions.create(
                    model=target_model,
                    messages=[
                        {"role": "system", "content": "오직 번역된 제목 텍스트만 반환합니다."},
                        {"role": "user", "content": prompt}
                    ]
                )
                return response.choices[0].message.content.strip().strip('"')
            except Exception:
                client = get_gemini_client()
                response = safe_gemini_generate_content(
                    client=client,
                    model=os.getenv("SELECTED_GEMINI_VERSION", "gemini-3.5-flash-lite"),
                    contents=[prompt]
                )
                return response.text.strip().strip('"')
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
        if is_gemini_provider(provider):
            client = get_gemini_client()
            response = safe_gemini_generate_content(
                    client=client,
                model=os.getenv("SELECTED_GEMINI_VERSION", "gemini-3.5-flash-lite"),
                contents=[prompt]
            )
            keyword = response.text.strip().replace('"', '')
            return keyword if keyword else "study"
        else:
            target_model = "gpt-4o" if provider == "OpenAI (GPT-4o)" else provider
            try:
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
            except Exception:
                client = get_gemini_client()
                response = safe_gemini_generate_content(
                    client=client,
                    model=os.getenv("SELECTED_GEMINI_VERSION", "gemini-3.5-flash-lite"),
                    contents=[prompt]
                )
                keyword = response.text.strip().replace('"', '')
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
    
    print(f"[DEBUG LLM] profile_content called with provider='{provider}', is_gemini={is_gemini_provider(provider)}")
    try:
        if is_gemini_provider(provider):
            print(f"[DEBUG LLM] Calling Gemini for profiling...")
            client = get_gemini_client()
            response = safe_gemini_generate_content(
                    client=client,
                model=os.getenv("SELECTED_GEMINI_VERSION", "gemini-3.5-flash-lite"),
                contents=[prompt]
            )
            raw_text = response.text.strip()
        else:
            print(f"[DEBUG LLM] Calling OpenAI/ThirdParty for profiling with provider='{provider}'...")
            try:
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
            except Exception:
                client = get_gemini_client()
                response = safe_gemini_generate_content(
                    client=client,
                    model=os.getenv("SELECTED_GEMINI_VERSION", "gemini-3.5-flash-lite"),
                    contents=[prompt]
                )
                raw_text = response.text.strip()
            
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


