#!/usr/bin/env python3
"""
qa_extractor.py - Q&A Pair Extractor
C8 Challenge Level 2 (Silver)

Extracts question-answer pairs from classified messages.
Matching strategy:
  1. reply_to field (explicit reply chain)
  2. Time-window matching (answer within 10 minutes of question, same thread)

Usage:
    python qa_extractor.py --input linked.jsonl --output qa_pairs.json
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone, timedelta


QUESTION_SIGNALS = re.compile(
    r"[？?]|怎么|如何|为什么|什么是|请问|有没有|能不能|可以吗|"
    r"帮我|求助|不懂|不会|报错|error|Error|issue|问题|咋|啥|哪里",
    re.I,
)

ANSWER_SIGNALS = re.compile(
    r"是的|对的|没错|可以|不行|不能|应该|建议|你需要|试试|参考|"
    r"因为|所以|步骤|方法|解决|答案|这样|如下",
    re.I,
)

STOP_WORDS = {"[表情]", "[图片]", "[语音]", "[文件]"}


def parse_ts(ts_str: str) -> datetime | None:
    if not ts_str:
        return None
    try:
        return datetime.fromisoformat(ts_str)
    except ValueError:
        return None


def quality_score(question: str, answer: str) -> float:
    """Simple quality heuristic: longer + signal-rich = higher score."""
    score = 0.3
    if len(answer) > 30:
        score += 0.2
    if len(answer) > 80:
        score += 0.1
    if ANSWER_SIGNALS.search(answer):
        score += 0.2
    if len(question) > 10:
        score += 0.1
    if "?" in question or "？" in question:
        score += 0.1
    return min(round(score, 2), 1.0)


def extract_topic_tags(text: str) -> list[str]:
    tags = []
    patterns = {
        "github": r"github|git|repo|仓库|commit",
        "python": r"python|pip|import|脚本",
        "wechat": r"微信|wechat|群|消息",
        "submission": r"提交|上传|作业|deadline",
        "setup": r"安装|配置|环境|setup|install",
        "challenge": r"C[1-8]|挑战|challenge",
        "api": r"api|接口|请求|response",
    }
    for tag, pattern in patterns.items():
        if re.search(pattern, text, re.I):
            tags.append(tag)
    return tags


def extract_qa_pairs(messages: list[dict]) -> list[dict]:
    """Extract Q&A pairs using reply chain and time-window heuristics."""
    # Index by msg_id for reply-chain lookup
    by_id: dict[str, dict] = {}
    for msg in messages:
        mid = msg.get("msg_id")
        if mid:
            by_id[mid] = msg

    questions = [
        m for m in messages
        if m.get("intent") == "question"
        or (m.get("type") == "text" and QUESTION_SIGNALS.search(m.get("content", "") or ""))
    ]

    answers = [
        m for m in messages
        if m.get("intent") == "answer"
        or (m.get("type") == "text" and ANSWER_SIGNALS.search(m.get("content", "") or ""))
    ]

    pairs = []
    used_answer_ids = set()

    # Pass 1: explicit reply_to chain
    for ans in answers:
        reply_to = ans.get("reply_to")
        if not reply_to or reply_to not in by_id:
            continue
        q_msg = by_id[reply_to]
        q_content = q_msg.get("content", "") or ""
        a_content = ans.get("content", "") or ""
        if not q_content or not a_content or a_content in STOP_WORDS:
            continue

        pair_id = f"qa_{q_msg.get('msg_id', '')}_{ans.get('msg_id', '')}"
        pairs.append({
            "pair_id": pair_id,
            "question_msg_id": q_msg.get("msg_id"),
            "answer_msg_id": ans.get("msg_id"),
            "question": q_content,
            "answer": a_content,
            "asker": q_msg.get("sender", {}),
            "answerer": ans.get("sender", {}),
            "timestamp": q_msg.get("timestamp"),
            "topic_tags": extract_topic_tags(q_content + " " + a_content),
            "quality_score": quality_score(q_content, a_content),
            "challenge_ref": q_msg.get("challenge_ref") or ans.get("challenge_ref"),
            "match_method": "reply_chain",
        })
        used_answer_ids.add(ans.get("msg_id"))

    # Pass 2: time-window matching (question → answer within 10 min, different sender)
    WINDOW = timedelta(minutes=10)
    for q_msg in questions:
        q_ts = parse_ts(q_msg.get("timestamp"))
        if not q_ts:
            continue
        q_sender = (q_msg.get("sender") or {}).get("wechat_id", "")
        q_content = q_msg.get("content", "") or ""
        if not q_content or not QUESTION_SIGNALS.search(q_content):
            continue

        best_ans = None
        best_gap = WINDOW

        for ans in answers:
            if ans.get("msg_id") in used_answer_ids:
                continue
            a_ts = parse_ts(ans.get("timestamp"))
            if not a_ts:
                continue
            a_sender = (ans.get("sender") or {}).get("wechat_id", "")
            a_content = ans.get("content", "") or ""
            if not a_content or a_content in STOP_WORDS:
                continue
            # Must be after the question, different sender
            gap = a_ts - q_ts
            if timedelta(0) < gap < best_gap and a_sender != q_sender:
                best_gap = gap
                best_ans = ans

        if best_ans:
            a_content = best_ans.get("content", "") or ""
            pair_id = f"qa_{q_msg.get('msg_id', '')}_{best_ans.get('msg_id', '')}"
            # Avoid duplicates
            if any(p["pair_id"] == pair_id for p in pairs):
                continue
            pairs.append({
                "pair_id": pair_id,
                "question_msg_id": q_msg.get("msg_id"),
                "answer_msg_id": best_ans.get("msg_id"),
                "question": q_content,
                "answer": a_content,
                "asker": q_msg.get("sender", {}),
                "answerer": best_ans.get("sender", {}),
                "timestamp": q_msg.get("timestamp"),
                "topic_tags": extract_topic_tags(q_content + " " + a_content),
                "quality_score": quality_score(q_content, a_content),
                "challenge_ref": q_msg.get("challenge_ref") or best_ans.get("challenge_ref"),
                "match_method": "time_window",
            })
            used_answer_ids.add(best_ans.get("msg_id"))

    # Sort by quality score descending
    pairs.sort(key=lambda p: p["quality_score"], reverse=True)
    return pairs


def main():
    parser = argparse.ArgumentParser(description="Q&A Pair Extractor")
    parser.add_argument("--input", default="linked.jsonl")
    parser.add_argument("--output", default="qa_pairs.json")
    args = parser.parse_args()

    try:
        with open(args.input, encoding="utf-8") as f:
            messages = [json.loads(l) for l in f if l.strip()]
    except FileNotFoundError:
        print(f"[ERROR] {args.input} not found", file=sys.stderr)
        sys.exit(1)

    pairs = extract_qa_pairs(messages)

    output = {
        "total": len(pairs),
        "pairs": pairs,
    }
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"[+] Extracted {len(pairs)} Q&A pairs → {args.output}")
    for p in pairs[:5]:
        print(f"    [{p['quality_score']:.2f}] Q: {p['question'][:40]!r}")
        print(f"          A: {p['answer'][:40]!r}")


if __name__ == "__main__":
    main()
