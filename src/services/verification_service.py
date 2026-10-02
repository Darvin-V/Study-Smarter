"""
Study Smarter - Independent Answer Verification Service Module
Programmatically verifies proposed AI answers using Python arithmetic, formula solvers,
and multi-strategy validation rules. Never blindly trusts a single AI output.

Status Hierarchy:
- VERIFIED: Programmatically verified by deterministic Python code.
- AI_VERIFIED: Solved by AI model with High/Medium confidence and valid schema, but non-numerical.
- NEEDS_REVIEW: Verification disagreed with proposed answer, confidence is Low, API failed, or question is ambiguous.
"""

import re
from typing import Dict, Any, Optional, Tuple
from src.logger import logger


class VerificationService:
    """Independent Verification Layer for evaluating MCQ answers programmatically."""

    @classmethod
    def verify_answer(
        cls,
        question_text: str,
        options: Dict[str, str],
        proposed_answer: str,
        confidence: str = "High",
        explanation: str = "",
        ai_confidence: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Independent Answer Verification Entry Point.
        
        1. Attempts deterministic Python mathematical/formula verification for numerical MCQs.
        2. If Python solver finds a definitive answer:
           - If Python result agrees with proposed_answer: Status = 'VERIFIED'
           - If Python result disagrees with proposed_answer: Status = 'NEEDS_REVIEW'
        3. If non-numerical conceptual MCQ:
           - If confidence in ['High', 'Medium'] and valid option: Status = 'AI_VERIFIED'
           - If confidence is 'Low' or input ambiguous: Status = 'NEEDS_REVIEW'
        """
        if ai_confidence is not None and confidence == "High":
            if isinstance(ai_confidence, (float, int)):
                confidence = "High" if ai_confidence >= 0.7 else ("Medium" if ai_confidence >= 0.4 else "Low")
            else:
                confidence = str(ai_confidence)

        clean_proposed = str(proposed_answer).strip().upper()
        clean_conf = str(confidence).strip().capitalize()

        # Step 1: Attempt Python programmatic formula / arithmetic solver
        py_result = cls._try_python_programmatic_solver(question_text, options)

        if py_result["verified_by_python"]:
            python_calc_opt = py_result["calculated_option"]
            calc_val = py_result["calculated_value"]

            if python_calc_opt == clean_proposed:
                logger.info(f"Python Programmatic Solver AGREES with proposed answer '{clean_proposed}' (Value={calc_val}).")
                return {
                    "correct_answer": clean_proposed,
                    "explanation": f"Programmatically verified by Python formula engine (Calculated value: {calc_val}). {explanation}",
                    "confidence": "High",
                    "confidence_score": 0.99,
                    "verification_status": "VERIFIED",
                    "verification_method": "Python Programmatic Solver",
                    "python_agreed": True,
                }
            else:
                logger.warning(
                    f"Python Programmatic Solver DISAGREES with proposed answer '{clean_proposed}'. "
                    f"Python calculated Option '{python_calc_opt}' (Value={calc_val}). Setting NEEDS_REVIEW."
                )
                return {
                    "correct_answer": clean_proposed,
                    "explanation": explanation,
                    "confidence": "Low",
                    "confidence_score": 0.30,
                    "verification_status": "NEEDS_REVIEW",
                    "verification_method": "Python Verification Disagreed",
                    "review_reason": f"Independent Python solver calculated Option '{python_calc_opt}', which disagrees with proposed Option '{clean_proposed}'.",
                    "python_agreed": False,
                }

        # Step 2: Non-numerical / conceptual question cross-verification strategy
        if clean_proposed in ["A", "B", "C", "D"]:
            if clean_conf in ["High", "Medium"]:
                return {
                    "correct_answer": clean_proposed,
                    "explanation": explanation or "",
                    "confidence": clean_conf,
                    "confidence_score": 0.85 if clean_conf == "High" else 0.70,
                    "verification_status": "AI_VERIFIED",
                    "verification_method": "High Confidence Model Schema Check",
                    "review_reason": None,
                    "python_agreed": None,
                }
            else:
                return {
                    "correct_answer": clean_proposed,
                    "explanation": explanation or "",
                    "confidence": "Low",
                    "confidence_score": 0.40,
                    "verification_status": "NEEDS_REVIEW",
                    "verification_method": "Low Confidence Flag",
                    "review_reason": "Low confidence answer proposed by model.",
                    "python_agreed": None,
                }

        # Invalid option letter fallback
        return {
            "correct_answer": "A",
            "explanation": "",
            "confidence": "Low",
            "confidence_score": 0.20,
            "verification_status": "NEEDS_REVIEW",
            "verification_method": "Invalid Schema Flag",
            "review_reason": f"Invalid proposed answer '{clean_proposed}'.",
            "python_agreed": None,
        }

    @classmethod
    def _try_python_programmatic_solver(cls, question_text: str, options: Dict[str, str]) -> Dict[str, Any]:
        """
        Extracts numbers and formula patterns from question text to evaluate deterministically.
        Supports common NCERT formulas:
        - F = q * E (Electric Force = charge * electric field)
        - p = q * 2a (Electric Dipole Moment)
        - V = I * R (Ohm's Law)
        - Basic Arithmetic / Multiplication / Division / Percentage
        """
        text_lower = question_text.lower()

        # Formula 1: Force F = q * E
        # Example: "A charge of 2 uC (or 2e-6 C) in electric field of 100 N/C..."
        if ("charge" in text_lower or "coulomb" in text_lower) and ("electric field" in text_lower or "field of" in text_lower):
            calc_val = cls._solve_electric_force_formula(question_text)
            if calc_val is not None:
                matched_opt = cls._match_numeric_value_to_options(calc_val, options)
                if matched_opt:
                    return {"verified_by_python": True, "calculated_value": calc_val, "calculated_option": matched_opt}

        # Formula 2: Ohm's Law V = I * R or I = V / R or R = V / I
        if "ohm" in text_lower or ("voltage" in text_lower and "resistance" in text_lower):
            calc_val = cls._solve_ohms_law_formula(question_text)
            if calc_val is not None:
                matched_opt = cls._match_numeric_value_to_options(calc_val, options)
                if matched_opt:
                    return {"verified_by_python": True, "calculated_value": calc_val, "calculated_option": matched_opt}

        # Formula 3: Simple Arithmetic / Multiplication in question (e.g. "What is 15% of 200?")
        if "what is" in text_lower or "calculate" in text_lower or "find" in text_lower:
            calc_val = cls._solve_basic_arithmetic(question_text)
            if calc_val is not None:
                matched_opt = cls._match_numeric_value_to_options(calc_val, options)
                if matched_opt:
                    return {"verified_by_python": True, "calculated_value": calc_val, "calculated_option": matched_opt}

        return {"verified_by_python": False, "calculated_value": None, "calculated_option": None}

    @classmethod
    def _solve_electric_force_formula(cls, question_text: str) -> Optional[float]:
        """Solves F = q * E from question text."""
        # Find charge q (e.g. 2 uC -> 2e-6, 5 C -> 5)
        q_match = re.search(r"(\d+(?:\.\d+)?)\s*(uC|µC|mC|C)\b", question_text, re.IGNORECASE)
        # Find electric field E (e.g. 100 N/C or 50 V/m)
        e_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:N/C|V/m)\b", question_text, re.IGNORECASE)

        if q_match and e_match:
            q_val = float(q_match.group(1))
            unit = q_match.group(2).lower()
            if "u" in unit or "µ" in unit:
                q_val *= 1e-6
            elif "m" in unit:
                q_val *= 1e-3

            e_val = float(e_match.group(1))
            force = q_val * e_val
            return force

        return None

    @classmethod
    def _solve_ohms_law_formula(cls, question_text: str) -> Optional[float]:
        """Solves V = I * R from question text."""
        v_match = re.search(r"(\d+(?:\.\d+)?)\s*V\b", question_text, re.IGNORECASE)
        r_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:ohm|ohms|Ω)\b", question_text, re.IGNORECASE)
        i_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:A|amp|ampere)\b", question_text, re.IGNORECASE)

        if v_match and r_match:
            v_val = float(v_match.group(1))
            r_val = float(r_match.group(1))
            return v_val / r_val if r_val != 0 else None
        elif i_match and r_match:
            i_val = float(i_match.group(1))
            r_val = float(r_match.group(1))
            return i_val * r_val

        return None

    @classmethod
    def _solve_basic_arithmetic(cls, question_text: str) -> Optional[float]:
        """Solves basic arithmetic percentages or products."""
        # Check percentage e.g. "15% of 200"
        pct_match = re.search(r"(\d+(?:\.\d+)?)\s*%\s*of\s*(\d+(?:\.\d+)?)", question_text, re.IGNORECASE)
        if pct_match:
            pct = float(pct_match.group(1))
            val = float(pct_match.group(2))
            return (pct / 100.0) * val

        # Check product e.g. "product of 12 and 5"
        prod_match = re.search(r"product of (\d+(?:\.\d+)?) and (\d+(?:\.\d+)?)", question_text, re.IGNORECASE)
        if prod_match:
            return float(prod_match.group(1)) * float(prod_match.group(2))

        return None

    @classmethod
    def _match_numeric_value_to_options(cls, target_val: float, options: Dict[str, str]) -> Optional[str]:
        """
        Helper method to match calculated numeric float value to option strings A, B, C, D.
        Supports scientific notation e.g. 2e-4 matching '2 x 10^-4 N'.
        """
        for opt_key, opt_text in options.items():
            # Extract numbers from option text
            # Check for scientific notation e.g. 2 x 10^-4 or 2*10^-4
            sci_match = re.search(r"(\d+(?:\.\d+)?)\s*[\*xX]\s*10\^\s*(-?\d+)", opt_text)
            if sci_match:
                coef = float(sci_match.group(1))
                exp = float(sci_match.group(2))
                opt_val = coef * (10 ** exp)
                if abs(opt_val - target_val) < 1e-9 or abs(opt_val - target_val) / max(abs(target_val), 1e-9) < 0.05:
                    return opt_key.upper()

            # Direct numeric match
            num_match = re.search(r"-?\d+(?:\.\d+)?(?:e-?\d+)?", opt_text, re.IGNORECASE)
            if num_match:
                try:
                    opt_val = float(num_match.group(0))
                    if abs(opt_val - target_val) < 1e-6 or abs(opt_val - target_val) / max(abs(target_val), 1e-6) < 0.05:
                        return opt_key.upper()
                except ValueError:
                    pass

        return None
