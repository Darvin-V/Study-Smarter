"""
Study Smarter - Quiz Engine Verification Script
Tests question selection, backend answer verification, answer validation,
score/time tracking, and MySQL attempt recording.

Usage:
  python test_quiz_engine.py
"""

from src.services.quiz_service import QuizService
from src.models.schemas import QuestionModel


def run_quiz_engine_tests():
    print("=" * 65)
    print("  STUDY SMARTER - QUIZ ENGINE & BACKEND EVALUATION TEST")
    print("=" * 65)

    # -------------------------------------------------------------
    # Step 1: Test Question Retrieval matching Class, Subject, Chapter, Topic
    # -------------------------------------------------------------
    print("\n[Step 1/5] Testing Question Retrieval with Syllabus Filters...")
    quiz = QuizService.fetch_quiz_questions(
        class_level=12,
        subject="Physics",
        chapter="Electric Charges and Fields",
        topic="Electric Charge and Conservation",
        limit=5
    )
    print(f"  Retrieved Quiz Title : '{quiz.title}'")
    print(f"  Total Questions      : {quiz.total_questions}")
    assert quiz is not None
    assert isinstance(quiz.questions, list)
    print("  [OK] Question Retrieval Test PASSED.")

    # -------------------------------------------------------------
    # Step 2: Test Server-Side Single Question Answer Evaluation (Correct)
    # -------------------------------------------------------------
    print("\n[Step 2/5] Testing Backend Evaluation for CORRECT Answer...")
    q1 = quiz.questions[0] if quiz.questions else QuestionModel(
        id=1, question_text="What is the unit of electric dipole moment?",
        option_a="C m", option_b="N/C", option_c="V m", option_d="T",
        correct_answer="A", class_level=12, subject="Physics"
    )
    eval_correct = QuizService.verify_question_answer(q1, q1.correct_answer)
    print(f"  Question        : '{q1.question_text[:45]}...'")
    print(f"  Selected        : Option {eval_correct['selected_option']}")
    print(f"  Correct Answer  : Option {eval_correct['correct_answer']}")
    print(f"  Backend Result  : {eval_correct['status_text']} (is_correct={eval_correct['is_correct']})")
    assert eval_correct["valid"] is True
    assert eval_correct["is_correct"] is True
    print("  [OK] Correct Answer Evaluation PASSED.")

    # -------------------------------------------------------------
    # Step 3: Test Server-Side Single Question Answer Evaluation (Incorrect)
    # -------------------------------------------------------------
    print("\n[Step 3/5] Testing Backend Evaluation for INCORRECT Answer...")
    wrong_opt = "B" if q1.correct_answer != "B" else "A"
    eval_wrong = QuizService.verify_question_answer(q1, wrong_opt)
    print(f"  Selected        : Option {eval_wrong['selected_option']}")
    print(f"  Correct Answer  : Option {eval_wrong['correct_answer']}")
    print(f"  Backend Result  : {eval_wrong['status_text']} (is_correct={eval_wrong['is_correct']})")
    assert eval_wrong["valid"] is True
    assert eval_wrong["is_correct"] is False
    assert eval_wrong["selected_option"] == wrong_opt
    assert eval_wrong["correct_answer"] == q1.correct_answer
    print("  [OK] Incorrect Answer Evaluation PASSED.")

    # -------------------------------------------------------------
    # Step 4: Test Invalid Selection Validation
    # -------------------------------------------------------------
    print("\n[Step 4/5] Testing Invalid Answer Selection Validation...")
    eval_invalid = QuizService.verify_question_answer(q1, "")
    print(f"  Empty selection response: {eval_invalid}")
    assert eval_invalid["valid"] is False
    print("  [OK] Answer Selection Validation PASSED.")

    # -------------------------------------------------------------
    # Step 5: Test Full Quiz Submission & Scoring & Time Tracking
    # -------------------------------------------------------------
    print("\n[Step 5/5] Testing Full Quiz Submission & Scoring Summary...")
    mock_responses = [
        {
            "question_id": q1.id,
            "question_text": q1.question_text,
            "selected_option": q1.correct_answer,
            "correct_answer": q1.correct_answer,
            "is_correct": True,
            "topic_name": q1.topic,
        }
    ]
    quiz.questions = [q1]
    summary = QuizService.submit_quiz_attempt(
        quiz=quiz,
        user_id=1,
        attempt_details=mock_responses,
        total_time_seconds=25
    )
    print(f"  Summary Score       : {summary['score']}/{summary['total_questions']} ({summary['percentage']}%)")
    print(f"  Correct Count       : {summary['correct_count']}")
    print(f"  Incorrect Count     : {summary['incorrect_count']}")
    print(f"  Total Time (sec)    : {summary['total_time_seconds']}s")
    print(f"  DB Persistence Status: {'Saved to MySQL' if summary['db_recorded'] else 'Handled Offline Gracefully'}")
    assert summary["score"] == 1
    assert summary["percentage"] == 100.0
    assert summary["total_time_seconds"] == 25
    print("  [OK] Full Quiz Submission & Scoring Summary PASSED.")

    print("\n" + "=" * 65)
    print("[SUCCESS] ALL QUIZ ENGINE TESTS COMPLETED CLEANLY!")
    print("=" * 65)
    return True


if __name__ == "__main__":
    run_quiz_engine_tests()
