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
  Signal (read from dspy 3.3.1 source + verified live): every stock
  optimizer wraps teacher rollouts in `dspy.context(trace=[])`, which
  populates the thread-local overrides dict — outside any context
  that dict is empty. `trace`'s VALUE is indistinguishable from the
  default (`[]`), so the guard reads the OVERRIDES dict, plus an
  explicit `wangp_compile_guard=True` flag our own harness sets
  (verified: dspy.context accepts arbitrary keys).

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
