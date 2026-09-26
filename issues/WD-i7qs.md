---
id: WD-i7qs
title: "Video LTX-2.5: decouple fix_mistral_regex from the gemma4 extra_special_tokens override in the WanGP LTX tokenizer wrapper"
status: in_progress
priority: 1
type: bug
labels: [capability, video, evidence, external-integration]
parent: WD-3nod
created_at: 2026-09-26T03:44:27Z
created_by: speed
updated_at: 2026-09-26T03:44:33Z
content_hash: "sha256:424a7353ca5d6563930d88a90ea98ae145bc18276006b241293f4cdde9a1c484"
assignee: dev-WD-i7qs
follows: [WD-r4n8]
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


## History
- 2026-09-26T03:44:33Z status: open -> in_progress
- 2026-09-26T03:44:33Z auto-follows: linked to predecessor WD-r4n8
- 2026-09-26T03:44:33Z claimed by dev-WD-i7qs

## Links
- Parent: [[WD-3nod]]
- Follows: [[WD-r4n8]]

## Comments
