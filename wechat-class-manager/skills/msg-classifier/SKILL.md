# Skill: msg-classifier

对微信群消息进行意图分类，并关联到具体挑战（C1-C8）。

## 触发词
`消息分类`, `classify messages`, `意图分类`, `challenge linker`

## 输入 (Input)
```yaml
messages: MessageStream   # 来自 wechat-bridge 的消息流
```

## 输出 (Output)
```yaml
classified.jsonl:
  # 原始字段 + 新增：
  intent: submission|question|answer|discussion|announcement|resource|social|system
  challenge_ref: C1|C2|...|C8|null
```

## 依赖
- wechat-bridge（提供消息流）

## 使用示例
```bash
python classifier.py --input messages.jsonl --output classified.jsonl
```

## 分类规则
| 标签 | 信号特征 |
|------|----------|
| submission | 包含文件 + 挑战命名规范 |
| question | 问号、"怎么"、"请问" |
| answer | 回复一个 question 消息 |
| announcement | @所有人、deadline、截止 |
| resource | 链接、文件、推荐 |
| social | 不属于以上任何一类 |
