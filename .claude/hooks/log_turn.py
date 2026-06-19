#!/usr/bin/env python3
"""Stop-hook backstop for AGENTS.md per-turn logging.

Appends a minimal, timestamped turn marker to ~/hackerrank_orchestrate/log.txt (created if missing).
The agent still writes the rich AGENTS.md §5.2 entry via /log; this only guarantees a turn is never
silently unlogged. Writes no secrets. Fail-open: never blocks the session.
"""
import datetime as dt
import json
import os
import sys
from pathlib import Path


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        data = {}
    try:
        log = Path.home() / "hackerrank_orchestrate" / "log.txt"
        log.parent.mkdir(parents=True, exist_ok=True)
        ts = dt.datetime.now().astimezone().isoformat(timespec="seconds")
        cwd = data.get("cwd", os.getcwd())
        entry = (f"\n## [{ts}] TURN (auto-backstop)\n"
                 f"Context:\n  repo_root={cwd}\n"
                 f"  note=skeleton written by Stop hook; agent expands the real summary via /log\n")
        with open(log, "a", encoding="utf-8") as fh:
            fh.write(entry)
    except Exception:
        pass
    sys.exit(0)


if __name__ == "__main__":
    main()
