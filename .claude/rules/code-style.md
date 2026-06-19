---
description: Code and explanation style. Concise by default.
---

# Code Style

## Code
- Python 3. Every module starts with a one-line docstring; every public function/class gets a short
  docstring.
- Descriptive names (`extract_claim`, not `doIt`); constants `UPPER_SNAKE_CASE`; booleans
  `is_` / `has_` / `can_`.
- Comment *why*, not *what* — one line is usually enough.
- Keep lines under ~100 chars. No dead or commented-out code. Prefer the standard library.
- Match the existing style of the file you're editing.

## Explanations
- Be concise and direct (the user's stated preference): make the point once, clearly. No filler.
- Reach for an analogy or a worked example only when it helps a hard concept land — not by default.
- The user is learning here, so a tight "why it works this way" is welcome where it adds understanding.
