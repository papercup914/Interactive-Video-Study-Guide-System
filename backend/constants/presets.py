from typing import Optional

# 요약 분량 프리셋 상수 정의
LENGTH_PRESETS = ["핵심 요약", "적당한 설명", "아주 상세하게"]

# 설명 방식 프리셋 상수 정의
ANALOGY_PRESETS = ["비유 없이 담백하게", "적절한 비유 추가", "풍부한 비유"]

def normalize_length_preset(val: Optional[str]) -> str:
    """요약 분량 프리셋 문자열을 정규화합니다."""
    if not val:
        return "적당한 설명"
    v = val.strip().lower()
    if any(k in v for k in ["핵심", "basic", "short", "summary", "quick"]):
        return "핵심 요약"
    if any(k in v for k in ["상세", "deep", "detailed", "long"]):
        return "아주 상세하게"
    return "적당한 설명"

def normalize_analogy_preset(val: Optional[str]) -> str:
    """설명 방식 프리셋 문자열을 정규화합니다."""
    if not val:
        return "적절한 비유 추가"
    v = val.strip().lower()
    if any(k in v for k in ["담백", "academic", "none", "plain"]):
        return "비유 없이 담백하게"
    if any(k in v for k in ["풍부", "story", "rich", "feynman"]):
        return "풍부한 비유"
    return "적절한 비유 추가"

def extract_video_key(url: Optional[str], title: Optional[str]) -> str:
    """비디오 URL 또는 제목으로부터 그룹화용 고유 키를 추출합니다."""
    if not url:
        return (title or "unknown").strip().lower()
    try:
        from backend.services.video import extract_video_id
        vid = extract_video_id(url)
        if vid:
            return f"yt_{vid}"
    except Exception:
        pass
    return url.strip().lower()
