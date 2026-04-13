#!/usr/bin/env python3
"""
import_data.py - Import messages.jsonl into Property Graph
C8 Challenge Level 3 (Gold)

Usage:
    python import_data.py [--input ../messages.jsonl]
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))
from graph import PropertyGraph
from config_loader import get_config

_cfg = get_config()
CHALLENGES = {c["id"]: c.get("name_cn", c["id"]) for c in _cfg.challenges}

# 真实群成员（27人），display_name = 微信昵称
REAL_MEMBERS = [
    {"username": "xfj7777777",             "display_name": "肖福军班主任"},
    {"username": "wxid_7pti7exj2z522",     "display_name": "Blue"},
    {"username": "wxid_3xrps8zrgwk612",    "display_name": "MAGIC"},
    {"username": "wxid_dphbp69y3vp622",    "display_name": "Re."},
    {"username": "wxid_yu4atk86fjmv22",    "display_name": "Sterling"},
    {"username": "wxid_ntt7v4s151qz22",    "display_name": "dao"},
    {"username": "wxid_dwfciv2qm06w22",    "display_name": "zack"},
    {"username": "wxid_i4hmf57zw30041",    "display_name": "μ"},
    {"username": "tongrj",                  "display_name": "Richard-佟佳睿"},
    {"username": "wxid_x4ezzap9p4bm12",    "display_name": "喀"},
    {"username": "wxid_s3q6bm4zgr7822",    "display_name": "墨圆"},
    {"username": "wxid_3bvm6bqcvy1222",    "display_name": "妖Yao"},
    {"username": "wxid_5sqk55x25blp22",    "display_name": "安"},
    {"username": "wxid_ow1zd67jmzi722",    "display_name": "小狗有什么心思"},
    {"username": "wxid_r2bed62gnoil22",    "display_name": "幸福科技小陈"},
    {"username": "wxid_7zylxqhy1vtg22",    "display_name": "愤怒的公牛"},   # 张浩，群昵称见 group_nicknames.yaml
    {"username": "wxid_d7q3ybu0927c22",    "display_name": "扶砚"},
    {"username": "wxid_cuo6hogc2qqp22",    "display_name": "抡起大锤"},
    {"username": "wxid_g2r276x1yjut22",    "display_name": "朝露"},
    {"username": "wxid_6y9vxutthobm22",    "display_name": "木辛梓"},
    {"username": "wxid_2as6slvk4mz322",    "display_name": "椿"},
    {"username": "a37206006",               "display_name": "胡祥恩"},
    {"username": "wxid_2f2tgmeuueu312",    "display_name": "自在如风"},
    {"username": "wxid_sjdndlma0qwy22",    "display_name": "让我来漏一手"},
    {"username": "wxid_gdw0jcw1aspg22",    "display_name": "閪Sʜᴀᴅᴏᴡ . ₪"},
    {"username": "shy3991",                 "display_name": "飞"},
    {"username": "wxid_pcac65p6iz5g22",    "display_name": "🐋"},
]

# wechat-cli 对自己发的消息用 "me" 作为 sender，映射到真实账号
ME_WECHAT_ID = "wxid_7zylxqhy1vtg22"


def load_group_nicknames() -> dict[str, str]:
    """Load group_nicknames.yaml: wechat_id → group_nickname."""
    config_path = Path(__file__).parent / "config" / "group_nicknames.yaml"
    if not config_path.exists():
        return {}
    if not HAS_YAML:
        # Simple YAML parser for key: "value" lines
        result = {}
        for line in config_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("#") or ":" not in line:
                continue
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key and val and not val.startswith("#"):
                result[key] = val
        return result
    with open(config_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("nicknames", {}) if data else {}


def import_messages(input_path: str):
    g = PropertyGraph()

    # Load group nickname overrides
    group_nicknames = load_group_nicknames()  # wechat_id → group_nickname

    # Seed challenge nodes
    for cid, name in CHALLENGES.items():
        g.add_node(f"challenge_{cid}", "Challenge", challenge_id=cid, name=name)

    # Seed 27 real members, applying group nickname if available
    display_to_id: dict[str, str] = {}
    for m in REAL_MEMBERS:
        uid = m["username"]
        student_id = f"student_{uid}"
        # Use group nickname if configured, otherwise fall back to WeChat display_name
        nickname = group_nicknames.get(uid, m["display_name"])
        g.add_node(student_id, "Student", nickname=nickname, wechat_id=uid,
                   display_name=m["display_name"])
        display_to_id[m["display_name"]] = student_id

    # Import messages
    input_path = Path(input_path)
    if not input_path.exists():
        print(f"[WARN] {input_path} not found, using member data only")
    else:
        with open(input_path, encoding="utf-8") as f:
            messages = [json.loads(l) for l in f if l.strip()]

        for msg in messages:
            sender = msg.get("sender") or {}
            wechat_id = sender.get("wechat_id", "unknown")
            nickname = sender.get("nickname", wechat_id)

            # Skip system messages
            if wechat_id == "system" or nickname == "system" or msg.get("type") == "system":
                continue

            # Map "me" to the current user
            if wechat_id == "me" or nickname == "me":
                wechat_id = ME_WECHAT_ID
                student_id = f"student_{ME_WECHAT_ID}"
            else:
                # Match by display_name first, then by wechat_id
                student_id = display_to_id.get(nickname) or f"student_{wechat_id}"

            # Only add if this student isn't in the real member list (shouldn't happen)
            if not g.get_node(student_id):
                g.add_node(student_id, "Student", nickname=nickname, wechat_id=wechat_id)

            # Add message node
            msg_node_id = f"msg_{msg.get('msg_id', '')}"
            g.add_node(msg_node_id, "Message",
                       content=msg.get("content", "")[:200],
                       msg_type=msg.get("type", "text"),
                       timestamp=msg.get("timestamp", ""),
                       intent=msg.get("intent", ""),
                       challenge_ref=msg.get("challenge_ref"))

            g.add_edge(student_id, msg_node_id, "SENT", timestamp=msg.get("timestamp"))

            # Submission edge
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

        print(f"[+] Imported {len(messages)} messages")

    stats = g.stats()
    print(f"[+] Graph stats: {stats}")
    g.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="../messages.jsonl")
    args = parser.parse_args()
    import_messages(args.input)


if __name__ == "__main__":
    main()
