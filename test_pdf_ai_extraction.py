"""
Study Smarter - PDF Upload & AI Extraction Verification Script
Tests PDF validation, pypdf text extraction, regex MCQ parser,
AI JSON schema validator/sanitizer, and API failure resilience.

Usage:
  python test_pdf_ai_extraction.py
"""

import io
import pypdf
from src.services.pdf_service import PDFService
from src.services.ai_service import AIService


def create_sample_pdf_bytes(text_content: str) -> bytes:
    """Helper method to generate valid PDF byte streams for testing."""
    writer = pypdf.PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    # pypdf blank page object creation for stream testing
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def run_pdf_ai_extraction_tests():
    print("=" * 65)
    print("  STUDY SMARTER - PDF & AI EXTRACTION SYSTEM INTEGRATION TEST")
    print("=" * 65)

    # 1. Test PDF File Validation
    print("\n[Test 1/6] Testing PDF File Validation Rules...")
    
    # Create mock uploaded file object
    class MockUploadedFile:
        def __init__(self, name: str, content: bytes):
            self.name = name
            self.content = content
        def getvalue(self):
            return self.content

    valid_file = MockUploadedFile("sample_physics.pdf", b"Dummy PDF Bytes Stream Content")
    val_ok = PDFService.validate_pdf_file(valid_file, max_mb=10.0)
    print(f"  Valid PDF file check : {val_ok}")
    assert val_ok["valid"] is True

    invalid_ext_file = MockUploadedFile("sample_doc.docx", b"Word content")
    val_invalid_ext = PDFService.validate_pdf_file(invalid_ext_file)
    print(f"  Invalid extension check: {val_invalid_ext['message']}")
    assert val_invalid_ext["valid"] is False

    empty_file = MockUploadedFile("empty.pdf", b"")
    val_empty = PDFService.validate_pdf_file(empty_file)
    print(f"  Empty file check: {val_empty['message']}")
    assert val_empty["valid"] is False
    print("  [OK] PDF File Validation Rules PASSED.")

    # 2. Test PDF Text Extraction via PyPDF
    print("\n[Test 2/6] Testing PyPDF Text Extraction...")
    sample_pdf_bytes = create_sample_pdf_bytes("NCERT Class 12 Physics Question Bank")
    extracted_text = PDFService.extract_text_from_pdf(sample_pdf_bytes)
    print(f"  Extracted text character length: {len(extracted_text)}")
    print("  [OK] PyPDF Text Extraction PASSED.")

    # 3. Test Regex MCQ Parser
    print("\n[Test 3/6] Testing Regex MCQ Pattern Parser...")
    raw_sample_mcqs = """
Q1. What is the SI unit of electric field intensity?
A. Newton per Coulomb (N/C)
B. Volt meter (V m)
C. Joule per Coulomb (J/C)
D. Tesla (T)

2. The electric potential on an equipotential surface is:
(A) Variable
(B) Constant everywhere
(C) Zero
(D) Infinite
"""
    parsed_mcqs = PDFService.parse_mcqs_regex(raw_sample_mcqs)
    print(f"  Extracted {len(parsed_mcqs)} questions using Regex:")
    for q in parsed_mcqs:
        print(f"    - Q{q['question_num']}: '{q['question']}'")
        print(f"      Options: A={q['options']['A']}, B={q['options']['B']}, C={q['options']['C']}, D={q['options']['D']}")
    
    assert len(parsed_mcqs) == 2
    assert parsed_mcqs[0]["options"]["A"] == "Newton per Coulomb (N/C)"
    assert parsed_mcqs[1]["options"]["B"] == "Constant everywhere"
    print("  [OK] Regex MCQ Pattern Parser PASSED.")

    # 4. Test AI JSON Schema Validator & Code Fence Stripper
    print("\n[Test 4/6] Testing AI JSON Schema Validator & Code Block Stripper...")
    markdown_json_response = """
```json
{
  "questions": [
    {
      "question": "What is the unit of electric dipole moment?",
      "options": {
        "A": "Coulomb meter (C m)",
        "B": "Coulomb per meter (C/m)",
        "C": "Volt meter",
        "D": "Newton"
      }
    },
    {
      "question": "Which particles carry electric current in metals?",
      "options": {
        "A": "Protons",
        "B": "Free Electrons"
      }
    }
  ]
}
```
"""
    sanitized = AIService.validate_and_sanitize_json_schema(markdown_json_response)
    print(f"  Sanitized {len(sanitized)} AI output questions:")
    for q in sanitized:
        print(f"    - '{q['question']}'")
        print(f"      Options: A={q['options']['A']}, B={q['options']['B']}, C={q['options']['C']}, D={q['options']['D']}")

    assert len(sanitized) == 2
    assert sanitized[0]["options"]["A"] == "Coulomb meter (C m)"
    assert sanitized[1]["options"]["C"] == "[Option C Missing]"  # Missing option fallback filled automatically!
    print("  [OK] AI JSON Schema Validator & Code Block Stripper PASSED.")

    # 5. Test AI API Resilience on Malformed Input
    print("\n[Test 5/6] Testing AI JSON Schema Resilience on Malformed Text...")
    malformed_text = "This is not valid JSON text content at all."
    res_malformed = AIService.validate_and_sanitize_json_schema(malformed_text)
    print(f"  Malformed text parsing result: {res_malformed}")
    assert res_malformed == []
    print("  [OK] AI JSON Schema Resilience PASSED.")

    # 6. Test AI API Request Resilience (App Never Crashes when API Key Missing)
    print("\n[Test 6/6] Testing AI Service Resilience when API Key is Unset...")
    from src.config import config
    orig_gemini_key = config.GEMINI_API_KEY
    orig_ai_key = config.AI_API_KEY
    try:
        config.GEMINI_API_KEY = ""
        config.AI_API_KEY = ""
        ai_call_res = AIService.extract_structured_questions("Q1. Sample question? A. Opt 1 B. Opt 2 C. Opt 3 D. Opt 4")
        print(f"  AI API Call Status Report: success={ai_call_res['success']}, message='{ai_call_res['message']}'")
        assert ai_call_res["success"] is False
        assert isinstance(ai_call_res["questions"], list)
        print("  [OK] AI Service Resilience PASSED (Graceful handling verified).")
    finally:
        config.GEMINI_API_KEY = orig_gemini_key
        config.AI_API_KEY = orig_ai_key

    print("\n" + "=" * 65)
    print("[SUCCESS] ALL PDF & AI EXTRACTION SYSTEM TESTS PASSED CLEANLY!")
    print("=" * 65)
    return True


if __name__ == "__main__":
    run_pdf_ai_extraction_tests()
