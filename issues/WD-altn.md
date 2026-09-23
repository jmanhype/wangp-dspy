---
id: WD-altn
title: "Capability report includes the download plan and the current implemented surfaces"
status: closed
priority: 1
type: feature
labels: [capability, verification, accepted]
created_at: 2026-09-23T04:24:58Z
created_by: speed
updated_at: 2026-09-23T05:16:11Z
content_hash: "sha256:6c012d2a5ae0b35a985434c306ab8534929947f0675ad3085e0701acce7ba9a4"
assignee: dev-WD-altn
closed_at: 2026-09-23T05:16:11Z
close_reason: "Accepted: exact-head diff is scoped; four manifest states agree read-only with first-run; full suite, build, and CI pass."
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


## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-23.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence
Summary: Added a read-only capability `download_plan` by reusing `predict.model_assets.asset_report`, exposed typed model-assets manifests through `wgp doctor --capabilities`, printed per-asset state/action in human output, corrected implemented/not-implemented capability lists, and documented the block. No download, host contact, GPU work, or model fetch was executed.

Commands run:
- `wgp doctor --capabilities` and `wgp doctor --capabilities --json` at parent head `57fcb76` and delivered head `5c49bae7`, with `ssh`, `curl`, `wget`, and `nvidia-smi` shadowed; forbidden-call log contained 0 bytes.
- `uv run --frozen --extra dev pytest tests/test_content_and_capabilities.py -q --junitxml=/tmp/wd-altn-test-results/target.xml` — exit 0; JUnit `tests=13 failures=0 errors=0 skipped=0`.
- `uv run --frozen --extra dev pytest -q --junitxml=/tmp/wd-altn-test-results/full.xml` at clean committed head — exit 0; JUnit `tests=1783 failures=0 errors=0 skipped=1`.
- `uv build --out-dir /tmp/wd-altn-build-final` — exit 0; exactly one wheel and one sdist.
- `git push -u origin story/WD-altn` — pushed only `story/WD-altn`.
- `gh pr create --base main --head story/WD-altn ...` — https://github.com/jmanhype/wangp-dspy/pull/167.
- `gh api repos/jmanhype/wangp-dspy/commits/5c49bae774cbb21a5bd7a231e50cdf651e4fa72b/check-runs` — one `test` check, `completed`, conclusion `success`.
- `git diff --exit-code 57fcb76..HEAD -- datasets` — exit 0; committed datasets Git tree `a642ce311543e7993a2a2f2c23a0bad5db425f9d`.

SHA: 5c49bae774cbb21a5bd7a231e50cdf651e4fa72b

### BEFORE HUMAN (`57fcb76`, manifest absent)
```text
platform=Darwin arm64
python=CPython 3.14.4
ffmpeg=available ffprobe=available
local_accelerator=nvidia-smi visible on PATH; presence check only, GPU was not called
ram_available_bytes=6356172800
disk_free_bytes=144809103360
host_configuration=incomplete (missing host.target, host.wgp_root, host.wgp_python)
model_manifest=absent entries=none
implemented=no-GPU content planning; host-backed rendering through the governed queue when explicitly configured
not_implemented=image generation; music generation; speech/voice cloning; sound effects; upscaling; face refinement; video editing; GUI
collection=read_only network_access=false host_contact=false
```

### BEFORE JSON (relevant members)
```json
{"model_manifest":{"entries":[],"remediation":"supply a manifest with sha256 plus local_path or remote_path for every required model; Wangp will not download models","status":"absent"},"generation_capabilities":{"implemented":["no-GPU content planning","host-backed rendering through the governed queue when explicitly configured"],"not_implemented":["image generation","music generation","speech/voice cloning","sound effects","upscaling","face refinement","video editing","GUI"]},"collection":{"host_contact":false,"network_access":false,"read_only":true},"download_plan_present":false}
```

### AFTER HUMAN (manifest absent)
```text
model_manifest=absent entries=none
download_plan=absent would_download=0 total_size_bytes=0 wangp_downloads=false
download_plan_remediation=supply a wangp-dspy.model-assets/v1 manifest; no asset is downloadable until source, hash, size, licence, and destination are recorded
implemented=video planning; image planning; music planning; content planning; first-run planning
not_implemented=video generation; image generation; music generation; speech/voice cloning; sound effects; upscaling; face refinement; video editing; GUI
collection=read_only network_access=false host_contact=false
```

### AFTER HUMAN (temporary typed manifest)
```text
model_manifest=present entries=complete.bin:complete, mismatch.bin:checksum_mismatch, partial.bin:partial, absent.bin:absent
download_plan=present would_download=3 total_size_bytes=24 wangp_downloads=false
download_entry=complete.bin status=complete required_action=none: local bytes and SHA-256 already match
download_entry=mismatch.bin status=checksum_mismatch required_action=operator-authorized download required
download_entry=partial.bin status=partial required_action=operator-authorized download required
download_entry=absent.bin status=absent required_action=operator-authorized download required
download_plan_remediation=run wgp first-run download with this manifest and an explicit state path for operator review
```

