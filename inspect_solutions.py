from src.database.connection import get_db_cursor

with get_db_cursor() as cur:
    cur.execute('SELECT id, question_text, correct_answer, explanation FROM questions LIMIT 5')
    for row in cur.fetchall():
        print(f"ID: {row['id']}")
        print(f"Q: {row['question_text']}")
        print(f"Ans: {row['correct_answer']}")
        print(f"Expl: {row['explanation']}")
        print("-" * 60)
