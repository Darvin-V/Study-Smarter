"""
Study Smarter - Database Solution Repair Migration Script
Finds all questions in MySQL with bad metadata in the explanation field,
re-solves them in batches with Gemini, and writes verified correct answers
and genuine educational solutions into MySQL.
"""

import time
from src.database.connection import get_db_cursor
from src.services.ai_service import AIService
from src.config import Config


def repair_database_solutions():
    print("==================================================")
    print("STARTING DATABASE SOLUTION REPAIR MIGRATION")
    print("==================================================")

    # 1. Fetch all questions needing repair
    query = """
        SELECT id, bank_id, subject, class as class_level, chapter, topic, question_text,
               option_a, option_b, option_c, option_d, correct_answer, explanation, verification_status
        FROM questions
        WHERE explanation LIKE '%Low Confidence%'
           OR explanation LIKE '%Unable to determine%'
           OR explanation LIKE '%held for review%'
           OR explanation LIKE '%AI verified%'
           OR explanation LIKE '%Unverified%'
           OR explanation LIKE '%Flagged for review%'
           OR explanation LIKE '%Processing error%'
           OR explanation IS NULL
           OR TRIM(explanation) = ''
        ORDER BY bank_id, id
    """

    with get_db_cursor() as cur:
        cur.execute(query)
        rows = cur.fetchall()

    print(f"Found {len(rows)} questions in MySQL needing solution repair.")
    if not rows:
        print("No bad solutions found in database! Exiting.")
        return

    # Convert rows to dict format for AIService
    questions_to_solve = []
    for r in rows:
        q_item = {
            "db_id": r["id"],
            "question": r["question_text"],
            "options": {
                "A": r.get("option_a", ""),
                "B": r.get("option_b", ""),
                "C": r.get("option_c", ""),
                "D": r.get("option_d", ""),
            },
            "subject": r.get("subject", "General"),
            "class_level": r.get("class_level", 0),
            "chapter": r.get("chapter", "General"),
            "topic": r.get("topic", "General"),
        }
        questions_to_solve.append(q_item)

    batch_size = 10
    total = len(questions_to_solve)
    repaired_count = 0
    needs_review_count = 0

    print(f"Processing in batches of {batch_size} via Gemini API...")

    for i in range(0, total, batch_size):
        batch = questions_to_solve[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (total + batch_size - 1) // batch_size
        print(f"\n--- Batch {batch_num}/{total_batches} ({len(batch)} questions) ---")

        solved_batch = AIService.batch_solve_and_classify_questions(
            extracted_questions=batch,
            class_level=batch[0].get("class_level", 0),
            subject=batch[0].get("subject", "General"),
            batch_size=len(batch),
        )

        update_sql = """
            UPDATE questions
            SET correct_answer = %s,
                explanation = %s,
                verification_status = %s,
                difficulty = %s,
                chapter = %s,
                topic = %s
            WHERE id = %s
        """

        with get_db_cursor() as cur:
            for solved in solved_batch:
                db_id = solved.get("db_id")
                corr_ans = solved.get("correct_answer", "A")
                expl = solved.get("explanation", "")
                status = solved.get("verification_status", "NEEDS_REVIEW")
                diff = solved.get("difficulty", "Medium")
                chap = solved.get("chapter", "General")
                top = solved.get("topic", "General")

                if status == "AI_VERIFIED" and len(expl) >= 15:
                    repaired_count += 1
                else:
                    needs_review_count += 1

                cur.execute(update_sql, (corr_ans, expl if expl else None, status, diff, chap, top, db_id))

        print(f"Batch {batch_num} updated in MySQL. (Total repaired so far: {repaired_count})")
        time.sleep(1.0)

    print("\n==================================================")
    print("MIGRATION SUMMARY")
    print(f"Total rows inspected: {total}")
    print(f"Successfully repaired with educational solutions: {repaired_count}")
    print(f"Held for review: {needs_review_count}")
    print("==================================================")


if __name__ == "__main__":
    repair_database_solutions()
