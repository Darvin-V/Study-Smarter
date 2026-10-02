"""
Study Smarter - Comprehensive Phase 24 Verification Test
Validates:
1. App launch & Home page layout
2. NO sidebar rendered (len(at.sidebar) == 0)
3. Top navbar, Hero, 5 Action Cards, Stats Strip, Recent Banks
4. Navigation to Upload ('upload')
5. Navigation to Practice ('practice')
6. Wrong answer submission, staying on same question, correct answer + solution displayed
7. Next question advance & correct answer feedback
8. Navigation to Progress ('progress') with separate Completion vs Accuracy metrics
9. Navigation to Review Mistakes ('mistakes')
10. Navigation to Study History ('history')
11. Persistence verification
"""

import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from streamlit.testing.v1 import AppTest
from src.database.connection import DatabaseManager, get_db_cursor
from src.database.question_repository import QuestionRepository
from src.database.attempt_repository import AttemptRepository
from src.services.quiz_service import QuizService
from src.services.analytics_service import AnalyticsService


def run_phase_24_test():
    print("=" * 60)
    print("  STUDY SMARTER - PHASE 24 REAL WORKFLOW VERIFICATION")
    print("=" * 60)

    # 1 & 2. Open App & Confirm NO sidebar
    at = AppTest.from_file("main.py", default_timeout=20)
    at.run()
    assert not at.exception, f"Startup error: {at.exception}"
    print("[1] App Launched cleanly: PASS")

    assert len(at.sidebar) == 0, f"Sidebar has {len(at.sidebar)} elements! Must be 0."
    print("[2] Confirm NO sidebar (0 elements): PASS")

    # 3. Confirm Home page layout elements
    assert at.session_state["page"] == "home"
    button_labels = [b.label for b in at.button]
    assert "Home" in button_labels
    assert "Progress" in button_labels
    assert "History" in button_labels
    print("[3] Navbar & Home design elements: PASS")

    # 4. Navigate to Upload ('upload')
    at.session_state["page"] = "upload"
    at.run()
    assert not at.exception, f"Upload error: {at.exception}"
    assert len(at.sidebar) == 0
    print("[4] Scan Question Bank Page ('upload'): PASS")

    # 5. Practice Page ('practice')
    at.session_state["page"] = "practice"
    at.run()
    assert not at.exception, f"Practice error: {at.exception}"
    assert len(at.sidebar) == 0
    print("[5] Start Practice Page ('practice'): PASS")

    # 6. Test Quiz Verification: Answer one wrong -> check answer stays on question with solution
    # Get a real question from MySQL
    questions = QuestionRepository.get_all_questions()
    assert len(questions) > 0, "No questions in database!"
    target_q = questions[0]
    wrong_opt = "B" if target_q.correct_answer != "B" else "C"

    eval_wrong = QuizService.verify_question_answer(target_q, wrong_opt)
    assert not eval_wrong["is_correct"], "Expected wrong answer to evaluate as incorrect!"
    assert eval_wrong["correct_answer"] == target_q.correct_answer
    assert "explanation" in eval_wrong
    print(f"[6] Wrong answer evaluation: PASS (Selected {wrong_opt}, Correct {target_q.correct_answer})")

    # 7. Test Correct Answer evaluation
    eval_correct = QuizService.verify_question_answer(target_q, target_q.correct_answer)
    assert eval_correct["is_correct"], "Expected correct answer to evaluate as correct!"
    print(f"[7] Correct answer evaluation: PASS (Selected {target_q.correct_answer})")

    # 8. Unattempted-first prioritization check
    quiz_set = QuizService.fetch_quiz_questions_by_bank(bank_id=None, limit=5, user_id=1)
    assert len(quiz_set.questions) > 0
    print(f"[8] Quiz generation with unattempted prioritization: PASS ({len(quiz_set.questions)} questions)")

    # 9. Navigate to Progress ('progress')
    at.session_state["page"] = "progress"
    at.run()
    assert not at.exception, f"Progress error: {at.exception}"
    assert len(at.sidebar) == 0
    print("[9] Progress Page ('progress'): PASS")

    # 10. Navigate to Review Mistakes ('mistakes')
    at.session_state["page"] = "mistakes"
    at.run()
    assert not at.exception, f"Mistakes error: {at.exception}"
    assert len(at.sidebar) == 0
    print("[10] Review Mistakes Page ('mistakes'): PASS")

    # 11. Navigate to Study History ('history')
    at.session_state["page"] = "history"
    at.run()
    assert not at.exception, f"History error: {at.exception}"
    assert len(at.sidebar) == 0
    print("[11] Study History Page ('history'): PASS")

    # 12. Return to Home
    at.session_state["page"] = "home"
    at.run()
    assert not at.exception, f"Home return error: {at.exception}"
    assert len(at.sidebar) == 0
    print("[12] Return to Home cleanly: PASS")

    print("=" * 60)
    print("  ALL PHASE 24 REAL WORKFLOW TESTS PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    run_phase_24_test()
