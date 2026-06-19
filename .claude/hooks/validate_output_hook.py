#!/usr/bin/env python3
"""PostToolUse middleware: when output.csv is written, run the schema validator and surface problems.

Scoped: acts only when the edited file's basename is output.csv. Fail-open and non-blocking — it
surfaces a warning the agent can see (the write already happened); it never rejects the edit.
"""
import json
import subprocess
import sys
from pathlib import Path


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    ti = data.get("tool_input", {}) or {}
    path = str(ti.get("file_path") or ti.get("path") or "")
    if not path or Path(path).name != "output.csv":
        sys.exit(0)

    project = data.get("cwd", ".")
    validator = (Path(project) / ".claude" / "skills" / "eval-harness"
                 / "scripts" / "validate_output.py")
    if not validator.exists():
        sys.exit(0)
    try:
        proc = subprocess.run([sys.executable, str(validator), path],
                              capture_output=True, text=True, timeout=60)
        if proc.returncode != 0:
            sys.stderr.write("Harness schema check on output.csv FAILED:\n"
                             + proc.stdout + proc.stderr)
            sys.exit(2)  # surfaces stderr to the agent without blocking
    except Exception:
        pass
    sys.exit(0)


if __name__ == "__main__":
    main()
