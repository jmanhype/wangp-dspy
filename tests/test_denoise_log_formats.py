"""Live-log regression for verify_denoise_steps (tqdm-shaped H3 lines).

The strict-chain V2 run (2026-09-03) proved WanGP emits
    H3 denoising: 100%|██████████| 20/20 [03:35<00:00, 10.80s/steps]
while the old matcher required `Denoising 20/20` — healthy renders
were rejected and the poller fell to the load-stall watchdog.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from host.wangp_adapter import verify_denoise_steps, _DENOISE_LINE_RE

TQDM_DONE = ("\rH3 denoising:  95%|█████████▌| 19/20 [03:14<00:21, 10.82s/steps]"
             "\rH3 denoising: 100%|██████████| 20/20 [03:35<00:00, 10.80s/steps]"
             "\rH3 denoising: 100%|██████████| 20/20 [03:35<00:00, 10.80s/steps]")
TQDM_PARTIAL = "\rH3 denoising:  45%|████▌     | 9/20 [01:36<01:58, 10.75s/steps]"
LEGACY_DONE = "Denoising 20/20 steps complete"


def test_tqdm_complete_line_accepts():
    assert verify_denoise_steps(TQDM_DONE, 20)


def test_tqdm_partial_line_rejects():
    assert not verify_denoise_steps(TQDM_PARTIAL, 20)


def test_legacy_plain_line_still_accepts():
    assert verify_denoise_steps(LEGACY_DONE, 20)


def test_empty_and_zero_reject():
    assert not verify_denoise_steps("", 20)
    assert not verify_denoise_steps(TQDM_DONE, 0)


def test_watchdog_line_re_matches_tqdm():
    assert _DENOISE_LINE_RE.search(TQDM_DONE)
    assert _DENOISE_LINE_RE.search(TQDM_PARTIAL)
