# services/jobs — durable jobs + preflight (PR feat/jobs-preflight)

One trusted 3090. No broker, no worker pool, no render farm. Five
pieces, exactly as ruled by the operator on 2026-09-01.

## State diagram

```
            ┌──────────┐
            │  pending │
            └────┬─────┘
                 v
            ┌──────────┐  fail
            │preflight ├──────────────┐
            └────┬─────┘              v
                 v              ┌──────────┐  N=3 same class  ┌────────────┐
            ┌──────────┐        │  failed  ├─────────────────►│ dead_letter│
            │rendering │ ──────►│          │                  └────────────┘
            └────┬─────┘  fail  └────┬─────┘
        render ok│   fail            │ retry (→ preflight)
                 v                   │
   ┌───────────────────────┐         │
   │ rendered_pending_qc   │◄────────┘ (QC unavailable mid-run)
   │  (QC was unavailable; │
   │   NOT failed — parks) │
   └────┬────────────┬─────┘
    QC back        qc fail → failed
        v
   ┌──────────┐
   │   qc     │
   └────┬─────┘
    all clips KEEP
        v
   ┌──────────┐
   │   done   │
   └──────────┘
```

## The five pieces

### 1. Preflight before queue admission (`services/jobs/preflight.py`)
- SSH reachable (`ssh 3090 true`)
- Exact model file paths + sha256 hashes (`sha256sum` per pinned spec)
- Disk headroom (`df -BG --output=avail /mnt/bulk` vs min)
- GPU state: `nvidia-smi --query-compute-apps` — any compute pid =
  stale tenant, named by pid in the failure detail
- QC service availability (`curl -fsS <healthz>`)

All five run BEFORE a job leaves `pending`; any failure blocks
admission with check-level detail naming the offending path/hash/pid.
Host interactions go through `host/render_host.SshHost.run_probe`
(new method on the EXISTING host seam — not a duplicate). Unit tests
stub the host; `tests/test_jobs_integration_3090.py` is the optional
live probe (`WANGP_3090=1`, no render, no GPU use).

### 2. Planning pure, execution separate
- `services/chain/controller.py` (planner) is untouched: it emits
  plans/manifests only.
- `services/jobs/executor.py` is the NEW job executor: SSH/render/
  retry/QC orchestration via injected queue/preflight/render/QC
  collaborators (real run wires the existing WanGPAdapter/SshHost).
