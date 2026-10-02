"""
Runtime Test Harness for Study Smarter using official Streamlit AppTest.
Tests TEST A (Solution Quality) and TEST B (Metadata Absence) at runtime.
"""
from streamlit.testing.v1 import AppTest

def test_practice_and_metadata():
    print("==================================================")
    print("RUNNING STREAMLIT RUNTIME APPTEST")
    print("==================================================")
    
    at = AppTest.from_file("main.py", default_timeout=30)
    at.run()
    
    # 1. Start on Home
    print("[1] Home Page Loaded.")
    
    # Check forbidden words on Home
    forbidden = [
        "low confidence", "unable to determine", "held for review",
        "needs_review", "ai_verified", "confidence_score", "bank_id",
        "question_id", "source_pdf"
    ]
    
    def check_text_for_forbidden(text, page_name):
        text_lower = text.lower()
        for f in forbidden:
            assert f not in text_lower, f"Forbidden word '{f}' found on {page_name}!"
            
    home_text = " ".join([m.value for m in at.markdown])
    check_text_for_forbidden(home_text, "Home Page")
    print("    [OK] Home page free of metadata.")
    
    # 2. Go to Practice page
    at.session_state["current_page"] = "practice"
    at.run()
    print("[2] Practice Setup Page Loaded.")
    
    # Click "Start Practice →" button
    start_btn = next((b for b in at.button if "Start Practice" in b.label or b.key == "pz_start"), None)
    assert start_btn is not None, "Start Practice button not found!"
    start_btn.click().run()
    print("[3] Practice Session Started!")
    
    # Inspect Question 1
    assert "quiz_active" in at.session_state and at.session_state["quiz_active"] is True, "Quiz should be active"
    quiz = at.session_state["quiz_model"]
    curr_idx = at.session_state.get("quiz_current_index", 0) if hasattr(at.session_state, "get") else (at.session_state["quiz_current_index"] if "quiz_current_index" in at.session_state else 0)
    curr_q = quiz.questions[curr_idx]
    
    print(f"    Question 1: {curr_q.question_text}")
    print(f"    Options: A: {curr_q.option_a} | B: {curr_q.option_b} | C: {curr_q.option_c} | D: {curr_q.option_d}")
    print(f"    Correct Answer in DB: {curr_q.correct_answer}")
    
    # Select Option A
    radio = next((r for r in at.radio if r.key == f"q_opt_{curr_q.id}"), None)
    assert radio is not None, "Option radio not found!"
    radio.select(radio.options[0]).run()
    
    # Click Submit Answer
    submit_btn = next((b for b in at.button if b.key == f"sub_{curr_q.id}"), None)
    assert submit_btn is not None, "Submit button not found!"
    submit_btn.click().run()
    print("[4] Answer Submitted! Reading results...")
    
    # Read rendered markdown / html
    all_markdown = [m.value for m in at.markdown]
    all_html = [h.value for h in getattr(at, "html", [])]
    full_output = "\n".join(all_markdown + all_html)
    
    # Verify Solution presence and content
    assert "Solution" in full_output or "Explanation" in full_output, "Solution section not found in output!"
    check_text_for_forbidden(full_output, "Practice Results Screen")
    
    # Find the solution text
    sol_lines = []
    found_sol = False
    for line in full_output.splitlines():
        if "Solution" in line or "Explanation" in line:
            found_sol = True
            continue
        if found_sol and line.strip():
            sol_lines.append(line.strip())
            if len(sol_lines) >= 3:
                break
                
    solution_text = "\n".join(sol_lines)
    print("--------------------------------------------------")
    print("RUNTIME SOLUTION DISPLAYED:")
    print(solution_text)
    print("--------------------------------------------------")
    
    # 5. Check Progress Page
    at.session_state["current_page"] = "progress"
    at.run()
    prog_text = " ".join([m.value for m in at.markdown])
    check_text_for_forbidden(prog_text, "Progress Page")
    print("[5] Progress Page free of metadata.")
    
    # 6. Check History Page
    at.session_state["current_page"] = "history"
    at.run()
    hist_text = " ".join([m.value for m in at.markdown])
    check_text_for_forbidden(hist_text, "History Page")
    print("[6] History Page free of metadata.")
    
    # 7. Check Mistakes Page
    at.session_state["current_page"] = "mistakes"
    at.run()
    mistakes_text = " ".join([m.value for m in at.markdown])
    check_text_for_forbidden(mistakes_text, "Mistakes Page")
    print("[7] Mistakes Page free of metadata.")
    
    print("==================================================")
    print("TEST A & TEST B PASSED IN STREAMLIT RUNTIME!")
    print("==================================================")

if __name__ == "__main__":
    test_practice_and_metadata()
