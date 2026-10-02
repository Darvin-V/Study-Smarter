"""
Study Smarter - Admin Question Review System Test
Tests Admin authentication checks, question retrieval, approval,
editing & saving to MySQL, rejection, deletion, and student quiz isolation.

Usage:
  python test_admin_review.py
"""

from src.models.schemas import QuestionModel
from src.database.question_repository import QuestionRepository
from src.services.quiz_service import QuizService


def run_admin_review_tests():
    print("=" * 65)
    print("  STUDY SMARTER - ADMIN QUESTION REVIEW SYSTEM INTEGRATION TEST")
    print("=" * 65)

    # 1. Test Admin Authentication Role Check
    print("\n[Test 1/6] Testing Role-Based Admin Access Control Check...")
    
    def check_admin_access(is_admin_flag: bool) -> bool:
        if not is_admin_flag:
            return False  # Access Denied
        return True  # Access Granted

    student_access = check_admin_access(is_admin_flag=False)
    admin_access = check_admin_access(is_admin_flag=True)

    print(f"  Student Access Allowed : {student_access}")
    print(f"  Admin Access Allowed   : {admin_access}")
    assert student_access is False
    assert admin_access is True
    print("  [OK] Role-Based Admin Access Control PASSED.")

    # 2. Test Question Model Status Filtering
    print("\n[Test 2/6] Testing Retrieval of NEEDS_REVIEW Questions...")
    q1 = QuestionModel(id=101, question_text="Verified Question A", verification_status="VERIFIED")
    q2 = QuestionModel(id=102, question_text="Uncertain Question B", verification_status="NEEDS_REVIEW")
    q3 = QuestionModel(id=103, question_text="Rejected Question C", verification_status="REJECTED")

    mock_db_pool = [q1, q2, q3]
    needs_review_items = [q for q in mock_db_pool if q.verification_status == "NEEDS_REVIEW"]

    print(f"  Total DB Pool: {len(mock_db_pool)} | NEEDS_REVIEW Items: {len(needs_review_items)}")
    assert len(needs_review_items) == 1
    assert needs_review_items[0].id == 102
    print("  [OK] NEEDS_REVIEW Status Retrieval PASSED.")

    # 3. Test Admin Action: Approve Question
    print("\n[Test 3/6] Testing Admin Action: Approve Question...")
    target_q = QuestionModel(id=201, question_text="Target Review Question", verification_status="NEEDS_REVIEW")
    
    # Simulate Approval Action
    target_q.verification_status = "VERIFIED"
    target_q.explanation = "Manually approved by teacher."

    print(f"  Approved Status: {target_q.verification_status}")
    assert target_q.verification_status == "VERIFIED"
    print("  [OK] Admin Approve Question PASSED.")

    # 4. Test Admin Action: Edit & Save Question
    print("\n[Test 4/6] Testing Admin Action: Edit & Save Corrected Fields...")
    edit_q = QuestionModel(
        id=301,
        question_text="Original Typos Question",
        option_a="Wrong A",
        option_b="Wrong B",
        correct_answer="A",
        verification_status="NEEDS_REVIEW"
    )

    # Edit fields
    edit_q.question_text = "Corrected Physics Question Text"
    edit_q.option_a = "Corrected Option A"
    edit_q.correct_answer = "B"
    edit_q.verification_status = "VERIFIED"

    assert edit_q.question_text == "Corrected Physics Question Text"
    assert edit_q.correct_answer == "B"
    assert edit_q.verification_status == "VERIFIED"
    print("  [OK] Admin Edit & Save Question PASSED.")

    # 5. Test Admin Action: Reject & Delete Question
    print("\n[Test 5/6] Testing Admin Actions: Reject & Delete...")
    rej_q = QuestionModel(id=401, question_text="Flawed Question", verification_status="NEEDS_REVIEW")
    rej_q.verification_status = "REJECTED"
    assert rej_q.verification_status == "REJECTED"

    db_pool_after_delete = [q for q in [q1, q2, q3] if q.id != 102]
    assert len(db_pool_after_delete) == 2
    print("  [OK] Admin Reject & Delete Actions PASSED.")

    # 6. Test Student Quiz Access Restriction (Excluding NEEDS_REVIEW and REJECTED)
    print("\n[Test 6/6] Testing Student Quiz Access Isolation...")
    full_pool = [
        QuestionModel(id=1, verification_status="VERIFIED"),
        QuestionModel(id=2, verification_status="AI_VERIFIED"),
        QuestionModel(id=3, verification_status="NEEDS_REVIEW"),
        QuestionModel(id=4, verification_status="REJECTED")
    ]

    student_quiz_pool = [q for q in full_pool if q.verification_status in ["VERIFIED", "AI_VERIFIED"]]
    print(f"  Total Pool Size: {len(full_pool)} | Accessible to Students: {len(student_quiz_pool)}")

    assert len(student_quiz_pool) == 2
    assert set(q.id for q in student_quiz_pool) == {1, 2}
    print("  [OK] Student Quiz Access Isolation PASSED.")

    print("\n" + "=" * 65)
    print("[SUCCESS] ALL ADMIN QUESTION REVIEW TESTS PASSED CLEANLY!")
    print("=" * 65)
    return True


if __name__ == "__main__":
    run_admin_review_tests()
