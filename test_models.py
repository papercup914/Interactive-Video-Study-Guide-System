import os
import time
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.environ.get('GEMINI_API_KEY'))

models = [
    'gemini-3.5-flash',
    'gemini-3.1-flash-lite',
    'gemini-3.1-pro-preview',
    'gemini-3-flash-preview',
    'gemini-3-pro-preview',
    'gemini-2.0-flash',
    'gemini-2.0-flash-lite',
    'gemini-flash-latest'
]

print("Testing models:")
for m in models:
    try:
        response = client.models.generate_content(model=m, contents='hi')
        print(f'{m}: SUCCESS')
    except Exception as e:
        error_msg = str(e)
        if '429' in error_msg:
            print(f'{m}: QUOTA_EXHAUSTED (Supported, but out of quota)')
        elif '404' in error_msg:
            print(f'{m}: NOT_FOUND (Unsupported)')
        elif '403' in error_msg:
            print(f'{m}: FORBIDDEN (No access)')
        else:
            print(f'{m}: ERROR - {error_msg}')
    time.sleep(1)
