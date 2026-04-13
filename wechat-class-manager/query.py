#!/usr/bin/env python3
"""
query.py - Natural Language Query Interface for Class Management Graph
C8 Challenge Level 3 (Gold)

Supports 5+ query types via keyword/rule matching (no LLM required).

Usage:
    python query.py "张三提交了哪些挑战？"
    python query.py  # runs demo queries
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from graph import PropertyGraph


def query(q: str, g: PropertyGraph | None = None) -> str:
    if g is None:
        g = PropertyGraph()

    q_lower = q.lower()

    # --- Query type 2 (优先): 某挑战还有谁没交 ---
    m2 = re.search(r"(C[1-8][A-Z]?)", q, re.I)
    if m2 and ("没交" in q or "未提交" in q or "还没" in q or "没提交" in q):
        ch_ref = m2.group(1).upper()
        all_students = g.all_nodes("Student")
        ch_id = f"challenge_{ch_ref}"
        submitters = {e["src"] for e in g.get_edges(dst=ch_id, edge_type="SUBMITTED")}
        missing = [s["nickname"] for s in all_students if s["id"] not in submitters]
        if not missing:
            return f"✅ {ch_ref} 所有学生均已提交！"
        return f"⚠️  {ch_ref} 未提交学生（{len(missing)}人）：{', '.join(missing[:10])}{'...' if len(missing) > 10 else ''}"

    # --- Query type 1: 某学生提交了哪些挑战 ---
    m = re.search(r"^([\u4e00-\u9fff\w]+?)(?:提交了|交了|完成了)", q)
    if m:
        name = m.group(1) if m else None
        if name:
            students = g.find_nodes("Student", nickname=name)
            if not students:
                students = [s for s in g.all_nodes("Student")
                            if name.lower() in s.get("wechat_id", "").lower()
                            or name in s.get("nickname", "")]
            if students:
                s = students[0]
                edges = g.get_edges(src=s["id"], edge_type="SUBMITTED")
                if not edges:
                    return f"📭 {s['nickname']} 暂无提交记录"
                challenges = []
                for e in edges:
                    ch = g.get_node(e["dst"])
                    if ch:
                        challenges.append(ch.get("name", ch.get("challenge_id", e["dst"])))
                return f"📋 {s['nickname']} 已提交：{', '.join(set(challenges))}"
            return f"❓ 未找到学生：{name}"

    # --- (type 2 already handled above) ---
    if False:
        ch_ref = m.group(1).upper()
        all_students = g.all_nodes("Student")
        ch_id = f"challenge_{ch_ref}"
        submitters = {e["src"] for e in g.get_edges(dst=ch_id, edge_type="SUBMITTED")}
        missing = [s["nickname"] for s in all_students if s["id"] not in submitters]
        if not missing:
            return f"✅ {ch_ref} 所有学生均已提交！"
        return f"⚠️  {ch_ref} 未提交学生（{len(missing)}人）：{', '.join(missing[:10])}{'...' if len(missing) > 10 else ''}"

    # --- Query type 3: 谁最活跃 ---
    if "活跃" in q or "发言" in q or "最多" in q:
        days = 7
        m = re.search(r"(\d+)\s*[天周]", q)
        if m:
            n = int(m.group(1))
            days = n * 7 if "周" in q[m.start():m.end()+1] else n

        students = g.all_nodes("Student")
        counts = []
        for s in students:
            cnt = g.get_student_message_count(s["id"])
            if cnt > 0:
                counts.append((s["nickname"], cnt))
        counts.sort(key=lambda x: -x[1])
        if not counts:
            return "📊 暂无发言数据"
        top = counts[:5]
        lines = [f"  {i+1}. {name} — {cnt} 条" for i, (name, cnt) in enumerate(top)]
        return f"🏆 最活跃学生 Top {len(top)}（最近 {days} 天）:\n" + "\n".join(lines)

    # --- Query type 4: 关于某话题的常见问题 ---
    if "问题" in q or "常见" in q or "faq" in q.lower() or "提问" in q:
        topic = None
        for kw in ["github", "git", "提交", "python", "api", "微信", "wechat", "安装", "配置"]:
            if kw in q_lower:
                topic = kw
                break
        msgs = g.find_nodes("Message")
        qa_msgs = [m for m in msgs if m.get("intent") == "question"
                   and (topic is None or topic.lower() in (m.get("content") or "").lower())]
        if not qa_msgs:
            return f"💬 暂无{'关于 ' + topic + ' 的' if topic else ''}问题记录"
        lines = [f"  • {m['content'][:60]}" for m in qa_msgs[:5]]
        return f"❓ 常见问题{('（' + topic + '）') if topic else ''}:\n" + "\n".join(lines)

    # --- Query type 5: 整体提交率 ---
    if "提交率" in q or "整体" in q or "统计" in q or "多少人" in q:
        all_students = g.all_nodes("Student")
        total = len(all_students)
        if total == 0:
            return "📊 暂无学生数据"
        results = []
        for cid, name in [("C5", "GitHub主页"), ("C8", "微信班级管理")]:
            ch_id = f"challenge_{cid}"
            submitters = len(set(e["src"] for e in g.get_edges(dst=ch_id, edge_type="SUBMITTED")))
            rate = submitters / total * 100
            results.append(f"  {cid} {name}: {submitters}/{total} ({rate:.0f}%)")
        stats = g.stats()
        return f"📊 班级提交统计（共 {total} 名学生）:\n" + "\n".join(results) + \
               f"\n  总消息数: {stats.get('nodes', {}).get('Message', 0)}"

    # --- Query type 6: 图谱统计 ---
    if "统计" in q or "overview" in q_lower or "概览" in q:
        stats = g.stats()
        lines = [f"  {k}: {v}" for k, v in stats.get("nodes", {}).items()]
        return "📈 图谱概览:\n节点:\n" + "\n".join(lines)

    return f"🤔 未能理解查询：{q!r}\n支持的查询类型：提交查询、未提交查询、活跃度、常见问题、提交率统计"


DEMO_QUERIES = [
    "Alice提交了哪些挑战？",
    "C5 还有谁没交？",
    "最近一周谁最活跃？",
    "关于 GitHub 的常见问题有哪些？",
    "班级整体提交率是多少？",
    "C8 还有谁未提交？",
]


def main():
    g = PropertyGraph()
    if len(sys.argv) > 1:
        q = " ".join(sys.argv[1:])
        print(query(q, g))
    else:
        print("=" * 60)
        print("wechat-class-manager 自然语言查询演示")
        print("=" * 60)
        for q in DEMO_QUERIES:
            print(f"\n🔍 查询: {q}")
            print(query(q, g))
    g.close()


if __name__ == "__main__":
    main()
