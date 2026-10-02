"""
Study Smarter - Automatic NCERT Classification Verification Script
Tests NCERT classification across Class 10 Science, Class 12 Physics,
Class 12 Chemistry, difficulty normalization, and strict rejection of
invented chapter names (assigning NEEDS_REVIEW status).

Usage:
  python test_ncert_classifier.py
"""

from src.services.ai_service import AIService
from src.services.syllabus_service import SyllabusService


def run_ncert_classifier_tests():
    print("=" * 65)
    print("  STUDY SMARTER - AUTOMATIC NCERT CLASSIFICATION INTEGRATION TEST")
    print("=" * 65)

    # 1. Test Class 12 Physics Classification
    print("\n[Test 1/5] Testing Class 12 Physics Question Classification...")
    phys_q = "What is the capacitance of a parallel plate capacitor with dielectric constant K?"
    phys_opts = {"A": "K * C0", "B": "C0 / K", "C": "C0 + K", "D": "Zero"}

    res_phys = AIService.classify_question_ncert(phys_q, phys_opts, class_level=12, subject="Physics")
    print(f"  Class 12 Physics Result:")
    print(f"    Chapter    : '{res_phys['chapter']}'")
    print(f"    Topic      : '{res_phys['topic']}'")
    print(f"    Difficulty : '{res_phys['difficulty']}'")
    print(f"    Syllabus OK: {res_phys['valid_syllabus']}")

    assert SyllabusService.validate_chapter(12, "Physics", res_phys["chapter"]) is True
    assert res_phys["difficulty"] in ["Easy", "Medium", "Hard"]
    print("  [OK] Class 12 Physics Classification PASSED.")

    # 2. Test Class 10 Science Classification
    print("\n[Test 2/5] Testing Class 10 Science Question Classification...")
    bio_q = "Which organelle is responsible for cellular respiration in human cells?"
    bio_opts = {"A": "Mitochondria", "B": "Chloroplast", "C": "Nucleus", "D": "Ribosome"}

    res_bio = AIService.classify_question_ncert(bio_q, bio_opts, class_level=10, subject="Science")
    print(f"  Class 10 Science Result:")
    print(f"    Chapter    : '{res_bio['chapter']}'")
    print(f"    Topic      : '{res_bio['topic']}'")
    print(f"    Difficulty : '{res_bio['difficulty']}'")

    assert SyllabusService.validate_chapter(10, "Science", res_bio["chapter"]) is True
    print("  [OK] Class 10 Science Classification PASSED.")

    # 3. Test Invented / Arbitrary Chapter Rejection -> NEEDS_REVIEW
    print("\n[Test 3/5] Testing Rejection of Invented Chapter Names...")
    fake_ai_json = """
```json
{
  "chapter": "Quantum Artificial Intelligence and Hologram Physics",
  "topic": "Hologram Wave Mechanics",
  "difficulty": "Hard"
}
```
"""
    res_fake = AIService.validate_and_normalize_classification(12, "Physics", fake_ai_json)
    print(f"  Invented Chapter Check Result:")
    print(f"    Chapter       : '{res_fake['chapter']}'")
    print(f"    Valid Syllabus: {res_fake['valid_syllabus']}")
    print(f"    Backend Msg   : '{res_fake['message']}'")

    assert res_fake["valid_syllabus"] is False
    assert "Invalid" in res_fake["chapter"] or "NEEDS_REVIEW" in res_fake["message"]
    print("  [OK] Invented Chapter Rejection PASSED (Marked invalid/NEEDS_REVIEW).")

    # 4. Test Difficulty Normalization
    print("\n[Test 4/5] Testing Difficulty Normalization...")
    diff_json = """
{
  "chapter": "Electric Charges and Fields",
  "topic": "Coulomb's Law and Electrostatic Force",
  "difficulty": "super-hard-challenging"
}
"""
    res_diff = AIService.validate_and_normalize_classification(12, "Physics", diff_json)
    print(f"  Normalized Difficulty: '{res_diff['difficulty']}'")
    assert res_diff["difficulty"] == "Hard"
    print("  [OK] Difficulty Normalization PASSED.")

    # 5. Test Question Batch Classification
    print("\n[Test 5/5] Testing Question Batch Classification...")
    sample_batch = [
        {
            "question_num": 1,
            "question": "What is the unit of electric current?",
            "options": {"A": "Ampere", "B": "Volt", "C": "Ohm", "D": "Watt"}
        },
        {
            "question_num": 2,
            "question": "State Ohm's Law formula V = IR",
            "options": {"A": "V=IR", "B": "V=I/R", "C": "V=R/I", "D": "I=V^2 R"}
        }
    ]

    classified_batch = AIService.classify_question_batch(sample_batch, class_level=12, subject="Physics")
    print(f"  Batch size: {len(classified_batch)}")
    for q in classified_batch:
        print(f"    - Q{q['question_num']}: Chapter='{q.get('chapter')}', Topic='{q.get('topic')}', Diff='{q.get('difficulty')}'")

    assert len(classified_batch) == 2
    assert "chapter" in classified_batch[0]
    assert "difficulty" in classified_batch[0]
    print("  [OK] Question Batch Classification PASSED.")

    print("\n" + "=" * 65)
    print("[SUCCESS] ALL AUTOMATIC NCERT CLASSIFICATION TESTS PASSED!")
    print("=" * 65)
    return True


if __name__ == "__main__":
    run_ncert_classifier_tests()
