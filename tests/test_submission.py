#!/usr/bin/env python3
"""
tests/test_submission.py - Unit tests for Submission Detector
C8 Challenge Level 3 (Gold)

Usage:
    python -m pytest tests/test_submission.py -v
    # or
    python tests/test_submission.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from submission_detector import is_submission, extract_level


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

def make_msg(content, intent="", msg_type="text", challenge_ref=None):
    return {
        "content": content,
        "intent": intent,
        "type": msg_type,
        "challenge_ref": challenge_ref,
        "sender": {"wechat_id": "student1", "nickname": "张三"},
    }


# ---------------------------------------------------------------------------
# is_submission() tests
# ---------------------------------------------------------------------------

def test_submission_by_intent():
    msg = make_msg("这是我的作业", intent="submission")
    assert is_submission(msg) is True

def test_submission_jielong():
    # classifier.py sets intent="submission" for #接龙; is_submission() trusts that label
    msg = make_msg("#接龙\n1. 张三 - abc123 - 5 repos", intent="submission")
    assert is_submission(msg) is True

def test_submission_file_with_ref():
    # file type + explicit C-ref in content (ASCII-only) → submission
    msg = make_msg("C5.pdf", msg_type="file", challenge_ref="C5")
    assert is_submission(msg) is True

def test_submission_text_with_file_and_ref():
    msg = make_msg("提交 C8 代码：wechat_bridge.py 已完成")
    assert is_submission(msg) is True

def test_not_submission_plain_question():
    msg = make_msg("请问 C5 怎么做？", intent="question")
    assert is_submission(msg) is False

def test_not_submission_discussion():
    msg = make_msg("我觉得 GitHub 很有用", intent="discussion")
    assert is_submission(msg) is False

def test_not_submission_empty():
    msg = make_msg("", intent="social")
    assert is_submission(msg) is False

def test_submission_completed_keyword():
    # "已完成" triggers classifier's SUBMISSION_PATTERNS → intent="submission"
    msg = make_msg("已完成 C5 挑战！", intent="submission")
    assert is_submission(msg) is True

def test_submission_level_keyword():
    # Level/Bronze/Silver/Gold/Platinum in content → classifier sets intent="submission"
    msg = make_msg("Silver Level 提交", intent="submission")
    assert is_submission(msg) is True


# ---------------------------------------------------------------------------
# extract_level() tests
# ---------------------------------------------------------------------------

def test_extract_bronze():
    assert extract_level("Bronze level 完成") == "Bronze"

def test_extract_silver():
    assert extract_level("我完成了 Silver") == "Silver"

def test_extract_gold():
    assert extract_level("Gold 提交") == "Gold"

def test_extract_platinum():
    assert extract_level("Platinum 级别") == "Platinum"

def test_extract_level_number():
    assert extract_level("Level 2 完成") == "Silver"

def test_extract_none():
    assert extract_level("普通消息，无级别") is None


# ---------------------------------------------------------------------------
# Integration: fixture-based test
# ---------------------------------------------------------------------------

def test_fixture_detect_submissions():
    fixture_path = Path(__file__).parent / "fixtures" / "classified.jsonl"
    if not fixture_path.exists():
        print("  [SKIP] classified fixture not found")
        return

    messages = [json.loads(l) for l in fixture_path.read_text().splitlines() if l.strip()]
    submissions = [m for m in messages if is_submission(m)]

    print(f"  [OK] {len(submissions)}/{len(messages)} messages detected as submissions")
    # Fixture should have at least 1 submission
    assert len(submissions) >= 1, "Expected at least 1 submission in fixture"


def test_fixture_submission_has_challenge_ref():
    fixture_path = Path(__file__).parent / "fixtures" / "linked.jsonl"
    if not fixture_path.exists():
        print("  [SKIP] linked fixture not found")
        return

    messages = [json.loads(l) for l in fixture_path.read_text().splitlines() if l.strip()]
    submissions = [m for m in messages if m.get("intent") == "submission"]
    with_ref = [m for m in submissions if m.get("challenge_ref")]

    print(f"  [OK] {len(with_ref)}/{len(submissions)} submissions have challenge_ref")
    if submissions:
        ratio = len(with_ref) / len(submissions)
        assert ratio >= 0.5, f"Expected ≥50% of submissions to have challenge_ref, got {ratio:.0%}"


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    tests = [
        test_submission_by_intent,
        test_submission_jielong,
        test_submission_file_with_ref,
        test_submission_text_with_file_and_ref,
        test_not_submission_plain_question,
        test_not_submission_discussion,
        test_not_submission_empty,
        test_submission_completed_keyword,
        test_submission_level_keyword,
        test_extract_bronze,
        test_extract_silver,
        test_extract_gold,
        test_extract_platinum,
        test_extract_level_number,
        test_extract_none,
        test_fixture_detect_submissions,
        test_fixture_submission_has_challenge_ref,
    ]

    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL  {t.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR {t.__name__}: {e}")
            failed += 1

    print(f"\n{passed} passed, {failed} failed out of {len(tests)} tests")
    sys.exit(0 if failed == 0 else 1)
