#!/usr/bin/env python3
"""Create the durable WD-bxhc voice/portable-character completion queue."""
from __future__ import annotations

import json
from pathlib import Path

from services.jobs.queue import JobQueue


CLIPS = [
    {"clip_index": 1, "status": "pending", "log": None, "mp4": None, "qc_verdict": None,
     "kind": "voice_generation", "row": "vibevoice/vibe_7b", "artifact": "outputs/wd_bxhc_vibevoice_speech.wav"},
    {"clip_index": 2, "status": "pending", "log": None, "mp4": None, "qc_verdict": None,
     "kind": "voice_generation", "row": "chatterbox/chatterbox_multilingual", "artifact": "outputs/wd_bxhc_chatterbox_speech.wav"},
    {"clip_index": 3, "status": "pending", "log": None, "mp4": None, "qc_verdict": None,
     "kind": "portable_character", "row": "Portable package round-trip and hashes", "artifact": "packages/portable-witness.wgpcharacter"},
    {"clip_index": 4, "status": "pending", "log": None, "mp4": None, "qc_verdict": None,
     "kind": "portable_character", "row": "Saved voice binding", "artifact": "packages/portable-witness.wgpvoice"},
    {"clip_index": 5, "status": "pending", "log": None, "mp4": None, "qc_verdict": None,
     "kind": "portable_character", "row": "Native-source recovery", "artifact": "packages/recovered-native.png"},
    {"clip_index": 6, "status": "pending", "log": None, "mp4": None, "qc_verdict": None,
     "kind": "portable_character", "row": "Registry identity resolution", "artifact": "packages/registry-resolve-id.json"},
    {"clip_index": 7, "status": "pending", "log": None, "mp4": None, "qc_verdict": None,
     "kind": "portable_character", "row": "Appearance and voice mismatch rejection", "artifact": "planning/boundaries"},
    {"clip_index": 8, "status": "pending", "log": None, "mp4": None, "qc_verdict": None,
     "kind": "portable_character", "row": "Duplicate and ambiguous identity rejection", "artifact": "planning/boundaries"},
    {"clip_index": 9, "status": "pending", "log": None, "mp4": None, "qc_verdict": None,
     "kind": "portable_character", "row": "Immutable non-executable planning", "artifact": "planning/cli"},
    {"clip_index": 10, "status": "pending", "log": None, "mp4": None, "qc_verdict": None,
     "kind": "portable_character", "row": "Seed-based reconstruction", "artifact": "planning/cli"},
    {"clip_index": 11, "status": "pending", "log": None, "mp4": None, "qc_verdict": None,
     "kind": "portable_character", "row": "Cross-mode identity preservation", "artifact": "character-media-identity.json"},
]


def main() -> int:
    bundle = Path(__file__).resolve().parent
    database = bundle / "queue.db"
    if database.exists():
        raise SystemExit(f"refusing to replace existing queue: {database}")
    queue = JobQueue(database)
    try:
        job_id = queue.submit(plan_ref="WD-bxhc-voice-portable-character-batch-1", clips=CLIPS)
    finally:
        queue.close()
    record = {
        "queue_id": "wangp-JobQueue-WD-bxhc",
        "database": "queue.db",
        "job_id": job_id,
        "retry_id": "attempt-final-after-recorded-debug-attempts",
        "admission_state": "admitted",
        "preflight": "lane-coexistence-preflight.json",
        "standard_preflight": "standard-preflight.json",
        "ledger_semantics": "durable evidence ledger admitted after the authorized native operations; it binds completed artifacts and does not overwrite renderer admission semantics",
    }
    (bundle / "queue-record.json").write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(record, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
