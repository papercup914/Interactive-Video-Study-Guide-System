import os
import time
import re
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Any
from google import genai
from backend.config import settings

# LLM 비동기 작업을 위한 전용 Bounded ThreadPool (무제한 스레드 생성 DoS 방지)
_MAX_LLM_WORKERS = max(4, int(os.getenv("CHAPTER_GENERATION_CONCURRENCY", str(settings.chapter_generation_concurrency))) * 2)
_llm_executor = ThreadPoolExecutor(max_workers=_MAX_LLM_WORKERS, thread_name_prefix="llm_bounded_worker")

def _should_retry_error(exception: BaseException) -> bool:
    """인증 오류, 결제/크레딧 부족(402), 404(모델 없음), 설정 누락, 타임아웃은 재시도하지 않고 즉시 Fallback으로 넘깁니다."""
    err_str = str(exception).lower()
    non_retry_keywords = (
        "authentication", "401", "api_key", "invalid_api_key", "incorrect api key",
        "404", "not_found", "model not found", "unsupported",
        "402", "payment_required", "insufficient_quota", "credit_balance_exhausted", "billing",
        "readtimeout", "connecttimeout", "timed out", "timeout"
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
    3) 타임아웃 발생 시 현재 모델에서 무한 대기하지 않고 다음 가용 모델로 즉시 전환합니다.
    """
    target_model = model or settings.selected_gemini_version or "gemini-3.5-flash-lite"
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
                is_timeout = "timeout" in err_str_lower or "timed out" in err_str_lower or "readtimeout" in err_str_lower
                
                if is_timeout:
                    print(f"[Gemini Timeout Fallback] Model '{current_model}' timed out -> Switching immediately to next candidate model...")
                    break
                
                if is_quota or is_unavailable:
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

def get_gemini_client(custom_api_key: Optional[str] = None):
    api_key = custom_api_key or settings.gemini_api_key or os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "여기에_GEMINI_API_키를_입력하세요":
        raise ValueError("GEMINI_API_KEY 환경 변수가 설정되지 않았습니다.")
    return genai.Client(api_key=api_key, http_options={"timeout": 45})

def is_gemini_provider(provider: str = None) -> bool:
    """주어진 provider 문자열이 Gemini 계열인지 확인합니다."""
    p = str(provider).lower().strip() if provider else ""
    if any(k in p for k in ("groq", "openrouter", "openai", "cerebras", "glm", "nvidia", "byok", "gpt", ":free")):
        return False
    if not provider:
        gemini_key = settings.gemini_api_key or os.getenv("GEMINI_API_KEY")
        alt_key = settings.groq_api_key or settings.openrouter_api_key or os.getenv("GROQ_API_KEY") or os.getenv("OPENROUTER_API_KEY")
        if not gemini_key and alt_key:
            return False
        return True
    return "gemini" in p or "google" in p or p == "default"

def get_openai_client(
    provider: str = None, 
    custom_api_key: Optional[str] = None, 
    custom_base_url: Optional[str] = None,
    timeout: float = 60.0
):
    """OpenAI 호환 API 클라이언트(Groq, OpenRouter, NVIDIA NIM, Cerebras, OpenAI, BYOK)를 생성합니다."""
    api_key = custom_api_key
    base_url = custom_base_url or settings.openai_base_url or os.getenv("OPENAI_BASE_URL")
    p_lower = str(provider).lower() if provider else ""
    
    if not api_key:
        if "groq" in p_lower:
            api_key = settings.groq_api_key or os.getenv("GROQ_API_KEY")
            base_url = base_url or "https://api.groq.com/openai/v1"
        elif "openrouter" in p_lower or ":free" in p_lower:
            api_key = settings.openrouter_api_key or os.getenv("OPENROUTER_API_KEY")
            base_url = base_url or "https://openrouter.ai/api/v1"
        elif provider == "cerebras/gpt-oss-120b":
            api_key = settings.cerebras_api_key or os.getenv("CEREBRAS_API_KEY")
            base_url = base_url or "https://api.cerebras.ai/v1"
        elif provider == "glm-5.2":
            api_key = settings.glm_api_key or os.getenv("GLM_API_KEY")
        elif "nemotron" in p_lower or "nvidia" in p_lower:
            api_key = settings.nemotron_3_ultra_api_key or settings.glm_api_key or os.getenv("NEMOTRON_3_ULTRA_API_KEY") or os.getenv("GLM_API_KEY")
            base_url = base_url or "https://integrate.api.nvidia.com/v1"
        elif (settings.openai_api_key or os.getenv("OPENAI_API_KEY")) and (settings.openai_api_key or os.getenv("OPENAI_API_KEY")) != "여기에_OPENAI_API_키를_입력하세요":
            api_key = settings.openai_api_key or os.getenv("OPENAI_API_KEY")
        else:
            if settings.openrouter_api_key or os.getenv("OPENROUTER_API_KEY"):
                api_key = settings.openrouter_api_key or os.getenv("OPENROUTER_API_KEY")
                base_url = base_url or "https://openrouter.ai/api/v1"
            elif settings.groq_api_key or os.getenv("GROQ_API_KEY"):
                api_key = settings.groq_api_key or os.getenv("GROQ_API_KEY")
                base_url = base_url or "https://api.groq.com/openai/v1"
            elif settings.nemotron_3_ultra_api_key or os.getenv("NEMOTRON_3_ULTRA_API_KEY"):
                api_key = settings.nemotron_3_ultra_api_key or os.getenv("NEMOTRON_3_ULTRA_API_KEY")
                base_url = base_url or "https://integrate.api.nvidia.com/v1"
            
    if not api_key:
        raise ValueError(f"{provider if provider else 'AI'} 모델을 위한 API 키가 설정되지 않았습니다. 개인 API Key를 입력하거나 .env 설정을 확인해주세요.")
    
    if not base_url and api_key.startswith("nvapi-"):
        base_url = "https://integrate.api.nvidia.com/v1"
    elif not base_url and api_key.startswith("gsk_"):
        base_url = "https://api.groq.com/openai/v1"
    elif not base_url and api_key.startswith("sk-or-"):
        base_url = "https://openrouter.ai/api/v1"
        
    try:
        import openai
        return openai.Client(api_key=api_key, base_url=base_url, timeout=timeout)
    except ImportError:
        raise ImportError("openai 패키지가 설치되지 않았습니다. pip install openai 를 실행하세요.")
