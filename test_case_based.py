import sys
from src.database.connection import get_db_cursor

with get_db_cursor() as cursor:
    cursor.execute("SELECT id, bank_id, question_text, option_a FROM questions WHERE bank_id = 1 AND id BETWEEN 8 AND 16")
    rows = cursor.fetchall()

for r in rows:
    print(f"=== Question ID {r['id']} (Bank {r['bank_id']}) ===")
    print(r["question_text"])
    print("-" * 40)