### AFTER JSON (relevant members)
```json
{"download_plan":{"asset_count":3,"authorization_required":true,"entries":[{"bytes_present":8,"id":"complete.bin","required_action":"none: local bytes and SHA-256 already match","size_bytes":8,"status":"complete"},{"bytes_present":8,"id":"mismatch.bin","required_action":"operator-authorized download required","size_bytes":8,"status":"checksum_mismatch"},{"bytes_present":4,"id":"partial.bin","required_action":"operator-authorized download required","size_bytes":8,"status":"partial"},{"bytes_present":null,"id":"absent.bin","required_action":"operator-authorized download required","size_bytes":8,"status":"absent"}],"remediation":"run wgp first-run download with this manifest and an explicit state path for operator review","status":"present","total_size_bytes":24,"wangp_downloads":false},"generation_capabilities":{"implemented":["video planning","image planning","music planning","content planning","first-run planning"],"not_implemented":["video generation","image generation","music generation","speech/voice cloning","sound effects","upscaling","face refinement","video editing","GUI"]}}
```

### CI/Test Results
- Targeted JUnit: `tests=13`, `failures=0`, `errors=0`, `skipped=0`, exit 0.
- Full-suite JUnit at exact clean committed head `5c49bae774cbb21a5bd7a231e50cdf651e4fa72b`: `tests=1783`, `failures=0`, `errors=0`, `skipped=1`, exit 0. The single skip is the existing intentional live-3090 test. An initial full run before committing had one release-cleanliness failure because this story's edits made the worktree dirty; the exact clean-head rerun above passed.
- Build: one wheel `wangp_dspy-0.1.0-py3-none-any.whl`, SHA256 `2d9043a5c47e9674e01609c64ccf6712906a5e7996cdaf0d4de212e5f6bf63cf`; one sdist `wangp_dspy-0.1.0.tar.gz`, SHA256 `524d6ea9316caf1d988cbc11d00bbe89285e30fca9f3b0415e5b5a8a42da247e`.
- GitHub check-runs at exact head: total_count=1; `test` status=completed, conclusion=success.
- PR: https://github.com/jmanhype/wangp-dspy/pull/167.

### AC Verification
| AC | Result | Evidence |
| --- | --- | --- |
| 1. Human and JSON capability reports show the existing-computation-derived download plan with per-entry state and required action | verified | `wangp/environment.py` calls `asset_report`; after-output above; `tests/test_content_and_capabilities.py::test_capability_download_plan_reuses_first_run_asset_state`. |
| 2. Manifest-absent, complete, incomplete/partial, and hash-mismatch states are distinct and no download is claimed | verified | Absent plan reports zero/remediation; temporary-manifest output distinguishes `complete`, `partial`, `checksum_mismatch`, and `absent`; all output says `wangp_downloads=false`. |
| 3. Implemented and not-implemented lists name current planning versus unimplemented generation/editing/GUI surfaces | verified | Implemented is video/image/music/content/first-run planning; not-implemented names video/image/music generation, speech/voice cloning, sound effects, upscaling, face refinement, video editing, GUI; targeted test asserts both. |
| 4. Collection remains read-only with unchanged exits and zero external calls | verified | Capability exits remain 0; tests assert read-only collection and empty shadowed `ssh`/`curl`/`wget`/`nvidia-smi` logs; final capture log was 0 bytes. |
| 5. Capability report and first-run download agree for the same manifest | verified | Real-process test compares per-entry state, pending count, byte total, and no-download flag against `wgp first-run download`; both use `asset_report`. |

## nd_contract
status: delivered

### evidence
- Exact head `5c49bae774cbb21a5bd7a231e50cdf651e4fa72b`; branch `story/WD-altn`; PR #167.
- Targeted JUnit 13/13 pass; full JUnit 1783 tests, 0 failures, 0 errors, 1 skip.
- Build produced one wheel and one sdist; committed datasets tree unchanged; GitHub `test` check succeeded.

### proof
- [x] AC #1: Human and JSON capability reports expose the reused download plan with per-entry state/action.
- [x] AC #2: Manifest-absent, complete, incomplete, and hash-mismatch states are truthful and no download occurred.
- [x] AC #3: Current planning surfaces and unimplemented generation/speech/effects/upscaling/refinement/editing/GUI are named correctly.
- [x] AC #4: Capability collection remains read-only with unchanged exit codes and zero shadowed external calls.
- [x] AC #5: Capability and first-run download reports agree for the same typed manifest and state.

## History
- 2026-09-23T04:25:06Z status: open -> in_progress
- 2026-09-23T04:25:06Z claimed by dev-WD-altn
- 2026-09-23T05:01:44Z status: in_progress -> in_progress
- 2026-09-23T05:16:11Z status: in_progress -> closed

## Links


## Comments
