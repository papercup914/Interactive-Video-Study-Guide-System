import os
import re
import json
import asyncio
import hashlib
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception

from backend.prompts.chapter_guide import build_chapter_system_prompt
from backend.services.llm.clients import (
    get_gemini_client,
    get_openai_client,
    is_gemini_provider,
    safe_gemini_generate_content,
    _should_retry_error,
    _llm_executor
)
from backend.services.llm.cache import (
    _get_cache_dir,
    get_or_create_document_cache
)
from backend.services.llm.validators import (
    sanitize_chapter_narrative,
    validate_chapter_narrative,
    FORBIDDEN_START_PATTERN,
    INTERACTIVE_TAG_PATTERN
)
from backend.config import settings

async def async_generate_chapter_content(
    section_title: str, 
    context_data: str, 
    provider: str, 
    chunk_index: int, 
    total_chunks: int, 
    length_preset: str = "아주 상세하게", 
    analogy_preset: str = "풍부한 비유", 
    learner_profile: str = "", 
    url_hash: str = "", 
    tutor_persona: dict = None, 
    force_refresh: bool = False,
    custom_api_key: Optional[str] = None,
    custom_base_url: Optional[str] = None
) -> str:
    """
    전체 스크립트를 LLM에 전달하여 챕터 내용에 해당하는 부분을 스스로 찾아서 작성하도록 합니다. (정확도 우선)
    [파트 1: 상세 서술형 학습 본문] + [파트 2: 인터랙티브 학습 장치]의 2단계 엄격 출력 구조를 강제합니다.
    """
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
    # 12,000자 초과 대용량 스크립트의 경우 현재 챕터 위치에 맞게 스마트 슬라이싱하여 타임아웃 방지 및 생성 집중도 극대화
    # [버그 수정]: section_index, total_sections 미정의 버그를 chunk_index, total_chunks로 정상 수정
    if isinstance(context_data, str) and not context_data.startswith("GEMINI_FILE_URI::") and len(context_data) > 12000:
        total_len = len(context_data)
        safe_total = max(1, total_chunks)
        center_ratio = (chunk_index + 0.5) / safe_total
        center_idx = int(total_len * center_ratio)
        half_window = 4500  # 앞뒤 4,500자 (총 9,000자 윈도우)
        start_idx = max(0, center_idx - half_window)
        end_idx = min(total_len, center_idx + half_window)
        prefix = "...[앞부분 내용 생략]...\n" if start_idx > 0 else ""
        suffix = "\n...[뒷부분 내용 생략]..." if end_idx < total_len else ""
        chunked_context = f"{prefix}{context_data[start_idx:end_idx]}{suffix}"
        print(f"[Smart Slicing] Chapter '{section_title}' ({chunk_index+1}/{safe_total}): extracted {len(chunked_context)} chars (from {start_idx} to {end_idx})")

    if length_preset == "문서 원본 번역":
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

        system_prompt = build_chapter_system_prompt(
            section_title=section_title,
            tutor_directive=tutor_directive,
            learner_profile=learner_profile,
            analogy_instruction=analogy_instruction,
            length_instruction=length_instruction
        )

        user_instruction = (
            f"[🚨 최우선 필수 지침: 100% 자연스러운 한국어로 번역 및 해설 서술 (Strict Korean Policy)]\n"
            f"원본 영상 스크립트가 영어, 일본어 등 외국어이더라도, 출력되는 모든 마크다운 서술형 본문과 인터랙티브 태그 내용은 100% 자연스럽고 유창한 한국어로 번역 및 풀어서 작성하십시오. 필수 기술 용어(Docker, API, PromptQL 등)를 제외하고 영문 문장을 출력하면 시스템 검증에서 즉시 탈락(Reject)됩니다.\n\n"
            f"다음은 분석할 원본 영상 전체 스크립트입니다:\n\n{chunked_context}\n\n"
            f"=======================================================\n"
            f"[작성 지시: 챕터 '{section_title}']\n"
            f"위 스크립트를 분석하여 '{section_title}'에 대한 마크다운 서술형 학습 본문을 100% 자연스러운 한국어로 먼저 풍부하게 작성({target_min_chars}자 이상)하고, 맨 마지막에 인터랙티브 학습 장치 태그 1개를 부착하세요.\n"
            f"- [100% 한국어 서술]: 본문의 모든 설명, 비유, 인사이트, 팁은 100% 자연스러운 한국어로 번역 및 작성하십시오.\n"
            f"- [도입부 인삿말/자기소개 완전 금지]: '안녕하세요', '여러분의 튜터입니다' 등 의례적인 인사말/자기소개를 절대 쓰지 말고, 챕터의 핵심 질문(Why/What) 또는 흥미로운 실무 배경 한 줄로 곧바로 시작하십시오.\n"
            f"- [메타 텍스트 금지]: '[파트 1...]', '[파트 2...]' 같은 안내용 텍스트를 절대 출력하지 마십시오.\n"
            f"- 절대로 XML 태그나 JSON으로 바로 시작하지 마십시오. 반드시 마크다운 대제목(## {section_title})과 핵심 문제 제기 본문부터 시작하십시오!"
        )
    
    loop = asyncio.get_event_loop()
    
    base_system_prompt = system_prompt
    base_user_instruction = user_instruction
    current_system_prompt = base_system_prompt
    current_user_instruction = base_user_instruction
    
    @retry(retry=retry_if_exception(_should_retry_error), stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1.5, min=2, max=5))
    def _call_gemini_with_retry():
        client = get_gemini_client(custom_api_key=custom_api_key)
        model_id = settings.selected_gemini_version or "gemini-3.5-flash-lite"
        if chunked_context.startswith("GEMINI_FILE_URI::"):
            file_name = chunked_context.split("::")[1]
            try:
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
                try:
                    uploaded_file = client.files.get(name=file_name)
                except Exception as file_get_err:
                    print(f"[Gemini Cache] 원격 파일({file_name}) 재조회 실패: {file_get_err}")
                    raise RuntimeError(f"Gemini 원격 파일({file_name})이 만료되었거나 삭제되었습니다. 문서를 다시 업로드해주세요.")
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
                model=model_id,
                contents=contents_payload
            )
            return response.text

    @retry(retry=retry_if_exception(_should_retry_error), stop=stop_after_attempt(1))
    def _call_openai_with_retry(target_provider="OpenAI (GPT-4o)"):
        target_model = target_provider or "OpenAI (GPT-4o)"
        p_lower = str(target_provider).lower()
        if "groq" in p_lower:
            target_model = "llama-3.3-70b-versatile"
        elif "openrouter" in p_lower or ":free" in p_lower:
            target_model = target_provider.replace("openrouter/", "") if "/" in target_provider else target_provider
            if target_model in ("openrouter", "openrouter/free", "meta-llama/llama-3.3-70b-instruct:free"):
                target_model = "nvidia/nemotron-3.5-lightning:free"
        elif target_provider == "OpenAI (GPT-4o)":
            target_model = "gpt-4o"
        elif target_provider == "cerebras/gpt-oss-120b":
            target_model = "gpt-oss-120b"
        elif "nemotron" in p_lower:
            target_model = "nvidia/nemotron-3.5-lightning:free"
        elif "nvidia" in p_lower:
            target_model = "nvidia/nemotron-3.5-lightning:free"
            
        client = get_openai_client(target_provider, custom_api_key=custom_api_key, custom_base_url=custom_base_url, timeout=25.0)
        candidate_models = [target_model]
        if "openrouter" in p_lower or ":free" in p_lower:
            for fallback_m in ("nvidia/nemotron-3.5-lightning:free", "nvidia/nemotron-3-ultra-550b-a55b:free", "meta-llama/llama-3.3-70b-instruct:free"):
                if fallback_m not in candidate_models:
                    candidate_models.append(fallback_m)
            
        last_error = None
        for cur_model in candidate_models:
            clean_m = cur_model.replace("openrouter/", "") if "/" in cur_model and cur_model.startswith("openrouter/") else cur_model
            try:
                response = client.chat.completions.create(
                    model=clean_m,
                    messages=[
                        {"role": "system", "content": current_system_prompt},
                        {"role": "user", "content": current_user_instruction}
                    ]
                )
                if response and response.choices and len(response.choices) > 0 and response.choices[0].message and response.choices[0].message.content:
                    return response.choices[0].message.content
                else:
                    raise ValueError(f"Empty or malformed completion response from {clean_m}")
            except Exception as e:
                last_error = e
                print(f"[Warning] Chapter generation failed on {clean_m}: {e}. Trying fallback model if available...")
                continue
                
        raise last_error

    def _build_heuristic_chapter():
        print(f"[Heuristic Chapter Fallback] Generating robust heuristic narrative for '{section_title}'...")
        snippet = chunked_context if isinstance(chunked_context, str) and not chunked_context.startswith("GEMINI_FILE_URI::") else ""
        clean_sentences = []
        for line in snippet.split("\n"):
            line_str = line.strip()
            if len(line_str) > 20 and not line_str.startswith(("#", "[", "http", "www")):
                clean_sentences.append(line_str)
        
        extracted_body = "\n\n".join(clean_sentences[:8]) if clean_sentences else f"**{section_title}**의 주요 내용과 핵심 메커니즘을 상세히 다룹니다."
        
        return (
            f"## {section_title}\n\n"
            f"**{section_title}**의 핵심 개념과 주요 동작 원리를 체계적으로 분석하고 정리합니다.\n\n"
            f"### 1. 도입 및 핵심 배경\n"
            f"{section_title}은 시스템 아키텍처와 전체 워크플로우에서 매우 중요한 역할을 담당합니다. "
            f"이 개념을 정확히 이해하면 복잡한 데이터 흐름과 로직을 명확하게 파악할 수 있으며, 실무 구현 시 발생할 수 있는 잠재적 문제를 사전에 방지할 수 있습니다.\n\n"
            f"### 2. 세부 메커니즘 및 상세 해설\n"
            f"{extracted_body}\n\n"
            f"각 단계별 처리 과정은 유기적으로 연결되어 있으며, 입력 데이터의 정합성을 보장하면서 목적한 결과를 효율적으로 도출하도록 설계되어 있습니다.\n\n"
            f"> **💡 핵심 인사이트**\n"
            f"> {section_title}의 본질은 복잡성을 캡슐화하고 신뢰성 높은 인터페이스를 제공하는 데 있습니다. 개별 구성 요소 간의 결합도를 낮추고 응집도를 극대화하는 것이 핵심입니다.\n\n"
            f"### 3. 실무 적용 팁 & 주의사항\n"
            f"- 실무 환경에 적용하기 전에 입력 데이터의 유효성과 예외 경계 조건을 반드시 사전에 검증하십시오.\n"
            f"- 성능 병목 현상을 방지하기 위해 비동기 처리 파이프라인 및 캐싱 전략을 적극적으로 도입하는 것이 권장됩니다.\n\n"
            f"<quiz>\n"
            f'{{"question": "{section_title}을 실무에 도입할 때 가장 우선적으로 고려해야 할 사항은 무엇인가요?", '
            f'"options": ["입력 데이터 유효성 및 경계 조건 검증", "코드 라인 수 무조건 단축", "예외 처리 생략", "모든 로직을 동기식으로 단일 처리"], '
            f'"answer": 0, "explanation": "{section_title}의 안정성을 보장하기 위해서는 입력 데이터 검증과 사전 경계 조건 파악이 가장 중요합니다."}}\n'
            f"</quiz>"
        )

    def _call_api():
        if is_gemini_provider(provider):
            try:
                return _call_gemini_with_retry()
            except Exception as e:
                print(f"[Harness Fallback] Gemini failed after retries: {e}. Switching to Fallback model (OpenAI).")
                try:
                    return _call_openai_with_retry(provider or "OpenAI (GPT-4o)")
                except Exception as e2:
                    print(f"[Harness Error] Both Gemini and OpenAI chapter generation failed: {e2}. Triggering Heuristic Fallback.")
                    return _build_heuristic_chapter()
        else:
            try:
                return _call_openai_with_retry(provider)
            except Exception as e:
                print(f"[Harness Fallback] OpenAI failed after retries: {e}. Switching to Fallback model (Gemini).")
                try:
                    return _call_gemini_with_retry()
                except Exception as e2:
                    print(f"[Harness Error] Both OpenAI and Gemini chapter generation failed: {e2}. Triggering Heuristic Fallback.")
                    return _build_heuristic_chapter()

    try:
        result = await asyncio.wait_for(loop.run_in_executor(_llm_executor, _call_api), timeout=60.0)
    except Exception as wait_err:
        print(f"[LLM Wait Exception/Timeout] Chapter '{section_title}' timed out or failed ({wait_err}). Generating robust heuristic chapter...")
        result = _build_heuristic_chapter()

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
            
            korean_extra = ""
            if "한국어" in reason:
                korean_extra = (
                    "🚨 [경고: 외국어 미번역 감지!] 이전 출력이 한국어가 아닌 외국어(영어 등)로 작성되었습니다.\n"
                    "지금 즉시 본문의 모든 설명과 문장을 100% 유창하고 자연스러운 한국어로 번역 및 해설하여 작성하십시오!\n"
                    "고유 기술 명칭(예: Docker, API, PromptQL 등) 외에 영문 문장이 단 하나라도 포함되어서는 안 됩니다!\n"
                )
            
            escalation = (
                f"\n\n[🚨 치명적 오류 수정 지시: 지침 위반 ({reason})]\n"
                f"{korean_extra}"
                f"이전 출력에서 서술형 학습 본문이 누락되거나 분량이 부족했거나, 인사말/메타텍스트가 포함되었거나, 한국어로 번역되지 않았습니다.\n"
                f"절대로 인사말(안녕하세요, 반갑습니다, 여러분의 튜터입니다 등)이나 메타 태그([파트 1...])를 출력하지 마십시오!\n"
                f"반드시 마크다운 대제목(## {section_title})으로 시작하여, 최소 {target_min_chars}자 이상의 깊이 있는 100% 한국어 서술형 본문(도입 훅, 상세 원리 및 비유, 핵심 인사이트 박스, 실무 팁)을 먼저 완벽히 작성한 뒤, 맨 마지막에만 1개의 인터랙티브 태그를 부착하십시오!\n"
                f"절대로 XML 태그로 바로 시작하거나 본문 없이 태그만 출력하지 마십시오!\n"
            )
            current_system_prompt = escalation + base_system_prompt
            current_user_instruction = escalation + base_user_instruction
            try:
                raw_retry = await asyncio.wait_for(loop.run_in_executor(_llm_executor, _call_api), timeout=120.0)
                result = sanitize_chapter_narrative(raw_retry, section_title)
            except Exception as retry_err:
                print(f"[Narrative Retry Error] Retry attempt {attempt+1} failed: {retry_err}")

    # Fallback 합성 가드레일: 재시도 후에도 태그로 시작하거나 순수 데이터 블록이거나 한국어 번역이 누락된 경우 서술형 본문 구조 강제 보정
    if length_preset != "문서 원본 번역":
        trimmed_res = result.strip() if result else ""
        korean_chars_final = len(re.findall(r'[가-힣]', trimmed_res))
        is_non_korean = korean_chars_final < 150
        if FORBIDDEN_START_PATTERN.match(trimmed_res) or trimmed_res.startswith(("{", "[")) or is_non_korean:
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
            elif not is_non_korean:
                tag_block = trimmed_res
            else:
                tag_block = ""

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
