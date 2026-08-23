# comic_critics — local QC lane for COMIC-style video eval

Port of the COMIC video_eval harness (arXiv:2603.11048) to a
judge-agnostic setup, so skits can be scored against YouTube-aligned
comedy critics WITHOUT Gemini quota.

## Honest caveat (read before trusting numbers)

The critic personas (global_best + channel_best) were **validated on
Gemini**. Local-vLLM and GLM scores are **correlation experiments
until calibrated against user judgments** — treat them as a relative
signal, not ground truth.

Known baseline numbers (Gemini, eval_20260821_232933):
- cloud H3: **55% combined win rate**
- v11 local partial: **0/4**

Also note: the local vLLM judge convention samples video at ~1s/frame
and receives **no audio** — comedic timing that lives in audio or
sub-second editing is invisible to it.

## Usage

    python -m qc.comic_critics.evaluate \
        --gen /tmp/comic-eval/data/videos \
        --judge local --max-refs 2 \
        --report-dir /tmp/comic-eval-local/eval_out

- `--judge local` — OpenAI-compatible vLLM server (default
  `http://<3090-host>:18020/v1`, qwen 27B; override with
  `COMIC_VLLM_BASE_URL` / `COMIC_VLLM_MODEL` / `COMIC_VLLM_API_KEY`).
- `--judge glm` — glm-4.6v with `video_url` content parts. Requires
  **public http(s) URLs** (serve local renders and tunnel). Key from
  `ZAI_API_KEY`.
- `--judge gemini` — passthrough of the original backend, for
  cross-validation against the baseline only.

Output shapes are identical to the upstream Gemini harness
(per-critic CSV + combined CSV/JSON with avg_win_rate, g_norm_inter,
g_norm_intra), so runs are directly comparable with
eval_20260821_232933.

## Deliberate divergence from upstream

Upstream's malformed-output fallback was `random.choice([1, 2])`.
This port falls back **deterministically to candidate-1** and records
a `parse_error` in the evaluation call (also counted in output). This
is the only behavioral change; everything else is contract-preserving.

## Tests

    .venv/bin/python -m pytest tests/tools/comic_critics/ -v

Recorded fixtures only — no live API calls in tests.

## References manifest format

`--refs` takes a text file mapping channels to reference videos
(same shape as upstream `data/test/middle.txt`):

    # Channel_Name (underscored)
    Video_Title https://www.youtube.com/watch?v=<11-char-id>
    Another_Title https://youtu.be/<11-char-id>

Lines starting with `#` are channel headers; each following line is
`<ref_id> <youtube_url>`. Reference mp4s are resolved from
`<videos_dir>/val_videos/<id>.mp4` (cached); missing files fall back to
the YouTube URL for judges that accept remote URLs (Gemini/GLM — the
local vLLM backend requires cached files).
