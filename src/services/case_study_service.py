"""
Study Smarter - Dedicated Case-Study & Passage-Based Question Service Module
Provides specialized support for:
1. Detecting case studies, context paragraphs, and comprehension passages in PDFs.
2. Associating each passage with all its corresponding sub-questions (e.g., 5 questions per passage).
3. Switching dynamically to new paragraphs when a new case-based section begins.
4. Cleanly separating passages and questions for rendering in the Practice & Quiz UI.
5. Generating rich, dark-mode UI card HTML for case-based and standard questions.

Preserves existing standard MCQ extraction without breaking any existing functionality.
"""

import re
from typing import List, Dict, Any, Tuple, Optional
from src.logger import logger
from src.services.pdf_service import PDFService


class CaseStudyService:
    """Specialized service for handling case-based and passage-based MCQs."""

    # Passage header patterns (e.g. CBSE / NCERT exam formats)
    PASSAGE_HEADER_PATTERNS = [
        # Chemistry / CBSE: "(XVI) Read the passage given below and answer the following questions:"
        r"^\s*(?:\([IVXLCDM]+\)\s*)?Read the passage given below and answer the (?:following )?questions?:?",
        # Mathematics / CBSE: "CASE STUDY 1:", "CASE STUDY1:", "Case Study 2 -"
        r"^\s*CASE\s*STUDY\s*(\d*)\s*[\:\-]",
        # Generic passage: "Passage 1:", "Passage:"
        r"^\s*Passage\s*(?:\d+)?\s*[\:\-]",
    ]

    COMBINED_HEADER_REGEX = re.compile(
        "|".join(f"(?:{p})" for p in PASSAGE_HEADER_PATTERNS),
        re.MULTILINE | re.IGNORECASE
    )

    # Trailing transition prompts right before the questions start
    TRANSITION_PROMPT_PATTERNS = [
        r"(?:Based on the (?:above\s+)?(?:passage|information|situation|paragraph|given data),?\s*(?:answer the following(?: questions)?)?[\:\.]?)",
        r"(?:From this situation\s*,?\s*answer the following[\:\.]?)",
        r"(?:In the following questions,?\s*a statement of assertion.*?on the basis of the above passage[\:\.]?)",
        r"(?:Answer the following questions?[\:\.]?)",
    ]

    COMBINED_TRANSITION_REGEX = re.compile(
        "|".join(f"(?:{p})" for p in TRANSITION_PROMPT_PATTERNS),
        re.IGNORECASE
    )

    @classmethod
    def format_case_question(cls, passage: str, sub_question: str) -> str:
        """
        Formats a case-based sub-question by prepending its passage context.
        Human-readable and structured so it can be parsed back or displayed anywhere.
        """
        passage_clean = passage.strip()
        sub_q_clean = sub_question.strip()
        return f"[Case / Passage Context]\n{passage_clean}\n\n[Question]\n{sub_q_clean}"

    @classmethod
    def split_passage_and_question(cls, question_text: str) -> Tuple[Optional[str], str]:
        """
        Extracts (passage_text, clean_sub_question) from a stored question string.
        If no passage is detected, returns (None, original_question_text).
        """
        if not question_text:
            return None, ""

        # Pattern 1: [Case / Passage Context] ... [Question] ...
        m1 = re.match(
            r"^\s*\[(?:Case\s*(?:\/\s*Passage)?\s*Context|Passage)\]\s*\n(.*?)\n\s*\[Question\]\s*\n(.*)$",
            question_text,
            re.DOTALL | re.IGNORECASE,
        )
        if m1:
            return m1.group(1).strip(), m1.group(2).strip()

        # Pattern 2: Embedded "(XVI) Read the passage given below..." header
        m2 = re.match(
            r"^\s*(?:\([IVXLCDM]+\)\s*)?Read the passage given below and answer the (?:following )?questions?:?\s*\n(.*?)\n\s*(?:(?:Q(?:uestion)?\s*)?[1-9]\.|\(?\b[A-D]\)?\b)(.*)$",
            question_text,
            re.DOTALL | re.IGNORECASE,
        )
        if m2:
            return m2.group(1).strip(), m2.group(2).strip()

        return None, question_text.strip()

    @classmethod
    def parse_case_block(
        cls, block_text: str, start_num: int = 1
    ) -> Tuple[Optional[str], List[Dict[str, Any]]]:
        """
        Parses a single case study section:
        Extracts the common passage paragraph and all its sub-questions.
        """
        lines = block_text.strip().split("\n")
        body = "\n".join(lines[1:]).strip()

        # Match sub-question headers like 1., 2., Q1., 1)
        q_pattern = r"(?m)^\s*(?:Q(?:uestion)?[\.\s]*)?(\d+)[\.\:\)]\s+"
        q_matches = list(re.finditer(q_pattern, body))
        if not q_matches:
            return None, []

        first_q_pos = q_matches[0].start()
        passage_raw = body[:first_q_pos].strip()

        # Remove trailing transition statements
        t_match = cls.COMBINED_TRANSITION_REGEX.search(passage_raw)
        if t_match:
            passage_raw = passage_raw[:t_match.start()].strip()

        passage_clean = re.sub(r"\n{3,}", "\n\n", passage_raw).strip()
        if len(passage_clean) < 20:
            return None, []

        # Split sub-questions
        sub_blocks = []
        for q_idx in range(len(q_matches)):
            q_start = q_matches[q_idx].start()
            q_end = q_matches[q_idx + 1].start() if q_idx + 1 < len(q_matches) else len(body)
            sub_blocks.append(body[q_start:q_end].strip())

        parsed_qs = []
        option_pattern = r"(?i)(?:\n|^|\s)(?:\(|\[)?\s*([A-D])\s*(?:\)|\]|\.|\:)\s*"
        for idx, sblock in enumerate(sub_blocks, start_num):
            parts = re.split(option_pattern, sblock)
            q_text = parts[0].strip()
            q_clean = re.sub(r"^(?:Q(?:uestion)?)?[\.\s\:\d\-\)]*", "", q_text, flags=re.IGNORECASE).strip()

            opts = {}
            for k in range(1, len(parts) - 1, 2):
                let = parts[k].strip().upper()
                val = parts[k + 1].strip()
                if let in ["A", "B", "C", "D"]:
                    opts[let] = " ".join(val.split())

            if q_clean and len(opts) >= 2:
                formatted_text = cls.format_case_question(passage_clean, q_clean)
                parsed_qs.append({
                    "question_num": idx,
                    "question": formatted_text,
                    "raw_question": q_clean,
                    "passage_text": passage_clean,
                    "is_case_based": True,
                    "options": {
                        "A": opts.get("A", "[Option A Missing]"),
                        "B": opts.get("B", "[Option B Missing]"),
                        "C": opts.get("C", "[Option C Missing]"),
                        "D": opts.get("D", "[Option D Missing]"),
                    },
                    "extraction_method": "Case-Study Extractor",
                })

        return passage_clean, parsed_qs

    @classmethod
    def parse_mcqs_with_cases(cls, raw_text: str) -> List[Dict[str, Any]]:
        """
        Extracts MCQs from raw PDF text with full support for case-based passages:
        - If case studies/passages are found, binds the passage paragraph to every sub-question.
        - When a new case study begins, binds the new paragraph to subsequent sub-questions.
        - Preserves all standard non-case MCQs in their natural sequential order.
        - If no case studies are detected, defers directly to PDFService.parse_mcqs_regex().
        """
        if not raw_text or not raw_text.strip():
            return []

        raw_text = raw_text.replace("\r\n", "\n").strip()
        header_matches = list(cls.COMBINED_HEADER_REGEX.finditer(raw_text))

        # No case-based passages: fallback cleanly to standard regex parser
        if not header_matches:
            logger.info("No case studies detected in text. Using standard regex parser.")
            return PDFService.parse_mcqs_regex(raw_text)

        logger.info(f"Detected {len(header_matches)} case study / passage headers in document.")
        all_questions = []
        q_counter = 1

        # 1. Text before the first case study (standard questions)
        pre_text = raw_text[:header_matches[0].start()].strip()
        if pre_text:
            std_qs = PDFService.parse_mcqs_regex(pre_text)
            for sq in std_qs:
                sq["question_num"] = q_counter
                q_counter += 1
                all_questions.append(sq)

        # 2. Process each case study section
        for i, m in enumerate(header_matches):
            c_start = m.start()
            c_end = header_matches[i + 1].start() if i + 1 < len(header_matches) else len(raw_text)
            case_section = raw_text[c_start:c_end]

            passage, case_qs = cls.parse_case_block(case_section, start_num=q_counter)
            if case_qs:
                for cq in case_qs:
                    cq["question_num"] = q_counter
                    q_counter += 1
                    all_questions.append(cq)
            else:
                # Fallback if case block had an unusual format: extract questions with standard regex
                fallback_qs = PDFService.parse_mcqs_regex(case_section)
                for fq in fallback_qs:
                    fq["question_num"] = q_counter
                    q_counter += 1
                    all_questions.append(fq)

        logger.info(f"Extracted {len(all_questions)} questions ({sum(1 for q in all_questions if q.get('is_case_based'))} case-based).")
        return all_questions

    @classmethod
    def render_question_card_html(
        cls,
        question_text: str,
        question_num: Optional[int] = None,
        topic_line: str = "",
    ) -> str:
        """
        Renders the Question card HTML for the Streamlit Practice & Quiz interface.
        If the question is case-based, renders the paragraph passage in a styled
        dark-mode callout card, followed by the sub-question.
        If standard, renders the regular question cleanly.
        """
        passage_text, clean_q = cls.split_passage_and_question(question_text)

        q_num_html = f'<div class="ss-q-header">Question {question_num}</div>' if question_num is not None else ""

        passage_html = ""
        if passage_text:
            safe_passage = (
                passage_text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
            )
            passage_html = (
                f'<div class="ss-case-card">'
                f'<div class="ss-case-badge">📖 Case / Context Passage</div>'
                f'<div class="ss-case-text">{safe_passage}</div>'
                f'</div>'
            )

        safe_clean_q = (
            clean_q.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

        topic_html = f'<div class="ss-q-topic">{topic_line}</div>' if topic_line else ""

        card_html = (
            f'<div class="ss-question-card">'
            f'{q_num_html}'
            f'{passage_html}'
            f'<div class="ss-q-text">{safe_clean_q}</div>'
            f'{topic_html}'
            f'</div>'
        )
        return card_html
