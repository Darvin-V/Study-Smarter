"""
Real-world validation script for live Gemini API call.
Sends one harmless Class 10 Science MCQ through production AIService.
"""

import sys
import os
from src.config import config
from src.services.ai_service import AIService

def run_real_gemini_test():
    assert bool(config.GEMINI_API_KEY), "GEMINI_API_KEY not loaded from .env"
    print(f"[+] GEMINI_API_KEY loaded successfully (length: {len(config.GEMINI_API_KEY)})")
    print(f"[+] Target Model: {config.AI_MODEL_NAME}")

    # Harmless Class 10 Science MCQ
    q_text = "Which cell organelle is commonly known as the powerhouse of the cell?"
    options = {
        "A": "Mitochondria",
        "B": "Ribosome",
        "C": "Golgi Apparatus",
        "D": "Lysosome"
    }

    print("[+] Calling live Gemini API via AIService.solve_and_verify_question...")
    result = AIService.solve_and_verify_question(
        question_text=q_text,
        options=options,
        class_level=10,
        subject="Science",
        chapter="Life Processes",
        topic="Cellular Respiration"
    )

    print("\n--- Live Gemini API Result ---")
    print(f"Correct Answer     : {result.get('correct_answer')}")
    print(f"Confidence Level   : {result.get('confidence')}")
    print(f"Confidence Score   : {result.get('confidence_score')}")
    print(f"Verification Status: {result.get('verification_status')}")
    print(f"In Scope           : {result.get('in_scope')}")
    print(f"Explanation        : {result.get('explanation')}")

    # Assertions
    assert result.get("correct_answer") == "A", f"Expected 'A', got {result.get('correct_answer')}"
    assert bool(result.get("explanation")), "Explanation is missing"
    assert result.get("confidence") in ["High", "Medium", "Low"], f"Invalid confidence: {result.get('confidence')}"
    assert result.get("verification_status") in ["VERIFIED", "AI_VERIFIED", "NEEDS_REVIEW"], f"Invalid status: {result.get('verification_status')}"

    print("\n[SUCCESS] REAL SERVICE TEST PASSED: Gemini API successfully resolved Class 10 Science MCQ.")
    return True

if __name__ == "__main__":
    try:
        run_real_gemini_test()
    except Exception as e:
        print(f"\n[FAILED] Real Gemini test error: {e}", file=sys.stderr)
        sys.exit(1)
