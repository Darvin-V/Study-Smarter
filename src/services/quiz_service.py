"""
Study Smarter - Quiz Engine Service Module
Handles server-side quiz question retrieval, single-question grading verification,
time tracking, score calculations, and MySQL attempt recording.
"""

import time
from typing import List, Optional, Dict, Any
from src.logger import logger
from src.database.connection import MYSQL_AVAILABLE
from src.database.question_repository import QuestionRepository
from src.database.attempt_repository import AttemptRepository
from src.models.schemas import QuestionModel, QuizModel, AttemptModel
from src.utils.exceptions import QuizNotFoundError, DatabaseQueryError


class QuizService:
    """Business logic handler for interactive quizzes and backend answer evaluation."""

    @staticmethod
    def fetch_quiz_questions_by_bank(
        bank_id: Optional[int] = None,
        bank_name: str = "All Banks",
        limit: int = 5,
        user_id: int = 1,
    ) -> QuizModel:
        """
        Retrieves questions from a specific question bank (or all banks if bank_id is None).
        Skips questions with NEEDS_REVIEW status.
        Prioritizes UNATTEMPTED questions first so "Continue Practicing" always
        surfaces questions the student hasn't seen yet before repeating old ones.
        """
        import random
        db_questions: List[QuestionModel] = []

        if MYSQL_AVAILABLE:
            try:
                all_qs = QuestionRepository.get_all_questions(bank_id=bank_id)
                # Filter questions: exclude NEEDS_REVIEW and ensure clean educational explanation
                bad_kw = ["low confidence", "unable to determine", "held for review", "flagged for review", "processing error", "unverified"]
                filtered = [
                    q for q in all_qs
                    if getattr(q, "verification_status", "VERIFIED") != "NEEDS_REVIEW"
                    and q.explanation
                    and len(q.explanation.strip()) >= 15
                    and not any(kw in q.explanation.lower() for kw in bad_kw)
                ]

                # Fetch IDs already attempted by this user in this bank
                already_attempted_ids: set = set()
                try:
                    from src.database.attempt_repository import AttemptRepository
                    logs = AttemptRepository.get_user_attempts(user_id=user_id, bank_id=bank_id)
                    already_attempted_ids = {row.get("question_id") for row in logs if row.get("question_id")}
                except Exception:
                    pass

                # Split into unattempted and already-attempted pools
                unattempted = [q for q in filtered if q.id not in already_attempted_ids]
                attempted_pool = [q for q in filtered if q.id in already_attempted_ids]

                # Shuffle both pools independently
                random.shuffle(unattempted)
                random.shuffle(attempted_pool)

                # Fill from unattempted first, then pad with attempted if needed
                combined = (unattempted + attempted_pool)
                if limit and limit > 0:
                    combined = combined[:limit]
                db_questions = combined

            except Exception as err:
                logger.warning(f"Failed to fetch questions from MySQL: {err}")
                db_questions = []

        title = f"{bank_name} Practice Quiz" if bank_name and bank_name != "All Banks" else "Practice Quiz"

        return QuizModel(
            id=int(time.time()),
            title=title,
            class_level=0,
            subject="General",
            bank_id=bank_id,
            bank_name=bank_name,
            total_questions=len(db_questions),
            questions=db_questions,
        )

    @staticmethod
    def fetch_quiz_questions(
        class_level: int = 12,
        subject: str = "Physics",
        chapter: Optional[str] = None,
        topic: Optional[str] = None,
        limit: int = 5,
    ) -> QuizModel:
        """
        Retrieves matching questions from MySQL filtered by class/subject (legacy NCERT path).
        Returns empty QuizModel if no questions exist in the database for the selection.
        """
        db_questions: List[QuestionModel] = []

        if MYSQL_AVAILABLE:
            try:
                raw_questions = QuestionRepository.get_questions_by_class_and_subject(
                    class_level=class_level, subject=subject
                )
                filtered = []
                for q in raw_questions:
                    if getattr(q, "verification_status", "VERIFIED") == "NEEDS_REVIEW":
                        continue
                    match_ch = True
                    match_tp = True
                    if chapter and chapter != "All Chapters":
                        match_ch = (q.chapter.lower() == chapter.lower())
                    if topic and topic != "All Topics":
                        match_tp = (q.topic.lower() == topic.lower())
                    if match_ch and match_tp:
                        filtered.append(q)
                db_questions = filtered[:limit]
            except Exception as err:
                logger.warning(f"Failed to fetch questions from MySQL: {err}")
                db_questions = []

        quiz_title = f"Practice Quiz"
        if class_level and class_level > 0:
            quiz_title = f"Class {class_level} {subject} Quiz"
        if chapter and chapter != "All Chapters":
            quiz_title += f" - {chapter}"

        quiz = QuizModel(
            id=int(time.time()),
            title=quiz_title,
            class_level=class_level,
            subject=subject,
            total_questions=len(db_questions),
            questions=db_questions,
        )
        return quiz

    @staticmethod
    def verify_question_answer(question: QuestionModel, selected_option: str) -> Dict[str, Any]:
        """
        Server-side single question answer evaluation.
        Checks correctness on the backend and returns status report.
        """
        if not selected_option or not selected_option.strip():
            return {
                "valid": False,
                "message": "Please select an answer option before submitting!",
            }

        selected_clean = selected_option.strip().upper()
        correct_clean = question.correct_answer.strip().upper()
        is_correct = (selected_clean == correct_clean)

        explanation = question.explanation or "No detailed explanation available."

        return {
            "valid": True,
            "question_id": question.id,
            "selected_option": selected_clean,
            "correct_answer": correct_clean,
            "is_correct": is_correct,
            "explanation": explanation,
            "status_text": "Correct!" if is_correct else "Incorrect",
        }

    @staticmethod
    def submit_quiz_attempt(
        quiz: QuizModel,
        user_id: int,
        attempt_details: List[Dict[str, Any]],
        total_time_seconds: int,
        save_to_db: bool = True,
        quiz_record_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Calculates final score, percentage, correct/incorrect count,
        and optionally persists attempt records to MySQL database.
        """
        total_questions = len(quiz.questions)
        correct_count = sum(1 for item in attempt_details if item.get("is_correct", False))
        incorrect_count = total_questions - correct_count

        percentage = round((correct_count / total_questions * 100), 2) if total_questions > 0 else 0.0
        per_question_time = max(1, total_time_seconds // total_questions) if total_questions > 0 else 0

        db_recorded = True

        if save_to_db:
            # Record quiz session into MySQL quizzes table to satisfy foreign key constraint if needed
            if quiz_record_id is None:
                try:
                    from src.database.connection import get_db_cursor
                    with get_db_cursor() as cursor:
                        cursor.execute(
                            "INSERT INTO quizzes (title, class_level, subject, total_questions) VALUES (%s, %s, %s, %s)",
                            (quiz.title, quiz.class_level, quiz.subject, total_questions)
                        )
                        quiz_record_id = cursor.lastrowid
                except Exception as err:
                    logger.info(f"Could not persist quiz session to MySQL quizzes table: {err}")
                    quiz_record_id = None

            # Create AttemptModel objects for database persistence
            attempt_models = []
            for item in attempt_details:
                q_id = item.get("question_id", 0)
                sel = item.get("selected_option", "A")
                corr = item.get("correct_answer", "A")
                is_corr = item.get("is_correct", False)
                q_time = item.get("time_taken", per_question_time)

                att_model = AttemptModel(
                    user_id=user_id,
                    quiz_id=quiz_record_id,
                    question_id=q_id,
                    selected_answer=sel,
                    correct_answer=corr,
                    is_correct=is_corr,
                    time_taken=q_time,
                )
                attempt_models.append(att_model)

            # Attempt to record into MySQL
            if MYSQL_AVAILABLE and attempt_models:
                try:
                    rec_count = AttemptRepository.record_bulk_attempts(attempt_models)
                    db_recorded = (rec_count > 0)
                    try:
                        from src.services.analytics_service import _fetch_user_attempt_logs
                        _fetch_user_attempt_logs.clear()
                    except Exception:
                        pass
                except Exception as err:
                    logger.warning(f"Could not persist attempt log to MySQL: {err}")
                    db_recorded = False

        return {
            "total_questions": total_questions,
            "correct_count": correct_count,
            "incorrect_count": incorrect_count,
            "score": correct_count,
            "percentage": percentage,
            "total_time_seconds": total_time_seconds,
            "db_recorded": db_recorded,
            "details": attempt_details,
        }
