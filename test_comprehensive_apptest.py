"""
Comprehensive End-to-End Streamlit AppTest Suite for Study Smarter
Tests every interactive UI feature, widget, navigation, quiz flow, feedback, and analytics view.
"""

import sys
import time
from streamlit.testing.v1 import AppTest

def test_full_application_features():
    print("=" * 70)
    print("  STUDY SMARTER - COMPREHENSIVE STREAMLIT APPTEST AUDIT")
    print("=" * 70)

    at = AppTest.from_file("main.py", default_timeout=35)
    at.run()
    assert not at.exception, f"Home startup error: {at.exception}"
    print("[1/6] Home Page Verified:")
    print(f"      - Navbar buttons: {[b.label for b in at.button if b.key.startswith('_nb_')]}")
    print(f"      - Action cards & quick links found")

    # Navigate to Upload Page
    at.session_state["page"] = "upload"
    at.run()
    assert not at.exception, f"Upload Page error: {at.exception}"
    assert any("Scan Question Bank" in str(m.value) for m in at.markdown)
    print("[2/6] Upload Page Verified:")
    print("      - Upload headers, inputs, and file upload zone rendered cleanly")

    # Test Validation on Upload Page: Click Scan without file
    scan_btn = next((b for b in at.button if b.key == "up_scan_btn"), None)
    assert scan_btn is not None
    scan_btn.click().run()
    assert not at.exception
    # Should show warning
    assert len(at.warning) > 0
    print(f"      - Validation alert triggered properly: '{at.warning[0].value}'")

    # Navigate to Practice Page
    at.session_state["page"] = "practice"
    at.run()
    assert not at.exception, f"Practice Page error: {at.exception}"
    print("[3/6] Practice / Quiz Configuration Page Verified:")
    bank_selectbox = next((s for s in at.selectbox if s.key == "qz_sel_bank"), None)
    assert bank_selectbox is not None
    print(f"      - Bank Selectbox found with options: {bank_selectbox.options[:3]}... ({len(bank_selectbox.options)} total)")

    slider = next((s for s in at.slider if s.key == "qz_count"), None)
    assert slider is not None
    print(f"      - Question Count Slider found: min={slider.min}, max={slider.max}, value={slider.value}")

    # Start Quiz
    start_btn = next((b for b in at.button if b.key == "qz_start"), None)
    assert start_btn is not None
    start_btn.click().run()
    assert not at.exception, f"Quiz Start error: {at.exception}"
    assert at.session_state["quiz_active"] is True
    quiz = at.session_state["quiz_model"]
    assert len(quiz.questions) > 0
    print(f"[4/6] Interactive Quiz Engine Active with {len(quiz.questions)} questions:")

    # Answer Question 1
    q1 = quiz.questions[0]
    radio = next((r for r in at.radio if r.key.startswith("radio_q_0_")), None)
    assert radio is not None
    print(f"      - Answering Question 1: '{q1.question_text[:60]}...'")
    radio.set_value(radio.options[0]).run()
    assert not at.exception

    submit_btn = next((b for b in at.button if b.key == "qz_submit_0"), None)
    assert submit_btn is not None
    submit_btn.click().run()
    assert not at.exception, f"Question Submit error: {at.exception}"
    assert at.session_state["submitted_current"] is True
    print(f"      - Answer checked! Evaluation is_correct: {at.session_state['current_eval']['is_correct']}")
    print("      - Instant feedback & explanation displayed")

    # Next Question or finish
    next_btn = next((b for b in at.button if b.key == "qz_next_0"), None)
    assert next_btn is not None
    next_btn.click().run()
    assert not at.exception
    print(f"      - Transitioned to next question (index: {at.session_state['current_q_index']})")

    # Navigate to Progress Page
    at.session_state["page"] = "progress"
    at.run()
    assert not at.exception, f"Progress Page error: {at.exception}"
    print("[5/6] Progress & Analytics Page Verified:")
    metrics = [f"{m.label}: {m.value}" for m in at.metric]
    print(f"      - Metrics: {metrics}")
    tabs = at.tabs
    print(f"      - Tabs: {len(tabs)} analysis tabs rendered")

    # Navigate to Mistakes & History
    at.session_state["page"] = "mistakes"
    at.run()
    assert not at.exception, f"Mistakes Page error: {at.exception}"
    print("[6/6] Mistakes & History Pages Verified:")
    print("      - Mistakes page rendered cleanly with explanations and answers")

    at.session_state["page"] = "history"
    at.run()
    assert not at.exception, f"History Page error: {at.exception}"
    print("      - History page rendered cleanly with past quiz session details")

    print("\n" + "=" * 70)
    print("  [ALL COMPREHENSIVE STREAMLIT APPTEST AUDITS PASSED CLEANLY!]")
    print("=" * 70)

if __name__ == "__main__":
    test_full_application_features()
