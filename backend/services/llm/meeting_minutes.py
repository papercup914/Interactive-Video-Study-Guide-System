"""
오디오 전사 대본 기반 전문 회의록(Meeting Minutes) 생성 서비스
"""

import os
import re
from typing import Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception
from google.genai import types

from backend.prompts.meeting_minutes import build_meeting_minutes_system_prompt
from backend.services.llm.clients import (
    get_gemini_client,
    get_openai_client,
    is_gemini_provider,
    safe_gemini_generate_content,
    _should_retry_error
)
from backend.config import settings

def generate_meeting_minutes_content(
    transcript: str,
    provider: str,
    raw_title: str = "",
    custom_api_key: Optional[str] = None,
    custom_base_url: Optional[str] = None
) -> Dict[str, str]:
    """
    오디오 전사 텍스트를 분석하여 5대 핵심 회의록 섹션 및 원문 전사본으로 구성된
    구조화된 딕셔너리를 반환합니다.
    """
    if not transcript or not transcript.strip():
        raise ValueError("전사된 음성 텍스트가 비어 있어 회의록을 생성할 수 없습니다.")

    system_prompt = build_meeting_minutes_system_prompt(raw_title=raw_title)
    
    # 너무 긴 텍스트(토큰 초과 방지)를 대비해 최대 40,000자로 제한
    trimmed_transcript = transcript[:40000]
    user_prompt = f"""다음은 회의/음성 녹음 파일에서 추출한 원본 대본(전사 텍스트)입니다:

[음성 전사 텍스트]
{trimmed_transcript}

위 내용을 분석하여 시스템 지침에 따라 100% 비즈니스 한국어로 '전문 회의록'을 작성하십시오.
"""

    minutes_text = ""

    if is_gemini_provider(provider):
        client = get_gemini_client(custom_api_key=custom_api_key)
        config = types.GenerateContentConfig(
            temperature=0.2,
            max_output_tokens=8192
        )
        
        @retry(retry=retry_if_exception(_should_retry_error), stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=3, max=20))
        def _call_gemini():
            contents_payload = [system_prompt, user_prompt]
            response = safe_gemini_generate_content(
                client=client,
                model=settings.selected_gemini_version or "gemini-2.5-flash",
                contents=contents_payload,
                config=config
            )
            return response.text

        minutes_text = _call_gemini()
    else:
        # OpenAI / Groq / OpenRouter 등
        client = get_openai_client(
            provider, 
            custom_api_key=custom_api_key, 
            custom_base_url=custom_base_url,
            timeout=70.0
        )
        target_model = "gpt-4o"
        p_lower = str(provider).lower()
        if "groq" in p_lower:
            target_model = "llama-3.3-70b-versatile"
        elif "openrouter" in p_lower:
            target_model = provider.replace("openrouter/", "") if "/" in provider else "google/gemma-4-26b-a4b-it:free"

        @retry(retry=retry_if_exception(_should_retry_error), stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1.5, min=2, max=15))
        def _call_openai():
            response = client.chat.completions.create(
                model=target_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                max_tokens=4096
            )
            return response.choices[0].message.content

        minutes_text = _call_openai()

    if not minutes_text or not minutes_text.strip():
        raise RuntimeError("회의록 생성 결과 텍스트가 비어 있습니다.")

    # 마크다운 섹션별 분할 파싱 (가이드 뷰어 호환용 딕셔너리 생성)
    sections_dict = _parse_meeting_sections(minutes_text, transcript)
    return sections_dict


def _parse_meeting_sections(minutes_markdown: str, full_transcript: str) -> Dict[str, str]:
    """
    생성된 전체 회의록 마크다운을 뷰어 챕터 형식에 맞게 섹션별로 분할하고,
    마지막에 '음성 전사 전문 (Transcript)'을 첨부합니다.
    """
    sections = {}
    
    # 정규식으로 '## ' 헤더를 기준으로 섹션 분리
    pattern = re.compile(r'(^##\s+.*?$)', re.MULTILINE)
    splits = pattern.split(minutes_markdown)
    
    if len(splits) > 1:
        # 첫 번째 파트 (보통 제목이나 서두 개요)
        first_part = splits[0].strip()
        if first_part and not first_part.startswith("##"):
            sections["회의 개요 (Overview)"] = first_part

        # 헤더와 본문 짝 맞추기
        for i in range(1, len(splits), 2):
            header = splits[i].replace("##", "").strip()
            body = splits[i+1].strip() if i+1 < len(splits) else ""
            clean_title = re.sub(r'^[0-9]+[\.\s\-]+', '', header).strip()
            clean_title = clean_title or header
            sections[clean_title] = f"## {header}\n\n{body}"
    else:
        # 분할되지 않은 경우 단일 본문으로 처리
        sections["회의록 요약 및 상세 내용"] = minutes_markdown

    # 마지막 섹션으로 원문 음성 전사 전문(Full Transcript) 추가
    formatted_transcript = (
        f"## 음성 전사 전문 (Full Transcript)\n\n"
        f"> **💡 안내**: 본 내용은 오디오 파일에서 AI 음성 인식(STT) 엔진을 통해 추출된 원문 텍스트 전문입니다.\n\n"
        f"```text\n{full_transcript.strip()}\n```"
    )
    sections["음성 전사 전문 (Full Transcript)"] = formatted_transcript
    
    return sections
