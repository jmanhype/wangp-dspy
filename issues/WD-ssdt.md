---
id: WD-ssdt
title: "Reject content-brief guide duration mismatches before planning"
status: open
priority: 0
type: bug
labels: [bug]
parent: WD-h73w
created_at: 2026-09-20T23:53:48Z
created_by: speed
updated_at: 2026-09-20T23:53:48Z
content_hash: "sha256:0bd22489c649d938a4dd054521bf0f624a2e92d57701d907a8e4fdf6fa8c9edd"
blocks: [WD-42no]
---

## Description
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

## Acceptance Criteria
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


## History
- 2026-09-20T23:53:58Z dep_added: blocks WD-42no

## Links
- Parent: [[WD-h73w]]
- Blocks: [[WD-42no]]

## Comments
