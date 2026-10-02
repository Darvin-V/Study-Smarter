"""
Study Smarter - PDF Processing Service Module
Handles PDF validation, file saving, raw text extraction via pypdf,
and regex-based MCQ question detection.
"""

import re
import time
import io
from pathlib import Path
from typing import List, Dict, Any, Union
import pypdf
from src.config import config
from src.logger import logger
from src.utils.exceptions import PDFProcessingError

# Define uploads directory
UPLOADS_DIR = Path(config.BASE_DIR) / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


class PDFService:
    """Service for handling PDF file uploads, text extraction, and regex MCQ parsing."""

    @staticmethod
    def validate_pdf_file(uploaded_file: Any, max_mb: float = 10.0) -> Dict[str, Any]:
        """
        Validates uploaded file type, extension, and file size.
        
        :param uploaded_file: Streamlit UploadedFile object or file object
        :param max_mb: Maximum allowed file size in megabytes
        """
        if uploaded_file is None:
            return {"valid": False, "message": "No file uploaded.", "size_mb": 0.0}

        filename = getattr(uploaded_file, "name", "file.pdf")
        if not filename.lower().endswith(".pdf"):
            return {"valid": False, "message": f"Invalid file type for '{filename}'. Only PDF files (.pdf) are allowed.", "size_mb": 0.0}

        # Calculate file size
        size_bytes = getattr(uploaded_file, "size", None)
        if size_bytes is None:
            if hasattr(uploaded_file, "seek"):
                try:
                    uploaded_file.seek(0)
                except Exception:
                    pass
            file_bytes = uploaded_file.getvalue() if hasattr(uploaded_file, "getvalue") else uploaded_file.read()
            if hasattr(uploaded_file, "seek"):
                try:
                    uploaded_file.seek(0)
                except Exception:
                    pass
            size_bytes = len(file_bytes)
        size_mb = round(size_bytes / (1024 * 1024), 2)

        if size_bytes == 0:
            return {"valid": False, "message": "The uploaded PDF file is empty (0 bytes).", "size_mb": 0.0}

        if size_mb > max_mb:
            return {"valid": False, "message": f"File size ({size_mb} MB) exceeds maximum limit of {max_mb} MB.", "size_mb": size_mb}

        return {"valid": True, "message": "PDF file format and size validated successfully.", "size_mb": size_mb}

    @staticmethod
    def save_uploaded_pdf(uploaded_file: Any) -> Path:
        """
        Safely saves an uploaded file stream to the uploads/ directory with a sanitized filename.
        """
        orig_name = getattr(uploaded_file, "name", "uploaded.pdf")
        clean_name = re.sub(r"[^\w\.-]", "_", orig_name)
        timestamp = int(time.time())
        dest_path = UPLOADS_DIR / f"{timestamp}_{clean_name}"

        if hasattr(uploaded_file, "seek"):
            try:
                uploaded_file.seek(0)
            except Exception:
                pass
        file_bytes = uploaded_file.getvalue() if hasattr(uploaded_file, "getvalue") else uploaded_file.read()
        if hasattr(uploaded_file, "seek"):
            try:
                uploaded_file.seek(0)
            except Exception:
                pass
        with open(dest_path, "wb") as f:
            f.write(file_bytes)

        logger.info(f"Safely saved uploaded PDF to {dest_path}")
        return dest_path

    @staticmethod
    def extract_text_from_pdf(pdf_source: Union[str, Path, bytes, Any]) -> str:
        """
        Extracts raw text content from a PDF file path or byte stream using pypdf.
        Handles empty or corrupted PDFs gracefully.
        """
        try:
            if isinstance(pdf_source, (str, Path)):
                reader = pypdf.PdfReader(str(pdf_source))
            elif isinstance(pdf_source, bytes):
                reader = pypdf.PdfReader(io.BytesIO(pdf_source))
            elif hasattr(pdf_source, "getvalue"):
                reader = pypdf.PdfReader(io.BytesIO(pdf_source.getvalue()))
            else:
                reader = pypdf.PdfReader(pdf_source)

            if len(reader.pages) == 0:
                raise PDFProcessingError("The provided PDF file contains 0 pages.")

            extracted_text = []
            for idx, page in enumerate(reader.pages, start=1):
                page_text = page.extract_text()
                if page_text:
                    extracted_text.append(page_text)

            full_text = "\n".join(extracted_text).strip()
            if not full_text:
                logger.warning("PDF text extraction produced empty text (scanned image or unreadable layout).")
                return ""

            logger.info(f"Extracted {len(full_text)} characters across {len(reader.pages)} pages.")
            return full_text

        except pypdf.errors.PdfReadError as err:
            logger.error(f"PyPDF Read Error: {err}")
            raise PDFProcessingError(f"Corrupted or invalid PDF file: {err}") from err
        except Exception as err:
            logger.error(f"Unexpected PDF extraction error: {err}")
            raise PDFProcessingError(f"Failed to process PDF: {err}") from err

    @staticmethod
    def parse_mcqs_regex(raw_text: str) -> List[Dict[str, Any]]:
        """
        Parses raw extracted text into structured MCQ dictionaries using regex.
        Detects question headers (e.g. Q1., 1., Question 1:) and options (A., (A), A)).
        Preserves question numbering and flags missing options.
        """
        if not raw_text or not raw_text.strip():
            return []

        # Normalize Windows newlines (\r\n -> \n)
        raw_text = raw_text.replace("\r\n", "\n").strip()

        # Regex pattern for splitting questions at line start (MULTILINE mode)
        # Matches: Q1., Question 1:, Q.1, 1., 1)
        q_pattern = r"(?m)^\s*(?:Q(?:uestion)?[\.\s]*)?\d+[\.\:\)]?\s+"
        
        matches = list(re.finditer(q_pattern, raw_text, re.IGNORECASE))
        if not matches:
            # Fallback: try splitting by double newlines
            blocks = [b.strip() for b in raw_text.split("\n\n") if b.strip()]
        else:
            blocks = []
            for i in range(len(matches)):
                start = matches[i].start()
                end = matches[i + 1].start() if i + 1 < len(matches) else len(raw_text)
                blocks.append(raw_text[start:end].strip())

        parsed_questions = []
        for idx, block in enumerate(blocks, start=1):
            cleaned_block = block.strip()
            if not cleaned_block:
                continue

            # Split block by option identifiers: A., (A), A), [A]
            option_pattern = r"(?i)(?:\n|^|\s)(?:\(|\[)?\s*([A-D])\s*(?:\)|\]|\.|\:)\s*"
            parts = re.split(option_pattern, cleaned_block)

            # parts[0] is Question header/text
            q_text = parts[0].strip()
            # Remove leading question numbering like "Q1.", "1.", ". "
            q_text_clean = re.sub(r"^(?:Q(?:uestion)?)?[\.\s\:\d\-\)]*", "", q_text, flags=re.IGNORECASE).strip()

            options_found = {}
            for i in range(1, len(parts) - 1, 2):
                opt_letter = parts[i].strip().upper()
                opt_val = parts[i + 1].strip()
                # Clean newlines and extra spaces inside option string
                opt_val_clean = " ".join(opt_val.split())
                if opt_letter in ["A", "B", "C", "D"]:
                    options_found[opt_letter] = opt_val_clean

            # Ensure all options A, B, C, D exist (fill missing with fallback)
            option_a = options_found.get("A", "[Option A Missing]")
            option_b = options_found.get("B", "[Option B Missing]")
            option_c = options_found.get("C", "[Option C Missing]")
            option_d = options_found.get("D", "[Option D Missing]")

            if q_text_clean and len(options_found) >= 2:
                parsed_questions.append({
                    "question_num": idx,
                    "question": q_text_clean,
                    "options": {
                        "A": option_a,
                        "B": option_b,
                        "C": option_c,
                        "D": option_d,
                    },
                    "extraction_method": "Regex Pattern Extractor",
                })

        logger.info(f"Regex MCQ parser extracted {len(parsed_questions)} questions.")
        return parsed_questions
