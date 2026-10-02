import urllib.request, json, time
from src.config import Config

api_key = Config.GEMINI_API_KEY
test_models = [
    "gemini-2.5-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-2.5-flash",
    "gemini-flash-latest",
    "gemini-3.5-flash-lite",
    "gemini-3.6-flash",
    "gemini-3.7-flash"
]

for model in test_models:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": "Answer in JSON: {\"answer\": \"B\", \"solution\": \"Xenon acts as a ligand donating a lone pair.\"}"}]}],
        "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"}
    }
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            print(f"[{model}] SUCCESS: {text.strip()}")
            break
    except Exception as e:
        print(f"[{model}] FAILED: {e}")
    time.sleep(1)
