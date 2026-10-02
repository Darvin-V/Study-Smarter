"""
Study Smarter - Performance Analytics & Recommendation Service Module
Analyzes real student attempt logs from MySQL to calculate overall accuracy,
topic/chapter/subject/difficulty breakdowns, and generates targeted recommendations.
"""

from typing import List, Dict, Any, Optional
import streamlit as st
from src.config import config
from src.logger import logger
from src.database.connection import MYSQL_AVAILABLE
from src.database.attempt_repository import AttemptRepository
from src.models.schemas import TopicPerformanceModel


@st.cache_data(ttl=60, show_spinner=False)
def _fetch_user_attempt_logs(user_id: int = 1, bank_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """Retrieves raw attempt logs from MySQL with short-lived TTL caching for fast page navigation."""
    if MYSQL_AVAILABLE:
        try:
            logs = AttemptRepository.get_user_attempts(user_id, bank_id=bank_id)
            if logs:
                return logs
        except Exception as err:
            logger.warning(f"Could not fetch attempt logs from MySQL: {err}")
    return []


class AnalyticsService:
    """Service for student performance analysis, topic classification, and AI-like recommendation generation."""

    @classmethod
    def _get_raw_attempt_logs(cls, user_id: int = 1, bank_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieves raw attempt logs strictly from MySQL database using cached query executor.
        Returns empty list if database is empty or no attempt logs exist.
        """
        return _fetch_user_attempt_logs(user_id, bank_id=bank_id)

    @classmethod
    def get_overall_summary(cls, user_id: int = 1, bank_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Calculates high-level metrics:
        - overall_accuracy (based on all attempts, scoped to bank if provided)
        - total_questions_attempted: count of DISTINCT questions attempted
        - total_quizzes_completed
        - strongest_topic
        - weakest_topic
        """
        logs = cls._get_raw_attempt_logs(user_id, bank_id=bank_id)
        if not logs:
            return {
                "overall_accuracy": 0.0,
                "total_questions_attempted": 0,
                "total_quizzes_completed": 0,
                "strongest_topic": "N/A",
                "weakest_topic": "N/A",
            }

        total_attempt_rows = len(logs)
        correct_count = sum(1 for item in logs if item.get("is_correct"))
        overall_accuracy = round((correct_count / total_attempt_rows * 100), 2)

        # CORRECT coverage numerator: unique distinct questions attempted
        unique_attempted = len({item.get("question_id") for item in logs if item.get("question_id")})

        distinct_quizzes = len({item.get("quiz_id") for item in logs if item.get("quiz_id") is not None})

        # Calculate topic-wise metrics to find strongest & weakest topics
        topic_breakdown = cls.get_topic_accuracy_breakdown(user_id, bank_id=bank_id, logs=logs)

        strongest_topic = "N/A"
        weakest_topic = "N/A"

        if topic_breakdown:
            # Sort by accuracy
            sorted_topics = sorted(topic_breakdown, key=lambda x: x["accuracy_percentage"], reverse=True)
            strongest_topic = sorted_topics[0]["topic_name"]
            weakest_topic = sorted_topics[-1]["topic_name"] if len(sorted_topics) > 1 else "N/A"

        return {
            "overall_accuracy": overall_accuracy,
            "total_questions_attempted": unique_attempted,  # UNIQUE questions, not raw attempt count
            "total_attempt_rows": total_attempt_rows,        # raw count kept for internal use
            "total_quizzes_completed": distinct_quizzes,
            "strongest_topic": strongest_topic,
            "weakest_topic": weakest_topic,
        }

    @classmethod
    def get_topic_accuracy_breakdown(
        cls,
        user_id: int = 1,
        bank_id: Optional[int] = None,
        logs: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Calculates topic-wise accuracy and categorizes each into Strong, Average, or Weak
        using configurable thresholds from Config (WEAK_TOPIC_THRESHOLD, STRONG_TOPIC_THRESHOLD).
        """
        if logs is None:
            logs = cls._get_raw_attempt_logs(user_id, bank_id=bank_id)
        stats: Dict[str, Dict[str, Any]] = {}

        for item in logs:
            topic = item.get("topic") or item.get("topic_name") or "General"
            subject = item.get("subject") or item.get("subject_name") or "NCERT"
            is_correct = bool(item.get("is_correct"))

            if topic not in stats:
                stats[topic] = {"subject": subject, "total": 0, "correct": 0}

            stats[topic]["total"] += 1
            if is_correct:
                stats[topic]["correct"] += 1

        results = []
        for topic, d in stats.items():
            total = d["total"]
            correct = d["correct"]
            acc = round((correct / total * 100), 2) if total > 0 else 0.0

            # Classification using Config thresholds
            if acc >= config.STRONG_TOPIC_THRESHOLD:
                status = "Strong"
            elif acc >= config.WEAK_TOPIC_THRESHOLD:
                status = "Average"
            else:
                status = "Weak"

            results.append({
                "topic_name": topic,
                "subject_name": d["subject"],
                "total_attempted": total,
                "correct_count": correct,
                "accuracy_percentage": acc,
                "status": status,
                "needs_revision": (acc < config.WEAK_TOPIC_THRESHOLD),
            })

        return sorted(results, key=lambda x: x["accuracy_percentage"], reverse=True)

    @classmethod
    def classify_topics_by_performance(cls, topic_list: List[Dict[str, Any]]):
        """Classifies a list of topic dicts into (strong_topics, avg_topics, weak_topics)."""
        strong, avg, weak = [], [], []
        for item in topic_list:
            acc = item.get("accuracy", item.get("accuracy_percentage", 0.0))
            if acc >= config.STRONG_TOPIC_THRESHOLD:
                strong.append(item)
            elif acc >= config.WEAK_TOPIC_THRESHOLD:
                avg.append(item)
            else:
                weak.append(item)
        return strong, avg, weak

    @classmethod
    def get_chapter_accuracy_breakdown(cls, user_id: int = 1, bank_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Calculates accuracy breakdown grouped by chapter."""
        logs = cls._get_raw_attempt_logs(user_id, bank_id=bank_id)
        stats: Dict[str, Dict[str, Any]] = {}

        for item in logs:
            chapter = item.get("chapter") or item.get("chapter_name") or "General Chapter"
            subject = item.get("subject") or item.get("subject_name") or "NCERT"
            is_correct = bool(item.get("is_correct"))

            if chapter not in stats:
                stats[chapter] = {"subject": subject, "total": 0, "correct": 0}

            stats[chapter]["total"] += 1
            if is_correct:
                stats[chapter]["correct"] += 1

        results = []
        for chapter, d in stats.items():
            total = d["total"]
            correct = d["correct"]
            acc = round((correct / total * 100), 2) if total > 0 else 0.0

            results.append({
                "chapter_name": chapter,
                "subject_name": d["subject"],
                "total_attempted": total,
                "correct_count": correct,
                "accuracy_percentage": acc,
            })

        return sorted(results, key=lambda x: x["accuracy_percentage"], reverse=True)

    @classmethod
    def get_subject_accuracy_breakdown(cls, user_id: int = 1, bank_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Calculates accuracy breakdown grouped by subject."""
        logs = cls._get_raw_attempt_logs(user_id, bank_id=bank_id)
        stats: Dict[str, Dict[str, int]] = {}

        for item in logs:
            subject = item.get("subject") or item.get("subject_name") or "NCERT"
            is_correct = bool(item.get("is_correct"))

            if subject not in stats:
                stats[subject] = {"total": 0, "correct": 0}

            stats[subject]["total"] += 1
            if is_correct:
                stats[subject]["correct"] += 1

        results = []
        for subject, d in stats.items():
            total = d["total"]
            correct = d["correct"]
            acc = round((correct / total * 100), 2) if total > 0 else 0.0

            results.append({
                "subject_name": subject,
                "total_attempted": total,
                "correct_count": correct,
                "accuracy_percentage": acc,
            })

        return sorted(results, key=lambda x: x["accuracy_percentage"], reverse=True)

    @classmethod
    def get_difficulty_accuracy_breakdown(cls, user_id: int = 1, bank_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Calculates accuracy breakdown grouped by difficulty level (Easy, Medium, Hard)."""
        logs = cls._get_raw_attempt_logs(user_id, bank_id=bank_id)
        stats: Dict[str, Dict[str, int]] = {}

        for item in logs:
            difficulty = item.get("difficulty") or item.get("difficulty_level") or "Medium"
            is_correct = bool(item.get("is_correct"))

            if difficulty not in stats:
                stats[difficulty] = {"total": 0, "correct": 0}

            stats[difficulty]["total"] += 1
            if is_correct:
                stats[difficulty]["correct"] += 1

        results = []
        for difficulty, d in stats.items():
            total = d["total"]
            correct = d["correct"]
            acc = round((correct / total * 100), 2) if total > 0 else 0.0

            results.append({
                "difficulty_level": difficulty,
                "total_attempted": total,
                "correct_count": correct,
                "accuracy_percentage": acc,
            })

        return results

    @classmethod
    def generate_recommendations(cls, user_id: int = 1, bank_id: Optional[int] = None) -> List[str]:
        """
        Recommendation Engine:
        Analyzes real database attempt data to generate actionable, targeted recommendations.
        Identifies weak topics (< WEAK_TOPIC_THRESHOLD) and topics significantly below overall accuracy.
        """
        overall = cls.get_overall_summary(user_id, bank_id=bank_id)
        overall_acc = overall["overall_accuracy"]
        topic_breakdown = cls.get_topic_accuracy_breakdown(user_id, bank_id=bank_id)

        recommendations: List[str] = []

        if not topic_breakdown:
            return ["Attempt practice quizzes to generate personalized revision recommendations."]

        # 1. Identify weak topics (< WEAK_TOPIC_THRESHOLD)
        weak_topics = [t for t in topic_breakdown if t["needs_revision"]]
        for t in weak_topics:
            topic_name = t["topic_name"]
            acc = t["accuracy_percentage"]
            total_att = t.get("total_attempted", 0)
            if total_att < 2:
                recommendations.append(
                    f"Practice more questions on '{topic_name}' (only {total_att} attempt recorded) to establish your baseline accuracy."
                )
            else:
                recommendations.append(
                    f"Revise '{topic_name}' (Accuracy: {acc}% across {total_att} attempts) and attempt a targeted practice quiz."
                )

        # 2. Identify topics significantly below overall average (diff > 15%)
        for t in topic_breakdown:
            if not t["needs_revision"]:  # Not already added
                acc = t["accuracy_percentage"]
                if (overall_acc - acc) >= 15.0:
                    topic_name = t["topic_name"]
                    recommendations.append(
                        f"Your accuracy in '{topic_name}' ({acc}%) is significantly below your overall average ({overall_acc}%). Review this chapter."
                    )

        # Fallback praise if all topics are strong
        if not recommendations:
            recommendations.append(
                "Great job! Your topic accuracy is consistently strong (>= 60%). Keep practicing regularly to maintain high performance."
            )

        return recommendations

    @staticmethod
    def analyze_attempt_details(attempt_details: List[Dict[str, Any]]) -> List[TopicPerformanceModel]:
        """Processes list of attempted question details and aggregates accuracy per topic."""
        return analyze_attempt_details(attempt_details)

    @staticmethod
    def get_weak_topics(topic_performances: List[TopicPerformanceModel]) -> List[TopicPerformanceModel]:
        """Filters topics requiring revision."""
        return get_weak_topics(topic_performances)


# Backward compatibility methods
def analyze_attempt_details(attempt_details: List[Dict[str, Any]]) -> List[TopicPerformanceModel]:
    """Processes list of attempted question details and aggregates accuracy per topic."""
    topic_stats: Dict[str, Dict[str, int]] = {}

    for item in attempt_details:
        topic = item.get("topic_name", "General Topic")
        is_correct = item.get("is_correct", False)

        if topic not in topic_stats:
            topic_stats[topic] = {"total": 0, "correct": 0}

        topic_stats[topic]["total"] += 1
        if is_correct:
            topic_stats[topic]["correct"] += 1

    results = []
    for topic, stats in topic_stats.items():
        total = stats["total"]
        correct = stats["correct"]
        acc = round((correct / total * 100), 2) if total > 0 else 0.0

        perf = TopicPerformanceModel(
            topic_name=topic,
            subject_name="Practice Questions",
            total_attempted=total,
            correct_count=correct,
            accuracy_percentage=acc,
        )
        results.append(perf)

    return results


def get_weak_topics(topic_performances: List[TopicPerformanceModel]) -> List[TopicPerformanceModel]:
    """Filters topics requiring revision."""
    return [tp for tp in topic_performances if tp.needs_revision]
