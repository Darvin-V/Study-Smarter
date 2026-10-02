from src.services.ai_service import AIService
from src.config import Config
import json, urllib.request

api_key = Config.GEMINI_API_KEY
print("Has API Key:", bool(api_key))
print("Configured Model:", Config.AI_MODEL_NAME)

# Test models
for model in ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-2.5-flash", Config.AI_MODEL_NAME]:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": "Respond with JSON: {\"status\": \"ok\"}"}]}],
        "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"}
    }
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            print(f"Model {model}: SUCCESS -> {text.strip()}")
            break
    except Exception as e:
        print(f"Model {model}: FAILED -> {e}")
