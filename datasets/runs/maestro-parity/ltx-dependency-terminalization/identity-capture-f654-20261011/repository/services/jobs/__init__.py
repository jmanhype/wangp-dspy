"""services.jobs — durable jobs + preflight for the one trusted 3090.

Five pieces (operator rulings, 2026-09-01):
1. Preflight before queue admission (ssh/models/disk/GPU/QC).
2. Planning stays pure; execution lives in the job executor, with a
   compile-guard so a real adapter can never fire under dspy compile.
3. Durable state machine (SQLite WAL), states below — no broker, no
   worker pool: one trusted 3090.
4. Verify-before-trust: rendered mp4 accepted only after log
   step-count verification ("N/N" Denoising present; truncated log =>
   failed with tail captured).
5. Checkpoint resume per chain clip; relaunch skips done clips.
"""
