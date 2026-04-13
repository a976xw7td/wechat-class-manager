#!/usr/bin/env python3
"""
dashboard/app.py - Local Web Dashboard
C8 Challenge Level 4 (Platinum)

A Flask-based local web dashboard showing 5+ dimensions of class data.

Usage:
    pip install flask
    python dashboard/app.py
    Open http://localhost:5000
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent / "wechat-class-manager"))
sys.path.insert(0, str(Path(__file__).parent.parent))
from graph import PropertyGraph
from config_loader import get_config

_cfg = get_config()

try:
    from flask import Flask, jsonify, render_template_string
except ImportError:
    print("[ERROR] Flask not installed. Run: pip install flask")
    sys.exit(1)

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ group_name }} Dashboard</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
         background: #0f172a; color: #e2e8f0; min-height: 100vh; padding: 24px; }
  h1 { font-size: 1.8rem; font-weight: 700; color: #f8fafc; margin-bottom: 4px; }
  .subtitle { color: #94a3b8; font-size: 0.9rem; margin-bottom: 28px; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; }
  .card { background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 20px; }
  .card h2 { font-size: 1rem; color: #94a3b8; font-weight: 500; margin-bottom: 16px;
             text-transform: uppercase; letter-spacing: 0.05em; }
  .stat { display: flex; align-items: baseline; gap: 8px; margin-bottom: 8px; }
  .stat-value { font-size: 2.5rem; font-weight: 700; color: #38bdf8; }
  .stat-label { color: #94a3b8; font-size: 0.85rem; }
  .bar-row { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; font-size: 0.85rem; }
  .bar-label { width: 120px; color: #cbd5e1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .bar-track { flex: 1; background: #334155; border-radius: 4px; height: 8px; }
  .bar-fill { height: 8px; border-radius: 4px; background: linear-gradient(90deg, #38bdf8, #818cf8); }
  .bar-count { width: 30px; text-align: right; color: #64748b; }
  .tag { display: inline-block; padding: 2px 8px; border-radius: 20px; font-size: 0.75rem;
         background: #1e3a5f; color: #38bdf8; margin: 2px; }
  .alert-item { padding: 10px 12px; border-radius: 8px; margin-bottom: 8px; font-size: 0.85rem; }
  .alert-high { background: #450a0a; border-left: 3px solid #ef4444; color: #fca5a5; }
  .alert-medium { background: #422006; border-left: 3px solid #f59e0b; color: #fcd34d; }
  .table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
  .table th { text-align: left; padding: 6px 8px; color: #64748b; font-weight: 500;
              border-bottom: 1px solid #334155; }
  .table td { padding: 6px 8px; border-bottom: 1px solid #1e293b; }
  .badge { padding: 2px 8px; border-radius: 20px; font-size: 0.75rem; }
  .badge-green { background: #052e16; color: #4ade80; }
  .badge-red { background: #450a0a; color: #f87171; }
  .badge-gray { background: #1e293b; color: #64748b; }
  footer { text-align: center; color: #334155; font-size: 0.8rem; margin-top: 32px; }
</style>
</head>
<body>
<h1>📊 {{ group_name }} Dashboard</h1>
<p class="subtitle">今日数据 · 更新于 {{ updated_at }} · {{ group_name }}（共 {{ stats.students }} 人）</p>

<div class="grid">

  <!-- 维度1: 总览统计 -->
  <div class="card">
    <h2>📈 班级概览</h2>
    <div class="stat">
      <span class="stat-value">{{ stats.students }}</span>
      <span class="stat-label">名学生</span>
    </div>
    <div style="margin-top:8px; color:#94a3b8; font-size:0.85rem;">
      <div>💬 消息总数：{{ stats.messages }}</div>
      <div>📋 提交事件：{{ stats.submissions }}</div>
      <div>🎯 挑战数量：{{ stats.challenges }}</div>
    </div>
  </div>

  <!-- 维度2: 活跃度排行 -->
  <div class="card">
    <h2>🏆 今日发言活跃度 Top 10</h2>
    {% for name, cnt, pct in top_active %}
    <div class="bar-row">
      <span class="bar-label" title="{{ name }}">{{ name }}</span>
      <div class="bar-track"><div class="bar-fill" style="width:{{ pct }}%"></div></div>
      <span class="bar-count">{{ cnt }}</span>
    </div>
    {% endfor %}
  </div>

  <!-- 维度3: 挑战提交率 -->
  <div class="card">
    <h2>📋 挑战提交率</h2>
    {% for ch_id, ch_name, submitted, total, pct in challenge_rates %}
    <div style="margin-bottom:12px;">
      <div style="display:flex; justify-content:space-between; margin-bottom:4px; font-size:0.85rem;">
        <span><strong>{{ ch_id }}</strong> {{ ch_name }}</span>
        <span style="color:#94a3b8;">{{ submitted }}/{{ total }} ({{ pct }}%)</span>
      </div>
      <div class="bar-track">
        <div class="bar-fill" style="width:{{ pct }}%; background: {% if pct < 30 %}#ef4444{% elif pct < 60 %}#f59e0b{% else %}#22c55e{% endif %};"></div>
      </div>
    </div>
    {% endfor %}
  </div>

  <!-- 维度4: 预警信息 -->
  <div class="card">
    <h2>⚠️ 预警信息</h2>
    {% for alert in alerts %}
    <div class="alert-item alert-{{ alert.severity }}">
      {{ alert.message }}
    </div>
    {% endfor %}
    {% if not alerts %}
    <div style="color:#4ade80; font-size:0.85rem;">✅ 暂无预警</div>
    {% endif %}
  </div>

  <!-- 维度5: 学生提交状态 -->
  <div class="card" style="grid-column: span 2;">
    <h2>👥 学生提交状态</h2>
    <table class="table">
      <thead>
        <tr>
          <th>学生</th>
          <th>发言数</th>
          {% for ch_id, _ in challenge_list %}
          <th>{{ ch_id }}</th>
          {% endfor %}
          <th>状态</th>
        </tr>
      </thead>
      <tbody>
        {% for s in student_table %}
        <tr>
          <td>{{ s.nickname }}</td>
          <td>{{ s.msg_count }}</td>
          {% for ch_id, _ in challenge_list %}
          <td>
            {% if ch_id in s.submitted %}
            <span class="badge badge-green">✓</span>
            {% else %}
            <span class="badge badge-red">✗</span>
            {% endif %}
          </td>
          {% endfor %}
          <td>
            {% if s.msg_count > 5 %}
            <span class="badge badge-green">活跃</span>
            {% elif s.msg_count > 0 %}
            <span class="badge badge-gray">普通</span>
            {% else %}
            <span class="badge badge-red">沉默</span>
            {% endif %}
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>

</div>

<footer>wechat-class-manager · C8 Level 4 Platinum · 自动生成</footer>
</body>
</html>
"""


