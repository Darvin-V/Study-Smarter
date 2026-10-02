from streamlit.testing.v1 import AppTest

at = AppTest.from_string('''
import streamlit as st

curr_idx = 0
passage_text = "On her birth day, Seema decided to donate some money to children."
clean_q = "The equation of the plane passing through the points A, B and C is"
topic_line = "Three Dimensional Geometry"

with st.container():
    st.markdown(
        f'<div style="font-size:0.70rem;color:#5B8BFF;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:10px;">'
        f'Question {curr_idx + 1}</div>',
        unsafe_allow_html=True,
    )
    if passage_text:
        st.markdown(
            f'<div style="background:rgba(91,139,255,0.06);border:1px solid rgba(91,139,255,0.2);border-left:4px solid #5B8BFF;border-radius:10px;padding:14px 18px;margin-bottom:16px;">'
            f'<div style="font-size:0.75rem;font-weight:700;color:#5B8BFF;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:8px;display:flex;align-items:center;gap:6px;">'
            f'<span>📖</span> <span>Case / Context Passage</span></div>'
            f'<div style="font-size:0.92rem;color:#E2E8F0;line-height:1.68;white-space:pre-line;">{passage_text}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    st.markdown(
        f'<div style="font-size:1.08rem;font-weight:600;color:#F1F5F9;line-height:1.6;margin-bottom:8px;">'
        f'{clean_q}</div>',
        unsafe_allow_html=True,
    )
    if topic_line:
        st.markdown(
            f'<div style="font-size:0.74rem;color:#64748B;margin-bottom:20px;">{topic_line}</div>',
            unsafe_allow_html=True,
        )
''')
at.run()
print("Total markdown elements:", len(at.markdown))
for i, m in enumerate(at.markdown):
    print(f"MD #{i}: {repr(m.value)}")
