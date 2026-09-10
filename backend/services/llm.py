"""
backend.services.llm - 하위 호환성을 위한 파사드(Facade) 모듈
실제 기능 단위 구현은 backend.services.llm/ 패키지의 각 모듈로 분리되었습니다:
- clients.py: API 클라이언트 및 재시도 설정
- cache.py: 챕터 캐시 및 컨텍스트 캐시 관리
- validators.py: 챕터 텍스트 살균 및 유효성 검증
- audio.py: 오디오 전사 및 청킹
- outline.py: 목차 생성
- chapter.py: 챕터 본문 비동기 생성 및 가드레일
- profiling.py: 프로파일링, 제목 번역, 키워드 추출, Q&A
"""

from backend.services.llm import (
    safe_gemini_generate_content,
    get_gemini_client,
    is_gemini_provider,
    get_openai_client,
    FALLBACK_GEMINI_MODELS,
    _should_retry_error,
    _MAX_LLM_WORKERS,
    _llm_executor,
    get_or_create_document_cache,
    clean_invalid_cached_chapters,
    clean_invalid_cached_outlines,
    _get_cache_dir,
    sanitize_chapter_narrative,
    validate_chapter_narrative,
    INTERACTIVE_TAGS,
    INTERACTIVE_TAG_PATTERN,
    FORBIDDEN_START_PATTERN,
    process_audio,
    _split_audio_if_needed,
    generate_outline,
    async_generate_chapter_content,
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
    "clean_invalid_cached_outlines",
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