def get_dashboard_data():
    g = PropertyGraph()
    now = datetime.now(tz=timezone(timedelta(hours=8)))

    all_students = [s for s in g.all_nodes("Student") if s["id"] != "student_system"]
    total = len(all_students)

    # Stats
    stats = {
        "students": total,
        "messages": len(g.all_nodes("Message")),
        "submissions": len(g.all_nodes("Submission")),
        "challenges": len(g.all_nodes("Challenge")),
    }

    # Top active
    activity = []
    for s in all_students:
        cnt = len(g.get_edges(src=s["id"], edge_type="SENT"))
        activity.append((s.get("nickname", s["id"]), cnt))
    activity.sort(key=lambda x: -x[1])
    max_cnt = activity[0][1] if activity else 1
    top_active = [(n, c, int(c / max_cnt * 100)) for n, c in activity[:10] if c > 0]

    # Challenge rates
    challenge_list = _cfg.challenge_list
    challenge_rates = []
    for ch_id, ch_name in challenge_list:
        ch_node_id = f"challenge_{ch_id}"
        submitted = len(set(e["src"] for e in g.get_edges(dst=ch_node_id, edge_type="SUBMITTED")))
        pct = int(submitted / total * 100) if total else 0
        challenge_rates.append((ch_id, ch_name, submitted, total, pct))

    # Alerts
    from alert_engine import check_deadline_warnings, check_low_submission_rate, check_silent_students
    alerts = []
    alerts.extend(check_deadline_warnings(g, now))
    alerts.extend(check_low_submission_rate(g, now))
    alerts.extend(check_silent_students(g, now)[:3])

    # Student table — all 27 members, sorted by msg_count desc
    student_table = []
    for s in sorted(all_students, key=lambda x: -len(g.get_edges(src=x["id"], edge_type="SENT"))):
        submitted_challenges = set()
        for ch_id, _ in challenge_list:
            ch_node_id = f"challenge_{ch_id}"
            if g.get_edges(src=s["id"], dst=ch_node_id, edge_type="SUBMITTED"):
                submitted_challenges.add(ch_id)
        student_table.append({
            "nickname": s.get("nickname", s["id"]),
            "msg_count": len(g.get_edges(src=s["id"], edge_type="SENT")),
            "submitted": submitted_challenges,
        })

    g.close()
    return {
        "stats": stats,
        "top_active": top_active,
        "challenge_rates": challenge_rates,
        "challenge_list": challenge_list,
        "alerts": alerts,
        "student_table": student_table,
        "updated_at": now.strftime("%Y-%m-%d %H:%M:%S"),
        "group_name": _cfg.group_display_name,
    }


@app.route("/")
def index():
    data = get_dashboard_data()
    return render_template_string(HTML, **data)


@app.route("/api/stats")
def api_stats():
    return jsonify(get_dashboard_data()["stats"])


if __name__ == "__main__":
    print("[*] Dashboard starting at http://localhost:8080")
    app.run(debug=False, host="0.0.0.0", port=8080)
