import os
import json
from backend.services.llm.clients import (
    get_gemini_client,
    get_openai_client,
    is_gemini_provider,
    safe_gemini_generate_content
)
from backend.config import settings

def _normalize_openai_model(provider: str) -> str:
    """OpenRouter 접두사 제거 및 제공자별 실제 모델명을 정규화합니다."""
    if not provider:
        return "gpt-4o"
    p = str(provider).strip()
    if p == "OpenAI (GPT-4o)":
        return "gpt-4o"
    if p == "cerebras/gpt-oss-120b":
        return "gpt-oss-120b"
    if p.startswith("openrouter/"):
        p = p.replace("openrouter/", "", 1)
    if p in ("openrouter", "openrouter/free", "meta-llama/llama-3.3-70b-instruct:free"):
        return "nvidia/nemotron-3.5-lightning:free"
    return p

def generate_answer(selected_text: str, context: str, question: str, provider: str, learner_profile: str = "") -> str:
    """
    본문 컨텍스트를 바탕으로 사용자가 선택한 특정 텍스트에 대한 질문에 답변을 생성합니다.
    """
    prompt = f"""
    당신은 학습자의 질문에 답하는 1:1 맞춤형 사고 확장 파트너입니다.
    사용자가 문서 학습 중 특정 단어나 문장을 선택하여 질문을 남겼습니다.
    
    [전체 문맥 (배경 지식 참고용)]: 
    {context}
    
    [사용자가 선택한 텍스트 (집중 분석 대상)]: 
    "{selected_text}"
    
    [사용자의 질문]: 
    {question}
    
    <PERSONA_DIRECTIVE>
    당신은 무미건조한 AI가 아닙니다. 아래의 [학습자 프로필]에 100% 빙의하여 답변하십시오.
    
    [학습자 프로필]
    {learner_profile if learner_profile else "일반적인 성인 학습자"}
    
    1. 어조 강제: 명시된 '원하는 어조'를 철저하게 유지하십시오.
    2. 비유 강제: 이해를 돕기 위해 반드시 프로필의 '주요 관심사'에 빗대어 찰떡같은 비유를 하나 들어주세요.
    3. 눈높이 강제: '학습 목표'와 '연령대/직업'에 맞추어 어휘를 선택하십시오.
    </PERSONA_DIRECTIVE>
    
    지시사항:
    1. 전체 문맥을 요약하지 마세요. 사용자의 질문은 오직 **[사용자가 선택한 텍스트]**에 관한 것입니다.
    2. 선택된 단어/문장의 정의, 역할, 이유 등을 전체 문맥에 비추어 정확하게 설명하세요.
    3. **(중요)** "안녕하세요", "좋은 질문입니다" 같은 인사말이나 불필요한 서론을 절대 쓰지 마세요. 곧바로 답변(본론)부터 시작하세요.
    """
    
    model_id = settings.selected_gemini_version or "gemini-3.5-flash-lite"
    if is_gemini_provider(provider):
        try:
            client = get_gemini_client()
            response = safe_gemini_generate_content(
                client=client,
                model=model_id,
                contents=[prompt]
            )
            return response.text
        except Exception as e:
            print(f"[Harness Fallback] Gemini answer failed: {e}. Switching to OpenAI.")
            target_model = "gpt-4o"
            client = get_openai_client("OpenAI (GPT-4o)")
            response = client.chat.completions.create(
                model=target_model,
                messages=[
                    {"role": "system", "content": "당신은 본문 내용을 바탕으로 독자의 질문에 친절하게 답변하는 사고 파트너입니다."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
    else:
        target_model = _normalize_openai_model(provider)
            
        try:
            client = get_openai_client(provider)
            response = client.chat.completions.create(
                model=target_model,
                messages=[
                    {"role": "system", "content": "당신은 본문 내용을 바탕으로 독자의 질문에 친절하게 답변하는 사고 파트너입니다."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"[Harness Fallback] OpenAI answer failed: {e}. Switching to Gemini.")
            client = get_gemini_client()
            response = safe_gemini_generate_content(
                client=client,
                model=model_id,
                contents=[prompt]
            )
            return response.text

def translate_title(title: str, provider: str) -> str:
    """
    원본 영상의 제목이 외국어인 경우 한국어로 적절히 번역합니다.
    이미 한국어인 경우 원본을 그대로 반환합니다.
    """
    prompt = f"""
    당신은 전문 번역가입니다. 다음 유튜브 영상 제목을 확인하고, 
    만약 제목이 한국어가 아니라면(영어 등 외국어라면) 가장 자연스러운 한국어로 번역해주세요.
    이미 한국어거나 한국어가 주로 포함되어 있다면 원본을 그대로 출력하세요.
    다른 군더더기 말 없이 오직 "최종 제목" 텍스트만 출력하세요.
    
    원본 제목: "{title}"
    """
    model_id = settings.selected_gemini_version or "gemini-3.5-flash-lite"
    try:
        if is_gemini_provider(provider):
            client = get_gemini_client()
            response = safe_gemini_generate_content(
                client=client,
                model=model_id,
                contents=[prompt]
            )
            return response.text.strip().strip('"')
        else:
            target_model = _normalize_openai_model(provider)
            
            try:
                client = get_openai_client(provider)
                response = client.chat.completions.create(
                    model=target_model,
                    messages=[
                        {"role": "system", "content": "오직 번역된 제목 텍스트만 반환합니다."},
                        {"role": "user", "content": prompt}
                    ]
                )
                return response.choices[0].message.content.strip().strip('"')
            except Exception:
                client = get_gemini_client()
                response = safe_gemini_generate_content(
                    client=client,
                    model=model_id,
                    contents=[prompt]
                )
                return response.text.strip().strip('"')
    except Exception as e:
        print(f"Title translation failed: {str(e)}")
        return title

def extract_image_keyword(title: str, provider: str) -> str:
    """
    제목을 기반으로 사진 검색에 사용할 핵심 영문 키워드 1-2개를 추출합니다.
    """
    prompt = f"""
    You are an expert image researcher. Analyze the following video title and output EXACTLY ONE OR TWO English keywords that best represent its visual theme.
    These keywords will be used to search Unsplash for a high-quality background photo.
    Do not output anything else, no explanations, no quotes. Just the keywords in English.
    
    Video Title: "{title}"
    """
    model_id = settings.selected_gemini_version or "gemini-3.5-flash-lite"
    try:
        if is_gemini_provider(provider):
            client = get_gemini_client()
            response = safe_gemini_generate_content(
                client=client,
                model=model_id,
                contents=[prompt]
            )
            keyword = response.text.strip().replace('"', '')
            return keyword if keyword else "study"
        else:
            target_model = _normalize_openai_model(provider)
            try:
                client = get_openai_client(provider)
                response = client.chat.completions.create(
                    model=target_model,
                    messages=[
                        {"role": "system", "content": "Output only English keywords for image search."},
                        {"role": "user", "content": prompt}
                    ]
                )
                keyword = response.choices[0].message.content.strip().replace('"', '')
                return keyword if keyword else "study"
            except Exception:
                client = get_gemini_client()
                response = safe_gemini_generate_content(
                    client=client,
                    model=model_id,
                    contents=[prompt]
                )
                keyword = response.text.strip().replace('"', '')
                return keyword if keyword else "study"
    except Exception as e:
        print(f"Keyword extraction failed: {str(e)}")
        return "study"

def profile_content(context_data: str, provider: str) -> dict:
    """
    Analyzes the beginning of the transcript to dynamically profile the content type 
    and recommend optimal generation settings.
    """
    sample_text = context_data[:5000] if len(context_data) > 5000 else context_data
    
    prompt = f"""
    You are an expert AI content profiler. Analyze the following transcript sample and determine its content type, information density, and target audience.
    Based on your analysis, choose the most appropriate settings for generating a study guide.

    Output MUST be a valid JSON object without any markdown formatting. Use this EXACT schema:
    {{
        "length_preset": "핵심 요약" | "적당한 설명" | "아주 상세하게",
        "analogy_preset": "비유 없이 담백하게" | "적절한 비유 추가" | "풍부한 비유",
        "profile_message": "A short, friendly Korean message explaining your decision (e.g., '💡 AI가 전문적인 IT 강의로 인식하여 비유 없이 상세하게 정리합니다.')",
        "tutor_persona": {{
            "role": "The specific role the AI should take (e.g., '문학 평론가', 'IT 시니어 개발자', '열정적인 동기부여 강사', '중립적인 토론 진행자')",
            "tone": "The tone of voice (e.g., '전문적이고 냉철하게', '친절하고 비유를 섞어서', '학술적이고 객관적으로')",
            "focus_areas": "What to focus on based on content type (e.g., '핵심 쟁점과 논거 분석', '실무 적용 가능한 코드 스니펫', '저자의 의도와 문맥 해석')"
        }}
    }}

    Transcript Sample:
    {sample_text}
    """
    
    model_id = settings.selected_gemini_version or "gemini-3.5-flash-lite"
    try:
        if is_gemini_provider(provider):
            client = get_gemini_client()
            response = safe_gemini_generate_content(
                client=client,
                model=model_id,
                contents=[prompt]
            )
            raw_text = response.text.strip()
        else:
            try:
                client = get_openai_client(provider)
                target_model = _normalize_openai_model(provider)
                response = client.chat.completions.create(
                    model=target_model,
                    messages=[
                        {"role": "system", "content": "Output valid JSON only."},
                        {"role": "user", "content": prompt}
                    ]
                )
                raw_text = response.choices[0].message.content.strip()
            except Exception:
                client = get_gemini_client()
                response = safe_gemini_generate_content(
                    client=client,
                    model=model_id,
                    contents=[prompt]
                )
                raw_text = response.text.strip()
            
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.startswith("```"):
            raw_text = raw_text[3:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
            
        return json.loads(raw_text.strip())
    except Exception as e:
        print(f"Profiling failed: {str(e)}")
        return {
            "length_preset": "적당한 설명",
            "analogy_preset": "적절한 비유 추가",
            "profile_message": "💡 영상 길이에 맞는 기본 설정으로 정리했습니다."
        }
