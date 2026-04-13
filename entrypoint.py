#!/usr/bin/env python3
"""
entrypoint.py - Docker container startup script
Cross-platform: uses pathlib throughout, no shell dependencies.

Modes:
  DEMO  — /data/messages.jsonl not mounted → runs on built-in sample data
  REAL  — /data/messages.jsonl mounted     → runs on user-provided data
"""

import subprocess
import sys
from pathlib import Path

APP = Path("/app")
DATA_DIR = APP / "wechat-class-manager" / "data"
CLASSIFIED = Path("/tmp/classified.jsonl")
LINKED = Path("/tmp/linked.jsonl")
USER_DATA = Path("/data/messages.jsonl")
DEMO_DATA = APP / "demo" / "sample_messages.jsonl"


def run(cmd: list[str]) -> None:
    """Run a command, stream output, exit on failure."""
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        sys.exit(result.returncode)


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if USER_DATA.exists():
        print(f"[*] Found user data at {USER_DATA}")
        input_messages = USER_DATA
        import_script = APP / "wechat-class-manager" / "import_data.py"
        import_cmd = [sys.executable, str(import_script), "--input", str(LINKED)]
    else:
        print("[*] No user data found — running in DEMO MODE with sample data")
        print("[*] To use your own data:")
        print("[*]   docker run -v ./messages.jsonl:/data/messages.jsonl ...")
        input_messages = DEMO_DATA
        import_script = APP / "demo" / "import_demo.py"
        import_cmd = [sys.executable, str(import_script), str(LINKED)]

    # Step 1: classify
    run([sys.executable, str(APP / "classifier.py"),
         "--input", str(input_messages),
         "--output", str(CLASSIFIED)])

    # Step 2: link challenges
    run([sys.executable, str(APP / "challenge_linker.py"),
         "--input", str(CLASSIFIED),
         "--output", str(LINKED)])

    # Step 3: build graph
    db_path = DATA_DIR / "graph.db"
    if db_path.exists():
        db_path.unlink()

    run(import_cmd)

    # Step 4: start dashboard
    print("[*] Starting dashboard at http://localhost:8080")
    run([sys.executable, str(APP / "dashboard" / "app.py")])


if __name__ == "__main__":
    main()
