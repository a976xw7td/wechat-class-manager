#!/usr/bin/env python3
"""
watcher.py - Incremental Message Watcher Agent
C8 Challenge Level 4 (Platinum)

Periodically fetches new messages from WeChat group,
updates the Property Graph incrementally (only new messages since last checkpoint).

Usage:
    python watcher.py --group "AI+X Elite Class" --interval 3600
    python watcher.py --group "AI+X Elite Class" --once   # single run
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "wechat-class-manager"))
from graph import PropertyGraph


CHECKPOINT_FILE = Path(__file__).parent / ".watcher_checkpoint.json"


def load_checkpoint() -> dict:
    if CHECKPOINT_FILE.exists():
        with open(CHECKPOINT_FILE) as f:
            return json.load(f)
    return {"last_timestamp": None, "processed_msg_ids": []}


def save_checkpoint(data: dict):
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(data, f, indent=2)


def fetch_new_messages(group: str, since_ts: str | None) -> list[str]:
    """Fetch messages from wechat-cli, filter to only new ones."""
    result = subprocess.run(
        ["wechat-cli", "history", group, "--limit", "9999"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"[ERROR] wechat-cli: {result.stderr}", file=sys.stderr)
        return []

    data = json.loads(result.stdout)
    messages = data.get("messages", [])

    if not since_ts or not isinstance(messages[0] if messages else None, str):
        return messages

    # Filter to messages after checkpoint
    new = []
    for line in messages:
        try:
            ts_str = line[1:line.index("]")]
            dt = datetime.strptime(ts_str, "%Y-%m-%d %H:%M").replace(
                tzinfo=timezone(timedelta(hours=8))
            )
            if dt.isoformat() > since_ts:
                new.append(line)
        except (ValueError, IndexError):
            pass
    return new


def normalize_line(line: str) -> dict | None:
    """Parse a plain-text message line."""
    line = line.strip()
    if not line:
        return None
    try:
        ts_end = line.index("]")
        ts_str = line[1:ts_end]
        rest = line[ts_end + 2:]
        dt = datetime.strptime(ts_str, "%Y-%m-%d %H:%M").replace(
            tzinfo=timezone(timedelta(hours=8))
        )
        if "[系统]" in rest[:10]:
            sender_id = "system"
            content = rest.replace("[系统]", "").strip()
            msg_type = "system"
        elif ": " in rest:
            colon = rest.index(": ")
            sender_id = rest[:colon].strip()
            content = rest[colon + 2:]
            msg_type = "text"
            if content.startswith("[图片]"):
                msg_type = "image"
            elif content.startswith("[文件]"):
                msg_type = "file"
        else:
            return None
        return {
            "msg_id": f"{int(dt.timestamp())}_{sender_id}",
            "timestamp": dt.isoformat(),
            "sender": {"wechat_id": sender_id, "nickname": sender_id},
            "type": msg_type,
            "content": content,
        }
    except (ValueError, IndexError):
        return None


def update_graph(messages: list, g: PropertyGraph) -> int:
    """Update Property Graph with new messages. Returns count added."""
    count = 0
    for raw in messages:
        if isinstance(raw, str):
            msg = normalize_line(raw)
        else:
            msg = raw
        if not msg:
            continue

        sender = msg.get("sender", {})
        wechat_id = sender.get("wechat_id", "unknown")
        student_id = f"student_{wechat_id}"

        if not g.get_node(student_id):
            g.add_node(student_id, "Student",
                       nickname=sender.get("nickname", wechat_id),
                       wechat_id=wechat_id)

        msg_node_id = f"msg_{msg['msg_id']}"
        if not g.get_node(msg_node_id):
            g.add_node(msg_node_id, "Message",
                       content=msg.get("content", "")[:200],
                       msg_type=msg.get("type", "text"),
                       timestamp=msg.get("timestamp", ""))
            g.add_edge(student_id, msg_node_id, "SENT",
                       timestamp=msg.get("timestamp"))
            count += 1

    return count


def run_once(group: str, g: PropertyGraph):
    checkpoint = load_checkpoint()
    since = checkpoint.get("last_timestamp")

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Fetching new messages since {since or 'beginning'}...")
    raw_messages = fetch_new_messages(group, since)

    if not raw_messages:
        print("[*] No new messages.")
        return

    added = update_graph(raw_messages, g)

    # Update checkpoint
    latest_ts = None
    for raw in raw_messages:
        if isinstance(raw, str):
            msg = normalize_line(raw)
            if msg:
                ts = msg.get("timestamp")
                if ts and (latest_ts is None or ts > latest_ts):
                    latest_ts = ts

    if latest_ts:
        checkpoint["last_timestamp"] = latest_ts
        save_checkpoint(checkpoint)

    stats = g.stats()
    print(f"[+] Added {added} new messages. Graph: {stats}")


def main():
    parser = argparse.ArgumentParser(description="WeChat Group Watcher Agent")
    parser.add_argument("--group", default="AI+X Elite Class")
    parser.add_argument("--interval", type=int, default=3600, help="Interval in seconds")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    args = parser.parse_args()

    g = PropertyGraph()

    if args.once:
        run_once(args.group, g)
        g.close()
        return

    print(f"[*] Watcher started. Polling every {args.interval}s. Ctrl+C to stop.")
    try:
        while True:
            run_once(args.group, g)
            print(f"[*] Next check in {args.interval}s...")
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n[*] Watcher stopped.")
    finally:
        g.close()


if __name__ == "__main__":
    main()
