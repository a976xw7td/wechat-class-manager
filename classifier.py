#!/usr/bin/env python3
"""
classifier.py - Message Intent Classifier
C8 Challenge Level 2 (Silver)

Classifies each message into one of:
  submission, question, answer, discussion, announcement, resource, social

Usage:
    python classifier.py --input messages.jsonl --output classified.jsonl
"""

import argparse
import json
import re
import sys


# ---------------------------------------------------------------------------
# Rule-based classifier
# ---------------------------------------------------------------------------

SUBMISSION_PATTERNS = [
    r"#接龙", r"提交", r"完成了", r"已完成", r"上传", r"我的作业",
    r"这是我的", r"这是我做的", r"C\d[A-Z]?\s*(提交|完成|上传)",
    r"\.(py|md|pdf|zip|ipynb|js|html)\b",
    r"Level\s*[1-4]", r"Bronze|Silver|Gold|Platinum",
]

QUESTION_PATTERNS = [
    r"[？?]", r"怎么", r"如何", r"为什么", r"什么是", r"请问",
    r"有没有", r"能不能", r"可以吗", r"帮我", r"求助", r"不懂",
    r"不会", r"报错", r"error", r"Error", r"issue", r"问题",
]

ANNOUNCEMENT_PATTERNS = [
    r"@所有人", r"通知", r"公告", r"deadline", r"截止", r"明天",
    r"今天", r"请大家", r"提醒", r"注意", r"重要", r"必须",
    r"作业要求", r"提交格式",
]

RESOURCE_PATTERNS = [
    r"http[s]?://", r"github\.com", r"分享", r"推荐", r"资料",
    r"文档", r"教程", r"链接", r"参考", r"\[链接", r"\[文件",
]

ANSWER_SIGNAL = r"↳|回复|是的|对的|没错|可以|不行|不能|应该|建议"

CHALLENGE_REF = r"\bC[1-8][A-Z]?\b"


def classify(msg: dict) -> str:
    """Return intent label for a message."""
    content = msg.get("content", "") or ""
    msg_type = msg.get("type", "text")
    sender = (msg.get("sender") or {}).get("wechat_id", "")

    # System messages are always system
    if msg_type == "system" or sender == "system":
        return "system"

    # File uploads are likely submissions
    if msg_type in ("file", "image") and re.search(CHALLENGE_REF, content, re.I):
        return "submission"

    # Check submission patterns
    if any(re.search(p, content, re.I) for p in SUBMISSION_PATTERNS):
        return "submission"

    # Check announcement patterns (teacher/admin messages)
    if any(re.search(p, content) for p in ANNOUNCEMENT_PATTERNS):
        return "announcement"

    # Check question patterns
    if any(re.search(p, content) for p in QUESTION_PATTERNS):
        return "question"

    # Check answer patterns (reply context)
    if msg.get("reply_to") or re.search(ANSWER_SIGNAL, content):
        return "answer"

    # Check resource patterns
    if any(re.search(p, content, re.I) for p in RESOURCE_PATTERNS):
        return "resource"

    # Multi-turn text without clear signal → discussion
    if len(content) > 20 and msg_type == "text":
        return "discussion"

    return "social"


def link_challenge(content: str) -> str | None:
    """Extract challenge reference from message content."""
    match = re.search(r"\b(C[1-8][A-Z]?)\b", content, re.I)
    return match.group(1).upper() if match else None


def main():
    parser = argparse.ArgumentParser(description="Message Intent Classifier")
    parser.add_argument("--input", default="messages.jsonl", help="Input JSONL file")
    parser.add_argument("--output", default="classified.jsonl", help="Output JSONL file")
    args = parser.parse_args()

    messages = []
    try:
        with open(args.input, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    messages.append(json.loads(line))
    except FileNotFoundError:
        print(f"[ERROR] Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    label_counts: dict[str, int] = {}
    with open(args.output, "w", encoding="utf-8") as f:
        for msg in messages:
            label = classify(msg)
            challenge_ref = link_challenge(msg.get("content", "") or "")
            msg["intent"] = label
            msg["challenge_ref"] = challenge_ref
            f.write(json.dumps(msg, ensure_ascii=False) + "\n")
            label_counts[label] = label_counts.get(label, 0) + 1

    print(f"[+] Classified {len(messages)} messages → {args.output}")
    print("[+] Label distribution:")
    for label, count in sorted(label_counts.items(), key=lambda x: -x[1]):
        print(f"    {label:15s} {count}")


if __name__ == "__main__":
    main()
