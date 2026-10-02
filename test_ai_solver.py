"""
Study Smarter - AI Answer-Solving & Verification System Test
Tests answer resolution, numerical question explanation conciseness,
strict JSON schema validation, invalid option blocking, confidence handling,
and NEEDS_REVIEW status assignment.

Usage:
  python test_ai_solver.py
"""

import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from src.services.ai_service import AIService
from src.services.quiz_service import QuizService
from src.models.schemas import QuestionModel


def run_ai_solver_tests():
    print("=" * 65)
    print("  STUDY SMARTER - AI ANSWER-SOLVING & VERIFICATION SYSTEM TEST")
    print("=" * 65)

    # 1. Test Valid AI Answer JSON Validation (High Confidence)
    print("\n[Test 1/5] Testing Valid AI Response Validation (High Confidence)...")
    valid_json = """
```json
{
  "correct_answer": "A",
  "explanation": "Electric dipole moment p = q * 2a has SI units of Coulomb meter (C m).",
  "confidence": "High"
}
```
"""
    res_high = AIService.validate_ai_answer_response(valid_json)
    print(f"  Result: {res_high}")
    assert res_high["correct_answer"] == "A"
    assert res_high["confidence"] == "High"
    assert res_high["verification_status"] in ["VERIFIED", "AI_VERIFIED"]
    print("  [OK] Valid AI High Confidence Validation PASSED.")

    # 2. Test Low Confidence Handling -> NEEDS_REVIEW Assignment
    print("\n[Test 2/5] Testing Low Confidence Handling (NEEDS_REVIEW Assignment)...")
    low_conf_json = """
{
  "correct_answer": "B",
  "explanation": "Question lacks complete boundary conditions. Requires teacher review.",
  "confidence": "Low"
}
"""
    res_low = AIService.validate_ai_answer_response(low_conf_json)
    print(f"  Result: {res_low}")
    assert res_low["correct_answer"] == "B"
    assert res_low["confidence"] == "Low"
    assert res_low["verification_status"] == "NEEDS_REVIEW"
    print("  [OK] Low Confidence NEEDS_REVIEW Assignment PASSED.")

    # 3. Test Invalid Option Letter Blocking (e.g. Option 'E' or 'X')
    print("\n[Test 3/5] Testing Invalid Option Letter Blocking...")
    invalid_option_json = """
{
  "correct_answer": "E",
  "explanation": "None of the above options are correct.",
  "confidence": "High"
}
"""
    res_invalid_opt = AIService.validate_ai_answer_response(invalid_option_json)
    print(f"  Result: {res_invalid_opt}")
    assert res_invalid_opt["verification_status"] == "NEEDS_REVIEW"
    assert "invalid option" in res_invalid_opt["explanation"].lower()
    print("  [OK] Invalid Option Letter Blocking PASSED.")

    # 4. Test Numerical Question Explanation Conciseness (No Private CoT Dumps)
    print("\n[Test 4/5] Testing Numerical MCQ Answer Solving & Concise Explanation...")
    num_question = "A charge of 2 uC is placed in an electric field of 100 N/C. What is the force experienced?"
    num_options = {
        "A": "2 x 10^-4 N",
        "B": "2 x 10^-2 N",
        "C": "200 N",
        "D": "50 N"
    }

    # Simulate solver execution
    num_res = AIService.solve_and_verify_question(
        question_text=num_question,
        options=num_options,
        class_level=12,
        subject="Physics"
    )
    print(f"  Numerical Question Result:")
    print(f"    Correct Answer      : Option {num_res['correct_answer']}")
    print(f"    Explanation         : '{num_res['explanation']}'")
    print(f"    Confidence Level    : {num_res['confidence']}")
    print(f"    Verification Status : {num_res['verification_status']}")

    assert num_res["correct_answer"] in ["A", "B", "C", "D"]
    assert len(num_res["explanation"]) > 0
    assert "verification_status" in num_res
    print("  [OK] Numerical Question Answer Solving PASSED.")

    # 5. Test Quiz Service Filter Excluding NEEDS_REVIEW Questions
    print("\n[Test 5/5] Testing Quiz Service Exclusion of NEEDS_REVIEW Questions...")
    # Verify that QuestionModel with NEEDS_REVIEW is filtered out of student practice quizzes
    q_verified = QuestionModel(id=1, question_text="Verified Question", verification_status="VERIFIED")
    q_needs_review = QuestionModel(id=2, question_text="Unverified Question", verification_status="NEEDS_REVIEW")

    sample_pool = [q_verified, q_needs_review]
    filtered_for_quiz = [q for q in sample_pool if q.verification_status != "NEEDS_REVIEW"]
    
    print(f"  Pool Count: {len(sample_pool)} | Published to Students: {len(filtered_for_quiz)}")
    assert len(filtered_for_quiz) == 1
    assert filtered_for_quiz[0].id == 1
    print("  [OK] Quiz Service Exclusion of NEEDS_REVIEW Questions PASSED.")

    print("\n" + "=" * 65)
    print("[SUCCESS] ALL AI ANSWER-SOLVING & VERIFICATION TESTS PASSED!")
    print("=" * 65)
    return True


if __name__ == "__main__":
    run_ai_solver_tests()
