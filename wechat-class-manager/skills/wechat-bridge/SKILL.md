# Skill: wechat-bridge

从本地微信数据中提取群消息，输出标准 JSON Lines 格式。

## 触发词
`提取消息`, `extract messages`, `wechat bridge`, `消息提取`

## 输入 (Input)
```yaml
group: string       # 微信群名称
days: int           # 提取最近几天（默认7）
output: string      # 输出文件路径（默认 messages.jsonl）
```

## 输出 (Output)
```yaml
messages.jsonl:     # 每行一条消息，标准 schema
  msg_id: string
  timestamp: ISO8601
  sender: {wechat_id, nickname}
  type: text|image|file|voice|link|system
  content: string
  media_ref: string|null
  reply_to: string|null
```

## 依赖
- wechat-cli (`npm install -g @canghe_ai/wechat-cli`)
- Python 3.10+
- 微信已登录并完成 `sudo wechat-cli init`

## 使用示例
```bash
python bridge.py --group "AI+X Elite Class" --days 7 --output messages.jsonl
```
