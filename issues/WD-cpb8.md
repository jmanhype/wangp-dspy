---
id: WD-cpb8
title: "First-class content surface: wgp content and the first-run capability report"
status: open
priority: 1
type: feature
labels: [product, verification]
created_at: 2026-09-22T20:19:12Z
created_by: speed
updated_at: 2026-09-22T20:19:12Z
content_hash: "sha256:61e14b53842f4f47804097a51efd4677585ef4065dc9e882defea9552b3e137a"
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


## History


## Links


## Comments
