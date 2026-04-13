# Skill: student-profile

从群互动中自动构建学生能力画像。

## 触发词
`学生画像`, `student profile`, `学生分析`, `能力标签`

## 输入 (Input)
```yaml
messages: MessageStream
submissions: SubmissionMatrix
```

## 输出 (Output)
```yaml
student_profiles.json:
  students:
    - wechat_id: string
      nickname: string
      activity_score: float
      submission_count: int
      question_count: int
      answer_count: int
      skill_tags: [string]
      last_active: ISO8601
      status: active|silent|at_risk
```

## 依赖
- msg-classifier
- submission-tracker

## 使用示例
```bash
python profiler.py --input classified.jsonl --submissions submissions.json --output profiles.json
```
