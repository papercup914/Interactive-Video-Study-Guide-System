import json
import re

transcript_path = r'C:\Users\radia\.gemini\antigravity\brain\cd8fd9d5-a2a6-47e0-964d-3155fb781c9b\.system_generated\logs\transcript.jsonl'
lines = []

with open(transcript_path, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            data = json.loads(line.strip())
            if data.get('type') == 'USER_INPUT' and data.get('source') == 'USER_EXPLICIT':
                c = data.get('content', '')
                if 'USER_REQUEST' in c:
                    match = re.search(r'<USER_REQUEST>(.*?)</USER_REQUEST>', c, re.DOTALL)
                    if match:
                        text = match.group(1).strip()
                        lines.append(f'\n[사용자 질문]\n{text}')
            elif data.get('type') == 'PLANNER_RESPONSE' and data.get('source') == 'MODEL':
                c = data.get('content', '')
                if c:
                    text = re.sub(r'`.*?`', '[코드 블록 생략]', c, flags=re.DOTALL).strip()
                    if text:
                        lines.append(f'\n[AI 답변 요약]\n{text[:500]}...')
        except Exception as e:
            pass

with open('summary_output.txt', 'w', encoding='utf-8') as out_f:
    for l in lines[-40:]:
        out_f.write(l + '\n')
