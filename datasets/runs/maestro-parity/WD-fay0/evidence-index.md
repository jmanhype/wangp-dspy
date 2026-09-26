# WD-fay0 consolidated Maestro-parity evidence index

Generated: `2026-09-26T00:24:32.451856+00:00`; capstone base: `82f6c38570a818dd8dbd3e70baebd037459661b3`.

**VERDICT: NOT COMPLETE: operator scope decisions and checker/generation prerequisites remain; no lane verdict was upgraded by this capstone.**

The index is read-only consolidation. It does not authorize work, edit another lane, relabel a verdict, or copy lane media.

## Lane checker matrix

| Lane | Scope | Retrieval | `evidence.json` SHA-256 | Files / bytes | Authorization / reviewer | Checker | Result / exact blocker |
| --- | --- | --- | --- | --- | --- | --- | --- |
| WD-0zj8 | clean-machine install | base `82f6c38570a818dd8dbd3e70baebd037459661b3` | `MISSING` | 21 / 27417 | auth=not_applicable_no_generation_bundle; reviewer=not_applicable_no_generation_bundle | exit 1 | FAIL manifest: [Errno 2] No such file or directory: '/Users/Shared/HermesWorkspace/wangp-dspy/.claude/worktrees/dev-WD-fay0/datasets/runs/maestro-parity/WD-0zj8/evidence.json' |
| WD-2gyw | video subset | base `82f6c38570a818dd8dbd3e70baebd037459661b3` | `3b4486412a9cf20d05b7b2d1235fe70cbb35315ce8df5abe28ede97f36b2315a` | 181 / 8671186 | auth=approved; reviewer=approved | exit 0 | PASS wangp-dspy.maestro-parity-evidence/v1 datasets/runs/maestro-parity/WD-2gyw |
| WD-bxhc | voice + portable character | base `82f6c38570a818dd8dbd3e70baebd037459661b3` | `9197c7782c1f8f3360ddaecba16b9d2bbb1bcc7629fb5f7da6534af7ba7727d8` | 342 / 14852376 | auth=approved; reviewer=approved | exit 0 | PASS wangp-dspy.maestro-parity-evidence/v1 datasets/runs/maestro-parity/WD-bxhc |
| WD-cpow | SFX/audio post | base `82f6c38570a818dd8dbd3e70baebd037459661b3` | `74a4098fa66acd8ed80b0b2578acb8af17841925750c63de9f641efbe4a82d56` | 113 / 5108477 | auth=approved; reviewer=approved | exit 0 | PASS wangp-dspy.maestro-parity-evidence/v1 datasets/runs/maestro-parity/WD-cpow |
| WD-dmf2 | director/editor composition | story branch only `741a8bb27c4bec3be38667b090a03bedb00e3010` | `024d049cf39aab51913b3eaed107066136db0da1faf91f3bea8d8b2397fcf6de` | 292 / 28004352 | auth=approved; reviewer=pending | exit 1 | FAIL objective_gate_results[21].verdict: must be pass<br>FAIL objective_gate_results[23].verdict: must be pass<br>FAIL objective_gate_results[24].verdict: must be pass<br>FAIL objective_gate_results[26].verdict: must be pass<br>FAIL objective_gate_results[27].verdict: must be pass<br>FAIL reviewer_verdict.decision: must be approved |
| WD-m0r5 | image | base `82f6c38570a818dd8dbd3e70baebd037459661b3` | `e6ca75ae8144f3e28e482c37b8aefd58833e9354657511c97371286e4b2d8eab` | 155 / 34840635 | auth=approved; reviewer=approved | exit 0 | PASS wangp-dspy.maestro-parity-evidence/v1 datasets/runs/maestro-parity/WD-m0r5 |
| WD-r81u | finishing | base `82f6c38570a818dd8dbd3e70baebd037459661b3` | `e14c4b367f4876c279c8c167e770988817cc1e044274cd6978b0e266039c444d` | 146 / 18246836 | auth=approved; reviewer=approved | exit 0 | PASS wangp-dspy.maestro-parity-evidence/v1 datasets/runs/maestro-parity/WD-r81u |
| WD-rous | music | base `82f6c38570a818dd8dbd3e70baebd037459661b3` | `100fa53ba45b573f8e7237f508f75412dbcdc32160f5ad58c473eb08ced85c50` | 68 / 6042432 | auth=approved; reviewer=approved | exit 0 | PASS wangp-dspy.maestro-parity-evidence/v1 datasets/runs/maestro-parity/WD-rous |

Raw checker output, exact command identities, and gate output tails are consolidated in `gate-transcript.md`. WD-dmf2 was checked read-only in a disposable worktree at the PM-recorded accepted commit; it is not merged into this capstone base.

## Complete matrix-row/cell disposition table

Scope: Every state-bearing operation/mode column in the eight markdown capability matrices; trailing Generation evidence prose columns are supporting citations, not additional capability states.

