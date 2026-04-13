# Skill: submission-tracker

检测提交事件，构建学生×挑战提交矩阵。

## 触发词
`提交追踪`, `submission tracker`, `谁提交了`, `追踪提交`

## 输入 (Input)
```yaml
messages: MessageStream     # 来自 msg-classifier 的分类消息
challenges: ChallengeConfig # 来自 config/challenges.yaml
```

## 输出 (Output)
```yaml
submissions.json:
  total_submissions: int
  submissions:
    - student: string
      challenge: string
      level_claimed: Bronze|Silver|Gold|Platinum|null
      timestamp: ISO8601
      status: received|reviewing|accepted|needs_revision
  matrix:
    student_name:
      challenge_id: [submission_list]
```

## 依赖
- msg-classifier

## 使用示例
```bash
python tracker.py --input classified.jsonl --output submissions.json
```
