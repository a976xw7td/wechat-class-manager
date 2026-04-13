# AI 协作日志 — C8 Level 1 (Bronze)

**姓名：** 张浩  
**日期：** 2026-04-13  
**任务：** 从本地微信数据中提取群消息，输出为 Agent 可消费的 JSON Lines 格式

---

## 目标 vs 结果

- **计划做什么：** 安装 wechat-cli，提取 AI+X Elite Class 群消息，输出标准 JSON schema
- **实际做到什么：** 成功提取 55 条消息，涵盖文本、图片、文件、链接、系统消息五种类型，CLI 可重复运行
- **差距：** 消息时间戳精度只到分钟（wechat-cli 原始格式限制），msg_id 唯一性依赖时间戳+发送者组合，存在极低概率碰撞

---

## 关键决策

**选择 `freestylefly/wechat-cli`（npm 版）而不是 pip 版或自写脚本**

- 原因：文档推荐 macOS 首选，JSON 输出格式对 AI 友好，零配置安装
- 如果重来：可能先评估 `sjzar/chatlog`，因为它提供 HTTP API，更方便后续 Level 2/3 集成

---

## 困难与突破

**问题：** wechat-cli init 对微信重新签名后，微信无法启动（`Launchd job spawn failed`）

**原因：** wechat-cli 在 macOS 安全策略下需要给微信添加调试权限，重签名后 macOS Gatekeeper 拦截了启动

**解决：** 用 `codesign --force --deep --sign -` 重新以 ad-hoc 方式签名，恢复微信正常启动，然后再次 init 成功提取密钥

**AI 帮了什么：** 诊断错误原因、提供 codesign 修复命令、识别微信数据目录中哪个是当前登录账号

---

## 学到的技能

- macOS 代码签名机制（codesign、ad-hoc 签名、task_for_pid 权限）
- SQLCipher 加密数据库的密钥提取原理
- JSON Lines（.jsonl）格式：每行一条独立 JSON，适合流式处理和大文件
- wechat-cli 返回的消息是纯文本字符串，需要正则解析，而不是结构化 dict

**可迁移场景：** 任何需要把非结构化聊天记录转为结构化数据的场景（Slack 导出、Telegram 备份等）

---

## KSTAR 编码

- **K（已知）：** 知道微信本地数据是 SQLCipher 加密的 SQLite，需要内存提取密钥
- **S（情境）：** Mac M 系列芯片，微信 macOS 版，需要 root 权限访问进程内存
- **T（任务分解）：** 安装工具 → init 提取密钥 → history 拉消息 → normalize 标准化 → 写 CLI 包装
- **A（实际行动）：** 修复签名问题、处理字符串格式消息解析、按时间过滤消息
- **R（结果）：** CLI 一条命令可提取任意天数消息，格式符合 C8 schema 要求，通过 Bronze 验收标准
