"""
Study Smarter - End-to-End Pipeline Service Module
Connects all individual components into one unified, fault-tolerant processing pipeline:

UPLOAD PDF → VALIDATE PDF → EXTRACT QUESTIONS → STRUCTURE QUESTIONS
  → CLASSIFY TOPIC → DETERMINE & VERIFY ANSWERS → PERSIST MYSQL → PRACTICE READY

Works with any question bank — no NCERT class/subject restriction.
Handles question-level failures gracefully without stopping the entire PDF processing.
"""

from typing import Dict, Any, List, Optional, Callable
from src.config import config
from src.logger import logger
from src.models.schemas import QuestionModel
from src.services.pdf_service import PDFService
from src.services.case_study_service import CaseStudyService
from src.services.ai_service import AIService
from src.database.question_repository import QuestionRepository


class PipelineService:
    """Orchestrator Service for End-to-End PDF Question Processing Pipeline."""

    @classmethod
    def process_pdf_question_bank(
        cls,
        uploaded_file: Any,
        bank_id: Optional[int] = None,
        bank_name: str = "General",
        target_subject: str = "General",
        use_ai_extraction: bool = False,
        progress_callback: Optional[Callable[[str, int], None]] = None,
        # Legacy parameters kept for backward compatibility
        target_class: int = 0,
    ) -> Dict[str, Any]:
        """
        Executes complete end-to-end PDF processing pipeline:
        1. Validate PDF
        2. Extract text & structure MCQs
        3. Classify Topic & Difficulty (any subject, not restricted to NCERT)
        4. Determine & Verify Answers via Gemini
        5. Separate Verified vs Needs Review questions
        6. Persist to MySQL database table 'questions' with bank_id
        """
        def update_step(step_msg: str, step_pct: int):
            logger.info(f"Pipeline Step ({step_pct}%): {step_msg}")
            if progress_callback:
                progress_callback(step_msg, step_pct)

        # Handle raw bytes or ensure seekable position
        if isinstance(uploaded_file, bytes):
            class _BytesUploadedFile:
                def __init__(self, b: bytes, name: str = "uploaded_bank.pdf"):
                    self._b = b
                    self.name = name
                    self.size = len(b)
                def read(self, *args):
                    return self._b
                def getvalue(self):
                    return self._b
                def seek(self, *args):
                    pass
            uploaded_file = _BytesUploadedFile(uploaded_file)
        elif hasattr(uploaded_file, "seek"):
            try:
                uploaded_file.seek(0)
            except Exception:
                pass

        # Step 1: Validate PDF File
        update_step("Uploading & Validating PDF...", 10)
        val_res = PDFService.validate_pdf_file(uploaded_file, max_mb=10.0)
        if not val_res["valid"]:
            return {
                "success": False,
                "message": val_res["message"],
                "total_extracted": 0,
                "verified_count": 0,
                "review_count": 0,
                "saved_count": 0,
                "questions_saved": 0,
                "needs_review": 0,
                "bank_id": bank_id,
                "bank_name": bank_name,
                "verified_questions": [],
                "needs_review_questions": [],
            }

        # Save PDF file safely
        saved_path = PDFService.save_uploaded_pdf(uploaded_file)
        orig_filename = getattr(uploaded_file, "name", "uploaded_bank.pdf")

        # Step 2: Extract Raw Text from PDF
        update_step("Extracting text from PDF...", 25)
        raw_text = PDFService.extract_text_from_pdf(saved_path)
        if not raw_text or not raw_text.strip():
            return {
                "success": False,
                "message": "The uploaded PDF produced no readable text. It may be a scanned image or empty PDF.",
                "total_extracted": 0,
                "verified_count": 0,
                "review_count": 0,
                "saved_count": 0,
                "questions_saved": 0,
                "needs_review": 0,
                "bank_id": bank_id,
                "bank_name": bank_name,
                "verified_questions": [],
                "needs_review_questions": [],
            }

        # Step 3: Extract & Structure MCQs
        update_step("Structuring MCQs (Questions & Options A-D)...", 40)
        if use_ai_extraction:
            ai_res = AIService.extract_structured_questions(raw_text)
            if ai_res["success"] and ai_res["questions"]:
                extracted_questions = ai_res["questions"]
            else:
                logger.warning("AI extraction failed/empty. Falling back to regex parser.")
                extracted_questions = PDFService.parse_mcqs_regex(raw_text)
        else:
            extracted_questions = CaseStudyService.parse_mcqs_with_cases(raw_text)
            if not extracted_questions:
                logger.info("Regex extraction found 0 MCQs. Attempting AI structured extraction fallback...")
                try:
                    ai_res = AIService.extract_structured_questions(raw_text)
                    if ai_res.get("success") and ai_res.get("questions"):
                        extracted_questions = ai_res["questions"]
                except Exception as ex_ai:
                    logger.warning(f"AI extraction fallback failed: {ex_ai}")

        if not extracted_questions:
            return {
                "success": False,
                "message": "No suitable MCQ questions were found.",
                "total_extracted": 0,
                "verified_count": 0,
                "review_count": 0,
                "saved_count": 0,
                "questions_saved": 0,
                "needs_review": 0,
                "bank_id": bank_id,
                "bank_name": bank_name,
                "verified_questions": [],
                "needs_review_questions": [],
            }

        # Step 4: Batch Solve, Explain & Classify using Gemini
        update_step(f"Generating answers and solutions for '{bank_name}' ({len(extracted_questions)} questions)...", 45)
        solved_questions = AIService.batch_solve_and_classify_questions(
            extracted_questions=extracted_questions,
            class_level=target_class,
            subject=target_subject if target_subject else "General",
            batch_size=getattr(config, "GEMINI_BATCH_SIZE", 10),
            progress_callback=update_step,
        )

        # Step 5: Convert to QuestionModel objects and strictly validate educational solutions
        update_step(f"Saving {len(solved_questions)} questions for '{bank_name}' to database...", 90)
        q_models = []
        verified_list = []
        needs_review_list = []
        py_verified_count = 0
        ai_verified_count = 0

        for q in solved_questions:
            status = q.get("verification_status", "NEEDS_REVIEW")
            explanation = q.get("explanation", "") or ""

            # Strict solution quality validation: reject metadata keywords
            bad_kw = ["low confidence", "unable to determine", "held for review", "flagged for review", "processing error", "unverified"]
            if any(kw in explanation.lower() for kw in bad_kw):
                explanation = ""
                status = "NEEDS_REVIEW"

            q_model = QuestionModel(
                class_level=target_class,
                subject=target_subject if target_subject else "General",
                chapter=q.get("chapter", "General"),
                topic=q.get("topic", "General"),
                question_text=q.get("question", ""),
                option_a=q.get("options", {}).get("A", ""),
                option_b=q.get("options", {}).get("B", ""),
                option_c=q.get("options", {}).get("C", ""),
                option_d=q.get("options", {}).get("D", ""),
                correct_answer=q.get("correct_answer", "A"),
                explanation=explanation,
                difficulty=q.get("difficulty", "Medium"),
                source_pdf=orig_filename,
                answer_confidence=q.get("answer_confidence", 0.90),
                verification_status=status,
                bank_id=bank_id,
                bank_name=bank_name,
            )
            q_models.append(q_model)

            if status == "VERIFIED":
                py_verified_count += 1
                verified_list.append(q_model)
            elif status == "AI_VERIFIED":
                ai_verified_count += 1
                verified_list.append(q_model)
            else:
                needs_review_list.append(q_model)

        # Step 6: Bulk Persist to MySQL in single transaction
        created_ids = QuestionRepository.create_questions_bulk(q_models)
        saved_count = len([q for q in q_models if getattr(q, "is_persisted", False)])

        update_step("Question bank ready!", 100)

        db_persisted = (saved_count > 0)
        if db_persisted:
            persist_msg = f" Successfully saved {saved_count} practice question(s) to '{bank_name}'."
        else:
            persist_msg = " ⚠️ We couldn't save your questions permanently. Please check your storage settings and try again."

        summary_msg = (
            f"Pipeline finished for '{bank_name}': {len(verified_list)} questions published "
            f"({py_verified_count} Verified, {ai_verified_count} AI Verified), "
            f"{len(needs_review_list)} held for review.{persist_msg}"
        )

        return {
            "success": True,
            "message": summary_msg,
            "db_persisted": db_persisted,
            "total_extracted": len(solved_questions),
            "verified_count": len(verified_list),
            "py_verified_count": py_verified_count,
            "ai_verified_count": ai_verified_count,
            "out_of_scope_count": 0,
            "review_count": len(needs_review_list),
            "saved_count": saved_count,
            "verified_questions": verified_list,
            "needs_review_questions": needs_review_list,
            # Aliases for UI callers
            "bank_id": bank_id,
            "bank_name": bank_name,
            "questions_saved": saved_count,
            "needs_review": len(needs_review_list),
            "ready_questions": len(verified_list),
        }

    @classmethod
    def process_pdf_upload(
        cls,
        uploaded_file: Any = None,
        pdf_bytes: Optional[bytes] = None,
        bank_name: str = "General",
        bank_id: Optional[int] = None,
        user_id: int = 1,
        on_progress: Optional[Callable] = None,
        progress_callback: Optional[Callable] = None,
        target_subject: str = "General",
        use_ai_extraction: bool = False,
        target_class: int = 0,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Compatibility wrapper for process_pdf_question_bank.
        Ensures any caller expecting process_pdf_upload executes seamlessly.
        """
        file_obj = uploaded_file if uploaded_file is not None else pdf_bytes

        # If bank_id is not provided, ensure/create bank in question_banks table
        if bank_id is None and bank_name:
            try:
                from src.database.question_repository import QuestionRepository
                source_name = getattr(uploaded_file, "name", "uploaded.pdf") if uploaded_file else "uploaded.pdf"
                bank_id = QuestionRepository.create_question_bank(
                    name=bank_name.strip(),
                    source_pdf=source_name,
                )
            except Exception as b_err:
                logger.warning(f"Could not ensure question bank in process_pdf_upload: {b_err}")

        cb = progress_callback or on_progress
        def _adapted_cb(msg: str, pct: int):
            if cb:
                try:
                    cb(msg, pct)
                except TypeError:
                    try:
                        cb(pct, 100, msg)
                    except Exception:
                        pass

        return cls.process_pdf_question_bank(
            uploaded_file=file_obj,
            bank_id=bank_id,
            bank_name=bank_name,
            target_subject=target_subject,
            use_ai_extraction=use_ai_extraction,
            progress_callback=_adapted_cb if cb else None,
            target_class=target_class,
        )
