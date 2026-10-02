import sys
sys.stdout.reconfigure(encoding='utf-8')
from src.database.connection import get_db_cursor

with get_db_cursor() as cursor:
    cursor.execute("SELECT id, bank_id, question_text FROM questions WHERE bank_id = 1 ORDER BY id")
    chem_rows = cursor.fetchall()
    cursor.execute("SELECT id, bank_id, question_text FROM questions WHERE bank_id = 2 ORDER BY id")
    math_rows = cursor.fetchall()

print(f"Chemistry questions: {len(chem_rows)}")
print(f"Maths questions: {len(math_rows)}")

for idx, r in enumerate(chem_rows):
    if any(k in r['question_text'].lower() for k in ['passage', 'case', 'read the', 'following question']):
        print(f"Chem Q#{idx+1} (ID {r['id']}):")
        print(r['question_text'][:300])
        print("="*60)

for idx, r in enumerate(math_rows):
    if any(k in r['question_text'].lower() for k in ['case', 'read the', 'passage', 'following question', 'based on']):
        print(f"Math Q#{idx+1} (ID {r['id']}):")
        print(r['question_text'][:300])
        print("="*60)
