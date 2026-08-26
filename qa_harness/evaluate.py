import argparse
import asyncio
import json
import os
import uuid
import yaml
from datetime import datetime
from google import genai
from pydantic import BaseModel
import traceback
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent.parent / "backend" / ".env"
load_dotenv(env_path)

from http_client import QAHttpClient

class Evaluator:
    def __init__(self, job_id: str, persona_name: str, max_turns: int = 3):
        self.job_id = job_id
        self.persona_name = persona_name
        self.max_turns = max_turns
        self.client = QAHttpClient()
        
        # Load persona
        with open("qa_harness/personas.yaml", "r", encoding="utf-8") as f:
            personas = yaml.safe_load(f).get("personas", {})
        
        if persona_name not in personas:
            raise ValueError(f"Persona '{persona_name}' not found in personas.yaml")
        
        self.persona = personas[persona_name]
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not configured in environment.")
        self.llm_client = genai.Client(api_key=api_key)

    async def get_guide_context(self):
        try:
            data = await self.client.get_guide(self.job_id)
            document = data.get("document") or {}
            # just take the first chapter's content as context
            if document:
                first_key = list(document.keys())[0]
                return document[first_key]
            return "테스트용 가이드 본문입니다."
        except Exception as e:
            print(f"Failed to fetch guide context: {e}")
            return "테스트용 가이드 본문입니다."

    async def generate_student_question(self, context: str, history: list):
        prompt = f"{self.persona['system_prompt']}\n\n[학습 내용 원문]\n{context}\n\n[대화 기록]\n"
        for msg in history:
            role = "학생" if msg["role"] == "user" else "튜터"
            prompt += f"{role}: {msg['content']}\n"
        prompt += "\n학생:"
        
        response = self.llm_client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=prompt,
            config={"max_output_tokens": 150, "temperature": 0.0}
        )
        return response.text.strip()

    async def evaluate(self, transcript: str):
        import re
        
        rubric = self.persona.get("evaluation_criteria", "채점 기준:\n- 8~10점: 소크라테스식 문답법 유지\n- 1~7점: 문답법 무너짐")
        
        prompt = f"""다음은 AI 학생 페르소나('{self.persona['name']}')와 소크라테스식 튜터 간의 대화록입니다.
학생의 목적: {self.persona['purpose']}

대화록을 읽고 튜터가 소크라테스식 문답법을 잘 유지했는지 평가하여 JSON 형식으로 반환하세요.

{rubric}

형식: {{"score": 1~10, "feedback": "상세한 판정 근거"}}

<transcript>
{transcript}
</transcript>"""

        for attempt in range(2):
            try:
                response = self.llm_client.models.generate_content(
                    model="gemini-3.1-flash-lite",
                    contents=prompt,
                    config={"response_mime_type": "application/json"}
                )
                
                text = response.text.strip()
                text = re.sub(r"```json\s*", "", text, flags=re.IGNORECASE)
                text = re.sub(r"```\s*", "", text)
                
                return json.loads(text)
            except Exception as e:
                if attempt == 1:
                    print(f"Failed to parse evaluation JSON: {e}")
                    return {"status": "judge_error", "score": None, "feedback": f"Evaluation failed: {str(e)}"}

    async def run(self):
        try:
            print(f"Starting QA Evaluation for job_id: {self.job_id}, persona: {self.persona_name}")
            
            # 1. Pre-flight health check
            is_healthy = await self.client.ping_health()
            if not is_healthy:
                print("Server connection failed (Health check). Aborting QA test.")
                return

            # 2. Get guide content
            context = await self.get_guide_context()
            
            history = []
            transcript = ""
            correlation_id = uuid.uuid4().hex
            
            # Quantitative Metrics
            total_student_length = 0
            total_tutor_length = 0
            tutor_question_marks = 0
            
            print(f"Using Correlation-ID: {correlation_id}")
            
            try:
                for turn in range(self.max_turns):
                    question = await self.generate_student_question(context, history)
                    print(f"\n[Turn {turn+1}] Student ({self.persona_name}): {question}")
                    
                    payload = {
                        "section_content": context,
                        "history": history,
                        "message": question
                    }
                    
                    # 4. Send to Main Backend
                    response = await self.client.chat(payload, correlation_id)
                    tutor_reply = response.json().get("reply", "")
                    print(f"[Turn {turn+1}] Tutor: {tutor_reply}")
                    
                    history.append({"role": "user", "content": question})
                    history.append({"role": "assistant", "content": tutor_reply})
                    
                    transcript += f"학생: {question}\n튜터: {tutor_reply}\n\n"
                    
                    # Accumulate metrics
                    total_student_length += len(question)
                    total_tutor_length += len(tutor_reply)
                    tutor_question_marks += tutor_reply.count('?')
            except Exception as e:
                print(f"Error during chat loop: {e}")
                traceback.print_exc()

            # Calculate final metrics
            turns_completed = max(1, len(history) // 2)
            
            # Count redirection anchor keywords (ADHD/Derailment detection)
            anchor_keywords = ["본문", "학습 내용", "텍스트", "원문", "교재"]
            tutor_redirect_count = sum(
                1 for msg in history if msg["role"] == "assistant" and any(k in msg["content"] for k in anchor_keywords)
            )
            
            metrics = {
                "quantitative": {
                    "turns_completed": turns_completed,
                    "avg_student_length": round(total_student_length / turns_completed, 1),
                    "avg_tutor_length": round(total_tutor_length / turns_completed, 1),
                    "tutor_question_marks": tutor_question_marks,
                    "tutor_redirect_count": tutor_redirect_count
                },
                "derived": {
                    "tutor_question_density": round(tutor_question_marks / turns_completed, 2),
                    "redirect_ratio": round(tutor_redirect_count / turns_completed, 2)
                }
            }

            # 5. Judge
            print("\nEvaluating transcript...")
            evaluation = await self.evaluate(transcript)
            print(f"Score: {evaluation.get('score')}/10")
            print(f"Feedback: {evaluation.get('feedback')}")
            
            # Output result
            os.makedirs("qa_harness/reports", exist_ok=True)
            report = {
                "schema_version": "1.1",
                "job_id": self.job_id,
                "persona": self.persona_name,
                "correlation_id": correlation_id,
                "timestamp": datetime.now().isoformat(),
                "metrics": metrics,
                "evaluation": evaluation,
                "transcript": history
            }
            
            report_path = f"qa_harness/reports/eval_report_{self.job_id}_{correlation_id[:6]}.json"
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
                
            print(f"Report saved to {report_path}")
        finally:
            await self.client.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Persona QA Harness")
    parser.add_argument("--job_id", type=str, required=True, help="Job ID to test against")
    parser.add_argument("--persona", type=str, required=True, help="Persona name from personas.yaml")
    parser.add_argument("--max_turns", type=int, default=3, help="Maximum number of conversation turns")
    
    args = parser.parse_args()
    asyncio.run(Evaluator(args.job_id, args.persona, args.max_turns).run())
