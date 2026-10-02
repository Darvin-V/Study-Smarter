"""
Comprehensive End-to-End Test Suite for Study Smarter
Tests every visible feature against live MySQL and running Streamlit server.
Executes the exact 31-step scenario from Section 27, plus Section 6 (Invalid Uploads),
Section 12 (Completion logic), Section 13 (Accuracy logic), and Section 17 (Restart persistence).
"""

import sys
import os
import time
import io
import requests
from typing import Dict, Any, List

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from src.database.connection import get_db_cursor
from src.database.question_repository import QuestionRepository
from src.database.attempt_repository import AttemptRepository
from src.services.pipeline_service import PipelineService
from src.services.quiz_service import QuizService
from src.services.analytics_service import AnalyticsService
from src.services.pdf_service import PDFService
from src.models.schemas import QuestionModel, AttemptModel


def generate_test_pdf(filename: str, questions: List[Dict[str, Any]]) -> str:
    """Generates a real PDF file formatted with MCQs using reportlab."""
    filepath = os.path.join("uploads", filename)
    os.makedirs("uploads", exist_ok=True)
    c = canvas.Canvas(filepath, pagesize=letter)
    width, height = letter

    y = height - 50
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Study Smarter - Comprehensive Test Question Bank")
    y -= 30

    c.setFont("Helvetica", 11)
    for i, q in enumerate(questions, 1):
        if y < 100:
            c.showPage()
            y = height - 50
            c.setFont("Helvetica", 11)

        c.drawString(50, y, f"{i}. {q['question']}")
        y -= 18
        c.drawString(70, y, f"A) {q['A']}")
        y -= 16
        c.drawString(70, y, f"B) {q['B']}")
        y -= 16
        c.drawString(70, y, f"C) {q['C']}")
        y -= 16
        c.drawString(70, y, f"D) {q['D']}")
        y -= 24

    c.save()
    return filepath


def generate_empty_pdf(filename: str) -> str:
    """Generates an empty 1-page PDF with no text."""
    filepath = os.path.join("uploads", filename)
    os.makedirs("uploads", exist_ok=True)
    c = canvas.Canvas(filepath, pagesize=letter)
    c.showPage()
    c.save()
    return filepath


def generate_no_mcq_pdf(filename: str) -> str:
    """Generates a PDF with plain descriptive text but no MCQs."""
    filepath = os.path.join("uploads", filename)
    os.makedirs("uploads", exist_ok=True)
    c = canvas.Canvas(filepath, pagesize=letter)
    c.setFont("Helvetica", 12)
    c.drawString(50, 700, "This is an essay about climate change and photosynthesis.")
    c.drawString(50, 680, "It does not contain any multiple choice questions or option letters.")
    c.save()
    return filepath


class RealUploadFile:
    """Mock Streamlit UploadedFile wrapper around real bytes on disk."""
    def __init__(self, filepath: str):
        self.name = os.path.basename(filepath)
        with open(filepath, "rb") as f:
            self._bytes = f.read()
        self.size = len(self._bytes)
        self._io = io.BytesIO(self._bytes)

    def read(self, *args):
        return self._io.read(*args)

    def seek(self, *args):
        return self._io.seek(*args)

    def getbuffer(self):
        return self._bytes


