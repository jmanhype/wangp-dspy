# Rebase Required for Speed — `verified`

Fork @`cb84f4f`: **16.7 s/step**. Rebased onto upstream main
(branch `rebase-onto-upstream`): **5.23 s/step** — **3.2x faster**.

- Upstream deepy optimizations + RTX-3090 tuning are required; the
  stale fork does not carry them.
- `multi_prompts_gen_type=FG` is needed for multiline prompts.

## Evidence

- RENDER-LOGS-0830: step-time measurements before/after rebase on the
  same 3090, same profile (`--profile 3 --attention sdpa`).
- WANGP-UPSTREAM: Wan2GP upstream main history (deepy optimization
  commits between cb84f4f and main).
- 3090 checkout: `/home/straughter/Wan2GP`, branch `rebase-onto-upstream`.

## Consequences

- ~3 min/shot at 56 frames post-rebase (was ~16 min/shot on the fork).
