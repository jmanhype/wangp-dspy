---
id: WD-i7qs
title: "Video LTX-2.5: decouple fix_mistral_regex from the gemma4 extra_special_tokens override in the WanGP LTX tokenizer wrapper"
status: closed
priority: 1
type: bug
labels: [capability, video, evidence, external-integration, accepted]
parent: WD-3nod
created_at: 2026-09-26T03:44:27Z
created_by: speed
updated_at: 2026-09-26T04:06:33Z
content_hash: "sha256:cddbee368ae2d700abfab36db483d98af51744f0d60c1ac8146ce5b26ce5b8a9"
assignee: dev-WD-i7qs
follows: [WD-r4n8, WD-fay0, WD-dmf2]
closed_at: 2026-09-26T04:06:33Z
close_reason: "Accepted: independently reproduced real gemma4 load, video token 258884, RED/GREEN/skip behavior, branch and live-tree gates. Live deployment is deliberately NOT changed; LTX-2.5 host run remains a separately authorized batch."
blocks: [WD-fay0]
led_to: [WD-14ej, WD-isg9]
---

## Description
## Why (diagnosed on the live host, 2026-09-26)

The video matrix row `ltx/2.5` is `planned` because the authorized int8 ConvRot
attempt died before generation:

    TypeError: 'tokenizers.pre_tokenizers.Split' object does not support item assignment

Root cause is a conflation bug in the WanGP LTX gemma text encoder, proven offline:

- `models/ltx2/ltx_core/text_encoders/gemma/tokenizer.py` builds
  `kwargs = {"extra_special_tokens": {"video_token": "<|video|>"}} if fix_mistral_regex else {}`
  and passes `fix_mistral_regex=fix_mistral_regex` straight into
  `AutoTokenizer.from_pretrained`. The default is `False`.
- The call site `models/ltx2/ltx_core/text_encoders/gemma/encoders/base_encoder.py:472`
  passes `fix_mistral_regex=gemma4` -- i.e. it enables a **Mistral** regex patch for a
  **Gemma** tokenizer purely as a side effect of the gemma4 flag.
- With `fix_mistral_regex=True`, transformers `4.57.6` runs
  `tokenization_utils_base._patch_mistral_regex`, which does
  `tokenizer.backend_tokenizer.pre_tokenizer[0] = ...`. This tokenizer's
  `pre_tokenizer` is a bare `Split`, not a sequence, so the assignment raises.
- Separately, `ckpts/gemma4-12b-ltx-v1/tokenizer_config.json` declares
  `extra_special_tokens = ["<|video|>"]` as a **list**; transformers `4.57.6`
  cannot merge that form (`AttributeError: 'list' object has no attribute 'keys'`).
  So the dict override is REQUIRED and must not be removed.
- `base_encoder.py:496` in the same file already calls the wrapper with the
  default `fix_mistral_regex=False`, so line 472 is the anomaly.

### Offline proof (host `3090`, existing Wan2GP venv, CPU only, no downloads, no dependency change, no live-tree edit)

    transformers: 4.57.6 | tokenizers: 0.22.2
    tokenizer path: /home/straughter/Wan2GP/ckpts/gemma4-12b-ltx-v1

    FAIL fix_mistral_regex=True  + extra_special_tokens dict   TypeError: 'tokenizers.pre_tokenizers.Split' object does not support item assignment
    OK   fix_mistral_regex=False + extra_special_tokens dict   vocab=262144 video_token_id=258884
    FAIL fix_mistral_regex=False, no override                  AttributeError: 'list' object has no attribute 'keys'

    OK-path tokenisation: "a cat walks through rain" -> [2, 236746, 5866, 23241, 1343, 6927]
    decode: '<bos>a cat walks through rain'   (bos prefix only -- benign)
    "<|video|>" -> [2, 258884, 236768]        (video token resolves)

Conclusion: the fix is a decoupling, **not** a dependency pin and **not** a
model download. This also supersedes the earlier hypothesis that only a
`transformers<5` pin would work; the host venv is already 4.57.6 and the bug
reproduces there.

## Acceptance criteria

- AC1: The gemma4 LTX tokenizer loads through the real code path against the local
  `ckpts/gemma4-12b-ltx-v1` directory with no `TypeError`. Paste the command and output.
- AC2: `<|video|>` still resolves to id `258884` and is present in the encoded ids
  for a sample string containing it. No regression in the gemma4 behaviour that the
  dict override was providing.
- AC3: `extra_special_tokens` is passed independently of `fix_mistral_regex`;
  the wrapper still defaults to no mistral patch; non-gemma4 call sites and
  `base_encoder.py:496` keep their current behaviour.
