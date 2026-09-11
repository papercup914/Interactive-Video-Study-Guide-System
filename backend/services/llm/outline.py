import os
import re
import json
from typing import List, Optional
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception
from google.genai import types

from backend.services.llm.clients import (
    get_gemini_client,
    get_openai_client,
    is_gemini_provider,
    safe_gemini_generate_content,
    _should_retry_error
)
from backend.config import settings

def generate_outline(
    context_data: str, 
    provider: str, 
    url_hash: str, 
    length_preset: str = "아주 상세하게", 
    force_refresh: bool = False, 
    video_chapters: list = None,
    custom_api_key: Optional[str] = None,
    custom_base_url: Optional[str] = None,
    default_title: str = "학습 가이드"
) -> List[str]:
    """
    오디오 컨텍스트를 분석하여 상세 목차를 생성하고 로컬에 캐시합니다.
    """
    preset_suffix = "summary" if length_preset == "핵심 요약" else ("normal" if length_preset == "적당한 설명" else "detailed")
    cache_file = os.path.join("backend/data", f"{url_hash}_outline_{preset_suffix}.json")
    if not force_refresh and os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cached_sections = json.load(f)
            
            is_corrupted = False
            if not isinstance(cached_sections, list) or len(cached_sections) == 0:
                is_corrupted = True
            else:
                corrupted_keywords = ["그래서 오늘 저희", "마운틴뷰", "본사", "시스템 아키텍처와 전체 워크플로우"]
                for s in cached_sections:
                    if not isinstance(s, str) or "(" in s or ")" in s or any(kw in s for kw in corrupted_keywords):
                        is_corrupted = True
                        break
                
                # 원본 타임스탬프 챕터가 3개 이상 제공되었는데 캐시된 챕터 수가 일치하지 않는 경우
                if video_chapters and len(video_chapters) >= 3 and len(cached_sections) != len(video_chapters):
                    is_corrupted = True
                    
            if is_corrupted:
                print(f"[Outline Cache Invalidation] Corrupted or outdated outline cache found ({cache_file}). Purging and regenerating...")
                try:
                    os.remove(cache_file)
                except Exception:
                    pass
            else:
                return cached_sections
        except Exception as cache_err:
            print(f"[Outline Cache] Failed to load {cache_file}: {cache_err}. Purging and regenerating...")
            try:
                os.remove(cache_file)
            except Exception:
                pass

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
    
    if length_preset == "문서 원본 번역":
        if len(context_data) < 50000:
            return ["전체 문서"]
            
        for line in context_data.split("\n"):
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
        당신은 100만 지식 큐레이션 채널(예: BZCF 등)의 수석 콘텐츠 기획자입니다.
        유튜브 영상의 원작자가 등록한 공식 챕터 정보가 주어집니다.
        이 공식 챕터들을 독자가 흥미를 느끼고 핵심 교훈(Benefit)을 직관적으로 파악할 수 있도록
        감칠맛 나는 한국어 질문형/통찰형 챕터 제목으로 번역 및 각색해주세요.
        
        [작성 규칙]
        - 단순한 직역 대신, 시청자가 해당 파트에서 얻어갈 수 있는 '핵심 질문(Why/How)'이나 '인사이트'가 드러나도록 매력적으로 작성하세요.
          (예: "Why Today's Startups Are More Ambitious" -> "왜 지금 세대의 스타트업은 더 거대해졌는가?")
          (예: "What Actually Motivates Founders" -> "돈이 아닌 '이것'에 미친 사람만 창업해야 하는 이유")
        - 원래의 챕터 개수와 시간적 순서(Time Sequence)를 100% 엄격하게 동일하게 유지해야 합니다.
        - 각 목차 항목은 번호나 기호 없이 새로운 줄에 순수 한국어 제목만 하나씩 작성해줘.
        
        공식 챕터 제목:
        {chapter_text}
        """
        script_snippet = context_data[:2500].strip() if context_data else ""
        context_data = f"[영상 배경 및 내용 요약 발췌]\n{script_snippet}" if script_snippet else "영상 컨텍스트"
    else:
        prompt = f"""
        당신은 100만 지식 큐레이션 채널(예: BZCF 등)의 수석 콘텐츠 기획자입니다.
        주어진 내용(오디오 또는 스크립트)을 분석하여 학습용 목차(Outline)를 작성해줘.
        {outline_instruction}
        - [🚨 최우선 절대 준수: 시간 순서(Time Sequence) 엄격 유지]
          반드시 영상의 시작(도입/배경)부터 중간(핵심 내용/원리/실습), 끝(결론/마무리/전망) 순서대로 시간 흐름에 맞게 나열해야 합니다.
          절대로 '결론'이나 '마무리'가 1번이나 앞부분에 오거나, '도입'이나 '개요'가 뒷부분에 오는 역순(Inversion)으로 작성하지 마십시오!
        - [직관적 훅 챕터 지침]:
          '핵심 원리와 메커니즘 분석', '시스템 아키텍처' 같은 무미건조한 공학적 표현을 일괄 적용하지 마십시오.
          영상의 성격(비즈니스, 스타트업, 인문, 라이프, 기술 등)에 완벽히 맞추어, 
          독자의 지적 호기심을 자극하고 실질적 통찰을 제공하는 생생한 질문형/메시지형 챕터 제목을 작성하세요.
          (예: "비즈니스 모델의 3대 성공 공식", "위대한 파운더를 만드는 단 1가지 조건", "실전에 즉시 적용하는 4단계 액션 플랜")
        - [중요] 원본 스크립트가 외국어(영어 등)이더라도, 각 목차 항목의 제목은 반드시 자연스럽고 명확한 한국어로 번역하여 작성하세요.
        - 각 목차 항목은 번호나 기호 없이 새로운 줄에 순수 한국어 제목만 하나씩 작성해줘.
        """
    
    class OutlineSchema(BaseModel):
        sections: List[str] = Field(description="한국어로 작성된 목차 항목들의 리스트 (기호나 번호 없이 순수 한국어 제목만 포함)")

    @retry(retry=retry_if_exception(_should_retry_error), stop=stop_after_attempt(5), wait=wait_exponential(multiplier=2, min=4, max=30))
    def _call_gemini_outline():
        client = get_gemini_client(custom_api_key=custom_api_key)
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
            model=settings.selected_gemini_version or "gemini-3.5-flash-lite",
            contents=contents_payload,
            config=config
        )
        return response.text

    def _build_heuristic_sections(text: str, default_title: str = "학습 가이드") -> List[str]:
        """모든 AI API 호출이 실패하거나 타임아웃되었을 때 영상의 실제 주제어를 반영한 4개 표준 챕터를 자동 생성하는 안전망."""
        # 1. default_title에서 브래킷 태그 제거 및 핵심 주제어 추출
        raw_t = re.sub(r'\[.*?\]', '', default_title).strip()
        raw_t = re.sub(r'^[0-9]+[\.\s\-]+', '', raw_t).strip()
        # 하이픈, 콜론 등으로 구분된 구절 중 가장 의미 있는 토픽 구절 추출
        topic_parts = [p.strip() for p in re.split(r'[-:|–—]', raw_t) if len(p.strip()) >= 2]
        clean_topic = topic_parts[0] if topic_parts else "핵심 주제"
        if clean_topic in ("학습 가이드", "유튜브 학습 가이드", "AI 맞춤형 학습 가이드") or len(clean_topic) < 2:
            clean_topic = "핵심 주제와 문제의식"

        combined_text = (default_title + " " + (text[:1000] if text else "")).lower()
        
        # 2. 비즈니스 / 스타트업 / 마케팅 / 인터뷰 / 에세이 계열 감지
        biz_keywords = ["startup", "스타트업", "창업", "사업", "founder", "ambition", "vc", "yc", "투자", "비즈니스", "마케팅", "ceo", "경영", "돈", "성공", "인터뷰", "이야기", "철학"]
        if any(kw in combined_text for kw in biz_keywords):
            return [
                f"도입: {clean_topic}의 본질과 핵심 배경",
                f"{clean_topic}을 둘러싼 오해와 주요 실패 요인",
                f"{clean_topic}의 성공을 가르는 결정적 조건과 통찰",
                f"실전 적용: {clean_topic}을 위한 핵심 실천 전략"
            ]
            
        # 3. 기술 / 프로그래밍 / 개발 / 아키텍처 계열 감지
        tech_keywords = ["docker", "python", "api", "code", "개발", "코드", "서버", "아키텍처", "데이터", "프레임워크", "알고리즘", "인프라", "llm", "ai 모델"]
        if any(kw in combined_text for kw in tech_keywords):
            return [
                f"도입: {clean_topic}의 배경과 시스템 아키텍처",
                f"{clean_topic}의 핵심 동작 원리와 데이터 흐름",
                f"{clean_topic}의 실무 구현 전략과 장애 방지 가이드",
                f"최종 점검: {clean_topic} 최적화 체크리스트"
            ]
            
        # 4. 일반 교양 / 인문 / 라이프스타일 / 기타 보편형
        return [
            f"도입: {clean_topic}의 핵심 배경과 질문",
            f"{clean_topic}에 대한 심층 분석과 새로운 시각",
            f"{clean_topic}이 주는 일상과 실무의 시사점",
            f"핵심 요약: {clean_topic}의 미래 통찰"
        ]

    @retry(retry=retry_if_exception(_should_retry_error), stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1.5, min=2, max=10))
    def _call_openai_outline(target_provider="OpenAI (GPT-4o)"):
        target_model = target_provider or "OpenAI (GPT-4o)"
        p_lower = str(target_provider).lower()
        if "groq" in p_lower:
            target_model = "llama-3.3-70b-versatile"
        elif "openrouter" in p_lower or ":free" in p_lower:
            target_model = target_provider.replace("openrouter/", "") if "/" in target_provider else target_provider
            if target_model in ("openrouter", "openrouter/free", "meta-llama/llama-3.3-70b-instruct:free"):
                target_model = "google/gemma-4-26b-a4b-it:free"
        elif target_provider == "OpenAI (GPT-4o)":
            target_model = "gpt-4o"
        elif target_provider == "cerebras/gpt-oss-120b":
            target_model = "gpt-oss-120b"
        elif "nemotron" in p_lower:
            target_model = "nvidia/nemotron-3.5-lightning:free"
        elif "nvidia" in p_lower:
            target_model = "nvidia/nemotron-3.5-lightning:free"
            
        client = get_openai_client(target_provider, custom_api_key=custom_api_key, custom_base_url=custom_base_url, timeout=35.0)
        
        trimmed_context = context_data
        if len(context_data) > 10000:
            mid_idx = len(context_data) // 2
            trimmed_context = (
                context_data[:3500] + 
                "\n\n[... 중간 내용 발췌 ...]\n\n" + 
                context_data[mid_idx-1500:mid_idx+1500] + 
                "\n\n[... 후반부 내용 발췌 ...]\n\n" + 
                context_data[-3500:]
            )
        
        candidate_models = [target_model]
        # OpenRouter 무료 고성능 모델들을 항상 백업 폴백으로 대기
        for fallback_m in (
            "google/gemma-4-26b-a4b-it:free",
            "nex-agi/nex-n2.5-pro:free",
            "nex-agi/nex-n2.5-mini:free",
            "nvidia/nemotron-3.5-lightning:free",
            "google/gemma-4-31b-it:free"
        ):
            if fallback_m not in candidate_models:
                candidate_models.append(fallback_m)
        
        last_error = None
        for cur_model in candidate_models:
            clean_m = cur_model.replace("openrouter/", "") if "/" in cur_model and cur_model.startswith("openrouter/") else cur_model
            # 모델에 따른 OpenRouter 전용 클라이언트 분기 (타 엔드포인트 base_url 간섭 원천 차단)
            if ":free" in cur_model or "openrouter" in cur_model:
                cur_client = get_openai_client("openrouter", custom_api_key=custom_api_key, custom_base_url=None, timeout=35.0)
            else:
                cur_client = client
                
            try:
                response = cur_client.chat.completions.create(
                    model=clean_m,
                    messages=[
                        {"role": "system", "content": prompt + "\n반드시 JSON 형식 ({\"sections\": [\"챕터1\", \"챕터2\", ...]})으로만 출력해줘."},
                        {"role": "user", "content": f"다음은 영상 스크립트 내용입니다:\n\n{trimmed_context}"}
                    ],
                    response_format={"type": "json_object"}
                )
                return response.choices[0].message.content
            except Exception as e:
                last_error = e
                try:
                    response = cur_client.chat.completions.create(
                        model=clean_m,
                        messages=[
                            {"role": "system", "content": prompt + "\n반드시 마크다운 코드블록 없이 순수 JSON 형식 ({\"sections\": [\"챕터1\", \"챕터2\", ...]})으로만 출력해줘."},
                            {"role": "user", "content": f"다음은 영상 스크립트 내용입니다:\n\n{trimmed_context}"}
                        ]
                    )
                    return response.choices[0].message.content
                except Exception as inner_e:
                    last_error = inner_e
                    print(f"[Warning] Outline generation failed on {clean_m}: {inner_e}. Trying fallback model if available...")
                    continue
                    
        raise last_error

    outline_raw = "{}"
    if is_gemini_provider(provider):
        try:
            outline_raw = _call_gemini_outline()
        except Exception as e:
            print(f"[Harness Fallback] Gemini failed outline generation: {e}. Switching to OpenAI.")
            try:
                outline_raw = _call_openai_outline(provider or "OpenAI (GPT-4o)")
            except Exception as e2:
                print(f"[Harness Error] Both Gemini and OpenAI outline failed: {e2}")
                outline_raw = "{}"
    else:
        try:
            outline_raw = _call_openai_outline(provider)
        except Exception as e:
            print(f"[Harness Fallback] OpenAI outline failed: {e}. Switching to Gemini Fallback.")
            try:
                outline_raw = _call_gemini_outline()
            except Exception as e2:
                print(f"[Harness Error] Both OpenAI and Gemini outline failed: {e2}")
                outline_raw = "{}"
        
    try:
        parsed_json = json.loads(outline_raw)
        raw_sections = parsed_json.get("sections", [])
    except Exception as e:
        print(f"[Harness Error] Failed to parse structured output: {e}")
        raw_sections = []
        
    for line in raw_sections:
        clean_line = re.sub(r'^\s*(?:\d+[\.\-\)\:]\s*|[\*\#\-\s]+)', '', line).strip()
        if clean_line:
            sections.append(clean_line)
            
    if not sections:
        print("[Outline Fallback] AI outline generation yielded no valid sections. Triggering Smart Heuristic Outline...")
        sections = _build_heuristic_sections(context_data, default_title=default_title)
    else:
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
