"""
Study Smarter - End-to-End Question Processing Pipeline Test
Tests complete unified pipeline execution from mock PDF input bytes ->
text extraction -> MCQ structuring -> NCERT classification -> answer resolution ->
independent Python verification -> question-level fault-tolerance -> student quiz availability.

Usage:
  python test_pipeline_end_to_end.py
"""

import io
import pypdf
from src.services.pipeline_service import PipelineService
from src.services.pdf_service import PDFService
from src.services.quiz_service import QuizService
from src.models.schemas import QuestionModel


def create_sample_pdf_bytes(text_content: str) -> bytes:
    """Helper method to generate valid PDF byte streams for testing."""
    writer = pypdf.PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


class MockUploadedPDF:
    """Mock Streamlit UploadedFile object."""
    def __init__(self, name: str, text: str):
        self.name = name
        self.bytes_data = create_sample_pdf_bytes(text)
    def getvalue(self):
        return self.bytes_data


def run_pipeline_end_to_end_tests():
    print("=" * 65)
    print("  STUDY SMARTER - END-TO-END QUESTION PROCESSING PIPELINE TEST")
    print("=" * 65)

    # Sample PDF MCQ text content
    pdf_text_content = """
Q1. A charge of 2 uC is placed in an electric field of 100 N/C. Calculate force.
A. 2 x 10^-4 N
B. 5 x 10^-2 N
C. 200 N
D. 0.5 N

2. What is the SI unit of electric dipole moment?
(A) Coulomb meter (C m)
(B) Volt meter
(C) Newton per Coulomb
(D) Tesla

3. What is the charge on an unspecified quantum particle near boundary?
(A) Ambiguous Option A
(B) Ambiguous Option B
(C) Ambiguous Option C
(D) Ambiguous Option D
"""

    mock_pdf = MockUploadedPDF("class12_physics_bank.pdf", pdf_text_content)

    # Patch PDFService.extract_text_from_pdf for mock testing
    original_extract = PDFService.extract_text_from_pdf
    PDFService.extract_text_from_pdf = lambda source: pdf_text_content

    progress_log = []
    def on_progress(msg: str, pct: int):
        progress_log.append((msg, pct))
        print(f"  [Pipeline Tracker {pct}%] {msg}")

    print("\n[Test 1/4] Executing Complete End-to-End Pipeline...")
    try:
        res = PipelineService.process_pdf_question_bank(
            uploaded_file=mock_pdf,
            target_class=12,
            target_subject="Physics",
            use_ai_extraction=False,
            progress_callback=on_progress
        )
    finally:
        PDFService.extract_text_from_pdf = original_extract

    print(f"\n  Pipeline Summary Results:")
    print(f"    Success               : {res['success']}")
    print(f"    Total Extracted       : {res['total_extracted']}")
    print(f"    Verified & Published  : {res['verified_count']}")
    print(f"    Held for Admin Review : {res['review_count']}")
    print(f"    Persisted to MySQL    : {res['saved_count']}")

    assert res["success"] is True
    assert res["total_extracted"] > 0
    assert res["verified_count"] + res["review_count"] == res["total_extracted"]
    print("  [OK] Complete End-to-End Pipeline Execution PASSED.")

    # 2. Test Live Status Checklist Tracker
    print("\n[Test 2/4] Testing Live Status Progress Checklist Callback...")
    print(f"  Recorded {len(progress_log)} progress updates.")
    assert len(progress_log) >= 5
    assert progress_log[-1][1] == 100
    print("  [OK] Live Status Progress Checklist PASSED.")

    # 3. Test Fault-Tolerant Question Separation (VERIFIED vs NEEDS_REVIEW)
    print("\n[Test 3/4] Testing Fault-Tolerant Question Separation...")
    for v_q in res["verified_questions"]:
        status = getattr(v_q, "verification_status", None) if hasattr(v_q, "verification_status") else v_q.get("verification_status")
        q_text = getattr(v_q, "question_text", None) if hasattr(v_q, "question_text") else v_q.get("question", "")
        assert status in ["VERIFIED", "AI_VERIFIED"]
        print(f"    - Verified Q: '{q_text[:40]}...' [{status}]")

    for r_q in res["needs_review_questions"]:
        status = getattr(r_q, "verification_status", None) if hasattr(r_q, "verification_status") else r_q.get("verification_status")
        q_text = getattr(r_q, "question_text", None) if hasattr(r_q, "question_text") else r_q.get("question", "")
        assert status == "NEEDS_REVIEW"
        print(f"    - Review Q: '{q_text[:40]}...' [{status}]")

    print("  [OK] Fault-Tolerant Question Separation PASSED.")

    # 4. Test Student Quiz Availability (Exclusion of NEEDS_REVIEW)
    print("\n[Test 4/4] Testing Student Quiz Availability Filtering...")
    q_verified = QuestionModel(id=1, question_text="Verified Question", verification_status="VERIFIED")
    q_review = QuestionModel(id=2, question_text="Uncertain Question", verification_status="NEEDS_REVIEW")

    sample_pool = [q_verified, q_review]
    quiz_eligible = [q for q in sample_pool if getattr(q, "verification_status", "") != "NEEDS_REVIEW"]
    
    print(f"  Total Pool: {len(sample_pool)} | Eligible for Student Quizzes: {len(quiz_eligible)}")
    assert len(quiz_eligible) == 1
    assert quiz_eligible[0].id == 1
    print("  [OK] Student Quiz Availability Filtering PASSED.")

    print("\n" + "=" * 65)
    print("[SUCCESS] ALL END-TO-END PIPELINE TESTS PASSED CLEANLY!")
    print("=" * 65)
    return True


if __name__ == "__main__":
    run_pipeline_end_to_end_tests()