| Source | Line | Row | Cell | State | Evidence/boundary or exact planned blocker |
| --- | ---: | --- | --- | --- | --- |
| docs/image-capabilities.md | 60 | qwen_image/qwen-standard | Generate | `host_run_verified` | ../datasets/runs/maestro-parity/WD-m0r5/evidence.json |
| docs/image-capabilities.md | 60 | qwen_image/qwen-standard | Edit | `host_run_verified` | ../datasets/runs/maestro-parity/WD-m0r5/evidence.json |
| docs/image-capabilities.md | 60 | qwen_image/qwen-standard | Upscale | `host_run_verified` | ../datasets/runs/maestro-parity/WD-m0r5/evidence.json |
| docs/image-capabilities.md | 60 | qwen_image/qwen-standard | Outpaint | `host_run_verified` | ../datasets/runs/maestro-parity/WD-m0r5/evidence.json |
| docs/image-capabilities.md | 60 | qwen_image/qwen-standard | Identity edit | `host_run_verified` | ../datasets/runs/maestro-parity/WD-m0r5/evidence.json |
| docs/image-capabilities.md | 61 | qwen_image/qwen-professional | Generate | `host_run_verified` | ../datasets/runs/maestro-parity/WD-m0r5/evidence.json |
| docs/image-capabilities.md | 61 | qwen_image/qwen-professional | Edit | `host_run_verified` | ../datasets/runs/maestro-parity/WD-m0r5/evidence.json |
| docs/image-capabilities.md | 61 | qwen_image/qwen-professional | Upscale | `host_run_verified` | ../datasets/runs/maestro-parity/WD-m0r5/evidence.json |
| docs/image-capabilities.md | 61 | qwen_image/qwen-professional | Outpaint | `host_run_verified` | ../datasets/runs/maestro-parity/WD-m0r5/evidence.json |
| docs/image-capabilities.md | 61 | qwen_image/qwen-professional | Identity edit | `host_run_verified` | ../datasets/runs/maestro-parity/WD-m0r5/evidence.json |
| docs/image-capabilities.md | 62 | flux_kontext/flux-standard | Generate | `host_run_verified` | ../datasets/runs/maestro-parity/WD-m0r5/evidence.json |
| docs/image-capabilities.md | 62 | flux_kontext/flux-standard | Edit | `host_run_verified` | ../datasets/runs/maestro-parity/WD-m0r5/evidence.json |
| docs/image-capabilities.md | 62 | flux_kontext/flux-standard | Upscale | `unsupported` | documented boundary |
| docs/image-capabilities.md | 62 | flux_kontext/flux-standard | Outpaint | `unsupported` | documented boundary |
| docs/image-capabilities.md | 62 | flux_kontext/flux-standard | Identity edit | `host_run_verified` | ../datasets/runs/maestro-parity/WD-m0r5/evidence.json |
| docs/image-capabilities.md | 63 | flux_kontext/flux-kontext | Generate | `host_run_verified` | ../datasets/runs/maestro-parity/WD-m0r5/evidence.json |
| docs/image-capabilities.md | 63 | flux_kontext/flux-kontext | Edit | `host_run_verified` | ../datasets/runs/maestro-parity/WD-m0r5/evidence.json |
| docs/image-capabilities.md | 63 | flux_kontext/flux-kontext | Upscale | `unsupported` | documented boundary |
| docs/image-capabilities.md | 63 | flux_kontext/flux-kontext | Outpaint | `unsupported` | documented boundary |
| docs/image-capabilities.md | 63 | flux_kontext/flux-kontext | Identity edit | `host_run_verified` | ../datasets/runs/maestro-parity/WD-m0r5/evidence.json |
| docs/music-capabilities.md | 35 | ace_step | Generate | `host_run_verified` | ../datasets/runs/maestro-parity/WD-rous/evidence.json |
| docs/music-capabilities.md | 35 | ace_step | Style adapt | `host_run_verified` | ../datasets/runs/maestro-parity/WD-rous/evidence.json |
| docs/music-capabilities.md | 36 | stable_audio | Generate | `unsupported_on_this_hardware` | ../datasets/runs/maestro-parity/WD-rous/evidence.json |
| docs/music-capabilities.md | 36 | stable_audio | Style adapt | `unsupported for planning` | documented boundary |
| docs/sfx-capabilities.md | 28 | stable_audio/sound_effect | Sound effect | `unsupported_on_this_hardware` | ../datasets/runs/maestro-parity/WD-cpow/stable-audio-infeasibility.md |
| docs/sfx-capabilities.md | 28 | stable_audio/sound_effect | Revoice | `unsupported` | documented boundary |
| docs/sfx-capabilities.md | 28 | stable_audio/sound_effect | Refinement | `unsupported` | documented boundary |
| docs/sfx-capabilities.md | 29 | vibevoice/revoice | Sound effect | `unsupported` | documented boundary |
| docs/sfx-capabilities.md | 29 | vibevoice/revoice | Revoice | `host_run_verified` | ../datasets/runs/maestro-parity/WD-cpow/evidence.json |
| docs/sfx-capabilities.md | 29 | vibevoice/revoice | Refinement | `unsupported` | documented boundary |
| docs/sfx-capabilities.md | 30 | deepfilternet/refinement | Sound effect | `unsupported` | documented boundary |
| docs/sfx-capabilities.md | 30 | deepfilternet/refinement | Revoice | `unsupported` | documented boundary |
| docs/sfx-capabilities.md | 30 | deepfilternet/refinement | Refinement | `host_run_verified` | ../datasets/runs/maestro-parity/WD-cpow/evidence.json |
| docs/video-capabilities.md | 75 | minimax_h3/standard | Create | `host_run_verified` | ../datasets/runs/maestro-parity/WD-2gyw/evidence.json |
| docs/video-capabilities.md | 75 | minimax_h3/standard | Extend | `planned` | WD-2gyw verified only the representative Create operation; Extend was not run and needs a new operator-approved per-family/per-operation batch. |
| docs/video-capabilities.md | 75 | minimax_h3/standard | Blend | `planned` | WD-2gyw verified only the representative Create operation; Blend was not run and needs a new operator-approved per-family/per-operation batch. |
| docs/video-capabilities.md | 75 | minimax_h3/standard | Retake | `planned` | WD-2gyw verified only the representative Create operation; Retake was not run and needs a new operator-approved per-family/per-operation batch. |
| docs/video-capabilities.md | 75 | minimax_h3/standard | Edit | `planned` | WD-2gyw verified only the representative Create operation; Edit was not run and needs a new operator-approved per-family/per-operation batch. |
| docs/video-capabilities.md | 75 | minimax_h3/standard | Outpaint | `planned` | WD-2gyw verified only the representative Create operation; Outpaint was not run and needs a new operator-approved per-family/per-operation batch. |
| docs/video-capabilities.md | 75 | minimax_h3/standard | Repaint | `planned` | WD-2gyw verified only the representative Create operation; Repaint was not run and needs a new operator-approved per-family/per-operation batch. |
| docs/video-capabilities.md | 75 | minimax_h3/standard | Recast | `planned` | WD-2gyw verified only the representative Create operation; Recast was not run and needs a new operator-approved per-family/per-operation batch. |
| docs/video-capabilities.md | 75 | minimax_h3/standard | Upscale | `planned` | WD-2gyw verified only the representative Create operation; Upscale was not run and needs a new operator-approved per-family/per-operation batch. |
| docs/video-capabilities.md | 76 | minimax_h3/h3_vdn_hybrid_attention | Create | `host_run_verified` | ../datasets/runs/maestro-parity/WD-2gyw/evidence.json |
| docs/video-capabilities.md | 76 | minimax_h3/h3_vdn_hybrid_attention | Extend | `planned` | WD-2gyw verified only the representative Create operation; Extend was not run and needs a new operator-approved per-family/per-operation batch. |
| docs/video-capabilities.md | 76 | minimax_h3/h3_vdn_hybrid_attention | Blend | `planned` | WD-2gyw verified only the representative Create operation; Blend was not run and needs a new operator-approved per-family/per-operation batch. |
| docs/video-capabilities.md | 76 | minimax_h3/h3_vdn_hybrid_attention | Retake | `planned` | WD-2gyw verified only the representative Create operation; Retake was not run and needs a new operator-approved per-family/per-operation batch. |
| docs/video-capabilities.md | 76 | minimax_h3/h3_vdn_hybrid_attention | Edit | `planned` | WD-2gyw verified only the representative Create operation; Edit was not run and needs a new operator-approved per-family/per-operation batch. |
| docs/video-capabilities.md | 76 | minimax_h3/h3_vdn_hybrid_attention | Outpaint | `planned` | WD-2gyw verified only the representative Create operation; Outpaint was not run and needs a new operator-approved per-family/per-operation batch. |
| docs/video-capabilities.md | 76 | minimax_h3/h3_vdn_hybrid_attention | Repaint | `planned` | WD-2gyw verified only the representative Create operation; Repaint was not run and needs a new operator-approved per-family/per-operation batch. |
| docs/video-capabilities.md | 76 | minimax_h3/h3_vdn_hybrid_attention | Recast | `planned` | WD-2gyw verified only the representative Create operation; Recast was not run and needs a new operator-approved per-family/per-operation batch. |
| docs/video-capabilities.md | 76 | minimax_h3/h3_vdn_hybrid_attention | Upscale | `planned` | WD-2gyw verified only the representative Create operation; Upscale was not run and needs a new operator-approved per-family/per-operation batch. |
| docs/video-capabilities.md | 77 | minimax_h3/taomate_three_step | Create | `planned` | No TaoMate implementation or preset exists in either searched host tree; a generic three-step render would fabricate the named preset. |
| docs/video-capabilities.md | 77 | minimax_h3/taomate_three_step | Extend | `planned` | No TaoMate implementation or preset exists in either searched host tree; a generic three-step render would fabricate the named preset. |
| docs/video-capabilities.md | 77 | minimax_h3/taomate_three_step | Blend | `planned` | No TaoMate implementation or preset exists in either searched host tree; a generic three-step render would fabricate the named preset. |
| docs/video-capabilities.md | 77 | minimax_h3/taomate_three_step | Retake | `planned` | No TaoMate implementation or preset exists in either searched host tree; a generic three-step render would fabricate the named preset. |
| docs/video-capabilities.md | 77 | minimax_h3/taomate_three_step | Edit | `planned` | No TaoMate implementation or preset exists in either searched host tree; a generic three-step render would fabricate the named preset. |
| docs/video-capabilities.md | 77 | minimax_h3/taomate_three_step | Outpaint | `planned` | No TaoMate implementation or preset exists in either searched host tree; a generic three-step render would fabricate the named preset. |
| docs/video-capabilities.md | 77 | minimax_h3/taomate_three_step | Repaint | `planned` | No TaoMate implementation or preset exists in either searched host tree; a generic three-step render would fabricate the named preset. |
| docs/video-capabilities.md | 77 | minimax_h3/taomate_three_step | Recast | `planned` | No TaoMate implementation or preset exists in either searched host tree; a generic three-step render would fabricate the named preset. |
| docs/video-capabilities.md | 77 | minimax_h3/taomate_three_step | Upscale | `planned` | No TaoMate implementation or preset exists in either searched host tree; a generic three-step render would fabricate the named preset. |
| docs/video-capabilities.md | 78 | minimax_h3/kfi_frames_injection | Create | `planned` | WD-2gyw verified only the representative Retake operation; Create was not run and needs a new operator-approved per-family/per-operation batch. |
| docs/video-capabilities.md | 78 | minimax_h3/kfi_frames_injection | Extend | `planned` | WD-2gyw verified only the representative Retake operation; Extend was not run and needs a new operator-approved per-family/per-operation batch. |
| docs/video-capabilities.md | 78 | minimax_h3/kfi_frames_injection | Blend | `planned` | WD-2gyw verified only the representative Retake operation; Blend was not run and needs a new operator-approved per-family/per-operation batch. |
| docs/video-capabilities.md | 78 | minimax_h3/kfi_frames_injection | Retake | `host_run_verified` | ../datasets/runs/maestro-parity/WD-2gyw/evidence.json |
| docs/video-capabilities.md | 78 | minimax_h3/kfi_frames_injection | Edit | `planned` | WD-2gyw verified only the representative Retake operation; Edit was not run and needs a new operator-approved per-family/per-operation batch. |
| docs/video-capabilities.md | 78 | minimax_h3/kfi_frames_injection | Outpaint | `planned` | WD-2gyw verified only the representative Retake operation; Outpaint was not run and needs a new operator-approved per-family/per-operation batch. |
| docs/video-capabilities.md | 78 | minimax_h3/kfi_frames_injection | Repaint | `planned` | WD-2gyw verified only the representative Retake operation; Repaint was not run and needs a new operator-approved per-family/per-operation batch. |
| docs/video-capabilities.md | 78 | minimax_h3/kfi_frames_injection | Recast | `planned` | WD-2gyw verified only the representative Retake operation; Recast was not run and needs a new operator-approved per-family/per-operation batch. |
| docs/video-capabilities.md | 78 | minimax_h3/kfi_frames_injection | Upscale | `planned` | WD-2gyw verified only the representative Retake operation; Upscale was not run and needs a new operator-approved per-family/per-operation batch. |
| docs/video-capabilities.md | 79 | minimax_h3/h3_outpaint | Create | `planned` | Wan2GP FL2VA model definition comments out video_guide_outpainting; host control is disabled (implementation boundary, not 24-GiB infeasibility). |
| docs/video-capabilities.md | 79 | minimax_h3/h3_outpaint | Extend | `planned` | Wan2GP FL2VA model definition comments out video_guide_outpainting; host control is disabled (implementation boundary, not 24-GiB infeasibility). |
| docs/video-capabilities.md | 79 | minimax_h3/h3_outpaint | Blend | `planned` | Wan2GP FL2VA model definition comments out video_guide_outpainting; host control is disabled (implementation boundary, not 24-GiB infeasibility). |
| docs/video-capabilities.md | 79 | minimax_h3/h3_outpaint | Retake | `planned` | Wan2GP FL2VA model definition comments out video_guide_outpainting; host control is disabled (implementation boundary, not 24-GiB infeasibility). |
| docs/video-capabilities.md | 79 | minimax_h3/h3_outpaint | Edit | `planned` | Wan2GP FL2VA model definition comments out video_guide_outpainting; host control is disabled (implementation boundary, not 24-GiB infeasibility). |
| docs/video-capabilities.md | 79 | minimax_h3/h3_outpaint | Outpaint | `planned` | Wan2GP FL2VA model definition comments out video_guide_outpainting; host control is disabled (implementation boundary, not 24-GiB infeasibility). |
| docs/video-capabilities.md | 79 | minimax_h3/h3_outpaint | Repaint | `planned` | Wan2GP FL2VA model definition comments out video_guide_outpainting; host control is disabled (implementation boundary, not 24-GiB infeasibility). |
| docs/video-capabilities.md | 79 | minimax_h3/h3_outpaint | Recast | `planned` | Wan2GP FL2VA model definition comments out video_guide_outpainting; host control is disabled (implementation boundary, not 24-GiB infeasibility). |
| docs/video-capabilities.md | 79 | minimax_h3/h3_outpaint | Upscale | `planned` | Wan2GP FL2VA model definition comments out video_guide_outpainting; host control is disabled (implementation boundary, not 24-GiB infeasibility). |
| docs/video-capabilities.md | 80 | minimax_h3/h3_audio_refinement | Create | `planned` | WD-2gyw verified only the representative Edit operation; Create was not run and needs a new operator-approved per-family/per-operation batch. |
| docs/video-capabilities.md | 80 | minimax_h3/h3_audio_refinement | Extend | `planned` | WD-2gyw verified only the representative Edit operation; Extend was not run and needs a new operator-approved per-family/per-operation batch. |
| docs/video-capabilities.md | 80 | minimax_h3/h3_audio_refinement | Blend | `planned` | WD-2gyw verified only the representative Edit operation; Blend was not run and needs a new operator-approved per-family/per-operation batch. |
| docs/video-capabilities.md | 80 | minimax_h3/h3_audio_refinement | Retake | `planned` | WD-2gyw verified only the representative Edit operation; Retake was not run and needs a new operator-approved per-family/per-operation batch. |
| docs/video-capabilities.md | 80 | minimax_h3/h3_audio_refinement | Edit | `host_run_verified` | ../datasets/runs/maestro-parity/WD-2gyw/evidence.json |
| docs/video-capabilities.md | 80 | minimax_h3/h3_audio_refinement | Outpaint | `planned` | WD-2gyw verified only the representative Edit operation; Outpaint was not run and needs a new operator-approved per-family/per-operation batch. |
| docs/video-capabilities.md | 80 | minimax_h3/h3_audio_refinement | Repaint | `planned` | WD-2gyw verified only the representative Edit operation; Repaint was not run and needs a new operator-approved per-family/per-operation batch. |
| docs/video-capabilities.md | 80 | minimax_h3/h3_audio_refinement | Recast | `planned` | WD-2gyw verified only the representative Edit operation; Recast was not run and needs a new operator-approved per-family/per-operation batch. |
| docs/video-capabilities.md | 80 | minimax_h3/h3_audio_refinement | Upscale | `planned` | WD-2gyw verified only the representative Edit operation; Upscale was not run and needs a new operator-approved per-family/per-operation batch. |
| docs/video-capabilities.md | 81 | ltx/2.5 | Create | `planned` | WD-2gyw authorized int8 ConvRot attempt reached the Gemma4 tokenizer, then failed before generation with TypeError: 'tokenizers.pre_tokenizers.Split' object does not support item assignment; fixable dependency failure, not hardware. The representative lane validated no Create output for this family. |
| docs/video-capabilities.md | 81 | ltx/2.5 | Extend | `planned` | WD-2gyw authorized int8 ConvRot attempt reached the Gemma4 tokenizer, then failed before generation with TypeError: 'tokenizers.pre_tokenizers.Split' object does not support item assignment; fixable dependency failure, not hardware. The representative lane validated no Extend output for this family. |
| docs/video-capabilities.md | 81 | ltx/2.5 | Blend | `unsupported` | ../datasets/runs/maestro-parity/WD-2gyw/planning/boundaries/ltx-2.5-blend.result.json |
| docs/video-capabilities.md | 81 | ltx/2.5 | Retake | `planned` | WD-2gyw authorized int8 ConvRot attempt reached the Gemma4 tokenizer, then failed before generation with TypeError: 'tokenizers.pre_tokenizers.Split' object does not support item assignment; fixable dependency failure, not hardware. The representative lane validated no Retake output for this family. |
| docs/video-capabilities.md | 81 | ltx/2.5 | Edit | `planned` | WD-2gyw authorized int8 ConvRot attempt reached the Gemma4 tokenizer, then failed before generation with TypeError: 'tokenizers.pre_tokenizers.Split' object does not support item assignment; fixable dependency failure, not hardware. The representative lane validated no Edit output for this family. |
| docs/video-capabilities.md | 81 | ltx/2.5 | Outpaint | `planned` | WD-2gyw authorized int8 ConvRot attempt reached the Gemma4 tokenizer, then failed before generation with TypeError: 'tokenizers.pre_tokenizers.Split' object does not support item assignment; fixable dependency failure, not hardware. The representative lane validated no Outpaint output for this family. |
| docs/video-capabilities.md | 81 | ltx/2.5 | Repaint | `planned` | WD-2gyw authorized int8 ConvRot attempt reached the Gemma4 tokenizer, then failed before generation with TypeError: 'tokenizers.pre_tokenizers.Split' object does not support item assignment; fixable dependency failure, not hardware. The representative lane validated no Repaint output for this family. |
| docs/video-capabilities.md | 81 | ltx/2.5 | Recast | `planned` | WD-2gyw authorized int8 ConvRot attempt reached the Gemma4 tokenizer, then failed before generation with TypeError: 'tokenizers.pre_tokenizers.Split' object does not support item assignment; fixable dependency failure, not hardware. The representative lane validated no Recast output for this family. |
| docs/video-capabilities.md | 81 | ltx/2.5 | Upscale | `planned` | WD-2gyw authorized int8 ConvRot attempt reached the Gemma4 tokenizer, then failed before generation with TypeError: 'tokenizers.pre_tokenizers.Split' object does not support item assignment; fixable dependency failure, not hardware. The representative lane validated no Upscale output for this family. |
| docs/video-capabilities.md | 82 | ltx/2.3 | Create | `planned` | Only a pre-existing 29,531,884,062-byte ComfyUI FP8 checkpoint is present; hash/package mismatch the WanGP LTX-2.3 manifest. A correct package/download authorization is still required. |
| docs/video-capabilities.md | 82 | ltx/2.3 | Extend | `planned` | Only a pre-existing 29,531,884,062-byte ComfyUI FP8 checkpoint is present; hash/package mismatch the WanGP LTX-2.3 manifest. A correct package/download authorization is still required. |
| docs/video-capabilities.md | 82 | ltx/2.3 | Blend | `planned` | Only a pre-existing 29,531,884,062-byte ComfyUI FP8 checkpoint is present; hash/package mismatch the WanGP LTX-2.3 manifest. A correct package/download authorization is still required. |
| docs/video-capabilities.md | 82 | ltx/2.3 | Retake | `planned` | Only a pre-existing 29,531,884,062-byte ComfyUI FP8 checkpoint is present; hash/package mismatch the WanGP LTX-2.3 manifest. A correct package/download authorization is still required. |
| docs/video-capabilities.md | 82 | ltx/2.3 | Edit | `planned` | Only a pre-existing 29,531,884,062-byte ComfyUI FP8 checkpoint is present; hash/package mismatch the WanGP LTX-2.3 manifest. A correct package/download authorization is still required. |
| docs/video-capabilities.md | 82 | ltx/2.3 | Outpaint | `planned` | Only a pre-existing 29,531,884,062-byte ComfyUI FP8 checkpoint is present; hash/package mismatch the WanGP LTX-2.3 manifest. A correct package/download authorization is still required. |
| docs/video-capabilities.md | 82 | ltx/2.3 | Repaint | `planned` | Only a pre-existing 29,531,884,062-byte ComfyUI FP8 checkpoint is present; hash/package mismatch the WanGP LTX-2.3 manifest. A correct package/download authorization is still required. |
| docs/video-capabilities.md | 82 | ltx/2.3 | Recast | `planned` | Only a pre-existing 29,531,884,062-byte ComfyUI FP8 checkpoint is present; hash/package mismatch the WanGP LTX-2.3 manifest. A correct package/download authorization is still required. |
| docs/video-capabilities.md | 82 | ltx/2.3 | Upscale | `planned` | Only a pre-existing 29,531,884,062-byte ComfyUI FP8 checkpoint is present; hash/package mismatch the WanGP LTX-2.3 manifest. A correct package/download authorization is still required. |
| docs/video-capabilities.md | 83 | scail/2 | Create | `planned` | SCAIL-2 int8 main asset is 16,644,305,281 bytes, exceeding the 2,198,073,147 bytes remaining under the operator-approved 60,000,000,000-byte WD-2gyw download ceiling. |
| docs/video-capabilities.md | 83 | scail/2 | Extend | `planned` | SCAIL-2 int8 main asset is 16,644,305,281 bytes, exceeding the 2,198,073,147 bytes remaining under the operator-approved 60,000,000,000-byte WD-2gyw download ceiling. |
| docs/video-capabilities.md | 83 | scail/2 | Blend | `planned` | SCAIL-2 int8 main asset is 16,644,305,281 bytes, exceeding the 2,198,073,147 bytes remaining under the operator-approved 60,000,000,000-byte WD-2gyw download ceiling. |
| docs/video-capabilities.md | 83 | scail/2 | Retake | `planned` | SCAIL-2 int8 main asset is 16,644,305,281 bytes, exceeding the 2,198,073,147 bytes remaining under the operator-approved 60,000,000,000-byte WD-2gyw download ceiling. |
| docs/video-capabilities.md | 83 | scail/2 | Edit | `planned` | SCAIL-2 int8 main asset is 16,644,305,281 bytes, exceeding the 2,198,073,147 bytes remaining under the operator-approved 60,000,000,000-byte WD-2gyw download ceiling. |
| docs/video-capabilities.md | 83 | scail/2 | Outpaint | `unsupported` | ../datasets/runs/maestro-parity/WD-2gyw/planning/boundaries/scail-2-outpaint.result.json |
| docs/video-capabilities.md | 83 | scail/2 | Repaint | `planned` | SCAIL-2 int8 main asset is 16,644,305,281 bytes, exceeding the 2,198,073,147 bytes remaining under the operator-approved 60,000,000,000-byte WD-2gyw download ceiling. |
| docs/video-capabilities.md | 83 | scail/2 | Recast | `planned` | SCAIL-2 int8 main asset is 16,644,305,281 bytes, exceeding the 2,198,073,147 bytes remaining under the operator-approved 60,000,000,000-byte WD-2gyw download ceiling. |
| docs/video-capabilities.md | 83 | scail/2 | Upscale | `unsupported` | ../datasets/runs/maestro-parity/WD-2gyw/planning/boundaries/scail-2-upscale.result.json |
| docs/video-capabilities.md | 84 | wan/2gp | Create | `planned` | Wan 2.1 14B int8 main asset is 14,903,022,013 bytes, exceeding the 2,198,073,147 bytes remaining under the operator-approved 60,000,000,000-byte WD-2gyw download ceiling. |
| docs/video-capabilities.md | 84 | wan/2gp | Extend | `planned` | Wan 2.1 14B int8 main asset is 14,903,022,013 bytes, exceeding the 2,198,073,147 bytes remaining under the operator-approved 60,000,000,000-byte WD-2gyw download ceiling. |
| docs/video-capabilities.md | 84 | wan/2gp | Blend | `planned` | Wan 2.1 14B int8 main asset is 14,903,022,013 bytes, exceeding the 2,198,073,147 bytes remaining under the operator-approved 60,000,000,000-byte WD-2gyw download ceiling. |
| docs/video-capabilities.md | 84 | wan/2gp | Retake | `planned` | Wan 2.1 14B int8 main asset is 14,903,022,013 bytes, exceeding the 2,198,073,147 bytes remaining under the operator-approved 60,000,000,000-byte WD-2gyw download ceiling. |
| docs/video-capabilities.md | 84 | wan/2gp | Edit | `planned` | Wan 2.1 14B int8 main asset is 14,903,022,013 bytes, exceeding the 2,198,073,147 bytes remaining under the operator-approved 60,000,000,000-byte WD-2gyw download ceiling. |
| docs/video-capabilities.md | 84 | wan/2gp | Outpaint | `planned` | Wan 2.1 14B int8 main asset is 14,903,022,013 bytes, exceeding the 2,198,073,147 bytes remaining under the operator-approved 60,000,000,000-byte WD-2gyw download ceiling. |
| docs/video-capabilities.md | 84 | wan/2gp | Repaint | `planned` | Wan 2.1 14B int8 main asset is 14,903,022,013 bytes, exceeding the 2,198,073,147 bytes remaining under the operator-approved 60,000,000,000-byte WD-2gyw download ceiling. |
| docs/video-capabilities.md | 84 | wan/2gp | Recast | `planned` | Wan 2.1 14B int8 main asset is 14,903,022,013 bytes, exceeding the 2,198,073,147 bytes remaining under the operator-approved 60,000,000,000-byte WD-2gyw download ceiling. |
| docs/video-capabilities.md | 84 | wan/2gp | Upscale | `planned` | Wan 2.1 14B int8 main asset is 14,903,022,013 bytes, exceeding the 2,198,073,147 bytes remaining under the operator-approved 60,000,000,000-byte WD-2gyw download ceiling. |
| docs/video-capabilities.md | 85 | hunyuan/standard | Create | `host_run_verified` | ../datasets/runs/maestro-parity/WD-2gyw/evidence.json |
| docs/video-capabilities.md | 85 | hunyuan/standard | Extend | `planned` | WD-2gyw verified only the representative Create operation; Extend was not run and needs a new operator-approved per-family/per-operation batch. |
| docs/video-capabilities.md | 85 | hunyuan/standard | Blend | `planned` | WD-2gyw verified only the representative Create operation; Blend was not run and needs a new operator-approved per-family/per-operation batch. |
| docs/video-capabilities.md | 85 | hunyuan/standard | Retake | `planned` | WD-2gyw verified only the representative Create operation; Retake was not run and needs a new operator-approved per-family/per-operation batch. |
| docs/video-capabilities.md | 85 | hunyuan/standard | Edit | `planned` | WD-2gyw verified only the representative Create operation; Edit was not run and needs a new operator-approved per-family/per-operation batch. |
| docs/video-capabilities.md | 85 | hunyuan/standard | Outpaint | `unsupported` | ../datasets/runs/maestro-parity/WD-2gyw/planning/boundaries/hunyuan-standard-outpaint.result.json |
| docs/video-capabilities.md | 85 | hunyuan/standard | Repaint | `planned` | WD-2gyw verified only the representative Create operation; Repaint was not run and needs a new operator-approved per-family/per-operation batch. |
| docs/video-capabilities.md | 85 | hunyuan/standard | Recast | `planned` | WD-2gyw verified only the representative Create operation; Recast was not run and needs a new operator-approved per-family/per-operation batch. |
| docs/video-capabilities.md | 85 | hunyuan/standard | Upscale | `planned` | WD-2gyw verified only the representative Create operation; Upscale was not run and needs a new operator-approved per-family/per-operation batch. |
| docs/finishing-capabilities.md | 17 | ffmpeg | Interpolation | `host_run_verified` | ../datasets/runs/maestro-parity/WD-r81u/evidence.json |
| docs/finishing-capabilities.md | 17 | ffmpeg | Spatial upscale | `host_run_verified` | ../datasets/runs/maestro-parity/WD-r81u/evidence.json |
| docs/finishing-capabilities.md | 17 | ffmpeg | Film grain | `host_run_verified` | ../datasets/runs/maestro-parity/WD-r81u/evidence.json |
| docs/finishing-capabilities.md | 17 | ffmpeg | Face refinement | `planned` | The compass source contains no human face and no track identity, bounds, rights, or consent was supplied. |
| docs/finishing-capabilities.md | 18 | rife | Interpolation | `host_run_verified` | ../datasets/runs/maestro-parity/WD-r81u/evidence.json |
| docs/finishing-capabilities.md | 18 | rife | Spatial upscale | `unsupported` | documented boundary |
| docs/finishing-capabilities.md | 18 | rife | Film grain | `unsupported` | documented boundary |
| docs/finishing-capabilities.md | 18 | rife | Face refinement | `unsupported` | documented boundary |
| docs/finishing-capabilities.md | 19 | real_esrgan | Interpolation | `unsupported` | documented boundary |
| docs/finishing-capabilities.md | 19 | real_esrgan | Spatial upscale | `host_run_verified` | ../datasets/runs/maestro-parity/WD-r81u/evidence.json |
| docs/finishing-capabilities.md | 19 | real_esrgan | Film grain | `unsupported` | documented boundary |
| docs/finishing-capabilities.md | 19 | real_esrgan | Face refinement | `unsupported` | documented boundary |
| docs/finishing-capabilities.md | 20 | film | Interpolation | `unsupported` | documented boundary |
| docs/finishing-capabilities.md | 20 | film | Spatial upscale | `unsupported` | documented boundary |
| docs/finishing-capabilities.md | 20 | film | Film grain | `planned` | Measured film-grain pixel size 1 and temporal persistence 0 contradict planned controls 16 and 0.5. |
| docs/finishing-capabilities.md | 20 | film | Face refinement | `unsupported` | documented boundary |
| docs/finishing-capabilities.md | 21 | neural_frame_gen | Interpolation | `planned` | No named neural_frame_gen host implementation exists; absence is not hardware infeasibility. |
| docs/finishing-capabilities.md | 21 | neural_frame_gen | Spatial upscale | `planned` | No named neural_frame_gen host implementation exists; absence is not hardware infeasibility. |
| docs/finishing-capabilities.md | 21 | neural_frame_gen | Film grain | `unsupported` | documented boundary |
| docs/finishing-capabilities.md | 21 | neural_frame_gen | Face refinement | `planned` | The compass source contains no human face and no track identity, bounds, rights, or consent was supplied. |
| docs/voice-capabilities.md | 43 | vibevoice/vibe_7b | Plain speech | `host_run_verified` | ../datasets/runs/maestro-parity/WD-bxhc/evidence.json |
| docs/voice-capabilities.md | 43 | vibevoice/vibe_7b | One-reference clone | `evidence_complete_pending_review` | WD-bxhc provenance is corrected and hashes exist, but cross-story cloning-reuse consent for the WD-cpow-owned references is not evidenced; operator consent decision required. |
| docs/voice-capabilities.md | 43 | vibevoice/vibe_7b | Two-reference clone | `evidence_complete_pending_review` | WD-bxhc provenance is corrected and hashes exist, but cross-story cloning-reuse consent for the WD-cpow-owned references is not evidenced; operator consent decision required. |
| docs/voice-capabilities.md | 44 | chatterbox/chatterbox_multilingual | Plain speech | `host_run_verified` | ../datasets/runs/maestro-parity/WD-bxhc/evidence.json |
| docs/voice-capabilities.md | 44 | chatterbox/chatterbox_multilingual | One-reference clone | `unsupported` | documented boundary |
| docs/voice-capabilities.md | 44 | chatterbox/chatterbox_multilingual | Two-reference clone | `unsupported` | documented boundary |
| docs/character-capabilities.md | 48 | Portable package round-trip and hashes | Image | `host_run_verified` | ../datasets/runs/maestro-parity/WD-bxhc/evidence.json |
| docs/character-capabilities.md | 48 | Portable package round-trip and hashes | Video | `host_run_verified` | ../datasets/runs/maestro-parity/WD-bxhc/evidence.json |
| docs/character-capabilities.md | 49 | Saved voice binding | Image | `evidence_complete_pending_review` | WD-bxhc provenance is corrected and hashes exist, but cross-story cloning-reuse consent for the WD-cpow-owned references is not evidenced; operator consent decision required. |
| docs/character-capabilities.md | 49 | Saved voice binding | Video | `evidence_complete_pending_review` | WD-bxhc provenance is corrected and hashes exist, but cross-story cloning-reuse consent for the WD-cpow-owned references is not evidenced; operator consent decision required. |
| docs/character-capabilities.md | 50 | Native-source recovery | Image | `host_run_verified` | ../datasets/runs/maestro-parity/WD-bxhc/evidence.json |
| docs/character-capabilities.md | 50 | Native-source recovery | Video | `host_run_verified` | ../datasets/runs/maestro-parity/WD-bxhc/evidence.json |
| docs/character-capabilities.md | 51 | Registry identity resolution | Image | `host_run_verified` | ../datasets/runs/maestro-parity/WD-bxhc/evidence.json |
| docs/character-capabilities.md | 51 | Registry identity resolution | Video | `host_run_verified` | ../datasets/runs/maestro-parity/WD-bxhc/evidence.json |
| docs/character-capabilities.md | 52 | Appearance and voice mismatch rejection | Image | `host_run_verified` | ../datasets/runs/maestro-parity/WD-bxhc/evidence.json |
| docs/character-capabilities.md | 52 | Appearance and voice mismatch rejection | Video | `host_run_verified` | ../datasets/runs/maestro-parity/WD-bxhc/evidence.json |
| docs/character-capabilities.md | 53 | Duplicate and ambiguous identity rejection | Image | `host_run_verified` | ../datasets/runs/maestro-parity/WD-bxhc/evidence.json |
| docs/character-capabilities.md | 53 | Duplicate and ambiguous identity rejection | Video | `host_run_verified` | ../datasets/runs/maestro-parity/WD-bxhc/evidence.json |
| docs/character-capabilities.md | 54 | Immutable non-executable planning | Image | `host_run_verified` | ../datasets/runs/maestro-parity/WD-bxhc/evidence.json |
| docs/character-capabilities.md | 54 | Immutable non-executable planning | Video | `host_run_verified` | ../datasets/runs/maestro-parity/WD-bxhc/evidence.json |
| docs/character-capabilities.md | 55 | Seed-based reconstruction | Image | `host_run_verified` | ../datasets/runs/maestro-parity/WD-bxhc/evidence.json |
| docs/character-capabilities.md | 55 | Seed-based reconstruction | Video | `host_run_verified` | ../datasets/runs/maestro-parity/WD-bxhc/evidence.json |
| docs/character-capabilities.md | 56 | Cross-mode identity preservation | Image | `evidence_complete_pending_review` | WD-bxhc provenance is corrected and hashes exist, but cross-story cloning-reuse consent for the WD-cpow-owned references is not evidenced; operator consent decision required. |
| docs/character-capabilities.md | 56 | Cross-mode identity preservation | Video | `evidence_complete_pending_review` | WD-bxhc provenance is corrected and hashes exist, but cross-story cloning-reuse consent for the WD-cpow-owned references is not evidenced; operator consent decision required. |
| docs/character-capabilities.md | 57 | Generated speech, image, or video continuity | Image | `unsupported in this lane` | documented boundary |
| docs/character-capabilities.md | 57 | Generated speech, image, or video continuity | Video | `unsupported in this lane` | documented boundary |
| docs/director-capabilities.md | 32 | Deterministic ordered multi-clip plan | Prompt | `planned` | WD-dmf2 bundle is checker-failing: Whisper screenplay clip 1 0.556<0.6; SyncNet audio clip 1 0.594741<1.0; SyncNet screenplay clip 1 0.468897<1.0; reviewer_approved_count 0/1. It is also absent from capstone base 82f6c38 and retrievable only from accepted story/WD-dmf2@741a8bb. |
| docs/director-capabilities.md | 32 | Deterministic ordered multi-clip plan | Audio/music video | `planned` | WD-dmf2 bundle is checker-failing: Whisper screenplay clip 1 0.556<0.6; SyncNet audio clip 1 0.594741<1.0; SyncNet screenplay clip 1 0.468897<1.0; reviewer_approved_count 0/1. It is also absent from capstone base 82f6c38 and retrievable only from accepted story/WD-dmf2@741a8bb. |
| docs/director-capabilities.md | 32 | Deterministic ordered multi-clip plan | Screenplay | `planned` | WD-dmf2 bundle is checker-failing: Whisper screenplay clip 1 0.556<0.6; SyncNet audio clip 1 0.594741<1.0; SyncNet screenplay clip 1 0.468897<1.0; reviewer_approved_count 0/1. It is also absent from capstone base 82f6c38 and retrievable only from accepted story/WD-dmf2@741a8bb. |
| docs/director-capabilities.md | 33 | Per-clip prompt and six-frame overlap | Prompt | `planned` | WD-dmf2 bundle is checker-failing: Whisper screenplay clip 1 0.556<0.6; SyncNet audio clip 1 0.594741<1.0; SyncNet screenplay clip 1 0.468897<1.0; reviewer_approved_count 0/1. It is also absent from capstone base 82f6c38 and retrievable only from accepted story/WD-dmf2@741a8bb. |
| docs/director-capabilities.md | 33 | Per-clip prompt and six-frame overlap | Audio/music video | `planned` | WD-dmf2 bundle is checker-failing: Whisper screenplay clip 1 0.556<0.6; SyncNet audio clip 1 0.594741<1.0; SyncNet screenplay clip 1 0.468897<1.0; reviewer_approved_count 0/1. It is also absent from capstone base 82f6c38 and retrievable only from accepted story/WD-dmf2@741a8bb. |
| docs/director-capabilities.md | 33 | Per-clip prompt and six-frame overlap | Screenplay | `planned` | WD-dmf2 bundle is checker-failing: Whisper screenplay clip 1 0.556<0.6; SyncNet audio clip 1 0.594741<1.0; SyncNet screenplay clip 1 0.468897<1.0; reviewer_approved_count 0/1. It is also absent from capstone base 82f6c38 and retrievable only from accepted story/WD-dmf2@741a8bb. |
| docs/director-capabilities.md | 34 | Explicit continuity state and transitions | Prompt | `planned` | WD-dmf2 bundle is checker-failing: Whisper screenplay clip 1 0.556<0.6; SyncNet audio clip 1 0.594741<1.0; SyncNet screenplay clip 1 0.468897<1.0; reviewer_approved_count 0/1. It is also absent from capstone base 82f6c38 and retrievable only from accepted story/WD-dmf2@741a8bb. |
| docs/director-capabilities.md | 34 | Explicit continuity state and transitions | Audio/music video | `planned` | WD-dmf2 bundle is checker-failing: Whisper screenplay clip 1 0.556<0.6; SyncNet audio clip 1 0.594741<1.0; SyncNet screenplay clip 1 0.468897<1.0; reviewer_approved_count 0/1. It is also absent from capstone base 82f6c38 and retrievable only from accepted story/WD-dmf2@741a8bb. |
| docs/director-capabilities.md | 34 | Explicit continuity state and transitions | Screenplay | `planned` | WD-dmf2 bundle is checker-failing: Whisper screenplay clip 1 0.556<0.6; SyncNet audio clip 1 0.594741<1.0; SyncNet screenplay clip 1 0.468897<1.0; reviewer_approved_count 0/1. It is also absent from capstone base 82f6c38 and retrievable only from accepted story/WD-dmf2@741a8bb. |
| docs/director-capabilities.md | 35 | Beat-aware measured window mapping | Prompt | `not applicable` | not applicable |
| docs/director-capabilities.md | 35 | Beat-aware measured window mapping | Audio/music video | `planned` | WD-dmf2 bundle is checker-failing: Whisper screenplay clip 1 0.556<0.6; SyncNet audio clip 1 0.594741<1.0; SyncNet screenplay clip 1 0.468897<1.0; reviewer_approved_count 0/1. It is also absent from capstone base 82f6c38 and retrievable only from accepted story/WD-dmf2@741a8bb. |
| docs/director-capabilities.md | 35 | Beat-aware measured window mapping | Screenplay | `not applicable` | not applicable |
| docs/director-capabilities.md | 36 | Exact/window pacing preservation | Prompt | `planned` | WD-dmf2 bundle is checker-failing: Whisper screenplay clip 1 0.556<0.6; SyncNet audio clip 1 0.594741<1.0; SyncNet screenplay clip 1 0.468897<1.0; reviewer_approved_count 0/1. It is also absent from capstone base 82f6c38 and retrievable only from accepted story/WD-dmf2@741a8bb. |
| docs/director-capabilities.md | 36 | Exact/window pacing preservation | Audio/music video | `planned` | WD-dmf2 bundle is checker-failing: Whisper screenplay clip 1 0.556<0.6; SyncNet audio clip 1 0.594741<1.0; SyncNet screenplay clip 1 0.468897<1.0; reviewer_approved_count 0/1. It is also absent from capstone base 82f6c38 and retrievable only from accepted story/WD-dmf2@741a8bb. |
| docs/director-capabilities.md | 36 | Exact/window pacing preservation | Screenplay | `planned` | WD-dmf2 bundle is checker-failing: Whisper screenplay clip 1 0.556<0.6; SyncNet audio clip 1 0.594741<1.0; SyncNet screenplay clip 1 0.468897<1.0; reviewer_approved_count 0/1. It is also absent from capstone base 82f6c38 and retrievable only from accepted story/WD-dmf2@741a8bb. |
| docs/director-capabilities.md | 37 | Auto/manual review checkpoints | Prompt | `planned` | WD-dmf2 bundle is checker-failing: Whisper screenplay clip 1 0.556<0.6; SyncNet audio clip 1 0.594741<1.0; SyncNet screenplay clip 1 0.468897<1.0; reviewer_approved_count 0/1. It is also absent from capstone base 82f6c38 and retrievable only from accepted story/WD-dmf2@741a8bb. Applicable auto-mode mandatory gate count is 2/3. |
| docs/director-capabilities.md | 37 | Auto/manual review checkpoints | Audio/music video | `planned` | WD-dmf2 bundle is checker-failing: Whisper screenplay clip 1 0.556<0.6; SyncNet audio clip 1 0.594741<1.0; SyncNet screenplay clip 1 0.468897<1.0; reviewer_approved_count 0/1. It is also absent from capstone base 82f6c38 and retrievable only from accepted story/WD-dmf2@741a8bb. Applicable auto-mode mandatory gate count is 2/3. |
| docs/director-capabilities.md | 37 | Auto/manual review checkpoints | Screenplay | `planned` | WD-dmf2 bundle is checker-failing: Whisper screenplay clip 1 0.556<0.6; SyncNet audio clip 1 0.594741<1.0; SyncNet screenplay clip 1 0.468897<1.0; reviewer_approved_count 0/1. It is also absent from capstone base 82f6c38 and retrievable only from accepted story/WD-dmf2@741a8bb. Applicable auto-mode mandatory gate count is 2/3. |
| docs/director-capabilities.md | 38 | Immutable non-executable queue records | Prompt | `planned` | WD-dmf2 bundle is checker-failing: Whisper screenplay clip 1 0.556<0.6; SyncNet audio clip 1 0.594741<1.0; SyncNet screenplay clip 1 0.468897<1.0; reviewer_approved_count 0/1. It is also absent from capstone base 82f6c38 and retrievable only from accepted story/WD-dmf2@741a8bb. |
| docs/director-capabilities.md | 38 | Immutable non-executable queue records | Audio/music video | `planned` | WD-dmf2 bundle is checker-failing: Whisper screenplay clip 1 0.556<0.6; SyncNet audio clip 1 0.594741<1.0; SyncNet screenplay clip 1 0.468897<1.0; reviewer_approved_count 0/1. It is also absent from capstone base 82f6c38 and retrievable only from accepted story/WD-dmf2@741a8bb. |
| docs/director-capabilities.md | 38 | Immutable non-executable queue records | Screenplay | `planned` | WD-dmf2 bundle is checker-failing: Whisper screenplay clip 1 0.556<0.6; SyncNet audio clip 1 0.594741<1.0; SyncNet screenplay clip 1 0.468897<1.0; reviewer_approved_count 0/1. It is also absent from capstone base 82f6c38 and retrievable only from accepted story/WD-dmf2@741a8bb. |
| docs/director-capabilities.md | 39 | Authorized prompt-only enhancement | Prompt | `planned` | WD-dmf2 bundle is checker-failing: Whisper screenplay clip 1 0.556<0.6; SyncNet audio clip 1 0.594741<1.0; SyncNet screenplay clip 1 0.468897<1.0; reviewer_approved_count 0/1. It is also absent from capstone base 82f6c38 and retrievable only from accepted story/WD-dmf2@741a8bb. No produced media corresponds to the enhanced prompt. |
| docs/director-capabilities.md | 39 | Authorized prompt-only enhancement | Audio/music video | `planned` | WD-dmf2 bundle is checker-failing: Whisper screenplay clip 1 0.556<0.6; SyncNet audio clip 1 0.594741<1.0; SyncNet screenplay clip 1 0.468897<1.0; reviewer_approved_count 0/1. It is also absent from capstone base 82f6c38 and retrievable only from accepted story/WD-dmf2@741a8bb. No produced media corresponds to the enhanced prompt. |
| docs/director-capabilities.md | 39 | Authorized prompt-only enhancement | Screenplay | `planned` | WD-dmf2 bundle is checker-failing: Whisper screenplay clip 1 0.556<0.6; SyncNet audio clip 1 0.594741<1.0; SyncNet screenplay clip 1 0.468897<1.0; reviewer_approved_count 0/1. It is also absent from capstone base 82f6c38 and retrievable only from accepted story/WD-dmf2@741a8bb. No produced media corresponds to the enhanced prompt. |
| docs/director-capabilities.md | 40 | Seed-based hash reconstruction | Prompt | `planned` | WD-dmf2 bundle is checker-failing: Whisper screenplay clip 1 0.556<0.6; SyncNet audio clip 1 0.594741<1.0; SyncNet screenplay clip 1 0.468897<1.0; reviewer_approved_count 0/1. It is also absent from capstone base 82f6c38 and retrievable only from accepted story/WD-dmf2@741a8bb. |
| docs/director-capabilities.md | 40 | Seed-based hash reconstruction | Audio/music video | `planned` | WD-dmf2 bundle is checker-failing: Whisper screenplay clip 1 0.556<0.6; SyncNet audio clip 1 0.594741<1.0; SyncNet screenplay clip 1 0.468897<1.0; reviewer_approved_count 0/1. It is also absent from capstone base 82f6c38 and retrievable only from accepted story/WD-dmf2@741a8bb. |
| docs/director-capabilities.md | 40 | Seed-based hash reconstruction | Screenplay | `planned` | WD-dmf2 bundle is checker-failing: Whisper screenplay clip 1 0.556<0.6; SyncNet audio clip 1 0.594741<1.0; SyncNet screenplay clip 1 0.468897<1.0; reviewer_approved_count 0/1. It is also absent from capstone base 82f6c38 and retrievable only from accepted story/WD-dmf2@741a8bb. |
| docs/director-capabilities.md | 41 | Generated clip, audio, or finished film | Prompt | `unsupported in this lane` | documented boundary |
| docs/director-capabilities.md | 41 | Generated clip, audio, or finished film | Audio/music video | `unsupported in this lane` | documented boundary |
| docs/director-capabilities.md | 41 | Generated clip, audio, or finished film | Screenplay | `unsupported in this lane` | documented boundary |

