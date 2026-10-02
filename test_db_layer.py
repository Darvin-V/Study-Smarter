"""
Study Smarter - Database Layer Verification Script
Tests MySQL connection, table schema creation, SQL query parameterization, and Question CRUD operations.

Usage:
  python test_db_layer.py
"""

from unittest.mock import MagicMock
from src.config import config
from src.logger import logger
from src.database import DatabaseManager, init_db, QuestionRepository
from src.models.schemas import QuestionModel


def test_sql_parameterization():
    """Validates SQL statement structure and parameterized bindings (%s) offline."""
    print("\n[Offline Validation] Testing SQL Parameterization & DAO Query Integrity...")
    
    mock_cursor = MagicMock()
    mock_cursor.lastrowid = 42
    mock_cursor.rowcount = 1
    mock_row = {
        "id": 42,
        "class": 12,
        "subject": "Physics",
        "chapter": "Electrostatics",
        "topic": "Electric Potential",
        "question_text": "Sample MCQ?",
        "option_a": "Opt A",
        "option_b": "Opt B",
        "option_c": "Opt C",
        "option_d": "Opt D",
        "correct_answer": "A",
        "explanation": "Exp",
        "difficulty": "Easy",
        "source_pdf": "test.pdf",
        "answer_confidence": 0.95,
        "verification_status": "VERIFIED",
        "created_at": None,
    }
    mock_cursor.fetchone.side_effect = [None, mock_row, mock_row, mock_row]
    mock_cursor.fetchall.return_value = [mock_row]

    sample_q = QuestionModel(
        class_level=12,
        subject="Physics",
        chapter="Electrostatics",
        topic="Electric Potential",
        question_text="Sample MCQ?",
        option_a="Opt A",
        option_b="Opt B",
        option_c="Opt C",
        option_d="Opt D",
        correct_answer="A",
        explanation="Exp",
        difficulty="Easy",
        source_pdf="test.pdf",
        answer_confidence=0.95,
        verification_status="VERIFIED",
    )

    from unittest.mock import patch

    with patch("src.database.question_repository.get_db_cursor") as mock_get_cursor:
        mock_get_cursor.return_value.__enter__.return_value = mock_cursor

        # 1. Test CREATE
        inserted_id = QuestionRepository.create_question(sample_q)
        assert inserted_id == 42
        sql_inserted, params_inserted = mock_cursor.execute.call_args[0]
        assert "INSERT INTO questions" in sql_inserted
        assert len(params_inserted) == 15
        assert sql_inserted.count("%s") == 15
        print("  [OK] Parameterized INSERT query syntax verified (15 parameters bound).")

        # 2. Test READ (by ID)
        fetched = QuestionRepository.get_question_by_id(42)
        assert fetched is not None and fetched.id == 42
        sql_read, params_read = mock_cursor.execute.call_args[0]
        assert "SELECT * FROM questions WHERE id = %s" in sql_read
        assert params_read == (42,)
        print("  [OK] Parameterized SELECT BY ID query syntax verified.")

        # 3. Test READ (by Class and Subject)
        fetched_list = QuestionRepository.get_questions_by_class_and_subject(12, "Physics")
        assert len(fetched_list) == 1
        sql_filter, params_filter = mock_cursor.execute.call_args[0]
        assert "WHERE class = %s AND subject = %s" in sql_filter
        assert params_filter == (12, "Physics")
        print("  [OK] Parameterized SELECT FILTER query syntax verified.")

        # 4. Test UPDATE
        updated = QuestionRepository.update_question(42, {"difficulty": "Hard", "verification_status": "VERIFIED"})
        assert updated is True
        sql_update, params_update = mock_cursor.execute.call_args[0]
        assert "UPDATE questions SET" in sql_update
        assert "difficulty = %s" in sql_update
        assert params_update == ["Hard", "VERIFIED", 42]
        print("  [OK] Parameterized UPDATE query syntax verified.")

        # 5. Test DELETE
        deleted = QuestionRepository.delete_question(42)
        assert deleted is True
        sql_delete, params_delete = mock_cursor.execute.call_args[0]
        assert "DELETE FROM questions WHERE id = %s" in sql_delete
        assert params_delete == (42,)
        print("  [OK] Parameterized DELETE query syntax verified.")

    print("[OK] Offline SQL Parameterization & CRUD Logic Verification: PASSED (100% Correct)")


