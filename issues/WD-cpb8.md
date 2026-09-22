---
id: WD-cpb8
title: "First-class content surface: wgp content and the first-run capability report"
status: closed
priority: 1
type: feature
labels: [product, verification, accepted]
created_at: 2026-09-22T20:19:12Z
created_by: speed
updated_at: 2026-09-22T21:14:45Z
content_hash: "sha256:823944d93a0df66e1c75a8647ef2f7141ac2fec41c28cc991a3407c72460aa21"
assignee: dev-WD-cpb8
closed_at: 2026-09-22T20:56:09Z
close_reason: "Accepted: exact-head CLI/read-only/tests/CI checks pass; 970-line overrun is proportionate to the broad capability report and real-process tests"
---

## Description
## USER INTENT
Observable outcome: a user who wants a film never sees internal script paths. One verb turns a committed content brief plus plates into a reviewed, governed plan, tells the user exactly what will be generated and where it will run, and refuses to pretend when the machine cannot do the work. A companion first-run report states what this machine can do: no-GPU planning, host-backed rendering, which models are present, what would be downloaded, and what is missing.

## Context (Embedded)
- The planning engine already exists and is deterministic: `scripts/run_content_brief.py` and `wgp plan` produce the canonical `wangp-dspy.content-plan/v1` summary (`clip_count`, `planned_duration_s`, `dry_run`, `gpu_work`, `queue_submitted`). `wgp doctor` already reports readiness with a remediation per check, `wgp brief validate` validates a brief, and jobs are submitted only through the governed queue.
- Maestro (the reference product) auto-detects GPU/VRAM/RAM on first launch, picks a profile, reports download status, and surfaces a recovery banner. The parity target here is an explicit, honest, local first-run capability report rather than a silent guess.
- Deliberate boundary: this story adds the product front door and the capability report. It does not add new model families or generation modalities; those are separate capability stories. Where a capability does not exist, the report and the wrapper must say so instead of implying support.

## OUT OF SCOPE
- Executing a GPU render, contacting a host, downloading models, or mutating remote state.
- Adding new model families, modalities (image, music, voice, sound effects), or an editor/GUI.
- Bytes-identical re-encoding claims or any change to gate thresholds, retry policy, provenance semantics, or queue transitions.
- Publishing to a registry, creating a tag, or any credential use.

## DIFF BUDGET
- Roughly 5 files, under 300 authored changed LOC.

## Boundary Map
PRODUCES:
- wangp/content.py -> `build_content_request(brief, plates, ...)` and the render of a human plus JSON content summary that names what will be generated, the resolved host requirement, and the exact governed command that a real render would run.
- wangp/environment.py -> `describe_capabilities(repository_root, *, environ) -> CapabilityReport`: platform and Python, ffmpeg/ffprobe presence, local accelerator visibility (for example `nvidia-smi` when present, otherwise an explicit "no local accelerator" statement), RAM and disk headroom, resolved host configuration state, model-manifest presence and per-entry verification status, and the explicit list of capabilities that are NOT implemented yet.
- wangp/cli.py -> `wgp content --brief <path> --plates <dir> [--out <plan.json>] [--submit] [--json]` and `wgp doctor --capabilities [--json]`, following the established exit-code contract (0 clean, 2 typed input/configuration failure, 3 host-dependent operation without a complete host configuration, 4 unexpected internal).
- tests/test_content_and_capabilities.py -> real-process tests for the new verbs.
- docs/content.md -> the content verb, the capability report, and the honest list of unimplemented capabilities.
CONSUMES:
- wangp/cli.py -> `plan`, `brief validate`, `doctor`, and `status` stay the underlying behaviours; the content verb orchestrates them rather than duplicating them.
- wangp/config.py -> `load_host_config` remains the single host-resolution seam and must not gain hidden defaults.
- wangp/diagnostics.py -> typed, redacted diagnostics with a remediation and a next command.

