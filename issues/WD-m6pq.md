---
id: WD-m6pq
title: "Bug: Skill Router misses explicit skill invocations"
status: open
priority: 0
type: bug
parent: WD-wzbl
created_at: 2026-09-19T03:28:09Z
created_by: speed
updated_at: 2026-09-19T03:31:49Z
content_hash: "sha256:238ed987d82346f193f6bce8c98cc2251d0c5e639f1a878b1a7ebdca54d46668"
labels: [discovered-by-pm]
assignee: dev-WD-m6pq
follows: [WD-8r8a]
---

## Description
## Context (Embedded)
The accepted 50-prompt local calibration report found two prompts classified as explicit skill invocations, and the router missed the requested skill in both cases (`explicit_skill_invocation.top1 = 0/2`). The general ranking path is useful, but explicit operator requests must not compete probabilistically with other skills.

The router currently reads `/Users/speed/.codex/skill-router/hook.py`, tokenizes the prompt, queries SQLite FTS5, and returns candidates through `handle_payload(payload: Dict[str, Any], config: Dict[str, Any]) -> Tuple[str, List[Dict[str, Any]]]`. The index table exposes at least `name` and `path`.

## USER INTENT
When the operator explicitly names a skill, Codex must receive that exact skill as the router's first and only candidate so it can read the corresponding SKILL.md immediately.

## Root Cause
`handle_payload` sends every prompt through lexical FTS ranking. There is no pre-ranking resolver for unambiguous explicit invocation syntax.

## Affected Components
- `/Users/speed/.codex/skill-router/hook.py`
- `/Users/speed/.codex/skill-router/test_router.py`
- Local SQLite index: `/Users/speed/.codex/skill-router/skills.sqlite3`

## Boundary Map
PRODUCES:
- `/Users/speed/.codex/skill-router/hook.py` -> `resolve_explicit_invocation(connection: sqlite3.Connection, prompt: str) -> Dict[str, Any] | None`
- `/Users/speed/.codex/skill-router/hook.py` -> `handle_payload(payload: Dict[str, Any], config: Dict[str, Any]) -> Tuple[str, List[Dict[str, Any]]]` with exact-invocation precedence

CONSUMES:
- WD-59q6: `/Users/speed/.codex/skill-router/skills.sqlite3` -> `skills` FTS5 table columns `name TEXT`, `path TEXT`
- WD-o1xf: `/Users/speed/.codex/skill-router/hook.py` -> one-token exact-name boost and symptom-ranking behavior remain unchanged

## Acceptance Criteria
1. `resolve_explicit_invocation` recognizes these unambiguous forms against the indexed skill name:
   - `$alpha-widget-debugging`
   - `use skill alpha-widget-debugging`
   - `use the alpha-widget-debugging skill`
   - `invoke skill alpha-widget-debugging`
   - `load skill alpha-widget-debugging`
   - `skill: alpha-widget-debugging`
2. Matching is exact after casefold and separator normalization; `define a goal` must NOT resolve as `define-goal`.
3. When an explicit invocation resolves, `handle_payload` returns exactly one candidate: the requested indexed skill, with score `1.0`.
4. The explicit candidate contains the correct `name` and `path` from SQLite and follows the existing candidate dictionary shape.
5. Non-explicit prompts retain the current FTS ranking path and existing symptom-specific behavior.
6. Missing database, malformed input, SQLite errors, and unknown requested skills continue to fail open or fall back to ordinary ranking without blocking.
7. No network calls, raw-prompt persistence, hook-registration changes, or automatic skill execution are added.
8. The full router test suite passes with no skipped tests.
9. `pvg verify` on `hook.py` and `test_router.py` reports zero issues.

## Testing Requirements
- Unit: exact syntax matrix, casefold matching, hyphen/space normalization, unknown skill, and natural-language false-positive case (`define a goal`).
- Integration: use the real 405-skill SQLite index to resolve an actual installed skill by explicit name and verify path.
- Fail-open: malformed stdin and missing database continue to return `{}` / abstain.
- Commands:
  - `/usr/bin/python3 -m unittest discover -s /Users/speed/.codex/skill-router -p 'test_router.py' -v`
  - `pvg verify /Users/speed/.codex/skill-router/hook.py /Users/speed/.codex/skill-router/test_router.py --format=text`

## OUT OF SCOPE
- Jev reranking or embeddings: network/semantic inference is not needed for exact syntax.
- Global threshold tuning: the 50-prompt report recommends against changing general scoring.
- Automatic index refresh: separate infrastructure concern.
- Reading or persisting raw prompt history: calibration already produced hash-only evidence.

## DIFF BUDGET
- ~2 files, under 150 changed LOC.

## Skills To Use
- `factory-first` applies to implementation routing, but this machine-global hook is security-sensitive and is implemented directly under the established Paivot infrastructure exception.

## Delivery Requirements
- Developer must paste exact test and verify output summaries into nd notes.
- Developer must include an AC verification table and artifact hashes.
- Developer must use `pvg story deliver`; do not close the task directly.

## Discovered During
Task WD-8r8a: 50-prompt local calibration found `explicit_skill_invocation.top1 = 0/2`; report path `/Users/speed/.codex/skill-router/calibration-20260919-natural50.json`.

## nd_contract
status: new

### evidence
- Created 2026-09-19 from accepted calibration report SHA-256 `e2ef842e5913dada6aa899307a26444a57f4dafea1a6b221fd0f36bdfe873972`.

### proof
- [ ] Pending implementation


## Acceptance Criteria


## Design


## Notes
## nd_contract
status: in_progress

### evidence
- Claimed 2026-09-19 under the machine-global infrastructure exception; changes are confined to /Users/speed/.codex/skill-router and no repository worktree applies.

### proof
- [ ] RED tests and implementation pending.

## History
- 2026-09-19T03:28:36Z status: open -> in_progress
- 2026-09-19T03:28:37Z auto-follows: linked to predecessor WD-8r8a
- 2026-09-19T03:28:37Z claimed by dev-WD-m6pq
- 2026-09-19T03:31:49Z status: in_progress -> open

## Links
- Parent: [[WD-wzbl]]
- Follows: [[WD-8r8a]]

## Comments
