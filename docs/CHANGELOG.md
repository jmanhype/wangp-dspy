# CHANGELOG — decision records (ADOPT stories #27–#33)

This file is a **decision-record corpus**, not a release log. Each entry
answers, for one merged ADOPT story: what failure or gap was observed,
what the root cause was, which fix was chosen, which alternatives were
**rejected and why**, and the **measured evidence** behind the numbers.

Entry anatomy:

1. **Observed failure/gap** — the concrete breakage or hole that motivated
   the story.
2. **Root cause** — why it happened.
3. **Chosen fix** — what shipped, in one paragraph.
4. **Rejected alternatives** — at least one, with the reason it lost.
5. **Measured evidence** — commands run and their outputs. Every number in
   this file was measured at write time; none is recalled.

Provenance convention: extraction docs live under
`docs/extraction/shuohao-skills/` (source repo github.com/eternityspring/
shuohao-skills, Apache-2.0). Where an entry discusses gate scope, the
central axiom applies: 误拦的门比没有门更糟——门的信用比数量重要 (a
false-blocking gate is worse than no gate; a gate's credibility matters
more than its count) — `changelog-design-rationale.md:12`, citing source
CHANGELOG:355-356.

---

## #27 — no-proper-nouns gate vs entity registry

PR #27 · merge `7971612` · extraction: `no-names-doctrine.md`

**Observed failure/gap.** Multi-ref shots reference character sheets by
IMAGE, so any name left in the text prompt is pure poison: image models
are heavily biased toward names they recognize and will draw *their*
memory of that character, not ours (`no-names-doctrine.md`, profile-pass.md:28
verbatim: "图像模型对这些偏见极重，会画成它记忆里的角色而不是你的角色").
We had no check anywhere in the pipeline that a proper noun reached a
prompt field.

**Root cause.** Prompt QA was ad-hoc string review; there was no registry
of named entities to match against, and no deterministic gate step.

**Chosen fix.** `gates/no_names_gate.py`: deterministic
`check_no_proper_nouns(text, registry)` — exact, case-insensitive,
word-boundary-anchored matching of names + aliases, longest-surface-wins
overlap, NO LLM/network. Seed `datasets/entity-registry.json` (placeholders
pending bible ingestion; common nouns from banked intents deliberately NOT
entities). `RenderBrief` gains a `registry` kwarg with typed ValueError
rejection beside the meta-hint guard; `registry=None` skips LOUDLY. CLI
`scripts/check_names.py` with exit 0/1/2.

**Rejected alternatives.**
- *Free-text / LLM-based name detection*: rejected — non-deterministic and
  model-dependent; the doctrine's own enforcement is deterministic string
  matching against the cast list, and our zero-model contract requires the
  same.
- *Blocking ALL capitalized words*: rejected — would false-positive on
  legitimate vocabulary (Kodak Vision3, PS2); the 误拦 axiom applies
  directly: a gate that blocks good material destroys its own credibility
  (extraction :12). The registry-scoped match keeps precision high.

**Measured evidence.**
```
$ git show --stat 7971612          # 8 files changed, 568 insertions(+), 1 deletion(-)
$ cd /tmp/wd23r7-verify-7971612 && /Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/python -m pytest --co -q
  -> 282 tests collected at this commit
```
Commit message: "22 tests, zero-model" for the new suite.

---

## #28 — two-round sign-off checkpoint

PR #28 · merge `97318fd` · extraction: `report-assembler.md` /
`changelog-design-rationale.md` section C (claim-fields precursor)

**Observed failure/gap.** Pipeline stages could run end-to-end on a
skeleton that had never been reviewed by a human — stage work built on top
of an unvalidated outline, wasting render budget on bad structure.

**Root cause.** No checkpoint between round-1 skeleton production and the
downstream stages; the pipeline had no notion of "signed off yet?".

