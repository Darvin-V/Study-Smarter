"""
Real-world end-to-end PDF Pipeline Validation Script.
Generates a legitimate NCERT Class 10 Science MCQ PDF and processes it through
the complete production pipeline:
PDF -> Text Extraction -> MCQ Parsing -> Scope Validation -> Live Gemini API -> Answer Verification -> Persistence.
"""

import os
import io
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from src.config import config
from src.services.pdf_service import PDFService
from src.services.pipeline_service import PipelineService
from src.database.question_repository import QuestionRepository

class MockUploadedFile(io.BytesIO):
    """Wrapper to mimic Streamlit UploadedFile with name and size attributes."""
    def __init__(self, buffer: bytes, name: str):
        super().__init__(buffer)
        self.name = name
        self.size = len(buffer)

def generate_sample_ncert_pdf() -> bytes:
    """Generates a legitimate PDF byte stream containing Class 10 Science MCQs."""
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, 750, "NCERT Class 10 Science - Practice Question Bank")
    p.setFont("Helvetica", 11)
    
    # Question 1
    p.drawString(50, 710, "1. Which cellular organelle is known as the powerhouse of the cell?")
    p.drawString(70, 690, "A) Mitochondria")
    p.drawString(70, 675, "B) Ribosome")
    p.drawString(70, 660, "C) Golgi Body")
    p.drawString(70, 645, "D) Lysosome")
    
    # Question 2
    p.drawString(50, 610, "2. Which acid is secreted in the human stomach to aid digestion?")
    p.drawString(70, 590, "A) Hydrochloric Acid")
    p.drawString(70, 575, "B) Sulphuric Acid")
    p.drawString(70, 560, "C) Nitric Acid")
    p.drawString(70, 545, "D) Acetic Acid")
    
    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer.getvalue()

def run_real_pdf_pipeline_test():
    print("[1] Generating legitimate NCERT Class 10 Science PDF fixture...")
    pdf_bytes = generate_sample_ncert_pdf()
    print(f"    Generated PDF size: {len(pdf_bytes)} bytes.")
    
    # Save to disk as well
    sample_path = "uploads/test_real_class10_science.pdf"
    with open(sample_path, "wb") as f:
        f.write(pdf_bytes)
    print(f"    Saved sample to '{sample_path}'.")

    # Step 1: Text extraction check
    print("\n[2] Testing real PDF text extraction...")
    extracted_text = PDFService.extract_text_from_pdf(sample_path)
    print(f"    Extracted text ({len(extracted_text)} chars):")
    for line in extracted_text.splitlines():
        if line.strip():
            print(f"      | {line.strip()}")
    assert "powerhouse" in extracted_text.lower(), "Question 1 missing from extracted text!"
    assert "stomach" in extracted_text.lower(), "Question 2 missing from extracted text!"
    print("    -> PDF text extraction: PASS")

    # Step 2: Full pipeline processing
    print("\n[3] Executing complete production PipelineService with live Gemini API...")
    uploaded_file = MockUploadedFile(pdf_bytes, "test_real_class10_science.pdf")
    
    progress_log = []
    def on_progress(msg, pct):
        progress_log.append(f"[{pct}%] {msg}")
        print(f"    Pipeline progress: [{pct}%] {msg}")

    result = PipelineService.process_pdf_question_bank(
        uploaded_file=uploaded_file,
        target_class=10,
        target_subject="Science",
        use_ai_extraction=False,  # Use standard regex extractor on clean PDF text
        progress_callback=on_progress
    )

    print("\n[4] Inspecting Pipeline Execution Results:")
    print(f"    Success           : {result.get('success')}")
    print(f"    Message           : {result.get('message')}")
    print(f"    Total Extracted   : {result.get('total_extracted')}")
    print(f"    Verified Count    : {result.get('verified_count')}")
    print(f"    AI Verified Count : {result.get('ai_verified_count')}")
    print(f"    Review Count      : {result.get('review_count')}")
    print(f"    Saved Count       : {result.get('saved_count')}")

    assert result.get("success"), "Pipeline failed to execute successfully!"
    assert result.get("total_extracted") >= 2, f"Expected at least 2 questions, got {result.get('total_extracted')}"

    # Verify questions in repository
    print("\n[5] Verifying questions in repository:")
    for q in (result["verified_questions"] + result["needs_review_questions"]):
        print(f"    ID: {q.id} | Class {q.class_level} {q.subject} | Status: {q.verification_status}")
        print(f"      Q: {q.question_text}")
        print(f"      Correct Ans: {q.correct_answer} (Confidence: {q.answer_confidence})")
        print(f"      Explanation: {q.explanation}")
        
        # Verify can be retrieved from QuestionRepository
        retrieved = QuestionRepository.get_question_by_id(q.id)
        assert retrieved is not None, f"Failed to retrieve question ID {q.id} from repository!"
        assert retrieved.question_text == q.question_text, "Retrieved text mismatch!"

    print("\n[SUCCESS] REAL PDF PIPELINE TEST PASSED: Full lifecycle from PDF to verified questions executed cleanly!")
    return True

if __name__ == "__main__":
    run_real_pdf_pipeline_test()