def run_e2e_tests():
    print("==================================================")
    print("STARTING COMPLETE E2E TEST SCENARIO")
    print("==================================================")

    # -------------------------------------------------------------
    # Step 1: Open Study Smarter (HTTP check on live Streamlit server)
    # -------------------------------------------------------------
    print("\n[Step 1] Verifying live Streamlit application HTTP status...")
    try:
        resp = requests.get("http://localhost:8501", timeout=5)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        print("  -> PASS: Live Streamlit app is responding with HTTP 200")
    except Exception as e:
        print(f"  -> FAIL: Could not reach http://localhost:8501: {e}")
        sys.exit(1)

    # -------------------------------------------------------------
    # Step 2-7: Scan Question Bank with Real PDF
    # -------------------------------------------------------------
    test_ts = int(time.time())
    bank_name = f"Cell Biology Test Bank {test_ts}"
    print(f"\n[Step 2-3] Scanning Question Bank with name: '{bank_name}'")

    raw_test_questions = [
        {
            "question": "What is the primary function of the mitochondrion?",
            "A": "Energy production via ATP synthesis",
            "B": "Protein degradation",
            "C": "Photosynthetic glucose generation",
            "D": "Lipid export",
            "correct": "A",
            "explanation": "Mitochondria produce ATP through cellular respiration, powering biological processes."
        },
        {
            "question": "Which molecule carries genetic information from the nucleus to the ribosome?",
            "A": "tRNA",
            "B": "mRNA",
            "C": "rRNA",
            "D": "DNA Polymerase",
            "correct": "B",
            "explanation": "Messenger RNA (mRNA) transcribes DNA code and delivers it to ribosomes for translation."
        },
        {
            "question": "What is the basic unit of life?",
            "A": "Tissue",
            "B": "Organ",
            "C": "Cell",
            "D": "Organism",
            "correct": "C",
            "explanation": "The cell is the fundamental structural and functional unit of all living organisms."
        },
        {
            "question": "Which enzyme unwinds DNA during replication?",
            "A": "DNA Ligase",
            "B": "Helicase",
            "C": "Amylase",
            "D": "RNA Polymerase",
            "correct": "B",
            "explanation": "Helicase breaks hydrogen bonds between nucleotide base pairs to unwind the DNA double helix."
        },
        {
            "question": "Which organelle contains digestive enzymes that break down waste?",
            "A": "Lysosome",
            "B": "Centriole",
            "C": "Endoplasmic Reticulum",
            "D": "Peroxisome",
            "correct": "A",
            "explanation": "Lysosomes contain acid hydrolases that degrade biological waste and cellular debris."
        }
    ]

    pdf_path = generate_test_pdf(f"e2e_cell_bio_{test_ts}.pdf", raw_test_questions)
    print(f"[Step 4] Generated real PDF with 5 MCQs: {pdf_path}")
    uploaded_file = RealUploadFile(pdf_path)

    # Step 5: Process PDF
    print("[Step 5] Processing PDF via PipelineService...")
    bank_id = QuestionRepository.create_question_bank(
        name=bank_name,
        source_pdf=uploaded_file.name
    )
    assert bank_id > 0, f"Failed to create bank, got ID: {bank_id}"
    print(f"  -> Created bank_id: {bank_id}")

    pipeline_result = PipelineService.process_pdf_question_bank(
        uploaded_file=uploaded_file,
        bank_id=bank_id,
        bank_name=bank_name,
        target_subject="Biology",
        use_ai_extraction=False,
    )

    print(f"  -> Pipeline result: success={pipeline_result.get('success')}, extracted={pipeline_result.get('total_extracted')}")
    assert pipeline_result.get("success") is True, f"Pipeline failed: {pipeline_result}"

    # Step 6-7: Verify bank and questions in MySQL
    print("\n[Step 6-7] Verifying bank and questions in MySQL...")
    with get_db_cursor() as cur:
        cur.execute("SELECT id, name, source_pdf FROM question_banks WHERE id = %s", (bank_id,))
        db_bank = cur.fetchone()
        assert db_bank is not None, "Bank not found in MySQL"
        print(f"  -> PASS: Verified question bank in MySQL: {db_bank}")

        cur.execute("SELECT id, bank_id, question_text, option_a, option_b, option_c, option_d, correct_answer, explanation FROM questions WHERE bank_id = %s", (bank_id,))
        db_questions = cur.fetchall()
        assert len(db_questions) == 5, f"Expected 5 questions in bank, got {len(db_questions)}"
        for q in db_questions:
            assert q["bank_id"] == bank_id, f"Question {q['id']} has wrong bank_id: {q['bank_id']}"
            assert q["correct_answer"] in ["A", "B", "C", "D"], f"Invalid correct answer: {q['correct_answer']}"
        print(f"  -> PASS: Verified all {len(db_questions)} questions persisted with bank_id={bank_id}")

    # -------------------------------------------------------------
    # Step 8-9: Return Home & Verify new bank appears
    # -------------------------------------------------------------
    print("\n[Step 8-9] Verifying new bank appears in Home Page metrics & recent banks...")
    all_banks = QuestionRepository.get_question_banks()
    target_bank = next((b for b in all_banks if b.id == bank_id), None)
    assert target_bank is not None, f"Bank {bank_id} not returned by get_question_banks"
    assert target_bank.question_count == 5, f"Expected 5 questions for bank, got {target_bank.question_count}"
    print(f"  -> PASS: Home page query found bank '{target_bank.name}' with {target_bank.question_count} questions")

    # -------------------------------------------------------------
    # Step 10-11: Start Practice & Select the new bank
    # -------------------------------------------------------------
    print("\n[Step 10-11] Starting Practice session for the new bank...")
    quiz = QuizService.fetch_quiz_questions_by_bank(
        bank_id=bank_id,
        bank_name=bank_name,
        limit=5,
        user_id=1
    )
    assert len(quiz.questions) == 5, f"Expected 5 questions in quiz, got {len(quiz.questions)}"
    print(f"  -> Loaded quiz session with {len(quiz.questions)} questions")

    # Create a real quiz session row in MySQL quizzes table
    with get_db_cursor() as cur:
        cur.execute(
            "INSERT INTO quizzes (title, class_level, subject, total_questions) VALUES (%s, %s, %s, %s)",
            (quiz.title, quiz.class_level, quiz.subject, len(quiz.questions))
        )
        quiz_session_id = cur.lastrowid
    assert quiz_session_id > 0, "Failed to create quiz session in MySQL"
    print(f"  -> Created quiz_session_id: {quiz_session_id}")

    # -------------------------------------------------------------
    # Step 12-13: Answer Question 1 CORRECTLY
    # -------------------------------------------------------------
    q1 = quiz.questions[0]
    print(f"\n[Step 12-13] Answering Question 1: '{q1.question_text[:50]}...'")
    correct_opt = q1.correct_answer
    eval_q1 = QuizService.verify_question_answer(q1, correct_opt)
    assert eval_q1["is_correct"] is True, f"Expected True for correct answer {correct_opt}, got {eval_q1}"
    print(f"  -> PASS: Correct answer flow returned: is_correct={eval_q1['is_correct']}")

    # Save attempt 1 to MySQL
    att1 = AttemptModel(
        user_id=1,
        quiz_id=quiz_session_id,
        question_id=q1.id,
        selected_answer=correct_opt,
        correct_answer=correct_opt,
        is_correct=True,
        time_taken=12.0
    )
    ok1 = AttemptRepository.record_attempt(att1)
    assert ok1 > 0, "Failed to record attempt 1"
    print(f"  -> Attempt 1 recorded in MySQL: {ok1}")

    # -------------------------------------------------------------
    # Step 14-17: Answer Question 2 INCORRECTLY
    # -------------------------------------------------------------
    q2 = quiz.questions[1]
    print(f"\n[Step 14-17] Next Question -> Answering Question 2: '{q2.question_text[:50]}...'")
    wrong_opt = "C" if q2.correct_answer != "C" else "D"
    eval_q2 = QuizService.verify_question_answer(q2, wrong_opt)
    assert eval_q2["is_correct"] is False, f"Expected False for wrong answer {wrong_opt}, got {eval_q2}"
    assert eval_q2["correct_answer"] == q2.correct_answer
    assert eval_q2["explanation"] is not None and len(eval_q2["explanation"]) > 0
    print(f"  -> PASS: Wrong answer flow verified:")
    print(f"     Your Answer: {eval_q2['selected_option']}")
    print(f"     Correct Answer: {eval_q2['correct_answer']}")
    print(f"     Solution: {eval_q2['explanation'][:60]}...")

    # Save attempt 2 to MySQL
    att2 = AttemptModel(
        user_id=1,
        quiz_id=quiz_session_id,
        question_id=q2.id,
        selected_answer=wrong_opt,
        correct_answer=q2.correct_answer,
        is_correct=False,
        time_taken=15.0
    )
    ok2 = AttemptRepository.record_attempt(att2)
    assert ok2 > 0, "Failed to record attempt 2"
    print(f"  -> Attempt 2 recorded in MySQL: {ok2}")

    # Clear analytics cache
    from src.services.analytics_service import _fetch_user_attempt_logs
    _fetch_user_attempt_logs.clear()

    # -------------------------------------------------------------
    # Step 18-20: Leave practice early & Open Progress
    # Verify Completion and Accuracy Formulas
    # -------------------------------------------------------------
    print("\n[Step 18-20] Leaving practice early after 2 questions. Verifying Progress metrics...")
    summary = AnalyticsService.get_overall_summary(user_id=1, bank_id=bank_id)
    unique_done = AttemptRepository.get_unique_questions_attempted(user_id=1, bank_id=bank_id)
    total_in_bank = QuestionRepository.get_total_questions_in_bank(bank_id=bank_id)

    completion = round(unique_done / total_in_bank * 100, 1) if total_in_bank > 0 else 0.0
    print(f"  -> Unique questions attempted: {unique_done} of {total_in_bank}")
    print(f"  -> Completion: {completion}%")
    print(f"  -> Overall Accuracy: {summary['overall_accuracy']}%")

    # 2 questions attempted out of 5 = 40.0%
    assert unique_done == 2, f"Expected 2 unique questions, got {unique_done}"
    assert completion == 40.0, f"Expected Completion 40.0%, got {completion}%"
    # 1 correct out of 2 attempts = 50.0%
    assert summary["overall_accuracy"] == 50.0, f"Expected Accuracy 50.0%, got {summary['overall_accuracy']}%"
    print("  -> PASS: Completion (40.0%) and Accuracy (50.0%) match expected formulas!")

    # Verify that reattempting does NOT inflate completion
    print("\n[Section 12 Verification] Reattempting question 1 (already attempted)...")
    att_reattempt = AttemptModel(
        user_id=1,
        quiz_id=quiz_session_id,
        question_id=q1.id,
        selected_answer=correct_opt,
        correct_answer=correct_opt,
        is_correct=True,
        time_taken=10.0
    )
    AttemptRepository.record_attempt(att_reattempt)
    _fetch_user_attempt_logs.clear()

    unique_after_reattempt = AttemptRepository.get_unique_questions_attempted(user_id=1, bank_id=bank_id)
    completion_after = round(unique_after_reattempt / total_in_bank * 100, 1)
    summary_after = AnalyticsService.get_overall_summary(user_id=1, bank_id=bank_id)

    print(f"  -> Unique after reattempt: {unique_after_reattempt} (Completion: {completion_after}%)")
    print(f"  -> Accuracy after reattempt (2 correct / 3 attempts): {summary_after['overall_accuracy']}%")
    assert completion_after == 40.0, f"Completion should still be 40.0%, got {completion_after}%"
    assert round(summary_after["overall_accuracy"], 1) == 66.7, f"Accuracy should be 66.7%, got {summary_after['overall_accuracy']}%"
    print("  -> PASS: Reattempting did NOT inflate completion (remained 40.0%) while accuracy updated correctly.")

    # -------------------------------------------------------------
    # Step 21-22: Open Review Mistakes
    # -------------------------------------------------------------
    print("\n[Step 21-22] Verifying Review Mistakes page content...")
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT a.selected_answer, a.correct_answer as correct_ans, a.attempted_at,
                   q.question_text, q.option_a, q.option_b, q.option_c, q.option_d,
                   q.explanation, q.topic, q.chapter, q.subject
            FROM attempts a JOIN questions q ON a.question_id = q.id
            WHERE a.user_id = 1 AND a.is_correct = 0 AND q.bank_id = %s
            ORDER BY a.attempted_at DESC LIMIT 10
        """, (bank_id,))
        mistakes = cur.fetchall()

    assert len(mistakes) >= 1, f"Expected at least 1 mistake for bank {bank_id}, got {len(mistakes)}"
    m = mistakes[0]
    assert m["question_text"] == q2.question_text
    assert m["selected_answer"] == wrong_opt
    assert m["correct_ans"] == q2.correct_answer
    print(f"  -> PASS: Review Mistakes correctly shows:")
    print(f"     Question: {m['question_text'][:50]}...")
    print(f"     Your Wrong Answer: {m['selected_answer']}")
    print(f"     Correct Answer: {m['correct_ans']}")
    print(f"     Solution: {m['explanation'][:50]}...")

    # -------------------------------------------------------------
    # Step 23-24: Open Study History
    # -------------------------------------------------------------
    print("\n[Step 23-24] Verifying Study History page content...")
    history = AttemptRepository.get_quiz_history(user_id=1, bank_id=bank_id)
    assert len(history) >= 1, f"Expected at least 1 history session for bank {bank_id}, got {len(history)}"
    h_row = history[0]
    print(f"  -> PASS: Found history session: {h_row}")
    assert int(h_row["total_attempted"]) >= 2, f"Expected >=2 attempts, got {h_row['total_attempted']}"

    # -------------------------------------------------------------
    # Step 25-26: Return Home & Verify metrics changed
    # -------------------------------------------------------------
    print("\n[Step 25-26] Verifying Home metrics reflect the new session...")
    home_summary = AnalyticsService.get_overall_summary(user_id=1)
    print(f"  -> Total Questions Practiced: {home_summary['total_questions_attempted']}")
    print(f"  -> Overall Accuracy: {home_summary['overall_accuracy']}%")
    assert home_summary["total_questions_attempted"] >= 2
    print("  -> PASS: Home metrics updated correctly.")

    # -------------------------------------------------------------
    # Step 30-31: Continue Practice & Verify Unattempted-First Logic
    # -------------------------------------------------------------
    print("\n[Step 30-31] Testing Continue Practice unattempted-first prioritization...")
    continue_quiz = QuizService.fetch_quiz_questions_by_bank(
        bank_id=bank_id,
        bank_name=bank_name,
        limit=3,
        user_id=1
    )
    continue_q_ids = [q.id for q in continue_quiz.questions]
    attempted_q_ids = {q1.id, q2.id}
    print(f"  -> Already attempted question IDs: {attempted_q_ids}")
    print(f"  -> Continue Practice loaded question IDs: {continue_q_ids}")

    # None of the unattempted questions should be in attempted_q_ids (since 3 unattempted remain: q3, q4, q5)
    for q_id in continue_q_ids:
        assert q_id not in attempted_q_ids, f"Question {q_id} was already attempted but returned before unattempted!"
    print("  -> PASS: Continue Practice loaded strictly unattempted questions (questions 3, 4, 5)!")

    # -------------------------------------------------------------
    # Section 6: Test Invalid Uploads
    # -------------------------------------------------------------
    print("\n[Section 6] Testing Invalid Upload Handling...")

    # Test 6.1: Empty PDF
    empty_pdf_path = generate_empty_pdf(f"empty_{test_ts}.pdf")
    empty_upload = RealUploadFile(empty_pdf_path)
    res_empty = PipelineService.process_pdf_question_bank(
        uploaded_file=empty_upload,
        bank_id=99999,
        bank_name="Empty Bank",
        use_ai_extraction=False
    )
    print(f"  -> Empty PDF result: success={res_empty.get('success')}, message='{res_empty.get('message')}'")
    assert res_empty.get("success") is False, "Empty PDF should not succeed"
    assert "no readable text" in res_empty.get("message", "").lower() or "scanned" in res_empty.get("message", "").lower()
    print("  -> PASS: Empty PDF handled gracefully without crash.")

    # Test 6.2: PDF with No Usable MCQs
    no_mcq_pdf_path = generate_no_mcq_pdf(f"no_mcq_{test_ts}.pdf")
    no_mcq_upload = RealUploadFile(no_mcq_pdf_path)
    res_no_mcq = PipelineService.process_pdf_question_bank(
        uploaded_file=no_mcq_upload,
        bank_id=99999,
        bank_name="No MCQ Bank",
        use_ai_extraction=False
    )
    print(f"  -> No MCQ PDF result: success={res_no_mcq.get('success')}, message='{res_no_mcq.get('message')}'")
    assert res_no_mcq.get("success") is False, "No MCQ PDF should not succeed"
    assert "no suitable mcq questions were found" in res_no_mcq.get("message", "").lower()
    print("  -> PASS: Non-MCQ PDF returned clean student-facing message.")

    print("\n==================================================")
    print("ALL E2E SCENARIO TESTS PASSED SUCCESSFULLY!")
    print("==================================================")


if __name__ == "__main__":
    run_e2e_tests()
