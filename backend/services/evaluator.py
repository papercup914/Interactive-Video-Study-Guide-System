import os
import json
from backend.services.llm import get_gemini_client

def evaluate_learning_profile(question: str, answer: str) -> dict:
    """
    사용자의 질문과 답변 내용을 분석하여 단일 질문에 대한 학습 수준을 평가하고 JSON 형태로 반환합니다.
    """
    prompt = f"""
    당신은 사용자 맞춤형 학습 진단 전문가입니다.
    사용자가 문서 학습 중 남긴 질문과 AI의 답변을 분석하여, 사용자의 현재 질문 수준을 평가해 주세요.

    [사용자의 질문]: {question}
    [AI의 답변]: {answer}

    위 내용을 바탕으로 다음 JSON 포맷으로 엄격하게 결과를 반환하세요.
    - score: 질문의 난이도나 깊이를 1부터 10까지의 숫자로 평가 (1: 아주 기초적인 단어 뜻 질문, 5: 내용 확인, 10: 고차원적인 응용/비판적 사고)
    - type: 질문의 유형 (예: "단순 개념", "원리 이해", "응용 및 추론" 중 택 1)
    - advice: 이 질문 수준을 보인 사용자에게 해줄 수 있는 1문장짜리 짧은 학습 조언 (예: "기초 개념을 잘 잡아가고 있습니다. 다음엔 실제 사례를 찾아보세요.")

    출력 예시:
    {{"score": 3, "type": "단순 개념", "advice": "기초 단어를 잘 파악했습니다. 맥락 속에서 어떻게 쓰이는지 확인해보세요."}}
    
    오직 JSON만 출력하세요. 다른 텍스트는 포함하지 마세요.
    """

    try:
        client = get_gemini_client()
        response = client.models.generate_content(
            model=os.getenv("SELECTED_GEMINI_VERSION", "gemini-3.6-flash"),
            contents=[prompt]
        )
        raw = response.text.strip()
        if raw.startswith("```json"):
            raw = raw[7:-3]
        elif raw.startswith("```"):
            raw = raw[3:-3]
        return json.loads(raw.strip())
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        return {"score": 5, "type": "원리 이해", "advice": "꾸준히 질문하며 학습을 이어가세요."}

def generate_global_evaluation(profiles_data: str) -> str:
    """
    여러 문서의 질문 기록을 바탕으로 시스템 전체의 종합 학습 방향을 진단합니다.
    """
    prompt = f"""
    당신은 1:1 맞춤형 수석 학습 튜터입니다.
    사용자가 여러 문서에서 남긴 질문 내역과 평균 점수 데이터를 바탕으로, 
    현재 사용자의 전반적인 학습 상태를 종합적으로 진단하고 앞으로의 학습 방향을 제시해주세요.

    [사용자의 질문 데이터 요약]:
    {profiles_data}

    지시사항:
    1. 마크다운 형식으로 보기 좋게 3문단 정도로 정리해주세요.
    2. 칭찬과 격려를 포함하되, 어떤 유형의 질문이 주를 이루는지(예: 기초 개념 위주인지, 심화 응용 위주인지) 분석해주세요.
    3. 앞으로 어떤 점에 집중해서 공부하면 좋을지 구체적인 학습 방향을 제시하세요.
    """
    try:
        client = get_gemini_client()
        response = client.models.generate_content(
            model=os.getenv("SELECTED_GEMINI_VERSION", "gemini-3.6-flash"),
            contents=[prompt]
        )
        return response.text
    except Exception as e:
        return f"종합 평가를 생성하는 중 오류가 발생했습니다: {e}"
