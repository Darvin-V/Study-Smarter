import sys
sys.stdout.reconfigure(encoding='utf-8')
from src.database.connection import get_db_cursor

with get_db_cursor() as cursor:
    cursor.execute("SELECT id, question_text, option_a FROM questions WHERE bank_id = 1 AND id BETWEEN 35 AND 42")
    rows = cursor.fetchall()

for r in rows:
    print(f"ID={r['id']}: {repr(r['question_text'][:120])}")