**Chosen fix.** Round-1 skeleton module (`predict/skeleton.py`) +
deterministic validator + sign-off gate wired as
`Pipeline.forward_with_skeleton` — the gate runs FIRST (the Boom-collab
test proves zero stage runs before sign-off), with typed
`PipelineStageError` naming id + status. `scripts/review_skeleton.py` is a
zero-model CLI rendering three sign-off questions, violations on stderr,
exit 1 when invalid. Design source: shuohao outline-pass doctrine
(pass-methodology-outline.md L19-26 two-round validation, L17 decision
sentences, L15 evidence-on-decisions).

**Rejected alternatives.**
- *Folding the gate into `forward()`'s default path*: rejected at merge
  time — recorded as a SEAM NOTE in the commit message: `forward()` itself
  stays unchanged; the gated entry point is the documented seam, and
  folding becomes a follow-up once a skeleton PRODUCER exists. Reason:
  changing the default path before a producer exists would gate calls that
  have nothing to gate.
- *Human-in-the-loop via chat confirmation*: rejected — not reproducible
  in CI and not testable; the three-question CLI is deterministic and
  scriptable.

**Measured evidence.**
```
$ git show --stat 97318fd          # 5 files changed, 535 insertions(+)
$ cd /tmp/wd23r7-verify-97318fd && /Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/python -m pytest --co -q
  -> 301 tests collected at this commit
```
Commit message: "19/19 skeleton suite; full suite green except PRE-EXISTING
test_wd_oa4i_tooling manifest failure (verified failing on clean main too)".

---

## #29 — beat-claims claim-fields

PR #29 · merge `4464925` · extraction: `changelog-design-rationale.md`
section C (hookBeat pattern)

**Observed failure/gap.** Beat-grid and lyric-boundary intentions lived as
free prose ("the hook lands early"), so episodes drifted without anyone
noticing — declarations had no machine-checkable form.

**Root cause.** Soft intentions were descriptions, not claims. Upstream
fix (novel-script 1.1.0, source CHANGELOG:482-500): `hookBeat: [scene,
beat]` CLAIMS the hook's location; the gate checks the claim
("衔接从此是门不是自觉" — handoffs become gates, not self-discipline).

**Chosen fix.** `gates/beat_claims.py`: Phrase/BeatGrid/CutClaim/CutRecord
schema + deterministic `validate_beat_claims` (zero-model): unknown phrase
refs, offset bounds, per-cut tolerance override, boundary-inclusive PASS
(exactly-at-tolerance passes, just-beyond fails); unclaimed cuts are
violations (loud); EMPTY_GRID / EMPTY_CUTS raise DISTINCT typed kinds —
loud skip, never silent; typed `BeatClaimValidationError` with
`.violations`. CLI `scripts/check_beat_claims.py` with the check_names.py
pattern (exit 0/1/2, stdin support).

**Rejected alternatives.**
- *Keyword scanning for "hook"/"beat" positions in prose*: rejected —
  keyword scans leak both ways (extraction section B voice case :103);
  position-checkable sub-cases get a claim FIELD, not a text scan.
- *LLM judgment of whether the hook landed*: rejected — non-deterministic;
  the claim-field pattern makes the intention a machine-checkable datum
  first, then the check is pure arithmetic.

**Measured evidence.**
```
$ git show --stat 4464925          # 4 files changed, 502 insertions(+)
$ cd /tmp/wd23r7-verify-4464925 && /Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/python -m pytest --co -q
  -> 316 tests collected at this commit
```
Commit message: "15/15 new tests; full suite 314 passed with ONLY the 2
pre-existing test_wd_oa4i_tooling manifest failures (unchanged vs main)".

---

## #30 — common-actions anti-mush gate

PR #30 · merge `bc92937` · extraction: `gate-array-pattern.md`

**Observed failure/gap.** Shot/action text kept drifting into micro-gesture
"mush" — flickers of doubt, barely-there smiles, one-inch closer — actions
video models cannot render because they've never seen them in training
data at usable frequency.

**Root cause.** No rule enforced that shot actions be things real-life
video contains. Upstream script-pass judgment test (pass-methodology-outline
section 4, RUBRIC A4.2): "is this action common in real-life video?"

