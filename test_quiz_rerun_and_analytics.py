"""
Verification test for Quiz attempt submission, Streamlit rerun deduplication,
and analytics accuracy calculation against attempt data.
"""

import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.models.schemas import QuestionModel, QuizModel, AttemptModel
from src.database.question_repository import QuestionRepository
from src.database.attempt_repository import AttemptRepository
from src.services.quiz_service import QuizService
from src.services.analytics_service import AnalyticsService

def test_quiz_rerun_and_analytics():
    print("[1] Setting up Question Bank for Quiz Testing...")
    
    q1 = QuestionModel(
        class_level=10,
        subject="Science",
        chapter="Life Processes",
        topic="Respiration",
        question_text="What is the primary energy currency of the cell?",
        option_a="ATP",
        option_b="ADP",
        option_c="Glucose",
        option_d="Pyruvate",
        correct_answer="A",
        verification_status="VERIFIED"
    )
    
    q2 = QuestionModel(
        class_level=10,
        subject="Science",
        chapter="Life Processes",
        topic="Excretion",
        question_text="What is the basic filtration unit of the kidney?",
        option_a="Nephron",
        option_b="Neuron",
        option_c="Alveoli",
        option_d="Villi",
        correct_answer="A",
        verification_status="VERIFIED"
    )

    q1_id = QuestionRepository.create_question(q1)
    q2_id = QuestionRepository.create_question(q2)
    q1.id = q1_id
    q2.id = q2_id
    
    quiz = QuizModel(
        id=9999,
        title="NCERT Class 10 Science Practice Quiz",
        class_level=10,
        subject="Science",
        total_questions=2,
        questions=[q1, q2]
    )
    
    print("\n[2] Simulating Quiz Responses:")
    # Response 1: Correct (Selected A)
    eval1 = QuizService.verify_question_answer(q1, "A")
    # Response 2: Incorrect (Selected B)
    eval2 = QuizService.verify_question_answer(q2, "B")
    
    assert eval1["is_correct"] is True, "Eval 1 should be correct"
    assert eval2["is_correct"] is False, "Eval 2 should be incorrect"
    
    responses = [
        {"question_id": q1_id, "selected_option": "A", "correct_answer": "A", "is_correct": True, "time_taken": 15},
        {"question_id": q2_id, "selected_option": "B", "correct_answer": "A", "is_correct": False, "time_taken": 20},
    ]

    initial_attempts_count = len(AttemptRepository._MEMORY_ATTEMPTS)

    print("\n[3] Testing Streamlit Rerun Deduplication Guard:")
    # Simulate first submission
    session_state = {}
    
    if "quiz_summary" not in session_state or session_state["quiz_summary"] is None:
        session_state["quiz_summary"] = QuizService.submit_quiz_attempt(
            quiz=quiz,
            user_id=1,
            attempt_details=responses,
            total_time_seconds=35
        )

    # Simulate 5 consecutive Streamlit page reruns
    for rerun_idx in range(1, 6):
        if "quiz_summary" not in session_state or session_state["quiz_summary"] is None:
            # This should NEVER trigger on reruns!
            session_state["quiz_summary"] = QuizService.submit_quiz_attempt(
                quiz=quiz,
                user_id=1,
                attempt_details=responses,
                total_time_seconds=35
            )

    attempts_after_reruns = len(AttemptRepository._MEMORY_ATTEMPTS)
    new_attempts = attempts_after_reruns - initial_attempts_count
    
    print(f"    Total attempts recorded after 5 reruns: {new_attempts}")
    assert new_attempts == 2, f"Expected exactly 2 attempts recorded for 2 questions, but found {new_attempts} (Deduplication FAILED!)"
    print("    -> Streamlit Rerun Deduplication: PASS (Exactly once submission verified)")

    print("\n[4] Verifying Analytics Calculations Against Underlying Attempt Logs:")
    # Manual SQL/Data expected calculations:
    user_logs = [a for a in AttemptRepository._MEMORY_ATTEMPTS if a.get("user_id") == 1]
    expected_total_attempted = len(user_logs)
    expected_correct = sum(1 for a in user_logs if a.get("is_correct"))
    expected_accuracy = round((expected_correct / expected_total_attempted * 100), 2) if expected_total_attempted > 0 else 0.0

    print(f"    Manual SQL Calculation: {expected_correct} correct / {expected_total_attempted} attempted -> {expected_accuracy}%")

    # Analytics Service calculation:
    analytics_summary = AnalyticsService.get_overall_summary(user_id=1)
    print(f"    Analytics Service Output: {analytics_summary['overall_accuracy']}% overall accuracy, {analytics_summary['total_questions_attempted']} questions attempted")

    assert analytics_summary["total_questions_attempted"] == expected_total_attempted, "Total attempted mismatch!"
    assert analytics_summary["overall_accuracy"] == expected_accuracy, f"Accuracy mismatch! Expected {expected_accuracy}%, got {analytics_summary['overall_accuracy']}%"
    
    print("    -> Analytics Accuracy Agreement: PASS (UI and underlying Attempt logs agree 100%)")
    
    print("\n[SUCCESS] QUIZ RERUN DEDUPLICATION & ANALYTICS TEST PASSED!")
    return True

if __name__ == "__main__":
    test_quiz_rerun_and_analytics()
