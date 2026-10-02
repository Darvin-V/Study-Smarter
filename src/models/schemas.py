"""
Study Smarter - Data Models & Schemas Module
Defines standard dataclasses representing core entities in the application.
Supports arbitrary question banks uploaded by the user.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class QuestionBankModel:
    """Represents a user-defined question bank (a named collection of questions)."""
    id: Optional[int] = None
    name: str = "General"
    source_pdf: Optional[str] = None
    question_count: int = 0
    created_at: Optional[datetime] = None
    subject: Optional[str] = "General"
    class_level: Optional[int] = 0


@dataclass
class UserModel:
    """Represents a student or user in the system."""
    id: Optional[int] = None
    name: str = "Student"
    email: Optional[str] = None
    class_level: int = 0  # 0 = unspecified; 10 or 12 kept for legacy NCERT data
    created_at: Optional[datetime] = None


@dataclass
class QuestionModel:
    """Represents a Multiple Choice Question (MCQ)."""
    id: Optional[int] = None
    class_level: int = 0  # 0 = unspecified (non-NCERT); legacy: 10 or 12
    subject: str = "General"
    chapter: str = "General"
    topic: str = "General"
    question_text: str = ""
    option_a: str = ""
    option_b: str = ""
    option_c: str = ""
    option_d: str = ""
    correct_answer: str = "A"  # 'A', 'B', 'C', 'D'
    explanation: Optional[str] = None
    difficulty: str = "Medium"  # 'Easy', 'Medium', 'Hard'
    source_pdf: Optional[str] = None
    answer_confidence: float = 1.0
    verification_status: str = "UNVERIFIED"  # 'UNVERIFIED', 'VERIFIED', 'AI_GENERATED'
    bank_id: Optional[int] = None   # FK to question_banks; None = Uncategorised
    bank_name: Optional[str] = None  # Denormalised for display convenience
    is_persisted: bool = False  # True only if successfully committed to MySQL
    created_at: Optional[datetime] = None

    @property
    def correct_option(self) -> str:
        """Backward compatibility alias for correct_answer."""
        return self.correct_answer

    def get_options_dict(self) -> Dict[str, str]:
        """Utility method to get options as a dictionary."""
        return {
            "A": self.option_a,
            "B": self.option_b,
            "C": self.option_c,
            "D": self.option_d,
        }


@dataclass
class QuizModel:
    """Represents an interactive Quiz set."""
    id: Optional[int] = None
    title: str = "Practice Quiz"
    class_level: int = 0
    subject: str = "General"
    bank_id: Optional[int] = None
    bank_name: Optional[str] = None
    total_questions: int = 0
    questions: List[QuestionModel] = field(default_factory=list)
    created_at: Optional[datetime] = None


@dataclass
class AttemptModel:
    """Represents a single question response in a quiz attempt."""
    id: Optional[int] = None
    user_id: Optional[int] = None
    quiz_id: Optional[int] = None
    question_id: int = 0
    selected_answer: str = "A"
    correct_answer: str = "A"
    is_correct: bool = False
    time_taken: int = 0  # Seconds
    attempted_at: Optional[datetime] = None


# Alias for backward compatibility
StudentAttemptModel = AttemptModel


@dataclass
class StudentAttemptSummary:
    """Represents overall summary of a completed quiz attempt by a student."""
    quiz_id: int
    user_name: str
    total_questions: int
    score: int
    percentage: float
    details: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class TopicPerformanceModel:
    """Represents topic-wise performance metrics for identifying weak areas."""
    topic_name: str
    subject_name: str
    total_attempted: int
    correct_count: int
    accuracy_percentage: float

    @property
    def needs_revision(self) -> bool:
        """Flag to highlight weak topics requiring revision (< 60% accuracy)."""
        return self.accuracy_percentage < 60.0
