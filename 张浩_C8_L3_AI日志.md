# AI 协作日志 — C8 Level 3 (Gold)

**姓名：** 张浩  
**日期：** 2026-04-13  
**任务：** Agent Skill 封装 + Property Graph + 自然语言查询

---

## 目标 vs 结果

- **计划做什么：** 封装 Level 1-2 功能为标准 Agent Skill，实现 Property Graph，支持自然语言查询
- **实际做到什么：** 完整的 wechat-class-manager/ 目录结构，6 个子 Skill 各有 SKILL.md，SQLite Property Graph，6 种自然语言查询
- **差距：** 每个子 Skill 的 .py 实现文件是封装层（复用 Level 1-2 的逻辑），尚未完全独立；图谱中提交边数量少（群数据刚建立）

---

## 关键决策

**选择 SQLite + JSON 而不是 Neo4j 做 Property Graph**

- 原因：SQLite 是 Python 标准库，零依赖，适合 Bronze/Silver 级别；节点属性存为 JSON 列保持灵活性
- 如果重来：如果数据规模超过 10 万节点，迁移到 NetworkX（内存图）或 Neo4j 更合适

**自然语言查询用规则匹配不用 LLM**

- 原因：查询类型固定（5-6 种），规则匹配可预测、可调试；LLM 调用有延迟和成本
- 查询路由策略：优先匹配最具体的模式（C8+未提交），再匹配通用模式（谁最活跃）

---

## 困难与突破

**问题：** 查询路由顺序错误，"班级整体提交率" 被错误路由到"学生提交查询"  
**解决：** 调整 if-elif 顺序，把更具体的模式（挑战+未提交）放在通用模式（提交）之前；改用 `^` 锚点限制学生姓名匹配范围

---

## 学到的技能

- Property Graph 的 SQLite 实现：节点/边分两表，属性存 JSON，通过 JOIN 实现图遍历
- SKILL.md 标准格式设计：触发词 + Input/Output schema + 依赖 + 示例，让 Agent 可以自动识别和调用
- 自然语言查询的规则路由：按特异性排序 if-elif 链，最具体的规则放最前面

---

## KSTAR 编码

- **K：** 知道 Property Graph 的概念，了解 SQLite 和 JSON 组合可以模拟图数据库
- **S：** 需要让 Claude Code 和 OpenClaw 能通过 SKILL.md 自动识别并调用各子系统
- **T：** 设计目录结构 → 实现 graph.py → 导入数据 → 实现查询接口 → 验证 6 种查询
- **A：** 用 SQLite 节点/边两表 + JSON 属性列，用规则路由实现自然语言查询
- **R：** 41 个学生节点、8 个挑战节点、48 条消息节点，6 种查询类型全部正常工作
