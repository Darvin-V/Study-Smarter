"""
Study Smarter v2.0 – Premium Dark UI
Session-state navigation (no sidebar). All backend logic preserved.
Redesigned to match modern SaaS learning-app aesthetic.
"""

import time
import streamlit as st
from src.config import config
from src.logger import logger
from src.database.connection import DatabaseManager, get_db_cursor
from src.database.question_repository import QuestionRepository
from src.services.quiz_service import QuizService
from src.services.analytics_service import AnalyticsService
from src.services.pdf_service import PDFService
from src.services.ai_service import AIService
from src.services.pipeline_service import PipelineService
from src.services.case_study_service import CaseStudyService
from src.database.attempt_repository import AttemptRepository
from src.models.schemas import AttemptModel


# ╔══════════════════════════════════════════════════════════════════════╗
# ║                    MASTER CSS — DESIGN SYSTEM                        ║
# ╚══════════════════════════════════════════════════════════════════════╝

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

/* ── Design Tokens ───────────────────────────────────────────── */
:root {
  --bg:        #070C19;
  --bg-card:   #0D1528;
  --bg-card2:  #111827;
  --border:    rgba(255,255,255,0.07);
  --text:      #F1F5F9;
  --text-sub:  #94A3B8;
  --text-dim:  #64748B;
  --blue:      #5B8BFF;
  --purple:    #A855F7;
  --green:     #10B981;
  --orange:    #F59E0B;
  --pink:      #EC4899;
  --red:       #EF4444;
  --cyan:      #22D3EE;
}

/* ── Base ────────────────────────────────────────────────────── */
html, body, [class*="css"], .stApp {
  font-family: 'Inter', -apple-system, sans-serif !important;
  background-color: var(--bg) !important;
  color: var(--text) !important;
}
h1,h2,h3,h4,h5,h6 { color: var(--text) !important; margin-top: 0; }
p { color: inherit; }
a { color: var(--blue); text-decoration: none; }

/* ── Hide Streamlit Chrome ───────────────────────────────────── */
section[data-testid="stSidebar"]        { display: none !important; }
header[data-testid="stHeader"]          { display: none !important; }
#MainMenu                               { display: none !important; }
footer                                  { display: none !important; }
.stDeployButton                         { display: none !important; }
[data-testid="stDecoration"]            { display: none !important; }
[data-testid="stToolbarActionButton"]   { display: none !important; }
div[data-testid="collapsedControl"]     { display: none !important; }

/* ── Layout ──────────────────────────────────────────────────── */
.main .block-container {
  padding: 0 !important;
  max-width: 100% !important;
}

/* ── Sticky Top Navbar ────────────────────────────────────────── */
div.st-key-ss_navbar_container {
  background: rgba(7, 12, 25, 0.96) !important;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08) !important;
  padding: 10px 48px !important;
  position: sticky !important;
  top: 0 !important;
  z-index: 9999 !important;
  backdrop-filter: blur(16px) !important;
  -webkit-backdrop-filter: blur(16px) !important;
  margin-bottom: 16px !important;
}

div.st-key-ss_navbar_container .stButton > button,
div.st-key-_nb_home button,
div.st-key-_nb_progress button,
div.st-key-_nb_history button {
  background: transparent !important;
  border: 1px solid transparent !important;
  color: #94A3B8 !important;
  font-size: 0.88rem !important;
  font-weight: 600 !important;
  padding: 7px 18px !important;
  border-radius: 8px !important;
  transition: all 0.2s ease !important;
  box-shadow: none !important;
  white-space: nowrap !important;
}

div.st-key-ss_navbar_container .stButton > button:hover,
div.st-key-_nb_home button:hover,
div.st-key-_nb_progress button:hover,
div.st-key-_nb_history button:hover {
  background: rgba(91, 139, 255, 0.12) !important;
  color: #5B8BFF !important;
  border-color: rgba(91, 139, 255, 0.25) !important;
}

/* ── Page wrapper ────────────────────────────────────────────── */
.ss-page {
  max-width: 1180px;
  margin: 0 auto;
  padding: 0 36px 80px;
}

