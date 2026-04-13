#!/usr/bin/env python3
"""
report_engine.py - Weekly/Monthly Report Generator
C8 Challenge Level 4 (Platinum)

Generates structured Markdown reports that can be directly sent to the group.

Usage:
    python report_engine.py --period weekly --output weekly_report.md
    python report_engine.py --period monthly --output monthly_report.md
"""

import argparse
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "wechat-class-manager"))
sys.path.insert(0, str(Path(__file__).parent))
from graph import PropertyGraph
from config_loader import get_config

_cfg = get_config()


def ascii_bar(value: float, width: int = 20) -> str:
    filled = int(value * width)
    return "█" * filled + "░" * (width - filled)


def generate_daily_report(g: PropertyGraph, day: datetime) -> str:
    return generate_weekly_report(g, day, period_days=1)

def generate_weekly_report(g: PropertyGraph, week_start: datetime, period_days: int = 7) -> str:
    week_end = week_start + timedelta(days=period_days)
    now = datetime.now(tz=timezone(timedelta(hours=8)))

    all_students = [s for s in g.all_nodes("Student") if s["id"] != "student_system"]
    total_students = len(all_students)

    # Activity stats
    activity = []
    for s in all_students:
        cnt = len(g.get_edges(src=s["id"], edge_type="SENT"))
        if cnt > 0:
            activity.append((s.get("nickname", s["id"]), cnt))
    activity.sort(key=lambda x: -x[1])
    top5 = activity[:5]

    # Submission stats per challenge
    challenges = _cfg.challenge_list
    submission_stats = []
    for ch_id, ch_name in challenges:
        ch_node_id = f"challenge_{ch_id}"
        submitters = len(set(e["src"] for e in g.get_edges(dst=ch_node_id, edge_type="SUBMITTED")))
        rate = submitters / total_students if total_students else 0
        submission_stats.append((ch_id, ch_name, submitters, total_students, rate))

    # Total messages this period
    all_msgs = g.all_nodes("Message")
    total_msgs = len(all_msgs)

    lines = [
        f"# 📊 {_cfg.group_display_name} 周报",
        f"**统计周期：** {week_start.strftime('%Y-%m-%d')} ~ {week_end.strftime('%Y-%m-%d')}{'（今日）' if period_days == 1 else '（本周）'}",
        f"**生成时间：** {now.strftime('%Y-%m-%d %H:%M')}",
        "",
        "---",
        "",
        "## 📬 消息概览",
        "",
        f"- 群内消息总数：**{total_msgs}** 条",
        f"- 活跃学生人数：**{len(activity)}** / {total_students}",
        "",
        "## 🏆 最活跃学生 Top 5",
        "",
        "| 排名 | 姓名 | 发言数 | 活跃度 |",
        "|------|------|--------|--------|",
    ]

    max_cnt = top5[0][1] if top5 else 1
    for i, (name, cnt) in enumerate(top5):
        bar = ascii_bar(cnt / max_cnt, 10)
        lines.append(f"| {i+1} | {name} | {cnt} | `{bar}` |")

    lines += [
        "",
        "## 📋 挑战提交率",
        "",
        "| 挑战 | 名称 | 提交 | 总数 | 完成率 |",
        "|------|------|------|------|--------|",
    ]
    for ch_id, ch_name, submitted, total, rate in submission_stats:
        bar = ascii_bar(rate, 10)
        lines.append(f"| {ch_id} | {ch_name} | {submitted} | {total} | `{bar}` {rate*100:.0f}% |")

    lines += [
        "",
        "## ⚠️ 需要关注",
        "",
    ]

    # Find students with no submissions
    for ch_id, ch_name, submitted, total, rate in submission_stats:
        if rate < 0.5:
            ch_node_id = f"challenge_{ch_id}"
            submitters = {e["src"] for e in g.get_edges(dst=ch_node_id, edge_type="SUBMITTED")}
            missing = [s.get("nickname") for s in all_students if s["id"] not in submitters]
            if missing:
                lines.append(f"- **{ch_id}** 未提交（{len(missing)}人）：{', '.join(missing[:5])}{'...' if len(missing) > 5 else ''}")

    # Silent students (no messages)
    silent = [s.get("nickname") for s in all_students
              if len(g.get_edges(src=s["id"], edge_type="SENT")) == 0]
    if silent:
        lines.append(f"- **沉默学生**（{len(silent)}人）：{', '.join(silent[:5])}")

    lines += [
        "",
        "---",
        "",
        f"*本报告由 wechat-class-manager 自动生成 · {now.strftime('%Y-%m-%d %H:%M')}*",
    ]

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Report Engine")
    parser.add_argument("--period", choices=["daily", "weekly", "monthly"], default="daily")
    parser.add_argument("--output", default="weekly_report.md")
    args = parser.parse_args()

    g = PropertyGraph()
    now = datetime.now(tz=timezone(timedelta(hours=8)))

    if args.period == "daily":
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        report = generate_weekly_report(g, day_start, period_days=1)
    elif args.period == "weekly":
        week_start = now - timedelta(days=now.weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        report = generate_weekly_report(g, week_start)
    else:
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        report = generate_weekly_report(g, month_start)

    g.close()

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"[+] Report generated → {args.output}")
    print(report[:500] + "...")


if __name__ == "__main__":
    main()
