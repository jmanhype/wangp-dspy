# PLAN — <one-line title of the change>

> **For agentic workers:** REQUIRED SUB-SKILL: Use Hermes
> `delegate_task` (subagent-driven development) or a kanban lane. Steps
> use checkbox syntax for tracking. This plan is written to be
> machine-executable by a fresh agent with ZERO conversation context:
> every decision lives in the spec, every command and expected output
> lives here. If you find yourself making a judgment call that is not
> answered by this file, STOP and report — do not improvise.

**Goal.** <One sentence, copied from the spec's Goal.>

**Architecture.** <The key invariant(s) that order the work — e.g. "Treat
the current working-tree snapshot as the authoritative source. Import
and publish that snapshot first; only after the remote contains a
verified copy may the old directory be deleted".>

**Tech Stack.** <Languages, runtimes, tools, exact interpreter/venv paths
(e.g. `/Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/python`).>

**Spec.** `docs/specs/<date>-<slug>.md` — decisions and reasons live
there; this file never re-litigates them.

## Global Constraints

- Absolute paths only: <repo root>, <worktree roots>.
- Repo names / visibility: <name, private/public>.
- Staging ban: explicit `git add <path>` per file; **never `git add .`**.
- Sequencing safety: <e.g. "Never delete X until Y passes and branch Z
  is pushed">. State every condition under which a destructive step is
  permitted; absence of a condition means the step is forbidden.
- Tier boundary: <docs-tier / code-tier / test-tier — what this plan may
  and may not touch>.

## File Map

Every file created / modified / deleted, listed BEFORE any task. A task
that touches a file not on this map is out of scope — stop and report.

| File | Action | Task |
|------|--------|------|
| `<path>` | create / modify / delete | N |

## Tasks

### Task 1 — <name>

- [ ] **Step 1.1** — <what, one line>

```bash
$ <command>
```

Expected: <observable outcome, exact where possible — e.g. "`git branch
--show-current` prints `feat/wd-xxxx-slug`".>

Failure gate: <what observation means STOP instead of retry — e.g. "If
either test fails, stop before creating or deleting repository
content".>

- [ ] **Step 1.2** — <what>

```bash
$ <command>
```

Expected: <observable outcome.>

Failure gate: <stop condition.>

### Task 2 — <name>

- [ ] **Step 2.1** — <what>

```bash
$ <command>
```

Expected: <observable outcome.>

Failure gate: <stop condition.>

## Final verification

```bash
$ <full-suite / end-to-end command>
```

Expected: <measured green count, pasted verbatim from the real run into
the PR description.>
