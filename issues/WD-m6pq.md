---
id: WD-m6pq
title: "Bug: Skill Router misses explicit skill invocations"
status: in_progress
priority: 0
type: bug
parent: WD-wzbl
created_at: 2026-09-19T03:28:09Z
created_by: speed
updated_at: 2026-09-19T03:35:37Z
content_hash: "sha256:818c26bc2979a73d3d766f02fb8e2af0b46eb543a1d3e54a369770f458d7336b"
labels: [discovered-by-pm, delivered]
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
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-18.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence

### CI/Test Results
Commands run:
 - /usr/bin/python3 -m py_compile /Users/speed/.codex/skill-router/hook.py /Users/speed/.codex/skill-router/test_router.py
 - /usr/bin/python3 -m unittest discover -s /Users/speed/.codex/skill-router -p 'test_router.py' -v
 - pvg verify /Users/speed/.codex/skill-router/hook.py /Users/speed/.codex/skill-router/test_router.py /Users/speed/.codex/skill-router/README.md --format=text
 - Static security/scope scan over hook, tests, and README.
 - Fresh Codex app-bundle exec integration probe with one-time reviewed hook-trust bypass.
Summary: compile PASS; tests PASS 13/13, 0 failures, 0 errors, 0 skipped; pvg verify PASS with 0 issues; fresh process PASS with exact requested skill and one automatic hash-only event.
Coverage: syntax matrix, real-index exact resolution, natural-language false-positive check, unknown skill fallback, malformed stdin, missing database, existing symptom-ranking behavior, and fresh UserPromptSubmit integration.
Commit SHA: cc6eb8053290f54f1389cf05b59b11339923e20952b094ba8adb41fd4a4bd01c
This is the deterministic machine-global artifact-manifest SHA, not a wangp-dspy Git commit.

### Implementation
- Added .
- Added exact normalization and longest-match selection to prevent broad Supabase CLI 2.75.0

Usage:
  supabase [command]

Quick Start:
  bootstrap            Bootstrap a Supabase project from a starter template

Local Development:
  db                   Manage Postgres databases
  gen                  Run code generation tools
  init                 Initialize a local project
  inspect              Tools to inspect your Supabase project
  link                 Link to a Supabase project
  login                Authenticate using an access token
  logout               Log out and delete access tokens locally
  migration            Manage database migration scripts
  seed                 Seed a Supabase project from supabase/config.toml
  services             Show versions of all Supabase services
  start                Start containers for Supabase local development
  status               Show status of local Supabase containers
  stop                 Stop all local Supabase containers
  test                 Run tests on local Supabase containers
  unlink               Unlink a Supabase project

Management APIs:
  backups              Manage Supabase physical backups
  branches             Manage Supabase preview branches
  config               Manage Supabase project configurations
  domains              Manage custom domain names for Supabase projects
  encryption           Manage encryption keys of Supabase projects
  functions            Manage Supabase Edge functions
  network-bans         Manage network bans
  network-restrictions Manage network restrictions
  orgs                 Manage Supabase organizations
  postgres-config      Manage Postgres database config
  projects             Manage Supabase projects
  secrets              Manage Supabase secrets
  snippets             Manage Supabase SQL snippets
  ssl-enforcement      Manage SSL enforcement configuration
  sso                  Manage Single Sign-On (SSO) authentication for projects
  storage              Manage Supabase Storage objects
  vanity-subdomains    Manage vanity subdomains for Supabase projects

Additional Commands:
  completion           Generate the autocompletion script for the specified shell
  help                 Help about any command

Flags:
      --create-ticket                                  create a support ticket for any CLI error
      --debug                                          output debug logs to stderr
      --dns-resolver [ native | https ]                lookup domain names using the specified resolver (default native)
      --experimental                                   enable experimental features
  -h, --help                                           help for supabase
      --network-id string                              use the specified docker network instead of a generated one
  -o, --output [ env | pretty | json | toml | yaml ]   output format of status variables (default pretty)
      --profile string                                 use a specific profile for connecting to Supabase API (default "supabase")
  -v, --version                                        version for supabase
      --workdir string                                 path to a Supabase project directory
      --yes                                            answer yes to all prompts

Use "supabase [command] --help" for more information about a command. from shadowing .
- Explicit candidates use score 1.0 and term_overlap 1.0.
- Explicit resolution runs before FTS ranking and returns exactly one candidate.
- Ordinary prompts retain the existing FTS path.
- Updated README to document explicit invocation behavior.

### Fresh Integration
- Prompt form: explicit .
- Event count increased from 22 to 23.
- Fresh Codex final message reported  with score 1.0.
- Event recorded prompt SHA-256 , duration 264 ms, and no raw prompt.
- The model correctly explained anon-role RLS filtering versus service-role bypass.

### Scope/Security
- Hook registration hash unchanged: .
- Config hash unchanged: .
- Static scan found no network, subprocess, eval/exec, or stub markers.
- No raw prompt persistence, hook-registration change, or automatic skill execution was added.
- Changed artifact hashes:
  - hook.py 
  - test_router.py 
  - README.md 