## Required Outcomes
1. `wgp content --brief <committed brief> --plates <dir>` validates and plans in the no-GPU lane, prints a human-readable summary of what would be generated (clip count, speakers, planned duration, resolved host requirement), and exits 0 with `gpu_work=false` and `queue_submitted=false`; `--json` emits the same facts as a stable object.
2. `wgp content --submit` without a complete host configuration exits 3 with one actionable message naming the exact missing configuration keys and the next command, and submits nothing; with a complete configuration it prints the exact governed queue command it would run without executing a render.
3. `wgp doctor --capabilities` reports the local facts truthfully: when no local accelerator is present it says so explicitly, when a model manifest is absent it says what would be needed, and it always lists the generation capabilities that are not implemented yet instead of implying support.
4. Capability reporting never contacts a host and never mutates anything: no SSH, no network, no GPU call, no file writes outside temporary storage.
5. An invalid brief or plates directory produces a typed diagnostic (exit 2) with the observed problem, a remediation, and a next command, and no partial plan is written.
6. All outputs are redacted through the existing diagnostics helper, and no host, credential, or absolute operator path leaks into the JSON form.

## Testing Requirements
- Real-process, no mocks: `uv run --frozen --extra dev pytest tests/test_content_and_capabilities.py -q` plus the full `uv run --frozen --extra dev pytest -q`.
- Tests must drive the installed `wgp` through subprocess and assert real exit codes, including the unconfigured-host failure and the invalid-brief case.
- Tests must assert that no SSH, network, or GPU call occurs (for example by shadowing `ssh`/`nvidia-smi` and asserting zero invocations) and that the repository stays byte-identical.

## MANDATORY SKILLS
- pvg

## Delivery Requirements
- Developer must paste targeted and full-suite output, the real human and JSON outputs for both verbs, and the exact-head CI conclusion into notes.
- Developer must include an AC verification table and read-only before/after hash evidence.
- Developer must use `pvg story deliver`.
- No GPU, SSH, model download, network, tag, or push to main is authorized; the story branch and its PR are the only push target.

## Acceptance Criteria


## Design


## Notes
## Rework Evidence