- AC4: A regression test reproduces the failure mode **without** the 13 GB checkpoint
  (e.g. a synthetic tokenizer config whose `extra_special_tokens` is a list), fails
  before the fix and passes after, and is skipped when the real tokenizer directory
  is absent.
- AC5: Base is `origin/main` of `git@github.com:jmanhype/Wan2GP.git`; the patch is
  committed on its own branch and pushed to the `fork` remote. Before the change the
  two files must be byte-identical to `origin/main` (they are: verified, and also
  identical to the deployed tree).
- AC6: The live deployment tree `/home/straughter/Wan2GP` is NOT edited by this
  story. Deployment is a separate operator-authorized step; this story produces the
  reviewable, committed patch plus evidence.

## Constraints

- No dependency changes, no model downloads, no network beyond pushing the branch.
- Do not touch the 106 pre-existing uncommitted files in the live tree; work in an
  isolated Wan2GP worktree created from `origin/main`.
- Do not run a render. The LTX-2.5 host run remains a separately authorized batch.
- Record native scripts and outputs under
  `datasets/runs/maestro-parity/<story-id>/native-scripts/`.

## nd_contract
status: new

### evidence
- (pending)

### proof
- [ ] AC1: gemma4 LTX tokenizer loads on the real path, no TypeError
- [ ] AC2: video token still resolves to 258884
- [ ] AC3: extra_special_tokens decoupled from fix_mistral_regex; other call sites unchanged
- [ ] AC4: checkpoint-free regression test fails before / passes after, skips when absent
- [ ] AC5: committed branch from origin/main, pushed to fork; base files byte-identical
- [ ] AC6: live deployment tree untouched

## Acceptance Criteria


## Design


## Notes


## nd_contract
status: accepted

### evidence
- PM closeout applied via pvg story accept on 2026-09-25.

### proof
- [x] Story closed after accepted label was applied.


## Implementation Evidence

Commands run:
- Targeted unittest before and after the fix.
- Real-path tokenizer check.
- `pvg verify --include-tests`.

Summary: targeted GREEN 5/5 PASS; real path PASS; pvg verify 0 issues.

Commit SHA: faea82d15bf10b3479c42c0ea430892aae975870

## nd_contract
status: delivered

### evidence
- Wan2GP commit SHA: faea82d15bf10b3479c42c0ea430892aae975870

### proof
- [x] AC1: PASS
- [x] AC2: PASS
- [x] AC3: PASS
- [x] AC4: PASS
- [x] AC5: PASS
- [x] AC6: PASS

## Implementation Evidence

Commands run:
- `cd /home/straughter/Wan2GP-story-WD-i7qs && /home/straughter/Wan2GP/venv/bin/python -m unittest discover -s tests -p "test_ltx_gemma_tokenizer.py" -v`
- `PYTHONPATH=/home/straughter/Wan2GP-story-WD-i7qs /home/straughter/Wan2GP/venv/bin/python /tmp/50_real_path_check.py`
- `pvg verify --include-tests --format=text <explicit WD-i7qs evidence/test/script paths>`

Summary: targeted RED 0/5 (3 errors, 1 failure, 1 expected config failure); targeted GREEN 5/5 PASS; real gemma4 path PASS; py_compile 3/3 PASS; git diff --check PASS; full suite 21/24 PASS with 3 unrelated failures reproduced at base.

Commit SHA: Wan2GP `faea82d15bf10b3479c42c0ea430892aae975870`; wangp-dspy `9539cf5ca8e2b9c6b6966b0781c616c37bfb0068`.

### AC Verification
| AC | Status |
|----|--------|
| AC1 real tokenizer loads without TypeError | PASS |
| AC2 video token ID 258884 appears | PASS |
| AC3 options independent and legacy call unchanged | PASS |
| AC4 synthetic RED/GREEN with absence skip guard | PASS |
| AC5 branch pushed to fork | PASS |
| AC6 live tree unchanged | PASS |

## nd_contract
status: delivered

### evidence
- Wan2GP `story/WD-i7qs@faea82d15bf10b3479c42c0ea430892aae975870`.
- wangp-dspy `story/WD-i7qs@9539cf5ca8e2b9c6b6966b0781c616c37bfb0068`.

### proof
- [x] AC1: PASS
- [x] AC2: PASS
- [x] AC3: PASS
- [x] AC4: PASS
- [x] AC5: PASS
- [x] AC6: PASS

## nd_contract
status: delivered

### evidence
- Transitioned via pvg story deliver on 2026-09-25.

