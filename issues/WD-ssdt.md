---
id: WD-ssdt
title: "Reject content-brief guide duration mismatches before planning"
status: in_progress
priority: 0
type: bug
labels: [bug, delivered]
parent: WD-h73w
created_at: 2026-09-20T23:53:48Z
created_by: speed
updated_at: 2026-09-21T00:16:50Z
content_hash: "sha256:09f5f72c4585862508cf3a177fb1123dd2aa38489e9428a40d0a8aabee01659a"
blocks: [WD-42no]
assignee: dev-WD-ssdt
follows: [WD-z46c, WD-rj6e]
---
## Description
Reject a supplied content-brief guide whose measured duration contradicts the declared turn before any no-GPU plan or run artifact is emitted.

## USER INTENT
The operator wants the no-GPU Content Brief Gateway to refuse physically impossible plans before any render authorization or GPU work, while preserving every existing valid no-GPU plan and every existing QC, AV, and retry gate.

## Context (Embedded)
The LF004 dogfood brief declared four 4.458333333333333 s turns (107 frames at 24 fps), but its four supplied guide WAVs each measure 2.333333 s (56 frames at 24 fps). The generated plan declares `frames`, `audio_length_frames`, `guide_duration_s`, and `shot_duration_s` as 107 / 4.458 for every cut. The render consequently tries to fill about 2.125 s without guide speech; observed failures include repeated/hallucinated speech and double-exposure vision rejection. The accepted LF003 four-cut baseline in WD-rij6 used these same guides at 56 frames per cut and passed the full gate set.

Verified source behavior:

- `predict/content_brief.py` defines `DEFAULT_DURATION_S = 56.0 / 24.0`.
- `predict/content_brief.py -> load_content_brief(path: str | Path) -> ContentBrief` validates `durations_s` through `_positive_number(value: Any, field: str) -> float`, but does not inspect audio duration.
- `predict/content_brief.py -> build_run_film_inputs(brief: ContentBrief, plates_dir: str | Path, *, run_dir: str | Path) -> dict[str, Any]` resolves supplied `audio_paths` and checks existence before its first output side effect, but likewise does not measure duration.
- `scripts/run_content_brief.py -> main(argv: list[str] | None = None) -> int` calls `load_content_brief`, `build_run_film_inputs`, and `run_film(..., dry_run=True)` before canonical plan write.
- `services/director/wiring.py -> plan_to_clips(...)` derives `frames` from the declared duration and emits `shot_duration_s`, `guide_duration_s`, and `audio_length_frames` from that same frame count; it never probes the supplied guide.
- `services/director/renderers/policy.py -> check_guide_duration(guide_duration_s: float, shot_duration_s: float) -> None` compares two supplied values with a `1e-9` threshold. The bad plan makes both values 4.458, so this existing invariant passes trivially.

The preflight comparison of a real ffprobe measurement to a brief-declared duration MUST use an explicit absolute tolerance of `0.000001 s` (one microsecond). This is above ffprobe's six-decimal duration quantization and floating-point noise while being far smaller than one 24 fps frame (`1 / 24 s`); the LF004 discrepancy is about 2.125 s and remains unequivocally rejected.

## Root Cause
No no-GPU planning stage measures supplied guide audio. The gateway validates only positive declared numbers, and the downstream guide/shot equality check receives two plan-declared values rather than one measured value and one declared value.

## Affected Components
- `predict/content_brief.py`
- `scripts/run_content_brief.py`
- `services/director/wiring.py` (existing downstream behavior; modify only if strictly needed for recorded policy provenance)
- `services/director/renderers/policy.py` (existing invariant; do not weaken)
- `tests/test_content_brief.py`

## OUT OF SCOPE
- Starting, resuming, or approving a corrected LF004 render: the corrected plan changes the plan hash and needs explicit future operator authorization under WD-h73w.
- Editing the committed LF004 brief/plan to produce a new approved dogfood plan: that is recovery work, not the planning-integrity bug fix.
- Relaxing, reordering, bypassing, or retuning Whisper, vision, mouth-box, SyncNet, QC, retry, or provenance gates: those gates are outside this bug and remain the epic's acceptance boundary.
- General audio-preparation redesign: `predict/audio_prep.py` intentionally trims/tail-pads raw turn audio during preparation; this story only inspects already-supplied gateway guides. A future feature may extend preparation policy separately.
- Arbitrary filler modes: only explicit recorded tail silence is permitted by this story; any other policy needs a separate design story.

