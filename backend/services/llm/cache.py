import os
from typing import Optional
from backend.services.llm.clients import get_gemini_client
from backend.services.llm.validators import validate_chapter_narrative

_gemini_cache_map = {}

def get_or_create_document_cache(file_name: str, model_id: str) -> str | None:
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
        try:
            uploaded_file = client.files.get(name=file_name)
        except Exception as file_err:
            print(f"[Gemini Cache] 원격 파일 '{file_name}' 조회 실패(만료 또는 미존재): {file_err}")
            _gemini_cache_map[file_name] = None
            raise FileNotFoundError(f"업로드된 원격 파일({file_name})이 만료되었거나 존재하지 않습니다.")
        
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

def _get_cache_dir() -> str:
    """캐시 디렉토리 절대 경로를 일관되게 반환합니다."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    cache_dir = os.path.join(base_dir, "data", "cache_chapters")
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir

def clean_invalid_cached_chapters(data_dir: Optional[str] = None) -> int:
    """
    기존 캐시 디렉토리를 전수 스캔하여, 1,000자 미만이거나 태그 단독 등
    2단계 서술형 구조를 위반하는 불량 캐시 파일들을 자동 영구 삭제(무효화)합니다.
    """
    dirs_to_clean = [data_dir] if data_dir else [_get_cache_dir()]
    
    # 중첩된 레거시 캐시 경로(backend/backend/data/cache_chapters)가 존재할 경우 함께 정리
    if not data_dir:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
