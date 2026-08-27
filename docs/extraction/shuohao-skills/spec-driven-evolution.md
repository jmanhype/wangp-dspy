# Spec-Driven Skill Evolution (superpowers plans + specs) — extraction from shuohao-skills

Source: github.com/eternityspring/shuohao-skills (clone at /tmp/shuohao-skills), Apache-2.0, © 2026 烁皓 (eternityspring). Extracted 2026-08-27 for WD-4k56 follow-up (parent WD-j9nx).

## Mechanism (our terms)

The repo contains one worked example of a **spec → plan → implementation** cycle using the "superpowers" method (obra/superpowers-style), for migrating the `shot-recipes` skill into a new private repo:

**1. The SPEC** (`docs/superpowers/specs/2026-08-21-shot-recipes-repository-migration-design.md`, 114 lines) — a pure decision document. Fixed sections: 目标 (goal, incl. the success invariant "只有一个权威副本；两个仓库都可以独立安装、测试和维护") / 仓库与目录 (layout) / 迁移范围 (scope, including what is explicitly NOT migrated — "分段说明.md 不属于 skill，不迁移也不提交") / 历史策略 (history strategy: clean snapshot, with the reason — old repo has only one commit for the skill) / 旧仓库清理 (source cleanup list) / 提交与 GitHub 流程 (branch names, draft PRs, staging policy) / 验证 (the exact commands both repos must run) / 失败与恢复 (recovery: old repo content remains in Git history; never stash/reset user's uncommitted work). Every non-obvious choice carries its reason inline.

**2. The PLAN** (`docs/superpowers/plans/2026-08-21-shot-recipes-repository-migration.md`, 501 lines) — the executable decomposition. Structure:
- Header block addressed to **agentic workers**: "REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development… Steps use checkbox syntax for tracking." One-line Goal, an Architecture paragraph (the key invariant: "Treat the current working-tree snapshot as the authoritative 1.1.0 source. Import and publish that snapshot first; only after the private remote contains a verified copy may the old directory be deleted"), Tech Stack, and a pointer back to the spec.
- **Global Constraints** section: absolute paths, repo names, visibility, staging bans ("do not use `git add .`"), and sequencing safety ("Never delete the old skill directory until the new repository tests pass").
- **File Map**: every file to create/modify/delete, listed before any task.
- **Tasks → Steps**, each step = a shell command block + an "Expected:" line stating the observable outcome (e.g. "`git branch --show-current` prints `codex/import-shot-recipes`… `PRIVATE`"). Steps are individually verifiable; failure conditions gate progression ("If either test fails, stop before creating or deleting repository content").

The notable property: **the plan is machine-executable by a fresh agent with zero conversation context** — every decision lives in the spec, every command and expected-output in the plan. The pair is a template for delegating risky multi-repo operations without judgment drift.

**3. Relationship to the rest of the repo:** this is a one-off so far (single spec/plan pair), but it demonstrates the workflow the skills themselves encode: decisions frozen in a design doc BEFORE a 500-line step list exists, and the step list written so verification is mechanical. It pairs with the CHANGELOG's evidence-first culture (see changelog-design-rationale.md): spec = why, plan = how, changelog = what was learned.

## File:line references (into /tmp/shuohao-skills)

- `docs/superpowers/specs/2026-08-21-shot-recipes-repository-migration-design.md:1-9` — goal + single-authoritative-copy invariant
- `:22-33` — scope incl. explicit non-goals ("不迁移也不提交")
- `:35-42` — history strategy with rationale
- `:84-95` — the verification command lists (both repos)
- `:97-105` — failure & recovery (git history as safety net; no stash/reset of user work)
- `docs/superpowers/plans/2026-08-21-shot-recipes-repository-migration.md:1-3` — agentic-worker header + required sub-skill
- `:5-9` — Goal/Architecture/Spec-pointer block ("Import and publish that snapshot first; only after… may the old directory be deleted")
- `:22-31` — Global Constraints (staging bans, sequencing safety)
- `:33-47` — File Map (create/modify/delete enumerated before tasks)
- `:60-105` — Task 1 steps with Expected: outcomes ("If either test fails, stop before creating or deleting")

## Verbatim key excerpts

```text
// plan:1-2
> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development …
// plan:7
**Architecture:** Treat the current `skills/shot-recipes/` working-tree snapshot as the authoritative 1.1.0 source.
Import and publish that snapshot first; only after the private remote contains a verified copy may the old directory be deleted.
// plan:22
- Never delete the old skill directory until the new repository tests pass and the import branch is pushed to GitHub.
// spec:97-98
迁移期间旧仓库原始内容仍在 Git 历史中……用户现有未提交内容不通过 stash、reset 或 checkout 改写。
```

## RECOMMENDATION vs SGFLIX bible pipeline / wangp-dspy / X-content

**ADOPT**
- The spec/plan pair as the standard format for our own multi-step agent operations (kanban lanes, repo migrations like the gist-archive restructures, WanGP pipeline rollouts): spec = decisions+reasons+verification commands+recovery; plan = constraints → file map → steps each with an "Expected:" observable. This maps directly onto our `writing-plans` / `subagent-driven-development` skills — the shuohao example is a clean, minimal instance of that pattern and worth keeping as a reference exemplar.
- "Expected:" line discipline on every step: cheap, makes delegated execution self-verifying (matches our empirical-verification ethos: the executor can't claim success without matching the expected output).
- Recovery section as mandatory plan component (what state is recoverable, what is never touched).

**ADAPT**
- The superpowers sub-skill reference: our stack uses Hermes delegate_task / kanban lanes rather than superpowers; keep the "for agentic workers" header but point at our tooling.

**PASS**
- The migration's specifics (gh draft-PR flow, private repo creation) — one-time operational detail, not methodology.
