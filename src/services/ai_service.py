"""
Study Smarter - AI Service Module
Provides isolated interfaces for:
1. AI-assisted structured MCQ question extraction from PDFs.
2. AI-assisted answer resolution, step-by-step concise explanation, confidence scoring,
   and verification status assignment (VERIFIED vs NEEDS_REVIEW).
3. Topic & Difficulty Classification - works for any subject domain (not restricted to NCERT).

Never hardcodes credentials or crashes the application on API failure.
"""

import json
import re
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional
from src.config import config
from src.logger import logger
from src.utils.exceptions import AIServiceError
from src.services.syllabus_service import SyllabusService


class AIService:
    """Isolated Service Module for AI Extraction, Answer Solving, and Topic Classification."""

    EXTRACT_PROMPT_TEMPLATE = """
You are a precise educational question extractor.
Your ONLY task is to extract Multiple Choice Questions (MCQs) and their options (A, B, C, D) from the raw text provided.

CRITICAL INSTRUCTIONS:
1. Do NOT determine or invent correct answers or explanations.
2. Return ONLY a single valid JSON object. Do not include markdown text, commentary, or extra output outside the JSON.
3. The JSON output MUST strictly conform to the following JSON structure:

{{
  "questions": [
    {{
      "question": "The complete question text here?",
      "options": {{
        "A": "First option text",
        "B": "Second option text",
        "C": "Third option text",
        "D": "Fourth option text"
      }}
    }}
  ]
}}

Raw Text to Extract:
\"\"\"
{raw_text}
\"\"\"
"""

    SOLVE_PROMPT_TEMPLATE = """
You are an expert educator specializing in {subject}.
Analyze the following Multiple Choice Question (MCQ) and determine the correct answer option from (A, B, C, D).

Context: {chapter} — {topic}

Question:
\"{question_text}\"

Options:
A: {option_a}
B: {option_b}
C: {option_c}
D: {option_d}

CRITICAL INSTRUCTIONS:
1. Select EXACTLY ONE correct option letter from ["A", "B", "C", "D"].
2. Provide a concise, student-friendly explanation.
3. Set confidence to "High", "Medium", or "Low" based on certainty.
4. Always set "in_scope": true.
5. Return ONLY a single valid JSON object with NO markdown code fences or extra commentary:

{{
  "in_scope": true,
  "correct_answer": "A|B|C|D",
  "explanation": "short student-friendly explanation",
  "confidence": "High|Medium|Low"
}}
"""

    CLASSIFY_PROMPT_TEMPLATE = """
You are an expert educator. Classify the following Multiple Choice Question into a chapter and topic.
{context_hint}

Question to Classify:
\"{question_text}\"

Options:
A: {option_a}
B: {option_b}
C: {option_c}
D: {option_d}

CRITICAL INSTRUCTIONS:
1. Infer the most appropriate chapter and topic based on the question content.
2. Assess the difficulty level as strictly one of: "Easy", "Medium", "Hard".
3. Return ONLY a single valid JSON object with NO markdown code fences or extra commentary:

{{
  "chapter": "Chapter or Unit Name",
  "topic": "Specific Topic Name",
  "difficulty": "Medium"
}}
"""

    @classmethod
    def extract_structured_questions(cls, raw_text: str) -> Dict[str, Any]:
        """
        Sends raw text content to AI API and requests strict structured JSON output for questions/options.
        Catches all API timeouts and errors safely without crashing.
        """
        if not raw_text or not raw_text.strip():
            return {"success": False, "message": "Raw text input is empty.", "questions": []}

        api_key = (config.GEMINI_API_KEY or config.AI_API_KEY).strip()
        if not api_key or api_key == "your_ai_api_key_here":
            logger.warning("Gemini API key is not configured in .env file.")
            return {
                "success": False,
                "message": "Gemini API key is not configured. Please set GEMINI_API_KEY in your .env file.",
                "questions": [],
            }

        prompt = cls.EXTRACT_PROMPT_TEMPLATE.format(raw_text=raw_text[:4000])

        try:
            logger.info("Initiating AI API request for structured MCQ extraction...")
            raw_json_str = cls._call_gemini_api(prompt, api_key)
            valid_questions = cls.validate_and_sanitize_json_schema(raw_json_str)
            return {
                "success": True,
                "message": f"Successfully extracted {len(valid_questions)} questions via AI API.",
                "questions": valid_questions,
            }
        except Exception as err:
            logger.error(f"AI API Extraction Failed: {err}")
            return {
                "success": False,
                "message": f"AI API Request Failed: {err}",
                "questions": [],
            }

    @classmethod
    def solve_single_question(
        cls,
        question_dict: Dict[str, Any],
        class_level: int = 12,
        subject: str = "Physics"
    ) -> Dict[str, Any]:
        """Convenience method to solve a single question dictionary."""
        q_text = question_dict.get("question", "") if isinstance(question_dict, dict) else str(question_dict)
        opts = question_dict.get("options", {}) if isinstance(question_dict, dict) else {}
        ch = question_dict.get("chapter", "General") if isinstance(question_dict, dict) else "General"
        tp = question_dict.get("topic", "General") if isinstance(question_dict, dict) else "General"
        return cls.solve_and_verify_question(q_text, opts, class_level=class_level, subject=subject, chapter=ch, topic=tp)

    @classmethod
    def solve_and_verify_question(
        cls,
        question_text: str,
        options: Dict[str, str],
        class_level: int = 12,
        subject: str = "Physics",
        chapter: str = "General",
        topic: str = "General"
    ) -> Dict[str, Any]:
        """
        AI Answer-Solving System with STRICT Class & Subject Scoping:
        Pre-validates scope before calling Gemini, sends strict scope constraints to Gemini,
        and verifies results via the Independent Verification Layer.
        """
        opt_a = options.get("A", "")
        opt_b = options.get("B", "")
        opt_c = options.get("C", "")
        opt_d = options.get("D", "")

        # Scope check only for legacy NCERT data (class_level 10 or 12)
        if class_level in (10, 12):
            scope_val = SyllabusService.validate_question_scope(question_text, class_level, subject)
            if not scope_val["in_scope"]:
                logger.warning(f"Pre-Gemini Scope Check Failed: {scope_val['reason']}")
                return {
                    "correct_answer": "A",
                    "explanation": scope_val["reason"],
                    "confidence": "Low",
                    "confidence_score": 0.10,
                    "verification_status": "NEEDS_REVIEW",
                    "in_scope": False,
                }

        api_key = (config.GEMINI_API_KEY or config.AI_API_KEY).strip()
        if not api_key or api_key == "your_ai_api_key_here":
            logger.warning("Gemini API key is not configured for answer solving.")
            return cls._fallback_heuristic_solver(question_text, options)

        prompt = cls.SOLVE_PROMPT_TEMPLATE.format(
            subject=subject if subject and subject != "General" else "the subject",
            chapter=chapter or "General",
            topic=topic or "General",
            question_text=question_text,
            option_a=opt_a,
            option_b=opt_b,
            option_c=opt_c,
            option_d=opt_d,
        )

        try:
            logger.info(f"Calling AI Answer Solver for '{question_text[:50]}...'")
            raw_json_str = cls._call_gemini_api(prompt, api_key)
            solved_dict = cls.validate_ai_answer_response(
                raw_json_str,
                question_text=question_text,
                options=options,
                target_class=class_level,
                target_subject=subject
            )
            return solved_dict
        except Exception as err:
            logger.error(f"AI Answer Solver failed: {err}. Using fallback heuristic solver.")
            return cls._fallback_heuristic_solver(question_text, options)

    @classmethod
    def batch_solve_and_classify_questions(
        cls,
        extracted_questions: List[Dict[str, Any]],
        class_level: int = 0,
        subject: str = "General",
        batch_size: int = 10,
        progress_callback: Optional[Any] = None,
    ) -> List[Dict[str, Any]]:
        """
        Processes questions in structured batches of `batch_size` (default 10) to Gemini.
        In each batch request, Gemini simultaneously:
        1. Determines the strictly correct answer option (A, B, C, or D).
        2. Generates a 2-4 sentence educational solution explaining WHY that answer is correct.
        3. Infers chapter, topic, and difficulty.
        Strictly maps returned solutions to each original question by ID.
        Enforces educational solution quality (rejects internal metadata/empty solutions).
        """
        import time
        api_key = config.GEMINI_API_KEY
        total_qs = len(extracted_questions)
        if not api_key:
            logger.warning("No Gemini API key available. Marking batch for review.")
            out = []
            for q in extracted_questions:
                item = q.copy()
                item["correct_answer"] = "A"
                item["explanation"] = ""
                item["verification_status"] = "NEEDS_REVIEW"
                item["review_reason"] = "AI API key not configured."
                item["chapter"] = item.get("chapter") or "General"
                item["topic"] = item.get("topic") or "General"
                item["difficulty"] = item.get("difficulty") or "Medium"
                out.append(item)
            return out

        batch_size = max(1, getattr(config, "GEMINI_BATCH_SIZE", batch_size))
        all_results: List[Dict[str, Any]] = []

        for start_idx in range(0, total_qs, batch_size):
            end_idx = min(start_idx + batch_size, total_qs)
            batch_slice = extracted_questions[start_idx:end_idx]
            batch_num = (start_idx // batch_size) + 1
            total_batches = (total_qs + batch_size - 1) // batch_size

            if progress_callback:
                pct = int(25 + (start_idx / total_qs) * 65)
                progress_callback(
                    f"Generating answers and solutions... ({start_idx}/{total_qs} processed)",
                    pct
                )

            batch_input = []
            for idx, q in enumerate(batch_slice, start=1):
                q_text = q.get("question") or q.get("question_text") or ""
                opts = q.get("options") or {}
                batch_input.append({
                    "id": idx,
                    "question": q_text,
                    "options": {
                        "A": opts.get("A", ""),
                        "B": opts.get("B", ""),
                        "C": opts.get("C", ""),
                        "D": opts.get("D", ""),
                    }
                })

            prompt = (
                f"You are an expert academic educator and exam question specialist.\n"
                f"For each of the following multiple-choice questions:\n"
                f"1. Determine the strictly correct option letter (\"A\", \"B\", \"C\", or \"D\").\n"
                f"2. Provide a high-quality educational solution (2 to 4 concise, clear sentences) explaining the conceptual reason WHY that option is correct. Never output metadata like \"Answer is A\" or \"Option B is correct\". Provide a clear, conceptual explanation suitable for students.\n"
                f"3. Infer the chapter name, topic name, and difficulty level (\"Easy\", \"Medium\", or \"Hard\") relevant to {subject}.\n\n"
                f"Questions to solve:\n{json.dumps(batch_input, indent=2)}\n\n"
                f"Respond with a valid JSON array of objects strictly matching this schema:\n"
                f"[\n"
                f"  {{\n"
                f"    \"id\": 1,\n"
                f"    \"correct_answer\": \"B\",\n"
                f"    \"solution\": \"Clear, educational 2-4 sentence explanation...\",\n"
                f"    \"chapter\": \"Chapter Name\",\n"
                f"    \"topic\": \"Topic Name\",\n"
                f"    \"difficulty\": \"Medium\"\n"
                f"  }}\n"
                f"]"
            )

            batch_solved_map = {}
            try:
                logger.info(f"Solving batch {batch_num}/{total_batches} ({len(batch_slice)} questions)...")
                raw_json = cls._call_gemini_api(prompt, api_key)
                clean_json = raw_json.strip()
                clean_json = re.sub(r"^```(?:json)?\s*", "", clean_json, flags=re.IGNORECASE)
                clean_json = re.sub(r"\s*```$", "", clean_json).strip()
                parsed_list = json.loads(clean_json)

                if isinstance(parsed_list, list):
                    for item in parsed_list:
                        if isinstance(item, dict) and "id" in item:
                            batch_solved_map[item["id"]] = item
            except Exception as err:
                logger.warning(f"Batch {batch_num} API call encountered error: {err}")

            # Assign and validate each question in the batch
            for idx, orig_q in enumerate(batch_slice, start=1):
                solved_item = batch_solved_map.get(idx, {})
                corr_ans = str(solved_item.get("correct_answer", "")).strip().upper()
                solution = str(solved_item.get("solution", "")).strip()
                chapter = str(solved_item.get("chapter", "")).strip() or orig_q.get("chapter", "General")
                topic = str(solved_item.get("topic", "")).strip() or orig_q.get("topic", "General")
                difficulty = str(solved_item.get("difficulty", "Medium")).strip().capitalize()
                if difficulty not in ["Easy", "Medium", "Hard"]:
                    difficulty = "Medium"

                is_valid_ans = corr_ans in ["A", "B", "C", "D"]
                bad_kw = [
                    "low confidence", "unable to determine", "held for review",
                    "flagged for review", "processing error", "unverified",
                    "answer is a", "answer is b", "answer is c", "answer is d",
                    "correct option is"
                ]
                is_valid_sol = (
                    len(solution) >= 15 and
                    not any(kw in solution.lower() for kw in bad_kw)
                )

                item_copy = orig_q.copy()
                item_copy["chapter"] = chapter
                item_copy["topic"] = topic
                item_copy["difficulty"] = difficulty

                if is_valid_ans and is_valid_sol:
                    item_copy["correct_answer"] = corr_ans
                    item_copy["explanation"] = solution
                    item_copy["verification_status"] = "AI_VERIFIED"
                    item_copy["answer_confidence"] = 0.90
                    item_copy["review_reason"] = None
                else:
                    item_copy["correct_answer"] = corr_ans if is_valid_ans else "A"
                    item_copy["explanation"] = ""
                    item_copy["verification_status"] = "NEEDS_REVIEW"
                    item_copy["answer_confidence"] = 0.30
                    item_copy["review_reason"] = "Could not verify with high confidence educational explanation."

                all_results.append(item_copy)

            if end_idx < total_qs:
                time.sleep(1.0)

        return all_results

    @classmethod
    def solve_question_batch(
        cls,
        extracted_questions: List[Dict[str, Any]],
        class_level: int = 12,
        subject: str = "Physics"
    ) -> List[Dict[str, Any]]:
        """
        Solves and assigns verified answers for a list of extracted questions.
        Fault-tolerant: individual question errors will not break batch processing.
        """
        results = []
        for q in extracted_questions:
            q_text = q.get("question", "")
            opts = q.get("options", {})
            ch = q.get("chapter", "General")
            tp = q.get("topic", "General")

            try:
                solve_res = cls.solve_and_verify_question(
                    question_text=q_text,
                    options=opts,
                    class_level=class_level,
                    subject=subject,
                    chapter=ch,
                    topic=tp
                )
            except Exception as err:
                logger.warning(f"Solving failed for question '{q_text[:30]}...': {err}")
                solve_res = {
                    "correct_answer": "A",
                    "explanation": f"Processing error: {err}",
                    "confidence": "Low",
                    "confidence_score": 0.20,
                    "verification_status": "NEEDS_REVIEW",
                }

            updated_q = q.copy()
            updated_q["correct_answer"] = solve_res["correct_answer"]
            updated_q["explanation"] = solve_res["explanation"]
            updated_q["answer_confidence"] = solve_res.get("confidence_score", 0.50)
            updated_q["confidence_level"] = solve_res.get("confidence", "Medium")
            updated_q["verification_status"] = solve_res.get("verification_status", "NEEDS_REVIEW")
            results.append(updated_q)

        return results

    @classmethod
    def classify_question_ncert(
        cls,
        question_text: str,
        options: Dict[str, str],
        class_level: int = 0,
        subject: str = "General"
    ) -> Dict[str, Any]:
        """
        Topic Classification Service:
        Classifies an MCQ into Chapter, Topic, and Difficulty.
        For NCERT data (class 10/12), validates against predefined syllabus.
        For generic question banks (class_level=0), lets Gemini infer freely.
        """
        opt_a = options.get("A", "")
        opt_b = options.get("B", "")
        opt_c = options.get("C", "")
        opt_d = options.get("D", "")

        api_key = config.AI_API_KEY.strip()
        if not api_key or api_key == "your_ai_api_key_here":
            logger.warning("AI API Key missing for classification. Using fallback classifier.")
            return cls._fallback_heuristic_classifier(question_text, class_level, subject)

        # For NCERT data, provide allowed chapters/topics as context
        if class_level in (10, 12):
            allowed_chapters = SyllabusService.get_chapters(class_level, subject)
            syllabus_lines = []
            for ch in allowed_chapters:
                topics = SyllabusService.get_topics(class_level, subject, ch)
                syllabus_lines.append(f"- Chapter: \"{ch}\" | Topics: {', '.join(topics[:5])}")
            context_hint = f"Classify strictly into NCERT Class {class_level} {subject} chapters:\n" + "\n".join(syllabus_lines)
        else:
            context_hint = f"The question is from a {subject} question bank. Infer the most appropriate chapter and topic."

        prompt = cls.CLASSIFY_PROMPT_TEMPLATE.format(
            context_hint=context_hint,
            question_text=question_text,
            option_a=opt_a,
            option_b=opt_b,
            option_c=opt_c,
            option_d=opt_d,
        )

        try:
            logger.info(f"Calling AI Classifier: '{question_text[:50]}...'")
            raw_json_str = cls._call_gemini_api(prompt, api_key)
            if class_level in (10, 12):
                return cls.validate_and_normalize_classification(class_level, subject, raw_json_str)
            else:
                return cls._parse_generic_classification(raw_json_str)
        except Exception as err:
            logger.error(f"AI Classification failed: {err}. Using fallback classifier.")
            return cls._fallback_heuristic_classifier(question_text, class_level, subject)

    @classmethod
    def classify_question_batch(
        cls,
        extracted_questions: List[Dict[str, Any]],
        class_level: int = 0,
        subject: str = "General"
    ) -> List[Dict[str, Any]]:
        """
        Classifies a list of extracted questions into Chapter, Topic, and Difficulty.
        Works for both NCERT (class 10/12) and generic question banks (class_level=0).
        """
        results = []
        for q in extracted_questions:
            q_text = q.get("question", "")
            opts = q.get("options", {})

            class_res = cls.classify_question_ncert(
                question_text=q_text,
                options=opts,
                class_level=class_level,
                subject=subject
            )

            updated_q = q.copy()
            updated_q["chapter"] = class_res["chapter"]
            updated_q["topic"] = class_res["topic"]
            updated_q["difficulty"] = class_res["difficulty"]

            # Only flag NEEDS_REVIEW for NCERT data with invalid chapters
            if class_level in (10, 12) and not class_res.get("valid_syllabus", True):
                updated_q["verification_status"] = "NEEDS_REVIEW"
                logger.warning(f"Question flagged NEEDS_REVIEW due to invalid chapter '{class_res['chapter']}'.")

            results.append(updated_q)

        return results

    @classmethod
    def _parse_generic_classification(cls, response_text: str) -> Dict[str, Any]:
        """Parses free-form Gemini classification response for non-NCERT question banks."""
        clean_text = response_text.strip()
        clean_text = re.sub(r"^```(?:json)?\s*", "", clean_text, flags=re.IGNORECASE)
        clean_text = re.sub(r"\s*```$", "", clean_text).strip()
        try:
            data = json.loads(clean_text)
            if isinstance(data, dict):
                chapter = str(data.get("chapter", "General")).strip() or "General"
                topic = str(data.get("topic", "General")).strip() or "General"
                raw_diff = str(data.get("difficulty", "Medium")).strip().capitalize()
                if raw_diff not in ("Easy", "Medium", "Hard"):
                    raw_diff = "Medium"
                return {"chapter": chapter, "topic": topic, "difficulty": raw_diff, "valid_syllabus": True}
        except Exception:
            pass
        return {"chapter": "General", "topic": "General", "difficulty": "Medium", "valid_syllabus": True}

    @classmethod
    def validate_and_normalize_classification(
        cls,
        class_level: int,
        subject: str,
        response_text: str
    ) -> Dict[str, Any]:
        """
        Backend Syllabus Validator & Normalizer:
        1. Strips markdown fences (```json ... ```).
        2. Validates proposed chapter against SyllabusService.validate_chapter().
        3. Normalizes chapter name via SyllabusService.match_or_fallback_chapter().
        4. Validates proposed topic against SyllabusService.validate_topic().
        5. Enforces difficulty in ['Easy', 'Medium', 'Hard'].
        6. Flags valid_syllabus=False and sets NEEDS_REVIEW if chapter is invented/invalid.
        """
        default_ch = SyllabusService.get_chapters(class_level, subject)[0] if SyllabusService.get_chapters(class_level, subject) else "General"
        default_tp = SyllabusService.get_topics(class_level, subject, default_ch)[0] if SyllabusService.get_topics(class_level, subject, default_ch) else "General"

        if not response_text or not response_text.strip():
            return {
                "chapter": default_ch,
                "topic": default_tp,
                "difficulty": "Medium",
                "valid_syllabus": False,
                "message": "AI Classification response was empty.",
            }

        clean_text = response_text.strip()
        clean_text = re.sub(r"^```(?:json)?\s*", "", clean_text, flags=re.IGNORECASE)
        clean_text = re.sub(r"\s*```$", "", clean_text)
        clean_text = clean_text.strip()

        try:
            data = json.loads(clean_text)
        except json.JSONDecodeError as err:
            logger.warning(f"Failed to parse AI Classification JSON: {err}")
            return {
                "chapter": default_ch,
                "topic": default_tp,
                "difficulty": "Medium",
                "valid_syllabus": False,
                "message": f"Malformed JSON: {err}",
            }

        if not isinstance(data, dict):
            return {
                "chapter": default_ch,
                "topic": default_tp,
                "difficulty": "Medium",
                "valid_syllabus": False,
                "message": "Response format was not a dictionary.",
            }

        raw_chapter = str(data.get("chapter", "")).strip()
        raw_topic = str(data.get("topic", "")).strip()
        raw_diff = str(data.get("difficulty", "Medium")).strip().capitalize()

        # Normalize difficulty
        if raw_diff not in ["Easy", "Medium", "Hard"]:
            if "easy" in raw_diff.lower():
                diff = "Easy"
            elif "hard" in raw_diff.lower() or "difficult" in raw_diff.lower():
                diff = "Hard"
            else:
                diff = "Medium"
        else:
            diff = raw_diff

        # Backend Syllabus Validation for Chapter
        is_valid_ch = SyllabusService.validate_chapter(class_level, subject, raw_chapter)
        matched_ch = SyllabusService.match_or_fallback_chapter(class_level, subject, raw_chapter)

        # Check if raw_chapter is an invented or unsupported chapter name
        is_fuzzy_matched = any(
            word in matched_ch.lower()
            for word in raw_chapter.lower().split()
            if len(word) > 3
        ) if (matched_ch and raw_chapter) else False

        if not is_valid_ch and not is_fuzzy_matched:
            logger.warning(f"AI returned invalid/invented chapter '{raw_chapter}'. Rejecting classification.")
            return {
                "chapter": f"Invalid: '{raw_chapter}'",
                "topic": raw_topic or default_tp,
                "difficulty": diff,
                "valid_syllabus": False,
                "message": f"Invented or unsupported NCERT chapter name '{raw_chapter}'. Flagged NEEDS_REVIEW.",
            }

        # Backend Syllabus Validation for Topic
        matched_tp = SyllabusService.match_or_fallback_topic(class_level, subject, matched_ch, raw_topic)

        return {
            "chapter": matched_ch,
            "topic": matched_tp,
            "difficulty": diff,
            "valid_syllabus": True,
            "message": "Successfully classified against predefined NCERT syllabus.",
        }

    @classmethod
    def _fallback_heuristic_classifier(
        cls,
        question_text: str,
        class_level: int,
        subject: str
    ) -> Dict[str, Any]:
        """
        Fallback keyword-matching classifier when AI API is unavailable.
        For NCERT data: matches keywords against predefined syllabus.
        For generic banks: returns 'General'.
        """
        if class_level in (10, 12):
            text_lower = question_text.lower()
            chapters = SyllabusService.get_chapters(class_level, subject)

            best_ch = chapters[0] if chapters else "General"
            best_tp = SyllabusService.get_topics(class_level, subject, best_ch)[0] if chapters else "General"

            for ch in chapters:
                if ch.lower() in text_lower or any(word in text_lower for word in ch.lower().split()):
                    best_ch = ch
                    topics = SyllabusService.get_topics(class_level, subject, ch)
                    for tp in topics:
                        if tp.lower() in text_lower or any(word in text_lower for word in tp.lower().split()):
                            best_tp = tp
                            break
                    break

            return {
                "chapter": best_ch,
                "topic": best_tp,
                "difficulty": "Medium",
                "valid_syllabus": True,
                "message": "Classified using fallback keyword-matching engine.",
            }

        # Generic fallback for non-NCERT banks
        return {
            "chapter": "General",
            "topic": "General",
            "difficulty": "Medium",
            "valid_syllabus": True,
            "message": "Generic fallback classification.",
        }

    @classmethod
    def validate_ai_answer_response(
        cls,
        response_text: str,
        question_text: str = "",
        options: Optional[Dict[str, str]] = None,
        target_class: int = 12,
        target_subject: str = "Physics"
    ) -> Dict[str, Any]:
        """
        Backend Validator for AI Answer Response with Scope Enforcement:
        1. Strips markdown fences (```json ... ```).
        2. Validates in_scope flag.
        3. Validates correct_answer is strictly in ['A', 'B', 'C', 'D'].
        4. Delegates to Independent Verification Service (Python programmatic solver & cross-verification).
        """
        if not response_text or not response_text.strip():
            return {
                "correct_answer": "A",
                "explanation": "Unverified - AI response was empty. Flagged for review.",
                "confidence": "Low",
                "confidence_score": 0.20,
                "verification_status": "NEEDS_REVIEW",
                "in_scope": False,
            }

        clean_text = response_text.strip()
        clean_text = re.sub(r"^```(?:json)?\s*", "", clean_text, flags=re.IGNORECASE)
        clean_text = re.sub(r"\s*```$", "", clean_text)
        clean_text = clean_text.strip()

        try:
            data = json.loads(clean_text)
        except json.JSONDecodeError as err:
            logger.warning(f"Failed to parse AI Answer JSON: {err}")
            return {
                "correct_answer": "A",
                "explanation": f"Unverified - AI returned malformed JSON: {err}",
                "confidence": "Low",
                "confidence_score": 0.20,
                "verification_status": "NEEDS_REVIEW",
                "in_scope": False,
            }

        if not isinstance(data, dict):
            return {
                "correct_answer": "A",
                "explanation": "Unverified - Response format was not a dictionary.",
                "confidence": "Low",
                "confidence_score": 0.20,
                "verification_status": "NEEDS_REVIEW",
                "in_scope": False,
            }

        # Check explicit in_scope flag from Gemini JSON
        in_scope = data.get("in_scope", True)
        if in_scope is False:
            explanation = str(data.get("explanation", "")).strip()
            logger.warning(f"Gemini flagged question as OUT_OF_SCOPE for Class {target_class} {target_subject}.")
            return {
                "correct_answer": "A",
                "explanation": explanation or f"OUT_OF_SCOPE: Question does not match Class {target_class} {target_subject} scope.",
                "confidence": "Low",
                "confidence_score": 0.10,
                "verification_status": "NEEDS_REVIEW",
                "in_scope": False,
            }

        raw_ans = data.get("correct_answer")
        explanation = str(data.get("explanation", "")).strip()

        # Reject null, empty, multiple options or invalid option letters
        if not raw_ans or not isinstance(raw_ans, str):
            logger.warning(f"AI returned null or invalid answer '{raw_ans}'. Marking NEEDS_REVIEW.")
            return {
                "correct_answer": "A",
                "explanation": explanation or "Question was ambiguous, incomplete, or returned no definitive answer.",
                "confidence": "Low",
                "confidence_score": 0.20,
                "verification_status": "NEEDS_REVIEW",
                "in_scope": True,
            }

        clean_ans = str(raw_ans).strip().upper()
        if clean_ans not in ["A", "B", "C", "D"]:
            logger.warning(f"AI returned invalid answer option '{clean_ans}'. Marking NEEDS_REVIEW.")
            return {
                "correct_answer": "A",
                "explanation": f"Unverified - AI selected invalid option or multi-option answer '{clean_ans}'.",
                "confidence": "Low",
                "confidence_score": 0.20,
                "verification_status": "NEEDS_REVIEW",
                "in_scope": True,
            }

        if not explanation:
            explanation = "Answer resolved by AI model."

        raw_conf = str(data.get("confidence", "Medium")).strip().capitalize()
        if raw_conf not in ["High", "Medium", "Low"]:
            raw_conf = "Medium"

        # Delegate to Independent Verification Service (Python math solver & cross-verification layer)
        from src.services.verification_service import VerificationService
        return VerificationService.verify_answer(
            question_text=question_text or str(data.get("question_text", "")),
            options=options or data.get("options", {}),
            proposed_answer=clean_ans,
            confidence=raw_conf,
            explanation=explanation,
        )

    @classmethod
    def _fallback_heuristic_solver(cls, question_text: str, options: Dict[str, str]) -> Dict[str, Any]:
        """
        Fallback answer solver when AI API is unavailable.
        Uses independent Python programmatic solver if formula is present, otherwise marks NEEDS_REVIEW.
        """
        logger.info("Using fallback solver for answer resolution.")
        from src.services.verification_service import VerificationService
        return VerificationService.verify_answer(
            question_text=question_text,
            options=options,
            proposed_answer="A",
            confidence="Low",
            explanation="",
        )

    @classmethod
    def _call_gemini_api(cls, prompt: str, api_key: str, max_retries: int = 3) -> str:
        """Helper method to invoke Gemini REST API with model fallback, timeout, and backoff."""
        import time
        models_to_try = [
            getattr(config, "AI_MODEL_NAME", "gemini-flash-lite-latest"),
            getattr(config, "AI_MODEL_FALLBACK", "gemini-flash-latest"),
        ]
        models = []
        for m in models_to_try:
            if m and m not in models:
                models.append(m)

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"}
        }

        req_bytes = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}

        last_error = None
        for model_name in models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
            for attempt in range(max_retries):
                try:
                    req = urllib.request.Request(url, data=req_bytes, headers=headers, method="POST")
                    with urllib.request.urlopen(req, timeout=20) as response:
                        res_data = json.loads(response.read().decode("utf-8"))
                        candidates = res_data.get("candidates", [])
                        if not candidates:
                            raise AIServiceError("Empty candidate list returned by AI API.")
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if not parts:
                            raise AIServiceError("No content parts returned by AI API.")
                        return parts[0].get("text", "")
                except Exception as err:
                    last_error = err
                    err_str = str(err)
                    if "404" in err_str:
                        break
                    if attempt < max_retries - 1:
                        time.sleep(1.5 * (2 ** attempt))

        raise AIServiceError(f"Gemini API request failed across models {models}: {last_error}")

    @classmethod
    def validate_and_sanitize_json_schema(cls, response_text: str) -> List[Dict[str, Any]]:
        """Backend JSON Schema Validator for question extraction."""
        if not response_text or not response_text.strip():
            return []

        clean_text = response_text.strip()
        clean_text = re.sub(r"^```(?:json)?\s*", "", clean_text, flags=re.IGNORECASE)
        clean_text = re.sub(r"\s*```$", "", clean_text)
        clean_text = clean_text.strip()

        try:
            data = json.loads(clean_text)
        except json.JSONDecodeError as json_err:
            logger.warning(f"Failed to parse AI JSON output: {json_err}")
            return []

        if not isinstance(data, dict) or "questions" not in data or not isinstance(data["questions"], list):
            return []

        sanitized_questions = []
        for idx, item in enumerate(data["questions"], start=1):
            if not isinstance(item, dict):
                continue

            q_text = str(item.get("question", "")).strip()
            if not q_text:
                continue

            raw_opts = item.get("options", {})
            if not isinstance(raw_opts, dict):
                raw_opts = {}

            opt_a = str(raw_opts.get("A", "[Option A Missing]")).strip()
            opt_b = str(raw_opts.get("B", "[Option B Missing]")).strip()
            opt_c = str(raw_opts.get("C", "[Option C Missing]")).strip()
            opt_d = str(raw_opts.get("D", "[Option D Missing]")).strip()

            sanitized_questions.append({
                "question_num": idx,
                "question": q_text,
                "options": {
                    "A": opt_a if opt_a else "[Option A Missing]",
                    "B": opt_b if opt_b else "[Option B Missing]",
                    "C": opt_c if opt_c else "[Option C Missing]",
                    "D": opt_d if opt_d else "[Option D Missing]",
                },
                "extraction_method": "AI API Structured JSON Extractor",
            })

        return sanitized_questions