Matrix totals: **46 verified, 34 unsupported, 120 planned, 6 pending operator consent, 2 not applicable** across 208 state-bearing cells.

The six undelivered video family groups are TaoMate, H3 outpaint, LTX-2.5, LTX-2.3, SCAIL-2, and Wan-2gp. Their exact blockers are in the table; representative-operation cells in otherwise verified families remain planned separately. Four logical voice/character rows (six Image/Video or clone cells) are pending cloning-reuse consent.

## Non-matrix editor and first-run dispositions

| Source | Line | Capability | State | Evidence/blocker |
| --- | ---: | --- | --- | --- |
| docs/editor.md | 13 | Headless deterministic project/export service | `verified_local` | tests/test_editor_project.py:150-291 real-process no-GPU coverage |
| docs/editor.md | 15 | Editor export durable queue submission | `verified_local` | tests/test_editor_project.py:178-220 deterministic export and real queue consumption |
| docs/editor.md | 19 | Authorized host export/media | `planned` | No authorized host run bundle with command, provenance, queue attempts, output hashes, QC evidence, and reviewer linkage. |
| docs/editor.md | 32 | Graphical/browser UI | `unsupported` | explicitly deferred; no GUI in this lane |
| docs/first-run.md | 8 | Hardware/advisory profile | `verified_local` | tests/test_first_run_platform.py:145-318 profile and advisory tests |
| docs/first-run.md | 34 | Download status/pause/resume | `verified_local` | tests/test_first_run_platform.py:320-433 durable download and provenance tests |
| docs/first-run.md | 59 | LLM runtime resolution | `verified_local` | tests/test_first_run_platform.py:435-474 local/external runtime tests |
| docs/first-run.md | 68 | Recorded OOM recovery guidance | `verified_local` | tests/test_first_run_platform.py:476-534 OOM recovery tests |
| docs/first-run.md | 81 | Remote host preview | `verified_local` | tests/test_first_run_platform.py:536-566 non-contacting preview tests |
| docs/first-run.md | 97 | Generated artifact from first-run | `planned` | WD-0zj8 generated half blocked on per-batch GPU/render-host authorization, model-download approval, and complete authorized host/model manifest. |

