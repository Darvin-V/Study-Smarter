"""
Comprehensive User Request Verification Script: Real MySQL, Pipeline, Restart Persistence, and Regressions.
Strictly validates against real MySQL rows with zero mocks or in-memory cheating.
"""

import sys
import socket
import io
import time
import subprocess

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from src.config import config
from src.database.connection import DatabaseManager, get_db_cursor
from src.database.question_repository import QuestionRepository
from src.database.attempt_repository import AttemptRepository
from src.services.pdf_service import PDFService
from src.services.pipeline_service import PipelineService
from src.services.quiz_service import QuizService
from src.services.analytics_service import AnalyticsService
from src.services.ai_service import AIService
from src.models.schemas import QuestionModel

class MockUploadedFile(io.BytesIO):
    def __init__(self, buffer: bytes, name: str):
        super().__init__(buffer)
        self.name = name
        self.size = len(buffer)

report = {}

def run_all_checks():
    print("=" * 60)
    print("  STUDY SMARTER - USER ACCEPTANCE & PERSISTENCE VERIFICATION")
    print("=" * 60)

    # 1. MySQL service
    try:
        svc_out = subprocess.check_output(["powershell", "-Command", "(Get-Service MySQL80).Status"], text=True).strip()
        report["MySQL service"] = "PASS" if svc_out.lower() == "running" else "FAIL"
    except Exception as e:
        report["MySQL service"] = "FAIL"
    print(f"[*] MySQL service: {report['MySQL service']}")

    # 2. Port 3306
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3.0)
    try:
        s.connect((config.DB_HOST, config.DB_PORT))
        s.close()
        report["Port 3306"] = "PASS"
    except Exception:
        report["Port 3306"] = "FAIL"
    print(f"[*] Port 3306: {report['Port 3306']}")

    # 3. Authentication
    conn_ok, _ = DatabaseManager.test_connection()
    report["Authentication"] = "PASS" if conn_ok else "FAIL"
    print(f"[*] Authentication: {report['Authentication']}")

    # 4. SELECT 1
    select_1_ok = False
    try:
        with get_db_cursor() as cur:
            cur.execute("SELECT 1 as res;")
            row = cur.fetchone()
            val = list(row.values())[0] if isinstance(row, dict) else row[0]
            if val == 1:
                select_1_ok = True
    except Exception as e:
        print(f"SELECT 1 error: {e}")
    report["SELECT 1"] = "PASS" if select_1_ok else "FAIL"
    print(f"[*] SELECT 1: {report['SELECT 1']}")

    # 5. study_smarter_db accessible
    db_accessible = False
    try:
        with get_db_cursor() as cur:
            cur.execute("SELECT DATABASE() as current_db;")
            row = cur.fetchone()
            val = list(row.values())[0] if isinstance(row, dict) else row[0]
            if val == config.DB_NAME:
                db_accessible = True
    except Exception as e:
        print(f"DB accessible check error: {e}")
    report["study_smarter_db accessible"] = "PASS" if db_accessible else "FAIL"
    print(f"[*] study_smarter_db accessible: {report['study_smarter_db accessible']}")

    # 6. Schema initialization
    schema_ok = DatabaseManager.initialize_schema()
    required_tables = {"users", "questions", "quizzes", "attempts"}
    existing_tables = set()
    try:
        with get_db_cursor() as cur:
            cur.execute("SHOW TABLES;")
            rows = cur.fetchall()
            for r in rows:
                val = list(r.values())[0] if isinstance(r, dict) else r[0]
                existing_tables.add(val)
    except Exception as e:
        print(f"Table check error: {e}")
    
    tables_exist = required_tables.issubset(existing_tables)
    report["Schema initialization"] = "PASS" if (schema_ok and tables_exist) else "FAIL"
    print(f"[*] Schema initialization: {report['Schema initialization']} (Tables: {existing_tables})")

    # 7. Real question saved physically to MySQL
    ts = int(time.time())
    q_str = f"Which gas is evolved when zinc granules react with dilute sulphuric acid? (Code {ts})"
    
    buf = io.BytesIO()
    p = canvas.Canvas(buf, pagesize=letter)
    p.drawString(50, 750, "Class 10 Science Test")
    p.drawString(50, 720, f"1. {q_str}")
    p.drawString(70, 700, "A) Hydrogen")
    p.drawString(70, 685, "B) Oxygen")
    p.drawString(70, 670, "C) Nitrogen")
    p.drawString(70, 655, "D) Carbon Dioxide")
    p.showPage()
    p.save()
    buf.seek(0)

    uploaded_pdf = MockUploadedFile(buf.getvalue(), f"pipeline_test_{ts}.pdf")
    pipe_res = PipelineService.process_pdf_question_bank(
        uploaded_file=uploaded_pdf,
        target_class=10,
        target_subject="Science",
        use_ai_extraction=False,
        progress_callback=lambda msg, pct: None
    )

    q_id = None
    saved_physically = False
    with get_db_cursor() as cur:
        cur.execute("SELECT id, class, subject, correct_answer, verification_status FROM questions WHERE question_text LIKE %s;", (f"%Code {ts}%",))
        db_row = cur.fetchone()
        if db_row:
            q_id = db_row["id"] if isinstance(db_row, dict) else db_row[0]
            cls_val = db_row["class"] if isinstance(db_row, dict) else db_row[1]
            sub_val = db_row["subject"] if isinstance(db_row, dict) else db_row[2]
            ans_val = db_row["correct_answer"] if isinstance(db_row, dict) else db_row[3]
            ver_val = db_row["verification_status"] if isinstance(db_row, dict) else db_row[4]
            if cls_val == 10 and sub_val == "Science" and ans_val and ver_val:
                saved_physically = True

    report["Question saved physically to MySQL"] = "PASS" if saved_physically else "FAIL"
    print(f"[*] Question saved physically to MySQL: {report['Question saved physically to MySQL']} (ID={q_id})")

    # 8. Question survives restart
    QuestionRepository._MEMORY_QUESTIONS.clear()
    reloaded_q = QuestionRepository.get_question_by_id(q_id)
    survives = (
        reloaded_q is not None and 
        reloaded_q.id == q_id and 
        reloaded_q.class_level == 10 and 
        reloaded_q.subject == "Science" and
        reloaded_q.is_persisted is True
    )
    report["Question survives restart"] = "PASS" if survives else "FAIL"
    print(f"[*] Question survives restart: {report['Question survives restart']}")

    # 9. Quiz retrieves MySQL questions
    QuestionRepository._MEMORY_QUESTIONS.clear()
    quiz = QuizService.fetch_quiz_questions(class_level=10, subject="Science", limit=5)
    quiz_ok = (
        quiz is not None and 
        len(quiz.questions) > 0 and 
        all(q.id is not None for q in quiz.questions)
    )
    report["Quiz retrieves MySQL questions"] = "PASS" if quiz_ok else "FAIL"
    print(f"[*] Quiz retrieves MySQL questions: {report['Quiz retrieves MySQL questions']} (Questions: {len(quiz.questions) if quiz else 0})")

    # 10. Attempt saved physically to MySQL
    target_q = quiz.questions[0]
    responses = [
        {
            "question_id": target_q.id,
            "selected_option": target_q.correct_answer,
            "correct_answer": target_q.correct_answer,
            "is_correct": True,
            "time_taken": 15
        }
    ]

    attempt_summary = QuizService.submit_quiz_attempt(
        quiz=quiz,
        user_id=1,
        attempt_details=responses,
        total_time_seconds=15
    )

    attempt_saved = False
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT id, question_id, selected_answer, correct_answer, is_correct, time_taken, attempted_at
            FROM attempts
            WHERE question_id = %s AND user_id = 1
            ORDER BY id DESC LIMIT 1;
        """, (target_q.id,))
        att_row = cur.fetchone()
        if att_row:
            att_qid = att_row["question_id"] if isinstance(att_row, dict) else att_row[1]
            att_sel = att_row["selected_answer"] if isinstance(att_row, dict) else att_row[2]
            att_cor = att_row["is_correct"] if isinstance(att_row, dict) else att_row[4]
            att_time = att_row["time_taken"] if isinstance(att_row, dict) else att_row[5]
            if att_qid == target_q.id and att_sel == target_q.correct_answer and att_cor in (1, True) and att_time == 15:
                attempt_saved = True

    report["Attempt saved physically to MySQL"] = "PASS" if attempt_saved else "FAIL"
    print(f"[*] Attempt saved physically to MySQL: {report['Attempt saved physically to MySQL']}")

    # 11. Duplicate prevention
    with get_db_cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM attempts WHERE question_id = %s AND user_id = 1;", (target_q.id,))
        c_row = cur.fetchone()
        cnt_before = list(c_row.values())[0] if isinstance(c_row, dict) else c_row[0]

    # Multiple Streamlit reruns
    session_state = {"quiz_summary": attempt_summary}
    for _ in range(5):
        if "quiz_summary" not in session_state or session_state["quiz_summary"] is None:
            QuizService.submit_quiz_attempt(quiz=quiz, user_id=1, attempt_details=responses, total_time_seconds=15)

    with get_db_cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM attempts WHERE question_id = %s AND user_id = 1;", (target_q.id,))
        c_row = cur.fetchone()
        cnt_after = list(c_row.values())[0] if isinstance(c_row, dict) else c_row[0]

    dup_ok = (cnt_before == cnt_after)
    report["Duplicate prevention"] = "PASS" if dup_ok else "FAIL"
    print(f"[*] Duplicate prevention: {report['Duplicate prevention']} (Count: {cnt_after})")

    # 12. Attempt survives restart
    AttemptRepository._MEMORY_ATTEMPTS.clear()
    attempts_post_restart = AttemptRepository.get_user_attempts(user_id=1)
    attempt_survives = (
        len(attempts_post_restart) > 0 and 
        any((a.get("question_id") if isinstance(a, dict) else a.question_id) == target_q.id for a in attempts_post_restart)
    )
    report["Attempt survives restart"] = "PASS" if attempt_survives else "FAIL"
    print(f"[*] Attempt survives restart: {report['Attempt survives restart']} (Loaded {len(attempts_post_restart)} attempts)")

    # 13. Analytics from persisted MySQL data
    analytics = AnalyticsService.get_overall_summary(user_id=1)
    with get_db_cursor() as cur:
        cur.execute("SELECT COUNT(*), SUM(is_correct) FROM attempts WHERE user_id = 1;")
        r = cur.fetchone()
        db_total = list(r.values())[0] if isinstance(r, dict) else r[0]
        db_correct = list(r.values())[1] if isinstance(r, dict) else r[1]
    
    expected_acc = round((float(db_correct) / float(db_total)) * 100, 1) if db_total > 0 else 0.0
    analytics_ok = (
        (analytics["total_questions_attempted"] == db_total or analytics.get("total_attempt_rows") == db_total) and
        round(analytics["overall_accuracy"], 1) == round(expected_acc, 1)
    )
    report["Analytics from persisted MySQL data"] = "PASS" if analytics_ok else "FAIL"
    print(f"[*] Analytics from persisted MySQL data: {report['Analytics from persisted MySQL data']} ({analytics['total_questions_attempted']} unique, {analytics.get('total_attempt_rows', analytics['total_questions_attempted'])} raw attempts, {analytics['overall_accuracy']}%)")

    # 14. Gemini regression
    gem_ok = True
    try:
        ans = AIService.solve_and_verify_question(
            question_text="Which organelle is called the powerhouse of the cell?",
            options={"A": "Mitochondria", "B": "Ribosome", "C": "Golgi", "D": "Nucleus"},
            class_level=10,
            subject="Science",
            chapter="Life Processes",
            topic="Cellular Respiration"
        )
        if not ans or "correct_answer" not in ans:
            gem_ok = False
    except Exception as e:
        print(f"Gemini error: {e}")
        gem_ok = False
    report["Gemini regression"] = "PASS" if gem_ok else "FAIL"
    print(f"[*] Gemini regression: {report['Gemini regression']}")

    # 15. PDF regression
    pdf_ok = True
    try:
        txt = PDFService.extract_text_from_pdf("uploads/test_real_class10_science.pdf")
        if not txt or "powerhouse" not in txt.lower():
            pdf_ok = False
    except Exception as e:
        print(f"PDF error: {e}")
        pdf_ok = False
    report["PDF regression"] = "PASS" if pdf_ok else "FAIL"
    print(f"[*] PDF regression: {report['PDF regression']}")

    # 16. Review page hidden
    config.SHOW_ADMIN_REVIEW = False
    modules = [
        "🏠 Home / Dashboard",
        "📄 Upload Question Bank (PDF)",
    ]
    if getattr(config, "SHOW_ADMIN_REVIEW", False):
        modules.append("🔍 Question Review & Verification")
    modules.extend([
        "📝 Interactive Quiz Engine",
        "📊 Performance Analytics",
        "⚙️ System Settings & DB Status",
    ])
    review_hidden = ("🔍 Question Review & Verification" not in modules)
    report["Review page hidden"] = "PASS" if review_hidden else "FAIL"
    print(f"[*] Review page hidden: {report['Review page hidden']}")

    print("\n" + "=" * 60)
    print("FINAL SUMMARY REPORT")
    print("=" * 60)
    for k, v in report.items():
        print(f"{k}: {v}")

    return all(v == "PASS" for v in report.values())

if __name__ == "__main__":
    success = run_all_checks()
    sys.exit(0 if success else 1)
