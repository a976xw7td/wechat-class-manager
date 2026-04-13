#!/usr/bin/env python3
"""
tests/test_classifier.py - Unit tests for Message Intent Classifier
C8 Challenge Level 3 (Gold)

Usage:
    python -m pytest tests/test_classifier.py -v
    # or
    python tests/test_classifier.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from classifier import classify, link_challenge
from challenge_linker import link as link_by_keywords


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

def make_msg(content, msg_type="text", wechat_id="user1", reply_to=None):
    return {
        "content": content,
        "type": msg_type,
        "sender": {"wechat_id": wechat_id, "nickname": wechat_id},
        "reply_to": reply_to,
    }


# ---------------------------------------------------------------------------
# classify() tests
# ---------------------------------------------------------------------------

def test_submission_jielong():
    msg = make_msg("#接龙\n1. 张三 - abc123 - 5 repos")
    assert classify(msg) == "submission"

def test_submission_explicit():
    msg = make_msg("C5 提交：这是我的 GitHub 主页")
    assert classify(msg) == "submission"

def test_submission_file_upload():
    msg = make_msg("C3 作业.pdf", msg_type="file")
    # file type + challenge ref → submission
    assert classify(msg) == "submission"

def test_question_mark():
    msg = make_msg("C5 的仓库名格式是什么？")
    assert classify(msg) == "question"

def test_question_howto():
    msg = make_msg("怎么设置 SSH key？")
    assert classify(msg) == "question"

def test_announcement_at_all():
    # Note: submission patterns are checked first; @所有人 without submission keywords → announcement
    msg = make_msg("@所有人 本周班会时间为周四晚 8 点，请大家准时参加")
    assert classify(msg) == "announcement"

def test_announcement_deadline():
    msg = make_msg("截止时间是今晚 24 点，请大家注意")
    assert classify(msg) == "announcement"

def test_resource_link():
    msg = make_msg("参考这个链接 https://docs.github.com/pages")
    assert classify(msg) == "resource"

def test_answer_reply():
    msg = make_msg("是的，用 username.github.io 格式就可以", reply_to="msg_001")
    assert classify(msg) == "answer"

def test_system_message():
    msg = make_msg("某某加入了群聊", msg_type="system")
    assert classify(msg) == "system"

def test_discussion_long_text():
    msg = make_msg("我觉得用 GitHub Pages 来展示项目挺好的，比较直观")
    assert classify(msg) == "discussion"

def test_social_short():
    msg = make_msg("好的")
    assert classify(msg) == "social"


# ---------------------------------------------------------------------------
# link_challenge() tests
# ---------------------------------------------------------------------------

def test_link_explicit_c5():
    assert link_challenge("C5 提交完成") == "C5"

def test_link_explicit_c8():
    assert link_challenge("这是 C8 的最终提交") == "C8"

def test_link_keyword_github():
    # challenge_linker.link() does keyword matching for C5 (github/repo keywords)
    msg = {"content": "我的 github repo 已经上传", "challenge_ref": None}
    assert link_by_keywords(msg) == "C5"

def test_link_keyword_api():
    # challenge_linker.link() does keyword matching for C2 (api/openai keywords)
    msg = {"content": "用 openai api 接入成功了", "challenge_ref": None}
    assert link_by_keywords(msg) == "C2"

def test_link_none():
    assert link_challenge("今天天气不错") is None


# ---------------------------------------------------------------------------
# Fixture-based integration test
# ---------------------------------------------------------------------------

def test_fixture_classification():
    fixture_path = Path(__file__).parent / "fixtures" / "sample_messages.jsonl"
    if not fixture_path.exists():
        print("  [SKIP] fixture file not found")
        return

    messages = [json.loads(l) for l in fixture_path.read_text().splitlines() if l.strip()]
    results = [classify(m) for m in messages]

    # Basic sanity: all results are valid labels
    valid_labels = {"submission", "question", "answer", "discussion",
                    "announcement", "resource", "social", "system"}
    for r in results:
        assert r in valid_labels, f"Unknown label: {r}"

    # At least 1 question in the fixture (fixture has several question messages)
    assert "question" in results, "Expected at least one question in fixture"
    print(f"  [OK] {len(messages)} fixture messages classified, labels: {set(results)}")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    tests = [
        test_submission_jielong,
        test_submission_explicit,
        test_submission_file_upload,
        test_question_mark,
        test_question_howto,
        test_announcement_at_all,
        test_announcement_deadline,
        test_resource_link,
        test_answer_reply,
        test_system_message,
        test_discussion_long_text,
        test_social_short,
        test_link_explicit_c5,
        test_link_explicit_c8,
        test_link_keyword_github,
        test_link_keyword_api,
        test_link_none,
        test_fixture_classification,
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
