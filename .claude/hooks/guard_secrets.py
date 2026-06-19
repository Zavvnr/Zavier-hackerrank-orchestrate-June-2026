#!/usr/bin/env python3
"""PreToolUse middleware: block any attempt to read or modify .env (AGENTS.md secret rule).

Reads the hook payload on stdin; denies Read/Edit/Write on a .env file and Bash commands that touch
.env. Fail-open: on any error it allows the action, so the hook can never brick a session.
"""
import json
import re
import sys

ENV_REF = re.compile(r"(^|[\s'\"=/\\])\.env(?!\.example|\.sample|\.template)(\b|$|['\"\s/\\])")


def _deny(reason):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason}}))
    sys.exit(0)


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)  # unparseable payload -> do not interfere
    tool = data.get("tool_name", "")
    ti = data.get("tool_input", {}) or {}

    targets = [str(ti[k]) for k in ("file_path", "path", "notebook_path") if ti.get(k)]
    if tool == "Bash" and ti.get("command"):
        targets.append(str(ti["command"]))

    for t in targets:
        base = t.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
        if base == ".env" or ENV_REF.search(t):
            _deny("Blocked by harness: .env is off-limits (AGENTS.md). "
                  "Read secrets from environment variables by name only.")
    sys.exit(0)


if __name__ == "__main__":
    main()
