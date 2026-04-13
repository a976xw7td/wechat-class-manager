#!/usr/bin/env python3
"""
wechat_bridge.py - WeChat Group Message Bridge
C8 Challenge Level 1 (Bronze)

Usage:
    python wechat_bridge.py --group "AI+X Elite Class" --days 7 --output messages.jsonl
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone


def fetch_messages(group: str, days: int) -> list:
    """Fetch messages from a WeChat group using wechat-cli."""
    result = subprocess.run(
        ["wechat-cli", "history", group, "--limit", "9999"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"[ERROR] wechat-cli failed: {result.stderr}", file=sys.stderr)
        sys.exit(1)

    data = json.loads(result.stdout)
    messages = data.get("messages", [])

    # If messages are plain strings, filter by parsing the timestamp from text
    if messages and isinstance(messages[0], str):
        cutoff = datetime.now(tz=timezone(timedelta(hours=8))) - timedelta(days=days)
        filtered = []
        for line in messages:
            try:
                ts_str = line[1:line.index("]")]
                dt = datetime.strptime(ts_str, "%Y-%m-%d %H:%M").replace(
                    tzinfo=timezone(timedelta(hours=8))
                )
                if dt >= cutoff:
                    filtered.append(line)
            except (ValueError, IndexError):
                pass
        return filtered

    # If messages are dicts, filter by timestamp field
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=days)
    filtered = []
    for msg in messages:
        ts = msg.get("timestamp")
        if ts and datetime.fromtimestamp(ts, tz=timezone.utc) >= cutoff:
            filtered.append(msg)
    return filtered


def classify_type(raw_type: str, content: str) -> str:
    """Map wechat-cli msg_type to standard type enum."""
    t = (raw_type or "").lower()
    c = content or ""
    if "图片" in t or "image" in t:
        return "image"
    if "文件" in t or "file" in t:
        return "file"
    if "语音" in t or "voice" in t:
        return "voice"
    if "链接" in t or "link" in t:
        return "link"
    if "系统" in t or "system" in t:
        return "system"
    return "text"


def normalize(raw_msg: dict, group: str) -> dict | None:
    """Convert a raw wechat-cli message dict to standard schema."""
    # wechat-cli history returns plain strings like:
    # "[2026-04-12 22:40] 肖福军班主任: hello"
    # but when called with --format json it returns dicts.
    # Handle both cases.
    if isinstance(raw_msg, str):
        return normalize_string(raw_msg)

    ts = raw_msg.get("timestamp")
    if not ts:
        return None

    dt = datetime.fromtimestamp(ts, tz=timezone(timedelta(hours=8)))
    content = raw_msg.get("content", "") or raw_msg.get("message", "")
    sender_id = raw_msg.get("sender") or raw_msg.get("username", "")
    nickname = raw_msg.get("nickname") or raw_msg.get("sender_nickname", sender_id)
    msg_type = classify_type(raw_msg.get("type", ""), content)

    return {
        "msg_id": raw_msg.get("msg_id") or raw_msg.get("id") or str(ts),
        "timestamp": dt.isoformat(),
        "sender": {
            "wechat_id": sender_id,
            "nickname": nickname,
        },
        "type": msg_type,
        "content": content,
        "media_ref": raw_msg.get("media_ref") or raw_msg.get("path"),
        "reply_to": raw_msg.get("reply_to") or raw_msg.get("parent_msg_id"),
        "group": group,
    }


def normalize_string(line: str) -> dict | None:
    """Parse a plain-text message line from wechat-cli."""
    # Format: "[YYYY-MM-DD HH:MM] sender: content"
    line = line.strip()
    if not line:
        return None
    try:
        ts_end = line.index("]")
        ts_str = line[1:ts_end]
        rest = line[ts_end + 2:]  # skip "] "

        # Determine if system message
        if rest.startswith("[系统]") or "[系统]" in rest[:6]:
            sender_id = "system"
            nickname = "system"
            content = rest.replace("[系统]", "").strip()
            msg_type = "system"
        elif ": " in rest:
            colon_pos = rest.index(": ")
            sender_id = rest[:colon_pos].strip()
            nickname = sender_id
            content = rest[colon_pos + 2:]
            msg_type = "text"
            # Detect media hints
            if content.startswith("[图片]"):
                msg_type = "image"
            elif content.startswith("[文件]"):
                msg_type = "file"
            elif content.startswith("[语音]"):
                msg_type = "voice"
            elif content.startswith("[链接/文件]"):
                msg_type = "link"
        else:
            return None

        dt = datetime.strptime(ts_str, "%Y-%m-%d %H:%M").replace(
            tzinfo=timezone(timedelta(hours=8))
        )

        return {
            "msg_id": f"{int(dt.timestamp())}_{sender_id}",
            "timestamp": dt.isoformat(),
            "sender": {"wechat_id": sender_id, "nickname": nickname},
            "type": msg_type,
            "content": content,
            "media_ref": None,
            "reply_to": None,
        }
    except (ValueError, IndexError):
        return None


def main():
    parser = argparse.ArgumentParser(description="WeChat Group Message Bridge")
    parser.add_argument("--group", required=True, help="Group name or username")
    parser.add_argument("--days", type=int, default=7, help="Days of history to fetch")
    parser.add_argument("--output", default="messages.jsonl", help="Output file (.jsonl)")
    args = parser.parse_args()

    print(f"[*] Fetching messages from '{args.group}' (last {args.days} days)...")
    raw_messages = fetch_messages(args.group, args.days)

    normalized = []
    for raw in raw_messages:
        msg = normalize(raw, args.group)
        if msg:
            normalized.append(msg)

    # Handle plain-string format (wechat-cli may return list of strings)
    if normalized and all(v is None for v in normalized):
        normalized = []

    # If raw messages came back as strings, normalize them
    string_messages = [m for m in raw_messages if isinstance(m, str)]
    if string_messages:
        normalized = [normalize_string(s) for s in string_messages]
        normalized = [m for m in normalized if m is not None]

    with open(args.output, "w", encoding="utf-8") as f:
        for msg in normalized:
            f.write(json.dumps(msg, ensure_ascii=False) + "\n")

    print(f"[+] Saved {len(normalized)} messages to {args.output}")

    # Print type breakdown
    types: dict[str, int] = {}
    for msg in normalized:
        t = msg["type"]
        types[t] = types.get(t, 0) + 1
    print("[+] Message types:", types)


if __name__ == "__main__":
    main()