- Head: `3283f30add5093b6223bf619b0c28a84425f70bf` (PR #160).
- Finding 1 fixed: omitted-output content now retains its temporary plan/run; no printed continuation references a cleaned path.
- Finding 2 fixed: `doctor --capabilities --db` and `--probe-host` now fail typed exit 2 instead of silently skipping work.
- Finding 3 fixed: mismatched and unreadable local model files report `hash_mismatch`/`unreadable` with `download_required=true`.
- Finding 4 fixed: empty and path/digest-invalid manifests report typed invalid configuration, not present/usable.
- Finding 5 fixed: dialogue control characters/newlines are rejected before script or ledger creation.
- Finding 6 fixed: complete-host `--submit` atomically queues four chained clips into `run/jobs.db`, prints the worker command for that existing DB, and does not execute the worker/render.
- Finding 7 fixed: auto-discovery normalizes legacy `path` to local verification.
- Tests: targeted 12 passed/0 failed; full 1,675 passed, 1 skipped/0 failed; one warning.
- Build: one wheel `0dd903963acbb556b0ebf03891e3655717847c4394c88f10a2ae96efd851c6db`; one sdist `c80d3c2be740eb46542117d8f518f9037f84128402297ea0a0ea62cd53a12345`.
- Fresh CLI captures: no-submit says nothing was queued; complete submit shows `queue_submitted=true` plus existing DB `[('pending', 4)]`; unconfigured submit exits 3; capabilities+DB exits 2; zero shadowed SSH/nvidia-smi calls.
- CI at exact head: `test` completed `success`, run `35785033563`.

## nd_contract
status: accepted

### evidence
- PM closeout applied via pvg story accept on 2026-09-22.

### proof
- [x] Story closed after accepted label was applied.


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-22.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence

Summary: Added the content front door and honest local capability report with real-subprocess exit-code, redaction, read-only, forbidden-call, manifest, build, and CI verification.

Commands run:
- `uv run --frozen --extra dev pytest tests/test_content_and_capabilities.py -q` → exit 0; output `..... [100%]`; 5 collected/passed, 0 failed.
- `uv run --frozen --extra dev pytest -q` → exit 0; 1665 collected, 1664 passed, 1 skipped (`s`), 0 failed; one Starlette deprecation warning.
- `uv build --out-dir /tmp/wd-cpb8-build.MEdacY` → exit 0; one wheel and one sdist.
- `git push -u origin story/WD-cpb8` → exit 0; pushed only `story/WD-cpb8`.
- `gh pr create --base main --head story/WD-cpb8 ...` → PR #160.
- `gh api repos/jmanhype/wangp-dspy/commits/e396542313122bf45fa21791c074a60cb7fa5a28/check-runs` → `test` completed `success`.
- Read-only baseline/final tracked dataset digest: `7eec7b126f82bf57c08cdc586ea5addb21fc93996f3e78eb84a9d638f8924fc3` both times; final `git status --short` empty.
- Shadowed `ssh` and `nvidia-smi` transcript: 0 bytes / 0 invocations.

SHA: e396542313122bf45fa21791c074a60cb7fa5a28

### CI/Test Results

Targeted real-process result:

```text
.....  [100%]
exit=0
```

Full-suite real-process result:

```text
[100%]
1 warning, 0 failures
exit=0
1665 tests collected; observed one `s` and all other dots passing
```

Captured `wgp content` human output:

```text
content=LF004 Operator Dogfood: Borrowed Sunrise
would_generate clip_count=4 speakers=Tess,Rho planned_duration_s=9.332
host_requirement=unconfigured (missing host.target,host.wgp_root,host.wgp_python); no-GPU planning needs no host
governed_queue_command=uv run --frozen --extra dev python -m scripts.run_jobs --db <captured-temp-run>/jobs.db
gpu_work=false queue_submitted=false
exit=0
```

Captured `wgp content --json` output:

```json
{"brief_hash":"sha256:67202d3597affeab4e5edcf15a1acef2f5e88ed00950ce17ff3012f5bb0472cd","governed_queue_command":"uv run --frozen --extra dev python -m scripts.run_jobs --db '<run-dir>/jobs.db'","host_requirement":{"configured":false,"contacted":false,"missing_keys":["host.target","host.wgp_root","host.wgp_python"]},"schema_version":"wangp-dspy.content-request/v1","submission_requested":false,"summary":{"clip_count":4,"dry_run":true,"gpu_work":false,"planned_duration_s":9.332,"queue_submitted":false,"speakers":["Tess","Rho","Tess","Rho"]},"what_will_be_generated":{"clip_count":4,"planned_duration_s":9.332,"speakers":["Tess","Rho","Tess","Rho"]}}
```

Captured unconfigured `wgp content --submit` output:

```text
diagnostic code=HOST_CONFIGURATION_INCOMPLETE severity=error: Content submission requires a complete render host
  observed: missing host keys: host.target, host.wgp_root, host.wgp_python (environment variables: WANGP_SSH_TARGET, WANGP_WGP_ROOT, WANGP_WGP_PYTHON)
  why: A partial host configuration cannot identify one safe renderer.
  remediation: Set the named keys in the environment or wangp.toml, then review the resolved local capability report before submission.
  next: wgp doctor --capabilities
  details: {"host_contact": false}
exit=3; no plan or queue database written
```

Captured complete-host submit preview:

```text
host_requirement=configured (not contacted)
governed_queue_command=uv run --frozen --extra dev python -m scripts.run_jobs --db /private/var/folders/7q/tx7m0tg12m5cgq7k8z8q2dzw0000gn/T/wd-cpb8-evidence/work/run/jobs.db
gpu_work=false queue_submitted=false
submission=preview_only; content did not execute the queue command
exit=0; no render or queue worker executed
```

Captured `wgp doctor --capabilities` output:

```text
platform=Darwin arm64
python=CPython 3.14.4
ffmpeg=available ffprobe=available
local_accelerator=no local accelerator (nvidia-smi not found on PATH)
ram_available_bytes=7377649664
disk_free_bytes=141490978816
host_configuration=incomplete (missing host.target, host.wgp_root, host.wgp_python)
model_manifest=absent entries=none
implemented=no-GPU content planning; host-backed rendering through the governed queue when explicitly configured
not_implemented=image generation; music generation; speech/voice cloning; sound effects; upscaling; face refinement; video editing; GUI
collection=read_only network_access=false host_contact=false
exit=0
```

Build artifacts:

```text
wangp_dspy-0.1.0-py3-none-any.whl sha256=6bb0b08da30d82e2755185c2dd43437c8cc74791bc8779da8dfedfe03692cc12
wangp_dspy-0.1.0.tar.gz sha256=dbf8e16bccebff7dfa2c2a1933ce5fb043d214ca4527fe2b7e152163082339ae
```

GitHub check run:

```text
name=test status=completed conclusion=success
url=https://github.com/jmanhype/wangp-dspy/actions/runs/35782265446/job/106930400144
```

### AC Verification

| AC | Result | Evidence |
|---|---|---|
| AC 1: committed brief plans in the no-GPU lane with stable human/JSON facts | PASS | Targeted test; captured human/JSON outputs show 4 clips, Tess/Rho, 9.332s, `gpu_work=false`, `queue_submitted=false`. |
| AC 2: submit fails closed without host and only prints the governed queue command with complete host | PASS | Real exit 3 diagnostic names exact keys/env vars/next command and writes nothing; complete-host real exit 0 prints queue command without render. |
| AC 3: capability report is honest about accelerator, manifest, and unsupported generation | PASS | Real output says `no local accelerator`; manifest absent remediation; all eight unimplemented capabilities listed. |
| AC 4: capability reporting is read-only with no host/network/GPU call or unintended writes | PASS | Tests shadow SSH/nvidia-smi and assert zero calls; tracked repository digest unchanged; captured forbidden-call file is empty. |
| AC 5: invalid brief/plates produce typed exit 2 with no partial plan | PASS | Real tests assert diagnostic observed/remediation/next and absent plan/run outputs for invalid brief and plates. |
| AC 6: outputs use existing redaction and JSON leaks no host, credential, or absolute operator path | PASS | Content/environment mappings use `redact_sensitive`; tests reject `/Users/`, temporary paths, and configured host in JSON. |

## nd_contract
status: delivered

### evidence
- Implementation, tests, documentation, build, CLI transcripts, repository/dataset hashes, and CI are recorded above at SHA `e396542313122bf45fa21791c074a60cb7fa5a28`.

### proof
- [x] AC #1: no-GPU committed-brief content summary and stable JSON facts are verified.
- [x] AC #2: host-incomplete submission exit 3 and complete-host command preview are verified.
- [x] AC #3: truthful accelerator, model-manifest, implemented, and unimplemented capabilities are verified.
- [x] AC #4: read-only collection with zero SSH/GPU invocations and unchanged tracked bytes is verified.
- [x] AC #5: invalid brief/plates typed exit 2 with no partial plan is verified.
- [x] AC #6: redacted JSON without host, credential, or absolute operator path is verified.

## History
- 2026-09-22T20:19:18Z status: open -> in_progress
- 2026-09-22T20:19:18Z claimed by dev-WD-cpb8
- 2026-09-22T20:48:56Z status: in_progress -> in_progress
- 2026-09-22T20:56:09Z status: in_progress -> closed

## Links


## Comments