**Chosen fix.** `gates/common_actions.py`: `ActionViolation` dataclass
(id/category/matched/span), `check_common_actions` — pure/deterministic/
offline, word-boundary anchored case-insensitive compile (no_names style);
EMPTY_TEXT typed loud skip; `load_actions_registry` with schema validation
(id/pattern/category/rationale all required). `datasets/common-actions.json`:
SAFE seed (documentation-only) + 9 RISKY patterns across 3 categories
(pole-blocks/domino/ricochet; flicker-of-doubt/slight-twitch/barely-there-
smile; one-inch-closer/tilts-by-a-degree/subtle-shift), each citing the
doctrine. Gate-array discipline adopted: `{id,label,ok,detail}` shape,
collect-then-report, optional inputs skip loudly (gate-array-pattern.md
design decisions 1–5).

**Rejected alternatives.**
- *A single monolithic "quality" check*: rejected — the gate-array pattern
  requires per-gate ids so the report, selftest, and gate-log share one
  source of truth; a monolith cannot be skipped, counted, or rewritten
  independently (误拦 axiom: a gate's credibility is per-gate, not
  aggregate).
- *LLM "does this look mushy" scoring*: rejected — non-deterministic and
  unselftestable; the pattern's whole value is zero-model checks that run
  in the selftest for free and cannot flake.

**Measured evidence.**
```
$ git show --stat bc92937          # 6 files changed, 534 insertions(+)
$ cd /tmp/wd23r7-verify-bc92937 && /Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/python -m pytest --co -q
  -> 335 tests collected at this commit
```
Commit message: "full suite 333 passed + 2 PRE-EXISTING manifest failures
(baseline, unchanged vs main)" (collection count includes the 2 known-failing).

---

## #31 — manifest fold / curation amendments

PR #31 · merge `c35dab3` · extraction: `export-pack-spec.md`

**Observed failure/gap.** `build_manifest` output diverged from the
checked-in `datasets/manifest.json`: curation amendments
(`duplicate_takes_dropped`) were not folded into the run_id → (status,
reason) lookup, so rebuilt manifests disagreed with the record of truth.

**Root cause.** `_curation_lookup` only read the base curation table; the
append-only amendment layer (later amendments override earlier ones) was
ignored during rebuild.

**Chosen fix.** `_curation_lookup` now folds
`curation["amendments"][*]["duplicate_takes_dropped"]` into the lookup with
the verbatim reason "duplicate take (kept best-QC sibling)", applied in
list order (append-only semantics preserved). This restores byte-parity
between build output and the checked-in manifest (35 records: 30 kept / 4
dropped / 1 excluded). Tests updated: bank-count assertions 35/30/4/1;
verification iterates ALL `datasets/runs/*.json` (35 rows); new regression
test asserts rebuild == checked-in manifest on every record field
(generated_utc excluded).

**Rejected alternatives.**
- *Regenerating the checked-in manifest from scratch and diffing away
  differences*: rejected — the checked-in file IS the record of truth;
  the rebuild must converge to it, not the reverse (fail-honest accounting
  per export-pack-spec.md design point 4: missing items are listed and
  counted, never silently omitted).
- *Using the per-take descriptions from the ledger as reasons*: rejected —
  recorded in the code comment: byte-parity with datasets/manifest.json
  depends on the exact string "duplicate take (kept best-QC sibling)";
  free-text ledger descriptions would break parity.

**Measured evidence.**
```
$ git show --stat c35dab3          # 2 files changed, 49 insertions(+), 5 deletions(-)
$ cd /tmp/wd23r7-verify-c35dab3 && /Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/python -m pytest --co -q
  -> 336 tests collected at this commit
```
Commit message carries the measured counts: "35 records: 30 kept / 4
dropped / 1 excluded".

---

## #32 — two-class language split + registry fold-in

PR #32 · merge `9595212` · extraction: `language-split-contract.md`

