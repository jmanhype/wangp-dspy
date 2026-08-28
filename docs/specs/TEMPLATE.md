# SPEC — <one-line title of the change>

Status: DRAFT → APPROVED (flip at sign-off; a plan may only be written
against an APPROVED spec) · Story: WD-xxxx · Author: <name/agent> · Date: YYYY-MM-DD

Format source: `docs/extraction/shuohao-skills/spec-driven-evolution.md`
(spec = why, plan = how, changelog = what was learned). This is a pure
DECISION document: no step lists, no commands that mutate state. Every
non-obvious choice carries its reason inline — a reader with zero
conversation context must be able to reconstruct *why* from this file
alone.

## Goal

<One or two sentences: what exists after this work that does not exist
now.>

**Success invariant.** <The single checkable statement that defines done,
e.g. "只有一个权威副本；两个仓库都可以独立安装、测试和维护" style: one sentence
a reviewer can verify mechanically. If you cannot write it, the goal is
not yet concrete enough.>

## Layout & scope

<What gets created/modified/deleted, and where — directories, modules,
files by path. The PLAN's File Map will enumerate per-task detail; here
you fix the shape.>

**Non-goals.** <Explicit list of things this story does NOT do, each with
a one-line reason. Example: "分段说明.md 不属于 skill，不迁移也不提交".
A non-goal without a reason is a future dispute.>

## History strategy

<How prior state is carried forward: clean snapshot vs full history
rebase vs append-only ledger vs in-place edit. State the strategy AND
the reason — e.g. "clean snapshot, because the old repo has only one
commit for the skill; preserving it buys nothing".>

## Cleanup & sequencing

<What gets removed or retired, in what order, and the safety condition
for each removal. Removals are ordered so that at every point in the
sequence the system is in a working state (see the plan's Global
Constraints for the machine-checkable form of these conditions).>

## Commit & GitHub flow

- Branch naming: `<pattern>` (e.g. `feat/wd-xxxx-<slug>`).
- PR policy: draft first / direct; required reviewers or gates.
- Staging policy: explicit file staging only (`git add <path>`);
  **never `git add .`** — one stray file in a commit undoes the
  docs-tier/code-tier boundary this repo runs on.
- Merge policy: who merges, when, and whether force-push is ever
  permitted (default: never).

## Verification

Exact commands, expected output stated. A verification section whose
commands have no expected output is a promise, not a check.

```bash
$ <command 1>
# Expected: <observable outcome, exact where possible>

$ <command 2>
# Expected: <observable outcome>
```

Full-suite gate: `<exact command>` must report the measured green count
(paste the real tail line into the PR description).

## Failure & recovery

- What state is recoverable if a step fails mid-way: <e.g. "old content
  remains in Git history; roll back by checking out the pre-change
  ref">.
- What is NEVER touched during recovery: <e.g. "user's uncommitted work
  is never rewritten via stash/reset/checkout">.
- Who decides when a failure is a stop-the-world vs a retry: <role>.
