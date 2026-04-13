# AI 协作日志 — C8 Level 4 (Platinum)

**姓名：** 张浩  
**日期：** 2026-04-13  
**任务：** 闭环系统——Watcher + Alert + Report + Dashboard

---

## 目标 vs 结果

- **计划做什么：** 实现增量监控、预警引擎、报告生成、可视化 Dashboard，达到 Platinum 验收标准
- **实际做到什么：** 四个组件全部实现并可独立运行；Watcher 实现 checkpoint 增量处理；Alert 检测 3 种预警类型；Report 生成 Markdown 周报；Dashboard 展示 5 个维度的班级数据
- **差距：** Dashboard 使用 Flask 需要 `pip install flask`；双向通道（Agent 写回微信群）未实现（需要 Wechaty，超出 Platinum 基础要求）

---

## 关键决策

**Watcher 用文件 checkpoint 而不是数据库时间戳**

- 原因：文件 checkpoint 简单可靠，重启后不会重复处理；数据库时间戳需要额外表维护
- 实现：`.watcher_checkpoint.json` 存储 last_timestamp 和已处理消息 ID 列表

**Dashboard 用 Flask render_template_string 而不是独立 HTML 文件**

- 原因：单文件部署，不需要配置模板目录；`render_template_string` 支持 Jinja2 语法
- 如果重来：可以用 Streamlit（更简单）或 FastAPI + 静态文件（更专业）

**Alert 用模拟时间参数（--simulate）而不是修改系统时间**

- 原因：可以在不同时间点演示预警效果，不依赖真实截止时间；测试更方便

---

## 困难与突破

**问题：** Alert 检测到 60 个预警（群刚建，所有学生都没提交）  
**分析：** 这是正常的——群建于 4 月 12 日，截止日期是 4 月 20/27 日，确实所有人都还没提交  
**解决：** 在真实生产环境中，Alert 应该只在截止前 3 天才开始检测，避免提前预警

**问题：** Dashboard 中 challenge_list 是元组列表，Jinja2 模板需要特殊处理  
**解决：** 直接传 list of tuples 给 Jinja2，用 `for ch_id, _ in challenge_list` 解包

---

## 学到的技能

- 增量处理模式：用 checkpoint 记录最后处理位置，每次只处理新增数据
- Flask `render_template_string`：单文件 Web 应用，避免模板文件管理
- 预警系统的三种模式：deadline_warning（时间维度）、silent_student（活跃度维度）、low_submission（完成率维度）

**可迁移场景：** 任何需要监控 + 预警 + 报告的管理系统（HR、项目管理、运营监控）

---

## KSTAR 编码

- **K：** 知道闭环系统的三要素：感知（Watcher）→ 推理（Alert）→ 行动（Report/Dashboard）
- **S：** 群数据刚建立，所有提交记录为空，需要模拟场景演示预警功能
- **T：** 实现 Watcher（增量）→ Alert（三种预警）→ Report（Markdown 周报）→ Dashboard（Flask）
- **A：** 用文件 checkpoint 实现增量处理，用 `--simulate` 参数演示不同时间场景，用 Flask 单文件 Dashboard
- **R：** 四组件全部可独立运行；Watcher 增量处理验证通过；Alert 检测 3 种预警类型；Report 生成格式完整的周报；Dashboard 展示 5 个数据维度