**Observed failure/gap.** Mixed-language prompt fields: engine-bound
prompt fragments occasionally carried non-English text (and human-review
fields carried English where the workflow language differed), producing a
whole class of copy-paste bugs downstream. Upstream had hit it in
production: a redundant local-language TTS field got copied into the
engine ("生产里真踩过", profile-pass.md:20).

**Root cause.** Field language was implicit convention, not a schema
contract; nothing checked which class a field belonged to.

**Chosen fix.** Two-class (three-way) field contract: ENGINE_BOUND fields
locked English, HUMAN_REVIEW fields follow the workflow language, EVIDENCE
never translated (quotes stay verbatim — "它是证据，翻译了就不是证据了",
profile-pass.md:26). `gates/language_gate.py`: FIELD_CLASSES contract for
all three signatures; deterministic `check_language_class` — non-ASCII in
engine fields, English mixing in lang-scoped human fields, verbatim
evidence matching (loud typed NO_SOURCE skip without a source); EMPTY_TEXT
loud skip. `RenderBrief.__post_init__` rejects non-English engine fields
(all 7 sections engine-bound). Registry-through-forward fold-in wires the
entity registry into the pipeline forward path.

**Rejected alternatives.**
- *Relabeling the ambiguous field with a warning instead of deleting it*
  (upstream's explicit rejection, "消除歧义优于解释歧义", source
  CHANGELOG:162): rejected — when a downstream consumer can copy the wrong
  field, DELETE the redundant field rather than relabel it.
- *Full trilingual UI machinery (I18N tables, ui-template)*: rejected per
  extraction PASS section — our artifacts are English-primary; not worth
  the surface.

**Measured evidence.**
```
$ git show --stat 9595212          # 7 files changed, 513 insertions(+), 7 deletions(-)
$ cd /tmp/wd23r7-verify-9595212 && /Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/python -m pytest --co -q
  -> 355 tests collected at this commit
```
Commit message: "RED-first. 19/19 new; FULL suite 355 passed, 0 failed
(repo uv venv)".

---

## #33 — provenance tiers: canon citation vs (inferred) marker

PR #33 · merge `9d0eb2f` · extraction: `inferred-marker-convention.md`

**Observed failure/gap.** Invented bible details were indistinguishable
from canon at generation time — an identity claim that was neither cited
nor marked looked exactly like ground truth, so reviewers (and the model)
could not tell what was decided vs filled-in.

**Root cause.** Identity fields had no provenance tier: no requirement to
cite canon, and no marker for inference.

**Chosen fix.** Two-tier provenance: a canon citation OR exactly one
`(inferred)` marker — no unmarked middle ground, no double-marking
("只用一种标记，不要中英都加"). Markers live in HUMAN fields only and are
stripped at handoff-to-prompt time by `brief_to_prompt` (the seam asserts
marker-free assembled output; a marker reaching the prompt is a typed
rejection — "(inferred) 混进去会被画进画面"). Specific-neutral fallback
gated: no blanks, no hedges. Decision provenance (from/mergeNote) and fact
provenance (inferred) are separate audit trails in the entity registry.
GLM verdict: ADOPT 7/7 zero overrides (WD-qbcj review capture).

**Rejected alternatives.**
- *Bilingual markers (both `(inferred)` and 「（推断）」)*: rejected —
  exactly one marker per item, English report form; dual markers double the
  surface area for the stripping seam to miss.
- *Leaving unresolved fields blank for later fill-in*: rejected —
  specific-neutral fallback commits to a concrete setting; blanks get
  filled by the model's Western-default prior (the no-names-doctrine rule 4
  failure mode).
- *Adopting the rendered-review-surface highlighting now*: deferred per
  extraction ADAPT section — adopt if/when bibles get a rendered review
  surface; until then the marker in JSON plus the near-free "no marker in
  prompt fields" check suffices.

**Measured evidence.**
```
$ git show --stat 9d0eb2f          # 8 files changed, 730 insertions(+), 5 deletions(-)
$ cd /tmp/wd23r7-verify-9d0eb2f && /Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/python -m pytest --co -q
  -> 390 tests collected at this commit
```
Commit message: "Full suite: 390 passed (.venv py3.12). Zero-model
throughout."

