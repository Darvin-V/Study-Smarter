"""
Study Smarter - Programmatic Streamlit UI & Navigation Test
Validates that:
1. The old sidebar is completely gone (zero sidebar elements).
2. Session-state navigation works across all pages (home, upload, practice, progress, mistakes, history).
3. The new UI renders error-free on startup and through all transitions.
"""

from streamlit.testing.v1 import AppTest


def test_complete_streamlit_navigation_flow():
    print("=" * 65)
    print("  STUDY SMARTER - STREAMLIT PROGRAMMATIC UI NAVIGATION AUDIT")
    print("=" * 65)

    at = AppTest.from_file("main.py", default_timeout=35)
    at.run()
    assert not at.exception, f"Startup Exception: {at.exception}"
    print("[1/7] App Launched cleanly. Home page verified.")

    # Phase 1 & 12 Check: Confirm sidebar is completely empty (no widgets rendered)
    assert len(at.sidebar) == 0, f"Sidebar has {len(at.sidebar)} elements! Expected 0."
    print("[2/7] Sidebar Verification: ZERO sidebar elements rendered (PASS).")

    # Check that Home page widgets and content exist
    assert at.session_state["page"] == "home"
    button_labels = [b.label for b in at.button]
    assert "Home" in button_labels
    assert "Progress" in button_labels
    assert "History" in button_labels
    print("[3/7] Top Navbar rendered: Home, Progress, History verified.")

    # Test navigation to Upload page
    at.session_state["page"] = "upload"
    at.run()
    assert not at.exception, f"Upload Page Exception: {at.exception}"
    print("[4/7] Upload Page ('upload') navigated cleanly.")

    # Test navigation to Practice page
    at.session_state["page"] = "practice"
    at.run()
    assert not at.exception, f"Practice Page Exception: {at.exception}"
    print("[5/7] Practice Page ('practice') navigated cleanly.")

    # Test navigation to Progress page
    at.session_state["page"] = "progress"
    at.run()
    assert not at.exception, f"Progress Page Exception: {at.exception}"
    print("[6/7] Progress Page ('progress') navigated cleanly.")

    # Test navigation to Mistakes and History pages
    at.session_state["page"] = "mistakes"
    at.run()
    assert not at.exception, f"Mistakes Page Exception: {at.exception}"

    at.session_state["page"] = "history"
    at.run()
    assert not at.exception, f"History Page Exception: {at.exception}"

    # Return to Home
    at.session_state["page"] = "home"
    at.run()
    assert not at.exception, f"Home Return Exception: {at.exception}"
    assert len(at.sidebar) == 0
    print("[7/7] Mistakes, History, and return to Home all passed cleanly.")

    print("\n" + "=" * 65)
    print("[SUCCESS] ALL PROGRAMMATIC STREAMLIT UI NAVIGATION AUDITS PASSED!")
    print("=" * 65)


if __name__ == "__main__":
    test_complete_streamlit_navigation_flow()
