"""
Study Smarter - NCERT Syllabus Management Service
Provides predefined NCERT syllabus configuration for Class 10 and Class 12.
Enforces strict hierarchy (Class -> Subject -> Chapter -> Topic) and validation
to prevent AI or PDF processors from inventing arbitrary chapter names.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import streamlit as st
from src.config import config
from src.logger import logger


@st.cache_data(show_spinner=False)
def _read_syllabus_file() -> Dict[str, Any]:
    """Reads and parses syllabus JSON dataset from disk with Streamlit caching."""
    json_path = config.BASE_DIR / "src" / "data" / "ncert_syllabus.json"
    if not json_path.exists():
        logger.error(f"Syllabus dataset missing at {json_path}")
        return {}

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info("Loaded NCERT syllabus configuration cleanly.")
        return data
    except Exception as err:
        logger.error(f"Failed to parse NCERT syllabus JSON: {err}")
        return {}


class SyllabusService:
    """NCERT Syllabus Manager for Class 10 & Class 12."""

    _SYLLABUS_DATA: Optional[Dict[str, Any]] = None
    SUPPORTED_CLASSES: List[int] = [10, 12]

    @classmethod
    def _load_syllabus_data(cls) -> Dict[str, Any]:
        """Loads and caches syllabus JSON dataset."""
        if cls._SYLLABUS_DATA is None:
            cls._SYLLABUS_DATA = _read_syllabus_file()
        return cls._SYLLABUS_DATA

    @classmethod
    def _normalize_class_level(cls, class_input: Any) -> str:
        """
        Normalizes class input (e.g. 10, '10', 'Class 10', 12, 'Class 12') to string key ('10' or '12').
        """
        raw_str = str(class_input).strip().lower()
        if "10" in raw_str:
            return "10"
        elif "12" in raw_str:
            return "12"
        return raw_str

    @classmethod
    def get_classes(cls) -> List[int]:
        """Returns list of supported NCERT class levels [10, 12]."""
        return cls.SUPPORTED_CLASSES.copy()

    @classmethod
    def get_subjects(cls, class_input: Any) -> List[str]:
        """
        Returns list of official subjects for specified class (10 or 12).
        Returns empty list for unsupported classes.
        """
        data = cls._load_syllabus_data()
        class_key = cls._normalize_class_level(class_input)
        if class_key in data:
            return list(data[class_key].keys())
        return []

    @classmethod
    def get_chapters(cls, class_input: Any, subject: str) -> List[str]:
        """
        Returns list of official chapters for given class level and subject.
        """
        data = cls._load_syllabus_data()
        class_key = cls._normalize_class_level(class_input)
        if class_key not in data:
            return []

        subjects_dict = data[class_key]
        # Case-insensitive subject lookup
        for subj_name, chapters_dict in subjects_dict.items():
            if subj_name.lower() == subject.strip().lower():
                return list(chapters_dict.keys())

        return []

    @classmethod
    def get_topics(cls, class_input: Any, subject: str, chapter: str) -> List[str]:
        """
        Returns list of official topics under a specified chapter.
        """
        data = cls._load_syllabus_data()
        class_key = cls._normalize_class_level(class_input)
        if class_key not in data:
            return []

        subjects_dict = data[class_key]
        for subj_name, chapters_dict in subjects_dict.items():
            if subj_name.lower() == subject.strip().lower():
                for ch_name, topics_list in chapters_dict.items():
                    if ch_name.lower() == chapter.strip().lower():
                        return list(topics_list)

        return []

    @classmethod
    def validate_chapter(cls, class_input: Any, subject: str, chapter: str) -> bool:
        """
        Strictly validates if a chapter exists in official NCERT syllabus.
        """
        official_chapters = cls.get_chapters(class_input, subject)
        target_ch = chapter.strip().lower()
        return any(ch.lower() == target_ch for ch in official_chapters)

    @classmethod
    def validate_topic(cls, class_input: Any, subject: str, chapter: str, topic: str) -> bool:
        """
        Strictly validates if a topic exists under specified chapter.
        """
        official_topics = cls.get_topics(class_input, subject, chapter)
        target_tp = topic.strip().lower()
        return any(tp.lower() == target_tp for tp in official_topics)

    @classmethod
    def match_or_fallback_chapter(cls, class_input: Any, subject: str, raw_chapter: str) -> str:
        """
        Normalizes and matches raw chapter text against official NCERT syllabus.
        Returns official chapter title if matched, otherwise returns 'General'.
        """
        official_chapters = cls.get_chapters(class_input, subject)
        target = raw_chapter.strip().lower()
        for ch in official_chapters:
            if ch.lower() == target or target in ch.lower() or ch.lower() in target:
                return ch
        return "General"

    @classmethod
    def validate_question_scope(cls, question_text: str, class_input: Any, subject: str) -> Dict[str, Any]:
        """
        Validates whether question_text matches the target class and subject scope prior to calling Gemini.
        Returns: {"in_scope": True/False, "reason": str}
        """
        text_lower = question_text.lower()
        target_subj = subject.strip().lower()

        # Keyword categories for subject boundary checking
        math_keywords = [
            "sin²", "cos²", "tan²", "trigonometry", "sin theta", "cos theta", "dy/dx",
            "integration", "derivative", "differentiate", "matrix", "determinant",
            "quadratic equation", "arithmetic progression"
        ]
        biology_keywords = [
            "photosynthesis", "chlorophyll", "stomata", "respiration", "xylem", "phloem",
            "mitosis", "meiosis", "dna", "chromosome", "enzyme", "hemoglobin", "nephron",
            "neuron", "reflex arc"
        ]
        physics_keywords = [
            "electric field", "magnetic field", "capacitance", "inductor", "solenoid",
            "refractive index", "coulomb", "potential difference", "resistance", "resistivity"
        ]
        chemistry_keywords = [
            "chemical equation", "stoichiometry", "oxidation state", "electronegativity",
            "alkane", "alkene", "alkyne", "isomers", "titration", "molarity"
        ]

        if "math" in target_subj:
            for kw in biology_keywords + chemistry_keywords:
                if kw in text_lower:
                    return {
                        "in_scope": False,
                        "reason": f"OUT_OF_SCOPE_SUBJECT: Question contains Science/Biology keyword '{kw}' when target subject is '{subject}'."
                    }
        elif "physics" in target_subj:
            for kw in biology_keywords + math_keywords:
                if kw in text_lower:
                    return {
                        "in_scope": False,
                        "reason": f"OUT_OF_SCOPE_SUBJECT: Question contains non-Physics keyword '{kw}' when target subject is '{subject}'."
                    }
        elif "chemistry" in target_subj:
            for kw in biology_keywords + math_keywords:
                if kw in text_lower:
                    return {
                        "in_scope": False,
                        "reason": f"OUT_OF_SCOPE_SUBJECT: Question contains non-Chemistry keyword '{kw}' when target subject is '{subject}'."
                    }
        elif "science" in target_subj:
            for kw in math_keywords:
                if kw in text_lower:
                    return {
                        "in_scope": False,
                        "reason": f"OUT_OF_SCOPE_SUBJECT: Question contains Mathematics keyword '{kw}' when target subject is '{subject}'."
                    }

        return {"in_scope": True, "reason": "In-scope for target class and subject."}

    @classmethod
    def match_or_fallback_topic(cls, class_input: Any, subject: str, chapter: str, raw_topic: str) -> str:
        """
        Normalizes and matches raw topic text against official NCERT syllabus topics.
        Returns official topic title if matched, otherwise returns 'General'.
        """
        official_topics = cls.get_topics(class_input, subject, chapter)
        target = raw_topic.strip().lower()
        for tp in official_topics:
            if tp.lower() == target or target in tp.lower() or tp.lower() in target:
                return tp
        return "General"


# Functional wrapper functions as required by specification
def get_classes() -> List[int]:
    """Returns supported NCERT class levels [10, 12]."""
    return SyllabusService.get_classes()


def get_subjects(class_name: Any) -> List[str]:
    """Returns official NCERT subjects for class_name (10 or 12)."""
    return SyllabusService.get_subjects(class_name)


def get_chapters(class_name: Any, subject: str) -> List[str]:
    """Returns official NCERT chapters for class_name and subject."""
    return SyllabusService.get_chapters(class_name, subject)


def get_topics(class_name: Any, subject: str, chapter: str) -> List[str]:
    """Returns official NCERT topics for class_name, subject, and chapter."""
    return SyllabusService.get_topics(class_name, subject, chapter)


def validate_chapter(class_name: Any, subject: str, chapter: str) -> bool:
    """Validates if chapter belongs to official NCERT syllabus."""
    return SyllabusService.validate_chapter(class_name, subject, chapter)


def validate_topic(class_name: Any, subject: str, chapter: str, topic: str) -> bool:
    """Validates if topic belongs to official NCERT syllabus chapter."""
    return SyllabusService.validate_topic(class_name, subject, chapter, topic)
