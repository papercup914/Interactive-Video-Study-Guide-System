import os
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
    custom_base_url: Optional[str] = None
) -> List[str]:
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
        유튜브 영상의 공식 챕터 정보가 주어집니다.
        다음 공식 챕터 제목들을 학습용 목차에 맞게 자연스럽고 명확한 한국어로 번역 및 정제해주세요.
        원래의 챕터 개수와 시간적 순서(Time Sequence)를 100% 엄격하게 동일하게 유지해야 합니다.
        
        - [중요] 각 목차 항목은 번호나 기호 없이 새로운 줄에 순수 한국어 제목만 하나씩 작성해줘.
        
        공식 챕터 제목:
        {chapter_text}
        """
        script_snippet = context_data[:2500].strip() if context_data else ""
        context_data = f"[영상 배경 및 내용 요약 발췌]\n{script_snippet}" if script_snippet else "영상 컨텍스트"
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
        """모든 AI API 호출이 실패하거나 타임아웃되었을 때 자막 텍스트 기반으로 3~5개 챕터를 자동 생성하는 안전망."""
        if not text or len(text.strip()) < 100:
            return ["영상 개요 및 핵심 개념", "핵심 내용 심층 분석", "최종 요약 및 결론"]
        
        # 텍스트 길이에 따라 3~5개 챕터 기본 구조 생성
        lines = [line.strip() for line in text.splitlines() if len(line.strip()) > 15]
        first_line = lines[0][:40] if lines else default_title
        
        return [
            f"도입 및 핵심 배경 ({first_line[:25]}...)",
            "핵심 원리와 메커니즘 분석",
            "실무 활용 전략 및 주요 사례",
            "핵심 요약과 향후 전망"
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
                target_model = "nvidia/nemotron-3.5-lightning:free"
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
        if "openrouter" in p_lower or ":free" in p_lower:
            for fallback_m in ("nvidia/nemotron-3.5-lightning:free", "nvidia/nemotron-3-ultra-550b-a55b:free", "meta-llama/llama-3.3-70b-instruct:free"):
                if fallback_m not in candidate_models:
                    candidate_models.append(fallback_m)
        
        last_error = None
        for cur_model in candidate_models:
            # openrouter 접두사가 남아있을 경우 제거
            clean_m = cur_model.replace("openrouter/", "") if "/" in cur_model and cur_model.startswith("openrouter/") else cur_model
            try:
                response = client.chat.completions.create(
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
                    response = client.chat.completions.create(
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
        clean_line = line.strip().lstrip('1234567890.-*# ')
        if clean_line:
            sections.append(clean_line)
            
    if not sections:
        print("[Outline Fallback] AI outline generation yielded no valid sections. Triggering Smart Heuristic Outline...")
        sections = _build_heuristic_sections(context_data)
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
