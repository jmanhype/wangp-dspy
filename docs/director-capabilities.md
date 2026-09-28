# Maestro director capability planning

`wgp director` is a deterministic, typed, no-GPU planning surface. It turns one prompt, one declared audio source, one beat-aware music-video declaration, or one screenplay into an ordered multi-clip film plan. Every mode first hands its derived turn text, durations, and the committed two-character plates to `wangp.content.build_content_request`; that existing wrapper invokes `scripts.run_content_brief.main`, `scripts.run_film.run_film`, and `services.director.wiring.plan_to_clips`. Director clips consume the planner's returned clip objects, prompts, identities, speakers, seeds, frames, and duration accounting. A successful plan proves request shape, evidence hashes, continuity declarations, pacing windows, review policy, and durable record shape; it never proves that media was generated.

## Request and evidence contract

Composition requests use `wangp-dspy.director-request/v1`. Every request selects exactly one mode and source: `prompt`, `audio`, `music_video`, or `screenplay`. Prompt mode records the complete prompt. Audio and music-video modes record a readable local path, SHA-256, measured duration, and — for music video — measured beat times whose provenance begins `measured:`. Screenplay mode records a character roster plus every scene's location, action, duration, participants, and explicit appearance/voice states.

Pacing supports `even`, `window_count`, `beat`, and `exact_timecode`. Windows are ordered, non-overlapping, and preserve the complete target duration up to the 60-minute programme ceiling. Beat pacing is valid only for music video and derives windows from the declared measured beats. Exact timecode names one complete target interval. Screenplay scenes map one-to-one to clips, and every scene duration contributes to the total.

Review is explicit. Auto review is a policy over the existing Whisper transcript, identity-vision, mouth-box consensus, and SyncNet gates; it cannot require a manual-only checkpoint and cannot bypass a gate. Manual review names the reviewer and required checkpoint. Both modes report that generated media has not been reviewed until an authorized run exists.

Queue enhancement is deliberately narrow: intent `replace_prompt` may copy a plan to a new database while changing only `prompt`, recording the reason and both canonical request hashes. The source database and original request hash remain recoverable and unchanged.

## Commands

```text
wgp director plan --request request.json --db run/director.db --json
wgp director enhance --request enhancement.json --output-db run/enhanced.db --json
wgp director queue --db run/director.db --json
wgp director review --db run/director.db --json
```

Plans are stored in `director_plan_records`, never in the executable `jobs` table. Update and delete triggers reject mutation. Each record embeds the typed recipe and seed needed to recompile its clip. `queue` uses the real `services.jobs.queue.JobQueue.next_admissible` selector on a temporary copy, reports no selected job, and leaves the original database byte-identical. A genuine render job in a separate database remains admissible. `review` independently reconstructs original or enhanced records and reports hash equality plus `hidden_mutation`.

Typed exit-2 diagnostics include remediation and a live next command for missing or conflicting sources, unknown character references, absent or mismatched audio, missing or unproven beats, unsupported pacing, pacing conflicts, auto/manual review conflicts, unsupported enhancement, existing outputs, malformed records, and reconstruction failures.

## Capability matrix and authorization boundary

