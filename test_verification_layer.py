"""
Study Smarter - Independent Answer Verification Layer Test
Tests deterministic Python numerical verification (VERIFIED),
disagreement detection (NEEDS_REVIEW), ambiguous/low confidence handling (NEEDS_REVIEW),
API failure resilience (NEEDS_REVIEW), and high-confidence conceptual questions (AI_VERIFIED).

Usage:
  python test_verification_layer.py
"""

from src.services.verification_service import VerificationService
from src.services.ai_service import AIService
from src.services.quiz_service import QuizService
from src.models.schemas import QuestionModel


def run_verification_layer_tests():
    print("=" * 65)
    print("  STUDY SMARTER - INDEPENDENT ANSWER-VERIFICATION LAYER TEST")
    print("=" * 65)

    # 1. Test Correct Numerical Answer (Python Verification Agrees -> VERIFIED)
    print("\n[Test 1/5] Testing Correct Numerical Answer (Python Solver Agrees -> VERIFIED)...")
    num_q = "A charge of 2 uC is placed in an electric field of 100 N/C. Calculate force."
    num_opts = {
        "A": "2 x 10^-4 N",
        "B": "5 x 10^-2 N",
        "C": "200 N",
        "D": "0.5 N"
    }

    res_correct_num = VerificationService.verify_answer(
        question_text=num_q,
        options=num_opts,
        proposed_answer="A",  # Correct calculation: 2e-6 * 100 = 2e-4 N (Option A)
        confidence="High",
        explanation="F = q * E = 2e-6 * 100 = 2e-4 N."
    )
    print(f"  Result: Status='{res_correct_num['verification_status']}', Method='{res_correct_num['verification_method']}'")
    assert res_correct_num["verification_status"] == "VERIFIED"
    assert res_correct_num["correct_answer"] == "A"
    assert res_correct_num["python_agreed"] is True
    print("  [OK] Correct Numerical Answer Verification PASSED (Marked VERIFIED).")

    # 2. Test Incorrect Numerical Answer (Python Verification Disagrees -> NEEDS_REVIEW)
    print("\n[Test 2/5] Testing Incorrect Numerical Answer (Python Solver Disagrees -> NEEDS_REVIEW)...")
    res_incorrect_num = VerificationService.verify_answer(
        question_text=num_q,
        options=num_opts,
        proposed_answer="C",  # Flawed proposed answer (200 N instead of 2e-4 N)
        confidence="High",
        explanation="Flawed reasoning proposing Option C."
    )
    print(f"  Result: Status='{res_incorrect_num['verification_status']}', Method='{res_incorrect_num['verification_method']}'")
    print(f"  Warning Message: '{res_incorrect_num['explanation'][:90]}...'")
    assert res_incorrect_num["verification_status"] == "NEEDS_REVIEW"
    assert res_incorrect_num["python_agreed"] is False
    print("  [OK] Incorrect Numerical Answer Detection PASSED (Marked NEEDS_REVIEW).")

    # 3. Test Ambiguous Response / Low Confidence -> NEEDS_REVIEW
    print("\n[Test 3/5] Testing Ambiguous Question / Low Confidence -> NEEDS_REVIEW...")
    res_low_conf = VerificationService.verify_answer(
        question_text="What is the behavior of charges near boundary under unspecified dielectric?",
        options={"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"},
        proposed_answer="B",
        confidence="Low",
        explanation="Ambiguous boundary conditions."
    )
    print(f"  Result: Status='{res_low_conf['verification_status']}', Method='{res_low_conf['verification_method']}'")
    assert res_low_conf["verification_status"] == "NEEDS_REVIEW"
    print("  [OK] Ambiguous / Low Confidence Test PASSED (Marked NEEDS_REVIEW).")

    # 4. Test API Failure Resilience -> NEEDS_REVIEW
    print("\n[Test 4/5] Testing API Failure Fallback -> NEEDS_REVIEW...")
    fallback_res = AIService._fallback_heuristic_solver(
        question_text="Conceptual physics question without formula",
        options={"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"}
    )
    print(f"  Result: Status='{fallback_res['verification_status']}', Method='{fallback_res['verification_method']}'")
    assert fallback_res["verification_status"] == "NEEDS_REVIEW"
    print("  [OK] API Failure Handling PASSED (Gracefully set NEEDS_REVIEW).")

    # 5. Test High Confidence Conceptual Question -> AI_VERIFIED
    print("\n[Test 5/5] Testing Conceptual MCQ (High Confidence Model -> AI_VERIFIED)...")
    res_conceptual = VerificationService.verify_answer(
        question_text="SI unit of electric charge is Coulomb.",
        options={"A": "Coulomb", "B": "Ampere", "C": "Volt", "D": "Ohm"},
        proposed_answer="A",
        confidence="High",
        explanation="Standard definition of electric charge unit."
    )
    print(f"  Result: Status='{res_conceptual['verification_status']}', Method='{res_conceptual['verification_method']}'")
    assert res_conceptual["verification_status"] == "AI_VERIFIED"
    assert res_conceptual["correct_answer"] == "A"
    print("  [OK] High Confidence Conceptual MCQ PASSED (Marked AI_VERIFIED).")

    print("\n" + "=" * 65)
    print("[SUCCESS] ALL INDEPENDENT VERIFICATION LAYER TESTS PASSED!")
    print("=" * 65)
    return True


if __name__ == "__main__":
    run_verification_layer_tests()
