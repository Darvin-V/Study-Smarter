import sys
import io
sys.stdout.reconfigure(encoding='utf-8')
from streamlit.testing.v1 import AppTest

def run():
    print("Testing AppTest on Practice page...")
    at = AppTest.from_file("main.py", default_timeout=30)
    at.session_state["page"] = "practice"
    at.run()
    
    print("Buttons found:")
    for b in at.button:
        try:
            print(f"  Key: {b.key}, Label: {b.label}")
        except Exception:
            pass
            
    # Find start practice button
    start_btn = next((b for b in at.button if b.key == "pz_start"), None)
    if not start_btn:
        start_btn = next((b for b in at.button if "Start Practice" in str(b.label)), None)
    print("Found start_btn:", start_btn.key if start_btn else None)
    
    if start_btn:
        start_btn.click().run()
        print("Quiz active?", at.session_state["quiz_active"])
        quiz = at.session_state["quiz_model"]
        print(f"Loaded {len(quiz.questions)} questions in quiz!")
        q1 = quiz.questions[0]
        print(f"Q1: {q1.question_text}")
        print(f"Options: A: {q1.option_a}, B: {q1.option_b}")
        
        # Select answer
        radio = next((r for r in at.radio if r.key == f"radio_q_0_{q1.id}"), None)
        print("Found radio:", radio.key if radio else None)
        if radio:
            # Pick an option that is definitely not correct
            wrong_opt = [opt for opt in radio.options if not opt.startswith(q1.correct_answer)][0]
            radio.set_value(wrong_opt).run()
            submit_btn = next((b for b in at.button if b.key == "qz_submit_0"), None)
            print("Found submit_btn:", submit_btn.key if submit_btn else None)
            if submit_btn:
                submit_btn.click().run()
                print("Submitted Wrong Answer!")
                for m in at.markdown:
                    val = str(m.value)
                    if "Solution" in val or "💡" in val or "Correct" in val or "Incorrect" in val or "Your Answer" in val:
                        print("Markdown element:\n", val)

if __name__ == "__main__":
    run()
