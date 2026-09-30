import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import errors

load_dotenv()
key = os.getenv("GEMINI_API_KEY")
primary = os.getenv("GEMINI_MODEL")

# Try primary first, then progressively safer fallbacks
MODELS = [primary, "gemini-flash-latest", "gemini-3.6-flash", "gemini-2.5-flash"]
client = genai.Client(api_key=key)

def ask(prompt: str) -> str:
    for model in MODELS:
        for attempt in range(3):
            try:
                r = client.models.generate_content(model=model, contents=prompt)
                print(f"[OK] model={model}")
                return r.text
            except errors.ServerError as e:      # 5xx = server busy, retry
                wait = 2 ** attempt
                print(f"[503] {model} busy, retry in {wait}s")
                time.sleep(wait)
            except errors.ClientError as e:      # 4xx = our mistake, try next model
                print(f"[4xx] {model}: {e.code}, trying next model")
                break
    raise RuntimeError("All models failed")

print(ask("Say 'LandfallReady is alive' in Hindi, one line."))
