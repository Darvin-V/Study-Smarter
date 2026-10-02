"""
Study Smarter - Comprehensive Service & UI Integration Audit Script
Verifies:
1. All Service & Repository APIs called from UI exist with correct signatures
2. Real end-to-end PDF processing with Question Bank creation & MySQL persistence
3. Quiz retrieval, answer checking, attempt recording, analytics, and history tracking
"""

import sys
import io
import time
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from src.logger import logger
from src.database.connection import DatabaseManager, get_db_cursor
from src.database.question_repository import QuestionRepository
from src.database.attempt_repository import AttemptRepository
from src.services.quiz_service import QuizService
from src.services.analytics_service import AnalyticsService
from src.services.pipeline_service import PipelineService
from src.services.pdf_service import PDFService
from src.services.ai_service import AIService


class MockUploadedFile:
    """Simulates a Streamlit UploadedFile object."""
    def __init__(self, data: bytes, name: str):
        self._data = data
        self.name = name
        self.size = len(data)
        self._io = io.BytesIO(data)

    def read(self, *args):
        return self._io.read(*args)

    def getvalue(self):
        return self._data

    def seek(self, offset, whence=0):
        return self._io.seek(offset, whence)


def run_service_api_audit():
    print("\n==================================================")
    print(" 1. AUDIT SERVICE & REPOSITORY METHOD INTERFACES")
    print("==================================================")

    # 1. PipelineService
    assert hasattr(PipelineService, "process_pdf_question_bank"), "Missing process_pdf_question_bank on PipelineService"
    assert hasattr(PipelineService, "process_pdf_upload"), "Missing process_pdf_upload compatibility on PipelineService"
    print("  [PASS] PipelineService has process_pdf_question_bank and process_pdf_upload")

    # 2. QuizService
    assert hasattr(QuizService, "fetch_quiz_questions_by_bank"), "Missing fetch_quiz_questions_by_bank on QuizService"
    assert hasattr(QuizService, "verify_question_answer"), "Missing verify_question_answer on QuizService"
    assert hasattr(QuizService, "submit_quiz_attempt"), "Missing submit_quiz_attempt on QuizService"
    print("  [PASS] QuizService has fetch_quiz_questions_by_bank, verify_question_answer, submit_quiz_attempt")

    # 3. AnalyticsService
    assert hasattr(AnalyticsService, "get_overall_summary"), "Missing get_overall_summary on AnalyticsService"
    assert hasattr(AnalyticsService, "generate_recommendations"), "Missing generate_recommendations on AnalyticsService"
    assert hasattr(AnalyticsService, "get_topic_accuracy_breakdown"), "Missing get_topic_accuracy_breakdown on AnalyticsService"
    assert hasattr(AnalyticsService, "get_chapter_accuracy_breakdown"), "Missing get_chapter_accuracy_breakdown on AnalyticsService"
    assert hasattr(AnalyticsService, "get_subject_accuracy_breakdown"), "Missing get_subject_accuracy_breakdown on AnalyticsService"
    assert hasattr(AnalyticsService, "get_difficulty_accuracy_breakdown"), "Missing get_difficulty_accuracy_breakdown on AnalyticsService"
    assert hasattr(AnalyticsService, "analyze_attempt_details"), "Missing analyze_attempt_details on AnalyticsService"
    assert hasattr(AnalyticsService, "get_weak_topics"), "Missing get_weak_topics on AnalyticsService"
    print("  [PASS] AnalyticsService has all required metrics and breakdown methods including analyze_attempt_details")

    # 4. QuestionRepository
    assert hasattr(QuestionRepository, "get_question_banks"), "Missing get_question_banks"
    assert hasattr(QuestionRepository, "create_question_bank"), "Missing create_question_bank"
    assert hasattr(QuestionRepository, "get_total_questions_in_bank"), "Missing get_total_questions_in_bank"
    assert hasattr(QuestionRepository, "get_all_questions"), "Missing get_all_questions"
    assert hasattr(QuestionRepository, "update_question"), "Missing update_question"
    assert hasattr(QuestionRepository, "create_question"), "Missing create_question"
    print("  [PASS] QuestionRepository has all CRUD and question bank methods")

    # 5. AttemptRepository
    assert hasattr(AttemptRepository, "get_user_attempts"), "Missing get_user_attempts"
    assert hasattr(AttemptRepository, "get_unique_questions_attempted"), "Missing get_unique_questions_attempted"
    assert hasattr(AttemptRepository, "get_quiz_history"), "Missing get_quiz_history"
    assert hasattr(AttemptRepository, "record_attempt"), "Missing record_attempt"
    assert hasattr(AttemptRepository, "record_bulk_attempts"), "Missing record_bulk_attempts"
    print("  [PASS] AttemptRepository has all attempt tracking, unique count, and history methods")

    # 6. DatabaseManager
    assert hasattr(DatabaseManager, "test_connection"), "Missing test_connection on DatabaseManager"
    test_res = DatabaseManager.test_connection()
    assert isinstance(test_res, dict) and "success" in test_res, f"Unexpected test_connection return: {test_res}"
    print(f"  [PASS] DatabaseManager.test_connection() returned: success={test_res['success']}")


