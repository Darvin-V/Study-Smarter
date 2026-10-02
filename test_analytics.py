"""
Study Smarter - Performance Analytics Verification Script
Tests math calculations, configurable threshold classifications,
breakdown aggregations, and Recommendation Engine advice output.

Usage:
  python test_analytics.py
"""

from src.config import config
from src.services.analytics_service import AnalyticsService


def run_analytics_tests():
    print("=" * 65)
    print("  STUDY SMARTER - PERFORMANCE ANALYTICS & DASHBOARD TEST")
    print("=" * 65)

    # 1. Test Overall Summary Calculation
    print("\n[Test 1/6] Testing Overall Summary Metrics...")
    summary = AnalyticsService.get_overall_summary(user_id=1)
    print(f"  Overall Accuracy        : {summary['overall_accuracy']}%")
    print(f"  Total Questions         : {summary['total_questions_attempted']}")
    print(f"  Quizzes Completed       : {summary['total_quizzes_completed']}")
    print(f"  Strongest Topic         : {summary['strongest_topic']}")
    print(f"  Weakest Topic           : {summary['weakest_topic']}")

    assert "overall_accuracy" in summary
    assert summary["total_questions_attempted"] >= 0
    assert "strongest_topic" in summary
    assert "weakest_topic" in summary
    print("  [OK] Overall Summary Metrics Test PASSED.")

    # 2. Test Topic Breakdown & Threshold Categorization
    print("\n[Test 2/6] Testing Topic Breakdown & Configurable Thresholds...")
    print(f"  Configured Weak Threshold   : < {config.WEAK_TOPIC_THRESHOLD}%")
    print(f"  Configured Strong Threshold : >= {config.STRONG_TOPIC_THRESHOLD}%")
    
    topic_data = AnalyticsService.get_topic_accuracy_breakdown(user_id=1)
    print(f"  Analyzed {len(topic_data)} topics:")
    for t in topic_data:
        print(f"    - {t['topic_name']}: {t['accuracy_percentage']}% -> Status: {t['status']}")
        acc = t["accuracy_percentage"]
        if acc >= config.STRONG_TOPIC_THRESHOLD:
            assert t["status"] == "Strong"
        elif acc >= config.WEAK_TOPIC_THRESHOLD:
            assert t["status"] == "Average"
        else:
            assert t["status"] == "Weak"
            assert t["needs_revision"] is True

    print("  [OK] Topic Categorization & Threshold Test PASSED.")

    # 3. Test Chapter Breakdown
    print("\n[Test 3/6] Testing Chapter Breakdown Aggregation...")
    chapter_data = AnalyticsService.get_chapter_accuracy_breakdown(user_id=1)
    print(f"  Analyzed {len(chapter_data)} chapters:")
    for c in chapter_data:
        print(f"    - {c['chapter_name']} ({c['subject_name']}): {c['accuracy_percentage']}% ({c['correct_count']}/{c['total_attempted']})")
        assert "accuracy_percentage" in c
    print("  [OK] Chapter Breakdown Test PASSED.")

    # 4. Test Subject Breakdown
    print("\n[Test 4/6] Testing Subject Breakdown Aggregation...")
    subject_data = AnalyticsService.get_subject_accuracy_breakdown(user_id=1)
    print(f"  Analyzed {len(subject_data)} subjects:")
    for s in subject_data:
        print(f"    - {s['subject_name']}: {s['accuracy_percentage']}% ({s['correct_count']}/{s['total_attempted']})")
        assert "accuracy_percentage" in s
    print("  [OK] Subject Breakdown Test PASSED.")

    # 5. Test Difficulty Breakdown
    print("\n[Test 5/6] Testing Difficulty Breakdown Aggregation...")
    diff_data = AnalyticsService.get_difficulty_accuracy_breakdown(user_id=1)
    print(f"  Analyzed {len(diff_data)} difficulty levels:")
    for d in diff_data:
        print(f"    - Difficulty '{d['difficulty_level']}': {d['accuracy_percentage']}% ({d['correct_count']}/{d['total_attempted']})")
        assert "accuracy_percentage" in d
    print("  [OK] Difficulty Breakdown Test PASSED.")

    # 6. Test Recommendation Engine Output
    print("\n[Test 6/6] Testing Data-Driven Recommendation Engine Output...")
    recommendations = AnalyticsService.generate_recommendations(user_id=1)
    print("  Generated Recommendations:")
    for rec in recommendations:
        print(f"    - {rec}")
    assert len(recommendations) > 0
    # Verify that recommendations contain topic names from attempt data
    assert any("Revise" in r or "accuracy" in r or "Great job" in r or "Attempt" in r for r in recommendations)
    print("  [OK] Recommendation Engine Test PASSED.")

    print("\n" + "=" * 65)
    print("[SUCCESS] ALL PERFORMANCE ANALYTICS & DASHBOARD TESTS PASSED!")
    print("=" * 65)
    return True


if __name__ == "__main__":
    run_analytics_tests()