---

## #34 — VLM QC failure triage: gate/rule/example classifier + ledger

PR #34 · merge `0db8996` · extraction: `changelog-design-rationale.md`
section B (three-tier escalation ladder; source CHANGELOG:384-398)

**Observed failure/gap.** When a QC failure recurred there was no
recorded decision about which tier absorbs it — a false-positive gate,
a missing rule, or an example gap all looked identical at failure time,
so recurring failures were re-handled ad hoc instead of escalated
deliberately.

**Root cause.** Failure events had no classification step: nothing
distinguished "the gate misfired" from "the rule is right and the
output is wrong" from "we have no training example for this case", so
no tier could be credited or corrected.

**Chosen fix.** `gates/qc_triage.py`: deterministic zero-model
classifier over structured failure events → exactly one of
{gate_false_positive, rule_violation, example_gap}; typed rejection on
ambiguous/unclassifiable events (never silently defaulted); loud skip
kind=empty_text; same pattern as provenance_gate.py. Append-only JSONL
ledger schema (`datasets/qc-triage-ledger.schema.json`) with verbatim
evidence + `stats()` helper (per-class counts, per-gate fire counts,
never-fired list — section G .gates.jsonl discipline). CLI
`scripts/check_qc_triage.py` exit 0/1/2 matching check_provenance.py.
`docs/qc-triage.md` maps the taxonomy onto RenderQC vocabulary (Verdict
PASS/REVISE/REJECT, CONCEPT_ENCODING_FAILURE, QCEscalationError,
GENRE_THRESHOLDS) with the decision procedure "first ask: is this
deterministically judgeable?". The central axiom is carried into our
vocabulary with provenance: 误拦的门比没有门更糟——门的信用比数量重要
(extraction :12, citing source CHANGELOG:355-356) — a triaged
false-positive gets its gate repaired, not another gate stacked on top.
Existing gates and evaluate/render_qc.py untouched: the classifier
consumes their verdicts as input records. No auto rule/doc rewriting
from the ledger — human decides; GEPA auto-accept is a later ADAPT
story.

**Rejected alternatives.**
- *Auto-appending new rules/examples to the registry from the ledger*:
  rejected — the ledger is evidence, not authority; automatic promotion
  would let a single misclassified event rewrite gate behavior (the
  误拦 axiom in action: credibility is earned per-decision, not by
  volume).
- *LLM-based classification of failure events*: rejected — non-
  deterministic and unselftestable; the classifier must run in the
  selftest for free, matching the zero-model contract of every other
  gate in this repo.
- *Silent default classification for ambiguous events*: rejected —
  typed rejection instead; an unclassifiable event that defaults quietly
  poisons the ledger's stats() counts.

**Measured evidence.**
```
$ git show --stat 0db8996          # 5 files changed, 716 insertions(+)
$ grep -c "def test_" <(git show 0db8996:tests/test_qc_triage.py)
  -> 16 tests
$ /Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/python -m pytest --co -q
  -> 406 tests collected at this commit (baseline 390 @ 9d0eb2f)
```
Commit message: "TDD RED->GREEN, cloned from test_provenance_gate.py
conventions (typed violations, seed data, CLI smoke 0/1/2). 16 tests."

---

## Suite trajectory (measured)

Test collection count at each merge commit, measured with
`/Users/Shared/HermesWorkspace/wangp-dspy/.venv/bin/python -m pytest --co -q`
in detached worktrees `/tmp/wd23r7-verify-<sha>`:

| Commit | Story | Collected |
|--------|-------|-----------|
| 7971612 | #27 no-proper-nouns | 282 |
| 97318fd | #28 sign-off checkpoint | 301 |
| 4464925 | #29 beat-claims | 316 |
| bc92937 | #30 common-actions | 335 |
| c35dab3 | #31 manifest fold | 336 |
| 9595212 | #32 language split | 355 |
| 9d0eb2f | #33 provenance tiers | 390 |
| 0db8996 | head (after #34) | 406 |
