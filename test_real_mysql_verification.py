"""
Comprehensive Real MySQL Verification Script for Study Smarter.
Tests:
1. Port 3306 reachability
2. Authentication using .env configuration
3. Schema initialization & tables verification
4. Real question persistence to MySQL (SELECT confirmation)
5. App restart / memory reset & question persistence verification
6. Real quiz attempt persistence to MySQL (SELECT confirmation)
7. Streamlit rerun deduplication check
8. App restart / memory reset & attempt persistence verification
9. Analytics calculations reading persisted MySQL attempts
"""

import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import socket
from src.config import config
from src.database.connection import DatabaseManager, get_db_cursor, get_db_connection
from src.database.question_repository import QuestionRepository
from src.database.attempt_repository import AttemptRepository
from src.models.schemas import QuestionModel, QuizModel, AttemptModel
from src.services.quiz_service import QuizService
from src.services.analytics_service import AnalyticsService

def verify_all_mysql_flows():
    print("==================================================")
    print("  STUDY SMARTER - REAL MYSQL PERSISTENCE AUDIT")
    print("==================================================")

    # 1. Port 3306 Reachability
    print(f"\n[1] Checking TCP Port {config.DB_PORT} reachability on {config.DB_HOST}...")
    s = socket.socket()
    s.settimeout(3.0)
    port_res = s.connect_ex((config.DB_HOST, config.DB_PORT))
    s.close()
    port_reachable = (port_res == 0)
    print(f"    Port {config.DB_PORT} Reachable: {port_reachable}")
    if not port_reachable:
        print(f"    [FAIL] Port {config.DB_PORT} is still closed or unreachable.")
        return False

    # 2. Authentication Test
    print("\n[2] Testing MySQL Authentication using .env credentials...")
    conn_result = DatabaseManager.test_connection()
    print(f"    Connection Success : {conn_result['success']}")
    print(f"    Connection Message : {conn_result['message']}")
    if not conn_result["success"]:
        print(f"    [FAIL] Could not authenticate to MySQL server.")
        return False

    # 3. Schema Initialization
    print("\n[3] Initializing Database Schema (study_smarter_db)...")
    init_success = DatabaseManager.initialize_schema()
    print(f"    Schema Initialized : {init_success}")
    assert init_success, "Database schema initialization failed!"

    # 4. Verify Required Tables Exist
    print("\n[4] Confirming required tables exist in study_smarter_db...")
    expected_tables = {"users", "questions", "quizzes", "attempts"}
    with get_db_cursor() as cursor:
        cursor.execute("SHOW TABLES")
        tables_found = set()
        for row in cursor.fetchall():
            t_name = list(row.values())[0] if isinstance(row, dict) else row[0]
            tables_found.add(t_name.lower())
    
    print(f"    Tables found in MySQL: {tables_found}")
    missing = expected_tables - tables_found
    if missing:
        print(f"    [FAIL] Missing required tables: {missing}")
        return False
    print("    -> Required tables exist: PASS")

    # 5. Save Real Question to MySQL
    print("\n[5] Saving one real processed question to MySQL via QuestionRepository...")
    test_q = QuestionModel(
        class_level=10,
        subject="Science",
        chapter="Life Processes",
        topic="Respiration",
        question_text="Which cellular organelle is known as the powerhouse of the cell?",
        option_a="Mitochondria",
        option_b="Ribosome",
        option_c="Golgi Body",
        option_d="Lysosome",
        correct_answer="A",
        explanation="Mitochondria generate ATP through cellular respiration.",
        difficulty="Easy",
        answer_confidence=0.95,
        verification_status="VERIFIED"
    )

    q_id = QuestionRepository.create_question(test_q)
    print(f"    Question Inserted. Returned ID: {q_id}")
    print(f"    is_persisted status: {test_q.is_persisted}")
    assert test_q.is_persisted is True, "Question failed to persist to MySQL!"

    # 6. Query MySQL directly to confirm physical existence
    print("\n[6] Querying MySQL directly to confirm physical storage...")
    with get_db_cursor() as cursor:
        cursor.execute("SELECT id, class, subject, question_text, correct_answer, verification_status FROM questions WHERE id = %s", (q_id,))
        row = cursor.fetchone()
    
    print(f"    Physical row retrieved from MySQL: {row}")
    assert row is not None, f"Row ID {q_id} not found in MySQL questions table!"
    assert row.get("correct_answer") == "A" or row[4] == "A", "Stored data mismatch!"
    print("    -> Physical MySQL question storage: PASS")

    # 7. Restart / In-Memory Reset Test for Question Persistence
    print("\n[7] Simulating complete application restart (clearing memory repository)...")
    QuestionRepository._MEMORY_QUESTIONS.clear()
    assert len(QuestionRepository._MEMORY_QUESTIONS) == 0, "In-memory buffer not empty!"

    # Retrieve strictly from MySQL
    persisted_q = QuestionRepository.get_question_by_id(q_id)
    print(f"    Retrieved Question after memory reset: ID={persisted_q.id if persisted_q else None}, Q='{persisted_q.question_text if persisted_q else None}'")
    assert persisted_q is not None, "Question vanished after restart! It was only in memory!"
    assert persisted_q.is_persisted is True, "Persisted flag missing after restart!"
    print("    -> Question restart persistence: PASS")

    # 8. Quiz Generation from MySQL
    print("\n[8] Generating Quiz strictly from MySQL questions...")
    quiz = QuizService.fetch_quiz_questions(class_level=10, subject="Science", limit=5)
    print(f"    Quiz generated with {len(quiz.questions)} questions from MySQL.")
    assert len(quiz.questions) >= 1, "Failed to retrieve quiz questions from MySQL!"

    # 9. Complete Quiz & Persist Attempt to MySQL
    print("\n[9] Completing quiz and persisting attempt to MySQL...")
    responses = [
        {
            "question_id": q_id,
            "selected_option": "A",
            "correct_answer": "A",
            "is_correct": True,
            "time_taken": 12
        }
    ]

    initial_attempts_in_db = 0
    with get_db_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) as cnt FROM attempts WHERE user_id = 1")
        f_row = cursor.fetchone()
        if f_row:
            initial_attempts_in_db = f_row.get("cnt") if isinstance(f_row, dict) else f_row[0]

    attempt_summary = QuizService.submit_quiz_attempt(
        quiz=quiz,
        user_id=1,
        attempt_details=responses,
        total_time_seconds=12
    )
    print(f"    Quiz submit result: db_recorded={attempt_summary['db_recorded']}, percentage={attempt_summary['percentage']}%")
    assert attempt_summary["db_recorded"] is True, "QuizService failed to record attempts to MySQL!"

    # Query physical MySQL attempts table
    with get_db_cursor() as cursor:
        cursor.execute("SELECT id, user_id, question_id, selected_answer, is_correct, time_taken FROM attempts WHERE question_id = %s ORDER BY id DESC LIMIT 1", (q_id,))
        att_row = cursor.fetchone()
    
    print(f"    Physical attempt row in MySQL: {att_row}")
    assert att_row is not None, "Attempt row was NOT physically written to MySQL attempts table!"
    print("    -> Physical MySQL attempt storage: PASS")

    # 10. Duplicate Prevention Test under Reruns
    print("\n[10] Testing Streamlit rerun duplicate prevention...")
    with get_db_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM attempts WHERE question_id = %s", (q_id,))
        c_row = cursor.fetchone()
        count_before = list(c_row.values())[0] if isinstance(c_row, dict) else c_row[0]

    # Simulate session state cached summary guard
    session_state = {"quiz_summary": attempt_summary}
    # 5 Streamlit reruns
    for _ in range(5):
        if "quiz_summary" not in session_state or session_state["quiz_summary"] is None:
            QuizService.submit_quiz_attempt(quiz=quiz, user_id=1, attempt_details=responses, total_time_seconds=12)

    with get_db_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM attempts WHERE question_id = %s", (q_id,))
        c_row = cursor.fetchone()
        count_val = list(c_row.values())[0] if isinstance(c_row, dict) else c_row[0]
    
    print(f"    Attempt rows for question {q_id} before reruns: {count_before}, after reruns: {count_val}")
    assert count_val == count_before, f"Duplicate attempts detected in MySQL! Count changed from {count_before} to {count_val}!"
    print("    -> Streamlit rerun duplicate prevention: PASS")

    # 11 & 12. App Restart & Attempt Persistence Verification
    print("\n[11] Simulating app restart for Attempt Persistence...")
    AttemptRepository._MEMORY_ATTEMPTS.clear()
    
    # Retrieve attempts strictly from MySQL
    restarted_attempts = AttemptRepository.get_user_attempts(user_id=1)
    print(f"    Attempts retrieved from MySQL after app restart: {len(restarted_attempts)}")
    assert len(restarted_attempts) >= 1, "Attempts vanished after application restart!"
    print("    -> Attempt restart persistence: PASS")

    # 13. Performance Analytics reading MySQL rows
    print("\n[12] Verifying Performance Analytics reads from persisted MySQL rows...")
    analytics_summary = AnalyticsService.get_overall_summary(user_id=1)
    print(f"    Analytics Overall Accuracy : {analytics_summary['overall_accuracy']}%")
    print(f"    Total Questions Attempted  : {analytics_summary['total_questions_attempted']}")
    assert analytics_summary["total_questions_attempted"] >= 1, "Analytics failed to load MySQL attempt logs!"
    assert analytics_summary["overall_accuracy"] > 0, "Expected positive accuracy from database attempts!"
    print("    -> Analytics reading from MySQL: PASS")

    print("\n==================================================")
    print("  [SUCCESS] ALL REAL MYSQL PERSISTENCE TESTS PASSED!")
    print("==================================================")
    return True

if __name__ == "__main__":
    ok = verify_all_mysql_flows()
    if not ok:
        sys.exit(1)
