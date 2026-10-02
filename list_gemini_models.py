import urllib.request, json
from src.config import Config

api_key = Config.GEMINI_API_KEY
url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
try:
    with urllib.request.urlopen(url, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        models = [m["name"] for m in data.get("models", []) if "generateContent" in m.get("supportedGenerationMethods", [])]
        print("Available models supporting generateContent:")
        for m in models:
            print("  -", m)
except Exception as e:
    print("Failed to list models:", e)