- Compile guard (`services/jobs/compile_guard.py`):
  `predict/pipeline.py forward()` raises `CompileContextError` when a
  real (non-None) adapter is present under dspy compile context.
  Detection is VERSION-DISPATCHED across dspy 2.x and 3.x:
  - dspy >= 3 (this repo's .venv runs dspy 3.3.1; verified live):
    stock optimizers wrap teacher rollouts in `dspy.context(trace=[])`,
    which populates `dspy.dsp.utils.settings.thread_local_overrides` —
    empty outside any context, non-empty inside. `trace`'s VALUE is
    indistinguishable from the default (`[]`), so the guard reads the
    OVERRIDES dict.
  - dspy 2.x (read from the 2.5.26 wheel source — the version the
    reviewer's environment ran): `thread_local_overrides` does NOT
    exist there, which made the original 3.3.1-only detection silently
    return "no context" and the guard INERT (reviewer B1). The 2.x
    signal is the `dsp.utils.settings.settings` singleton's per-thread
    context stack: depth 1 = outside any context; every
    `dspy.settings.context(...)` pushes a frame, so depth > 1 means a
    rollout context. (2.x's `DEFAULT_CONFIG.compiling` flag is dead —
    dspy 2.5's own predict.py asserts it is never True.)
  - Explicit `wangp_compile_guard=True` flag (dspy.context accepts
    arbitrary keys on both majors) — belt and suspenders.
  - Fail-closed (reviewer B1b): if NEITHER signal can be read
    (unrecognized dspy layout / import error), `assert_not_compiling`
    raises `CompileContextError` conservatively when an adapter is
    present — the guard never silently opens.

### 3. Durable state machine (`services/jobs/states.py`, `queue.py`)
- SQLite (stdlib sqlite3, WAL) — `JobQueue`.
- Exact vocabulary: pending → preflight → rendering →
  rendered_pending_qc → qc → done | failed | dead_letter; illegal
  pairs raise `InvalidTransition` (also enforced in the DB layer).

### 4. rendered_pending_qc (tonight's live failure mode)
A render completing while QC is UNAVAILABLE lands in
`rendered_pending_qc` — NOT failed. The mp4/log paths are recorded
(artifacts persist while parked), and the executor resumes the job
into `qc` when the service returns. Made structural in
`states.ALLOWED_TRANSITIONS` and executor `_qc_clips`.

### 4b. Stale-active recovery (reviewer B2)
A crash mid-render orphans the job in `rendering` (or
`preflight`/`qc`); `_pick_job()` only selects pending /
rendered_pending_qc, so the job was stuck forever. Fix:
- `JobQueue` schema gains `owner_pid` + `last_heartbeat` (auto-
  migrated; legacy rows are treated as stale).
- `queue.recover_stale_active(staleness_s=600)` (called at the top of
  every `run_once()` / `_pick_job()`): an active-state job whose
  owner pid is dead AND whose heartbeat is older than
  `WANGP_STALENESS_S` (default 600s) transitions `rendering` ->
  `pending` (now an allowed transition, recovery-only) and re-enters
  the queue. Per-clip checkpoints are untouched — done clips are NOT
  re-rendered.
- A job with a LIVE owner pid or FRESH heartbeat is never picked.

### 5. Verify-before-trust + checkpoint resume
- `executor.verify_render_log`: an mp4 is accepted only when the
  render log contains a complete `N/N` Denoising line (regex
  `Denoising\s+(\d+)/\1`). Truncated logs (`15/20`) or missing lines
  fail the clip with the log TAIL (800 chars) + log path captured in
  the failure detail.
- Dead-letter after N=3 failures of the same failure_class
  (class-keyed counter; a new class resets the count).
- Per-chain-clip records (clip_index = services/chain plan clip ids);
  done clips are skipped on relaunch (`--skip-done` semantics in
  `_render_clips`/`_qc_clips`).

## Artifact-path rule
Every artifact claim in a job record carries a path: clip `log`,
`mp4`, and `qc_verdict.path` — enforced by `_check_clip_artifacts`;
status-only records are rejected at write time.

## Tonight's failure modes cited
- QC down while render finished → `rendered_pending_qc` (live, made
  structural — piece 4).
- Accepting an mp4 on exit-code alone after a truncated log →
  step-count verification is now structural (piece 5).

## Render-lane routing (PR feat/ref2va-jobs-routing)

The "two parallel architectures" note is closed: the proven Ref2VA
lane (`host/ref2va_runtime.py`, S4 6/6 live renders) is now reachable
from the jobs layer through ONE routing seam — the adapter is no
longer FL2VA-only.

| job/clip kind                    | model_type            | lane    | renderer |
|----------------------------------|-----------------------|---------|----------|
| `ref2va_render`                  | `ref2va_lip_sync`     | ref2va  | existing `host/ref2va_runtime.run_ref2va_runtime` (reused, not duplicated) via `WanGPAdapter.render_for_job` |
| `shot1_three_ref_recipe`         | fl2va (default)       | fl2va   | existing `build_settings` + wgp path |
| `first_frame_continuation`       | fl2va (default)       | fl2va   | existing path |
| legacy (no kind)                 | —                     | fl2va   | existing path (byte-identical backward compat) |

### Semantic product-mode table (PR #62 amendment)

`services/jobs/modes.py` is the single authority: five product modes,
typed `ModeError` enforcement BEFORE any config emits, and `model_type`
DERIVED from mode + render_profile (a config carrying a raw
`model_type` as input is rejected — it is an output of derivation).

| product mode          | canonical H3                | image_prompt_type | inputs |
|-----------------------|------------------------------|-------------------|--------|
| `FL2VA_TEXT`          | `minimax_h3_fl2va_pruned`    | `T`               | text only (frames + audio refs forbidden) |
| `FL2VA_START_END`     | `minimax_h3_fl2va_pruned`    | `SE`              | requires start + end frames |
| `FL2VA_END_ONLY`      | `minimax_h3_fl2va_pruned`    | `E`               | exactly ONE end-frame ref, start frame forbidden |
| `REF2VA_IDENTITY_AUDIO` | `minimax_h3_ref2va_lip_sync` | `I`             | >=1 image refs + audio_guide; turbo banned when multi-ref (#57 gate) |
| `CONTINUATION`        | orchestration, not a model mode | —             | unwraps to an I2VA/FL2VA-style job + `temporal_strategy` in {`last_frame_chain`, `sliding_window`}; requires a VERIFIED prior-clip artifact |

WanGP L2VA ground truth (encoded in `modes.py`, documented like PR #61's
"SE" finding): there is no separate L2VA model. The FL2VA family
(`models/minimax_h3/minimax_h3_handler.py`) allows
`image_prompt_types_allowed="TSEVL"`, and
`shared/deepy/tool_settings.build_generation_task` derives the flags
from which of `image_start`/`image_end` are set: `S` is added ONLY
when `image_start` exists, `E` only when `image_end` exists. So
end-frame-only = `image_end` with no `image_start` →
`image_prompt_type "E"` — L2VA is a flag combination, not an
architecture.

- `render_lane_for` accepts the four model modes (`REF2VA_IDENTITY_AUDIO`
  → ref2va, the FL2VA trio → fl2va); `CONTINUATION` RAISES at dispatch —
  it must be unwrapped first (`modes.unwrap_continuation`, tested:
  `last_frame_chain` seeds `image_start` from the prior's VERIFIED last
  frame).
- `render_profile` is a sub-object (`pruned`/`int8`/`pdd`/`turbo`/
  `attention`/`steps`/`cache`) — the not-a-mode list lives here and
  nowhere else; unknown keys raise.
- CONTINUATION priors are verify-before-trust: `prior_clip.path` (and
  `last_frame`, when present) must appear in the verified-artifact set
  (job records / manifest); unverified → typed error, never a
  fabricated frame path.

Rules:
- Lane selection: `host/wangp_adapter.job_lane(job)` — kind
  `ref2va_render` or a `model_type` of `ref2va_lip_sync` (job-level or
  inside the embedded #57 `recipe` envelope) routes to ref2va; an
  unknown explicit `model_type` is a typed `WanGPError` (never a
  silent fl2va fallthrough); no lane signal at all = fl2va.
- Executor dispatch: `services/jobs/executor.render_lane_for(kind)` +
  an injected `ref2va_render` callable. A `ref2va_render` clip with no
  ref2va renderer wired FAILS CLOSED (`ref2va_lane_unavailable`),
  never falls back to fl2va. Clip records log the lane (`lane` key on
  `update_clip`; legacy records unchanged).
- Recipe envelope: ref2va jobs carry `image_refs` / `audio_guide` /
  `prompt` / `shot_duration_s` / `audio_provenance` from the #57
  recipe (job-level, or read out of the embedded `recipe` dict).
- Compile guard: `render_for_job` fires
  `assert_not_compiling` BEFORE lane dispatch — BOTH lanes are
  covered, not just the fl2va pipeline path.
- `scripts/run_cycle.py --lane {fl2va,ref2va}` (default fl2va,
  unchanged behavior); ref2va lane honors `WANGP_DRY_RUN=1`
  (adapter=None, planning/evidence only).

## Production render seam (PR feat/production-render-seam)

### Host-truth model names

The 3090 Wan2GP handler (`models/minimax_h3/minimax_h3_handler.py`)
exposes ONLY `minimax_h3_ref2va` and `minimax_h3_ref2va_pruned` —
there is no `minimax_h3_ref2va_lip_sync` handler (the historical
derived name would crash at the host). Canonical derivations now:

| mode | derived model_type |
|---|---|
| FL2VA_TEXT / FL2VA_START_END / FL2VA_END_ONLY | `minimax_h3_fl2va_pruned` |
| REF2VA_IDENTITY_AUDIO | `minimax_h3_ref2va_pruned` |

`services/jobs/modes.HOST_MODEL_ALLOWLIST` holds both real Ref2VA
handler names (+ fl2va); `derive_model_type` fails closed with a
typed `ModeError` if a derivation result is not in the allowlist —
a mode-table drift is caught at derivation time, never on the GPU
box. `host/wangp_adapter.REF2VA_MODEL_TYPE` is the pruned (proven
production) name; the old name survives only as a legacy
`_KNOWN_MODEL_TYPES` alias for git archaeology / old manifests.

### The verified wgp command shape

All host interaction goes through `host.render_host.SshHost`
(`run_probe` seam). The PROVEN serial invocation
(live-verified 2026-09-01):

```
flock /tmp/wgp_queue.lock -c \
  'cd /home/straughter/Wan2GP && PYTHONUNBUFFERED=1 \
   PYTORCH_ALLOC_CONF=expandable_segments:True \
   ./venv/bin/python wgp.py --process <settings.json> \
   --profile 3 --attention sdpa > <log> 2>&1'
```

- The queue lock serializes GPU access; GPU-tenant clearing stays OUT
  (preflight checks GPU state before admission).
- Settings JSON (from the recipe envelope) is written to the run dir
  before invocation.
- VERIFY-BEFORE-TRUST: the log is grepped for a complete
  `<steps>/<steps>` Denoising line (steps = the config's
  `num_inference_steps`) BEFORE the newest `outputs/*.mp4` is
  accepted (`ls -t`). A truncated log is a typed `WanGPError`.
- The newest output is `cp`'d to the job target path.
- Audio mux ONLY when `audio_guide` is present:
  `ffmpeg -y -i <mp4> -i <guide> -map 0:v -map 1:a -c:v copy
  -c:a aac -shortest` (remux lives next to the raw target).

Implementation: `host/wangp_adapter.production_ref2va_render`
(wired as the `_default_render` seam of the ref2va job path; every
step testable with an injected fake host).

### Queue worker entrypoint

`scripts/run_jobs.py --db jobs.db [--once | --loop SECS] [--dry-run]`

- Jobs execute IN ORDER (oldest first) through `JobExecutor`, honoring
  `needs` dependencies: a job whose needs-target is not `done` stays
  pending (blocked jobs never fail, they wait).
- `--once` processes one admissible job then exits; `--loop SECS`
  polls; `--dry-run` emits what would run with NO host calls and no
  state mutation.
- r2i -> fl2va dependency: when an `r2i_pose_target` job completes,
  its last frame is extracted on the host —
  `ffmpeg -y -sseof -0.1 -i <mp4> -frames:v 1 <png>` — into
  `<run_dir>/render/clipNNNN/<r2i job id>_last_frame.png` and recorded
  on the clip as the verified `last_frame` artifact the dependent
  `fl2va_first_last` job consumes.
- CONTINUATION jobs unwrap via `modes.unwrap_continuation` using the
  verified prior last-frame (rule 6 verify-before-trust).

Guard distinction: `scripts/run_cycle.py` KEEPS its ref2va
"dry-run only" guard (`WANGP_DRY_RUN`) — it is a one-shot cycle
driver whose ref2va lane predates this seam. The jobs path
(`run_jobs.py` + `JobExecutor`) removes that guard: it executes
ref2va through the production render seam. Different entrypoints,
different contracts.
