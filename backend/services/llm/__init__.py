"""
backend.services.llm 패키지
LLM 클라이언트, 캐시, 검증, 오디오, 아웃라인, 챕터 생성, 프로파일링 서브모듈을 통합 노출합니다.
"""

from backend.services.llm.clients import (
    safe_gemini_generate_content,
    get_gemini_client,
    is_gemini_provider,
    get_openai_client,
    FALLBACK_GEMINI_MODELS,
    _should_retry_error,
    _MAX_LLM_WORKERS,
    _llm_executor
)

from backend.services.llm.cache import (
    get_or_create_document_cache,
    clean_invalid_cached_chapters,
    _get_cache_dir
)

from backend.services.llm.validators import (
    sanitize_chapter_narrative,
    validate_chapter_narrative,
    INTERACTIVE_TAGS,
    INTERACTIVE_TAG_PATTERN,
    FORBIDDEN_START_PATTERN
)

from backend.services.llm.audio import (
    process_audio,
    _split_audio_if_needed
)

from backend.services.llm.outline import (
    generate_outline
)

from backend.services.llm.chapter import (
    async_generate_chapter_content
)

from backend.services.llm.profiling import (
    generate_answer,
    translate_title,
    extract_image_keyword,
    profile_content
)

__all__ = [
    "safe_gemini_generate_content",
    "get_gemini_client",
    "is_gemini_provider",
    "get_openai_client",
    "FALLBACK_GEMINI_MODELS",
    "_should_retry_error",
    "_MAX_LLM_WORKERS",
    "_llm_executor",
    "get_or_create_document_cache",
    "clean_invalid_cached_chapters",
    "_get_cache_dir",
    "sanitize_chapter_narrative",
    "validate_chapter_narrative",
    "INTERACTIVE_TAGS",
    "INTERACTIVE_TAG_PATTERN",
    "FORBIDDEN_START_PATTERN",
    "process_audio",
    "_split_audio_if_needed",
    "generate_outline",
    "async_generate_chapter_content",
    "generate_answer",
    "translate_title",
    "extract_image_keyword",
    "profile_content"
]
