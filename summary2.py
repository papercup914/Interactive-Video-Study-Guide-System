import json
import re
import sys

transcript_path = r'C:\Users\radia\.gemini\antigravity\brain\264415c3-6b4e-4d37-b860-4582a8dc633e\.system_generated\logs\transcript.jsonl'
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
                        lines.append(f'USER: {text}')
        except Exception as e:
            pass

with open('summary_2644.txt', 'w', encoding='utf-8') as out_f:
    for l in lines:
        out_f.write(l.replace(chr(10), ' ') + '\n')