### AC Verification
| AC | Status | Evidence |
|---|---|---|
| 1 | PASS | Syntax matrix covers all six requested forms. |
| 2 | PASS |  does not resolve explicitly; longest exact match prevents broad prefix shadowing. |
| 3 | PASS | Explicit handle returns one requested skill at score 1.0. |
| 4 | PASS | Candidate name/path come from SQLite and use existing shape. |
| 5 | PASS | Existing symptom-specific and short-domain tests pass. |
| 6 | PASS | Unknown explicit, malformed, and missing-database tests pass fail-open/fallback behavior. |
| 7 | PASS | Static scan and hashes confirm no prohibited behavior/registration changes. |
| 8 | PASS | 13/13 tests pass, 0 skipped. |
| 9 | PASS | pvg verify reports 0 issues. |

LEARNINGS:
- Explicit invocation must be parsed as a distinct command syntax; literal skill-name occurrence is not enough.
- Longest normalized-name selection is necessary when one skill name is a prefix of another.
- An early explicit-marker check avoids spending resolver time on ordinary prompts.

## nd_contract
status: delivered

### evidence
- RED, tests, pvg verify, static scan, unchanged registration/config hashes, fresh Codex process, event-log delta, and artifact hashes recorded above.

### proof
- [x] AC #1: all explicit syntax forms resolve.
- [x] AC #2: exact normalization avoids natural-language false positives.
- [x] AC #3: explicit request returns exactly one score-1.0 candidate.
- [x] AC #4: candidate uses indexed name/path and existing shape.
- [x] AC #5: non-explicit ranking remains unchanged and tested.
- [x] AC #6: unknown/malformed/missing-state paths fail open or fall back.
- [x] AC #7: no prohibited behavior added.
- [x] AC #8: full suite passes 13/13.
- [x] AC #9: pvg verify is clean.

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
- 2026-09-19T03:32:28Z status: open -> in_progress
- 2026-09-19T03:32:28Z claimed by dev-WD-m6pq
- 2026-09-19T03:35:15Z status: in_progress -> in_progress

## Links
- Parent: [[WD-wzbl]]
- Follows: [[WD-8r8a]]

## Comments

### 2026-09-19T03:31:49Z speed
loop: reset orphaned in_progress to open (no developer worktree found; prior session presumed dead)

### 2026-09-19T03:35:37Z speed
## Implementation Evidence (DELIVERED)

Commands run:
 - /usr/bin/python3 -m py_compile /Users/speed/.codex/skill-router/hook.py /Users/speed/.codex/skill-router/test_router.py
 - /usr/bin/python3 -m unittest discover -s /Users/speed/.codex/skill-router -p 'test_router.py' -v
 - pvg verify /Users/speed/.codex/skill-router/hook.py /Users/speed/.codex/skill-router/test_router.py /Users/speed/.codex/skill-router/README.md --format=text
 - Fresh Codex app-bundle exec integration probe with one-time reviewed hook-trust bypass
Summary: compile PASS; tests PASS 13/13 with 0 failures, 0 errors, and 0 skipped; pvg verify PASS with 0 issues; fresh process PASS with exact requested skill and one automatic hash-only event.
Commit SHA: cc6eb8053290f54f1389cf05b59b11339923e20952b094ba8adb41fd4a4bd01c
This SHA is the deterministic machine-global artifact manifest snapshot, not a wangp-dspy Git commit.

Implementation:
- Added resolve_explicit_invocation with exact command-syntax parsing and longest normalized-name selection.
- Explicit candidates return with score 1.0 before FTS ranking.
- Non-explicit prompts retain the existing ranking path.
- README documents explicit invocation behavior.

Fresh integration:
- Event count increased from 22 to 23.
- Fresh Codex reported supabase-rls-frontend-debugging at score 1.0.
- Event duration was 264 ms and stored only the prompt hash and candidate metadata.

Scope and security:
- Hook registration and config remained unchanged.
- Static scan found no network, subprocess, eval, exec, or stub markers.
- No raw prompt persistence, hook registration change, or skill execution behavior was added.
- Changed artifact hashes: hook.py 3b4546e67cdd4111266d861e16e868eec5ed9eaeb99a52cd37dad74f52de793c; test_router.py 55fad915e2a9d4dca834a34b45eaa5863cc938f86769fcfc2ab21b6458442bc1; README.md 010e5f6876d62ed57801014132e0928099ac9bb29ecab388dd9f738d2e2fe8c0.

## nd_contract
status: delivered

### evidence
- RED/GREEN tests, pvg verify, static scan, unchanged registration/config hashes, fresh Codex integration, event delta, and artifact hashes are recorded in Notes and this comment.

### proof
- [x] AC #1: all six explicit syntax forms resolve.
- [x] AC #2: exact normalization prevents natural-language false positives.
- [x] AC #3: explicit requests return exactly one score-1.0 candidate.
- [x] AC #4: candidate uses indexed name/path and existing shape.
- [x] AC #5: non-explicit ranking behavior remains covered.
- [x] AC #6: unknown/malformed/missing-state paths fail open or fall back.
- [x] AC #7: no prohibited behavior added.
- [x] AC #8: full suite passes 13/13.
- [x] AC #9: pvg verify reports zero issues.

