#!/usr/bin/env python3
"""
alert_engine.py - Alert Engine for Class Management
C8 Challenge Level 4 (Platinum)

Detects anomalies and generates alerts:
  1. Deadline approaching: student hasn't submitted 3 days before deadline
  2. Silent student: no messages for 7 consecutive days
  3. Low submission rate: challenge submission rate < 30%

Usage:
    python alert_engine.py --output alerts.json
    python alert_engine.py --simulate  # demo with simulated data
"""

import argparse
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "wechat-class-manager"))
from graph import PropertyGraph

CHALLENGES_DEADLINES = {
    "C5": "2026-04-20",
    "C8": "2026-04-27",
}

ALERT_TYPES = {
    "deadline_warning": "⚠️  Deadline Warning",
    "silent_student":   "🔕 Silent Student",
    "low_submission":   "📉 Low Submission Rate",
    "activity_drop":    "📊 Activity Drop",
}


def check_deadline_warnings(g: PropertyGraph, now: datetime) -> list[dict]:
    """Alert if student hasn't submitted within 3 days of deadline."""
    alerts = []
    for ch_id, deadline_str in CHALLENGES_DEADLINES.items():
        deadline = datetime.strptime(deadline_str, "%Y-%m-%d").replace(
            tzinfo=timezone(timedelta(hours=8))
        )
        days_left = (deadline - now).days
        if not (0 <= days_left <= 3):
            continue

        challenge_node_id = f"challenge_{ch_id}"
        all_students = g.all_nodes("Student")
        submitters = {e["src"] for e in g.get_edges(dst=challenge_node_id, edge_type="SUBMITTED")}

        for student in all_students:
            if student["id"] == "student_system":
                continue
            if student["id"] not in submitters:
                alerts.append({
                    "type": "deadline_warning",
                    "severity": "high" if days_left <= 1 else "medium",
                    "student": student.get("nickname", student["id"]),
                    "challenge": ch_id,
                    "days_left": days_left,
                    "message": f"{student.get('nickname')} 距 {ch_id} 截止还有 {days_left} 天，尚未提交",
                    "timestamp": now.isoformat(),
                })
    return alerts


def check_silent_students(g: PropertyGraph, now: datetime, days: int = 7) -> list[dict]:
    """Alert if student has sent no messages for `days` consecutive days."""
    alerts = []
    cutoff = (now - timedelta(days=days)).isoformat()
    all_students = g.all_nodes("Student")

    for student in all_students:
        if student["id"] in ("student_system",):
            continue
        edges = g.get_edges(src=student["id"], edge_type="SENT")
        if not edges:
            continue  # New student, no messages yet
        # Find latest message timestamp
        latest = max(
            (e.get("timestamp", "") for e in edges),
            default=""
        )
        if latest and latest < cutoff:
            alerts.append({
                "type": "silent_student",
                "severity": "medium",
                "student": student.get("nickname", student["id"]),
                "last_active": latest,
                "silent_days": days,
                "message": f"{student.get('nickname')} 已连续 {days} 天未发言",
                "timestamp": now.isoformat(),
            })
    return alerts


def check_low_submission_rate(g: PropertyGraph, now: datetime, threshold: float = 0.3) -> list[dict]:
    """Alert if a challenge has submission rate below threshold."""
    alerts = []
    all_students = [s for s in g.all_nodes("Student") if s["id"] != "student_system"]
    total = len(all_students)
    if total == 0:
        return []

    for ch_id in CHALLENGES_DEADLINES:
        ch_node_id = f"challenge_{ch_id}"
        submitters = len(set(e["src"] for e in g.get_edges(dst=ch_node_id, edge_type="SUBMITTED")))
        rate = submitters / total
        if rate < threshold:
            alerts.append({
                "type": "low_submission",
                "severity": "high" if rate < 0.1 else "medium",
                "challenge": ch_id,
                "submission_rate": round(rate, 2),
                "submitted": submitters,
                "total": total,
                "message": f"{ch_id} 提交率 {rate*100:.0f}% ({submitters}/{total})，低于阈值 {threshold*100:.0f}%",
                "timestamp": now.isoformat(),
            })
    return alerts


def run_alerts(simulate: bool = False) -> list[dict]:
    g = PropertyGraph()
    now = datetime.now(tz=timezone(timedelta(hours=8)))

    if simulate:
        # Simulate "3 days before C8 deadline" scenario
        now = datetime.strptime("2026-04-24T10:00:00", "%Y-%m-%dT%H:%M:%S").replace(
            tzinfo=timezone(timedelta(hours=8))
        )

    all_alerts = []
    all_alerts.extend(check_deadline_warnings(g, now))
    all_alerts.extend(check_silent_students(g, now))
    all_alerts.extend(check_low_submission_rate(g, now))

    g.close()
    return all_alerts


def main():
    parser = argparse.ArgumentParser(description="Alert Engine")
    parser.add_argument("--output", default="alerts.json")
    parser.add_argument("--simulate", action="store_true", help="Simulate future date for demo")
    args = parser.parse_args()

    alerts = run_alerts(simulate=args.simulate)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump({"generated_at": datetime.now().isoformat(),
                   "total": len(alerts), "alerts": alerts}, f,
                  ensure_ascii=False, indent=2)

    print(f"[+] Generated {len(alerts)} alerts → {args.output}")
    for a in alerts:
        icon = {"high": "🔴", "medium": "🟡"}.get(a.get("severity", ""), "⚪")
        print(f"  {icon} [{a['type']}] {a['message']}")


if __name__ == "__main__":
    main()
