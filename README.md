# wechat-class-manager

> **C8 Challenge — WeChat Group → Class Management Agent Skill**  
> Turn a WeChat group into a queryable, proactive class management system.

## What This Does

Reads messages from a WeChat group and turns them into structured, actionable data:

- **Submission tracking** — who submitted which challenge, via #接龙 or file upload
- **Activity analytics** — message counts, active vs silent students
- **Alert engine** — deadline warnings, low submission rates, silent student detection
- **Q&A extraction** — surfaces unanswered questions from the chat
- **Web dashboard** — 5-dimension class overview at `http://localhost:8080`
- **Weekly reports** — auto-generated Markdown summaries

## Architecture

```
WeChat SQLite DB
      │  wechat-cli
      ▼
wechat_bridge.py  ──►  messages.jsonl
      │
      ├──► classifier.py        (intent: submission/question/answer/...)
      ├──► challenge_linker.py  (maps to C1–C8)
      ├──► submission_detector.py
      └──► qa_extractor.py
                │
                ▼
        wechat-class-manager/
          graph.py          # SQLite Property Graph
          import_data.py    # seed graph from pipeline output
          query.py          # natural language queries
          skills/           # Agent Skill definitions (SKILL.md)
                │
                ├── alert_engine.py
                ├── report_engine.py
                ├── watcher.py
                └── dashboard/app.py
```

## Quick Start

### 1. Install dependencies

```bash
pip install flask pyyaml
```

### 2. Install wechat-cli

```bash
npm install -g @canghe_ai/wechat-cli
```

See [SETUP.md](SETUP.md) for macOS code-signing steps required by wechat-cli.

### 3. Configure your group

```bash
cp wechat-class-manager/config/group_nicknames.yaml.example \
   wechat-class-manager/config/group_nicknames.yaml
# Edit group_nicknames.yaml with your group members' WeChat IDs and nicknames
```

### 4. Pull messages & run pipeline

```bash
python wechat_bridge.py --group "Your Group Name" --output messages.jsonl

python classifier.py       --input messages.jsonl   --output classified.jsonl
python challenge_linker.py --input classified.jsonl  --output linked.jsonl

rm -f wechat-class-manager/data/graph.db
python wechat-class-manager/import_data.py --input linked.jsonl
```

### 5. Launch dashboard

```bash
python dashboard/app.py
# Open http://localhost:8080
```

### 6. Query the graph

```bash
python wechat-class-manager/query.py "C5 还有谁没提交？"
python wechat-class-manager/query.py "最近最活跃的同学是谁？"
python wechat-class-manager/query.py "班级整体提交率是多少？"
```

## Incremental Watcher

```bash
python watcher.py --group "Your Group Name" --interval 3600
```

Runs every hour, only processes new messages since last checkpoint.

## Generate Reports

```bash
python report_engine.py --period daily   --output daily_report.md
python report_engine.py --period weekly  --output weekly_report.md
python report_engine.py --period monthly --output monthly_report.md
```

## Run Tests

```bash
python tests/test_classifier.py
python tests/test_submission.py
```

## Agent Skill Integration

The `wechat-class-manager/` directory follows the standard SKILL.md format and can be invoked by Claude Code or any P3394-compatible agent runtime:

```
wechat-class-manager/
├── SKILL.md                    # root skill descriptor
└── skills/
    ├── wechat-bridge/SKILL.md  # Layer 1: data extraction
    ├── msg-classifier/SKILL.md # Layer 2: intent classification
    ├── submission-tracker/     # Layer 3: submission tracking
    ├── qa-sink/                # Layer 3: Q&A extraction
    ├── student-profile/        # Layer 3: student profiling
    └── class-report/           # Layer 3: report generation
```

## File Structure

```
.
├── wechat_bridge.py          # CLI: pull WeChat messages → JSONL
├── classifier.py             # CLI: classify message intent
├── challenge_linker.py       # CLI: link messages to challenges
├── submission_detector.py    # CLI: detect submission events
├── qa_extractor.py           # CLI: extract Q&A pairs
├── watcher.py                # CLI: incremental message watcher
├── alert_engine.py           # proactive alert rules
├── report_engine.py          # weekly/monthly report generator
├── dashboard/app.py          # Flask web dashboard (port 8080)
├── SETUP.md                  # installation & wechat-cli setup
├── ARCHITECTURE.md           # system design docs
├── tests/
│   ├── test_classifier.py
│   ├── test_submission.py
│   └── fixtures/             # sample messages for testing
└── wechat-class-manager/
    ├── SKILL.md
    ├── graph.py              # SQLite Property Graph
    ├── import_data.py
    ├── query.py
    ├── skills/               # SKILL.md per sub-skill
    ├── config/
    │   ├── challenges.yaml
    │   └── group_nicknames.yaml.example
    └── schemas/
```

## Requirements

- Python 3.10+
- macOS (wechat-cli requires local WeChat installation)
- WeChat Desktop running
- `flask`, `pyyaml`

## License

MIT
