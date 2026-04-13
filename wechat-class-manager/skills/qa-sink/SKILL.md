# Skill: qa-sink

从消息流中提取问答对，沉淀为课程 FAQ 知识库。

## 触发词
`Q&A提取`, `qa sink`, `常见问题`, `知识库`, `faq`

## 输入 (Input)
```yaml
messages: MessageStream   # 来自 msg-classifier 的分类消息
```

## 输出 (Output)
```yaml
qa_pairs.json:
  total: int
  pairs:
    - pair_id: string
      question: string
      answer: string
      asker: {wechat_id, nickname}
      answerer: {wechat_id, nickname}
      topic_tags: [string]
      quality_score: float  # 0-1
      challenge_ref: string|null
      match_method: reply_chain|time_window
```

## 依赖
- msg-classifier

## 使用示例
```bash
python sink.py --input classified.jsonl --output qa_pairs.json
```