Non-matrix totals: **7 verified-local, 1 unsupported, 2 planned** across 10 claims.

## Better-than-Maestro proofs

1. Checker fail-closed: **VERIFIED** — 61 targeted tests passed: every canonical field/constraint failure, symlink, tampered hash, denied authorization, and exact non-mutating CLI diagnostic is covered; transcript gate-transcript.md#targeted-fail-closed-and-clean-machine-proofs.
2. Clean-machine one command: **NO-GPU HALF VERIFIED; GENERATED HALF BLOCKED** — Same targeted run reproduced disposable install, clips=4 plan, generated_artifact=false, exit 3 HOST_CONFIGURATION_INCOMPLETE and MODEL_MANIFEST_REQUIRED with no traceback. WD-0zj8 blocked-record has 0 media bytes; operator host/model inputs absent.

## WD-fay0 acceptance-criteria assessment

| AC | Met | Reason |
| --- | --- | --- |
| 1 | False | 120 matrix cells remain planned and 6 pending consent; no operator-approved terminal disposition exists. |
| 2 | False | WD-0zj8 and WD-dmf2 checker exit 1; WD-dmf2 also is absent from capstone base and retrievable only from accepted story branch. |
| 3 | False | WD-0zj8 has no generated artifact or canonical evidence.json; generated half remains blocked on host/model operator inputs. |
| 4 | None | Mechanical gates are recorded in gate-transcripts; full suite was pending at initial index generation and is finalized after commit. |
| 5 | False | Consolidated coverage exists, but referenced set cannot validate successfully while WD-0zj8/WD-dmf2 fail or are absent and unresolved entries lack operator approval. |

