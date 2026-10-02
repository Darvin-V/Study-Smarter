"""
Study Smarter - Attempt Repository Module
Provides database access methods for recording and querying student quiz attempt logs.
"""

from typing import List, Dict, Any, Optional
from src.database.connection import get_db_cursor
from src.models.schemas import AttemptModel
from src.logger import logger
from src.utils.exceptions import DatabaseQueryError


class AttemptRepository:
    """DAO for persisting student attempt responses into MySQL database with memory fallback."""

    _MEMORY_ATTEMPTS: List[Dict[str, Any]] = []

    @staticmethod
    def record_attempt(attempt: AttemptModel) -> int:
        """
        Inserts a single question attempt record into MySQL attempts table.
        Returns the generated attempt record ID.
        """
        # Mirror to memory
        from src.database.question_repository import QuestionRepository
        q = QuestionRepository.get_question_by_id(attempt.question_id)
        AttemptRepository._MEMORY_ATTEMPTS.append({
            "attempt_id": len(AttemptRepository._MEMORY_ATTEMPTS) + 1,
            "user_id": attempt.user_id,
            "quiz_id": attempt.quiz_id,
            "question_id": attempt.question_id,
            "selected_answer": attempt.selected_answer,
            "correct_answer": attempt.correct_answer,
            "is_correct": attempt.is_correct,
            "time_taken": attempt.time_taken,
            "attempted_at": None,
            "class": q.class_level if q else 12,
            "subject": q.subject if q else "NCERT",
            "chapter": q.chapter if q else "General",
            "topic": q.topic if q else "General",
            "question_text": q.question_text if q else "",
        })

        # Validate foreign keys exist to satisfy MySQL relational integrity constraints
        valid_quiz_id = attempt.quiz_id
        if valid_quiz_id is not None:
            try:
                with get_db_cursor() as check_cur:
                    check_cur.execute("SELECT id FROM quizzes WHERE id = %s", (valid_quiz_id,))
                    if not check_cur.fetchone():
                        valid_quiz_id = None
            except Exception:
                valid_quiz_id = None

        valid_user_id = attempt.user_id
        if valid_user_id is not None:
            try:
                with get_db_cursor() as check_cur:
                    check_cur.execute("SELECT id FROM users WHERE id = %s", (valid_user_id,))
                    if not check_cur.fetchone():
                        valid_user_id = None
            except Exception:
                valid_user_id = None

        query = """
            INSERT INTO attempts (
                user_id, quiz_id, question_id, selected_answer,
                correct_answer, is_correct, time_taken
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s
            )
        """
        params = (
            valid_user_id,
            valid_quiz_id,
            attempt.question_id,
            attempt.selected_answer,
            attempt.correct_answer,
            attempt.is_correct,
            attempt.time_taken,
        )

        try:
            with get_db_cursor() as cursor:
                cursor.execute(query, params)
                attempt_id = cursor.lastrowid
                logger.info(f"Recorded attempt ID={attempt_id} for Question ID={attempt.question_id}")
                return attempt_id
        except Exception as err:
            from src.config import config
            if config.is_production:
                from src.utils.exceptions import DatabaseConnectionError
                raise DatabaseConnectionError("Database connection unavailable. Please try again shortly.") from err
            from src.utils.exceptions import DatabaseConnectionError
            if isinstance(err, DatabaseConnectionError):
                logger.warning(f"MySQL unavailable ({err}). Attempt buffered only in memory; NOT saved to MySQL.")
                return 0
            raise

    @staticmethod
    def record_bulk_attempts(attempts: List[AttemptModel]) -> int:
        """
        Inserts multiple attempt records for a completed quiz attempt.
        Returns total count of successfully recorded attempt rows.
        """
        if not attempts:
            return 0

        # Mirror to memory
        from src.database.question_repository import QuestionRepository
        for att in attempts:
            q = QuestionRepository.get_question_by_id(att.question_id)
            AttemptRepository._MEMORY_ATTEMPTS.append({
                "attempt_id": len(AttemptRepository._MEMORY_ATTEMPTS) + 1,
                "user_id": att.user_id,
                "quiz_id": att.quiz_id,
                "question_id": att.question_id,
                "selected_answer": att.selected_answer,
                "correct_answer": att.correct_answer,
                "is_correct": att.is_correct,
                "time_taken": att.time_taken,
                "attempted_at": None,
                "class": q.class_level if q else 12,
                "subject": q.subject if q else "NCERT",
                "chapter": q.chapter if q else "General",
                "topic": q.topic if q else "General",
                "question_text": q.question_text if q else "",
            })

        query = """
            INSERT INTO attempts (
                user_id, quiz_id, question_id, selected_answer,
                correct_answer, is_correct, time_taken
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s
            )
        """
        # Validate referenced foreign keys exist to satisfy relational integrity
        existing_quiz_ids = set()
        existing_user_ids = set()
        try:
            with get_db_cursor() as check_cur:
                qids = list({att.quiz_id for att in attempts if att.quiz_id is not None})
                if qids:
                    fmt = ",".join(["%s"] * len(qids))
                    check_cur.execute(f"SELECT id FROM quizzes WHERE id IN ({fmt})", tuple(qids))
                    existing_quiz_ids = {r.get("id") if isinstance(r, dict) else r[0] for r in check_cur.fetchall()}

                uids = list({att.user_id for att in attempts if att.user_id is not None})
                if uids:
                    fmt = ",".join(["%s"] * len(uids))
                    check_cur.execute(f"SELECT id FROM users WHERE id IN ({fmt})", tuple(uids))
                    existing_user_ids = {r.get("id") if isinstance(r, dict) else r[0] for r in check_cur.fetchall()}
        except Exception:
            pass

        params_list = [
            (
                att.user_id if att.user_id in existing_user_ids else None,
                att.quiz_id if att.quiz_id in existing_quiz_ids else None,
                att.question_id,
                att.selected_answer,
                att.correct_answer,
                att.is_correct,
                att.time_taken,
            )
            for att in attempts
        ]

        try:
            with get_db_cursor() as cursor:
                cursor.executemany(query, params_list)
                recorded_count = cursor.rowcount
                logger.info(f"Recorded {recorded_count} question attempt logs into database.")
                return recorded_count
        except Exception as err:
            from src.config import config
            if config.is_production:
                from src.utils.exceptions import DatabaseConnectionError
                raise DatabaseConnectionError("Database connection unavailable. Please try again shortly.") from err
            from src.utils.exceptions import DatabaseConnectionError
            if isinstance(err, DatabaseConnectionError):
                logger.warning(f"MySQL unavailable ({err}). Buffered {len(attempts)} attempts in memory; NOT saved to MySQL.")
                return 0
            raise

    @staticmethod
    def get_user_attempts(user_id: int, bank_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieves all past attempts for a given user joined with question details.
        Optionally filter to a specific bank via bank_id.
        """
        try:
            if bank_id is not None:
                query = """
                SELECT a.id as attempt_id, a.user_id, a.quiz_id, a.question_id,
                       a.selected_answer, a.correct_answer, a.is_correct, a.time_taken, a.attempted_at,
                       q.class, q.subject, q.chapter, q.topic, q.question_text, q.bank_id
                FROM attempts a
                JOIN questions q ON a.question_id = q.id
                WHERE a.user_id = %s AND q.bank_id = %s
                ORDER BY a.attempted_at DESC
                """
                params = (user_id, bank_id)
            else:
                query = """
                SELECT a.id as attempt_id, a.user_id, a.quiz_id, a.question_id,
                       a.selected_answer, a.correct_answer, a.is_correct, a.time_taken, a.attempted_at,
                       q.class, q.subject, q.chapter, q.topic, q.question_text, q.bank_id
                FROM attempts a
                JOIN questions q ON a.question_id = q.id
                WHERE a.user_id = %s
                ORDER BY a.attempted_at DESC
                """
                params = (user_id,)
            with get_db_cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()
                if rows:
                    return rows
                return []
        except Exception as err:
            from src.config import config
            if config.is_production:
                from src.utils.exceptions import DatabaseConnectionError
                raise DatabaseConnectionError("Database connection unavailable. Please try again shortly.") from err
            logger.info(f"MySQL unavailable ({err}); serving attempts from memory buffer.")

        from src.config import config
        if config.is_production:
            return []

        mem = [a for a in AttemptRepository._MEMORY_ATTEMPTS if a.get("user_id") == user_id]
        if bank_id is not None:
            mem = [a for a in mem if a.get("bank_id") == bank_id]
        return mem

    @staticmethod
    def get_unique_questions_attempted(user_id: int, bank_id: Optional[int] = None) -> int:
        """
        Returns count of DISTINCT questions attempted by a user.
        This is the correct numerator for the completion/coverage formula:
            unique questions attempted / total questions in bank × 100
        Optionally scoped to a specific bank_id.
        """
        try:
            if bank_id is not None:
                query = """
                SELECT COUNT(DISTINCT a.question_id) AS unique_count
                FROM attempts a
                JOIN questions q ON a.question_id = q.id
                WHERE a.user_id = %s AND q.bank_id = %s
                """
                params = (user_id, bank_id)
            else:
                query = """
                SELECT COUNT(DISTINCT question_id) AS unique_count
                FROM attempts
                WHERE user_id = %s
                """
                params = (user_id,)
            with get_db_cursor() as cursor:
                cursor.execute(query, params)
                row = cursor.fetchone()
                if row:
                    return int(row["unique_count"] if isinstance(row, dict) else row[0])
        except Exception as err:
            logger.info(f"MySQL unavailable ({err}); computing unique count from memory.")

        # Memory fallback
        mem = [a for a in AttemptRepository._MEMORY_ATTEMPTS if a.get("user_id") == user_id]
        if bank_id is not None:
            mem = [a for a in mem if a.get("bank_id") == bank_id]
        return len({a.get("question_id") for a in mem})

    @staticmethod
    def get_quiz_history(user_id: int, bank_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Returns per-quiz summary rows for Study History display.
        Each row aggregates: quiz_id, date, questions attempted, correct, incorrect, accuracy.
        Optionally scoped to a specific bank_id.
        """
        try:
            if bank_id is not None:
                query = """
                SELECT
                    a.quiz_id,
                    MIN(a.attempted_at) AS quiz_date,
                    COUNT(a.id) AS total_attempted,
                    SUM(a.is_correct) AS correct_count,
                    COUNT(a.id) - SUM(a.is_correct) AS incorrect_count,
                    ROUND(SUM(a.is_correct) / COUNT(a.id) * 100, 1) AS accuracy,
                    GROUP_CONCAT(DISTINCT qb.name ORDER BY qb.name SEPARATOR ', ') AS bank_names
                FROM attempts a
                JOIN questions q ON a.question_id = q.id
                LEFT JOIN question_banks qb ON q.bank_id = qb.id
                WHERE a.user_id = %s AND q.bank_id = %s
                GROUP BY a.quiz_id
                ORDER BY quiz_date DESC
                LIMIT 50
                """
                params = (user_id, bank_id)
            else:
                query = """
                SELECT
                    a.quiz_id,
                    MIN(a.attempted_at) AS quiz_date,
                    COUNT(a.id) AS total_attempted,
                    SUM(a.is_correct) AS correct_count,
                    COUNT(a.id) - SUM(a.is_correct) AS incorrect_count,
                    ROUND(SUM(a.is_correct) / COUNT(a.id) * 100, 1) AS accuracy,
                    GROUP_CONCAT(DISTINCT qb.name ORDER BY qb.name SEPARATOR ', ') AS bank_names
                FROM attempts a
                JOIN questions q ON a.question_id = q.id
                LEFT JOIN question_banks qb ON q.bank_id = qb.id
                WHERE a.user_id = %s
                GROUP BY a.quiz_id
                ORDER BY quiz_date DESC
                LIMIT 50
                """
                params = (user_id,)
            with get_db_cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()
                return rows or []
        except Exception as err:
            logger.info(f"MySQL unavailable ({err}); quiz history unavailable from memory.")
            return []

    @staticmethod
    def delete_quiz_session(quiz_id: int) -> bool:
        """Deletes all attempt records and the quiz session record for a specific quiz."""
        return AttemptRepository.delete_quiz_sessions([quiz_id])

    @staticmethod
    def delete_quiz_sessions(quiz_ids: List[int]) -> bool:
        """Batch deletes all attempt records and quiz records for multiple quiz IDs."""
        if not quiz_ids:
            return True
        try:
            placeholders = ", ".join(["%s"] * len(quiz_ids))
            with get_db_cursor() as cursor:
                cursor.execute(f"DELETE FROM attempts WHERE quiz_id IN ({placeholders})", tuple(quiz_ids))
                cursor.execute(f"DELETE FROM quizzes WHERE id IN ({placeholders})", tuple(quiz_ids))
            del_set = set(quiz_ids)
            AttemptRepository._MEMORY_ATTEMPTS = [
                a for a in AttemptRepository._MEMORY_ATTEMPTS if a.get("quiz_id") not in del_set
            ]
            logger.info(f"Batch deleted {len(quiz_ids)} quiz sessions: {quiz_ids}")
            return True
        except Exception as err:
            logger.error(f"Failed to batch delete quiz sessions {quiz_ids}: {err}")
            return False

    @staticmethod
    def clear_history(user_id: int = 1, bank_id: Optional[int] = None) -> bool:
        """
        Clears quiz attempt history.
        If bank_id is provided, deletes attempts on questions belonging to that bank.
        If bank_id is None, deletes all attempts for the specified user and orphaned quizzes.
        """
        try:
            with get_db_cursor() as cursor:
                if bank_id is not None:
                    cursor.execute("""
                        DELETE a FROM attempts a
                        JOIN questions q ON a.question_id = q.id
                        WHERE a.user_id = %s AND q.bank_id = %s
                    """, (user_id, bank_id))
                else:
                    cursor.execute("DELETE FROM attempts WHERE user_id = %s", (user_id,))
                    cursor.execute("""
                        DELETE FROM quizzes
                        WHERE id NOT IN (SELECT DISTINCT quiz_id FROM attempts WHERE quiz_id IS NOT NULL)
                    """)

            if bank_id is not None:
                AttemptRepository._MEMORY_ATTEMPTS = [
                    a for a in AttemptRepository._MEMORY_ATTEMPTS
                    if not (a.get("user_id") == user_id and a.get("bank_id") == bank_id)
                ]
            else:
                AttemptRepository._MEMORY_ATTEMPTS = [
                    a for a in AttemptRepository._MEMORY_ATTEMPTS if a.get("user_id") != user_id
                ]
            logger.info(f"Cleared attempt history for user_id={user_id}, bank_id={bank_id}")
            return True
        except Exception as err:
            logger.error(f"Failed to clear history: {err}")
            return False

    @staticmethod
    def reset_bank_attempts(user_id: int = 1, bank_id: int = 0) -> bool:
        """Resets all attempts on questions in a specific bank back to 0 (unattempted)."""
        return AttemptRepository.clear_history(user_id=user_id, bank_id=bank_id)

