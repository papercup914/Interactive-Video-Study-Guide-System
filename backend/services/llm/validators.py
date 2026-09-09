import re

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

def sanitize_chapter_narrative(content: str, section_title: str = "") -> str:
    """
    LLM 출력물에서 시스템 메타 텍스트(예: [파트 1: ...]) 및 서두 인사말(예: 안녕하세요, 반갑습니다 등)을
    정규식으로 완벽히 제거하여 순수한 서술형 학습 본문으로 정제합니다.
    """
    if not content or not isinstance(content, str):
        return ""

    sanitized = content.strip()

    # 1. 시스템 메타 텍스트 태그 전역 제거
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
        
    # 3. 인터랙티브 태그 이전의 서술형 본문 분량 검증
    tag_match = INTERACTIVE_TAG_PATTERN.search(trimmed)
    if tag_match:
        tag_start_pos = tag_match.start()
        narrative_part = trimmed[:tag_start_pos].strip()
        if len(narrative_part) < min_narrative_chars:
            return False, f"인터랙티브 태그 이전의 서술형 본문 분량이 부족합니다 ({len(narrative_part)} < {min_narrative_chars}자)."
            
    # 4. 전체 길이 검증
    if len(trimmed) < min_chars:
        return False, f"출력 전체 길이가 너무 짧습니다 ({len(trimmed)} < {min_chars}자)."

    # 5. 한국어 서술 검증 (외국어 미번역 방지)
    korean_chars = len(re.findall(r'[가-힣]', trimmed))
    if korean_chars < 150:
        return False, f"한국어로 번역되지 않았거나 한글 서술이 절대적으로 부족합니다 (한글 글자 수: {korean_chars}자 < 150자)."
            
    return True, "유효한 서술형 본문 및 2단계 구조입니다."
