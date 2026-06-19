# Harness components — the map (component observability)

Index of every editable harness component. Each is a file, so the action space is explicit and every
edit is a localized, revertible git diff. The mapping follows the seven AHE component types.

| AHE component | Lives in | Editable by /evolve? | Edit it to... |
|---|---|---|---|
| System prompt | `CLAUDE.md`, `rules/*.md` | yes | change behavior, workflow, constraints |
| Tool description | `skills/*/SKILL.md` | yes | clarify how/when to use a tool or rubric |
| Tool implementation | `skills/vlm-client/scripts/*`, `skills/eval-harness/scripts/*` | scripts yes; **scorer + validator NO** | add capability, fix IO (never weaken the test) |
| Middleware | `settings.json` + `hooks/*.py` | yes | intercept tool calls (secret guard, schema check, logging) |
| Skill | `skills/*/` | yes | add/extend a reusable workflow + domain knowledge |
| Sub-agent | `agents/*.md` | yes | add/tune a delegated specialist |
| Long-term memory | `memory/long_term_memory.md` | yes | record proven strategies, pitfalls, quirks |

Commands in `commands/*.md` drive the loop (`/run`, `/evaluate`, `/evolve`, `/attribute`, `/validate`,
`/review`, `/log`); they are the operator surface, not a separate AHE component.

## Observability artifacts (make evolution measurable)
- `harness/decision_manifest.md` — decision observability: every edit + predicted impact + verdict.
- `harness/evidence/` — experience observability: per-case root-cause reports + `overview.md`.
- `harness/evolution_history.md` — the iteration log.
- git history — one commit per edit = file-level rollback.

## Read-only to the evolve step (controllability)
`dataset/`, the expected labels, `skills/eval-harness/scripts/score.py` + `validate_output.py` (the
test), and `.env`. A higher score must come from better reasoning, never from weakening the test.

## Registering a new component
- New skill: `skills/<name>/SKILL.md` with front-matter `name` + `description` (loads on demand).
- New subagent: `agents/<name>.md` with front-matter `name`, `description`, optional `tools`.
- New command: `commands/<name>.md`, invoked as `/<name>`.
- New hook: `hooks/<name>.py`, registered under the right event in `settings.json`.
- New rule: `rules/<name>.md`, referenced from `CLAUDE.md`.
Then record the addition as a `decision_manifest.md` entry with a predicted impact.

## Cross-platform note
Hook commands use `python` (correct on Windows); on macOS/Linux switch to `python3` if needed. Paths
use `$CLAUDE_PROJECT_DIR`; the logger resolves home via the OS (`~` / `%USERPROFILE%`).
