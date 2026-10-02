"""
Study Smarter - Comprehensive Database Backfill for Case-Based Questions
Attaches the corresponding case study / passage paragraphs to existing
questions in Bank 1 (Chemistry XII) and Bank 2 (Mathematics XII).
Idempotent and safe to run multiple times.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')
import pypdf
import re
from typing import List, Dict, Any, Optional
from src.logger import logger
from src.database.connection import get_db_cursor
from src.services.case_study_service import CaseStudyService
from src.services.pdf_service import PDFService


MANUAL_CASE_MAPPINGS = {
    # Bank 2: Side-by-side / column layout case studies
    "plant": (
        "The relation between the height of the plant (y in cm) with respect to exposure to sunlight "
        "is governed by the following equation: y = 4x - (1/2)x² where x is the number of days exposed to sunlight."
    ),
    "profit": (
        "P(x) = -5x² + 125x + 37500 is the total profit function of a company, "
        "where x is the production of the company."
    ),
    "potter": (
        "A potter made a mud vessel, where the shape of the pot is based on "
        "f(x) = |x – 3| + |x – 2|, where f(x) represents the height of the pot."
    ),
    "stick": (
        "The shape of a toy is given as f(x) = 6(2x⁴ – x²). To make the toy beautiful, "
        "2 sticks which are perpendicular to each other were placed at a point (2, 3), above the toy."
    ),
    # Bank 1: Passage IV and VI
    "reduction": (
        "Reduction of carboxylic acids and their derivatives plays an important role in organic "
        "synthesis, in both laboratory and industrial processes. Traditionally, the reduction is "
        "performed using stoichiometric amounts of hydride reagents, generating stoichiometric "
        "amounts of waste. A much more attractive, atom-economical approach is a catalytic reaction "
        "using H2; however, hydrogenation of carboxylic acid derivatives under mild conditions is a "
        "very challenging task."
    ),
    "transition": (
        "Within the 3d series, manganese exhibits oxidation states in aqueous solution from +2 to +7, "
        "ranging from basic MnO to acidic Mn2O7. Transition metals are characterized by their "
        "partially filled d-orbitals, ability to form coordination complexes, and multiple oxidation states."
    ),
}


def find_best_case_match(db_row: Dict[str, Any], parsed_questions: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Finds matching parsed case-based question using text and option heuristics."""
    db_text = ' '.join(db_row['question_text'].split()).lower()
    db_opt_a = ' '.join((db_row.get('option_a') or '').split()).lower()

    for pq in parsed_questions:
        if not pq.get("is_case_based") or not pq.get("passage_text"):
            continue

        raw_sub = ' '.join(pq.get("raw_question", "").split()).lower()
        pq_opt_a = ' '.join(pq.get("options", {}).get("A", "").split()).lower()

        # 1. High-confidence prefix match on question text
        if len(raw_sub) >= 20 and len(db_text) >= 20:
            if raw_sub[:30] in db_text or db_text[:30] in raw_sub:
                return pq

        # 2. Match with option A correlation
        if len(db_opt_a) > 5 and len(pq_opt_a) > 5:
            if (db_opt_a[:20] in pq_opt_a or pq_opt_a[:20] in db_opt_a):
                if (raw_sub[:15] in db_text or db_text[:15] in raw_sub):
                    return pq

        # 3. Substring presence
        if len(raw_sub) >= 25 and raw_sub in db_text:
            return pq

    return None


def get_fallback_passage(db_text: str) -> Optional[str]:
    """Matches known specific case studies that had irregular PDF multi-column formatting."""
    lower = db_text.lower()
    if any(k in lower for k in ['plant', 'sunlight', 'exposed to the sunlight']):
        return MANUAL_CASE_MAPPINGS['plant']
    if any(k in lower for k in ['profit', 'production', '38250', '38,28,125']):
        return MANUAL_CASE_MAPPINGS['profit']
    if any(k in lower for k in ['potter', 'mud vessel', 'height in terms of x', 'slope vary with x']):
        return MANUAL_CASE_MAPPINGS['potter']
    if any(k in lower for k in ['stick', 'critical point if it passes through (2,3)', 'shape of a toy', 'second order derivative of the function at x = 5']):
        return MANUAL_CASE_MAPPINGS['stick']
    if any(k in lower for k in ['reactions can occur at different speeds', 'catalyst 3', 'reduction of carboxylic']):
        return MANUAL_CASE_MAPPINGS['reduction']
    if any(k in lower for k in ['willingness to form multiple bonds', 'transition metal', 'manganese']):
        return MANUAL_CASE_MAPPINGS['transition']
    return None


def repair_bank(bank_id: int, pdf_path: str, label: str):
    logger.info(f"Starting case-based backfill for Bank {bank_id} ({label}) using {pdf_path}...")
    print(f"\n==========================================")
    print(f"Backfilling Bank {bank_id} ({label})")
    print(f"==========================================")

    # 1. Extract and parse PDF with CaseStudyService
    raw_text = PDFService.extract_text_from_pdf(pdf_path)
    parsed = CaseStudyService.parse_mcqs_with_cases(raw_text)
    case_parsed = [q for q in parsed if q.get("is_case_based")]
    print(f"Parsed {len(parsed)} questions from PDF ({len(case_parsed)} case-based).")

    # 2. Fetch existing DB questions
    with get_db_cursor() as cursor:
        cursor.execute("SELECT id, question_text, option_a FROM questions WHERE bank_id = %s ORDER BY id", (bank_id,))
        db_rows = cursor.fetchall()

    print(f"Found {len(db_rows)} questions in database for Bank {bank_id}.")
    updated_count = 0
    already_done_count = 0

    with get_db_cursor() as update_cursor:
        for r in db_rows:
            q_id = r["id"]
            current_text = r["question_text"]

            # Check if already has passage attached
            existing_passage, clean_q = CaseStudyService.split_passage_and_question(current_text)
            if existing_passage:
                already_done_count += 1
                continue

            # First try automated match from parsed PDF
            match = find_best_case_match(r, parsed)
            if match and match.get("passage_text"):
                passage = match["passage_text"]
                clean_sub_q = match.get("raw_question") or clean_q or current_text
                new_formatted_text = CaseStudyService.format_case_question(passage, clean_sub_q)

                update_cursor.execute(
                    "UPDATE questions SET question_text = %s WHERE id = %s",
                    (new_formatted_text, q_id)
                )
                updated_count += 1
            else:
                # Try fallback for side-by-side layout case studies
                fb_passage = get_fallback_passage(current_text)
                if fb_passage:
                    clean_sub_q = clean_q or current_text
                    # Clean any leading headers/artifacts from clean_sub_q
                    clean_sub_q = re.sub(r'^(?:\d+[\.\:\)]\s*)+', '', clean_sub_q).strip()
                    new_formatted_text = CaseStudyService.format_case_question(fb_passage, clean_sub_q)
                    update_cursor.execute(
                        "UPDATE questions SET question_text = %s WHERE id = %s",
                        (new_formatted_text, q_id)
                    )
                    updated_count += 1

    print(f"Results for Bank {bank_id} ({label}):")
    print(f" - Updated with passage: {updated_count}")
    print(f" - Already had passage:  {already_done_count}")
    print(f" - Total now formatted:  {updated_count + already_done_count} / {len(db_rows)}")


def main():
    repair_bank(1, 'uploads/1790913742_ChemistryXII.pdf', 'Chemistry XII')
    repair_bank(2, 'uploads/1790918960_MathematicsXII.pdf', 'Mathematics XII')
    print("\n[SUCCESS] Case-based question backfill complete!")


if __name__ == "__main__":
    main()
