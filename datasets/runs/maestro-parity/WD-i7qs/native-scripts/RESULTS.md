# WD-i7qs native Wan2GP results

## Scope and routing

- Story: `WD-i7qs`
- Host: `3090`
- Wan2GP base: `origin/main` at `071ce70aab1169c61cc14bbefd71bdda3a04a9e9`
- Isolated working tree: `/home/straughter/Wan2GP-story-WD-i7qs`
- Review branch: `story/WD-i7qs`
- Pushed commit: `faea82d15bf10b3479c42c0ea430892aae975870`
- Remote: `fork/story/WD-i7qs` (`git@github.com:jmanhype/Wan2GP.git`)
- No dependency file changed, no model was downloaded, and no render or GPU work was run.

## Code change

The patch in `40_fix.patch` and `40_fix_applied.raw.txt` makes the wrapper option explicit:

- `models/ltx2/ltx_core/text_encoders/gemma/tokenizer.py` adds an independently defaulted
  `extra_special_tokens: dict[str, str] | None = None` argument and passes that override to
  `AutoTokenizer.from_pretrained` only when supplied. `fix_mistral_regex` remains independently
  defaulted to `False`.
- `models/ltx2/ltx_core/text_encoders/gemma/encoders/base_encoder.py` now passes
  `extra_special_tokens={"video_token": "<|video|>"}` for gemma4 without setting
  `fix_mistral_regex=True`. The legacy call at line 497 remains
  `LTXVGemmaTokenizer(tokenizer_path, 1024)`.

## Evidence index

- `00_setup.raw.txt`: pre-change live state (106 dirty files, unchanged HEAD), remotes, target hashes,
  list-form `extra_special_tokens`, and isolated branch setup.
- `20_probe_synthetic.py`: checkpoint-free probe used to design a local tokenizer with a bare `Split`
  pre-tokenizer and more than 100k vocabulary entries.
- `30_regression_before_fix.raw.txt`: desired new API failed on pre-fix code (3 errors plus 1 wrong
  failure message); this is the RED run.
- `31_regression_after_fix.raw.txt`: all 5 story tests pass.
- `50_real_path_check.raw.txt`: real deployed tokenizer matrix and AC1/AC2 output.
- `60_full_unittest_after_fix.raw.txt`: all 24 collected repository tests ran; the 5 story tests passed,
  while 3 unrelated MiniMax H3 tests failed.
- `61_existing_suite_base.raw.txt`: the same 3 MiniMax H3 failures reproduce at base commit
  `071ce70a` before this story's changes.
- `70_commit_and_push.raw.txt`: `py_compile`, `git diff --check`, commit, and push output.
- `71_source_and_remote.raw.txt`: numbered source locations, changed-file list, and remote SHA.
- `80_live_postflight.raw.txt`: final live-tree safety checks.
- `90_pvg_verify.raw.txt`: explicit changed-artifact scan passed with 0 issues.

## AC verification

| AC | Result | Evidence |
|----|--------|----------|
| AC1 | PASS: real gemma4 path loads with no `TypeError`; vocab is 262144. | `50_real_path_check.raw.txt` |
| AC2 | PASS: `<|video|>` maps to 258884 and appears in encoded IDs. | `50_real_path_check.raw.txt` |
| AC3 | PASS: options are separate arguments/defaults; line 497 remains unchanged. | `31_regression_after_fix.raw.txt`, `71_source_and_remote.raw.txt` |
| AC4 | PASS: synthetic list config fails pre-fix and passes post-fix; real-path test is `skipUnless` guarded. | `30_regression_before_fix.raw.txt`, `31_regression_after_fix.raw.txt` |
| AC5 | PASS: branch is based on `071ce70a`, committed, and pushed at the full SHA above. | `70_commit_and_push.raw.txt`, `71_source_and_remote.raw.txt` |
| AC6 | PASS: live dirty count stayed 106, HEAD stayed `4c93b64a...`, and both target hashes stayed unchanged. | `00_setup.raw.txt`, `80_live_postflight.raw.txt` |

## Falsification checks

The dispatcher's causal conclusion was rechecked against the real tokenizer:

- Old conflated call (`fix_mistral_regex=True` plus the dict override):
  `TypeError: 'tokenizers.pre_tokenizers.Split' object does not support item assignment`.
- No override against the list-only config: `AttributeError: 'list' object has no attribute 'keys'`.
- New real gemma4 path: loads successfully, vocab 262144, video token ID 258884.

One auxiliary dispatcher detail did not reproduce exactly: through the wrapper, plain special-token
encoding of `"<|video|>"` produced `[2, 258884]`, not `[2, 258884, 236768]`. The required video-token
identity and presence remain correct, so this does not falsify the diagnosed failure or the fix.

## Deterministic quality check

Command:

```bash
pvg verify --include-tests --format=text \
  datasets/runs/maestro-parity/WD-i7qs/native-scripts/00_host_preflight.sh \
  datasets/runs/maestro-parity/WD-i7qs/native-scripts/10_setup_worktree.sh \
  datasets/runs/maestro-parity/WD-i7qs/native-scripts/20_probe_synthetic.py \
  datasets/runs/maestro-parity/WD-i7qs/native-scripts/30_test_ltx_gemma_tokenizer.py \
  datasets/runs/maestro-parity/WD-i7qs/native-scripts/40_fix.patch \
  datasets/runs/maestro-parity/WD-i7qs/native-scripts/50_real_path_check.py \
  datasets/runs/maestro-parity/WD-i7qs/native-scripts/70_commit_and_push.sh \
  datasets/runs/maestro-parity/WD-i7qs/native-scripts/80_live_postflight.sh \
  datasets/runs/maestro-parity/WD-i7qs/native-scripts/RESULTS.md
```

Output: `VERIFY: PASSED (3 files scanned, 0 issues)`.

## Unrelated pre-existing failures

At base and with the fix, `tests/test_minimax_h3_grouped_masking.py` has the same three failures:

- line 193: `KeyError: 'video_guide_outpainting'`
- line 212: expected shared-timestep choice order differs
- line 219: `h3_grouped_masking_enabled(None)` returns `True` instead of `False`

These are outside this story's two-file tokenizer change and were not modified.
