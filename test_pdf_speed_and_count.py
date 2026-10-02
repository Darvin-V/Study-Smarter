"""
Verification Test for Issue 3:
1. Measures time for each stage:
   - PDF text extraction
   - MCQ parsing
   - Gemini batch processing
   - Validation
   - MySQL bulk saving
2. Confirms >20 questions detected, processed, and persisted in MySQL.
3. Tests runtime accessibility of Question 1, 20, 21, and last question (42) with real solutions.
"""
import time
import sys
import io
sys.stdout.reconfigure(encoding='utf-8')

from pathlib import Path
from src.services.pdf_service import PDFService
from src.services.ai_service import AIService
from src.database.question_repository import QuestionRepository
from src.database.connection import get_db_cursor
from src.models.schemas import QuestionModel
from src.services.quiz_service import QuizService

def run_pdf_benchmark():
    pdf_path = Path("uploads/1788676821_ChemistryXII.pdf")
    assert pdf_path.exists(), f"Test PDF not found at {pdf_path}"

    print("==================================================")
    print("STAGE-BY-STAGE TIMING & BENCHMARK FOR PDF PIPELINE")
    print(f"File: {pdf_path.name} ({round(pdf_path.stat().st_size / 1024, 2)} KB)")
    print("==================================================")

    # 1. PDF Text Extraction
    t0 = time.perf_counter()
    raw_text = PDFService.extract_text_from_pdf(pdf_path)
    t_extract = time.perf_counter() - t0
    print(f"[1] PDF Text Extraction : {t_extract:.3f}s (Extracted {len(raw_text)} chars)")

    # 2. MCQ Parsing (Regex / Structure)
    t0 = time.perf_counter()
    mcq_candidates = PDFService.parse_mcqs_regex(raw_text)
    t_parse = time.perf_counter() - t0
    print(f"[2] MCQ Parsing         : {t_parse:.3f}s (Detected {len(mcq_candidates)} valid MCQs)")
    assert len(mcq_candidates) > 20, f"Expected >20 MCQs, got {len(mcq_candidates)}"

    # 3. Create a unique test bank in MySQL
    bank_name = f"Chemistry XII Mastery (Bench {int(time.time())})"
    bank_id = QuestionRepository.create_question_bank(
        name=bank_name,
        source_pdf=pdf_path.name
    )
    print(f"    Created Question Bank ID={bank_id}: '{bank_name}'")

    # 4. Gemini Batch Processing (Batches of 10)
    t0 = time.perf_counter()
    solved_questions = AIService.batch_solve_and_classify_questions(
        extracted_questions=mcq_candidates,
        class_level=12,
        subject="Chemistry",
        batch_size=10
    )
    t_gemini = time.perf_counter() - t0
    print(f"[3] Gemini Batch Solving: {t_gemini:.3f}s (Processed {len(solved_questions)} questions across {len(mcq_candidates)//10 + 1} batches)")

    # 5. Validation
    t0 = time.perf_counter()
    q_models = []
    bad_kw = ["low confidence", "unable to determine", "held for review", "flagged for review", "processing error", "unverified"]
    for q in solved_questions:
        expl = q.get("explanation", "") or ""
        status = q.get("verification_status", "AI_VERIFIED")
        if any(kw in expl.lower() for kw in bad_kw) or len(expl.strip()) < 15:
            expl = ""
            status = "NEEDS_REVIEW"
        
        q_model = QuestionModel(
            class_level=12,
            subject="Chemistry",
            chapter=q.get("chapter", "Chemistry XII"),
            topic=q.get("topic", "General"),
            question_text=q.get("question", ""),
            option_a=q.get("options", {}).get("A", ""),
            option_b=q.get("options", {}).get("B", ""),
            option_c=q.get("options", {}).get("C", ""),
            option_d=q.get("options", {}).get("D", ""),
            correct_answer=q.get("correct_answer", "A"),
            explanation=expl,
            difficulty=q.get("difficulty", "Medium"),
            source_pdf=pdf_path.name,
            answer_confidence=q.get("answer_confidence", 0.90),
            verification_status=status,
            bank_id=bank_id,
            bank_name=bank_name,
        )
        q_models.append(q_model)
    t_val = time.perf_counter() - t0
    print(f"[4] Solution Validation : {t_val:.3f}s ({len(q_models)} validated)")

    # 6. Bulk MySQL Saving
    t0 = time.perf_counter()
    created_ids = QuestionRepository.create_questions_bulk(q_models)
    t_save = time.perf_counter() - t0
    print(f"[5] MySQL Bulk Save     : {t_save:.3f}s ({len(created_ids)} questions saved)")

    total_pipeline_time = t_extract + t_parse + t_gemini + t_val + t_save
    print("--------------------------------------------------")
    print(f"TOTAL PIPELINE TIME     : {total_pipeline_time:.3f}s")
    print(f"BOTTLEENECK ANALYSIS    : Gemini batch processing was {t_gemini/total_pipeline_time*100:.1f}% of total time.")
    print("--------------------------------------------------")

    # 7. Query MySQL directly for bank question count
    with get_db_cursor() as cur:
        cur.execute("SELECT COUNT(*) as cnt FROM questions WHERE bank_id = %s", (bank_id,))
        count_in_db = cur.fetchone()["cnt"]

    print(f"MySQL Verification Query: SELECT COUNT(*) FROM questions WHERE bank_id = {bank_id} -> {count_in_db} questions")
    assert count_in_db == len(mcq_candidates), f"Expected {len(mcq_candidates)}, got {count_in_db}"
    assert count_in_db > 20, f"Expected > 20 questions in MySQL, got {count_in_db}"

    # 8. Test Practice Accessibility beyond Question 20
    print("\n==================================================")
    print("VERIFYING PRACTICE ACCESS FOR >20 QUESTIONS")
    print("==================================================")
    quiz = QuizService.fetch_quiz_questions_by_bank(
        bank_id=bank_id,
        bank_name=bank_name,
        limit=count_in_db,
        user_id=1
    )
    print(f"Practice Quiz generated with {len(quiz.questions)} total questions from Bank {bank_id}!")
    assert len(quiz.questions) == count_in_db, f"Expected {count_in_db} questions in practice quiz, got {len(quiz.questions)}"

    # Check Question 1, Question 20, Question 21, and Question 42 (last)
    check_indices = [0, 19, 20, 30, count_in_db - 1]
    for idx in check_indices:
        q = quiz.questions[idx]
        q_num = idx + 1
        print(f"\n--- Checking Question #{q_num} of {count_in_db} ---")
        print(f"Question text: {q.question_text[:90]}...")
        print(f"Options: A: {q.option_a[:40]} | B: {q.option_b[:40]}")
        print(f"Correct Answer: Option {q.correct_answer}")
        print(f"Solution: {q.explanation}")
        
        # Verify solution quality
        assert len(q.explanation.strip()) >= 15, f"Solution too short for Q#{q_num}!"
        for bad in bad_kw:
            assert bad not in q.explanation.lower(), f"Bad metadata '{bad}' found in Q#{q_num} explanation!"

    print("\n==================================================")
    print("ALL VERIFICATIONS FOR ISSUE 3 PASSED PERFECTLY!")
    print(f"  Total MCQs Detected : {len(mcq_candidates)}")
    print(f"  Total MCQs Processed: {len(solved_questions)}")
    print(f"  Total MCQs in MySQL : {count_in_db}")
    print(f"  Question 21 Accessible: YES (Solution verified)")
    print(f"  Last Question #{count_in_db} Accessible: YES (Solution verified)")
    print("==================================================")

if __name__ == "__main__":
    run_pdf_benchmark()
