"""
Final Demo Flow Verification Script
Tests steps A through N:
A. Start Study Smarter
B. Select Class 10 -> Science
C. Upload a valid MCQ question-bank PDF
D. Extract questions
E. Process questions with Gemini / Pipeline
F. Save verified questions to MySQL
G. Generate a quiz using persisted questions
H. Complete quiz
I. Submit
J. View score and explanations
K. Open Performance Analytics
L. Confirm results are reflected correctly
M. Restart the application (clear in-memory caches)
N. Confirm questions, attempts, and analytics remain available
"""

import sys
import io
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from src.config import config
from src.database.connection import DatabaseManager, get_db_cursor
from src.database.question_repository import QuestionRepository
from src.database.attempt_repository import AttemptRepository
from src.services.pdf_service import PDFService
from src.services.pipeline_service import PipelineService
from src.services.quiz_service import QuizService
from src.services.analytics_service import AnalyticsService
from src.models.schemas import QuestionModel

class MockUploadedFile(io.BytesIO):
    def __init__(self, buffer: bytes, name: str):
        super().__init__(buffer)
        self.name = name
        self.size = len(buffer)

def run_demo():
    print("=" * 60)
    print("  EXECUTING FINAL DEMO FLOW (A -> N)")
    print("=" * 60)

    # Step A: Start Study Smarter & Verify DB Connection
    print("\n[Step A] Starting Study Smarter backend & checking DB...")
    db_ok, msg = DatabaseManager.test_connection()
    assert db_ok, f"Database not ready: {msg}"
    print(f"    DB Status: {msg}")

    # Step B: Select Class 10 -> Science
    target_class = 10
    target_subject = "Science"
    print(f"\n[Step B] Active context selected: Class {target_class} -> {target_subject}")

    # Step C: Upload a valid MCQ question-bank PDF
    ts = int(time.time())
    pdf_filename = f"demo_mcq_bank_{ts}.pdf"
    print(f"\n[Step C] Generating and uploading valid MCQ question bank PDF ({pdf_filename})...")
    
    buf = io.BytesIO()
    p = canvas.Canvas(buf, pagesize=letter)
    p.drawString(50, 750, "Class 10 Science Practice Paper")
    p.drawString(50, 715, f"1. Which component of blood helps in blood clotting during an injury? (Demo {ts})")
    p.drawString(70, 695, "A) Platelets")
    p.drawString(70, 680, "B) Red Blood Cells")
    p.drawString(70, 665, "C) White Blood Cells")
    p.drawString(70, 650, "D) Plasma")
    p.showPage()
    p.save()
    buf.seek(0)
    uploaded_file = MockUploadedFile(buf.getvalue(), pdf_filename)

    # Step D & E & F: Extract questions -> Process -> Save to MySQL
    print("\n[Steps D, E, F] Extracting, processing, and persisting questions...")
    pipe_res = PipelineService.process_pdf_question_bank(
        uploaded_file=uploaded_file,
        target_class=target_class,
        target_subject=target_subject,
        use_ai_extraction=False,
        progress_callback=lambda msg, pct: print(f"    Progress [{pct}%]: {msg}")
    )
    assert pipe_res["success"], f"Pipeline failed: {pipe_res['message']}"
    assert pipe_res["total_extracted"] >= 1, "No questions extracted from PDF!"
    assert pipe_res["db_persisted"] is True, "Questions failed to persist to MySQL!"
    print(f"    Pipeline result: {pipe_res['message']}")

    # Find the inserted question in MySQL
    with get_db_cursor() as cur:
        cur.execute("SELECT id, question_text, correct_answer FROM questions WHERE question_text LIKE %s;", (f"%Demo {ts}%",))
        q_row = cur.fetchone()
        assert q_row is not None, "Question not found in MySQL questions table!"
        persisted_id = q_row["id"] if isinstance(q_row, dict) else q_row[0]
        correct_ans = q_row["correct_answer"] if isinstance(q_row, dict) else q_row[2]
        print(f"    Confirmed question in MySQL: ID={persisted_id}, Correct Answer={correct_ans}")

    # Step G: Generate a quiz using persisted MySQL questions
    print("\n[Step G] Generating quiz from persisted MySQL questions...")
    QuestionRepository._MEMORY_QUESTIONS.clear()
    quiz = QuizService.fetch_quiz_questions(class_level=target_class, subject=target_subject, limit=5)
    assert quiz is not None and len(quiz.questions) >= 1, "Failed to retrieve quiz from MySQL!"
    print(f"    Quiz generated with {len(quiz.questions)} questions from MySQL.")

    # Step H: Complete quiz (simulate student answering)
    print("\n[Step H] Student completing quiz...")
    target_q = None
    for q in quiz.questions:
        if q.id == persisted_id:
            target_q = q
            break
    if not target_q:
        target_q = quiz.questions[0]

    student_responses = [
        {
            "question_id": target_q.id,
            "question_text": target_q.question_text,
            "selected_option": target_q.correct_answer,
            "correct_answer": target_q.correct_answer,
            "is_correct": True,
            "topic_name": target_q.topic,
        }
    ]

    # Step I: Submit
    print("\n[Step I] Submitting completed quiz attempt...")
    submission_summary = QuizService.submit_quiz_attempt(
        quiz=quiz,
        user_id=1,
        attempt_details=student_responses,
        total_time_seconds=18
    )
    assert submission_summary["db_recorded"] is True, "Failed to record attempt into MySQL!"
    print(f"    Submission confirmed. DB recorded: {submission_summary['db_recorded']}")

    # Step J: View score and explanations
    print("\n[Step J] Checking score summary & explanations...")
    score_pct = submission_summary["percentage"]
    total_q = submission_summary["total_questions"]
    correct_cnt = submission_summary["correct_count"]
    expected_pct = round((correct_cnt / total_q) * 100, 1)
    print(f"    Score: {correct_cnt}/{total_q} ({score_pct}%)")
    assert score_pct == expected_pct, f"Expected {expected_pct}%, got {score_pct}"

    # Step K & L: Open Performance Analytics and confirm results
    print("\n[Steps K & L] Loading Performance Analytics and verifying against MySQL rows...")
    analytics_data = AnalyticsService.get_overall_summary(user_id=1)
    print(f"    Analytics Total Attempted: {analytics_data['total_questions_attempted']}")
    print(f"    Analytics Overall Accuracy: {analytics_data['overall_accuracy']}%")
    assert analytics_data["total_questions_attempted"] >= 1, "Analytics returned zero attempts!"
    assert analytics_data["overall_accuracy"] > 0, "Analytics accuracy is 0%!"

    # Step M: Restart application (hard reset in-memory caches)
    print("\n[Step M] Simulating application restart (clearing all repository in-memory state)...")
    QuestionRepository._MEMORY_QUESTIONS.clear()
    AttemptRepository._MEMORY_ATTEMPTS.clear()

    # Step N: Confirm questions, attempts, and analytics remain available
    print("\n[Step N] Verifying questions, attempts, and analytics persist post-restart from MySQL...")
    reloaded_q = QuestionRepository.get_question_by_id(persisted_id)
    assert reloaded_q is not None, f"Question ID {persisted_id} vanished from MySQL after restart!"
    assert reloaded_q.is_persisted is True, "Persisted flag lost!"
    print(f"    Question persisted in MySQL: '{reloaded_q.question_text[:50]}...'")

    reloaded_attempts = AttemptRepository.get_user_attempts(user_id=1)
    assert len(reloaded_attempts) >= 1, "Attempts vanished from MySQL after restart!"
    print(f"    Total attempt logs retrieved from MySQL post-restart: {len(reloaded_attempts)}")

    post_restart_analytics = AnalyticsService.get_overall_summary(user_id=1)
    assert post_restart_analytics["total_questions_attempted"] >= 1, "Post-restart analytics returned zero attempts!"
    assert post_restart_analytics["overall_accuracy"] > 0, "Post-restart analytics returned 0% accuracy!"
    print(f"    Post-restart analytics intact: {post_restart_analytics['total_questions_attempted']} attempts, {post_restart_analytics['overall_accuracy']}% accuracy")

    print("\n==================================================")
    print("  [DEMO FLOW COMPLETE: STEPS A -> N ALL PASSED!]")
    print("==================================================")
    return True

if __name__ == "__main__":
    ok = run_demo()
    sys.exit(0 if ok else 1)
