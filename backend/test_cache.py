from google import genai
from google.genai import types

print(dir(genai.Client))
client = genai.Client()
print(dir(client))
if hasattr(client, 'caches'):
    print(dir(client.caches))
