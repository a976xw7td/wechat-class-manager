# Skill: class-report

自动生成班级周报/月报，格式为 Markdown，可直接发群或转公众号。

## 触发词
`生成报告`, `class report`, `周报`, `月报`, `班级总结`

## 输入 (Input)
```yaml
graph: PropertyGraph
period: weekly|monthly|challenge_summary
```

## 输出 (Output)
```yaml
report.md:
  # 本周新增提交 N 件，涉及 M 个挑战
  # 最活跃学生 Top 5
  # 最佳 Q&A 对
  # 各挑战完成率柱状图（ASCII）
```

## 依赖
- graph.py（PropertyGraph）
- student-profile

## 使用示例
```bash
python reporter.py --period weekly --output weekly_report.md
```