## DIFF BUDGET
- About 3 files and under 250 changed LOC: `predict/content_brief.py`, `tests/test_content_brief.py`, and `scripts/run_content_brief.py` if policy provenance requires CLI propagation. Do not expand into renderer or gate implementations.

## Boundary Map
PRODUCES:
- predict/content_brief.py -> ContentBrief.mapping() -> dict[str, Any]
  spec: optional `audio_filler_policy` is validated, included in the canonical mapping/brief hash, and absent behavior remains byte-for-byte compatible.
- predict/content_brief.py -> build_run_film_inputs(brief: ContentBrief, plates_dir: str | Path, *, run_dir: str | Path) -> dict[str, Any]
  spec: after resolving supplied guides and before `destination.mkdir(...)`, measure every guide with real ffprobe and fail closed on missing/unreadable audio or duration mismatch unless the explicit policy applies.
- scripts/run_content_brief.py -> main(argv: list[str] | None = None) -> int
  spec: preflight rejection returns/exits nonzero without writing the output plan, run ledger, or jobs database; successful no-GPU behavior remains dry-run and queue-free.

CONSUMES:
- (existing): predict/content_brief.py -> DEFAULT_DURATION_S = 56.0 / 24.0
  source: exact declared default used when `durations_s` is absent; it must also participate in the measured-duration check.
- (existing): scripts/run_film.py -> run_film(script_file, plates_dir, *, characters, whisper_map="", durations=None, audio_paths=None, db_path=None, host=None, pre_render=None, lm=None, dry_run=False, run_ledger_path=None, dataset_run_path=None, premise_id=None, continuation_mode=False, whisper_transcriber=None, vision_judge=None)
  source: the CLI's existing no-GPU plan builder call with `dry_run=True`; no new queue or host behavior is authorized.
- (existing): services/director/renderers/policy.py -> check_guide_duration(guide_duration_s: float, shot_duration_s: float) -> None
  spec: emitted plan values must continue to satisfy this exact `1e-9` guide/shot invariant; the new measured-vs-declared preflight uses the explicit `0.000001 s` tolerance above.
- (existing): services/director/wiring.py -> plan_to_clips(script_lines: Sequence[Dict[str, str]], characters: Sequence[dict], plates: Dict[str, Any], *, audio_paths: Optional[Sequence[str]] = None, durations: Optional[Sequence[float]] = None, whisper_map: str = "", run_dir: Optional[str] = None, scene_staging: str = "two characters framed left and right", listening_detail: str = "head tilted, eyes on the speaker", ambience: str = "room tone, faint brazier crackle", loras: Optional[Sequence[str]] = None, re_anchor_every: int = DEFAULT_RE_ANCHOR_EVERY) -> List[Dict[str, Any]]
  source: existing downstream clip emitter; supplied matching guides must remain valid without changing its interface.

## Story Acceptance Criteria
1. When `audio_paths` is present, `build_run_film_inputs(...)` resolves every guide and measures each file with real `ffprobe` before creating `run_dir`, writing `script.txt`, invoking `run_film(...)`, or writing a plan. A missing guide, unreadable guide, failed probe, non-numeric duration, or non-positive duration raises `ContentBriefError` and leaves no output side effects.
2. Unless a valid explicit filler policy applies, each declared turn duration must equal its measured guide duration within `abs(declared_s - measured_s) <= 0.000001`. If `durations_s` is absent, `DEFAULT_DURATION_S` is the declared value. A mismatch raises a `ContentBriefError` identifying the one-based turn, guide path, declared duration, and measured duration.
3. The only permitted mismatch bypass is an optional top-level brief field exactly named `audio_filler_policy` with `mode` equal to `tail_silence`, plus non-empty string `recorded_by` and `reason` fields. Unknown fields or modes are rejected. The policy is included in `ContentBrief.mapping()` and therefore `brief_hash`, and every affected emitted clip records it in `audio_provenance.filler_policy` with `source_duration_s`, `target_duration_s`, `mode`, `recorded_by`, and `reason`.
4. A tail-silence policy may be used only when the declared target is at least the measured source duration after the `0.000001 s` tolerance; it must never authorize trimming a longer guide or concealing an unrecorded mismatch.
5. A supplied real guide matching the declared (or default) duration is accepted. Its emitted `guide_duration_s`, `shot_duration_s`, `audio_length_frames`, and `keeper_window_s` remain mutually consistent and continue to pass `check_guide_duration(guide_duration_s: float, shot_duration_s: float) -> None`.
6. Briefs without `audio_paths` continue to materialize silent guides at the declared/default duration and produce the existing canonical no-GPU plan; existing valid briefs without `audio_filler_policy` retain their prior brief hash and successful queue-free behavior.
7. The LF004 shape is regressively rejected before planning: four real 2.333333 s guides paired with four declared 4.458333333333333 s turns produce no plan or run artifacts. The LF003-equivalent shape from WD-rij6—four real 56-frame/`56 / 24` second guides with matching declarations—is accepted.
8. `main(argv: list[str] | None = None) -> int` fails closed on every preflight rejection without writing `--output`, a run ledger, or a jobs database, and successful execution retains `summary.dry_run == True`, `summary.gpu_work == False`, and `summary.queue_submitted == False`.
9. No Whisper, vision, mouth-box, SyncNet, retry, QC threshold, provenance requirement, or renderer policy is weakened, removed, skipped, or reordered.

