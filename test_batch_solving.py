import urllib.request, json, time
from src.config import Config

api_key = Config.GEMINI_API_KEY
model = "gemini-flash-lite-latest"

questions_sample = [
    {
        "id": 1,
        "question": "In the complex ion [AuXe4]2+ , Xe acts as :",
        "options": {"A": "central atom", "B": "ligand", "C": "chelating agent", "D": "electrophile"}
    },
    {
        "id": 2,
        "question": "Hybridisation shown by Au in [AuXe4]2+ is :",
        "options": {"A": "sp3", "B": "sp3d", "C": "sp3d2", "D": "sp2"}
    },
    {
        "id": 3,
        "question": "Compounds of noble gases except _______ are known.",
        "options": {"A": "Krypton", "B": "Radon", "C": "Helium", "D": "Xenon"}
    },
    {
        "id": 4,
        "question": "Which of the following noble gases has the highest boiling point?",
        "options": {"A": "He", "B": "Ne", "C": "Ar", "D": "Xe"}
    },
    {
        "id": 5,
        "question": "Shape of XeF4 molecule is :",
        "options": {"A": "Tetrahedral", "B": "Square planar", "C": "Pyramidal", "D": "See-saw"}
    }
]

prompt = f"""You are an expert academic educator and exam specialist.
For each of the following multiple choice questions:
1. Determine the strictly correct option letter ("A", "B", "C", or "D").
2. Provide a high-quality educational solution (2 to 4 concise, clear sentences) explaining the conceptual reason WHY that option is correct. Never output metadata like "Answer is A" or "Option B is correct". Provide actual scientific or conceptual explanations.
3. Infer the chapter, topic, and difficulty ("Easy", "Medium", or "Hard").

Questions to solve:
{json.dumps(questions_sample, indent=2)}

Respond with a JSON array of objects strictly matching this schema:
[
  {{
    "id": 1,
    "correct_answer": "B",
    "solution": "In the complex ion [AuXe4]2+, xenon acts as a ligand donating its electron lone pair to form coordinate bonds with gold. Although noble gases are generally unreactive, xenon can act as a weak Lewis base toward very strong Lewis acids like gold cations.",
    "chapter": "p-Block Elements",
    "topic": "Compounds of Noble Gases",
    "difficulty": "Hard"
  }}
]
"""

url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
payload = {
    "contents": [{"parts": [{"text": prompt}]}],
    "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"}
}
req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")

t0 = time.time()
with urllib.request.urlopen(req, timeout=20) as resp:
    data = json.loads(resp.read().decode("utf-8"))
    res_text = data["candidates"][0]["content"]["parts"][0]["text"]
    elapsed = time.time() - t0
    print(f"Batch solving 5 questions took: {elapsed:.2f}s")
    results = json.loads(res_text)
    for r in results:
        print(f"Q{r['id']}: Correct={r['correct_answer']} | Difficulty={r.get('difficulty')} | Chapter={r.get('chapter')}")
        print(f"  Solution: {r['solution']}")
