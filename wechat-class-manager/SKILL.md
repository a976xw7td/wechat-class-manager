# Skill: wechat-class-manager

把微信班级群变成 Agent 可调用的班级管理系统。

## 触发词

`班级管理`, `class management`, `wechat class`, `群管理`, `提交追踪`, `学生画像`

## 系统架构

```
WeChat Group → wechat-bridge → msg-classifier → submission-tracker
                                              → qa-sink
                                              → student-profile
                                              → class-report
```

## 子 Skill 列表

| Skill | 功能 | 文件 |
|-------|------|------|
| wechat-bridge | 从本地微信数据提取群消息 | skills/wechat-bridge/ |
| msg-classifier | 对消息进行意图分类 | skills/msg-classifier/ |
| submission-tracker | 检测和追踪提交事件 | skills/submission-tracker/ |
| qa-sink | Q&A 提取与知识库管理 | skills/qa-sink/ |
| student-profile | 构建学生画像 | skills/student-profile/ |
| class-report | 生成班级周报/月报 | skills/class-report/ |

## 自然语言查询示例

```
"张三提交了哪些挑战？"       → submission-tracker
"C8 还有谁没交？"            → submission-tracker
"最近一周谁最活跃？"          → student-profile
"关于 GitHub 的常见问题？"    → qa-sink
"班级整体提交率是多少？"       → class-report
```

## 快速开始

```bash
# 1. 提取消息
python skills/wechat-bridge/bridge.py --group "AI+X Elite Class" --days 7 --output data/messages.jsonl

# 2. 分类 + 关联
python skills/msg-classifier/classifier.py --input data/messages.jsonl --output data/classified.jsonl

# 3. 检测提交
python skills/submission-tracker/tracker.py --input data/classified.jsonl --output data/submissions.json

# 4. 查询
python query.py "C8 还有谁没交？"
```

## 依赖

- Python 3.10+
- wechat-cli (`npm install -g @canghe_ai/wechat-cli`)
- sqlite3 (Python 标准库)