/* ── Gradient text ───────────────────────────────────────────── */
.ss-grad {
  background: linear-gradient(135deg, #5B8BFF, #A855F7);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* ── Primary Buttons ──────────────────────────────────────────── */
button[kind="primary"],
div.st-key-h_scan button,
div.st-key-up_scan_btn button,
div.st-key-up_start_prac button,
div.st-key-qz_start button,
div.st-key-qz_continue_prac button,
div.st-key-mk_prac_again button,
div.st-key-h_empty_scan button {
  background: linear-gradient(135deg, #5B8BFF, #A855F7) !important;
  color: #FFFFFF !important;
  border: none !important;
  border-radius: 12px !important;
  font-weight: 700 !important;
  font-size: 0.95rem !important;
  padding: 12px 24px !important;
  box-shadow: 0 4px 20px rgba(91, 139, 255, 0.35) !important;
  transition: all 0.2s ease !important;
  width: 100% !important;
  cursor: pointer !important;
}
button[kind="primary"]:hover,
div.st-key-h_scan button:hover,
div.st-key-up_scan_btn button:hover,
div.st-key-up_start_prac button:hover,
div.st-key-qz_start button:hover,
div.st-key-qz_continue_prac button:hover,
div.st-key-mk_prac_again button:hover,
div.st-key-h_empty_scan button:hover {
  transform: translateY(-2px) !important;
  box-shadow: 0 8px 28px rgba(91, 139, 255, 0.55) !important;
}

/* ── Secondary Buttons ────────────────────────────────────────── */
button[kind="secondary"],
div.st-key-h_practice button {
  background: rgba(255, 255, 255, 0.04) !important;
  color: #F1F5F9 !important;
  border: 1.5px solid rgba(91, 139, 255, 0.45) !important;
  border-radius: 12px !important;
  font-weight: 700 !important;
  font-size: 0.95rem !important;
  padding: 12px 24px !important;
  transition: all 0.2s ease !important;
  width: 100% !important;
  cursor: pointer !important;
}
button[kind="secondary"]:hover,
div.st-key-h_practice button:hover {
  background: rgba(91, 139, 255, 0.14) !important;
  border-color: #5B8BFF !important;
  box-shadow: 0 0 20px rgba(91, 139, 255, 0.3) !important;
  transform: translateY(-2px) !important;
}

/* ── Circular Arrow Buttons (Cards) ───────────────────────────── */
div[class*="st-key-c_"] {
  display: flex !important;
  justify-content: center !important;
  margin-top: 4px !important;
}
div[class*="st-key-c_"] button {
  background: rgba(91, 139, 255, 0.15) !important;
  color: #5B8BFF !important;
  border: 1px solid rgba(91, 139, 255, 0.3) !important;
  border-radius: 50% !important;
  width: 38px !important;
  height: 38px !important;
  min-height: 38px !important;
  max-width: 38px !important;
  padding: 0 !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  font-size: 1.1rem !important;
  line-height: 1 !important;
  transition: all 0.2s ease !important;
  box-shadow: none !important;
}
div[class*="st-key-c_"] button:hover {
  background: rgba(91, 139, 255, 0.35) !important;
  border-color: #5B8BFF !important;
  transform: scale(1.08) !important;
}

/* ── Bank Card Practice Buttons ───────────────────────────────── */
div[class*="st-key-bank_"] button {
  background: rgba(91, 139, 255, 0.1) !important;
  color: #5B8BFF !important;
  border: 1px solid rgba(91, 139, 255, 0.3) !important;
  border-radius: 10px !important;
  font-size: 0.82rem !important;
  font-weight: 600 !important;
  padding: 8px 14px !important;
  width: 100% !important;
  height: auto !important;
  min-height: 36px !important;
  max-width: 100% !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  transition: all 0.2s ease !important;
  box-shadow: none !important;
}
div[class*="st-key-bank_"] button:hover {
  background: rgba(91, 139, 255, 0.22) !important;
  border-color: #5B8BFF !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 4px 14px rgba(91, 139, 255, 0.25) !important;
}

/* ── Back Buttons ─────────────────────────────────────────────── */
div[class*="_back"] button {
  background: rgba(255, 255, 255, 0.04) !important;
  color: #94A3B8 !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  border-radius: 8px !important;
  font-size: 0.85rem !important;
  font-weight: 500 !important;
  padding: 6px 16px !important;
  transition: all 0.15s ease !important;
  box-shadow: none !important;
}
div[class*="_back"] button:hover {
  color: #F1F5F9 !important;
  border-color: rgba(255, 255, 255, 0.25) !important;
  background: rgba(255, 255, 255, 0.08) !important;
}

/* ── Danger & Trash Buttons ───────────────────────────────────── */
div[class*="del_"] button,
div[class*="danger"] button {
  background: rgba(239, 68, 68, 0.12) !important;
  color: #EF4444 !important;
  border: 1px solid rgba(239, 68, 68, 0.3) !important;
  border-radius: 8px !important;
  font-size: 0.85rem !important;
  transition: all 0.2s ease !important;
}
div[class*="del_"] button:hover,
div[class*="danger"] button:hover {
  background: rgba(239, 68, 68, 0.28) !important;
  border-color: #EF4444 !important;
  color: #FFFFFF !important;
  box-shadow: 0 0 12px rgba(239, 68, 68, 0.4) !important;
}

/* ── Tab Styling ──────────────────────────────────────────────── */
div[data-baseweb="tab-list"] {
  gap: 12px !important;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08) !important;
  margin-bottom: 24px !important;
}
div[data-baseweb="tab-list"] button[data-baseweb="tab"] {
  font-size: 0.95rem !important;
  font-weight: 600 !important;
  padding: 10px 18px !important;
  border-radius: 8px 8px 0 0 !important;
  background: transparent !important;
  border: none !important;
}
div[data-baseweb="tab-list"] button[data-baseweb="tab"][aria-selected="true"] {
  color: #5B8BFF !important;
  border-bottom: 2px solid #5B8BFF !important;
}

/* ── Gmail Checkbox Alignment ─────────────────────────────────── */
div.stCheckbox {
  margin-top: 14px !important;
}
div[class*="st-key-hs_master_select_all"],
div[class*="st-key-hs_master_select_all"] div.stCheckbox {
  margin-top: 4px !important;
}
div.stCheckbox label {
  cursor: pointer !important;
}
div.stCheckbox input[type="checkbox"] {
  width: 18px !important;
  height: 18px !important;
  accent-color: #5B8BFF !important;
  cursor: pointer !important;
}

/* ── Gmail-Style Toolbar Action Buttons ───────────────────────── */
div[class*="st-key-hs_batch_del_btn"] button {
  background: linear-gradient(135deg, #EF4444, #DC2626) !important;
  color: #FFFFFF !important;
  border: none !important;
  font-weight: 700 !important;
  border-radius: 8px !important;
  padding: 6px 14px !important;
  box-shadow: 0 2px 10px rgba(239, 68, 68, 0.4) !important;
}
div[class*="st-key-hs_batch_del_btn"] button:hover {
  background: #DC2626 !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 4px 14px rgba(239, 68, 68, 0.6) !important;
}
div[class*="st-key-hs_cancel_select"] button {
  background: rgba(255, 255, 255, 0.06) !important;
  color: #94A3B8 !important;
  border: 1px solid rgba(255, 255, 255, 0.12) !important;
  border-radius: 8px !important;
  padding: 6px 12px !important;
}
div[class*="st-key-hs_cancel_select"] button:hover {
  background: rgba(255, 255, 255, 0.12) !important;
  color: #F1F5F9 !important;
}

/* ── Bank Management Gmail-Style Toolbar & Buttons ───────────── */
div[class*="master_chk"],
div[class*="master_chk"] div.stCheckbox {
  margin-top: 4px !important;
}
div[class*="batch_del_btn"] button {
  background: linear-gradient(135deg, #EF4444, #DC2626) !important;
  color: #FFFFFF !important;
  border: none !important;
  font-weight: 700 !important;
  border-radius: 8px !important;
  padding: 6px 14px !important;
  box-shadow: 0 2px 10px rgba(239, 68, 68, 0.4) !important;
}
div[class*="batch_del_btn"] button:hover {
  background: #DC2626 !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 4px 14px rgba(239, 68, 68, 0.6) !important;
}
div[class*="mg_prac_"] button {
  background: rgba(91, 139, 255, 0.12) !important;
  color: #5B8BFF !important;
  border: 1px solid rgba(91, 139, 255, 0.3) !important;
  border-radius: 8px !important;
  font-size: 0.82rem !important;
  font-weight: 600 !important;
}
div[class*="mg_prac_"] button:hover {
  background: rgba(91, 139, 255, 0.25) !important;
  border-color: #5B8BFF !important;
}
div[class*="mg_view_qs_"] button {
  background: rgba(168, 85, 247, 0.12) !important;
  color: #A855F7 !important;
  border: 1px solid rgba(168, 85, 247, 0.3) !important;
  border-radius: 8px !important;
  font-size: 0.82rem !important;
  font-weight: 600 !important;
}
div[class*="mg_view_qs_"] button:hover {
  background: rgba(168, 85, 247, 0.25) !important;
  border-color: #A855F7 !important;
}
div[class*="mg_add_q_"] button {
  background: rgba(16, 185, 129, 0.12) !important;
  color: #10B981 !important;
  border: 1px solid rgba(16, 185, 129, 0.3) !important;
  border-radius: 8px !important;
  font-size: 0.82rem !important;
  font-weight: 600 !important;
}
div[class*="mg_add_q_"] button:hover {
  background: rgba(16, 185, 129, 0.25) !important;
  border-color: #10B981 !important;
}

/* ── Quiz Submit & Next Buttons ───────────────────────────────── */

div[class*="st-key-qz_submit"] button {
  background: linear-gradient(135deg, #5B8BFF, #3B82F6) !important;
  color: #FFFFFF !important;
  border: none !important;
  border-radius: 12px !important;
  font-weight: 700 !important;
  font-size: 0.95rem !important;
  padding: 12px 28px !important;
  box-shadow: 0 4px 16px rgba(59, 130, 246, 0.35) !important;
  transition: all 0.2s ease !important;
  width: 100% !important;
}
div[class*="st-key-qz_submit"] button:hover {
  transform: translateY(-2px) !important;
  box-shadow: 0 8px 24px rgba(59, 130, 246, 0.5) !important;
}

div[class*="st-key-qz_next"] button {
  background: rgba(16, 185, 129, 0.15) !important;
  color: #10B981 !important;
  border: 1.5px solid rgba(16, 185, 129, 0.4) !important;
  border-radius: 12px !important;
  font-weight: 700 !important;
  font-size: 0.95rem !important;
  padding: 12px 28px !important;
  transition: all 0.2s ease !important;
  width: 100% !important;
}
div[class*="st-key-qz_next"] button:hover {
  background: rgba(16, 185, 129, 0.25) !important;
  border-color: #10B981 !important;
  box-shadow: 0 0 20px rgba(16, 185, 129, 0.25) !important;
}

/* ── Radio → Answer Option Cards ────────────────────────────── */
.stRadio > label { display: none !important; }
.stRadio > div { gap: 0 !important; }
.stRadio > div > label {
  background: rgba(255,255,255,0.02) !important;
  border: 1.5px solid rgba(255,255,255,0.08) !important;
  border-radius: 12px !important;
  padding: 14px 18px !important;
  margin-bottom: 10px !important;
  cursor: pointer !important;
  transition: all 0.15s !important;
  width: 100% !important;
  display: flex !important;
  align-items: center !important;
  color: var(--text-sub) !important;
  font-size: 0.92rem !important;
}
.stRadio > div > label:hover {
  border-color: rgba(91,139,255,0.45) !important;
  background: rgba(91,139,255,0.06) !important;
  color: var(--text) !important;
}
.stRadio > div > label:has(input:checked) {
  border-color: var(--blue) !important;
  background: rgba(91,139,255,0.1) !important;
  color: var(--text) !important;
}
/* Colored radio dot */
.stRadio > div > label > div:first-child > div {
  background: var(--blue) !important;
  border-color: var(--blue) !important;
}

/* ── Text Inputs ─────────────────────────────────────────────── */
.stTextInput input, .stTextArea textarea {
  background: rgba(255,255,255,0.04) !important;
  border: 1px solid rgba(255,255,255,0.1) !important;
  border-radius: 10px !important;
  color: var(--text) !important;
  padding: 11px 14px !important;
  transition: border-color 0.2s !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
  border-color: var(--blue) !important;
  box-shadow: 0 0 0 2px rgba(91,139,255,0.15) !important;
}
.stTextInput label, .stTextArea label {
  color: var(--text-sub) !important;
  font-size: 0.83rem !important;
  font-weight: 500 !important;
  margin-bottom: 6px !important;
}

/* ── Selectbox ───────────────────────────────────────────────── */
div[data-baseweb="select"] > div {
  background: rgba(255,255,255,0.04) !important;
  border: 1px solid rgba(255,255,255,0.1) !important;
  border-radius: 10px !important;
  color: var(--text) !important;
}
div[data-baseweb="popover"], ul[role="listbox"], li[role="option"] {
  background: #0D1528 !important;
  color: var(--text) !important;
  border-color: rgba(255,255,255,0.1) !important;
}
li[role="option"]:hover, li[aria-selected="true"] {
  background: rgba(91,139,255,0.18) !important;
  color: var(--text) !important;
}

/* ── File Uploader ───────────────────────────────────────────── */
[data-testid="stFileUploader"] > section {
  background: rgba(91,139,255,0.04) !important;
  border: 1.5px dashed rgba(91,139,255,0.3) !important;
  border-radius: 14px !important;
  padding: 28px !important;
  transition: all 0.2s !important;
}
[data-testid="stFileUploader"] > section:hover {
  border-color: var(--blue) !important;
  background: rgba(91,139,255,0.08) !important;
}

/* ── Slider ──────────────────────────────────────────────────── */
.stSlider [data-baseweb="slider"] div[data-testid="stThumbValue"] { color: var(--blue) !important; }
.stSlider [role="slider"] { background: var(--blue) !important; }

/* ── Progress Bar ────────────────────────────────────────────── */
.stProgress > div > div {
  background: linear-gradient(90deg, #5B8BFF, #A855F7) !important;
  border-radius: 4px !important;
}
.stProgress > div {
  background: rgba(255,255,255,0.07) !important;
  border-radius: 4px !important;
  height: 6px !important;
}

/* ── Metrics ─────────────────────────────────────────────────── */
div[data-testid="stMetric"] {
  background: var(--bg-card) !important;
  border: 1px solid var(--border) !important;
  border-radius: 14px !important;
  padding: 20px !important;
}
div[data-testid="stMetricValue"] { color: var(--blue) !important; font-weight: 700 !important; }
div[data-testid="stMetricLabel"] { color: var(--text-dim) !important; font-size: 0.8rem !important; }

/* ── Tabs ────────────────────────────────────────────────────── */
button[data-baseweb="tab"] {
  color: var(--text-dim) !important;
  font-weight: 500 !important;
  background: transparent !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
  color: var(--blue) !important;
  border-bottom: 2px solid var(--blue) !important;
}

/* ── Dataframes ──────────────────────────────────────────────── */
div[data-testid="stDataFrame"], div[data-testid="stTable"] {
  background: var(--bg-card) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
}
div[data-testid="stDataFrame"] * { color: var(--text) !important; }

/* ── Scrollbar ───────────────────────────────────────────────── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(91,139,255,0.22); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(91,139,255,0.4); }

/* ── Question & Case Study Cards ────────────────────────────── */
.ss-question-card {
  background: rgba(13,21,40,0.85);
  border: 1px solid rgba(255,255,255,0.08);
  border-left: 3px solid #5B8BFF;
  border-radius: 14px;
  padding: 24px 28px;
  margin: 16px 0 20px;
}
.ss-case-card {
  background: rgba(91,139,255,0.06);
  border: 1px solid rgba(91,139,255,0.22);
  border-left: 4px solid #5B8BFF;
  border-radius: 10px;
  padding: 16px 20px;
  margin-bottom: 18px;
}
.ss-case-badge {
  font-size: 0.72rem;
  font-weight: 700;
  color: #5B8BFF;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 8px;
}
.ss-case-text {
  font-size: 0.95rem;
  color: #CBD5E1;
  line-height: 1.7;
  white-space: pre-line;
}
.ss-q-header {
  font-size: 0.70rem;
  color: #5B8BFF;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 10px;
}
.ss-q-text {
  font-size: 1.08rem;
  font-weight: 600;
  color: #F1F5F9;
  line-height: 1.6;
  white-space: pre-line;
}
.ss-q-topic {
  font-size: 0.75rem;
  color: #64748B;
  margin-top: 8px;
}
</style>
"""


# ╔══════════════════════════════════════════════════════════════════════╗
# ║                         NAVIGATION HELPERS                           ║
# ╚══════════════════════════════════════════════════════════════════════╝

def _go_to(page: str, **extra):
    """Navigate to a page by updating session state."""
    st.session_state["page"] = page
    for k, v in extra.items():
        st.session_state[k] = v
    st.rerun()


@st.cache_data(ttl=30, show_spinner=False)
def _cached_get_question_banks():
    return QuestionRepository.get_question_banks()


def _get_question_banks():
    """Returns list of QuestionBankModel objects from MySQL with short-lived TTL caching."""
    try:
        return _cached_get_question_banks()
    except Exception as err:
        from src.utils.exceptions import DatabaseConnectionError
        if isinstance(err, DatabaseConnectionError):
            st.error("Database connection unavailable. Please try again shortly.")
        return []


def _page_wrap_start():
    """Injects the ss-page container open tag."""
    st.markdown('<div class="ss-page">', unsafe_allow_html=True)


def _page_wrap_end():
    """Injects the ss-page container close tag."""
    st.markdown("</div>", unsafe_allow_html=True)


# ╔══════════════════════════════════════════════════════════════════════╗
# ║                          TOP NAVBAR                                   ║
# ╚══════════════════════════════════════════════════════════════════════╝

def render_navbar():
    """Sticky top navigation bar with logo and nav links."""
    with st.container(key="ss_navbar_container"):
        c_logo, _, c_home, c_prog, c_hist = st.columns([3.5, 4.5, 1.2, 1.2, 1.2])

        with c_logo:
            st.html(
                '<div style="display:flex;align-items:center;gap:10px;padding:4px 0;'
                'font-size:1.15rem;font-weight:800;color:#F1F5F9;cursor:default;">'
                '<div style="width:34px;height:34px;background:linear-gradient(135deg,#5B8BFF,#A855F7);'
                'border-radius:9px;display:flex;align-items:center;justify-content:center;'
                'font-size:1rem;flex-shrink:0;">📚</div>'
                'Study <span style="background:linear-gradient(135deg,#5B8BFF,#A855F7);'
                '-webkit-background-clip:text;-webkit-text-fill-color:transparent;'
                'background-clip:text;">Smarter</span>'
                '</div>'
            )

        with c_home:
            if st.button("Home", key="_nb_home", use_container_width=True):
                _go_to("home")

        with c_prog:
            if st.button("Progress", key="_nb_progress", use_container_width=True):
                _go_to("progress")

        with c_hist:
            if st.button("History", key="_nb_history", use_container_width=True):
                _go_to("history")


# ╔══════════════════════════════════════════════════════════════════════╗
# ║                          HERO VISUAL                                  ║
# ╚══════════════════════════════════════════════════════════════════════╝

_HERO_VISUAL = (
    '<div style="position:relative;padding:16px 8px;display:flex;align-items:center;justify-content:center;min-height:300px;">'
    '<div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:280px;height:280px;'
    'background:radial-gradient(circle,rgba(91,139,255,0.15) 0%,transparent 70%);border-radius:50%;pointer-events:none;"></div>'
    '<div style="position:relative;width:100%;max-width:380px;display:flex;flex-direction:column;gap:12px;">'
    
    '<div style="background:rgba(13,21,40,0.95);border:1px solid rgba(91,139,255,0.25);border-radius:14px;padding:14px 18px;'
    'box-shadow:0 8px 32px rgba(0,0,0,0.5);display:flex;align-items:center;justify-content:space-between;">'
    '<div style="display:flex;align-items:center;gap:12px;">'
    '<div style="width:40px;height:48px;background:linear-gradient(135deg,#EF4444,#F59E0B);border-radius:8px;'
    'display:flex;align-items:center;justify-content:center;font-size:0.78rem;font-weight:800;color:white;letter-spacing:-0.5px;">PDF</div>'
    '<div>'
    '<div style="font-size:0.88rem;font-weight:700;color:#F1F5F9;">Question Bank</div>'
    '<div style="font-size:0.7rem;color:#64748B;margin-top:2px;">Physics_Revision.pdf</div>'
    '<div style="height:4px;width:140px;background:rgba(255,255,255,0.08);border-radius:2px;margin-top:6px;">'
    '<div style="height:4px;width:75%;background:linear-gradient(90deg,#5B8BFF,#A855F7);border-radius:2px;"></div>'
    '</div></div></div>'
    '<div style="color:#5B8BFF;font-size:1.3rem;opacity:0.8;">&#10142;</div></div>'
    
    '<div style="background:rgba(13,21,40,0.95);border:1px solid rgba(91,139,255,0.2);border-radius:14px;padding:16px 18px;'
    'box-shadow:0 8px 32px rgba(0,0,0,0.45);">'
    '<div style="font-size:0.78rem;color:#94A3B8;margin-bottom:10px;font-weight:600;">Q. What is the powerhouse of the cell?</div>'
    '<div style="display:flex;flex-direction:column;gap:6px;">'
    '<div style="display:flex;align-items:center;gap:10px;padding:4px 8px;opacity:0.6;">'
    '<div style="width:12px;height:12px;border-radius:50%;border:1.5px solid #64748B;"></div>'
    '<span style="font-size:0.72rem;color:#94A3B8;">A. Ribosome</span></div>'
    '<div style="display:flex;align-items:center;gap:10px;background:rgba(16,185,129,0.12);border:1px solid rgba(16,185,129,0.35);border-radius:8px;padding:6px 10px;">'
    '<div style="width:12px;height:12px;border-radius:50%;background:#10B981;"></div>'
    '<span style="font-size:0.72rem;color:#10B981;font-weight:700;">B. Mitochondria &#10003;</span></div>'
    '<div style="display:flex;align-items:center;gap:10px;padding:4px 8px;opacity:0.6;">'
    '<div style="width:12px;height:12px;border-radius:50%;border:1.5px solid #64748B;"></div>'
    '<span style="font-size:0.72rem;color:#94A3B8;">C. Nucleus</span></div>'
    '</div></div>'
    
    '<div style="display:flex;gap:10px;align-items:stretch;">'
    '<div style="background:rgba(16,185,129,0.12);border:1px solid rgba(16,185,129,0.4);border-radius:12px;padding:10px 14px;'
    'display:flex;align-items:center;gap:8px;box-shadow:0 0 20px rgba(16,185,129,0.15);">'
    '<div style="width:20px;height:20px;background:#10B981;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:0.7rem;color:white;font-weight:800;">&#10003;</div>'
    '<div style="font-size:0.85rem;color:#10B981;font-weight:700;">Correct!</div></div>'
    '<div style="background:rgba(13,21,40,0.95);border:1px solid rgba(168,85,247,0.25);border-radius:12px;padding:10px 14px;flex:1;'
    'box-shadow:0 4px 20px rgba(0,0,0,0.4);">'
    '<div style="font-size:0.65rem;color:#A855F7;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:3px;">Explanation</div>'
    '<div style="font-size:0.68rem;color:#94A3B8;line-height:1.4;">Generates most of the chemical energy needed to power the cell.</div></div></div>'
    
    '</div></div>'
)


# ╔══════════════════════════════════════════════════════════════════════╗
# ║                          HOME PAGE                                    ║
# ╚══════════════════════════════════════════════════════════════════════╝

def render_home_page(selected_bank_id=None, selected_bank_name="All Banks"):
    """Home page: hero, action cards, stats strip, recent banks, footer."""
    _page_wrap_start()

    # ─── Hero ──────────────────────────────────────────────────────────
    st.html('<div style="height:32px;"></div>')

    hero_l, hero_r = st.columns([1.1, 0.9], gap="large")

    with hero_l:
        # Tag pill
        st.html(
            '<div style="display:inline-flex;align-items:center;gap:6px;'
            'background:rgba(91,139,255,0.1);border:1px solid rgba(91,139,255,0.25);'
            'border-radius:20px;padding:6px 16px;font-size:0.78rem;'
            'color:#5B8BFF;font-weight:500;margin-bottom:20px;">'
            '✦ Your Questions. Your Progress. A Smarter You.'
            '</div>'
        )

        # Heading
        st.html(
            '<div style="font-size:2.8rem;font-weight:900;line-height:1.15;'
            'letter-spacing:-0.02em;margin-bottom:16px;color:#F1F5F9;">'
            'Turn Your '
            '<span style="background:linear-gradient(135deg,#5B8BFF,#A855F7);'
            '-webkit-background-clip:text;-webkit-text-fill-color:transparent;'
            'background-clip:text;">Question Bank</span>'
            '<br>into Smart Practice.'
            '</div>'
        )

        # Description
        st.html(
            '<p style="font-size:1rem;color:#94A3B8;line-height:1.75;margin-bottom:28px;max-width:480px;">'
            'Upload your question-bank PDF, practice MCQs,<br>'
            'get instant feedback with solutions,<br>'
            'and track your progress — all in one place.'
            '</p>'
        )

        # CTA Buttons
        b1, b2, _ = st.columns([1.3, 1.2, 1.0])
        with b1:
            if st.button("Scan Question Bank →", key="h_scan", type="primary", use_container_width=True):
                _go_to("upload")
        with b2:
            if st.button("Start Practice →", key="h_practice", type="secondary", use_container_width=True):
                _go_to("practice")

    with hero_r:
        st.html(_HERO_VISUAL)

    # ─── Feature Pills ──────────────────────────────────────────────────
    st.html(
        '<div style="display:flex;flex-wrap:wrap;gap:12px;margin:32px 0 36px;">'
        '<span style="display:inline-flex;align-items:center;gap:6px;background:rgba(255,255,255,0.03);'
        'border:1px solid rgba(255,255,255,0.09);border-radius:20px;padding:6px 16px;font-size:0.78rem;'
        'color:#94A3B8;font-weight:500;">✦ AI-Powered Solutions</span>'
        '<span style="display:inline-flex;align-items:center;gap:6px;background:rgba(255,255,255,0.03);'
        'border:1px solid rgba(255,255,255,0.09);border-radius:20px;padding:6px 16px;font-size:0.78rem;'
        'color:#94A3B8;font-weight:500;">📈 Track Your Progress</span>'
        '<span style="display:inline-flex;align-items:center;gap:6px;background:rgba(255,255,255,0.03);'
        'border:1px solid rgba(255,255,255,0.09);border-radius:20px;padding:6px 16px;font-size:0.78rem;'
        'color:#94A3B8;font-weight:500;">🎯 Learn from Mistakes</span>'
        '<span style="display:inline-flex;align-items:center;gap:6px;background:rgba(255,255,255,0.03);'
        'border:1px solid rgba(255,255,255,0.09);border-radius:20px;padding:6px 16px;font-size:0.78rem;'
        'color:#94A3B8;font-weight:500;">⭐ Study Smarter</span>'
        '</div>'
    )

    # ─── 5 Action Cards ─────────────────────────────────────────────────
    _CARDS = [
        {
            "icon": "☁️", "title": "Scan Question Bank",
            "desc": "Upload a PDF and convert it into practice questions.",
            "color": "#3B82F6", "bg": "rgba(59,130,246,0.06)",
            "border": "rgba(59,130,246,0.22)", "page": "upload",
        },
        {
            "icon": "▶️", "title": "Start Practice",
            "desc": "Practice questions from your uploaded banks.",
            "color": "#10B981", "bg": "rgba(16,185,129,0.06)",
            "border": "rgba(16,185,129,0.22)", "page": "practice",
        },
        {
            "icon": "📊", "title": "View Progress",
            "desc": "Track your completion, accuracy and weak areas.",
            "color": "#A855F7", "bg": "rgba(168,85,247,0.06)",
            "border": "rgba(168,85,247,0.22)", "page": "progress",
        },
        {
            "icon": "📋", "title": "Review Mistakes",
            "desc": "Revisit questions you answered incorrectly.",
            "color": "#F59E0B", "bg": "rgba(245,158,11,0.06)",
            "border": "rgba(245,158,11,0.22)", "page": "mistakes",
        },
        {
            "icon": "🕐", "title": "Study History",
            "desc": "See your past practice sessions and performance.",
            "color": "#EC4899", "bg": "rgba(236,72,153,0.06)",
            "border": "rgba(236,72,153,0.22)", "page": "history",
        },
    ]

    card_cols = st.columns(5, gap="small")
    for i, (col, card) in enumerate(zip(card_cols, _CARDS)):
        with col:
            st.html(
                f'<div style="background:{card["bg"]};border:1px solid {card["border"]};'
                f'border-top:3px solid {card["color"]};border-radius:16px;'
                f'padding:20px 16px 14px;min-height:165px;margin-bottom:6px;">'
                f'<div style="width:48px;height:48px;border-radius:12px;'
                f'background:rgba(255,255,255,0.05);display:flex;align-items:center;justify-content:center;'
                f'font-size:1.35rem;margin-bottom:12px;">{card["icon"]}</div>'
                f'<div style="font-size:0.92rem;font-weight:700;color:#F1F5F9;margin-bottom:6px;">{card["title"]}</div>'
                f'<div style="font-size:0.75rem;color:#64748B;line-height:1.45;">{card["desc"]}</div>'
                f'</div>'
            )
            if st.button("→", key=f"c_{i}"):
                _go_to(card["page"])

    # ─── Stats Strip ─────────────────────────────────────────────────────
    try:
        _banks = _get_question_banks()
        _total_qs = sum(b.question_count for b in _banks) if _banks else QuestionRepository.get_total_questions_in_bank(bank_id=None)
        _summary = AnalyticsService.get_overall_summary(user_id=1)
        _st = {
            "banks": len(_banks),
            "qs": _total_qs,
            "practiced": _summary.get("total_questions_attempted", 0),
            "accuracy": _summary.get("overall_accuracy", 0.0),
        }
    except Exception:
        _st = {"banks": 0, "qs": 0, "practiced": 0, "accuracy": 0.0}

    st.html(
        f'<div style="background:rgba(13,21,40,0.85);border:1px solid rgba(255,255,255,0.07);'
        f'border-radius:16px;padding:22px 32px;margin:28px 0;'
        f'display:flex;align-items:center;justify-content:space-around;gap:16px;flex-wrap:wrap;">'

        f'<div style="display:flex;align-items:center;gap:14px;flex:1;min-width:120px;">'
        f'<div style="width:44px;height:44px;border-radius:12px;background:rgba(59,130,246,0.12);'
        f'display:flex;align-items:center;justify-content:center;font-size:1.2rem;">📘</div>'
        f'<div><div style="font-size:0.72rem;color:#64748B;font-weight:500;margin-bottom:3px;">Question Banks</div>'
        f'<div style="font-size:1.85rem;font-weight:800;color:#5B8BFF;line-height:1;">{_st["banks"]}</div></div></div>'

        f'<div style="width:1px;height:46px;background:rgba(255,255,255,0.06);flex-shrink:0;"></div>'

        f'<div style="display:flex;align-items:center;gap:14px;flex:1;min-width:120px;">'
        f'<div style="width:44px;height:44px;border-radius:12px;background:rgba(168,85,247,0.12);'
        f'display:flex;align-items:center;justify-content:center;font-size:1.2rem;">📄</div>'
        f'<div><div style="font-size:0.72rem;color:#64748B;font-weight:500;margin-bottom:3px;">Questions Available</div>'
        f'<div style="font-size:1.85rem;font-weight:800;color:#A855F7;line-height:1;">{_st["qs"]}</div></div></div>'

        f'<div style="width:1px;height:46px;background:rgba(255,255,255,0.06);flex-shrink:0;"></div>'

        f'<div style="display:flex;align-items:center;gap:14px;flex:1;min-width:120px;">'
        f'<div style="width:44px;height:44px;border-radius:12px;background:rgba(16,185,129,0.12);'
        f'display:flex;align-items:center;justify-content:center;font-size:1.2rem;">🎯</div>'
        f'<div><div style="font-size:0.72rem;color:#64748B;font-weight:500;margin-bottom:3px;">Questions Practiced</div>'
        f'<div style="font-size:1.85rem;font-weight:800;color:#10B981;line-height:1;">{_st["practiced"]}</div></div></div>'

        f'<div style="width:1px;height:46px;background:rgba(255,255,255,0.06);flex-shrink:0;"></div>'

        f'<div style="display:flex;align-items:center;gap:14px;flex:1;min-width:120px;">'
        f'<div style="width:44px;height:44px;border-radius:12px;background:rgba(245,158,11,0.12);'
        f'display:flex;align-items:center;justify-content:center;font-size:1.2rem;">🏆</div>'
        f'<div><div style="font-size:0.72rem;color:#64748B;font-weight:500;margin-bottom:3px;">Overall Accuracy</div>'
        f'<div style="font-size:1.85rem;font-weight:800;color:#F59E0B;line-height:1;">{_st["accuracy"]}%</div></div></div>'

        f'</div>'
    )

    # ─── Recent Question Banks ───────────────────────────────────────────
    banks = _banks

    # Header row with "View All" link
    rq_l, rq_r = st.columns([5, 1])
    with rq_l:
        st.html('<h2 style="font-size:1.15rem;font-weight:700;color:#F1F5F9;margin:8px 0 16px;">Your Recent Question Banks</h2>')
    with rq_r:
        if st.button("View All →", key="h_view_all"):
            _go_to("banks")

    if not banks:
        st.html(
            '<div style="background:rgba(13,21,40,0.6);border:1px dashed rgba(255,255,255,0.08);'
            'border-radius:14px;padding:40px;text-align:center;">'
            '<div style="font-size:2.2rem;margin-bottom:12px;opacity:0.35;">📂</div>'
            '<h3 style="font-size:1rem;color:#94A3B8;font-weight:500;margin-bottom:8px;">No question banks yet</h3>'
            '<p style="font-size:0.83rem;color:#64748B;margin-bottom:20px;">'
            'Scan your first PDF to start practicing.'
            '</p></div>'
        )
        _, _bc, _ = st.columns([2, 1.2, 2])
        with _bc:
            if st.button("Scan Question Bank", key="h_empty_scan", type="primary", use_container_width=True):
                _go_to("upload")
    else:
        recent = sorted(banks, key=lambda b: b.id or 0, reverse=True)[:3]
        recent_bids = [b.id for b in recent if b.id is not None]
        bank_done_map = AttemptRepository.get_unique_questions_attempted_by_banks(user_id=1, bank_ids=recent_bids) if recent_bids else {}
        _pdf_grads = [
            ("linear-gradient(135deg,#EF4444,#F59E0B)", "#3B82F6"),
            ("linear-gradient(135deg,#3B82F6,#A855F7)", "#A855F7"),
            ("linear-gradient(135deg,#10B981,#3B82F6)", "#10B981"),
        ]
        bank_cols = st.columns(min(len(recent), 3), gap="small")
        for i, (col, bank) in enumerate(zip(bank_cols, recent)):
            grad, bar_clr = _pdf_grads[i % 3]
            q_count = bank.question_count or 0
            done = bank_done_map.get(bank.id, 0)
            pct = round(done / q_count * 100) if q_count > 0 else 0

            with col:
                st.html(
                    f'<div style="background:rgba(13,21,40,0.85);border:1px solid rgba(255,255,255,0.07);'
                    f'border-radius:14px;padding:16px;display:flex;align-items:center;'
                    f'gap:12px;margin-bottom:6px;">'
                    f'<div style="width:44px;height:44px;background:{grad};border-radius:10px;'
                    f'display:flex;align-items:center;justify-content:center;'
                    f'font-size:0.7rem;font-weight:800;color:white;flex-shrink:0;'
                    f'letter-spacing:-0.5px;">PDF</div>'
                    f'<div style="flex:1;min-width:0;">'
                    f'<div style="font-size:0.88rem;font-weight:600;color:#F1F5F9;'
                    f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{bank.name}</div>'
                    f'<div style="font-size:0.72rem;color:#64748B;margin:2px 0;">{q_count} questions</div>'
                    f'<div style="height:4px;background:rgba(255,255,255,0.07);border-radius:2px;margin-top:5px;">'
                    f'<div style="height:4px;width:{pct}%;background:linear-gradient(90deg,#10B981,#5B8BFF);'
                    f'border-radius:2px;"></div></div>'
                    f'<div style="font-size:0.65rem;color:#64748B;margin-top:3px;">{pct}% complete</div>'
                    f'</div></div>'
                )
                if st.button("Continue Practice →", key=f"bank_{i}", use_container_width=True):
                    _go_to("practice", practice_bank_id=bank.id, practice_bank_name=bank.name)

    # ─── Footer ──────────────────────────────────────────────────────────
    st.html(
        '<div style="border-top:1px solid rgba(255,255,255,0.06);padding:24px 0;margin-top:48px;'
        'display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:16px;">'
        '<div style="display:flex;align-items:center;gap:8px;font-size:0.98rem;font-weight:700;color:#F1F5F9;">'
        '<div style="width:26px;height:26px;background:linear-gradient(135deg,#5B8BFF,#A855F7);'
        'border-radius:7px;display:flex;align-items:center;justify-content:center;font-size:0.75rem;">📚</div>'
        'Study <span style="background:linear-gradient(135deg,#5B8BFF,#A855F7);'
        '-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-left:3px;">Smarter</span>'
        '</div>'
        '<div style="font-size:0.8rem;color:#64748B;font-style:italic;">'
        '"A little progress each day adds up to big results."'
        '</div>'
        '</div>'
    )

    _page_wrap_end()



# ╔══════════════════════════════════════════════════════════════════════╗
# ║                  QUESTION BANKS MANAGEMENT COMPONENT                 ║
# ╚══════════════════════════════════════════════════════════════════════╝

def render_question_banks_management(key_prefix: str = "mg"):
    """
    Comprehensive Question Banks management view:
    - View all question banks with search, filtering, and sort
    - Gmail-style multi-select batch deletion of question banks
    - Create new Question Bank (no PDF upload required)
    - Per-bank operations:
        * Practice bank
        * Browse & inspect questions inside bank (with correct answer highlighting)
        * Add new questions to bank
        * Edit bank metadata (name, subject, class)
        * Edit/Delete individual questions inside the bank
        * Reset practice progress
        * Delete bank and uploaded PDF
    """
    banks = _get_question_banks()

    # ── Top Action Bar: Create Bank & Search / Filter Controls ──────────
    c_btn, _, c_srch, c_subj, c_sort = st.columns([1.6, 0.2, 1.8, 1.3, 1.3], gap="small")
    with c_btn:
        show_create = st.session_state.get(f"{key_prefix}_show_create_bank", False)
        create_lbl = "✖️ Close" if show_create else "➕ Create New Bank"
        if st.button(create_lbl, key=f"{key_prefix}_btn_create_toggle", use_container_width=True):
            st.session_state[f"{key_prefix}_show_create_bank"] = not show_create
            st.rerun()

    with c_srch:
        search_query = st.text_input(
            "Search",
            placeholder="🔍 Search banks...",
            key=f"{key_prefix}_search_input",
            label_visibility="collapsed",
        ).strip().lower()

    with c_subj:
        all_subjects = sorted(list({getattr(b, "subject", "General") or "General" for b in banks}))
        subj_choice = st.selectbox(
            "Subject Filter",
            options=["All Subjects"] + all_subjects,
            key=f"{key_prefix}_subj_filter",
            label_visibility="collapsed",
        )

    with c_sort:
        sort_choice = st.selectbox(
            "Sort Order",
            options=["Newest First", "Name (A-Z)", "Most Questions"],
            key=f"{key_prefix}_sort_filter",
            label_visibility="collapsed",
        )

    # ── New Bank Creation Panel ────────────────────────────────────────
    if st.session_state.get(f"{key_prefix}_show_create_bank", False):
        with st.container():
            st.markdown(
                '<div style="background:rgba(91,139,255,0.06);border:1px solid rgba(91,139,255,0.22);'
                'border-radius:12px;padding:18px 22px;margin:12px 0 18px;">'
                '<div style="font-size:0.95rem;font-weight:700;color:#5B8BFF;margin-bottom:12px;">'
                '➕ Create New Question Bank</div>',
                unsafe_allow_html=True,
            )
            nb_c1, nb_c2, nb_c3 = st.columns([1.6, 1.2, 0.8])
            with nb_c1:
                new_b_name = st.text_input("Question Bank Name *", placeholder="e.g. Physics Mechanics Chapter 1", key=f"{key_prefix}_nb_name")
            with nb_c2:
                new_b_subj = st.text_input("Subject Category", placeholder="e.g. Physics, Chemistry", key=f"{key_prefix}_nb_subj")
            with nb_c3:
                new_b_class = st.selectbox("Class Level", options=[0, 10, 11, 12], format_func=lambda x: "General (0)" if x == 0 else f"Class {x}", key=f"{key_prefix}_nb_class")

            nb_s1, _ = st.columns([1.5, 3])
            with nb_s1:
                if st.button("🚀 Create Question Bank", key=f"{key_prefix}_nb_submit", type="primary", use_container_width=True):
                    if not new_b_name or not new_b_name.strip():
                        st.warning("Please enter a question bank name.")
                    else:
                        clean_nb_name = new_b_name.strip()
                        new_bid = QuestionRepository.create_question_bank(clean_nb_name)
                        if new_bid:
                            subj_val = new_b_subj.strip() if new_b_subj and new_b_subj.strip() else "General"
                            QuestionRepository.update_question_bank(new_bid, clean_nb_name, subj_val, new_b_class)
                            st.session_state[f"{key_prefix}_show_create_bank"] = False
                            st.toast(f"Created question bank '{clean_nb_name}'!")
                            st.rerun()
                        else:
                            st.error("Could not create question bank.")
            st.markdown('</div>', unsafe_allow_html=True)

    if not banks:
        st.markdown(
            """
            <div style="background:rgba(13,21,40,0.6);border:1px dashed rgba(255,255,255,0.08);
                        border-radius:14px;padding:40px;text-align:center;margin-top:16px;">
                <div style="font-size:2rem;margin-bottom:10px;opacity:0.35;">📂</div>
                <h3 style="font-size:1rem;color:#94A3B8;font-weight:500;margin-bottom:6px;">No question banks available</h3>
                <p style="font-size:0.82rem;color:#64748B;">Upload a PDF in the 'Scan & Upload' tab or create a new question bank above.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # Filter & Sort
    filtered_banks = list(banks)
    if search_query:
        filtered_banks = [
            b for b in filtered_banks
            if search_query in (b.name or "").lower()
            or search_query in (getattr(b, "subject", "") or "").lower()
            or search_query in (b.source_pdf or "").lower()
        ]
    if subj_choice and subj_choice != "All Subjects":
        filtered_banks = [
            b for b in filtered_banks
            if (getattr(b, "subject", "General") or "General").lower() == subj_choice.lower()
        ]

    if sort_choice == "Newest First":
        filtered_banks = sorted(filtered_banks, key=lambda b: b.id or 0, reverse=True)
    elif sort_choice == "Name (A-Z)":
        filtered_banks = sorted(filtered_banks, key=lambda b: (b.name or "").lower())
    elif sort_choice == "Most Questions":
        filtered_banks = sorted(filtered_banks, key=lambda b: b.question_count or 0, reverse=True)

    if not filtered_banks:
        st.markdown(
            '<div style="padding:24px;text-align:center;color:#64748B;font-size:0.88rem;">'
            'No question banks matched your search or subject filter.</div>',
            unsafe_allow_html=True,
        )
        return

    # ── Gmail-Style Multi-Select Action Bar ────────────────────────────
    selected_bids = [
        b.id for b in filtered_banks
        if b.id and st.session_state.get(f"{key_prefix}_chk_{b.id}", False)
    ]
    num_b_selected = len(selected_bids)
    all_b_selected = (num_b_selected == len(filtered_banks) and len(filtered_banks) > 0)

    st.markdown('<div style="height:6px;"></div>', unsafe_allow_html=True)
    tb_c1, tb_c2, _ = st.columns([2.2, 4.2, 1.6], gap="small")

    with tb_c1:
        def _on_bank_select_all_toggle():
            new_v = st.session_state.get(f"{key_prefix}_master_chk", False)
            for b in filtered_banks:
                if b.id:
                    st.session_state[f"{key_prefix}_chk_{b.id}"] = new_v

        st.checkbox(
            f"Select All Banks ({len(filtered_banks)})",
            value=all_b_selected,
            key=f"{key_prefix}_master_chk",
            on_change=_on_bank_select_all_toggle,
        )

    with tb_c2:
        if num_b_selected > 0:
            cb_badge, cb_del, cb_cancel = st.columns([1.3, 1.8, 1.1])
            with cb_badge:
                st.markdown(
                    f'<div style="padding-top:6px;font-size:0.85rem;color:#5B8BFF;font-weight:700;">'
                    f'✓ {num_b_selected} selected</div>',
                    unsafe_allow_html=True,
                )
            with cb_del:
                confirm_del = st.session_state.get(f"{key_prefix}_confirm_del_batch", False)
                del_txt = "⚠️ Confirm?" if confirm_del else f"🗑️ Delete ({num_b_selected})"
                if st.button(del_txt, key=f"{key_prefix}_batch_del_btn", type="primary", use_container_width=True):
                    if not confirm_del:
                        st.session_state[f"{key_prefix}_confirm_del_batch"] = True
                        st.rerun()
                    else:
                        deleted = QuestionRepository.delete_question_banks(selected_bids)
                        for bid in selected_bids:
                            st.session_state.pop(f"{key_prefix}_chk_{bid}", None)
                        st.session_state[f"{key_prefix}_confirm_del_batch"] = False
                        st.session_state[f"{key_prefix}_master_chk"] = False
                        st.toast(f"Deleted {deleted} question bank(s) successfully!")
                        st.rerun()
            with cb_cancel:
                def _do_deselect_banks():
                    for b in filtered_banks:
                        if b.id:
                            st.session_state[f"{key_prefix}_chk_{b.id}"] = False
                    st.session_state[f"{key_prefix}_master_chk"] = False
                    st.session_state[f"{key_prefix}_confirm_del_batch"] = False

                if st.button("Cancel", key=f"{key_prefix}_cancel_batch", on_click=_do_deselect_banks):
                    _do_deselect_banks()
                    st.rerun()
        else:
            st.session_state[f"{key_prefix}_confirm_del_batch"] = False
            st.markdown(
                f'<div style="padding-top:6px;font-size:0.8rem;color:#64748B;">'
                f'{len(filtered_banks)} question bank(s) in collection</div>',
                unsafe_allow_html=True,
            )

    st.markdown('<div style="height:6px;"></div>', unsafe_allow_html=True)

    # ── Bank Cards Loop ────────────────────────────────────────────────
    for b_idx, bank in enumerate(filtered_banks):
        q_count = bank.question_count or 0
        done_count = 0
        try:
            done_count = AttemptRepository.get_unique_questions_attempted(user_id=1, bank_id=bank.id)
        except Exception:
            pass
        pct = round(done_count / q_count * 100) if q_count > 0 else 0
        created_str = str(bank.created_at)[:10] if bank.created_at else "Active"
        source_pdf_display = bank.source_pdf or "Manual Question Bank"
        subj_val = getattr(bank, "subject", "General") or "General"
        class_val = getattr(bank, "class_level", 0) or 0
        class_badge = f"Class {class_val}" if class_val > 0 else "General"

        is_chk = st.session_state.get(f"{key_prefix}_chk_{bank.id}", False)
        card_bg = "rgba(91,139,255,0.08)" if is_chk else "rgba(13,21,40,0.85)"
        card_border = "1px solid rgba(91,139,255,0.4)" if is_chk else "1px solid rgba(255,255,255,0.08)"

        row_chk, row_body = st.columns([0.4, 9.6], gap="small")
        with row_chk:
            st.checkbox(f"Select {bank.name}", key=f"{key_prefix}_chk_{bank.id}", label_visibility="collapsed")

        with row_body:
            st.markdown(
                f"""
                <div style="background:{card_bg};border:{card_border};
                            border-radius:14px;padding:20px 24px;margin-bottom:12px;transition:all 0.15s ease;">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:12px;">
                        <div>
                            <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;">
                                <span style="font-size:1.3rem;">📘</span>
                                <span style="font-size:1.15rem;font-weight:700;color:#F1F5F9;">{bank.name}</span>
                                <span style="background:rgba(91,139,255,0.15);color:#5B8BFF;font-size:0.75rem;font-weight:700;padding:3px 10px;border-radius:6px;">
                                    {q_count} Questions
                                </span>
                                <span style="background:rgba(168,85,247,0.15);color:#A855F7;font-size:0.75rem;font-weight:700;padding:3px 10px;border-radius:6px;">
                                    🧪 {subj_val}
                                </span>
                                <span style="background:rgba(16,185,129,0.15);color:#10B981;font-size:0.75rem;font-weight:700;padding:3px 10px;border-radius:6px;">
                                    🎓 {class_badge}
                                </span>
                            </div>
                            <div style="font-size:0.8rem;color:#64748B;margin-top:8px;display:flex;gap:20px;flex-wrap:wrap;">
                                <span>📄 <strong>Source:</strong> {source_pdf_display}</span>
                                <span>📅 <strong>Added:</strong> {created_str}</span>
                                <span>🎯 <strong>Practiced:</strong> {done_count}/{q_count} ({pct}%)</span>
                            </div>
                            <div style="height:4px;background:rgba(255,255,255,0.07);border-radius:2px;margin-top:10px;max-width:380px;">
                                <div style="height:4px;width:{pct}%;background:linear-gradient(90deg,#10B981,#5B8BFF);border-radius:2px;"></div>
                            </div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            btn_c1, btn_c2, btn_c3, btn_c4, btn_c5, btn_c6 = st.columns([1.1, 1.4, 1.2, 1.2, 1.4, 1.4])

            with btn_c1:
                if st.button("⚡ Practice", key=f"{key_prefix}_prac_{bank.id}_{b_idx}", use_container_width=True):
                    _go_to("practice", practice_bank_id=bank.id, practice_bank_name=bank.name)

            with btn_c2:
                qs_expanded = st.session_state.get(f"{key_prefix}_show_qs_{bank.id}", False)
                qs_label = "✖️ Hide Qs" if qs_expanded else f"👁️ Questions ({q_count})"
                if st.button(qs_label, key=f"{key_prefix}_view_qs_{bank.id}_{b_idx}", use_container_width=True):
                    st.session_state[f"{key_prefix}_show_qs_{bank.id}"] = not qs_expanded
                    st.session_state.pop(f"show_add_q_{bank.id}", None)
                    st.session_state.pop(f"show_edit_{bank.id}", None)
                    st.session_state.pop(f"show_reset_{bank.id}", None)
                    st.session_state.pop(f"show_del_{bank.id}", None)
                    st.rerun()

            with btn_c3:
                add_expanded = st.session_state.get(f"show_add_q_{bank.id}", False)
                add_label = "✖️ Close" if add_expanded else "➕ Add Q"
                if st.button(add_label, key=f"{key_prefix}_add_q_btn_{bank.id}_{b_idx}", use_container_width=True):
                    st.session_state[f"show_add_q_{bank.id}"] = not add_expanded
                    st.session_state.pop(f"{key_prefix}_show_qs_{bank.id}", None)
                    st.session_state.pop(f"show_edit_{bank.id}", None)
                    st.session_state.pop(f"show_reset_{bank.id}", None)
                    st.session_state.pop(f"show_del_{bank.id}", None)
                    st.rerun()

            with btn_c4:
                edit_expanded = st.session_state.get(f"show_edit_{bank.id}", False)
                btn_label = "✖️ Close" if edit_expanded else "✏️ Customize"
                if st.button(btn_label, key=f"{key_prefix}_edit_btn_{bank.id}_{b_idx}", use_container_width=True):
                    st.session_state[f"show_edit_{bank.id}"] = not edit_expanded
                    st.session_state.pop(f"{key_prefix}_show_qs_{bank.id}", None)
                    st.session_state.pop(f"show_add_q_{bank.id}", None)
                    st.session_state.pop(f"show_reset_{bank.id}", None)
                    st.session_state.pop(f"show_del_{bank.id}", None)
                    st.rerun()

            with btn_c5:
                reset_expanded = st.session_state.get(f"show_reset_{bank.id}", False)
                rst_label = "✖️ Close" if reset_expanded else "🔄 Reset Progress"
                if st.button(rst_label, key=f"{key_prefix}_rst_btn_{bank.id}_{b_idx}", use_container_width=True):
                    st.session_state[f"show_reset_{bank.id}"] = not reset_expanded
                    st.session_state.pop(f"{key_prefix}_show_qs_{bank.id}", None)
                    st.session_state.pop(f"show_add_q_{bank.id}", None)
                    st.session_state.pop(f"show_edit_{bank.id}", None)
                    st.session_state.pop(f"show_del_{bank.id}", None)
                    st.rerun()

            with btn_c6:
                del_expanded = st.session_state.get(f"show_del_{bank.id}", False)
                del_label = "✖️ Close" if del_expanded else "🗑️ Delete PDF Bank"
                if st.button(del_label, key=f"{key_prefix}_del_btn_{bank.id}_{b_idx}", use_container_width=True):
                    st.session_state[f"show_del_{bank.id}"] = not del_expanded
                    st.session_state.pop(f"{key_prefix}_show_qs_{bank.id}", None)
                    st.session_state.pop(f"show_add_q_{bank.id}", None)
                    st.session_state.pop(f"show_edit_{bank.id}", None)
                    st.session_state.pop(f"show_reset_{bank.id}", None)
                    st.rerun()

            # ── Sub-Panel 1: Questions Browser ──
            if st.session_state.get(f"{key_prefix}_show_qs_{bank.id}", False):
                with st.container():
                    st.markdown(
                        f"""
                        <div style="background:rgba(168,85,247,0.05);border:1px solid rgba(168,85,247,0.25);
                                    border-radius:12px;padding:16px 20px;margin:12px 0 16px;">
                            <div style="font-size:0.95rem;font-weight:700;color:#A855F7;margin-bottom:4px;">
                                👁️ Questions Inside '{bank.name}' ({q_count} total)
                            </div>
                            <div style="font-size:0.8rem;color:#94A3B8;">
                                Browse, inspect correct answers, edit questions, or remove questions from this bank.
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    bank_questions = QuestionRepository.get_all_questions(bank_id=bank.id)
                    if not bank_questions:
                        st.info("No questions in this bank yet. Click '➕ Add Q' above to create one!")
                    else:
                        for q_idx, q in enumerate(bank_questions, 1):
                            q_diff = q.difficulty or "Medium"
                            diff_clr = "#10B981" if q_diff == "Easy" else ("#F59E0B" if q_diff == "Medium" else "#EF4444")
                            corr_ans = (q.correct_answer or "A").strip().upper()

                            with st.container():
                                st.markdown(
                                    f"""
                                    <div style="background:rgba(13,21,40,0.6);border:1px solid rgba(255,255,255,0.06);
                                                border-radius:10px;padding:14px 18px;margin-bottom:10px;">
                                        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                                            <span style="font-size:0.75rem;font-weight:700;color:#64748B;">Question #{q_idx}</span>
                                            <span style="font-size:0.7rem;font-weight:700;color:{diff_clr};background:rgba(255,255,255,0.04);
                                                         padding:2px 8px;border-radius:4px;border:1px solid rgba(255,255,255,0.08);">
                                                {q_diff}
                                            </span>
                                        </div>
                                        <div style="font-size:0.92rem;font-weight:600;color:#F1F5F9;margin-bottom:12px;line-height:1.5;">
                                            {q.question_text}
                                        </div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )

                                # Render 4 Options
                                op_cols = st.columns(2)
                                opts = [
                                    ("A", q.option_a),
                                    ("B", q.option_b),
                                    ("C", q.option_c),
                                    ("D", q.option_d),
                                ]
                                for opt_i, (letter, opt_txt) in enumerate(opts):
                                    with op_cols[opt_i % 2]:
                                        is_corr = (letter == corr_ans)
                                        opt_border = "1px solid #10B981" if is_corr else "1px solid rgba(255,255,255,0.06)"
                                        opt_bg = "rgba(16,185,129,0.12)" if is_corr else "rgba(255,255,255,0.02)"
                                        opt_color = "#10B981" if is_corr else "#CBD5E1"
                                        corr_tag = " <span style='font-size:0.7rem;color:#10B981;font-weight:700;'>✓ Correct Answer</span>" if is_corr else ""
                                        st.markdown(
                                            f"""
                                            <div style="background:{opt_bg};border:{opt_border};border-radius:8px;
                                                        padding:8px 12px;margin-bottom:6px;font-size:0.82rem;color:{opt_color};">
                                                <strong>{letter}.</strong> {opt_txt}{corr_tag}
                                            </div>
                                            """,
                                            unsafe_allow_html=True,
                                        )

                                if q.explanation and q.explanation.strip():
                                    st.markdown(
                                        f"""
                                        <div style="background:rgba(91,139,255,0.05);border-left:3px solid #5B8BFF;
                                                    border-radius:0 8px 8px 0;padding:8px 12px;margin:6px 0 10px;font-size:0.8rem;color:#94A3B8;">
                                            <strong style="color:#5B8BFF;">💡 Explanation:</strong> {q.explanation}
                                        </div>
                                        """,
                                        unsafe_allow_html=True,
                                    )

                                # Question Actions: Edit / Delete
                                qa_col1, qa_col2, _ = st.columns([1.2, 1.2, 4])
                                with qa_col1:
                                    q_edit_open = st.session_state.get(f"show_edit_q_{q.id}", False)
                                    q_btn_lbl = "✖️ Close" if q_edit_open else "✏️ Edit Q"
                                    if st.button(q_btn_lbl, key=f"{key_prefix}_btn_edit_q_{q.id}", use_container_width=True):
                                        st.session_state[f"show_edit_q_{q.id}"] = not q_edit_open
                                        st.rerun()
                                with qa_col2:
                                    if st.button("🗑️ Delete Q", key=f"{key_prefix}_btn_del_q_{q.id}", use_container_width=True):
                                        QuestionRepository.delete_question(q.id)
                                        st.toast(f"Deleted Question #{q_idx}.")
                                        st.rerun()

                                # Inline Question Edit Form
                                if st.session_state.get(f"show_edit_q_{q.id}", False):
                                    with st.container():
                                        st.markdown(
                                            '<div style="background:rgba(91,139,255,0.04);border:1px solid rgba(91,139,255,0.18);'
                                            'border-radius:10px;padding:14px;margin:10px 0;">',
                                            unsafe_allow_html=True,
                                        )
                                        ed_txt = st.text_area("Question Text", value=q.question_text, key=f"{key_prefix}_ed_txt_{q.id}")
                                        e_c1, e_c2 = st.columns(2)
                                        with e_c1:
                                            ed_oa = st.text_input("Option A", value=q.option_a, key=f"{key_prefix}_ed_oa_{q.id}")
                                            ed_ob = st.text_input("Option B", value=q.option_b, key=f"{key_prefix}_ed_ob_{q.id}")
                                        with e_c2:
                                            ed_oc = st.text_input("Option C", value=q.option_c, key=f"{key_prefix}_ed_oc_{q.id}")
                                            ed_od = st.text_input("Option D", value=q.option_d, key=f"{key_prefix}_ed_od_{q.id}")

                                        ans_opts = ["A", "B", "C", "D"]
                                        curr_ans_idx = ans_opts.index(corr_ans) if corr_ans in ans_opts else 0
                                        diff_opts = ["Easy", "Medium", "Hard"]
                                        curr_diff_idx = diff_opts.index(q_diff) if q_diff in diff_opts else 1

                                        e_m1, e_m2 = st.columns([1, 1])
                                        with e_m1:
                                            ed_ans = st.selectbox("Correct Answer", options=ans_opts, index=curr_ans_idx, key=f"{key_prefix}_ed_ans_{q.id}")
                                        with e_m2:
                                            ed_diff = st.selectbox("Difficulty", options=diff_opts, index=curr_diff_idx, key=f"{key_prefix}_ed_diff_{q.id}")

                                        ed_exp = st.text_area("Explanation", value=q.explanation or "", key=f"{key_prefix}_ed_exp_{q.id}")

                                        if st.button("💾 Save Question", key=f"{key_prefix}_save_q_{q.id}", type="primary"):
                                            if not ed_txt.strip():
                                                st.warning("Question text cannot be empty.")
                                            else:
                                                QuestionRepository.update_question(q.id, {
                                                    "question_text": ed_txt.strip(),
                                                    "option_a": ed_oa.strip(),
                                                    "option_b": ed_ob.strip(),
                                                    "option_c": ed_oc.strip(),
                                                    "option_d": ed_od.strip(),
                                                    "correct_answer": ed_ans,
                                                    "difficulty": ed_diff,
                                                    "explanation": ed_exp.strip(),
                                                })
                                                st.session_state[f"show_edit_q_{q.id}"] = False
                                                st.toast(f"Saved Question #{q_idx}!")
                                                st.rerun()
                                        st.markdown('</div>', unsafe_allow_html=True)

                                st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)

            # ── Sub-Panel 2: Add New Question to Bank ──
            if st.session_state.get(f"show_add_q_{bank.id}", False):
                with st.container():
                    st.markdown(
                        f"""
                        <div style="background:rgba(16,185,129,0.06);border:1px solid rgba(16,185,129,0.25);
                                    border-radius:12px;padding:18px 22px;margin:10px 0 16px;">
                            <div style="font-size:0.92rem;font-weight:700;color:#10B981;margin-bottom:6px;">
                                ➕ Add a New Question to '{bank.name}'
                            </div>
                            <div style="font-size:0.8rem;color:#94A3B8;">
                                Create an MCQ question with 4 options, designate the correct answer, and provide an explanation.
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    add_txt = st.text_area("Question Text *", placeholder="Type the MCQ question text...", key=f"addq_txt_{bank.id}")
                    aq_c1, aq_c2 = st.columns(2)
                    with aq_c1:
                        add_oa = st.text_input("Option A *", key=f"addq_oa_{bank.id}")
                        add_ob = st.text_input("Option B *", key=f"addq_ob_{bank.id}")
                    with aq_c2:
                        add_oc = st.text_input("Option C *", key=f"addq_oc_{bank.id}")
                        add_od = st.text_input("Option D *", key=f"addq_od_{bank.id}")

                    aq_m1, aq_m2 = st.columns([1, 1])
                    with aq_m1:
                        add_ans = st.selectbox("Correct Answer *", options=["A", "B", "C", "D"], key=f"addq_ans_{bank.id}")
                    with aq_m2:
                        add_diff = st.selectbox("Difficulty", options=["Easy", "Medium", "Hard"], index=1, key=f"addq_diff_{bank.id}")

                    add_exp = st.text_area("Explanation / Solution", placeholder="Why is this the correct answer?", key=f"addq_exp_{bank.id}")

                    if st.button("➕ Save Question to Bank", key=f"addq_save_{bank.id}", type="primary"):
                        if not add_txt.strip() or not add_oa.strip() or not add_ob.strip() or not add_oc.strip() or not add_od.strip():
                            st.warning("Please provide question text and all 4 options (A-D).")
                        else:
                            new_q_model = QuestionModel(
                                class_level=class_val,
                                subject=subj_val,
                                chapter=bank.name,
                                topic=bank.name,
                                question_text=add_txt.strip(),
                                option_a=add_oa.strip(),
                                option_b=add_ob.strip(),
                                option_c=add_oc.strip(),
                                option_d=add_od.strip(),
                                correct_answer=add_ans,
                                explanation=add_exp.strip() if add_exp else None,
                                difficulty=add_diff,
                                source_pdf=bank.source_pdf,
                                verification_status="VERIFIED",
                                bank_id=bank.id,
                                bank_name=bank.name,
                            )
                            QuestionRepository.create_question(new_q_model)
                            st.session_state[f"show_add_q_{bank.id}"] = False
                            st.toast(f"Added question to '{bank.name}'!")
                            st.rerun()

            # ── Sub-Panel 3: Customize Bank Details ──
            if st.session_state.get(f"show_edit_{bank.id}", False):
                with st.container():
                    st.markdown(
                        '<div style="background:rgba(91,139,255,0.05);border:1px solid rgba(91,139,255,0.2);'
                        'border-radius:12px;padding:18px 22px;margin:10px 0 16px;">'
                        '<div style="font-size:0.88rem;font-weight:600;color:#5B8BFF;margin-bottom:12px;">'
                        f'✏️ Customize Question Bank Details</div>',
                        unsafe_allow_html=True,
                    )
                    ec1, ec2, ec3 = st.columns([1.5, 1.2, 0.8])
                    with ec1:
                        edit_name = st.text_input("Question Bank Name", value=bank.name, key=f"edit_name_{bank.id}")
                    with ec2:
                        edit_subj = st.text_input("Subject Category", value=subj_val, placeholder="e.g. Chemistry, Physics, Maths", key=f"edit_subj_{bank.id}")
                    with ec3:
                        class_opts = [0, 10, 11, 12]
                        cls_idx = class_opts.index(class_val) if class_val in class_opts else 0
                        edit_class = st.selectbox("Class Level", options=class_opts, index=cls_idx, format_func=lambda x: "General (0)" if x == 0 else f"Class {x}", key=f"edit_class_{bank.id}")

                    es1, _ = st.columns([1.3, 3])
                    with es1:
                        if st.button("💾 Save Changes", key=f"save_edit_{bank.id}", type="primary", use_container_width=True):
                            if edit_name.strip():
                                ok = QuestionRepository.update_question_bank(
                                    bank_id=bank.id,
                                    new_name=edit_name.strip(),
                                    new_subject=edit_subj.strip(),
                                    new_class=edit_class,
                                )
                                if ok:
                                    st.session_state.pop(f"show_edit_{bank.id}", None)
                                    st.toast(f"Saved changes to '{edit_name.strip()}'!")
                                    st.rerun()
                                else:
                                    st.error("Could not save changes.")
                            else:
                                st.warning("Bank name cannot be empty.")
                    st.markdown('</div>', unsafe_allow_html=True)

            # ── Sub-Panel 4: Reset Progress ──
            if st.session_state.get(f"show_reset_{bank.id}", False):
                with st.container():
                    st.markdown(
                        f"""
                        <div style="background:rgba(245,158,11,0.06);border:1px solid rgba(245,158,11,0.25);
                                    border-radius:12px;padding:18px 22px;margin:10px 0 16px;">
                            <div style="font-size:0.88rem;font-weight:700;color:#F59E0B;margin-bottom:6px;">
                                🔄 Reset Practice Progress for {bank.name}?
                            </div>
                            <p style="font-size:0.82rem;color:#94A3B8;margin-bottom:14px;">
                                This will clear all your attempts, scores, and answered status on this question bank back to 0%.
                                The questions and source file remain intact.
                            </p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    rc1, _ = st.columns([1.6, 3])
                    with rc1:
                        if st.button(f"Yes, Reset Progress (0%)", key=f"confirm_rst_{bank.id}", type="primary", use_container_width=True):
                            AttemptRepository.reset_bank_attempts(user_id=1, bank_id=bank.id)
                            st.session_state.pop(f"show_reset_{bank.id}", None)
                            st.toast(f"Progress reset for {bank.name}!")
                            st.rerun()

            # ── Sub-Panel 5: Delete Bank & PDF ──
            if st.session_state.get(f"show_del_{bank.id}", False):
                with st.container():
                    st.markdown(
                        f"""
                        <div style="background:rgba(239,68,68,0.07);border:1px solid rgba(239,68,68,0.3);
                                    border-radius:12px;padding:18px 22px;margin:10px 0 16px;">
                            <div style="font-size:0.92rem;font-weight:700;color:#EF4444;margin-bottom:6px;">
                                ⚠️ Permanently Delete {bank.name}?
                            </div>
                            <p style="font-size:0.82rem;color:#CBD5E1;margin-bottom:14px;">
                                This will permanently delete this question bank, its <strong>{q_count} questions</strong>,
                                all attempt history, and remove the source file (<code>{source_pdf_display}</code>) from the uploads directory.
                                This cannot be undone.
                            </p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    dc1, _ = st.columns([1.6, 3])
                    with dc1:
                        if st.button(f"🔥 Yes, Permanently Delete", key=f"confirm_del_{bank.id}", type="primary", use_container_width=True):
                            QuestionRepository.delete_question_bank(bank.id)
                            if st.session_state.get("practice_bank_id") == bank.id:
                                st.session_state.pop("practice_bank_id", None)
                                st.session_state.pop("practice_bank_name", None)
                            st.session_state.pop(f"show_del_{bank.id}", None)
                            st.toast(f"Deleted question bank '{bank.name}'.")
                            st.rerun()

        st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)


# ╔══════════════════════════════════════════════════════════════════════╗
# ║                        UPLOAD PAGE                                    ║
# ╚══════════════════════════════════════════════════════════════════════╝

def render_upload_page(selected_bank_id=None, selected_bank_name="All Banks"):

    """Upload page — premium redesign, pipeline logic preserved."""
    _page_wrap_start()
    st.markdown('<div style="height:32px;"></div>', unsafe_allow_html=True)

    # Back button
    st.markdown('<div class="ss-btn-back">', unsafe_allow_html=True)
    if st.button("← Back to Home", key="up_back"):
        st.session_state.pop("upload_success_data", None)
        _go_to("home")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div style="height:20px;"></div>', unsafe_allow_html=True)

    # Page heading
    st.markdown(
        """
        <div style="margin-bottom:32px;">
            <h1 style="font-size:2rem;font-weight:800;color:#F1F5F9;margin-bottom:8px;">
                Scan Question Bank
            </h1>
            <p style="color:#64748B;font-size:0.95rem;">
                Turn your PDF into interactive practice — powered by AI.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_upload, tab_manage = st.tabs(["📤 Scan & Upload PDF", "📂 Manage Question Banks & PDFs"])

    with tab_upload:
        upload_col, info_col = st.columns([1.4, 0.8], gap="large")

        with upload_col:
            # Bank name input
            bank_name = st.text_input(
                "Question Bank Name",
                placeholder="e.g. Physics Revision, Chapter 1...",
                key="up_bank_name",
            )

            # File uploader
            uploaded_file = st.file_uploader(
                "Upload PDF",
                type=["pdf"],
                help="Select a PDF containing MCQs with options A/B/C/D",
                key="up_file",
                label_visibility="collapsed",
            )

            if uploaded_file:
                st.markdown(
                    f"""
                    <div style="background:rgba(91,139,255,0.06);border:1px solid rgba(91,139,255,0.2);
                                border-radius:10px;padding:12px 16px;margin:12px 0;
                                display:flex;align-items:center;gap:10px;">
                        <span style="font-size:1rem;">📄</span>
                        <div>
                            <div style="font-size:0.85rem;color:#F1F5F9;font-weight:500;">{uploaded_file.name}</div>
                            <div style="font-size:0.72rem;color:#64748B;">{round(uploaded_file.size/1024,1)} KB</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)
            st.markdown('<div class="ss-btn-p">', unsafe_allow_html=True)
            scan_btn = st.button(
                "Scan & Extract Questions →",
                key="up_scan_btn",
                use_container_width=True,
            )
            st.markdown("</div>", unsafe_allow_html=True)

            # Validation & Pipeline execution
            if scan_btn:
                if not uploaded_file:
                    st.warning("⚠️ Please upload a PDF.")
                elif not bank_name or not bank_name.strip():
                    st.warning("⚠️ Please enter a question bank name.")
                else:
                    clean_bank_name = bank_name.strip()

                    status_container = st.empty()

                    def _show_step(msg: str, icon: str = "⏳"):
                        status_container.markdown(
                            f"""
                            <div style="background:rgba(91,139,255,0.06);border:1px solid rgba(91,139,255,0.18);
                                        border-radius:12px;padding:14px 18px;margin-top:16px;">
                                <div style="font-size:0.88rem;color:#94A3B8;display:flex;align-items:center;gap:10px;">
                                    <span style="font-size:1rem;">{icon}</span> {msg}
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                    try:
                        _show_step("Reading your PDF...", "📖")
                        progress_bar = st.progress(0, text="")

                        def on_pipeline_progress(msg: str, pct: int):
                            _show_step(msg)
                            progress_bar.progress(min(max(pct / 100.0, 0.0), 1.0))

                        # Ensure question bank exists and get bank_id
                        bank_id = QuestionRepository.create_question_bank(
                            name=clean_bank_name,
                            source_pdf=getattr(uploaded_file, "name", "uploaded.pdf"),
                        )

                        # Reset stream pointer
                        if hasattr(uploaded_file, "seek"):
                            uploaded_file.seek(0)

                        result = PipelineService.process_pdf_question_bank(
                            uploaded_file=uploaded_file,
                            bank_id=bank_id,
                            bank_name=clean_bank_name,
                            target_subject="General",
                            use_ai_extraction=False,
                            progress_callback=on_pipeline_progress,
                        )
                        progress_bar.progress(1.0)
                        status_container.empty()
                        progress_bar.empty()

                        if result.get("success") and result.get("saved_count", 0) > 0 and result.get("ready_questions", 0) > 0:
                            total_ext = result.get("total_extracted", 0)
                            saved_q = result.get("saved_count", result.get("questions_saved", total_ext))
                            needs_r = result.get("review_count", result.get("needs_review", 0))
                            ready_q = result.get("verified_count", result.get("ready_questions", max(0, total_ext - needs_r)))
                            b_id = result.get("bank_id") or bank_id

                            st.session_state["upload_success_data"] = {
                                "bank_id": b_id,
                                "bank_name": clean_bank_name,
                                "total_ext": total_ext,
                                "ready_q": ready_q,
                            }
                            try:
                                st.cache_data.clear()
                            except Exception:
                                pass
                            st.rerun()
                        else:
                            err_msg = result.get("message") or "We couldn't process this question bank. Please check your PDF and try again."
                            st.error(f"❌ {err_msg}")

                    except Exception as exc:
                        logger.error(f"Upload error: {exc}", exc_info=True)
                        st.error("❌ We couldn't process this question bank. Please try again.")

            # Show Question Bank Ready card & navigation buttons (persisted across clicks)
            success_data = st.session_state.get("upload_success_data")
            if success_data:
                clean_bank_name = success_data["bank_name"]
                total_ext = success_data["total_ext"]
                ready_q = success_data["ready_q"]
                b_id = success_data["bank_id"]

                st.markdown(
                    f"""
                    <div style="background:rgba(16,185,129,0.06);border:1px solid rgba(16,185,129,0.28);
                                border-radius:16px;padding:28px 28px;margin-top:20px;text-align:center;">
                        <div style="font-size:1.8rem;margin-bottom:10px;">✅</div>
                        <h2 style="font-size:1.3rem;font-weight:700;color:#F1F5F9;margin-bottom:8px;">
                            Question Bank Ready!
                        </h2>
                        <div style="font-size:1.1rem;font-weight:600;color:#10B981;margin-bottom:20px;">
                            {clean_bank_name}
                        </div>
                        <div style="display:flex;justify-content:center;gap:32px;flex-wrap:wrap;margin-bottom:20px;">
                            <div style="text-align:center;">
                                <div style="font-size:1.8rem;font-weight:800;color:#5B8BFF;">{total_ext}</div>
                                <div style="font-size:0.72rem;color:#64748B;margin-top:2px;">Questions Found</div>
                            </div>
                            <div style="text-align:center;">
                                <div style="font-size:1.8rem;font-weight:800;color:#10B981;">{ready_q}</div>
                                <div style="font-size:0.72rem;color:#64748B;margin-top:2px;">Ready to Practice</div>
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                def _on_start_practice():
                    st.session_state.pop("upload_success_data", None)
                    st.session_state["page"] = "practice"
                    st.session_state["quiz_active"] = False
                    st.session_state["quiz_completed"] = False
                    st.session_state["quiz_model"] = None
                    st.session_state["quiz_summary"] = None
                    st.session_state["current_q_index"] = 0
                    st.session_state["user_responses"] = []
                    st.session_state["submitted_current"] = False
                    st.session_state["current_eval"] = None
                    st.session_state["practice_bank_id"] = b_id
                    st.session_state["practice_bank_name"] = clean_bank_name
                    st.session_state["qz_sel_bank"] = clean_bank_name

                def _on_back_home():
                    st.session_state.pop("upload_success_data", None)
                    st.session_state["page"] = "home"

                _, bc1, bc2, _ = st.columns([1, 1.2, 1.2, 1])
                with bc1:
                    st.markdown('<div class="ss-btn-p">', unsafe_allow_html=True)
                    if st.button("Start Practice →", key="up_start_prac", use_container_width=True, on_click=_on_start_practice):
                        _on_start_practice()
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
                with bc2:
                    st.markdown('<div class="ss-btn-s">', unsafe_allow_html=True)
                    if st.button("Back to Home", key="up_back2", use_container_width=True, on_click=_on_back_home):
                        _on_back_home()
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)

        with info_col:
            st.markdown(
                """
                <div style="background:rgba(13,21,40,0.7);border:1px solid rgba(255,255,255,0.07);
                            border-radius:16px;padding:22px;margin-top:36px;">
                    <h3 style="font-size:0.92rem;font-weight:700;color:#F1F5F9;margin-bottom:16px;">
                        How it works
                    </h3>
                    <div style="display:flex;flex-direction:column;gap:12px;">
                        <div style="display:flex;align-items:flex-start;gap:10px;">
                            <div style="width:26px;height:26px;border-radius:8px;background:rgba(91,139,255,0.15);
                                        display:flex;align-items:center;justify-content:center;font-size:0.75rem;
                                        color:#5B8BFF;font-weight:700;flex-shrink:0;">1</div>
                            <div style="font-size:0.8rem;color:#94A3B8;line-height:1.5;">
                                <strong style="color:#F1F5F9;">Upload PDF</strong><br>Any MCQ question bank document
                            </div>
                        </div>
                        <div style="display:flex;align-items:flex-start;gap:10px;">
                            <div style="width:26px;height:26px;border-radius:8px;background:rgba(168,85,247,0.15);
                                        display:flex;align-items:center;justify-content:center;font-size:0.75rem;
                                        color:#A855F7;font-weight:700;flex-shrink:0;">2</div>
                            <div style="font-size:0.8rem;color:#94A3B8;line-height:1.5;">
                                <strong style="color:#F1F5F9;">Extract Questions</strong><br>Questions and options detected
                            </div>
                        </div>
                        <div style="display:flex;align-items:flex-start;gap:10px;">
                            <div style="width:26px;height:26px;border-radius:8px;background:rgba(16,185,129,0.15);
                                        display:flex;align-items:center;justify-content:center;font-size:0.75rem;
                                        color:#10B981;font-weight:700;flex-shrink:0;">3</div>
                            <div style="font-size:0.8rem;color:#94A3B8;line-height:1.5;">
                                <strong style="color:#F1F5F9;">Start Practice</strong><br>Instant feedback with solutions
                            </div>
                        </div>
                    </div>
                    <div style="margin-top:18px;padding-top:14px;border-top:1px solid rgba(255,255,255,0.06);">
                        <div style="font-size:0.72rem;color:#475569;line-height:1.5;">
                            ✓ Standard MCQ PDF support<br>
                            ✓ Instant answer verification<br>
                            ✓ Detailed solutions<br>
                            ✓ Track progress per bank
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with tab_manage:
        render_question_banks_management(key_prefix="mg")

    _page_wrap_end()


# ╔══════════════════════════════════════════════════════════════════════╗
# ║                   QUESTION BANKS DEDICATED PAGE                      ║
# ╚══════════════════════════════════════════════════════════════════════╝

def render_question_banks_page():
    """Dedicated Question Banks & PDFs management page."""
    _page_wrap_start()
    st.markdown('<div style="height:32px;"></div>', unsafe_allow_html=True)
    st.markdown('<div class="ss-btn-back">', unsafe_allow_html=True)
    if st.button("← Back to Home", key="banks_page_back"):
        _go_to("home")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        """
        <div style="margin-bottom:24px;">
            <h1 style="font-size:2rem;font-weight:800;color:#F1F5F9;margin-bottom:8px;">
                📂 Question Banks & Uploaded PDFs
            </h1>
            <p style="color:#64748B;font-size:0.95rem;">
                Browse, customize, inspect questions, and manage all your uploaded question banks.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_question_banks_management(key_prefix="bp")
    _page_wrap_end()



# ╔══════════════════════════════════════════════════════════════════════╗
# ║                       PRACTICE / QUIZ PAGE                            ║
# ╚══════════════════════════════════════════════════════════════════════╝

def _start_next_batch_quiz(bank_id=None, bank_name="All Banks", batch_size=10):
    """Cleanly starts a practice quiz with the next batch of unattempted questions."""
    with st.spinner(f"Preparing next {batch_size} questions..."):
        quiz = QuizService.fetch_quiz_questions_by_bank(
            bank_id=bank_id,
            bank_name=bank_name,
            limit=batch_size,
            user_id=1,
        )
    if not quiz.questions:
        st.warning(f"⚠️ No questions available for {bank_name}.")
        return False

    quiz_record_id = None
    try:
        with get_db_cursor() as cursor:
            cursor.execute(
                "INSERT INTO quizzes (title, class_level, subject, total_questions) VALUES (%s, %s, %s, %s)",
                (quiz.title, quiz.class_level, quiz.subject, len(quiz.questions))
            )
            quiz_record_id = cursor.lastrowid
    except Exception as q_err:
        logger.warning(f"Could not initialize quiz session in MySQL: {q_err}")

    st.session_state.update({
        "page": "practice",
        "quiz_active": True,
        "quiz_completed": False,
        "quiz_model": quiz,
        "quiz_session_id": quiz_record_id,
        "quiz_summary": None,
        "quiz_elapsed_seconds": None,
        "current_q_index": 0,
        "user_responses": [],
        "start_time": time.time(),
        "submitted_current": False,
        "current_eval": None,
        "practice_bank_id": bank_id,
        "practice_bank_name": bank_name,
    })
    return True


def render_quiz_page(selected_bank_id=None, selected_bank_name="All Banks"):
    """Practice Quiz Engine — all quiz logic preserved, redesigned visuals."""
    _page_wrap_start()
    st.markdown('<div style="height:32px;"></div>', unsafe_allow_html=True)

    # Initialize session state keys
    for key, default in [
        ("quiz_active", False),
        ("quiz_completed", False),
        ("quiz_model", None),
        ("current_q_index", 0),
        ("user_responses", []),
        ("start_time", 0),
        ("submitted_current", False),
        ("current_eval", None),
    ]:
        if key not in st.session_state:
            st.session_state[key] = default

    # Respect bank pre-selection from home page cards
    presel_bank_id = st.session_state.pop("practice_bank_id", selected_bank_id)
    presel_bank_name = st.session_state.pop("practice_bank_name", selected_bank_name)

    # ── PHASE 1: Configuration ─────────────────────────────────────────
    if not st.session_state["quiz_active"] and not st.session_state["quiz_completed"]:

        # Back button
        st.markdown('<div class="ss-btn-back">', unsafe_allow_html=True)
        if st.button("← Home", key="qz_back"):
            _go_to("home")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div style="height:20px;"></div>', unsafe_allow_html=True)
        st.markdown(
            """
            <h1 style="font-size:1.9rem;font-weight:800;color:#F1F5F9;margin-bottom:6px;">Start Practice</h1>
            <p style="color:#64748B;font-size:0.92rem;margin-bottom:28px;">
                Choose your question bank and number of questions.
            </p>
            """,
            unsafe_allow_html=True,
        )

        banks = _get_question_banks()
        bank_options = ["All Banks"] + [b.name for b in banks]
        bank_id_map = {"All Banks": None, **{b.name: b.id for b in banks}}

        default_idx = 0
        if presel_bank_name and presel_bank_name in bank_options:
            default_idx = bank_options.index(presel_bank_name)
            st.session_state["qz_sel_bank"] = presel_bank_name
        elif "qz_sel_bank" in st.session_state and st.session_state["qz_sel_bank"] in bank_options:
            default_idx = bank_options.index(st.session_state["qz_sel_bank"])
        else:
            default_idx = 0
            st.session_state.pop("qz_sel_bank", None)

        cfg_col, info_col = st.columns([1.5, 1], gap="large")

        with cfg_col:
            sel_bank_name = st.selectbox(
                "Question Bank",
                bank_options,
                index=default_idx,
                key="qz_sel_bank",
            )
            sel_bank_id = bank_id_map.get(sel_bank_name)

            if sel_bank_name != "All Banks":
                bk = next((b for b in banks if b.name == sel_bank_name), None)
                if bk:
                    total_in_bank = bk.question_count or 0
                    done_in_bank = 0
                    try:
                        done_in_bank = AttemptRepository.get_unique_questions_attempted(
                            user_id=1, bank_id=bk.id
                        )
                    except Exception:
                        pass
                    pct = round(done_in_bank / total_in_bank * 100) if total_in_bank > 0 else 0
                    rem_in_bank = max(0, total_in_bank - done_in_bank)
                    st.markdown(
                        f"""
                        <div style="background:rgba(91,139,255,0.06);border-radius:8px;padding:10px 12px;margin:8px 0 16px;">
                            <div style="display:flex;justify-content:space-between;font-size:0.75rem;color:#64748B;margin-bottom:5px;">
                                <span>{done_in_bank} of {total_in_bank} questions attempted ({rem_in_bank} remaining)</span>
                                <span style="color:#5B8BFF;">{pct}%</span>
                            </div>
                            <div style="height:4px;background:rgba(255,255,255,0.07);border-radius:2px;">
                                <div style="height:4px;width:{pct}%;background:linear-gradient(90deg,#5B8BFF,#A855F7);border-radius:2px;"></div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    if done_in_bank > 0 and rem_in_bank > 0:
                        next_batch_cnt = min(10, rem_in_bank)
                        st.markdown('<div class="ss-btn-p" style="margin-bottom:14px;">', unsafe_allow_html=True)
                        if st.button(f"⚡ Practice Next {next_batch_cnt} Questions (Unattempted) →", key="qz_next_10_p1", use_container_width=True):
                            _start_next_batch_quiz(bk.id, bk.name, batch_size=next_batch_cnt)
                            st.rerun()
                        st.markdown("</div>", unsafe_allow_html=True)

            slider_max = 50
            if sel_bank_name != "All Banks" and bk:
                slider_max = max(5, bk.question_count or 10)
            else:
                try:
                    tot = sum(b.question_count for b in banks) if banks else QuestionRepository.get_total_questions_in_bank()
                    slider_max = max(5, tot if tot > 0 else 50)
                except Exception:
                    slider_max = 50

            question_count = st.slider(
                "Number of Questions",
                min_value=1, max_value=slider_max, value=min(10, slider_max), key="qz_count",
            )

            st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
            st.markdown('<div class="ss-btn-p">', unsafe_allow_html=True)
            if st.button("Start Practice Quiz →", key="qz_start", use_container_width=True):
                try:
                    with st.spinner("Preparing your quiz..."):
                        quiz = QuizService.fetch_quiz_questions_by_bank(
                            bank_id=sel_bank_id,
                            bank_name=sel_bank_name,
                            limit=question_count,
                            user_id=1,
                        )
                    if not quiz.questions:
                        st.warning("⚠️ No questions available for this selection. Please upload a question bank PDF first!")
                    else:
                        quiz_record_id = None
                        try:
                            with get_db_cursor() as cursor:
                                cursor.execute(
                                    "INSERT INTO quizzes (title, class_level, subject, total_questions) VALUES (%s, %s, %s, %s)",
                                    (quiz.title, quiz.class_level, quiz.subject, len(quiz.questions))
                                )
                                quiz_record_id = cursor.lastrowid
                        except Exception as q_err:
                            logger.warning(f"Could not initialize quiz session in MySQL: {q_err}")

                        st.session_state.update({
                            "quiz_active": True,
                            "quiz_completed": False,
                            "quiz_model": quiz,
                            "quiz_session_id": quiz_record_id,
                            "quiz_summary": None,
                            "current_q_index": 0,
                            "user_responses": [],
                            "start_time": time.time(),
                            "submitted_current": False,
                            "current_eval": None,
                        })
                        st.rerun()
                except Exception as err:
                    from src.utils.exceptions import DatabaseConnectionError
                    if isinstance(err, DatabaseConnectionError):
                        st.error("Database connection unavailable. Please try again shortly.")
                    else:
                        st.error(f"Error starting quiz: {err}")
            st.markdown("</div>", unsafe_allow_html=True)

        with info_col:
            st.markdown(
                """
                <div style="background:rgba(91,139,255,0.05);border:1px solid rgba(91,139,255,0.15);
                            border-radius:16px;padding:22px;margin-top:0;">
                    <div style="font-size:0.85rem;font-weight:600;color:#5B8BFF;margin-bottom:14px;">
                        Quiz Features
                    </div>
                    <div style="font-size:0.8rem;color:#94A3B8;line-height:1.8;">
                        ✓ Unattempted questions first<br>
                        ✓ Instant correct/wrong feedback<br>
                        ✓ Full answer text displayed<br>
                        ✓ Solution shown after each answer<br>
                        ✓ Progress saved to database<br>
                        ✓ Bank coverage tracked
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # ── PHASE 2: One Question at a Time ───────────────────────────────
    elif st.session_state["quiz_active"] and not st.session_state["quiz_completed"]:
        quiz = st.session_state["quiz_model"]
        curr_idx = st.session_state["current_q_index"]
        total_q = len(quiz.questions)
        q = quiz.questions[curr_idx]

        # Header row
        hc1, hc2 = st.columns([1, 1])
        with hc1:
            st.markdown('<div class="ss-btn-back">', unsafe_allow_html=True)
            if st.button("← Home", key="qz_ph2_back"):
                for k in ["quiz_active", "quiz_completed", "quiz_model", "submitted_current", "current_eval"]:
                    st.session_state[k] = False if isinstance(st.session_state.get(k), bool) else None
                _go_to("home")
            st.markdown("</div>", unsafe_allow_html=True)
        with hc2:
            bank_lbl = getattr(q, "bank_name", None) or quiz.bank_name or "Practice"
            st.markdown(
                f'<div style="text-align:right;font-size:0.82rem;color:#64748B;padding-top:8px;">'
                f'{bank_lbl}</div>',
                unsafe_allow_html=True,
            )

        # Progress indicator
        st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)
        prog_l, prog_r = st.columns([5, 1])
        with prog_l:
            st.progress((curr_idx + 1) / total_q)
        with prog_r:
            st.markdown(
                f'<div style="text-align:right;font-size:0.8rem;color:#5B8BFF;font-weight:600;padding-top:2px;">'
                f'{curr_idx + 1} / {total_q}</div>',
                unsafe_allow_html=True,
            )

        # Question card
        topic_parts = []
        if q.chapter and q.chapter not in ("General", ""):
            topic_parts.append(q.chapter)
        if q.topic and q.topic not in ("General", ""):
            topic_parts.append(q.topic)
        topic_line = " · ".join(topic_parts) if topic_parts else ""

        st.html(
            CaseStudyService.render_question_card_html(
                question_text=q.question_text,
                question_num=curr_idx + 1,
                topic_line=topic_line,
            )
        )

        # Answer options
        options_dict = q.get_options_dict()
        submitted = st.session_state["submitted_current"]
        eval_res = st.session_state.get("current_eval") or {}

        if not submitted:
            options_list = [f"{k}. {v}" for k, v in options_dict.items()]
            selected_raw = st.radio(
                "Choose your answer",
                options_list,
                index=None,
                key=f"radio_q_{curr_idx}_{q.id}",
            )

            st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
            st.markdown('<div class="ss-btn-submit">', unsafe_allow_html=True)
            if st.button("Check Answer", key=f"qz_submit_{curr_idx}", use_container_width=True):
                if not selected_raw:
                    st.warning("⚠️ Please select an answer first!")
                else:
                    sel_key = selected_raw.split(".")[0].strip()
                    eval_result = QuizService.verify_question_answer(q, sel_key)
                    st.session_state["submitted_current"] = True
                    st.session_state["current_eval"] = eval_result
                    st.session_state["user_responses"].append({
                        "question_id": q.id,
                        "question_text": q.question_text,
                        "selected_option": sel_key,
                        "correct_answer": q.correct_answer,
                        "is_correct": eval_result["is_correct"],
                        "topic_name": q.topic,
                    })

                    # Persist attempt to MySQL immediately (exactly once)
                    try:
                        att_model = AttemptModel(
                            user_id=1,
                            quiz_id=st.session_state.get("quiz_session_id"),
                            question_id=q.id,
                            selected_answer=sel_key,
                            correct_answer=q.correct_answer,
                            is_correct=eval_result["is_correct"],
                            time_taken=10,
                        )
                        AttemptRepository.record_attempt(att_model)
                        try:
                            from src.services.analytics_service import _fetch_user_attempt_logs
                            _fetch_user_attempt_logs.clear()
                        except Exception:
                            pass
                    except Exception as att_err:
                        logger.warning(f"Could not persist attempt immediately: {att_err}")

                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        else:
            # Show color-coded options (static, post-submission)
            correct_letter = eval_res.get("correct_answer", "")
            selected_letter = eval_res.get("selected_option", "")

            for letter, text in options_dict.items():
                is_correct_opt = (letter == correct_letter)
                is_wrong_sel = (letter == selected_letter and not eval_res.get("is_correct", False))
                is_correct_sel = (letter == selected_letter and eval_res.get("is_correct", False))

                if is_correct_opt or is_correct_sel:
                    border = "rgba(16,185,129,0.55)"
                    bg = "rgba(16,185,129,0.07)"
                    letter_bg = "#10B981"
                    txt_c = "#D1FAE5"
                elif is_wrong_sel:
                    border = "rgba(239,68,68,0.55)"
                    bg = "rgba(239,68,68,0.07)"
                    letter_bg = "#EF4444"
                    txt_c = "#FEE2E2"
                else:
                    border = "rgba(255,255,255,0.05)"
                    bg = "rgba(255,255,255,0.01)"
                    letter_bg = "rgba(255,255,255,0.06)"
                    txt_c = "#475569"

                st.markdown(
                    f"""
                    <div style="border:1.5px solid {border};background:{bg};border-radius:12px;
                                padding:13px 18px;margin-bottom:9px;display:flex;align-items:center;gap:13px;">
                        <div style="width:28px;height:28px;border-radius:8px;background:{letter_bg};
                                    display:flex;align-items:center;justify-content:center;
                                    font-size:0.73rem;font-weight:700;color:white;flex-shrink:0;">{letter}</div>
                        <div style="font-size:0.9rem;color:{txt_c};">{text}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # Feedback panel
            if eval_res.get("is_correct"):
                st.markdown(
                    f"""
                    <div style="background:rgba(16,185,129,0.06);border:1px solid rgba(16,185,129,0.28);
                                border-radius:14px;padding:18px 22px;margin:14px 0;">
                        <div style="font-size:1rem;font-weight:700;color:#10B981;margin-bottom:10px;">✅ Correct!</div>
                        <div style="font-size:0.85rem;color:#94A3B8;">
                            <span style="color:#64748B;">Correct Answer: </span>
                            <strong style="color:#D1FAE5;">Option {correct_letter}: {options_dict.get(correct_letter,'')}</strong>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"""
                    <div style="background:rgba(239,68,68,0.05);border:1px solid rgba(239,68,68,0.25);
                                border-radius:14px;padding:18px 22px;margin:14px 0;">
                        <div style="font-size:1rem;font-weight:700;color:#EF4444;margin-bottom:10px;">❌ Incorrect</div>
                        <div style="font-size:0.85rem;color:#94A3B8;margin-bottom:6px;">
                            <span style="color:#64748B;">Your Answer: </span>
                            <strong style="color:#FEE2E2;">Option {selected_letter}: {options_dict.get(selected_letter,'')}</strong>
                        </div>
                        <div style="font-size:0.85rem;color:#94A3B8;">
                            <span style="color:#64748B;">Correct Answer: </span>
                            <strong style="color:#D1FAE5;">Option {correct_letter}: {options_dict.get(correct_letter,'')}</strong>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # Solution / Explanation
            explanation = eval_res.get("explanation") or ""
            bad_kw = ["low confidence", "unable to determine", "held for review", "flagged for review", "processing error", "unverified"]
            if any(kw in explanation.lower() for kw in bad_kw):
                explanation = ""
            if not explanation or explanation == "No detailed explanation available.":
                explanation = "No detailed explanation is available for this question." if not eval_res.get("is_correct") else ""

            if explanation:
                st.markdown(
                    f"""
                    <div style="background:rgba(245,158,11,0.05);border:1px solid rgba(245,158,11,0.2);
                                border-radius:12px;padding:14px 18px;margin-bottom:16px;">
                        <div style="font-size:0.72rem;color:#F59E0B;font-weight:700;margin-bottom:6px;text-transform:uppercase;letter-spacing:0.4px;">
                            💡 Solution
                        </div>
                        <div style="font-size:0.88rem;color:#FDE68A;line-height:1.65;">{explanation}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            if curr_idx < total_q - 1:
                st.markdown('<div class="ss-btn-next">', unsafe_allow_html=True)
                if st.button("Next Question →", key=f"qz_next_{curr_idx}", use_container_width=True):
                    st.session_state["current_q_index"] += 1
                    st.session_state["submitted_current"] = False
                    st.session_state["current_eval"] = None
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                cq1, cq2 = st.columns([1, 1.3])
                with cq1:
                    st.markdown('<div class="ss-btn-s">', unsafe_allow_html=True)
                    if st.button("Finish Quiz →", key=f"qz_next_{curr_idx}", use_container_width=True):
                        st.session_state["quiz_active"] = False
                        st.session_state["quiz_completed"] = True
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
                with cq2:
                    st.markdown('<div class="ss-btn-p">', unsafe_allow_html=True)
                    if st.button("Finish & Next 10 Questions →", key="qz_fin_next_10", use_container_width=True):
                        elapsed_seconds = int(time.time() - st.session_state.get("start_time", time.time()))
                        try:
                            QuizService.submit_quiz_attempt(
                                quiz=quiz, user_id=1,
                                attempt_details=st.session_state.get("user_responses", []),
                                total_time_seconds=elapsed_seconds,
                                save_to_db=False,
                                quiz_record_id=st.session_state.get("quiz_session_id"),
                            )
                        except Exception as q_fin_err:
                            logger.warning(f"Error finalizing attempt: {q_fin_err}")

                        _start_next_batch_quiz(
                            bank_id=getattr(quiz, "bank_id", None),
                            bank_name=getattr(quiz, "bank_name", "All Banks"),
                            batch_size=10,
                        )
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)

    # ── PHASE 3: Completion Summary ────────────────────────────────────
    elif st.session_state["quiz_completed"]:
        quiz = st.session_state["quiz_model"]
        responses = st.session_state["user_responses"]
        elapsed_seconds = int(time.time() - st.session_state["start_time"])

        if "quiz_summary" not in st.session_state or st.session_state["quiz_summary"] is None:
            with st.spinner("Calculating your results..."):
                st.session_state["quiz_summary"] = QuizService.submit_quiz_attempt(
                    quiz=quiz, user_id=1,
                    attempt_details=responses,
                    total_time_seconds=elapsed_seconds,
                    save_to_db=False,
                    quiz_record_id=st.session_state.get("quiz_session_id"),
                )
                st.session_state["quiz_elapsed_seconds"] = elapsed_seconds

        summary = st.session_state["quiz_summary"]
        display_elapsed = st.session_state.get("quiz_elapsed_seconds", elapsed_seconds)
        mins, secs = divmod(display_elapsed, 60)
        time_str = f"{mins}m {secs}s" if mins > 0 else f"{secs}s"

        pct = summary.get("percentage", 0)
        result_color = "#10B981" if pct >= 75 else ("#F59E0B" if pct >= 50 else "#EF4444")
        mistakes_count = summary["total_questions"] - summary["correct_count"]

        st.markdown(
            f"""
            <div style="text-align:center;padding:32px 0 16px;">
                <div style="font-size:3rem;margin-bottom:10px;">🎉</div>
                <h1 style="font-size:2rem;font-weight:800;color:#F1F5F9;margin-bottom:6px;">Great Work!</h1>
                <div style="font-size:3.5rem;font-weight:900;color:{result_color};line-height:1.1;">{pct}%</div>
                <div style="font-size:0.85rem;color:#64748B;margin-top:6px;">Accuracy</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Score", f"{summary['correct_count']} / {summary['total_questions']}")
        with m2:
            st.metric("Accuracy", f"{pct}%")
        with m3:
            st.metric("Questions Practiced", summary["total_questions"])
        with m4:
            st.metric("Mistakes", mistakes_count)

        if summary.get("db_recorded", False):
            st.markdown(
                """
                <div style="background:rgba(16,185,129,0.06);border:1px solid rgba(16,185,129,0.22);
                            border-radius:10px;padding:12px 18px;margin:16px 0;text-align:center;
                            font-size:0.85rem;color:#10B981;">
                    ✅ Your quiz progress has been saved.
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Topic breakdown
        st.markdown(
            '<div style="font-size:0.95rem;font-weight:600;color:#F1F5F9;margin:20px 0 10px;">Topic Performance</div>',
            unsafe_allow_html=True,
        )
        topic_perfs = AnalyticsService.analyze_attempt_details(summary["details"])
        weak_topics = AnalyticsService.get_weak_topics(topic_perfs)

        for tp in topic_perfs:
            icon = "❌" if tp.needs_revision else "✅"
            acc_col = "#EF4444" if tp.needs_revision else "#10B981"
            st.markdown(
                f"""
                <div style="background:rgba(13,21,40,0.7);border:1px solid rgba(255,255,255,0.07);
                            border-radius:10px;padding:12px 16px;margin-bottom:8px;
                            display:flex;align-items:center;justify-content:space-between;">
                    <span style="font-size:0.85rem;color:#F1F5F9;">{icon} {tp.topic_name}</span>
                    <span style="font-size:0.85rem;font-weight:600;color:{acc_col};">
                        {tp.accuracy_percentage}% ({tp.correct_count}/{tp.total_attempted})
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        if weak_topics:
            wt_names = ", ".join([t.topic_name for t in weak_topics])
            st.markdown(
                f"""
                <div style="background:rgba(245,158,11,0.06);border:1px solid rgba(245,158,11,0.22);
                            border-radius:10px;padding:12px 16px;margin:12px 0;font-size:0.85rem;color:#FDE68A;">
                    ⚠️ Recommended revision: <strong>{wt_names}</strong>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Check remaining unattempted questions in this bank
        curr_b_id = getattr(quiz, "bank_id", None)
        curr_b_name = getattr(quiz, "bank_name", "All Banks")
        rem_unattempted = 0
        total_in_b = 0
        try:
            total_in_b = QuestionRepository.get_total_questions_in_bank(bank_id=curr_b_id)
            done_in_b = AttemptRepository.get_unique_questions_attempted(user_id=1, bank_id=curr_b_id)
            rem_unattempted = max(0, total_in_b - done_in_b)
        except Exception:
            pass

        st.markdown('<div style="height:24px;"></div>', unsafe_allow_html=True)

        if rem_unattempted > 0:
            next_batch_n = min(10, rem_unattempted)
            bank_label = curr_b_name if curr_b_name and curr_b_name != "All Banks" else "Question Bank"
            st.markdown(
                f"""
                <div style="background:rgba(91,139,255,0.07);border:1px solid rgba(91,139,255,0.25);
                            border-radius:14px;padding:20px 24px;margin-bottom:16px;display:flex;
                            align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;">
                    <div>
                        <div style="font-size:1.02rem;font-weight:700;color:#F1F5F9;">
                            Continue Practicing
                        </div>
                        <div style="font-size:0.83rem;color:#94A3B8;margin-top:3px;">
                            You have <strong style="color:#5B8BFF;">{rem_unattempted} unattempted questions</strong> remaining in <strong style="color:#F1F5F9;">{bank_label}</strong>.
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown('<div class="ss-btn-p" style="margin-bottom:18px;">', unsafe_allow_html=True)
            if st.button(f"⚡ Practice Next {next_batch_n} Questions →", key="qz_next_10_summary", use_container_width=True):
                _start_next_batch_quiz(bank_id=curr_b_id, bank_name=curr_b_name, batch_size=next_batch_n)
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown(
                f"""
                <div style="background:rgba(16,185,129,0.07);border:1px solid rgba(16,185,129,0.25);
                            border-radius:14px;padding:18px 24px;margin-bottom:16px;text-align:center;">
                    <div style="font-size:1.5rem;margin-bottom:4px;">🏆</div>
                    <div style="font-size:1.02rem;font-weight:700;color:#10B981;">
                        Question Bank Completed!
                    </div>
                    <div style="font-size:0.82rem;color:#94A3B8;margin-top:2px;">
                        You have practiced all questions in this bank.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown('<div class="ss-btn-p" style="margin-bottom:18px;">', unsafe_allow_html=True)
            if st.button(f"🔄 Practice Full Bank Again (Revision Quiz) →", key="qz_next_10_summary_rev", use_container_width=True):
                _start_next_batch_quiz(bank_id=curr_b_id, bank_name=curr_b_name, batch_size=10)
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        ab1, ab2, ab3 = st.columns(3)
        with ab1:
            st.markdown('<div class="ss-btn-s">', unsafe_allow_html=True)
            if st.button("Review Mistakes", key="qz_rev_mistakes", use_container_width=True):
                for k in ["quiz_active", "quiz_completed", "quiz_model", "quiz_summary",
                          "quiz_elapsed_seconds", "current_q_index", "user_responses",
                          "start_time", "submitted_current", "current_eval"]:
                    st.session_state.pop(k, None)
                _go_to("mistakes")
            st.markdown("</div>", unsafe_allow_html=True)
        with ab2:
            st.markdown('<div class="ss-btn-s">', unsafe_allow_html=True)
            if st.button("Practice Setup / Change Bank", key="qz_continue_prac", use_container_width=True):
                for k in ["quiz_active", "quiz_completed", "quiz_model", "quiz_summary",
                          "quiz_elapsed_seconds", "current_q_index", "user_responses",
                          "start_time", "submitted_current", "current_eval"]:
                    st.session_state.pop(k, None)
                st.session_state["practice_bank_id"] = curr_b_id
                st.session_state["practice_bank_name"] = curr_b_name
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        with ab3:
            st.markdown('<div class="ss-btn-s">', unsafe_allow_html=True)
            if st.button("Back to Home", key="qz_home", use_container_width=True):
                for k in ["quiz_active", "quiz_completed", "quiz_model", "quiz_summary",
                          "quiz_elapsed_seconds", "current_q_index", "user_responses",
                          "start_time", "submitted_current", "current_eval"]:
                    st.session_state.pop(k, None)
                _go_to("home")
            st.markdown("</div>", unsafe_allow_html=True)

    _page_wrap_end()


# ╔══════════════════════════════════════════════════════════════════════╗
# ║                       PROGRESS / ANALYTICS PAGE                       ║
# ╚══════════════════════════════════════════════════════════════════════╝

def render_analytics_page(selected_bank_id=None, selected_bank_name="All Banks"):
    """Progress & Analytics — all AnalyticsService calls preserved, redesigned UI."""
    _page_wrap_start()
    st.markdown('<div style="height:32px;"></div>', unsafe_allow_html=True)

    st.markdown('<div class="ss-btn-back">', unsafe_allow_html=True)
    if st.button("← Home", key="an_back"):
        _go_to("home")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div style="height:20px;"></div>', unsafe_allow_html=True)

    # Bank selector
    banks = _get_question_banks()
    bank_options = ["All Banks"] + [b.name for b in banks]
    bank_id_map = {b.name: b.id for b in banks}

    sel_col, _ = st.columns([1.5, 2.5])
    with sel_col:
        sel_bank = st.selectbox("Filter by Bank", bank_options, key="an_bank", index=0)
    sel_bid = bank_id_map.get(sel_bank) if sel_bank != "All Banks" else None

    st.markdown(
        f"""
        <h1 style="font-size:1.8rem;font-weight:800;color:#F1F5F9;margin:16px 0 4px;">Your Progress</h1>
        <p style="color:#64748B;font-size:0.88rem;margin-bottom:24px;">
            {'Showing data for: <strong style="color:#5B8BFF;">' + sel_bank + '</strong>' if sel_bank != 'All Banks' else 'Showing data for all question banks'}
        </p>
        """,
        unsafe_allow_html=True,
    )

    with st.spinner("Loading analytics..."):
        summary = AnalyticsService.get_overall_summary(user_id=1, bank_id=sel_bid)
        try:
            total_qs = QuestionRepository.get_total_questions_in_bank(bank_id=sel_bid)
        except Exception:
            total_qs = 0

    unique_att = summary["total_questions_attempted"]
    coverage = round(unique_att / total_qs * 100, 1) if total_qs > 0 else 0.0

    mastered = 0
    try:
        with get_db_cursor() as cur:
            if sel_bid:
                cur.execute("""
                    SELECT COUNT(DISTINCT a.question_id)
                    FROM attempts a
                    JOIN questions q ON a.question_id = q.id
                    WHERE a.user_id = 1 AND a.is_correct = 1 AND q.bank_id = %s;
                """, (sel_bid,))
            else:
                cur.execute("""
                    SELECT COUNT(DISTINCT a.question_id)
                    FROM attempts a
                    WHERE a.user_id = 1 AND a.is_correct = 1;
                """)
            row = cur.fetchone()
            if row:
                mastered = list(row.values())[0] if isinstance(row, dict) else row[0]
    except Exception:
        mastered = 0

    # Metric cards (Phase 19: Separate Completion vs Accuracy)
    mc1, mc2, mc3, mc4 = st.columns(4)
    with mc1:
        st.metric("Overall Completion", f"{coverage}%", help="Unique questions attempted ÷ Total × 100")
    with mc2:
        st.metric("Overall Accuracy", f"{summary['overall_accuracy']}%", help="Correct attempts ÷ Total attempts × 100")
    with mc3:
        st.metric("Questions Practiced", unique_att, help="Distinct questions attempted")
    with mc4:
        st.metric("Questions Mastered", mastered, help="Distinct questions answered correctly")

    # Question Bank Progress cards (Phase 19)
    if banks:
        st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)
        st.markdown('<h2 style="font-size:1.15rem;font-weight:700;color:#F1F5F9;margin:16px 0 12px;">Question Bank Progress</h2>', unsafe_allow_html=True)
        b_cols = st.columns(min(len(banks), 3), gap="small")
        for i, b in enumerate(banks):
            col = b_cols[i % min(len(banks), 3)]
            b_total = b.question_count or 0
            b_done = 0
            try:
                b_done = AttemptRepository.get_unique_questions_attempted(user_id=1, bank_id=b.id)
            except Exception:
                pass
            b_pct = round(b_done / b_total * 100) if b_total > 0 else 0
            with col:
                st.markdown(
                    f"""
                    <div style="background:rgba(13,21,40,0.8);border:1px solid rgba(255,255,255,0.07);
                                border-radius:14px;padding:16px;margin-bottom:12px;">
                        <div style="font-size:0.92rem;font-weight:600;color:#F1F5F9;margin-bottom:4px;">{b.name}</div>
                        <div style="font-size:0.75rem;color:#64748B;margin-bottom:8px;">{b_done} / {b_total} questions practiced</div>
                        <div style="height:6px;background:rgba(255,255,255,0.07);border-radius:3px;margin-bottom:6px;">
                            <div style="height:6px;width:{b_pct}%;background:linear-gradient(90deg,#5B8BFF,#A855F7);border-radius:3px;"></div>
                        </div>
                        <div style="font-size:0.72rem;color:#5B8BFF;font-weight:600;">{b_pct}% complete</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # Coverage progress bar
    if total_qs > 0:
        st.markdown(
            f'<div style="font-size:0.8rem;color:#64748B;margin:16px 0 6px;">'
            f'Current Selection Coverage: {unique_att} of {total_qs} unique questions attempted</div>',
            unsafe_allow_html=True,
        )
        st.progress(min(coverage / 100.0, 1.0))

    # Strong/Weak
    if summary["strongest_topic"] != "N/A":
        sw_l, sw_r = st.columns(2)
        with sw_l:
            st.markdown(
                f"""
                <div style="background:rgba(16,185,129,0.06);border:1px solid rgba(16,185,129,0.22);
                            border-radius:12px;padding:16px 18px;margin-top:16px;">
                    <div style="font-size:0.7rem;color:#10B981;font-weight:600;margin-bottom:6px;text-transform:uppercase;">Strongest Topic</div>
                    <div style="font-size:1rem;font-weight:600;color:#F1F5F9;">{summary['strongest_topic']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with sw_r:
            st.markdown(
                f"""
                <div style="background:rgba(239,68,68,0.05);border:1px solid rgba(239,68,68,0.2);
                            border-radius:12px;padding:16px 18px;margin-top:16px;">
                    <div style="font-size:0.7rem;color:#EF4444;font-weight:600;margin-bottom:6px;text-transform:uppercase;">Needs Attention</div>
                    <div style="font-size:1rem;font-weight:600;color:#F1F5F9;">{summary['weakest_topic']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown('<div style="height:24px;"></div>', unsafe_allow_html=True)

    # Recommendations
    recs = AnalyticsService.generate_recommendations(user_id=1, bank_id=sel_bid)
    if recs:
        st.markdown('<div style="font-size:0.9rem;font-weight:600;color:#F1F5F9;margin-bottom:10px;">💡 Recommendations</div>', unsafe_allow_html=True)
        for r in recs:
            color = "#EF4444" if ("Revise" in r or "below" in r) else ("#5B8BFF" if "Practice" in r else "#10B981")
            st.markdown(
                f'<div style="background:rgba(13,21,40,0.7);border-left:3px solid {color};border-radius:0 10px 10px 0;'
                f'padding:10px 16px;margin-bottom:8px;font-size:0.83rem;color:#94A3B8;">{r}</div>',
                unsafe_allow_html=True,
            )

    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

    # Breakdown tabs
    t1, t2, t3 = st.tabs(["Topic Performance", "Chapter Breakdown", "Subject & Difficulty"])

    with t1:
        topic_data = AnalyticsService.get_topic_accuracy_breakdown(user_id=1, bank_id=sel_bid)
        if topic_data:
            for item in topic_data:
                clr = "#10B981" if item["status"] == "Strong" else ("#F59E0B" if item["status"] == "Average" else "#EF4444")
                st.markdown(
                    f"""
                    <div style="background:rgba(13,21,40,0.7);border:1px solid rgba(255,255,255,0.06);
                                border-radius:10px;padding:12px 16px;margin-bottom:8px;
                                display:flex;align-items:center;justify-content:space-between;">
                        <div>
                            <div style="font-size:0.88rem;color:#F1F5F9;font-weight:500;">{item['topic_name']}</div>
                            <div style="font-size:0.7rem;color:#64748B;margin-top:2px;">{item['total_attempted']} attempts</div>
                        </div>
                        <div style="text-align:right;">
                            <div style="font-size:1rem;font-weight:700;color:{clr};">{item['accuracy_percentage']}%</div>
                            <div style="font-size:0.68rem;color:#475569;">{item['status']}</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("ℹ️ No topic history yet. Complete a quiz first.")

    with t2:
        ch_data = AnalyticsService.get_chapter_accuracy_breakdown(user_id=1, bank_id=sel_bid)
        if ch_data:
            rows = [{"Chapter": d["chapter_name"], "Attempted": d["total_attempted"],
                     "Correct": d["correct_count"], "Accuracy": f"{d['accuracy_percentage']}%"} for d in ch_data]
            st.dataframe(rows, width="stretch")
        else:
            st.info("ℹ️ No chapter history yet.")

    with t3:
        subj_data = AnalyticsService.get_subject_accuracy_breakdown(user_id=1, bank_id=sel_bid)
        diff_data = AnalyticsService.get_difficulty_accuracy_breakdown(user_id=1, bank_id=sel_bid)
        if subj_data:
            st.markdown('<div style="font-size:0.85rem;font-weight:600;color:#94A3B8;margin-bottom:8px;">Subject</div>', unsafe_allow_html=True)
            rows_s = [{"Subject": d["subject_name"], "Attempted": d["total_attempted"],
                       "Correct": d["correct_count"], "Accuracy": f"{d['accuracy_percentage']}%"} for d in subj_data]
            st.dataframe(rows_s, width="stretch")
        if diff_data:
            st.markdown('<div style="font-size:0.85rem;font-weight:600;color:#94A3B8;margin:12px 0 8px;">Difficulty</div>', unsafe_allow_html=True)
            for d in diff_data:
                clr = "#10B981" if d["difficulty_level"] == "Easy" else ("#F59E0B" if d["difficulty_level"] == "Medium" else "#EF4444")
                st.markdown(
                    f'<div style="background:rgba(13,21,40,0.7);border:1px solid rgba(255,255,255,0.06);border-radius:10px;'
                    f'padding:12px 16px;margin-bottom:8px;display:flex;justify-content:space-between;align-items:center;">'
                    f'<span style="color:#F1F5F9;font-size:0.88rem;">{d["difficulty_level"]}</span>'
                    f'<span style="color:{clr};font-weight:700;font-size:0.95rem;">{d["accuracy_percentage"]}%</span></div>',
                    unsafe_allow_html=True,
                )

    _page_wrap_end()


# ╔══════════════════════════════════════════════════════════════════════╗
# ║                        MISTAKES PAGE                                  ║
# ╚══════════════════════════════════════════════════════════════════════╝

def render_mistakes_page(selected_bank_id=None, selected_bank_name="All Banks"):
    """Review Mistakes — student-safe, no admin controls."""
    _page_wrap_start()
    st.markdown('<div style="height:32px;"></div>', unsafe_allow_html=True)

    st.markdown('<div class="ss-btn-back">', unsafe_allow_html=True)
    if st.button("← Home", key="mk_back"):
        _go_to("home")
    st.markdown("</div>", unsafe_allow_html=True)

    banks = _get_question_banks()
    bank_options = ["All Banks"] + [b.name for b in banks]
    bank_id_map = {b.name: b.id for b in banks}

    st.markdown('<div style="height:20px;"></div>', unsafe_allow_html=True)
    bc, _ = st.columns([1.5, 2.5])
    with bc:
        sel_bank = st.selectbox("Filter by Bank", bank_options, key="mk_bank")
    sel_bid = bank_id_map.get(sel_bank) if sel_bank != "All Banks" else None

    st.markdown(
        """
        <h1 style="font-size:1.8rem;font-weight:800;color:#F1F5F9;margin:16px 0 4px;">Review Mistakes</h1>
        <p style="color:#64748B;font-size:0.88rem;margin-bottom:24px;">
            Questions you answered incorrectly — study the correct answers and solutions.
        </p>
        """,
        unsafe_allow_html=True,
    )

    mistakes = []
    try:
        if sel_bid is not None:
            query = """
                SELECT a.selected_answer, a.correct_answer as correct_ans, a.attempted_at,
                       q.question_text, q.option_a, q.option_b, q.option_c, q.option_d,
                       q.explanation, q.topic, q.chapter, q.subject
                FROM attempts a JOIN questions q ON a.question_id = q.id
                WHERE a.user_id = 1 AND a.is_correct = 0 AND q.bank_id = %s
                ORDER BY a.attempted_at DESC LIMIT 80
            """
            with get_db_cursor() as cursor:
                cursor.execute(query, (sel_bid,))
                mistakes = cursor.fetchall() or []
        else:
            query = """
                SELECT a.selected_answer, a.correct_answer as correct_ans, a.attempted_at,
                       q.question_text, q.option_a, q.option_b, q.option_c, q.option_d,
                       q.explanation, q.topic, q.chapter, q.subject
                FROM attempts a JOIN questions q ON a.question_id = q.id
                WHERE a.user_id = 1 AND a.is_correct = 0
                ORDER BY a.attempted_at DESC LIMIT 80
            """
            with get_db_cursor() as cursor:
                cursor.execute(query)
                mistakes = cursor.fetchall() or []
    except Exception as err:
        logger.warning(f"Mistakes load error: {err}")

    if not mistakes:
        st.markdown(
            """
            <div style="background:rgba(16,185,129,0.05);border:1px solid rgba(16,185,129,0.2);
                        border-radius:16px;padding:40px;text-align:center;margin:20px 0;">
                <div style="font-size:2.5rem;margin-bottom:12px;">🎉</div>
                <h3 style="font-size:1.1rem;color:#10B981;font-weight:600;margin-bottom:8px;">No Mistakes Found!</h3>
                <p style="font-size:0.85rem;color:#64748B;">Keep practicing to maintain your perfect record.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        _, mb, _ = st.columns([2, 1.5, 2])
        with mb:
            st.markdown('<div class="ss-btn-p">', unsafe_allow_html=True)
            if st.button("Start Practice →", key="mk_empty_prac", use_container_width=True):
                _go_to("practice", practice_bank_id=sel_bid, practice_bank_name=sel_bank)
            st.markdown('</div>', unsafe_allow_html=True)
        _page_wrap_end()
        return

    st.markdown(
        f'<div style="font-size:0.82rem;color:#F59E0B;margin-bottom:16px;font-weight:500;">'
        f'⚠️ {len(mistakes)} mistake(s) to review</div>',
        unsafe_allow_html=True,
    )

    for idx, m in enumerate(mistakes, 1):
        q_text = m.get("question_text", "")
        your_ans = m.get("selected_answer", "?")
        correct = m.get("correct_ans", "?")
        expl = m.get("explanation", "") or ""
        chapter = m.get("chapter", "") or ""
        topic = m.get("topic", "") or ""

        opts = {
            "A": m.get("option_a", "") or "",
            "B": m.get("option_b", "") or "",
            "C": m.get("option_c", "") or "",
            "D": m.get("option_d", "") or "",
        }

        p_text, clean_q = CaseStudyService.split_passage_and_question(q_text)
        disp_title = clean_q[:80] if clean_q else q_text[:80]
        with st.expander(f"#{idx} — {disp_title}{'...' if len(disp_title) > 80 else ''}", expanded=False):
            if p_text:
                safe_pt = p_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
                st.html(
                    f'<div style="background:rgba(91,139,255,0.06);border-left:3px solid #5B8BFF;'
                    f'border-radius:6px;padding:10px 14px;margin-bottom:12px;font-size:0.85rem;'
                    f'color:#CBD5E1;line-height:1.6;">'
                    f'<strong style="color:#5B8BFF;">📖 Passage Context:</strong><br>{safe_pt}</div>'
                )
            safe_cq = clean_q.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
            st.html(
                f'<div style="font-size:0.95rem;color:#F1F5F9;line-height:1.6;margin-bottom:14px;">{safe_cq}</div>'
            )

            # Options
            for letter, txt in opts.items():
                if not txt:
                    continue
                if letter == correct:
                    bdr = "rgba(16,185,129,0.5)"; bg = "rgba(16,185,129,0.07)"; lbg = "#10B981"; tc = "#D1FAE5"
                elif letter == your_ans:
                    bdr = "rgba(239,68,68,0.5)"; bg = "rgba(239,68,68,0.07)"; lbg = "#EF4444"; tc = "#FEE2E2"
                else:
                    bdr = "rgba(255,255,255,0.06)"; bg = "rgba(255,255,255,0.01)"; lbg = "rgba(255,255,255,0.07)"; tc = "#475569"

                st.markdown(
                    f"""
                    <div style="border:1.5px solid {bdr};background:{bg};border-radius:10px;
                                padding:11px 16px;margin-bottom:8px;display:flex;align-items:center;gap:12px;">
                        <div style="width:26px;height:26px;border-radius:7px;background:{lbg};
                                    display:flex;align-items:center;justify-content:center;
                                    font-size:0.72rem;font-weight:700;color:white;flex-shrink:0;">{letter}</div>
                        <div style="font-size:0.88rem;color:{tc};">{txt}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # Feedback
            st.markdown(
                f"""
                <div style="background:rgba(239,68,68,0.05);border:1px solid rgba(239,68,68,0.22);
                            border-radius:10px;padding:12px 16px;margin:10px 0 8px;
                            display:flex;gap:24px;flex-wrap:wrap;">
                    <div><span style="font-size:0.7rem;color:#64748B;">Your Answer</span><br>
                         <strong style="color:#FCA5A5;">Option {your_ans}: {opts.get(your_ans,'')}</strong></div>
                    <div><span style="font-size:0.7rem;color:#64748B;">Correct Answer</span><br>
                         <strong style="color:#6EE7B7;">Option {correct}: {opts.get(correct,'')}</strong></div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if expl and expl.strip() and expl.lower() not in ("none", "null", "n/a", ""):
                st.markdown(
                    f"""
                    <div style="background:rgba(245,158,11,0.05);border:1px solid rgba(245,158,11,0.18);
                                border-radius:10px;padding:12px 16px;margin-bottom:8px;">
                        <div style="font-size:0.7rem;color:#F59E0B;font-weight:700;margin-bottom:5px;text-transform:uppercase;">💡 Solution</div>
                        <div style="font-size:0.85rem;color:#FDE68A;line-height:1.6;">{expl}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    """
                    <div style="background:rgba(245,158,11,0.04);border:1px solid rgba(245,158,11,0.15);
                                border-radius:10px;padding:10px 16px;margin-bottom:8px;">
                        <div style="font-size:0.82rem;color:#92400E;">
                            💡 No detailed explanation is available for this question.
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            if chapter or topic:
                st.caption(f"Chapter: {chapter}  |  Topic: {topic}")

    st.markdown('<div style="height:24px;"></div>', unsafe_allow_html=True)
    st.markdown('<div class="ss-btn-p" style="max-width:280px;margin:0 auto;">', unsafe_allow_html=True)
    if st.button("Practice Again →", key="mk_prac_again", use_container_width=True):
        _go_to("practice", practice_bank_id=sel_bid, practice_bank_name=sel_bank)
    st.markdown("</div>", unsafe_allow_html=True)

    _page_wrap_end()


# ╔══════════════════════════════════════════════════════════════════════╗
# ║                        HISTORY PAGE                                   ║
# ╚══════════════════════════════════════════════════════════════════════╝

def render_history_page(selected_bank_id=None, selected_bank_name="All Banks"):
    """Study History — real MySQL quiz session data."""
    _page_wrap_start()
    st.markdown('<div style="height:32px;"></div>', unsafe_allow_html=True)

    st.markdown('<div class="ss-btn-back">', unsafe_allow_html=True)
    if st.button("← Home", key="hs_back"):
        _go_to("home")
    st.markdown("</div>", unsafe_allow_html=True)

    banks = _get_question_banks()
    bank_options = ["All Banks"] + [b.name for b in banks]
    bank_id_map = {b.name: b.id for b in banks}

    st.markdown('<div style="height:20px;"></div>', unsafe_allow_html=True)
    bc, clr_col = st.columns([2, 1.2])
    with bc:
        sel_bank = st.selectbox("Filter by Bank", bank_options, key="hs_bank")
    sel_bid = bank_id_map.get(sel_bank) if sel_bank != "All Banks" else None

    with clr_col:
        st.markdown('<div style="height:28px;"></div>', unsafe_allow_html=True)
        show_clr = st.session_state.get("hs_show_clear", False)
        clr_lbl = "✖️ Cancel" if show_clr else "🗑️ Clear History..."
        if st.button(clr_lbl, key="hs_toggle_clear", use_container_width=True):
            st.session_state["hs_show_clear"] = not show_clr
            st.rerun()

    if st.session_state.get("hs_show_clear", False):
        st.markdown(
            '<div style="background:rgba(239,68,68,0.06);border:1px solid rgba(239,68,68,0.25);'
            'border-radius:12px;padding:16px 20px;margin-bottom:20px;">'
            '<div style="font-size:0.88rem;font-weight:700;color:#EF4444;margin-bottom:6px;">'
            '🗑️ Delete Quiz Attempt History</div>'
            '<p style="font-size:0.82rem;color:#94A3B8;margin-bottom:12px;">'
            'Permanently remove past quiz sessions. This action cannot be undone.'
            '</p>',
            unsafe_allow_html=True,
        )
        cc1, cc2, _ = st.columns([1.5, 1.5, 1.5])
        with cc1:
            if sel_bank != "All Banks":
                if st.button(f"Delete '{sel_bank}' History", key="hs_clr_bank", type="primary", use_container_width=True):
                    AttemptRepository.clear_history(user_id=1, bank_id=sel_bid)
                    st.session_state.pop("hs_show_clear", None)
                    st.toast(f"Deleted history for {sel_bank}!")
                    st.rerun()
            else:
                st.caption("Select a bank to delete specific history.")
        with cc2:
            if st.button("🔥 Delete ALL History", key="hs_clr_all", type="primary", use_container_width=True):
                AttemptRepository.clear_history(user_id=1, bank_id=None)
                st.session_state.pop("hs_show_clear", None)
                st.toast("Deleted all quiz history!")
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(
        """
        <h1 style="font-size:1.8rem;font-weight:800;color:#F1F5F9;margin:16px 0 4px;">Study History</h1>
        <p style="color:#64748B;font-size:0.88rem;margin-bottom:20px;">
            Select multiple sessions with checkboxes to bulk delete, or clear your history — Gmail style.
        </p>
        """,
        unsafe_allow_html=True,
    )

    with st.spinner("Loading history..."):
        history = AttemptRepository.get_quiz_history(user_id=1, bank_id=sel_bid)

    if not history:
        st.markdown(
            """
            <div style="background:rgba(13,21,40,0.6);border:1px dashed rgba(255,255,255,0.08);
                        border-radius:14px;padding:40px;text-align:center;margin-top:20px;">
                <div style="font-size:2rem;margin-bottom:10px;opacity:0.3;">📅</div>
                <h3 style="font-size:1rem;color:#94A3B8;font-weight:500;margin-bottom:8px;">No history yet</h3>
                <p style="font-size:0.82rem;color:#64748B;">Complete a practice quiz to see your sessions here.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        _, hb, _ = st.columns([2, 1.5, 2])
        with hb:
            st.markdown('<div class="ss-btn-p">', unsafe_allow_html=True)
            if st.button("Start Practice →", key="hs_empty_prac", use_container_width=True):
                _go_to("practice", practice_bank_id=sel_bid, practice_bank_name=sel_bank)
            st.markdown('</div>', unsafe_allow_html=True)
        _page_wrap_end()
        return

    # Calculate selected sessions
    selected_qids = [
        r.get("quiz_id") for r in history
        if r.get("quiz_id") and st.session_state.get(f"hs_chk_{r.get('quiz_id')}", False)
    ]
    num_selected = len(selected_qids)
    all_selected = (num_selected == len(history) and len(history) > 0)

    # ── GMAIL-STYLE ACTION TOOLBAR ─────────────────────────────────────
    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)
    tb_c1, tb_c2, tb_c3 = st.columns([2.2, 4.2, 1.6], gap="small")

    with tb_c1:
        def _on_select_all_toggle():
            new_val = st.session_state.get("hs_master_select_all", False)
            for r in history:
                qid = r.get("quiz_id")
                if qid:
                    st.session_state[f"hs_chk_{qid}"] = new_val

        st.checkbox(
            f"Select All ({len(history)})",
            value=all_selected,
            key="hs_master_select_all",
            on_change=_on_select_all_toggle,
        )

    with tb_c2:
        if num_selected > 0:
            c_badge, c_del_btn, c_desel = st.columns([1.3, 1.8, 1.1])
            with c_badge:
                st.markdown(
                    f'<div style="padding-top:6px;font-size:0.85rem;color:#5B8BFF;font-weight:700;">'
                    f'✓ {num_selected} selected</div>',
                    unsafe_allow_html=True,
                )
            with c_del_btn:
                confirm_del_batch = st.session_state.get("hs_confirm_batch_del", False)
                del_btn_text = "⚠️ Confirm?" if confirm_del_batch else f"🗑️ Delete ({num_selected})"
                if st.button(del_btn_text, key="hs_batch_del_btn", type="primary", use_container_width=True):
                    if not confirm_del_batch:
                        st.session_state["hs_confirm_batch_del"] = True
                        st.rerun()
                    else:
                        AttemptRepository.delete_quiz_sessions(selected_qids)
                        for qid in selected_qids:
                            st.session_state.pop(f"hs_chk_{qid}", None)
                        st.session_state["hs_confirm_batch_del"] = False
                        st.session_state["hs_master_select_all"] = False
                        st.toast(f"Deleted {num_selected} sessions successfully!")
                        st.rerun()
            with c_desel:
                def _do_deselect():
                    for r in history:
                        qid = r.get("quiz_id")
                        if qid:
                            st.session_state[f"hs_chk_{qid}"] = False
                    st.session_state["hs_master_select_all"] = False
                    st.session_state["hs_confirm_batch_del"] = False

                if st.button("Cancel", key="hs_cancel_select", on_click=_do_deselect):
                    _do_deselect()
                    st.rerun()
        else:
            st.session_state["hs_confirm_batch_del"] = False
            st.markdown(
                f'<div style="padding-top:6px;font-size:0.8rem;color:#64748B;">'
                f'{len(history)} total session(s) in database'
                f'</div>',
                unsafe_allow_html=True,
            )

    with tb_c3:
        pass

    st.markdown('<div style="height:6px;"></div>', unsafe_allow_html=True)

    for idx, row in enumerate(history, 1):
        quiz_date = str(row.get("quiz_date", ""))[:16]
        total = int(row.get("total_attempted") or 0)
        correct = int(row.get("correct_count") or 0)
        incorrect = int(row.get("incorrect_count") or 0)
        accuracy = float(row.get("accuracy") or 0.0)
        bank_names = row.get("bank_names") or "General"
        quiz_id = row.get("quiz_id")

        is_checked = st.session_state.get(f"hs_chk_{quiz_id}", False)
        card_bg = "rgba(91,139,255,0.08)" if is_checked else "rgba(13,21,40,0.85)"
        card_border = "1px solid rgba(91,139,255,0.4)" if is_checked else "1px solid rgba(255,255,255,0.07)"

        acc_c = "#10B981" if accuracy >= 75 else ("#F59E0B" if accuracy >= 50 else "#EF4444")

        row_chk, row_body = st.columns([0.4, 9.6], gap="small")
        with row_chk:
            st.checkbox(f"Select Session {idx}", key=f"hs_chk_{quiz_id}", label_visibility="collapsed")

        with row_body:
            st.markdown(
                f"""
                <div style="background:{card_bg};border:{card_border};
                            border-radius:12px;padding:16px 20px;margin-bottom:6px;transition:all 0.15s ease;">
                    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;">
                        <div>
                            <div style="font-size:0.7rem;color:#64748B;margin-bottom:2px;">Session #{idx}</div>
                            <div style="font-size:0.95rem;font-weight:600;color:#F1F5F9;">📚 {bank_names}</div>
                            <div style="font-size:0.72rem;color:#475569;margin-top:2px;">{quiz_date}</div>
                        </div>
                        <div style="display:flex;gap:20px;flex-wrap:wrap;align-items:center;">
                            <div style="text-align:center;">
                                <div style="font-size:0.68rem;color:#64748B;margin-bottom:2px;">Attempted</div>
                                <div style="font-size:1.3rem;font-weight:800;color:#38BDF8;">{total}</div>
                            </div>
                            <div style="text-align:center;">
                                <div style="font-size:0.68rem;color:#64748B;margin-bottom:2px;">Correct</div>
                                <div style="font-size:1.3rem;font-weight:800;color:#10B981;">{correct}</div>
                            </div>
                            <div style="text-align:center;">
                                <div style="font-size:0.68rem;color:#64748B;margin-bottom:2px;">Incorrect</div>
                                <div style="font-size:1.3rem;font-weight:800;color:#EF4444;">{incorrect}</div>
                            </div>
                            <div style="text-align:center;">
                                <div style="font-size:0.68rem;color:#64748B;margin-bottom:2px;">Accuracy</div>
                                <div style="font-size:1.3rem;font-weight:800;color:{acc_c};">{accuracy}%</div>
                            </div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Individual session delete button
            if quiz_id:
                _, del_col = st.columns([5, 1.2])
                with del_col:
                    if st.button(f"🗑️ Delete Session #{idx}", key=f"del_sess_{quiz_id}_{idx}", use_container_width=True):
                        AttemptRepository.delete_quiz_sessions([quiz_id])
                        st.session_state.pop(f"hs_chk_{quiz_id}", None)
                        st.toast(f"Deleted Session #{idx}.")
                        st.rerun()

        st.markdown('<div style="height:6px;"></div>', unsafe_allow_html=True)

    # Aggregate totals
    total_sessions = len(history)
    total_qs_done = sum(int(r.get("total_attempted") or 0) for r in history)
    total_correct = sum(int(r.get("correct_count") or 0) for r in history)
    overall_acc = round(total_correct / total_qs_done * 100, 1) if total_qs_done > 0 else 0.0

    st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)
    sc1, sc2, sc3, sc4 = st.columns(4)
    with sc1:
        st.metric("Total Sessions", total_sessions)
    with sc2:
        st.metric("Total Answered", total_qs_done)
    with sc3:
        st.metric("Total Correct", total_correct)
    with sc4:
        st.metric("Overall Accuracy", f"{overall_acc}%")

    st.markdown('<div style="height:24px;"></div>', unsafe_allow_html=True)
    st.markdown('<div class="ss-btn-p" style="max-width:280px;margin:0 auto;">', unsafe_allow_html=True)
    if st.button("Continue Practice →", key="hs_prac_again", use_container_width=True):
        _go_to("practice", practice_bank_id=sel_bid, practice_bank_name=sel_bank)
    st.markdown("</div>", unsafe_allow_html=True)

    _page_wrap_end()


# ╔══════════════════════════════════════════════════════════════════════╗
# ║                       SETTINGS PAGE                                   ║
# ╚══════════════════════════════════════════════════════════════════════╝

def render_settings_page():
    """System settings and DB status."""
    _page_wrap_start()
    st.markdown('<div style="height:32px;"></div>', unsafe_allow_html=True)

    st.markdown('<div class="ss-btn-back">', unsafe_allow_html=True)
    if st.button("← Home", key="st_back"):
        _go_to("home")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        """
        <h1 style="font-size:1.8rem;font-weight:800;color:#F1F5F9;margin:20px 0 4px;">System Settings</h1>
        <p style="color:#64748B;font-size:0.88rem;margin-bottom:28px;">Database connection status and configuration.</p>
        """,
        unsafe_allow_html=True,
    )

    try:
        db_res = DatabaseManager.test_connection()
        db_ok = db_res.get("success", False) if isinstance(db_res, dict) else bool(db_res)
    except Exception:
        db_ok = False

    db_color = "#10B981" if db_ok else "#EF4444"
    db_label = "Connected" if db_ok else "Disconnected"
    db_icon = "✅" if db_ok else "❌"

    st.markdown(
        f"""
        <div style="background:rgba(13,21,40,0.8);border:1px solid rgba(255,255,255,0.08);
                    border-radius:14px;padding:24px;margin-bottom:20px;">
            <div style="font-size:0.8rem;color:#64748B;font-weight:500;margin-bottom:14px;text-transform:uppercase;letter-spacing:0.5px;">
                MySQL Database
            </div>
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:14px;">
                <div style="font-size:1rem;">{db_icon}</div>
                <div style="font-size:1rem;font-weight:600;color:{db_color};">{db_label}</div>
            </div>
            <div style="font-size:0.8rem;color:#475569;line-height:1.8;">
                Host: {config.DB_HOST}:{config.DB_PORT}<br>
                Database: {config.DB_NAME}<br>
                Environment: {config.APP_ENV}<br>
                Version: v{config.VERSION}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if db_ok:
        try:
            total_qs = QuestionRepository.get_total_questions_in_bank()
            banks = _get_question_banks()
            st.markdown(
                f"""
                <div style="background:rgba(16,185,129,0.05);border:1px solid rgba(16,185,129,0.2);
                            border-radius:12px;padding:18px 22px;">
                    <div style="font-size:0.8rem;color:#64748B;margin-bottom:10px;font-weight:500;text-transform:uppercase;">Database Stats</div>
                    <div style="display:flex;gap:32px;flex-wrap:wrap;">
                        <div><div style="font-size:0.7rem;color:#64748B;">Question Banks</div>
                             <div style="font-size:1.4rem;font-weight:700;color:#5B8BFF;">{len(banks)}</div></div>
                        <div><div style="font-size:0.7rem;color:#64748B;">Total Questions</div>
                             <div style="font-size:1.4rem;font-weight:700;color:#A855F7;">{total_qs}</div></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        except Exception:
            pass
    else:
        st.warning("⚠️ Database connection failed. Check your configuration.")

    if getattr(config, "SHOW_ADMIN_REVIEW", False):
        st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)
        st.markdown('<div class="ss-btn-s">', unsafe_allow_html=True)
        if st.button("Question Review & Verification", key="st_review"):
            _go_to("review")
        st.markdown("</div>", unsafe_allow_html=True)

    _page_wrap_end()


# ╔══════════════════════════════════════════════════════════════════════╗
# ║               ADMIN REVIEW PAGE (conditional)                         ║
# ╚══════════════════════════════════════════════════════════════════════╝

def render_review_page():
    """Question Review & Verification — admin only."""
    _page_wrap_start()
    st.markdown('<div style="height:32px;"></div>', unsafe_allow_html=True)

    st.markdown('<div class="ss-btn-back">', unsafe_allow_html=True)
    if st.button("← Home", key="rv_back"):
        _go_to("home")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<h1 style="font-size:1.8rem;font-weight:700;color:#F1F5F9;margin:20px 0;">Question Review</h1>', unsafe_allow_html=True)

    banks = _get_question_banks()
    bank_options = ["All Banks"] + [b.name for b in banks]
    bank_id_map = {b.name: b.id for b in banks}

    sel_bank = st.selectbox("Filter by Bank", bank_options, key="rv_bank")
    sel_bid = bank_id_map.get(sel_bank) if sel_bank != "All Banks" else None

    try:
        questions = QuestionRepository.get_all_questions(bank_id=sel_bid)
        needs_review = [q for q in questions if getattr(q, "verification_status", "") == "NEEDS_REVIEW"]
        verified = [q for q in questions if getattr(q, "verification_status", "") != "NEEDS_REVIEW"]

        st.markdown(f"**{len(needs_review)} need review** | **{len(verified)} verified** | **{len(questions)} total**")

        for idx, q in enumerate(needs_review[:30], 1):
            _, clean_q = CaseStudyService.split_passage_and_question(q.question_text)
            disp_title = clean_q if clean_q else q.question_text
            with st.expander(f"#{idx} {disp_title[:70]}...", expanded=False):
                e_qt = st.text_area("Question", q.question_text, key=f"rv_qt_{idx}")
                c1, c2 = st.columns(2)
                with c1:
                    e_a = st.text_input("A", q.option_a or "", key=f"rv_a_{idx}")
                    e_c = st.text_input("C", q.option_c or "", key=f"rv_c_{idx}")
                with c2:
                    e_b = st.text_input("B", q.option_b or "", key=f"rv_b_{idx}")
                    e_d = st.text_input("D", q.option_d or "", key=f"rv_d_{idx}")
                e_ans = st.selectbox("Correct Answer", ["A", "B", "C", "D"],
                                     index=["A","B","C","D"].index(q.correct_answer) if q.correct_answer in "ABCD" else 0,
                                     key=f"rv_ans_{idx}")
                e_expl = st.text_area("Explanation", q.explanation or "", key=f"rv_expl_{idx}")

                if st.button(f"✅ Verify", key=f"rv_save_{idx}", type="primary"):
                    QuestionRepository.update_question(q.id, {
                        "question_text": e_qt, "option_a": e_a, "option_b": e_b,
                        "option_c": e_c, "option_d": e_d, "correct_answer": e_ans,
                        "explanation": e_expl, "verification_status": "VERIFIED"
                    })
                    st.success(f"Question #{idx} verified!")
                    st.rerun()
    except Exception as e:
        logger.error(f"Error loading questions: {e}", exc_info=True)
        st.error("❌ We couldn't load questions. Please try again.")

    _page_wrap_end()


# Backward compat alias
render_admin_review_page = render_review_page


# ╔══════════════════════════════════════════════════════════════════════╗
# ║                    MAIN ENTRY POINT                                   ║
# ╚══════════════════════════════════════════════════════════════════════╝

def inject_custom_css():
    """Inject master CSS (alias for backward compatibility)."""
    st.markdown(_CSS, unsafe_allow_html=True)


def render_header():
    """Backward compat — no-op in new design (navbar handles branding)."""
    pass


def render_sidebar():
    """Backward compat — returns dummy values; sidebar is removed."""
    return "🏠 Home / Dashboard", None, "All Banks"


def render_ui():
    """Main rendering entry point for the Streamlit web app UI."""
    st.set_page_config(
        page_title=config.APP_NAME,
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    # Inject master CSS
    st.markdown(_CSS, unsafe_allow_html=True)

    # Initialize navigation state
    if "page" not in st.session_state:
        st.session_state["page"] = "home"

    # Render sticky navbar (first horizontal block — CSS targets it)
    render_navbar()

    # Route to page
    page = st.session_state.get("page", "home")

    if page == "home":
        render_home_page()
    elif page == "upload":
        render_upload_page()
    elif page == "banks":
        render_question_banks_page()
    elif page == "practice":
        render_quiz_page(
            selected_bank_id=st.session_state.get("practice_bank_id"),
            selected_bank_name=st.session_state.get("practice_bank_name", "All Banks"),
        )
    elif page == "progress":
        render_analytics_page()
    elif page == "mistakes":
        render_mistakes_page()
    elif page == "history":
        render_history_page()
    elif page == "settings":
        render_settings_page()
    elif page == "review" and getattr(config, "SHOW_ADMIN_REVIEW", False):
        render_review_page()
    else:
        render_home_page()