### proof
- [ ] Developer evidence block must remain authoritative above this contract.


## Implementation Evidence (DELIVERED)

PROOF:

### Implementation
- Wan2GP branch: `story/WD-i7qs`
- Wan2GP commit: `faea82d15bf10b3479c42c0ea430892aae975870`
- Wan2GP base: `origin/main` at `071ce70aab1169c61cc14bbefd71bdda3a04a9e9`
- Wan2GP remote: `fork/story/WD-i7qs`
- Code locations:
  - `models/ltx2/ltx_core/text_encoders/gemma/tokenizer.py:11-30` adds independent `extra_special_tokens` handling while preserving `fix_mistral_regex=False` by default.
  - `models/ltx2/ltx_core/text_encoders/gemma/encoders/base_encoder.py:472-473` requests the gemma4 token override without enabling the Mistral patch.
  - `models/ltx2/ltx_core/text_encoders/gemma/encoders/base_encoder.py:497` leaves the legacy two-argument call unchanged.
  - `tests/test_ltx_gemma_tokenizer.py:24-59` builds the checkpoint-free synthetic tokenizer; `:60-94` covers decoupling/list-config/bare-Split behavior; `:96-109` covers the deployed tokenizer and skips if absent.

### CI/Test Results
- Commands run:
  - RED: `cd /home/straughter/Wan2GP-story-WD-i7qs && /home/straughter/Wan2GP/venv/bin/python -m unittest discover -s tests -p "test_ltx_gemma_tokenizer.py" -v`
  - GREEN: same command after the fix.
  - Real path: `PYTHONPATH=/home/straughter/Wan2GP-story-WD-i7qs /home/straughter/Wan2GP/venv/bin/python /tmp/50_real_path_check.py`
  - Compile/diff gate: `/tmp/70_commit_and_push.sh` (`py_compile` on 3 files + `git diff --check`)
  - Full suite: `cd /home/straughter/Wan2GP-story-WD-i7qs && /home/straughter/Wan2GP/venv/bin/python -m unittest discover -s tests -v`
  - Full-suite baseline: same MiniMax H3 discovery command in a clean worktree at base `071ce70a`.
- Summary: RED 0/5 passing (3 errors, 1 incorrect expected failure, 1 expected config failure); GREEN 5/5 passing; real path PASS; compile PASS; diff-check PASS. Full suite ran 24 tests: 21 passed and the same 3 unrelated MiniMax H3 tests failed before and after this change.
- Coverage: no coverage runner is installed in the existing venv; no dependency was added. Behavioral coverage is 5 targeted tests plus the real-path check.
- Key output:
  - RED: `FAILED (failures=1, errors=3)`, including `TypeError: LTXVGemmaTokenizer.__init__() got an unexpected keyword argument 'extra_special_tokens'`.
  - GREEN: `Ran 5 tests in 1.731s` / `OK`.
  - Real path: `old_conflation: FAIL TypeError: 'tokenizers.pre_tokenizers.Split' object does not support item assignment`; `no_override: FAIL AttributeError: 'list' object has no attribute 'keys'`; `real_gemma4_path: OK vocab=262144 video_token_id=258884`; sample IDs contain `258884`.

### Evidence commit
- wangp-dspy branch: `story/WD-i7qs`
- wangp-dspy commit: `9539cf5ca8e2b9c6b6966b0781c616c37bfb0068`
- Evidence: `datasets/runs/maestro-parity/WD-i7qs/native-scripts/RESULTS.md`
- SHA-256 manifest: `datasets/runs/maestro-parity/WD-i7qs/native-scripts/91_evidence_manifest.sha256`

### Wiring
- `base_encoder.py:472-473` reaches the new wrapper option for gemma4.
- `base_encoder.py:497` retains the unchanged legacy default call.
- Changed files in the Wan2GP commit are exactly the two implementation files plus the new regression test; no dependency or model files changed.

### pvg verify
- `VERIFY: PASSED (3 files scanned, 0 issues)` from the explicit evidence/test/script paths recorded in `90_pvg_verify.raw.txt`.