## Testing Requirements
- Unit: cover duration absence/defaulting, positive-number behavior, exact filler-policy schema, policy inclusion in the brief hash, declared-versus-measured tolerance, and typed errors for missing/corrupt/unreadable guides.
- Integration: MANDATORY (no mocks). Invoke the real `scripts/run_content_brief.py -> main(argv: list[str] | None = None) -> int` path with real WAVs produced through ffmpeg and measured through the real ffprobe binary. Cover at minimum: matching guide accepted; LF004-style mismatch rejected; missing guide rejected; corrupt/non-probing guide rejected; valid recorded `tail_silence` policy accepted and recorded; no-audio default plan accepted.
- Negative integration assertions MUST verify absence of the output plan, `run_dir`, run ledger, and jobs database, not merely an exception type.
- Commands: `uv run --frozen --extra dev pytest -q tests/test_content_brief.py` and `git diff --check`; add any targeted policy-test command if coverage is split into another existing test file.
- No GPU, remote host, queue, model inference, or render execution is permitted while implementing or verifying this story.

## Discovered During
WD-h73w dogfood execution: the governed LF004 render failed closed after three cut-2 QC attempts; disk evidence showed the declared 107-frame turns paired with 56-frame guide audio. WD-rij6 is the accepted 56-frame four-cut control using the same guides.

## MANDATORY SKILLS
- pvg — required for story governance and delivery evidence.

## Delivery Requirements
- Developer must paste exact unit/integration command output summaries and negative-path artifact-absence checks into nd notes.
- Developer must include an AC verification table mapping every AC to code, test, and artifact evidence.
- Developer must confirm source diff inspection shows no QC/AV/retry gate change.
- Developer must update the authoritative `nd_contract` to delivered and add the `delivered` label using the pvg workflow.

## nd_contract
status: new

### evidence
- Created: 2026-09-20 from measured LF004 guide-duration mismatch evidence under WD-h73w and the accepted WD-rij6 56-frame control.

### proof
- [ ] Pending implementation

## Acceptance Criteria


## Design


## Notes
## Implementation Evidence (DELIVERED)

PROOF:

### CI/Test Results
- Commands run:
  - `uv run --frozen --extra dev pytest -q tests/test_content_brief.py`
  - `uv run --frozen --extra dev pytest -q`
  - `uv run --frozen --extra dev pytest --collect-only -q`
  - `uv run --frozen --extra dev --with pytest-cov pytest -q --cov=predict.content_brief --cov-report=term tests/test_content_brief.py`
  - `git diff --check`
  - `pvg verify predict/content_brief.py tests/test_content_brief.py --format=text`
- Targeted result: PASS, 19/19 executed (0 skipped).
- Full-suite result: exit 0; 1,553 collected, 1 pre-existing live-3090 skip, therefore 1,552 passed and 0 failed.
- Coverage: `predict/content_brief.py` 169 statements, 15 missed, 91%.
- Exact targeted tail:

```text
...................                                                        [100%]
```

- Exact full-suite tail (quiet mode does not print a count line):

```text
.................                                                        [100%]
=============================== warnings summary ===============================
.venv/lib/python3.14/site-packages/fastapi/testclient.py:1
  /Users/Shared/HermesWorkspace/wangp-dspy/.claude/worktrees/dev-WD-ssdt/.venv/lib/python3.14/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable.html
```

- A separate `-rs` full run identified the sole skip as `tests/test_jobs_integration_3090.py:20: set WANGP_3090=1 to run the live 3090 preflight probe`. It was not run because this story forbids GPU/remote work.
- `git diff --check`: PASS (empty output).
- `pvg verify`: `VERIFY: PASSED (2 files scanned, 0 issues)`.
- Real local toolchain: `/opt/homebrew/bin/ffmpeg` and `/opt/homebrew/bin/ffprobe`, both version 8.0.1. Integration fixtures are generated through ffmpeg and measured through ffprobe with no mocks or skip conditions.

