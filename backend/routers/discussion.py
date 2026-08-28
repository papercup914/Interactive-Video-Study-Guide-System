from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List
import os
from google import genai

router = APIRouter()

class ChatMessage(BaseModel):
    role: str
    content: str

class DiscussionRequest(BaseModel):
    section_content: str
    history: List[ChatMessage]
    message: str

@router.post("/chat")
async def chat(request: DiscussionRequest, req: Request):
    try:
        qa_test_mode = req.headers.get("x-qa-test-mode", "false").lower() == "true"
        correlation_id = req.headers.get("x-correlation-id", "unknown")
        
        if qa_test_mode:
            print(f"[QA TEST MODE] DB Save bypassed. Correlation-ID: {correlation_id}")

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or api_key == "여기에_GEMINI_API_키를_입력하세요":
            raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not configured.")
            
        client = genai.Client(api_key=api_key)
        
        system_instruction = f"""당신은 학습자의 깊은 이해를 돕기 위해 소크라테스식 문답법을 사용하는 친절한 튜터입니다.
아래 제공된 [학습 내용 원문]을 바탕으로 학생과 토론하세요.
답변은 친절하고 격려하는 어조를 유지하며, 정답을 바로 알려주기보다는 힌트를 주어 학생이 스스로 생각할 수 있도록 유도하세요.
본문 내용과 무관한 외부 지식보다는 본문을 기반으로 설명하세요.

[학습 내용 원문]
{request.section_content}"""

        prompt = system_instruction + "\n\n[대화 기록]\n"
        
        for msg in request.history:
            role_name = "학생" if msg.role == "user" else "튜터"
            prompt += f"{role_name}: {msg.content}\n"
            
        prompt += f"\n학생: {request.message}\n튜터:"

        from backend.services.llm import safe_gemini_generate_content
        response = safe_gemini_generate_content(
            client=client,
            model=os.getenv("SELECTED_GEMINI_VERSION", "gemini-3.6-flash"),
            contents=prompt
        )
        
        try:
            reply_text = response.text.strip()
        except ValueError:
            reply_text = "응답이 유해성 필터 등에 의해 차단되었습니다."
            
        return {"reply": reply_text}
    except Exception as e:
        print("Error in discussion chat:", e)
        raise HTTPException(status_code=500, detail=str(e))
