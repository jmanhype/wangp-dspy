---
id: WD-altn
title: "Capability report includes the download plan and the current implemented surfaces"
status: open
priority: 1
type: feature
labels: [capability, verification]
created_at: 2026-09-23T04:24:58Z
created_by: speed
updated_at: 2026-09-23T04:24:58Z
content_hash: "sha256:612eb0097ba5d8bdae7d8fb7ab975fe99e3837b63bbc9cd7ba3f1ef125e6cc78"
---

## Description
## USER INTENT
Observable outcome: one command answers a stranger's three first-run questions — what is this machine, what would be downloaded, and what is not implemented. Today `wgp doctor --capabilities` reports the hardware profile and the not-implemented list but says only that the model manifest is absent; the download plan lives in a separate verb (`wgp first-run download`), so the capability report cannot answer "what would download" on its own.

## Context (Embedded)
- Verified at main `57fcb76`: `wgp doctor --capabilities` emits platform, python, ffmpeg/ffprobe, `local_accelerator`, RAM/disk, host-configuration state, model-manifest state (`absent`, entries `[]`, remediation) and the not-implemented capability list. Its JSON has no download-plan member.
- `wgp first-run download` already computes the durable asset state without downloading: per-entry status and what would be required, with an explicit operator gate for any resume.
- The implemented list in the capability report predates the video, image and music planning surfaces that have since landed (WD-6tox, WD-pcen, WD-soa4). It should name the planning surfaces that genuinely exist while keeping generation explicitly unimplemented.

## OUT OF SCOPE
- Downloading, fetching, or installing anything; contacting any host; GPU work; paid providers.
- Any change to renderer, queue, QC/AV, gate, retry, recipe or release-verification semantics.
- Any capability claim beyond what a recorded run bundle proves: planning surfaces may be described as planning; generation must stay explicitly unverified.

## DIFF BUDGET
- Roughly 3 files, under 120 authored changed LOC.

## Boundary Map
PRODUCES:
- wangp/environment.py -> the capability report gains a `download_plan` member reused from the existing `first-run download` computation (never a second implementation of it), and the implemented/not-implemented lists are corrected to name the planning surfaces that exist.
- wangp/cli.py -> `wgp doctor --capabilities` human output prints the download plan summary (counts, per-entry status, and what would be required) while keeping the existing read-only, no-host guarantees and exit codes.
- tests/test_content_and_capabilities.py (or the existing first-run capability test) -> real-process assertions for the new member and the corrected lists.
- docs/first-run.md -> the download-plan block is documented as part of the capability report.
CONSUMES:
- wangp/platform_cli.py -> the existing download-state computation stays the single source of truth.
- wangp/platform_profile.py -> profile facts and the tool-attributed accelerator reporting stay unchanged.

## Required Outcomes
1. `wgp doctor --capabilities` (human and `--json`) reports, in addition to today's facts, what would be downloaded: per-entry status and the required action, derived from the existing download computation rather than a new one.
2. With no model manifest the report states plainly that nothing is downloadable yet and names the remediation; with a manifest containing complete, incomplete, and hash-mismatched entries it distinguishes each state truthfully and never claims a download occurred.
3. The implemented list names the planning surfaces that exist (video, image, music, content, first-run) and the not-implemented list continues to name generation, speech/voice, sound effects, upscaling, face refinement, video editing and GUI as unimplemented.
4. No download, host contact, SSH, GPU or network call occurs; exit codes and read-only guarantees are unchanged.
5. Both surfaces still agree: `first-run download` and the capability report cannot disagree about an asset's state.

## Testing Requirements
- Real-process, no mocks: the project's existing capability test file plus the full `uv run --frozen --extra dev pytest -q`.
- Assert the human and JSON download-plan members, the three manifest states (complete, incomplete, mismatch) using temporary manifests, the corrected implemented/not-implemented lists, and zero shadowed `ssh`/`curl`/`wget`/`nvidia-smi` invocations.
- Assert the capability report and `first-run download` agree for the same manifest.

## MANDATORY SKILLS
- pvg

## Delivery Requirements
- Developer must paste the before and after human and JSON output, the targeted and full-suite results with machine-readable counters, the build result, and the exact-head CI conclusion into notes.
- Developer must include an AC verification table and must use `pvg story deliver`.
- No GPU, SSH, network, model download, tag, or publish is authorized; the story branch and its PR are the only push target.

## Acceptance Criteria


## Design


## Notes


## History


## Links


## Comments
