#!/usr/bin/env python3
"""
demo/import_demo.py - Import demo messages into Property Graph (no hardcoded members)

Discovers students automatically from message senders.
Used by Docker entrypoint for demo mode.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "wechat-class-manager"))
from graph import PropertyGraph

CHALLENGES = {
    "C1": "环境配置", "C2": "API接入", "C3": "群内参与",
    "C4": "技能分享", "C5": "GitHub主页", "C6": "仪表盘",
    "C7": "Agent自动化", "C8": "微信班级管理",
}


def import_demo(input_path: str):
    g = PropertyGraph()

    # Seed challenge nodes
    for cid, name in CHALLENGES.items():
        g.add_node(f"challenge_{cid}", "Challenge", challenge_id=cid, name=name)

    with open(input_path, encoding="utf-8") as f:
        messages = [json.loads(l) for l in f if l.strip()]

    known_students = {}  # wechat_id → student_id

    for msg in messages:
        sender = msg.get("sender") or {}
        wechat_id = sender.get("wechat_id", "unknown")
        nickname = sender.get("nickname", wechat_id)

        if wechat_id in ("system", "unknown") or msg.get("type") == "system":
            continue

        student_id = f"student_{wechat_id}"
        if student_id not in known_students:
            g.add_node(student_id, "Student", nickname=nickname, wechat_id=wechat_id)
            known_students[wechat_id] = student_id

        msg_node_id = f"msg_{msg.get('msg_id', '')}"
        g.add_node(msg_node_id, "Message",
                   content=msg.get("content", "")[:200],
                   msg_type=msg.get("type", "text"),
                   timestamp=msg.get("timestamp", ""),
                   intent=msg.get("intent", ""),
                   challenge_ref=msg.get("challenge_ref"))

        g.add_edge(student_id, msg_node_id, "SENT", timestamp=msg.get("timestamp"))

        if msg.get("intent") == "submission" and msg.get("challenge_ref"):
            ch_id = f"challenge_{msg['challenge_ref']}"
            sub_id = f"sub_{msg.get('msg_id', '')}"
            g.add_node(sub_id, "Submission",
                       status="received",
                       timestamp=msg.get("timestamp", ""),
                       challenge_ref=msg.get("challenge_ref"))
            g.add_edge(student_id, ch_id, "SUBMITTED",
                       submission_id=sub_id,
                       timestamp=msg.get("timestamp"))

    stats = g.stats()
    print(f"[demo] Imported {len(messages)} messages")
    print(f"[demo] Graph: {stats}")
    g.close()


if __name__ == "__main__":
    default = Path(__file__).parent / "sample_messages.jsonl"
    path = sys.argv[1] if len(sys.argv) > 1 else str(default)
    import_demo(path)
