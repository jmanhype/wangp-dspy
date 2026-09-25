#!/usr/bin/env python3
"""Create the durable WD-dmf2 director composition batch."""
from __future__ import annotations

import json
from pathlib import Path

from services.jobs.queue import JobQueue


BUNDLE = Path(__file__).resolve().parent


def _clip(index: int, mode: str, request_hash: str, seed: int) -> dict:
    return {
        "clip_index": index,
        "status": "pending",
        "log": None,
        "mp4": f"outputs/wd_dmf2_{mode}_composition.mp4",
        "qc_verdict": None,
        "kind": "director_composition",
        "mode": mode,
        "plan_database": f"planning/plans/{mode}.db",
        "request_sha256": request_hash,
        "recipe_seed": seed,
        "segment_outputs": [
            f"outputs/clips/{mode}/clip{position:02d}.mp4"
            for position in (1, 2)
        ],
        "render_native": True,
        "reviewer_decision": "pending",
    }


def main() -> int:
    database = BUNDLE / "queue.db"
    if database.exists():
        raise SystemExit(f"refusing to replace existing queue: {database}")
    request_hashes = {}
    for mode in ("prompt", "audio", "music_video", "screenplay"):
        payload = json.loads(
            (BUNDLE / "planning" / "results" / f"{mode}.plan.json").read_text(
                encoding="utf-8"
            )
        )
        request_hashes[mode] = payload["request_sha256"]
    clips = [
        _clip(1, "prompt", request_hashes["prompt"], 9412),
        _clip(2, "audio", request_hashes["audio"], 9413),
        _clip(3, "music_video", request_hashes["music_video"], 9414),
        _clip(4, "screenplay", request_hashes["screenplay"], 9415),
    ]
    queue = JobQueue(database)
    try:
        job_id = queue.submit(
            plan_ref="WD-dmf2-director-composition-batch-1", clips=clips
        )
    finally:
        queue.close()
    record = {
        "queue_id": "wangp-JobQueue-WD-dmf2",
        "database": "queue.db",
        "job_id": job_id,
        "retry_id": "attempt-1",
        "admission_state": "admitted",
        "preflight": "host-preflight.json",
        "operator_authorization": "operator-authorization.md",
    }
    (BUNDLE / "queue-record.json").write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(record, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