### AC Verification
| AC # | Requirement | Code Location | Test Location | Status |
|------|-------------|---------------|---------------|--------|
| 1 | Real gemma4 tokenizer path loads without TypeError | `base_encoder.py:472-473` | `tests/test_ltx_gemma_tokenizer.py:96-109`, `50_real_path_check.raw.txt` | PASS |
| 2 | Video token remains 258884 and appears in IDs | `base_encoder.py:472-473` | `tests/test_ltx_gemma_tokenizer.py:103-109` | PASS |
| 3 | Extra token override is independent; defaults and line 497 unchanged | `tokenizer.py:11-30`; `base_encoder.py:497` | `tests/test_ltx_gemma_tokenizer.py:60-77` | PASS |
| 4 | Checkpoint-free test fails before, passes after, and guards real-path absence | `tokenizer.py:11-30` | `tests/test_ltx_gemma_tokenizer.py:24-109` | PASS |
| 5 | Own branch from origin/main, committed and pushed to fork | Wan2GP commit `faea82d1...` | `70_commit_and_push.raw.txt`, `71_source_and_remote.raw.txt` | PASS |
| 6 | Live deployment tree untouched | N/A | `00_setup.raw.txt`, `80_live_postflight.raw.txt` | PASS |

LEARNINGS:
- The synthetic regression fixture needs both a list-form `extra_special_tokens` config and a vocabulary over 100,000 entries; transformers gates `_patch_mistral_regex` on vocabulary size.
- A bare top-level `Split` pre-tokenizer is sufficient to reproduce the immutable-item-assignment failure without any model weights.
- The real-path matrix independently reproduced both dispatcher failure modes and the successful decoupled path.
- The dispatcher's core diagnosis held. One auxiliary exact sequence differed (`"<|video|>"` encoded as `[2, 258884]` through the wrapper rather than the reported `[2, 258884, 236768]`), but the required token identity remained correct.
- Creating the Wan2GP branch as a sibling git worktree kept the 106-file dirty live deployment unchanged.

### OBSERVATIONS (unrelated)
- The repository's 3 pre-existing MiniMax H3 failures are recorded in `61_existing_suite_base.raw.txt`; they reproduce identically at base.

### DISCOVERED_BUG
  title: MiniMax H3 legacy masking tests fail at Wan2GP origin/main
  context: While running the full CPU unittest suite, three failures appeared in tests unrelated to the LTX tokenizer. They also reproduce in a clean worktree at base commit 071ce70a with the existing venv. `tests/test_minimax_h3_grouped_masking.py:193` raises KeyError for video_guide_outpainting; line 212 sees only the Grouped Rows masking choice instead of Shared Timestep plus Grouped Rows; line 219 sees h3_grouped_masking_enabled(None) return True instead of False.
  affected_files: models/minimax_h3; tests/test_minimax_h3_grouped_masking.py
  discovered_during: WD-i7qs

## nd_contract
status: delivered

### evidence
- Wan2GP `story/WD-i7qs@faea82d15bf10b3479c42c0ea430892aae975870`, pushed to fork.
- wangp-dspy `story/WD-i7qs@9539cf5ca8e2b9c6b6966b0781c616c37bfb0068`, pushed to origin.
- Raw commands and outputs under `datasets/runs/maestro-parity/WD-i7qs/native-scripts/`.

### proof
- [x] AC1: gemma4 real tokenizer loads via wrapper with no TypeError; vocab=262144.
- [x] AC2: `<|video|>` maps to 258884 and appears in encoded IDs.
- [x] AC3: `extra_special_tokens` and `fix_mistral_regex` are independent; wrapper default remains False; line 497 unchanged.
- [x] AC4: checkpoint-free synthetic test is RED before and GREEN after; real-path test skips if directory is absent.
- [x] AC5: Wan2GP branch is based on origin/main 071ce70a and pushed to fork at full SHA above.
- [x] AC6: live dirty count remained 106; live HEAD and target hashes remained unchanged.

## History
- 2026-09-26T03:44:33Z status: open -> in_progress
- 2026-09-26T03:44:33Z auto-follows: linked to predecessor WD-r4n8
- 2026-09-26T03:44:33Z claimed by dev-WD-i7qs
- 2026-09-26T03:58:50Z status: in_progress -> in_progress
- 2026-09-26T03:58:50Z auto-follows: linked to predecessor WD-fay0
- 2026-09-26T03:59:20Z status: in_progress -> in_progress
- 2026-09-26T03:59:20Z auto-follows: linked to predecessor WD-dmf2
- 2026-09-26T04:06:33Z status: in_progress -> closed
- 2026-09-26T04:30:28Z dep_added: blocks WD-fay0
- 2026-09-26T20:50:57Z dep_added: blocks WD-btch
- 2026-09-26T20:53:06Z dep_removed: no_longer_blocks WD-btch

## Links
- Parent: [[WD-3nod]]
- Blocks: [[WD-fay0]]
- Follows: [[WD-r4n8]], [[WD-fay0]], [[WD-dmf2]]
- Led to: [[WD-14ej]], [[WD-isg9]]

## Comments