## Standing gates

| Gate | Result | Transcript |
| --- | --- | --- |
| pvg_lint | PASS 126 scanned, 0 errors, 0 review findings | `gate-transcript.md#backlog-lint` |
| targeted_proofs | PASS tests=61 errors=0 failures=0 skipped=0 | `gate-transcript.md#targeted-fail-closed-and-clean-machine-proofs` |
| full_suite | FIRST ATTEMPT FAIL: tests=2085 errors=0 failures=2 skipped=1; both failures are the real-tree check seeing in-repo gate instrumentation. Clean rerun pending | `gate-transcript.md#full-suite` |
| release_verify | PENDING_CLEAN_TREE_RERUN | `gate-transcript.md#release-verify` |
| protected_parity_base | PASS exit 0 | `gate-transcript.md#protected-file-parity` |
| protected_parity_40f8c2b | EXPECTED_EXCEPTION: services/jobs/preflight.py differs from accepted WD-e4r7 GPU CSV fail-closed fix; all other protected files unchanged | `gate-transcript.md#protected-file-parity` |
| git_diff_check | PASS exit 0 | `gate-transcript.md#whitespace-gate` |

Protected-file exception note: the only difference from `40f8c2b` is `services/jobs/preflight.py`, independently accepted by WD-e4r7 to parse `nvidia-smi` CSV and fail closed on occupied GPUs. Parity against this story base `82f6c38` is clean.

No model weights, credentials, lane media, disposable checkout, or operator normal-environment state was copied into this bundle.