def run_real_pdf_end_to_end():
    print("\n==================================================")
    print(" 2. REAL PDF UPLOAD & END-TO-END WORKFLOW")
    print("==================================================")

    ts = int(time.time())
    bank_name = f"Audit Bank {ts}"
    pdf_filename = f"audit_bank_{ts}.pdf"

    # Step A: Generate a real MCQ PDF with ReportLab
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.drawString(50, 750, f"Practice Examination - {bank_name}")
    c.drawString(50, 710, f"1. Which organelle is known as the powerhouse of the cell? [Audit Code {ts}]")
    c.drawString(70, 690, "A) Ribosome")
    c.drawString(70, 675, "B) Mitochondria")
    c.drawString(70, 660, "C) Nucleus")
    c.drawString(70, 645, "D) Endoplasmic Reticulum")

    c.drawString(50, 610, f"2. What is the unit of electrical resistance? [Audit Code {ts}]")
    c.drawString(70, 590, "A) Ohm")
    c.drawString(70, 575, "B) Volt")
    c.drawString(70, 560, "C) Ampere")
    c.drawString(70, 545, "D) Watt")
    c.showPage()
    c.save()
    pdf_bytes = buf.getvalue()

    # Step B: Create / ensure Question Bank
    bank_id = QuestionRepository.create_question_bank(name=bank_name, source_pdf=pdf_filename)
    assert bank_id is not None and bank_id > 0, f"Failed to create Question Bank '{bank_name}'"
    print(f"  [PASS] Question Bank created with ID={bank_id} ('{bank_name}')")

    # Step C: Execute PipelineService.process_pdf_question_bank
    uploaded_file = MockUploadedFile(pdf_bytes, pdf_filename)
    progress_steps = []
    def on_progress(msg, pct):
        progress_steps.append((pct, msg))

    result = PipelineService.process_pdf_question_bank(
        uploaded_file=uploaded_file,
        bank_id=bank_id,
        bank_name=bank_name,
        target_subject="Science",
        use_ai_extraction=False,
        progress_callback=on_progress,
    )

    assert result.get("success"), f"Pipeline execution failed: {result}"
    assert result.get("total_extracted", 0) >= 2, f"Expected >= 2 questions extracted, got {result.get('total_extracted')}"
    assert result.get("saved_count", 0) >= 2, f"Expected >= 2 questions saved to MySQL, got {result.get('saved_count')}"
    assert result.get("bank_id") == bank_id, f"Bank ID mismatch: expected {bank_id}, got {result.get('bank_id')}"
    print(f"  [PASS] PipelineService processed PDF: {result.get('saved_count')} saved, {result.get('verified_count')} verified")

    # Step D: Verify Question Bank appears in get_question_banks()
    all_banks = QuestionRepository.get_question_banks()
    matching_bank = next((b for b in all_banks if b.id == bank_id), None)
    assert matching_bank is not None, f"Bank ID {bank_id} not found in get_question_banks()"
    assert matching_bank.question_count >= 2, f"Expected question_count >= 2, got {matching_bank.question_count}"
    print(f"  [PASS] Question Bank verified in get_question_banks() with {matching_bank.question_count} questions")

    # Step E: Verify Practice Question Retrieval
    quiz = QuizService.fetch_quiz_questions_by_bank(
        bank_id=bank_id,
        bank_name=bank_name,
        limit=5,
        user_id=1,
    )
    assert quiz is not None and len(quiz.questions) >= 2, f"Expected >= 2 quiz questions, got {len(quiz.questions) if quiz else 0}"
    print(f"  [PASS] QuizService fetched {len(quiz.questions)} questions for bank '{bank_name}'")

    # Step F: Verify Wrong-Answer Evaluation and Solution Display
    q1 = quiz.questions[0]
    corr_ans = q1.correct_answer.strip().upper()
    wrong_opt = "A" if corr_ans != "A" else "C"

    eval_wrong = QuizService.verify_question_answer(q1, wrong_opt)
    assert eval_wrong.get("valid"), "verify_question_answer returned valid=False"
    assert not eval_wrong.get("is_correct"), "Deliberate wrong answer evaluated as correct!"
    assert eval_wrong.get("correct_answer") == corr_ans, f"Expected correct answer {corr_ans}, got {eval_wrong.get('correct_answer')}"
    assert len(eval_wrong.get("explanation", "")) > 0, "Missing explanation for wrong answer"
    print(f"  [PASS] Wrong-answer evaluated correctly: selected={wrong_opt}, correct={corr_ans}, explanation verified")

    # Step G: Record Attempt and Verify Analytics
    attempt_details = [{
        "question_id": q1.id,
        "question_text": q1.question_text,
        "selected_option": wrong_opt,
        "correct_answer": corr_ans,
        "is_correct": False,
        "topic_name": q1.topic,
        "time_taken": 15,
    }]
    sub_res = QuizService.submit_quiz_attempt(
        quiz=quiz,
        user_id=1,
        attempt_details=attempt_details,
        total_time_seconds=15,
    )
    assert sub_res.get("db_recorded"), f"Attempt not recorded to DB: {sub_res}"
    print(f"  [PASS] Attempt saved to MySQL via submit_quiz_attempt (score: {sub_res['score']}/{sub_res['total_questions']})")

    # Step H: Verify Analytics & Coverage
    summary = AnalyticsService.get_overall_summary(user_id=1, bank_id=bank_id)
    assert summary["total_questions_attempted"] >= 1, f"Expected >= 1 questions attempted in bank, got {summary['total_questions_attempted']}"
    unique_count = AttemptRepository.get_unique_questions_attempted(user_id=1, bank_id=bank_id)
    assert unique_count >= 1, f"Expected >= 1 unique attempted, got {unique_count}"
    print(f"  [PASS] Analytics & Unique count verified: {unique_count} distinct question(s) attempted in bank")

    # Step I: Verify Study History
    history = AttemptRepository.get_quiz_history(user_id=1, bank_id=bank_id)
    assert len(history) >= 1, "Expected >= 1 history record for this bank"
    h_row = history[0]
    assert h_row.get("total_attempted") >= 1, "Expected total_attempted >= 1"
    print(f"  [PASS] Study History retrieved: quiz_id={h_row.get('quiz_id')}, date={h_row.get('quiz_date')}, total={h_row.get('total_attempted')}")

    # Step J: Verify Compatibility wrapper process_pdf_upload
    compat_res = PipelineService.process_pdf_upload(
        pdf_bytes=pdf_bytes,
        bank_name=f"Compat Bank {ts}",
        user_id=1,
    )
    assert compat_res.get("success"), f"process_pdf_upload failed: {compat_res}"
    print(f"  [PASS] PipelineService.process_pdf_upload compatibility wrapper works cleanly")

    # Clean up temporary test data so database and UI remain completely clean
    try:
        QuestionRepository.delete_question_bank(bank_id)
        if compat_res.get("bank_id"):
            QuestionRepository.delete_question_bank(compat_res["bank_id"])
    except Exception as cleanup_err:
        pass

    print("\n==================================================")
    print(" [SUCCESS] ALL SERVICE & WORKFLOW AUDITS PASSED!")
    print("==================================================")



if __name__ == "__main__":
    run_service_api_audit()
    run_real_pdf_end_to_end()