def run_database_tests():
    print("=" * 65)
    print("  STUDY SMARTER - MYSQL DATABASE LAYER INTEGRATION TEST")
    print("=" * 65)

    # Offline SQL Parameterization Check
    test_sql_parameterization()

    # -------------------------------------------------------------
    # Step 1: Check Live Database Connection
    # -------------------------------------------------------------
    print("\n[Step 1/6] Checking MySQL database server connection...")
    db_status = DatabaseManager.test_connection()
    if not db_status["success"]:
        print(f"[!] Live Database Connection Report: {db_status['message']}")
        print("    --> Note: If your local MySQL server is not running or credentials")
        print("        in '.env' differ, please start MySQL service and update '.env'.")
        print("    --> Live MySQL server connection test: SKIPPED (MySQL Server offline).")
        return True

    print(f"[OK] Connection Successful: {db_status['message']}")

    # -------------------------------------------------------------
    # Step 2: Check Table Creation / Schema Initialization
    # -------------------------------------------------------------
    print("\n[Step 2/6] Initializing database schema (users, quizzes, questions, attempts)...")
    try:
        schema_ok = init_db()
        if schema_ok:
            print("[OK] Schema Initialization Successful! All 4 tables created/verified.")
        else:
            print("[!] Schema initialization returned False.")
            return False
    except Exception as err:
        print(f"[X] Schema Initialization Error: {err}")
        return False

    # -------------------------------------------------------------
    # Step 3: Test Inserting a Sample Question (Create)
    # -------------------------------------------------------------
    print("\n[Step 3/6] Testing INSERT question (Create)...")
    sample_q = QuestionModel(
        class_level=12,
        subject="Physics",
        chapter="Electrostatics",
        topic="Electric Charges and Fields",
        question_text="What is the unit of electric field intensity?",
        option_a="Newton per Coulomb (N/C)",
        option_b="Volt per meter (V/m)",
        option_c="Both A and B",
        option_d="Joule per Coulomb (J/C)",
        correct_answer="C",
        explanation="Electric field E = F/q (N/C) and E = -dV/dr (V/m). Both units are equivalent.",
        difficulty="Medium",
        source_pdf="ch1_physics_class12.pdf",
        answer_confidence=0.98,
        verification_status="VERIFIED",
    )

    try:
        new_id = QuestionRepository.create_question(sample_q)
        print(f"[OK] Question inserted successfully with ID = {new_id}")
    except Exception as err:
        print(f"[X] Insert Question Failed: {err}")
        return False

    # -------------------------------------------------------------
    # Step 4: Test Retrieving the Question (Read)
    # -------------------------------------------------------------
    print(f"\n[Step 4/6] Testing SELECT question by ID={new_id} (Read)...")
    try:
        fetched_q = QuestionRepository.get_question_by_id(new_id)
        if fetched_q and fetched_q.id == new_id:
            print(f"[OK] Retrieved Question successfully:")
            print(f"     Text       : '{fetched_q.question_text}'")
            print(f"     Class/Subj : Class {fetched_q.class_level} {fetched_q.subject}")
            print(f"     Answer     : Option {fetched_q.correct_answer}")
            print(f"     Source PDF : {fetched_q.source_pdf}")
            print(f"     Status     : {fetched_q.verification_status}")
        else:
            print(f"[X] Could not find inserted question ID={new_id}!")
            return False
    except Exception as err:
        print(f"[X] Retrieve Question Failed: {err}")
        return False

    # -------------------------------------------------------------
    # Step 5: Test Updating the Question (Update)
    # -------------------------------------------------------------
    print(f"\n[Step 5/6] Testing UPDATE question ID={new_id} (Update)...")
    try:
        update_data = {
            "difficulty": "Easy",
            "explanation": "Updated explanation: Electric field intensity unit is N/C or V/m.",
            "verification_status": "AI_VERIFIED"
        }
        updated = QuestionRepository.update_question(new_id, update_data)
        if updated:
            verify_q = QuestionRepository.get_question_by_id(new_id)
            print(f"[OK] Question updated successfully! New difficulty='{verify_q.difficulty}', Status='{verify_q.verification_status}'")
        else:
            print(f"[X] Update returned False!")
            return False
    except Exception as err:
        print(f"[X] Update Question Failed: {err}")
        return False

    # -------------------------------------------------------------
    # Step 6: Test Deleting the Question (Delete)
    # -------------------------------------------------------------
    print(f"\n[Step 6/6] Testing DELETE question ID={new_id} (Delete)...")
    try:
        deleted = QuestionRepository.delete_question(new_id)
        if deleted:
            check_del = QuestionRepository.get_question_by_id(new_id)
            if check_del is None:
                print(f"[OK] Question ID={new_id} deleted cleanly from MySQL database.")
            else:
                print(f"[X] Question still exists after deletion!")
                return False
        else:
            print(f"[X] Delete returned False!")
            return False
    except Exception as err:
        print(f"[X] Delete Question Failed: {err}")
        return False

    print("\n" + "=" * 65)
    print("[SUCCESS] ALL MYSQL DATABASE LAYER TESTS COMPLETED CLEANLY!")
    print("=" * 65)
    return True


if __name__ == "__main__":
    run_database_tests()
