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
        return "google/gemma-4-26b-a4b-it:free"
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

def translate_title(title: str, provider: str, context_text: str = "") -> str:
    """
    원본 영상의 제목과 맥락을 분석하여 BZCF 스타일의 [타깃 뱃지] + 직관적 훅 타이틀을 생성합니다.
    """
    context_snippet = f"\n영상 내용/설명 발췌:\n{context_text[:1200]}" if context_text else ""
    prompt = f"""
    당신은 100만 구독자를 보유한 탑티어 지식 큐레이션 채널(예: BZCF 등)의 메인 에디터이자 베스트셀러 출판 기획자입니다.
    주어진 유튜브 영상의 제목과 맥락(자막/설명 발췌)을 면밀히 분석하여, 학습자가 당장 열어보고 싶도록 직관적이고 매력적인 한국어 학습 가이드 대표 제목을 작성해주세요.

    [🚨 절대 금지 규칙 - 엄격 준수]
    1. 영상의 실제 본문 내용과 무관한 일반적인 수험/공부법 어그로 문구(예: "공부 안 해도 점수 오르는", "마법의 학습 가이드", "10분 투자로 뇌 깨우기", "성적 향상 비법" 등)를 절대 창작하지 마십시오!
    2. [타깃 뱃지]에 [학습 가이드 필독]이나 [영상 필독]처럼 아무런 의미가 없는 일반 명사를 절대 쓰지 마십시오. 반드시 영상의 실제 도메인과 타깃(예: [예비 창업가 필독], [초기 창업자 필독], [스타트업 대표 필수], [개발자 필독], [AI 연구자 추천] 등)을 정확히 지정하십시오.
    3. 만약 원본 제목이 일반적이거나 불명확하더라도, 반드시 아래 '영상 내용/설명 발췌'에서 핵심 인물(예: 폴 그레이엄, YC 등)과 핵심 사건/주제(스타트업, 야망, AI, 투자 등)를 찾아내어 제목을 작성하십시오.

    [작성 규칙]
    1. [타깃 뱃지]: 영상의 핵심 내용을 가장 필요로 하는 실제 대상 독자를 맨 앞에 대괄호로 지정.
    2. 직관적 훅 제목: 영상의 본질적 통찰과 질문을 정조준하는 직관적이고 강력한 제목(예: "사업하고 싶으면 이거 끝까지 봐야함", "진짜 창업가를 움직이는 힘은 돈이 아니다", "위대한 아이디어가 처음엔 두려워 보이는 이유").
    3. 명확한 부제: 하이픈(-) 뒤에 영상의 핵심 인물이나 핵심 주제(예: "폴 그레이엄의 위대한 창업가론").
    4. 최종 출력 형태는 오직 다음 한 줄만 출력해야 합니다:
       [타깃 뱃지] 직관적 훅 제목 - 부제
    5. 따옴표나 기타 설명, 서론 없이 오직 최종 제목 한 줄만 출력하세요.

    원본 제목: "{title}"{context_snippet}
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
            candidate_models = [target_model]
            for m in ("google/gemma-4-26b-a4b-it:free", "nex-agi/nex-n2.5-pro:free", "nvidia/nemotron-3.5-lightning:free"):
                if m not in candidate_models:
                    candidate_models.append(m)
            
            client = get_openai_client(provider)
            for cur_m in candidate_models:
                # OpenRouter 무료 모델 분기
                cur_client = get_openai_client("openrouter") if (":free" in cur_m or "openrouter" in cur_m) else client
                try:
                    response = cur_client.chat.completions.create(
                        model=cur_m,
                        messages=[
                            {"role": "system", "content": "오직 [타깃 뱃지] 직관적 훅 제목 - 부제 한 줄만 출력합니다. 공부법 어그로 문구는 절대 금지됩니다."},
                            {"role": "user", "content": prompt}
                        ],
                        timeout=15.0
                    )
                    if response and response.choices and len(response.choices) > 0:
                        content = response.choices[0].message.content or ""
                        if content.strip():
                            lines = [line.strip().strip('"*# ') for line in content.strip().splitlines() if line.strip()]
                            badge_lines = [l for l in lines if l.startswith("[") and "]" in l]
                            if badge_lines:
                                return badge_lines[-1]
                            return lines[-1]
                except Exception:
                    continue
            return title
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
