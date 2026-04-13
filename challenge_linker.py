#!/usr/bin/env python3
"""
challenge_linker.py - Challenge Reference Linker
C8 Challenge Level 2 (Silver)

Links messages to specific challenges (C1-C8) using keywords and patterns.

Usage:
    python challenge_linker.py --input classified.jsonl --output linked.jsonl
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config_loader import get_config

_cfg = get_config()
CHALLENGE_KEYWORDS = _cfg.challenge_keywords
EXPLICIT_REF = re.compile(rf"({_cfg.challenge_ref_pattern})", re.I)


def link(msg: dict) -> str | None:
    """Return the most likely challenge reference for a message."""
    content = (msg.get("content") or "").lower()

    # Explicit reference takes priority
    match = EXPLICIT_REF.search(msg.get("content") or "")
    if match:
        return match.group(1).upper()

    # Keyword matching
    scores: dict[str, int] = {}
    for challenge, keywords in CHALLENGE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw.lower() in content)
        if score > 0:
            scores[challenge] = score

    if scores:
        return max(scores, key=lambda k: scores[k])

    return None


def main():
    parser = argparse.ArgumentParser(description="Challenge Reference Linker")
    parser.add_argument("--input", default="classified.jsonl")
    parser.add_argument("--output", default="linked.jsonl")
    args = parser.parse_args()

    try:
        with open(args.input, encoding="utf-8") as f:
            messages = [json.loads(l) for l in f if l.strip()]
    except FileNotFoundError:
        print(f"[ERROR] {args.input} not found", file=sys.stderr)
        sys.exit(1)

    challenge_counts: dict[str, int] = {}
    with open(args.output, "w", encoding="utf-8") as f:
        for msg in messages:
            ref = link(msg)
            msg["challenge_ref"] = ref
            f.write(json.dumps(msg, ensure_ascii=False) + "\n")
            if ref:
                challenge_counts[ref] = challenge_counts.get(ref, 0) + 1

    print(f"[+] Linked {len(messages)} messages → {args.output}")
    print("[+] Challenge distribution:")
    for ch, count in sorted(challenge_counts.items()):
        print(f"    {ch}: {count} messages")


if __name__ == "__main__":
    main()
