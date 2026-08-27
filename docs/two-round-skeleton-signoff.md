# Two-round skeleton sign-off (round-1 checkpoint)

Adopted from shuohao-skills outline-pass doctrine:
`docs/extraction/shuohao-skills/pass-methodology-outline.md`
— two-round skeleton validation **L19-26**; decision sentences
**L17**; evidence-on-decisions **L15**.

## The discipline

Round 1 is a cheap "fast version": fill the four structural blocks,
validate deterministically, STOP, and go to the USER for sign-off.
Round 2 refines after feedback and re-validates. Rationale (L26,
translated): the fast round is cheap — "an error costs one skeleton,
not 60 episode synopses" (错了只损失一轮骨架，不是 60 集梗概).

The three sign-off questions that invalidate everything downstream
(L19-26): **which lines were cut / which people were merged / where
the major beats land.** In our flow the expensive artifacts are the
8-page IDENTITY_LOCK character bibles and rendered briefs; a wrong
direction was previously only caught at QC — after render spend.

## Round-1 artifact (`predict/skeleton.py`)

- `cuts`: every cut with its `why` (L15: evidence on decisions)
- `merges`: who merged, why, `from_source` provenance
- `payoff`: major-beat episode placement + total episodes
- `cut_note` / `merge_note`: the two decision sentences that
  headline the review (L17: "the story ends at…" / why this lead
  group — complete arcs)
- `signoff`: status pending/approved/rejected, reviewer, ts

## Deterministic validation (zero-model)

`validate_skeleton(skel) -> list[str]` violations; typed
`SkeletonValidationError` via `raise_on_invalid=True`. Rules: all
four blocks present and nonempty; every cut/merge carries a nonempty
why; payoff majors ascending, in range, first major within the first
2 episodes (no start vacuum), adjacent gap ≤ 3, last major within
the final 3 (no end vacuum), earliest major not the final episode
alone; both decision sentences present. No LLM anywhere.

## Sign-off gate

`Pipeline.forward_with_skeleton(intent, skeleton=...)` refuses to
run any stage while `signoff.status != "approved"` — typed
`PipelineStageError` (stage "signoff") naming the skeleton id and
status. The gate runs before director/selector/assembler/adapter
(pinned by a test whose collaborators are Boom stubs). Explicit
seam note: `Pipeline.forward` itself is unchanged this slice — the
gate lives in `forward_with_skeleton`, the documented entry point
for gated runs; folding it into `forward`'s default path is the
follow-up once the skeleton PRODUCER exists (a skeleton must come
from somewhere before every run can require one).

## Review tooling

`python -m scripts.review_skeleton <skeleton.json>` pretty-prints
the skeleton with the three questions rendered explicitly and
validation violations on stderr; exit 1 when invalid.
