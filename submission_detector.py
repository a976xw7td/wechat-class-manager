#!/usr/bin/env python3
"""
submission_detector.py - Submission Event Detector
C8 Challenge Level 2 (Silver)

Detects submission events from classified messages and builds a
student × challenge submission matrix.

Usage:
    python submission_detector.py --input linked.jsonl --output submissions.json
"""

import argparse
import json
import re
import sys
from datetime import datetime


FILE_EXT = re.compile(r"\.(py|md|pdf|zip|ipynb|js|html|txt|csv|json|yaml|yml)\b", re.I)
LEVEL_MAP = {"bronze": "Bronze", "silver": "Silver", "gold": "Gold", "platinum": "Platinum",
             "1": "Bronze", "2": "Silver", "3": "Gold", "4": "Platinum"}
CHALLENGE_REF = re.compile(r"\b(C[1-8][A-Z]?)\b", re.I)
LEVEL_REF = re.compile(r"(?:level\s*|L)([1-4])|(?i)(bronze|silver|gold|platinum)", re.I)


def extract_level(content: str) -> str | None:
    m = LEVEL_REF.search(content)
    if not m:
        return None
    key = (m.group(1) or m.group(2) or "").lower()
    return LEVEL_MAP.get(key)


def is_submission(msg: dict) -> bool:
    """Return True if the message looks like a submission."""
    intent = msg.get("intent", "")
    if intent == "submission":
        return True
    content = msg.get("content", "") or ""
    msg_type = msg.get("type", "text")
    # File upload with challenge reference
    if msg_type == "file" and CHALLENGE_REF.search(content):
        return True
    # Text containing file extensions + challenge ref
    if FILE_EXT.search(content) and CHALLENGE_REF.search(content):
        return True
    return False


def main():
    parser = argparse.ArgumentParser(description="Submission Detector")
    parser.add_argument("--input", default="linked.jsonl")
    parser.add_argument("--output", default="submissions.json")
    args = parser.parse_args()

    try:
        with open(args.input, encoding="utf-8") as f:
            messages = [json.loads(l) for l in f if l.strip()]
    except FileNotFoundError:
        print(f"[ERROR] {args.input} not found", file=sys.stderr)
        sys.exit(1)

    submissions = []
    matrix: dict[str, dict[str, list]] = {}  # student → challenge → [submission]

    for msg in messages:
        if not is_submission(msg):
            continue

        sender = (msg.get("sender") or {})
        student = sender.get("nickname") or sender.get("wechat_id", "unknown")
        content = msg.get("content", "") or ""
        challenge = msg.get("challenge_ref") or (CHALLENGE_REF.search(content) and
                                                  CHALLENGE_REF.search(content).group(1).upper())
        level = extract_level(content)

        submission = {
            "student": student,
            "challenge": challenge,
            "level_claimed": level,
            "timestamp": msg.get("timestamp"),
            "msg_id": msg.get("msg_id"),
            "content_preview": content[:100],
            "files": [m.group(0) for m in FILE_EXT.finditer(content)],
            "status": "received",
        }
        submissions.append(submission)

        # Update matrix
        if student not in matrix:
            matrix[student] = {}
        ch_key = challenge or "unknown"
        if ch_key not in matrix[student]:
            matrix[student][ch_key] = []
        matrix[student][ch_key].append(submission)

    output = {
        "generated_at": datetime.now().isoformat(),
        "total_submissions": len(submissions),
        "submissions": submissions,
        "matrix": matrix,
    }

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"[+] Detected {len(submissions)} submission events → {args.output}")
    print("[+] Students with submissions:")
    for student, challenges in matrix.items():
        print(f"    {student}: {list(challenges.keys())}")


if __name__ == "__main__":
    main()
