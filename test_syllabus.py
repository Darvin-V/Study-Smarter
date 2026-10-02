"""
Study Smarter - NCERT Syllabus Management Verification Script
Tests Class 10/12 selection, subject retrieval, chapter retrieval, topic retrieval,
and invalid chapter/topic validation handling.

Usage:
  python test_syllabus.py
"""

from src.services import (
    SyllabusService,
    get_classes,
    get_subjects,
    get_chapters,
    get_topics,
    validate_chapter,
    validate_topic,
)


def run_syllabus_tests():
    print("=" * 65)
    print("  STUDY SMARTER - NCERT SYLLABUS MANAGEMENT SYSTEM TEST")
    print("=" * 65)

    # 1. Test Class Selection (Only Class 10 & 12 allowed)
    print("\n[Test 1/7] Testing Supported Class Levels Selection...")
    classes = get_classes()
    print(f"  Supported Classes: {classes}")
    assert classes == [10, 12], f"Expected [10, 12], got {classes}"
    print("  [OK] Class Selection Test PASSED.")

    # 2. Test Class 10 Subject Retrieval
    print("\n[Test 2/7] Testing Class 10 Subject Retrieval...")
    class10_subjects = get_subjects(10)
    print(f"  Class 10 Subjects: {class10_subjects}")
    assert "Science" in class10_subjects and "Mathematics" in class10_subjects
    print("  [OK] Class 10 Subject Retrieval PASSED.")

    # 3. Test Class 12 Subject Retrieval
    print("\n[Test 3/7] Testing Class 12 Subject Retrieval...")
    class12_subjects = get_subjects(12)
    print(f"  Class 12 Subjects: {class12_subjects}")
    assert "Physics" in class12_subjects and "Chemistry" in class12_subjects and "Biology" in class12_subjects
    assert "Mathematics" in class12_subjects and "Computer Science" in class12_subjects
    print("  [OK] Class 12 Subject Retrieval PASSED.")

    # 4. Test Chapter Retrieval for Class 10 & Class 12
    print("\n[Test 4/7] Testing Chapter Retrieval...")
    c10_sci_chapters = get_chapters(10, "Science")
    print(f"  Class 10 Science Chapters ({len(c10_sci_chapters)}): {c10_sci_chapters[:3]} ...")
    assert "Life Processes" in c10_sci_chapters
    assert "Electricity" in c10_sci_chapters

    c12_phy_chapters = get_chapters(12, "Physics")
    print(f"  Class 12 Physics Chapters ({len(c12_phy_chapters)}): {c12_phy_chapters[:3]} ...")
    assert "Electric Charges and Fields" in c12_phy_chapters
    assert "Semiconductor Electronics" in c12_phy_chapters
    print("  [OK] Chapter Retrieval PASSED.")

    # 5. Test Topic Retrieval for Class 12 Physics & Class 10 Science
    print("\n[Test 5/7] Testing Topic Retrieval...")
    phy_topics = get_topics(12, "Physics", "Electric Charges and Fields")
    print(f"  Topics under Class 12 Physics 'Electric Charges and Fields': {phy_topics}")
    assert len(phy_topics) > 0
    assert "Gauss's Law and Applications" in phy_topics

    sci_topics = get_topics(10, "Science", "Life Processes")
    print(f"  Topics under Class 10 Science 'Life Processes': {sci_topics}")
    assert "Respiration in Humans" in sci_topics
    print("  [OK] Topic Retrieval PASSED.")

    # 6. Test Invalid Chapter & Topic Validation (Prevent Arbitrary AI Chapter Invention)
    print("\n[Test 6/7] Testing Invalid Chapter & Topic Handling...")
    valid_ch_check = validate_chapter(12, "Physics", "Electric Charges and Fields")
    print(f"  Validating official chapter 'Electric Charges and Fields': {valid_ch_check}")
    assert valid_ch_check is True

    invalid_ch_check = validate_chapter(12, "Physics", "Arbitrary AI Invented Chapter 99")
    print(f"  Validating fake chapter 'Arbitrary AI Invented Chapter 99': {invalid_ch_check}")
    assert invalid_ch_check is False

    invalid_topic_check = validate_topic(12, "Physics", "Electric Charges and Fields", "Quantum Teleportation Mechanics")
    print(f"  Validating fake topic under official chapter: {invalid_topic_check}")
    assert invalid_topic_check is False
    print("  [OK] Invalid Chapter & Topic Validation PASSED.")

    # 7. Test Unsupported Class Handling (e.g. Class 8 or Class 11)
    print("\n[Test 7/7] Testing Unsupported Class Level Handling...")
    unsupported_subj = get_subjects(8)
    print(f"  Subjects for Class 8 (Unsupported): {unsupported_subj}")
    assert unsupported_subj == []

    unsupported_val = validate_chapter(8, "Science", "Cell Structure")
    print(f"  Validating chapter for Class 8: {unsupported_val}")
    assert unsupported_val is False
    print("  [OK] Unsupported Class Level Handling PASSED.")

    print("\n" + "=" * 65)
    print("[SUCCESS] ALL NCERT SYLLABUS MANAGEMENT TESTS PASSED CLEANLY!")
    print("=" * 65)
    return True


if __name__ == "__main__":
    run_syllabus_tests()
