"""
Study Smarter - Question Repository Module
Provides CRUD operations for questions and question_banks tables using parameterized MySQL queries.
"""

from typing import List, Optional, Dict, Any
from src.database.connection import get_db_cursor
from src.models.schemas import QuestionModel, QuestionBankModel
from src.logger import logger
from src.utils.exceptions import DatabaseQueryError


class QuestionRepository:
    """Data Access Object (DAO) for managing questions in MySQL database with memory fallback."""

    _MEMORY_QUESTIONS: List[QuestionModel] = []
    _AUTO_ID_COUNTER: int = 1000

    # -----------------------------------------------------------------
    # In-memory fallback helpers (used only when MySQL is offline)
    # -----------------------------------------------------------------

    @classmethod
    def _create_in_memory(cls, question: QuestionModel) -> int:
        for existing in cls._MEMORY_QUESTIONS:
            if existing.question_text.strip().lower() == question.question_text.strip().lower():
                logger.info(f"Duplicate question detected in memory (ID={existing.id}). Skipping.")
                return existing.id
        cls._AUTO_ID_COUNTER += 1
        question_copy = QuestionModel(
            id=cls._AUTO_ID_COUNTER,
            class_level=question.class_level,
            subject=question.subject,
            chapter=question.chapter,
            topic=question.topic,
            question_text=question.question_text,
            option_a=question.option_a,
            option_b=question.option_b,
            option_c=question.option_c,
            option_d=question.option_d,
            correct_answer=question.correct_answer,
            explanation=question.explanation,
            difficulty=question.difficulty,
            source_pdf=question.source_pdf,
            answer_confidence=question.answer_confidence,
            verification_status=question.verification_status,
            bank_id=question.bank_id,
            bank_name=question.bank_name,
            is_persisted=False,
            created_at=question.created_at,
        )
        cls._MEMORY_QUESTIONS.append(question_copy)
        question.is_persisted = False
        return question_copy.id

    @classmethod
    def _sync_to_memory(cls, question: QuestionModel):
        for idx, q in enumerate(cls._MEMORY_QUESTIONS):
            if q.id == question.id or q.question_text == question.question_text:
                cls._MEMORY_QUESTIONS[idx] = question
                return
        cls._MEMORY_QUESTIONS.append(question)

    # -----------------------------------------------------------------
    # Question Bank operations
    # -----------------------------------------------------------------

    @staticmethod
    def get_question_banks() -> List[QuestionBankModel]:
        """Returns all question banks ordered by creation date with subject and class metadata."""
        banks: List[QuestionBankModel] = []
        try:
            query = """
                SELECT qb.id, qb.name, qb.source_pdf, qb.created_at,
                       COUNT(q.id) AS question_count,
                       COALESCE(MAX(q.subject), 'General') AS subject,
                       COALESCE(MAX(q.class), 0) AS class_level
                FROM question_banks qb
                LEFT JOIN questions q ON q.bank_id = qb.id
                GROUP BY qb.id, qb.name, qb.source_pdf, qb.created_at
                ORDER BY qb.id ASC
            """
            with get_db_cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                for row in (rows or []):
                    banks.append(QuestionBankModel(
                        id=row["id"],
                        name=row["name"],
                        source_pdf=row.get("source_pdf"),
                        question_count=int(row.get("question_count", 0)),
                        created_at=row.get("created_at"),
                        subject=row.get("subject", "General"),
                        class_level=int(row.get("class_level", 0)),
                    ))
        except Exception as err:
            logger.warning(f"Could not fetch question banks from MySQL: {err}")
        return banks

    @staticmethod
    def create_question_bank(name: str, source_pdf: Optional[str] = None) -> Optional[int]:
        """
        Creates a new question bank row if one with the same name doesn't already exist.
        Returns the bank ID (new or existing).
        """
        try:
            with get_db_cursor() as cursor:
                cursor.execute("SELECT id FROM question_banks WHERE name = %s", (name,))
                existing = cursor.fetchone()
                if existing:
                    return existing["id"] if isinstance(existing, dict) else existing[0]

            with get_db_cursor() as cursor:
                cursor.execute(
                    "INSERT INTO question_banks (name, source_pdf) VALUES (%s, %s)",
                    (name, source_pdf)
                )
                bank_id = cursor.lastrowid
                logger.info(f"Created question bank '{name}' with ID={bank_id}")
                return bank_id
        except Exception as err:
            logger.warning(f"Could not create question bank '{name}': {err}")
            return None

    @staticmethod
    def get_question_bank_by_id(bank_id: int) -> Optional[QuestionBankModel]:
        """Returns a question bank by its ID."""
        try:
            query = """
                SELECT qb.id, qb.name, qb.source_pdf, qb.created_at,
                       COUNT(q.id) AS question_count,
                       COALESCE(MAX(q.subject), 'General') AS subject,
                       COALESCE(MAX(q.class), 0) AS class_level
                FROM question_banks qb
                LEFT JOIN questions q ON q.bank_id = qb.id
                WHERE qb.id = %s
                GROUP BY qb.id, qb.name, qb.source_pdf, qb.created_at
            """
            with get_db_cursor() as cursor:
                cursor.execute(query, (bank_id,))
                row = cursor.fetchone()
                if row:
                    return QuestionBankModel(
                        id=row["id"],
                        name=row["name"],
                        source_pdf=row.get("source_pdf"),
                        question_count=int(row.get("question_count", 0)),
                        created_at=row.get("created_at"),
                        subject=row.get("subject", "General"),
                        class_level=int(row.get("class_level", 0)),
                    )
        except Exception as err:
            logger.warning(f"Could not fetch question bank {bank_id}: {err}")
        return None

    @staticmethod
    def update_question_bank(
        bank_id: int,
        new_name: str,
        new_subject: Optional[str] = None,
        new_class: Optional[int] = None
    ) -> bool:
        """
        Updates question bank name, and optionally updates subject and class level
        for all questions belonging to this bank.
        """
        try:
            with get_db_cursor() as cursor:
                cursor.execute(
                    "UPDATE question_banks SET name = %s WHERE id = %s",
                    (new_name.strip(), bank_id)
                )
                if new_subject and new_subject.strip():
                    cursor.execute(
                        "UPDATE questions SET subject = %s WHERE bank_id = %s",
                        (new_subject.strip(), bank_id)
                    )
                if new_class is not None:
                    cursor.execute(
                        "UPDATE questions SET class = %s WHERE bank_id = %s",
                        (new_class, bank_id)
                    )
            # In-memory sync
            for q in QuestionRepository._MEMORY_QUESTIONS:
                if getattr(q, "bank_id", None) == bank_id:
                    if new_subject and new_subject.strip():
                        q.subject = new_subject.strip()
                    if new_class is not None:
                        q.class_level = new_class

            logger.info(f"Successfully updated question bank ID={bank_id} to name='{new_name}'")
            return True
        except Exception as err:
            logger.error(f"Failed to update question bank ID={bank_id}: {err}")
            return False

    @staticmethod
    def delete_question_bank(bank_id: int) -> bool:
        """
        Deletes a question bank, all its questions, all associated attempt records,
        and removes the physical PDF file from the uploads directory if found.
        """
        try:
            source_pdf = None
            with get_db_cursor() as cursor:
                cursor.execute("SELECT source_pdf FROM question_banks WHERE id = %s", (bank_id,))
                row = cursor.fetchone()
                if row:
                    source_pdf = row.get("source_pdf") if isinstance(row, dict) else row[0]

            with get_db_cursor() as cursor:
                # 1. Delete attempts on questions belonging to this bank
                cursor.execute("""
                    DELETE a FROM attempts a
                    JOIN questions q ON a.question_id = q.id
                    WHERE q.bank_id = %s
                """, (bank_id,))

                # 2. Delete questions belonging to this bank
                cursor.execute("DELETE FROM questions WHERE bank_id = %s", (bank_id,))

                # 3. Delete the question bank row
                cursor.execute("DELETE FROM question_banks WHERE id = %s", (bank_id,))

            # 4. Remove physical PDF from uploads/ if found
            if source_pdf:
                try:
                    from pathlib import Path
                    from src.config import config
                    uploads_dir = Path(config.BASE_DIR) / "uploads"
                    if uploads_dir.exists():
                        for f in uploads_dir.iterdir():
                            if f.is_file() and (f.name == source_pdf or f.name.endswith(f"_{source_pdf}")):
                                try:
                                    f.unlink(missing_ok=True)
                                    logger.info(f"Deleted physical PDF file: {f.name}")
                                except Exception as fe:
                                    logger.warning(f"Could not remove PDF file {f.name}: {fe}")
                except Exception as file_err:
                    logger.warning(f"File cleanup warning for bank {bank_id}: {file_err}")

            # 5. Clean memory list
            QuestionRepository._MEMORY_QUESTIONS = [
                q for q in QuestionRepository._MEMORY_QUESTIONS if getattr(q, "bank_id", None) != bank_id
            ]

            logger.info(f"Successfully deleted question bank ID={bank_id} and all associated data.")
            return True
        except Exception as err:
            logger.error(f"Failed to delete question bank ID={bank_id}: {err}")
            return False

    @staticmethod
    def delete_question_banks(bank_ids: List[int]) -> int:
        """
        Batch deletes multiple question banks and their associated records.
        Returns the number of successfully deleted banks.
        """
        if not bank_ids:
            return 0
        deleted_count = 0
        for bid in bank_ids:
            try:
                if QuestionRepository.delete_question_bank(bid):
                    deleted_count += 1
            except Exception as e:
                logger.error(f"Error in batch deleting bank ID={bid}: {e}")
        return deleted_count

    @staticmethod
    def get_total_questions_in_bank(bank_id: Optional[int] = None) -> int:
        """Returns count of questions in a bank (or all if bank_id is None)."""
        try:
            with get_db_cursor() as cursor:
                if bank_id is not None:
                    cursor.execute("SELECT COUNT(*) AS cnt FROM questions WHERE bank_id = %s", (bank_id,))
                else:
                    cursor.execute("SELECT COUNT(*) AS cnt FROM questions")
                row = cursor.fetchone()
                if row:
                    return int(row["cnt"] if isinstance(row, dict) else row[0])
        except Exception:
            pass
        return len(QuestionRepository._MEMORY_QUESTIONS)

    # -----------------------------------------------------------------
    # Question CRUD
    # -----------------------------------------------------------------

    @staticmethod
    def create_question(question: QuestionModel) -> int:
        """
        Inserts a new question into the database using parameterized query.
        Prevents inserting duplicate question text.
        Returns the newly created or existing question ID.
        """
        try:
            if question.bank_id is not None:
                check_query = "SELECT id FROM questions WHERE question_text = %s AND bank_id = %s"
                check_params = (question.question_text, question.bank_id)
            else:
                check_query = "SELECT id FROM questions WHERE question_text = %s AND bank_id IS NULL"
                check_params = (question.question_text,)

            with get_db_cursor() as cursor:
                cursor.execute(check_query, check_params)
                existing_row = cursor.fetchone()
                if existing_row:
                    ex_id = existing_row.get("id") if isinstance(existing_row, dict) else existing_row[0]
                    question.id = ex_id
                    question.is_persisted = True
                    logger.info(f"Duplicate question detected in MySQL for bank {question.bank_id} (ID={ex_id}). Skipping.")
                    return ex_id

            query = """
                INSERT INTO questions (
                    class, subject, chapter, topic, question_text,
                    option_a, option_b, option_c, option_d,
                    correct_answer, explanation, difficulty,
                    source_pdf, answer_confidence, verification_status, bank_id
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s, %s
                )
            """
            params = (
                question.class_level,
                question.subject,
                question.chapter,
                question.topic,
                question.question_text,
                question.option_a,
                question.option_b,
                question.option_c,
                question.option_d,
                question.correct_answer,
                question.explanation,
                question.difficulty,
                question.source_pdf,
                question.answer_confidence,
                question.verification_status,
                question.bank_id,
            )

            with get_db_cursor() as cursor:
                cursor.execute(query, params)
                question_id = cursor.lastrowid
                question.id = question_id
                question.is_persisted = True
                QuestionRepository._sync_to_memory(question)
                logger.info(f"Inserted question ID={question_id} bank_id={question.bank_id}")
                return question_id
        except Exception as err:
            from src.utils.exceptions import DatabaseConnectionError
            if isinstance(err, DatabaseConnectionError):
                logger.warning(f"MySQL offline ({err}). Buffering question in memory repository.")
                question.is_persisted = False
                return QuestionRepository._create_in_memory(question)
            raise

    @staticmethod
    def create_questions_bulk(questions: List[QuestionModel]) -> List[int]:
        """
        Inserts multiple questions in a single database transaction.
        Checks for existing questions in the bank to avoid duplicates.
        Returns list of inserted/existing question IDs.
        """
        if not questions:
            return []

        created_ids = []
        try:
            with get_db_cursor() as cursor:
                bank_ids = list({q.bank_id for q in questions if q.bank_id is not None})
                existing_map = {}
                if bank_ids:
                    format_strings = ','.join(['%s'] * len(bank_ids))
                    cursor.execute(f"SELECT id, question_text, bank_id FROM questions WHERE bank_id IN ({format_strings})", tuple(bank_ids))
                    for row in cursor.fetchall():
                        r_id = row.get("id") if isinstance(row, dict) else row[0]
                        r_txt = row.get("question_text") if isinstance(row, dict) else row[1]
                        r_bid = row.get("bank_id") if isinstance(row, dict) else row[2]
                        existing_map[(r_txt, r_bid)] = r_id

                insert_sql = """
                    INSERT INTO questions (
                        class, subject, chapter, topic, question_text,
                        option_a, option_b, option_c, option_d,
                        correct_answer, explanation, difficulty,
                        source_pdf, answer_confidence, verification_status, bank_id
                    ) VALUES (
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s,
                        %s, %s, %s, %s
                    )
                """

                for q in questions:
                    key = (q.question_text, q.bank_id)
                    if key in existing_map:
                        ex_id = existing_map[key]
                        q.id = ex_id
                        q.is_persisted = True
                        created_ids.append(ex_id)
                        continue

                    params = (
                        q.class_level,
                        q.subject,
                        q.chapter,
                        q.topic,
                        q.question_text,
                        q.option_a,
                        q.option_b,
                        q.option_c,
                        q.option_d,
                        q.correct_answer,
                        q.explanation,
                        q.difficulty,
                        q.source_pdf,
                        q.answer_confidence,
                        q.verification_status,
                        q.bank_id,
                    )
                    cursor.execute(insert_sql, params)
                    q_id = cursor.lastrowid
                    q.id = q_id
                    q.is_persisted = True
                    existing_map[key] = q_id
                    created_ids.append(q_id)
                    QuestionRepository._sync_to_memory(q)

            logger.info(f"Bulk inserted/resolved {len(created_ids)} questions in single transaction.")
            return created_ids
        except Exception as err:
            logger.warning(f"Bulk insertion error: {err}. Falling back to single inserts.")
            fallback_ids = []
            for q in questions:
                try:
                    qid = QuestionRepository.create_question(q)
                    fallback_ids.append(qid)
                except Exception as ex:
                    logger.error(f"Single fallback insert failed: {ex}")
            return fallback_ids

    @staticmethod
    def get_question_by_id(question_id: int) -> Optional[QuestionModel]:
        """Retrieves a question by its primary key ID."""
        try:
            query = "SELECT * FROM questions WHERE id = %s"
            with get_db_cursor() as cursor:
                cursor.execute(query, (question_id,))
                row = cursor.fetchone()
                if row:
                    return QuestionRepository._row_to_model(row)
        except Exception:
            pass

        for q in QuestionRepository._MEMORY_QUESTIONS:
            if q.id == question_id:
                return q
        return None

    @staticmethod
    def get_all_questions(
        bank_id: Optional[int] = None,
        verification_status_filter: Optional[str] = None,
    ) -> List[QuestionModel]:
        """
        Retrieves all questions optionally filtered by bank_id.
        Used by the quiz engine when no class/subject filter is needed.
        """
        try:
            conditions = []
            params: list = []
            if bank_id is not None:
                conditions.append("bank_id = %s")
                params.append(bank_id)
            if verification_status_filter:
                conditions.append("verification_status = %s")
                params.append(verification_status_filter)

            where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""
            query = f"SELECT * FROM questions {where_clause} ORDER BY id ASC"

            with get_db_cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()
                if rows:
                    return [QuestionRepository._row_to_model(row) for row in rows]
        except Exception as err:
            logger.info(f"MySQL unavailable ({err}); serving questions from memory.")

        result = list(QuestionRepository._MEMORY_QUESTIONS)
        if bank_id is not None:
            result = [q for q in result if q.bank_id == bank_id]
        return result

    @staticmethod
    def get_questions_by_class_and_subject(class_level: int, subject: Optional[str] = None) -> List[QuestionModel]:
        """
        Retrieves questions filtered by class level and optional subject.
        Kept for backward compatibility with legacy NCERT data.
        """
        try:
            if subject:
                query = "SELECT * FROM questions WHERE class = %s AND subject = %s ORDER BY id ASC"
                params = (class_level, subject)
            else:
                query = "SELECT * FROM questions WHERE class = %s ORDER BY id ASC"
                params = (class_level,)

            with get_db_cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()
                if rows:
                    return [QuestionRepository._row_to_model(row) for row in rows]
        except Exception as err:
            logger.info(f"MySQL unavailable ({err}); serving questions from memory.")

        res = [q for q in QuestionRepository._MEMORY_QUESTIONS if q.class_level == class_level]
        if subject:
            res = [q for q in res if q.subject.lower() == subject.lower()]
        return res

    @staticmethod
    def get_questions_by_status(verification_status: str = "NEEDS_REVIEW") -> List[QuestionModel]:
        """Retrieves questions filtered by verification status."""
        try:
            query = "SELECT * FROM questions WHERE verification_status = %s ORDER BY id DESC"
            with get_db_cursor() as cursor:
                cursor.execute(query, (verification_status,))
                rows = cursor.fetchall()
                if rows:
                    return [QuestionRepository._row_to_model(row) for row in rows]
        except Exception as err:
            logger.info(f"MySQL unavailable ({err}); serving status questions from memory.")

        return [q for q in QuestionRepository._MEMORY_QUESTIONS if q.verification_status == verification_status]

    @staticmethod
    def update_question(question_id: int, update_data: Dict[str, Any]) -> bool:
        """Updates specific fields of an existing question using parameterized query."""
        if not update_data:
            return False

        if "class_level" in update_data:
            update_data["class"] = update_data.pop("class_level")

        allowed_fields = {
            "class", "subject", "chapter", "topic", "question_text",
            "option_a", "option_b", "option_c", "option_d", "correct_answer",
            "explanation", "difficulty", "source_pdf", "answer_confidence",
            "verification_status", "bank_id",
        }

        fields_to_update = {k: v for k, v in update_data.items() if k in allowed_fields}
        if not fields_to_update:
            logger.warning(f"No valid fields for updating question ID={question_id}")
            return False

        for q in QuestionRepository._MEMORY_QUESTIONS:
            if q.id == question_id:
                for k, v in fields_to_update.items():
                    attr_name = "class_level" if k == "class" else k
                    if hasattr(q, attr_name):
                        setattr(q, attr_name, v)

        try:
            set_clause = ", ".join([f"{col} = %s" for col in fields_to_update.keys()])
            query = f"UPDATE questions SET {set_clause} WHERE id = %s"
            params = list(fields_to_update.values()) + [question_id]

            with get_db_cursor() as cursor:
                cursor.execute(query, params)
                logger.info(f"Updated question ID={question_id}")
                return True
        except Exception:
            return True

    @staticmethod
    def delete_question(question_id: int) -> bool:
        """Deletes a question by primary key ID and associated attempt logs."""
        QuestionRepository._MEMORY_QUESTIONS = [q for q in QuestionRepository._MEMORY_QUESTIONS if q.id != question_id]
        try:
            with get_db_cursor() as cursor:
                cursor.execute("DELETE FROM attempts WHERE question_id = %s", (question_id,))
                cursor.execute("DELETE FROM questions WHERE id = %s", (question_id,))
                logger.info(f"Deleted question ID={question_id}")
                return True
        except Exception as err:
            logger.warning(f"Error deleting question ID={question_id}: {err}")
            return False


    @staticmethod
    def _row_to_model(row: Dict[str, Any]) -> QuestionModel:
        """Helper method to convert database row dictionary to QuestionModel instance."""
        return QuestionModel(
            id=row["id"],
            class_level=row.get("class", 0),
            subject=row.get("subject", "General"),
            chapter=row.get("chapter", "General"),
            topic=row.get("topic", "General"),
            question_text=row["question_text"],
            option_a=row["option_a"],
            option_b=row["option_b"],
            option_c=row["option_c"],
            option_d=row["option_d"],
            correct_answer=row["correct_answer"],
            explanation=row.get("explanation"),
            difficulty=row.get("difficulty", "Medium"),
            source_pdf=row.get("source_pdf"),
            answer_confidence=row.get("answer_confidence", 1.0),
            verification_status=row.get("verification_status", "UNVERIFIED"),
            bank_id=row.get("bank_id"),
            is_persisted=True,
            created_at=row.get("created_at"),
        )