| Capability | Prompt | Audio/music video | Screenplay | Generation evidence |
| --- | --- | --- | --- | --- |
| Deterministic ordered multi-clip plan | unsupported ([WD-p587 structural limitation](../datasets/runs/maestro-parity/director-structural-limitation/evidence.json)) | unsupported ([WD-p587 structural limitation](../datasets/runs/maestro-parity/director-structural-limitation/evidence.json)) | unsupported ([WD-p587 structural limitation](../datasets/runs/maestro-parity/director-structural-limitation/evidence.json)) | none |
| Per-clip prompt and six-frame overlap | unsupported ([WD-p587 structural limitation](../datasets/runs/maestro-parity/director-structural-limitation/evidence.json)) | unsupported ([WD-p587 structural limitation](../datasets/runs/maestro-parity/director-structural-limitation/evidence.json)) | unsupported ([WD-p587 structural limitation](../datasets/runs/maestro-parity/director-structural-limitation/evidence.json)) | none |
| Explicit continuity state and transitions | unsupported ([WD-p587 structural limitation](../datasets/runs/maestro-parity/director-structural-limitation/evidence.json)) | unsupported ([WD-p587 structural limitation](../datasets/runs/maestro-parity/director-structural-limitation/evidence.json)) | unsupported ([WD-p587 structural limitation](../datasets/runs/maestro-parity/director-structural-limitation/evidence.json)) | none |
| Beat-aware measured window mapping | not applicable | unsupported ([WD-p587 structural limitation](../datasets/runs/maestro-parity/director-structural-limitation/evidence.json)) | not applicable | none |
| Exact/window pacing preservation | unsupported ([WD-p587 structural limitation](../datasets/runs/maestro-parity/director-structural-limitation/evidence.json)) | unsupported ([WD-p587 structural limitation](../datasets/runs/maestro-parity/director-structural-limitation/evidence.json)) | unsupported ([WD-p587 structural limitation](../datasets/runs/maestro-parity/director-structural-limitation/evidence.json)) | none |
| Auto/manual review checkpoints | unsupported ([WD-p587 structural limitation](../datasets/runs/maestro-parity/director-structural-limitation/evidence.json)) | host_run_verified (WD-7fvx) | host_run_verified (WD-7fvx) | none |
| Immutable non-executable queue records | unsupported ([WD-p587 structural limitation](../datasets/runs/maestro-parity/director-structural-limitation/evidence.json)) | unsupported ([WD-p587 structural limitation](../datasets/runs/maestro-parity/director-structural-limitation/evidence.json)) | unsupported ([WD-p587 structural limitation](../datasets/runs/maestro-parity/director-structural-limitation/evidence.json)) | none |
| Authorized prompt-only enhancement | unsupported ([WD-p587 structural limitation](../datasets/runs/maestro-parity/director-structural-limitation/evidence.json)) | unsupported ([WD-p587 structural limitation](../datasets/runs/maestro-parity/director-structural-limitation/evidence.json)) | unsupported ([WD-p587 structural limitation](../datasets/runs/maestro-parity/director-structural-limitation/evidence.json)) | none |
| Seed-based hash reconstruction | unsupported ([WD-p587 structural limitation](../datasets/runs/maestro-parity/director-structural-limitation/evidence.json)) | unsupported ([WD-p587 structural limitation](../datasets/runs/maestro-parity/director-structural-limitation/evidence.json)) | unsupported ([WD-p587 structural limitation](../datasets/runs/maestro-parity/director-structural-limitation/evidence.json)) | none |
| Generated clip, audio, or finished film | unsupported in this lane | unsupported in this lane | unsupported in this lane | none |

Only the Audio/music-video and Screenplay cells in `Auto/manual review checkpoints` remain `host_run_verified`, mechanically from `datasets/runs/maestro-parity/WD-7fvx/evidence.json`: the synchronized WD-cpow speech pair preserved its complete 2.333333 s utterance and passed unchanged Whisper, identity-vision, three-frame mouth-box, motion, multicrop SyncNet, queue, and reviewer gates. WD-7fvx exercised authorized SSH execution on the RTX 3090 host with preexisting hash-verified local models, durable queue admission/retry transitions, and QC/AV gates. It did not perform or change a model/dependency/provider mutation or download, training, paid-provider work, threshold, or protected queue/preflight/renderer/wiring/engine semantic. The operator has accepted the WD-dmf2 clip-1 media-specific failures as a structural limitation: the other executable cells are terminal `unsupported` dispositions linked to [`WD-p587 evidence`](../datasets/runs/maestro-parity/director-structural-limitation/evidence.json); the generated-media row remains unchanged. This is not a claim that the RTX 3090 cannot pass the gates, because WD-dmf2 screenplay clip 2 passed the same 1.0 SyncNet bar.
