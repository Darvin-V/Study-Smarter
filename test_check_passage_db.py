import sys
sys.stdout.reconfigure(encoding='utf-8')
from src.database.connection import get_db_cursor

with get_db_cursor() as cursor:
    cursor.execute("SELECT id, question_text, option_a FROM questions WHERE bank_id = 1")
    rows = cursor.fetchall()

print(f"Total in Bank 1: {len(rows)}")
for r in rows:
    if "glycogen" in r['question_text'].lower() or "polysaccharide" in r['question_text'].lower() or "passage" in r['question_text'].lower() or "read the" in r['question_text'].lower():
        print(f"ID={r['id']}:")
        print(r['question_text'][:250])
        print("A:", r['option_a'])
        print("="*60)