### Commit / PR
- Branch: `story/WD-ssdt`
- Commit: `e8660db6d7588f147e7a6a6ae2a3ec2bd6480f7b`
- PR: https://github.com/jmanhype/wangp-dspy/pull/148
- Diff budget: 2 files, 175 insertions, 1 deletion (176 changed lines, below 250).

### AC Verification
| AC | Requirement | Code Location | Test / Artifact Evidence | Status |
|---|---|---|---|---|
| 1 | Resolve and really probe every supplied guide before output side effects | `predict/content_brief.py:283-296` (missing check, real ffprobe loop, first mkdir afterward) | `tests/test_content_brief.py:79-106`, `:146-162`, `:190-246`; negative assertions cover no run dir; CLI cases reject missing and corrupt guides | PASS |
| 2 | Declared/default duration must match measured duration within `0.000001 s`, with typed turn/path/declared/measured mismatch detail | `predict/content_brief.py:17`, `:238-245`, `:288-292` | `tests/test_content_brief.py:114-118` (tolerance), `:146-162` and `:190-246` (real mismatch) | PASS |
| 3 | PM Amendment supersedes declaration bypass; fallback is no filler policy | `predict/content_brief.py:19-22` leaves `audio_filler_policy` unknown; `:64-75` mapping/hash remains unchanged | `tests/test_content_brief.py:128-143` rejects the field; `:71-75` pins the no-policy brief hash | PASS (materialized-filler variant deliberately dropped under amendment) |
| 4 | No declaration may authorize trimming/concealing a mismatch | Same guard at `predict/content_brief.py:238-245`, `:288-292`; no bypass branch | Every mismatch test at `tests/test_content_brief.py:146-162`, `:190-246` is rejected | PASS (PM-amendment fallback) |
| 5 | Matching supplied guide remains valid and emitted guide/shot/frame/window values remain consistent | Guard accepts equality at `predict/content_brief.py:238-245`; unchanged downstream emitter `services/director/wiring.py:286-303` | `tests/test_content_brief.py:164-188` checks 56 frames, audio frames, keeper window, and calls unchanged `check_guide_duration` | PASS |
| 6 | No-audio/default behavior and prior no-policy brief hash remain compatible | `predict/content_brief.py:282-293` probes only supplied guides; mapping unchanged at `:64-75` | `tests/test_content_brief.py:59-76` pins prior hash; `:248-277` validates canonical no-audio no-GPU plan | PASS |
| 7 | LF004 shape rejected; LF003-equivalent 56-frame shape accepted | Mismatch guard at `predict/content_brief.py:288-292` | `tests/test_content_brief.py:146-162` and mismatch CLI case `:190-246` use 2.333333 s vs 4.458333333333333 s; `:164-188` accepts four 56-frame/default-duration real WAVs | PASS |
| 8 | CLI fail-closed before plan/ledger/jobs; success remains no-GPU/queue-free | `scripts/run_content_brief.py:50-53` preflights before `run_film`, `:54-64` dry run, `:86-95` summary/plan write | `tests/test_content_brief.py:190-246` asserts plan, run dir, run ledger, and jobs DB are absent for all negative CLI cases; `:164-188` and `:248-277` assert dry-run/no-GPU/no-queue summary | PASS |
| 9 | No gate/retry/renderer semantics changed | Diff contains only `predict/content_brief.py` and `tests/test_content_brief.py`; `services/director/renderers/policy.py` is byte-identical to main | `git diff --stat`; `tests/test_content_brief.py:164-188` invokes existing `check_guide_duration` unchanged | PASS |

### Gate / Scope Non-Regression
- Source diff inspection: only `predict/content_brief.py` and `tests/test_content_brief.py` changed.
- No change to Whisper, vision, mouth-box, SyncNet, QC threshold, retry, provenance, renderer, `services/director/wiring.py`, or `services/director/renderers/policy.py`.
- `check_guide_duration` retains its existing `1e-9` guide-vs-shot comparison; the new measured-vs-declared preflight is separate and uses `0.000001 s`.
- No GPU, render, remote host call, queue submission, or model inference was performed. The committed LF004 brief/plan dataset was not edited.

LEARNINGS:
- ffprobe's six-decimal duration output is comfortably sufficient for the mandated one-microsecond planning tolerance, including the LF004's multi-second discrepancy.
- Putting the ffprobe/probe-output parsing and duration comparison in small helpers made it possible to test numeric fail-closed paths and the tolerance directly without mocking the real integration path.
- The PM amendment's no-policy fallback kept the change inside budget while preserving the invariant that the renderer consumes a guide whose real duration already matches the declared turn.

