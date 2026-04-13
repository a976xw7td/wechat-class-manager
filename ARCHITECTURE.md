# System Architecture — C8 WeChat Class Management Agent

## Overview

A three-layer system that turns a WeChat group into a queryable, proactive class management agent.

```
┌──────────────────────────────────────────────────────┐
│  Layer 3: CLASS MANAGEMENT SKILLS                    │
│  alert_engine · report_engine · dashboard · watcher  │
├──────────────────────────────────────────────────────┤
│  Layer 2: AGENT RUNTIME (Property Graph + Skills)    │
│  graph.py · import_data.py · query.py                │
│  classifier · challenge_linker · submission_detector │
├──────────────────────────────────────────────────────┤
│  Layer 1: WECHAT CHANNEL ADAPTER                     │
│  wechat_bridge.py  →  messages.jsonl (JSONL stream)  │
└──────────────────────────────────────────────────────┘
```

## Data Flow

```
WeChat SQLite DB
      │  wechat-cli (DB decrypt + JSON parse)
      ▼
wechat_bridge.py  ──►  messages.jsonl        (raw JSONL stream)
      │
      ▼
classifier.py     ──►  classified.jsonl      (+ intent label)
      │
      ▼
challenge_linker.py ►  linked.jsonl          (+ challenge_ref)
      │
      ├──► submission_detector.py ──► submissions.json
      ├──► qa_extractor.py        ──► qa_pairs.json
      │
      ▼
import_data.py    ──►  graph.db (SQLite Property Graph)
      │
      ├──► query.py              (natural language queries)
      ├──► alert_engine.py       (deadline / silent / rate alerts)
      ├──► report_engine.py      (weekly/daily Markdown report)
      └──► dashboard/app.py      (Flask web UI on port 8080)
```

## Component Reference

| File | Layer | Role |
|------|-------|------|
| `wechat_bridge.py` | 1 | Reads WeChat group via wechat-cli, normalises to standard JSON schema |
| `classifier.py` | 2 | Rule-based 7-intent classifier (submission/question/answer/discussion/announcement/resource/social) |
| `challenge_linker.py` | 2 | Maps each message to C1–C8 via explicit ref or keyword matching |
| `submission_detector.py` | 2 | Detects submission events; builds student × challenge matrix |
| `qa_extractor.py` | 2 | Extracts Q&A pairs using reply_to chain + time-window heuristic |
| `wechat-class-manager/graph.py` | 2 | SQLite-backed Property Graph (nodes + typed edges) |
| `wechat-class-manager/import_data.py` | 2 | Seeds graph from linked.jsonl; handles "me" → real wechat_id mapping |
| `wechat-class-manager/query.py` | 3 | Natural language query router (6 query types) |
| `alert_engine.py` | 3 | Proactive alerts: deadline warning, silent students, low submission rate |
| `report_engine.py` | 3 | Markdown report generator (daily/weekly/monthly) |
| `watcher.py` | 3 | Incremental watcher: checkpoint-based, only processes new messages |
| `dashboard/app.py` | 3 | Flask dashboard (5+ dimensions of class data) on port 8080 |

## Property Graph Schema

**Node types:** Student · Challenge · Submission · Message · QAPair

**Edge types:**
- `SENT` — Student → Message
- `SUBMITTED` — Student → Challenge (via Submission)
- `ASKED` — Student → QAPair
- `ANSWERED` — Student → QAPair

## Skill Directory (`wechat-class-manager/skills/`)

Each sub-directory follows the standard SKILL.md format:

| Skill | Trigger | Function |
|-------|---------|----------|
| `wechat-bridge` | on_message | Fetch & normalise WeChat messages |
| `msg-classifier` | on_message | Classify intent + link challenge |
| `submission-tracker` | on_file / on_message | Track student submissions |
| `qa-sink` | on_message | Extract and store Q&A pairs |
| `student-profile` | on_query | Build and query student profiles |
| `class-report` | on_schedule | Generate weekly/monthly reports |

## Deployment

### Quick Start
```bash
# 1. Install dependencies
pip install flask pyyaml

# 2. Pull latest WeChat messages
python wechat_bridge.py --group "AI+X Elite Class" --output messages.jsonl

# 3. Run pipeline
python classifier.py --input messages.jsonl --output classified.jsonl
python challenge_linker.py --input classified.jsonl --output linked.jsonl

# 4. Build Property Graph
rm -f wechat-class-manager/data/graph.db
python wechat-class-manager/import_data.py --input linked.jsonl

# 5. Start dashboard
python dashboard/app.py
# Open http://localhost:8080
```

### Incremental Updates (Watcher)
```bash
python watcher.py --group "AI+X Elite Class" --interval 3600
```

### Generate Report
```bash
python report_engine.py --period weekly --output weekly_report.md
```

### Natural Language Query
```bash
python wechat-class-manager/query.py "C5 还有谁没提交？"
python wechat-class-manager/query.py "最近一周最活跃的同学是谁？"
```

## Configuration

- `wechat-class-manager/config/group_nicknames.yaml` — WeChat ID → group nickname mapping
- `wechat-class-manager/config/challenges.yaml` — Challenge definitions
- `wechat-class-manager/config/group_config.yaml` — Group metadata

## Requirements

- Python 3.10+
- `flask` (dashboard only)
- `pyyaml` (config loading)
- `wechat-cli` (message extraction from WeChat) — see SETUP.md
