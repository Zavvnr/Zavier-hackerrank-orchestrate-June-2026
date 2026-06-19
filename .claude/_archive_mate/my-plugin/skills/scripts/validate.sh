#!/usr/bin/env bash
# validate.sh — sanity checks for MATE's Python sources.
# Usage: bash validate.sh [file_or_directory]   (defaults to the repo root)
# Exit 0 = every file compiles (style issues are warnings). Exit 1 = a Python syntax error.

set -uo pipefail

TARGET="${1:-.}"
LIMIT=120

# Pick a Python interpreter.
PY=""
for c in "python3" "python" "py -3"; do
    if $c --version >/dev/null 2>&1; then PY="$c"; break; fi
done
if [[ -z "$PY" ]]; then echo "No Python interpreter found."; exit 1; fi

# Collect .py files, skipping noise.
if [[ -f "$TARGET" ]]; then
    FILES=("$TARGET")
else
    mapfile -t FILES < <(find "$TARGET" -name "*.py" \
        ! -path "*/.git/*" ! -path "*/venv/*" ! -path "*/.venv/*" \
        ! -path "*/__pycache__/*" ! -path "*/node_modules/*" | sort)
fi
if [[ ${#FILES[@]} -eq 0 ]]; then echo "No Python files in: $TARGET"; exit 0; fi

FAIL=0
WARN=0

echo "Validating ${#FILES[@]} Python file(s) in: $TARGET"
echo "----------------------------------------"

for f in "${FILES[@]}"; do
    # HARD (blocks): must compile.
    if ! $PY -m py_compile "$f" 2>/tmp/mate_pyc_err; then
        echo "[FAIL] $f — syntax error:"; sed 's/^/        /' /tmp/mate_pyc_err
        FAIL=$((FAIL + 1)); continue
    fi
    # WARN: over-long lines.
    long=$(awk -v n="$LIMIT" 'length > n' "$f" | wc -l | tr -d ' ')
    if [[ "$long" -gt 0 ]]; then
        echo "[warn] $f — $long line(s) over $LIMIT chars"; WARN=$((WARN + 1))
    fi
    # WARN: module docstring expected in the first lines (non-empty files only).
    if [[ -s "$f" ]] && ! head -3 "$f" | grep -q '"""'; then
        echo "[warn] $f — no module docstring in first lines"; WARN=$((WARN + 1))
    fi
done

echo "----------------------------------------"
echo "Result: $FAIL failure(s), $WARN warning(s)"
[[ $FAIL -gt 0 ]] && exit 1 || exit 0