### OBSERVATIONS (unrelated)
- The full suite contains an environment-gated live 3090 test and two pre-existing warning sources; details are below.
- `pvg notes search 'content brief guide duration ffprobe'` failed in this checkout because `.paivot/config.yaml` names vault `Claude`, while the available vault is `.vault`; a direct vlt search of `.vault` returned no additional context. Story context remained complete through `pvg nd show WD-ssdt`.

### DISCOVERED_BUG (pre-existing test/infrastructure issues)
  title: Full suite still has an environment-gated live 3090 test
  context: The full suite reports one skip at tests/test_jobs_integration_3090.py:20 (`set WANGP_3090=1`). It could not be executed under this story's no-GPU/no-remote constraint.
  affected_files: tests/test_jobs_integration_3090.py
  discovered_during: WD-ssdt

  title: FastAPI TestClient emits Starlette deprecation warning
  context: Full-suite runs warn from .venv/lib/python3.14/site-packages/fastapi/testclient.py:1 that using httpx with starlette.testclient is deprecated. This is dependency/test-client behavior outside the story's allowed files.
  affected_files: tests/qc/audio_critic tests importing fastapi.testclient; project dependency versions
  discovered_during: WD-ssdt

  title: Cold-cache prompt-director test emits invalid escape warning
  context: The first full-suite run emitted SyntaxWarning at tests/test_prompt_director.py:195 for `"\w"`. Subsequent cached runs did not repeat it, but the source issue remains outside this story's allowed diff scope.
  affected_files: tests/test_prompt_director.py
  discovered_during: WD-ssdt

  title: Repo notes adapter names an unavailable vault
  context: pvg notes search fails because .paivot/config.yaml sets notes vault to `Claude`, but vlt reports available vaults including `.vault` and not `Claude`.
  affected_files: .paivot/config.yaml
  discovered_during: WD-ssdt

## PM Amendment (dispatcher review, 2026-09-20)

Supersedes the declaration-only bypass semantics in AC #3 and AC #4. All other
acceptance criteria, tests, budget, and out-of-scope entries stand unchanged.

1. The guard compares the declared turn duration against the measured duration of
   the guide artifact that the render will actually consume.
2. A measured/declared mismatch is rejected. No field value — including
   `audio_filler_policy` — may by itself authorize acceptance of a guide whose
   measured duration differs from the declared duration.
3. `audio_filler_policy` is retained only if the implementation materializes the
   filler into the prepared guide (for example tail silence appended with real
   ffmpeg, then measured with real ffprobe) so that the measured duration of that
   prepared artifact equals the declared duration within `0.000001` s. The guard
   then verifies the materialized artifact; the policy is recorded in
   `audio_provenance.filler_policy` for audit, and is never an acceptance bypass.
4. If materializing the filler exceeds the story's diff budget, drop
   `audio_filler_policy` from this story entirely and reject every
   measured/declared mismatch. A later story may add materialized padding.

Rationale: the LF004 failure was the renderer filling unfilled speech time by
repeating the intended line (post-Whisper 0.167 on seeds 904 and 905) and by
double-exposure motion (seed 906). A declaration that changes no audio byte would
re-open exactly that failing configuration while making it look governed.
AC #7 (LF004 shape regressively rejected; WD-rij6 56-frame shape accepted) stands
as written and is the primary regression.

## nd_contract
status: new

### evidence
- Created 2026-09-20 from measured LF004 guide-duration mismatch evidence under WD-h73w and the accepted WD-rij6 56-frame control.
- Dispatcher review 2026-09-20: story verified against source; a declaration-only filler bypass was rejected and replaced by a materialization requirement.

### proof
- [ ] Pending implementation.

## History
- 2026-09-20T23:53:58Z dep_added: blocks WD-42no
- 2026-09-21T00:02:05Z status: open -> in_progress
- 2026-09-21T00:02:05Z auto-follows: linked to predecessor WD-z46c
- 2026-09-21T00:02:05Z claimed by dev-WD-ssdt
- 2026-09-21T00:16:50Z status: in_progress -> in_progress
- 2026-09-21T00:16:50Z auto-follows: linked to predecessor WD-rj6e

## Links
- Parent: [[WD-h73w]]
- Blocks: [[WD-42no]]
- Follows: [[WD-z46c]], [[WD-rj6e]]

## Comments
