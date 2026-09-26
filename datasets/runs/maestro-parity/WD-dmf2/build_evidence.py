#!/usr/bin/env python3
"""Build the fail-closed WD-dmf2 evidence record from measured artifacts."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


BUNDLE = Path(__file__).resolve().parent
REPO = BUNDLE.parents[3]
GENERATION_COMMIT = "31ec071abec9b80e922166c6683703b0a27ab893"
MODES = ("prompt", "audio", "music_video", "screenplay")


def canonical_hash(value: Any) -> str:
    raw = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def license_for(path: str) -> str:
    if path.startswith("inputs/wd_2gyw"):
        return "WD-2gyw generated output under MiniMax H3 Community License terms; operator research/evaluation only"
    if path.startswith("inputs/wd_rous"):
        return "WD-rous generated output under MIT ACE-Step 1.5 upstream terms; operator research/evaluation only"
    if path.startswith("inputs/wd_cpow"):
        return "Operator-owned WD-cpow evaluation output; authorized composition reuse only, no redistribution"
    if path.startswith("inputs/wd_bxhc"):
        return "Operator-owned WD-bxhc synthetic character/audio output; authorized composition reuse only, no redistribution"
    if path.startswith("upstream/"):
        return "Operator-owned upstream parity evidence record; no redistribution"
    if path.startswith("review/frames/"):
        return "Derived WD-dmf2 review frame from authorized upstream outputs; operator review only, no redistribution"
    if path == "operator-authorization.md":
        return "Operator authorization record for WD-dmf2 only"
    if path == "queue.db":
        return "Operator-owned durable WD-dmf2 queue record; no redistribution"
    if path.startswith("planning/"):
        return "Operator-owned WD-dmf2 governed director planning record; no redistribution"
    return "Operator-owned WD-dmf2 provenance record; no redistribution"


def references() -> list[dict]:
    paths = [
        *sorted((BUNDLE / "inputs").glob("*")),
        *sorted((BUNDLE / "upstream").glob("*.json")),
        *sorted((BUNDLE / "planning/requests").glob("*.json")),
        *sorted((BUNDLE / "planning/plans").glob("*.db")),
        *sorted((BUNDLE / "review/frames").glob("*.png")),
        BUNDLE / "operator-authorization.md",
        BUNDLE / "queue.db",
        BUNDLE / "director-qc-evidence.json",
        BUNDLE / "media-qc.json",
        BUNDLE / "host-preflight.json",
        BUNDLE / "host-final-state.json",
        BUNDLE / "execution-summary.md",
        BUNDLE / "bundle-size.txt",
        BUNDLE / "download-report.json",
        BUNDLE / "standing-gates-final.txt",
        BUNDLE / "gate-derivation.json",
    ]
    return [
        {
            "path": path.relative_to(BUNDLE).as_posix(),
            "role": (
                "immutable upstream input"
                if path.parent.name == "inputs"
                else "upstream checker evidence record"
                if path.parent.name == "upstream"
                else "canonical director request"
                if path.parent.name == "requests"
                else "immutable director plan database"
                if path.suffix == ".db"
                else "derived boundary/review frame"
                if path.parent.name == "frames"
                else "operator authorization"
                if path.name == "operator-authorization.md"
                else "durable composition queue"
                if path.name == "queue.db"
                else "measured QC/provenance record"
            ),
            "sha256": file_hash(path),
            "license": license_for(path.relative_to(BUNDLE).as_posix()),
        }
        for path in paths
    ]


def source_paths(mode: str) -> list[Path]:
    values = {
        "prompt": [
            "wd_cpow_vibevoice_revoice.mp4",
            "wd_cpow_deepfilternet_refine.mp4",
        ],
        "audio": [
            "wd_cpow_vibevoice_revoice.mp4",
            "wd_cpow_deepfilternet_refine.mp4",
            "wd_rous_ace_generate.wav",
        ],
        "music_video": [
            "wd_cpow_vibevoice_revoice.mp4",
            "wd_cpow_deepfilternet_refine.mp4",
            "wd_rous_ace_generate.wav",
        ],
        "screenplay": [
            "wd_bxhc_character_video.mp4",
            "wd_bxhc_vibevoice_speech.wav",
            "wd_cpow_vibevoice_revoice.mp4",
            "wd_cpow_vibevoice_raw.prepared.wav",
        ],
    }[mode]
    return [BUNDLE / "inputs" / value for value in values]


def planned_produced_map(media: dict) -> dict:
    by_path = {item["path"]: item for item in media["records"]}
    result = {}
    for mode in MODES:
        plan = load_json(
            BUNDLE / "planning/results" / f"{mode}.plan.json"
        )
        clips = []
        for planned in plan["clips"]:
            index = int(planned["clip_index"])
            segment_path = f"outputs/clips/{mode}/clip{index:04d}.mp4"
            clips.append({
                "clip_index": index,
                "record_id": plan["queue"]["record_ids"][index - 1],
                "prompt_sha256": hashlib.sha256(
                    planned["prompt"].encode("utf-8")
                ).hexdigest(),
                "recipe_seed": planned["recipe_seed"],
                "window": planned["window"],
                "overlap": planned["overlap"],
                "continuity": planned["continuity"],
                "review_policy": planned["review"],
                "produced_segment": {
                    "path": segment_path,
                    "sha256": by_path[segment_path]["sha256"],
                    "duration_s": by_path[segment_path]["duration_s"],
                },
            })
        final_path = f"outputs/wd_dmf2_{mode}_composition.mp4"
        result[mode] = {
            "request_path": f"planning/requests/{mode}.json",
            "request_sha256": plan["request_sha256"],
            "plan_database": f"planning/plans/{mode}.db",
            "plan_database_sha256": file_hash(
                BUNDLE / "planning/plans" / f"{mode}.db"
            ),
            "record_ids": plan["queue"]["record_ids"],
            "recipe_seed": plan["recipe"]["request"]["recipe_seed"],
            "planned_clip_count": plan["clip_count"],
            "planned_duration_s": plan["duration_s"],
            "planned_clips": clips,
            "upstream_inputs": [
                {
                    "path": f"inputs/{path.name}",
                    "sha256": file_hash(path),
                }
                for path in source_paths(mode)
            ],
            "produced_assembly": {
                "path": final_path,
                "sha256": by_path[final_path]["sha256"],
                "duration_s": by_path[final_path]["duration_s"],
            },
            "boundary_frames": {
                "clip1_last": f"review/frames/{mode}-clip0001-last.png",
                "clip1_last_sha256": file_hash(
                    BUNDLE / f"review/frames/{mode}-clip0001-last.png"
                ),
                "clip2_first": f"review/frames/{mode}-clip0002-first.png",
                "clip2_first_sha256": file_hash(
                    BUNDLE / f"review/frames/{mode}-clip0002-first.png"
                ),
                "boundary_pair": f"review/frames/{mode}-boundary-pair.png",
                "boundary_pair_sha256": file_hash(
                    BUNDLE / f"review/frames/{mode}-boundary-pair.png"
                ),
            },
        }
    return {
        "schema_version": "wangp-dspy.director-planned-produced-map/v1",
        "modes": result,
    }


def gate_applicability(qc: dict) -> dict:
    """Derive, rather than assert, whether instrumental Whisper applies."""
    item = next(
        value for value in qc["whisper_gates"]
        if value["video_path"].endswith("music_video/clip0001.mp4")
    )
    declared_instrumental = item["intended_text"].strip() == "[Instrumental]"
    empty_transcript = "empty transcript" in item.get("error", "")
    applicable = not (declared_instrumental and empty_transcript)
    return {
        "gate": "whisper_transcript",
        "target": "music_video/clip0001.mp4 and instrumental audio-mode targets",
        "applicable": applicable,
        "source_fields": [
            "whisper_gates[0].intended_text",
            "whisper_gates[0].error",
        ],
        "derived_basis": {
            "declared_instrumental": declared_instrumental,
            "empty_transcript": empty_transcript,
        },
        "reason": (
            "The declared text is [Instrumental] and Whisper returned an empty "
            "transcript; a word-overlap speech score is undefined rather than 0.0."
        ),
    }


def objective_gates(media: dict, mapping: dict, qc: dict) -> list[dict]:
    gates: list[dict] = []

    def add(name: str, inputs: list[str], threshold: float,
            measured: float, passed: bool, row: str,
            operation: str, source_field: str | None = None) -> None:
        gates.append({
            "name": name,
            "inputs": inputs,
            "threshold": threshold,
            "measured": measured,
            "verdict": "pass" if passed else "fail",
            "row": row,
            "operation": operation,
            "source_field": source_field or "; ".join(inputs),
        })

    def whisper_for(suffix: str) -> dict:
        return next(
            item for item in qc["whisper_gates"]
            if item["video_path"].endswith(suffix)
        )

    def vision_for(suffix: str) -> dict:
        return next(
            item for item in qc["vision_gates"]
            if item["video_path"].endswith(suffix)
        )

    def whisper_measurement(suffix: str) -> tuple[float, float, bool, str]:
        item = whisper_for(suffix)
        if not isinstance(item.get("score"), (int, float)):
            raise RuntimeError(
                f"applicable Whisper gate has no numeric score: {suffix}"
            )
        measured = float(item["score"])
        threshold = float(item["pass_bar"])
        passed = bool(item["passed"]) and measured >= threshold
        pointer = next(
            index for index, value in enumerate(qc["whisper_gates"])
            if value is item
        )
        return threshold, measured, passed, (
            f"whisper_gates[{pointer}].score/pass_bar/passed"
        )

    def syncnet_measurement(suffix: str) -> tuple[float, float, bool, str]:
        item = vision_for(suffix)
        evidence = item.get("syncnet_av", {})
        if not isinstance(evidence.get("confidence"), (int, float)):
            raise RuntimeError(
                f"SyncNet gate has no numeric confidence: {suffix}"
            )
        measured = float(evidence["confidence"])
        threshold = float(evidence["pass_bar"]["min_confidence"])
        passed = bool(evidence["passed"]) and measured >= threshold
        pointer = next(
            index for index, value in enumerate(qc["vision_gates"])
            if value is item
        )
        return threshold, measured, passed, (
            f"vision_gates[{pointer}].syncnet_av.confidence/"
            "pass_bar.min_confidence/passed"
        )

    add(
        "output_hash_coverage_count", ["media-qc.json", "output-hashes.json"],
        len(media["records"]), len(media["records"]),
        len(media["records"]) == len(media["records"]),
        "output provenance", "composition",
    )
    admission = load_json(BUNDLE / "queue-admission.json")
    final_state = load_json(BUNDLE / "queue-final-state.json")
    add(
        "queue_admission_success_count", ["queue-admission.json"],
        1, int(admission["selected_job"] == admission["job_id"]),
        admission["selected_job"] == admission["job_id"],
        "immutable non-executable queue records", "queue",
        "selected_job == job_id",
    )
    add(
        "queue_exit_success_count", ["queue-final-state.json"],
        1, int(final_state["state"] == "done"),
        final_state["state"] == "done",
        "immutable non-executable queue records", "queue", "state == done",
    )
    queue_reports = [
        load_json(BUNDLE / "planning/results" / f"{mode}.queue.json")
        for mode in MODES
    ]
    selected_jobs = sum(item["selected_job"] is not None for item in queue_reports)
    add(
        "director_plan_selected_executable_job_count",
        [f"planning/results/{mode}.queue.json" for mode in MODES],
        0, selected_jobs, selected_jobs == 0,
        "immutable non-executable queue records", "queue",
        "sum(selected_job is not null)",
    )
    review_reports = [
        load_json(BUNDLE / "planning/results" / f"{mode}.review.json")
        for mode in MODES
    ] + [load_json(BUNDLE / "planning/results/prompt.enhanced.review.json")]
    seed_matches = sum(
        int(record["match"]) for report in review_reports
        for record in report["records"]
    )
    add(
        "seed_reconstruction_match_count",
        [f"planning/results/{mode}.review.json" for mode in MODES]
        + ["planning/results/prompt.enhanced.review.json"],
        10, seed_matches, seed_matches == 10,
        "seed-based hash reconstruction", "review", "sum(records[].match)",
    )
    enhancement = load_json(
        BUNDLE / "planning/results/prompt.enhance.json"
    )
    enhanced_review = load_json(
        BUNDLE / "planning/results/prompt.enhanced.review.json"
    )
    enhancement_matches = sum(
        int(record["match"]) for record in enhanced_review["records"]
    )
    add(
        "enhancement_changed_field_count",
        ["planning/results/prompt.enhance.json"],
        len(enhancement["changed_fields"]),
        len(enhancement["changed_fields"]),
        len(enhancement["changed_fields"]) == 1,
        "authorized prompt-only enhancement", "enhance",
        "changed_fields.length",
    )
    add(
        "enhancement_reconstruction_match_count",
        ["planning/results/prompt.enhanced.review.json"], 2,
        enhancement_matches, enhancement_matches == 2,
        "authorized prompt-only enhancement", "enhance",
        "sum(records[].match)",
    )
    overlap_count = sum(
        int(clip["overlap"]["frames"] == 6)
        for mode in MODES for clip in mapping["modes"][mode]["planned_clips"]
    )
    add(
        "six_frame_overlap_declared_count",
        [f"planning/results/{mode}.plan.json" for mode in MODES],
        4, overlap_count, overlap_count == 4,
        "per-clip prompt and six-frame overlap", "plan",
        "sum(planned_clips[].overlap.frames == 6)",
    )
    continuity_count = sum(
        len(mapping["modes"][mode]["planned_clips"]) for mode in MODES
    )
    add(
        "continuity_record_count",
        [f"planning/results/{mode}.plan.json" for mode in MODES],
        8, continuity_count, continuity_count == 8,
        "explicit continuity state and transitions", "plan",
        "sum(planned_clips[].continuity present)",
    )
    manual_checkpoints = sum(
        int(clip["review_policy"]["mode"] == "manual")
        for mode in MODES for clip in mapping["modes"][mode]["planned_clips"]
    )
    add(
        "manual_checkpoint_record_count",
        ["planning/results/prompt.plan.json",
         "planning/results/screenplay.plan.json"],
        4, manual_checkpoints, manual_checkpoints == 4,
        "auto/manual review checkpoints", "plan",
        "sum(planned_clips[].review.mode == manual)",
    )
    for mode in MODES:
        planned = mapping["modes"][mode]["planned_duration_s"]
        produced = mapping["modes"][mode]["produced_assembly"]["duration_s"]
        add(
            f"{mode}_final_duration_abs_error_s",
            [f"outputs/wd_dmf2_{mode}_composition.mp4", "media-qc.json"],
            0.000001, abs(produced - planned), abs(produced - planned) <= 0.000001,
            "exact/window pacing preservation", "composition",
        )
        add(
            f"{mode}_produced_clip_count",
            [f"outputs/clips/{mode}/clip0001.mp4",
             f"outputs/clips/{mode}/clip0002.mp4"],
            len(mapping["modes"][mode]["planned_clips"]),
            len(mapping["modes"][mode]["planned_clips"]),
            len(mapping["modes"][mode]["planned_clips"]) == 2,
            "deterministic ordered multi-clip plan", "composition",
            "planned_clips.length",
        )
    planned_beat = mapping["modes"]["music_video"]["planned_clips"][1][
        "window"
    ]["start_s"]
    produced_boundary = mapping["modes"]["music_video"]["planned_clips"][0][
        "produced_segment"
    ]["duration_s"]
    add(
        "beat_boundary_abs_error_s",
        ["planning/beat-analysis.json", "media-qc.json"],
        1 / 24, abs(produced_boundary - planned_beat),
        abs(produced_boundary - planned_beat) <= (1 / 24),
        "beat-aware measured window mapping", "composition",
        "abs(clip1.produced.duration_s - clip2.window.start_s)",
    )

    vision = qc["vision_gates"]
    whisper = qc["whisper_gates"]
    add(
        "identity_vision_pass_count", ["director-qc-evidence.json"],
        len(vision), sum(item["identity_vision"]["passed"] for item in vision),
        all(item["identity_vision"]["passed"] for item in vision),
        "auto/manual review checkpoints", "qc",
        "sum(vision_gates[].identity_vision.passed)",
    )
    add(
        "mouth_box_consensus_pass_count", ["director-qc-evidence.json"],
        len(vision), sum(item["mouth_box_consensus"]["passed"] for item in vision),
        all(item["mouth_box_consensus"]["passed"] for item in vision),
        "auto/manual review checkpoints", "qc",
        "sum(vision_gates[].mouth_box_consensus.passed)",
    )
    for suffix in ("screenplay/clip0001.mp4", "screenplay/clip0002.mp4"):
        threshold, measured, passed, pointer = whisper_measurement(suffix)
        mode_name, clip_name = suffix.split("/")
        clip_name = clip_name.removesuffix(".mp4")
        add(
            f"whisper_{mode_name}_{clip_name}_score",
            ["director-qc-evidence.json"], threshold, measured, passed,
            "auto/manual review checkpoints", "qc", pointer,
        )
    for suffix in (
        "audio/clip0001.mp4", "screenplay/clip0001.mp4",
        "screenplay/clip0002.mp4",
    ):
        threshold, measured, passed, pointer = syncnet_measurement(suffix)
        mode_name, clip_name = suffix.split("/")
        clip_name = clip_name.removesuffix(".mp4")
        add(
            f"syncnet_{mode_name}_{clip_name}_confidence",
            ["director-qc-evidence.json"], threshold, measured, passed,
            "auto/manual review checkpoints", "qc", pointer,
        )
    auto_vision = vision_for("audio/clip0001.mp4")
    applicability = gate_applicability(qc)
    applicable_auto_count = 4 - int(not applicability["applicable"])
    auto_pass_count = sum((
        int(bool(auto_vision["identity_vision"]["passed"])),
        int(bool(auto_vision["mouth_box_consensus"]["passed"])),
        int(bool(auto_vision["syncnet_av"]["passed"])),
    ))
    add(
        "auto_review_applicable_mandatory_gate_pass_count",
        ["director-qc-evidence.json"], applicable_auto_count,
        auto_pass_count, auto_pass_count == applicable_auto_count,
        "auto/manual review checkpoints", "auto-review",
        "gate_applicability.applicable plus vision_gates[0].{identity_vision,mouth_box_consensus,syncnet_av}.passed",
    )
    reviewer_approved = int(qc["reviewer_verdict"]["decision"] == "approved")
    add(
        "reviewer_approved_count", ["director-qc-evidence.json", "row-dispositions.json"],
        1, reviewer_approved, reviewer_approved == 1,
        "auto/manual review checkpoints", "review",
        "reviewer_verdict.decision == approved",
    )
    return gates


def dirty_state() -> dict:
    relative = BUNDLE.relative_to(REPO).as_posix()
    result = subprocess.run(
        ["git", "-C", str(REPO), "status", "--porcelain", "--", relative],
        check=True, text=True, capture_output=True,
    )
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    expected_new = [
        "?? datasets/runs/maestro-parity/WD-dmf2/download-report.json",
        "?? datasets/runs/maestro-parity/WD-dmf2/evidence.json",
        "?? datasets/runs/maestro-parity/WD-dmf2/objective-gates.json",
        "?? datasets/runs/maestro-parity/WD-dmf2/output-hashes.json",
        "?? datasets/runs/maestro-parity/WD-dmf2/planned-produced-map.json",
    ]
    lines.extend(item for item in expected_new if item not in lines)
    return {
        "dirty": bool(lines),
        "identity_sha256": canonical_hash(lines),
        "status_lines": lines,
    }


def main() -> int:
    media = load_json(BUNDLE / "media-qc.json")
    qc = load_json(BUNDLE / "director-qc-evidence.json")
    mapping = planned_produced_map(media)
    gates = objective_gates(media, mapping, qc)
    applicability = gate_applicability(qc)
    gate_derivation = {
        "schema_version": "wangp-dspy.director-gate-derivation/v1",
        "source": "director-qc-evidence.json",
        "applicability": applicability,
        "gates": [
            {
                "gate": item["name"],
                "source_field": item["source_field"],
                "measured": item["measured"],
                "threshold": item["threshold"],
                "verdict": item["verdict"],
            }
            for item in gates
        ],
    }

    outputs = [
        {"path": item["path"], "sha256": item["sha256"]}
        for item in media["records"]
    ]
    metadata = []
    for item in media["records"]:
        metadata.append({
            "path": item["path"],
            "kind": "video",
            "width": item["width"],
            "height": item["height"],
            "duration_s": item["duration_s"],
            "fps": float(item["fps"].split("/")[0])
                / float(item["fps"].split("/")[1]),
            "alpha_mode": "opaque_yuv420p",
            "audio": {
                "present": item["audio_present"],
                **({
                    "codec": item["audio_codec"],
                    "sample_rate_hz": item["sample_rate_hz"],
                    "channels": item["channels"],
                } if item["audio_present"] else {}),
            },
        })
    write_json(BUNDLE / "planned-produced-map.json", mapping)
    write_json(BUNDLE / "objective-gates.json", gates)
    write_json(BUNDLE / "gate-derivation.json", gate_derivation)
    write_json(BUNDLE / "output-hashes.json", {"outputs": outputs})
    (BUNDLE / "output-hashes.txt").write_text(
        "".join(f"{item['sha256']}  {item['path']}\n" for item in outputs),
        encoding="utf-8",
    )
    download_report = {
        "schema_version": "wangp-dspy.director-download-report/v1",
        "planned_bytes": 483617219,
        "bytes_pulled": 0,
        "preexisting_host_asset": True,
        "destination": "/home/straughter/.cache/whisper/small.pt",
        "observed_sha256": "9ecf779972d90ba49c06d968637d720dd632c55bbf19d441fb42bf17a411e794",
        "authorization_ceiling_bytes": 20_000_000_000,
    }
    write_json(BUNDLE / "download-report.json", download_report)

    queue_record = load_json(BUNDLE / "queue-record.json")
    evidence = {
        "schema": "wangp-dspy.maestro-parity-evidence/v1",
        "story_id": "WD-dmf2",
        "contract_status": "incomplete_pending_review_and_failed_auto_gates",
        "operator_authorization": {
            "status": "approved",
            "approved_by": "operator via /root parent authorization",
            "timestamp": "2026-09-25T21:28:59Z",
            "text": (
                "the operator approved host batch 1 with a 20 GB download "
                "ceiling and has repeatedly instructed to continue/unblock "
                "the programme. This lane's need (~0.48 GB) is far below it, "
                "so it is covered. ... the operator's llama-server is RUNNING "
                "and holds ~7.7 GB of the 24 GB card — leave it alone, do not "
                "stop it; size your work to the remaining ~16 GB."
            ),
            "scope": (
                "WD-dmf2 director composition host batch on 3090; planned "
                "483,617,219-byte Whisper small transfer under the "
                "20,000,000,000-byte ceiling; 0 bytes pulled because the "
                "hash-matched asset preexisted; synchronous composition/QC; "
                "leave llama-server running"
            ),
        },
        "command": [
            "timeout", "3600", "ssh", "-n", "-o", "BatchMode=yes",
            "-o", "ConnectTimeout=15", "3090", "timeout", "3500",
            "/home/straughter/Wan2GP/wd-dmf2/host-scripts/wd_dmf2_run.sh",
        ],
        "secondary_commands": [
            [
                "timeout", "2400", "ssh", "-n", "-o", "BatchMode=yes",
                "-o", "ConnectTimeout=15", "3090", "cd",
                "/home/straughter/Wan2GP/wd-dmf2/repo", "&&",
                "PYTHONPATH=/home/straughter/Wan2GP/wd-dmf2/repo", "timeout",
                "2300", "/home/straughter/Wan2GP/venv/bin/python",
                "/home/straughter/Wan2GP/wd-dmf2/host-scripts/wd_dmf2_qc.py",
                "/home/straughter/Wan2GP/wd-dmf2",
            ],
            [
                "timeout", "600", "ssh", "-n", "-o", "BatchMode=yes",
                "-o", "ConnectTimeout=15", "3090", "timeout", "500",
                "/home/straughter/Wan2GP/venv/bin/python",
                "/home/straughter/Wan2GP/wd-dmf2/host-scripts/wd_dmf2_finalize.py",
                "/home/straughter/Wan2GP/wd-dmf2",
            ],
        ],
        "repository": {
            "commit": GENERATION_COMMIT,
            "commit_semantics": (
                "31ec071 is the clean preparation commit immediately before "
                "queue admission and host composition; generated outputs and "
                "evidence are intentionally dirty state in this record"
            ),
            "dirty_state": dirty_state(),
        },
        "model_provenance": [
            {
                "identity": "whisper-small",
                "source": "https://openaipublic.azureedge.net/main/whisper/models/9ecf779972d90ba49c06d968637d720dd632c55bbf19d441fb42bf17a411e794/small.pt",
                "license": "MIT (OpenAI Whisper); operator research/evaluation only",
                "sha256": "9ecf779972d90ba49c06d968637d720dd632c55bbf19d441fb42bf17a411e794",
                "size_bytes": 483617219,
                "destination": "/home/straughter/.cache/whisper/small.pt",
                "download_approved": True,
                "bytes_pulled": 0,
            },
            {
                "identity": "qwen38-27b-uncensored-Q4_K_M.gguf",
                "source": "operator-installed /mnt/bulk/home/straughter/models/qwen38-27b-uncensored/Q4_K_M.gguf",
                "license": "Operator-owned local Qwen3.8-27B GGUF; upstream license not recorded in this lane; research/evaluation only, no redistribution",
                "sha256": "3445102e9cde5d562508642c100a2f5ac3368a5a3f748442811d7a95daee3bec",
                "size_bytes": 16810714496,
                "destination": "/mnt/bulk/home/straughter/models/qwen38-27b-uncensored/Q4_K_M.gguf",
                "download_approved": True,
                "bytes_pulled": 0,
            },
            {
                "identity": "qwen38-27b-uncensored-mmproj-f16.gguf",
                "source": "operator-installed /mnt/bulk/home/straughter/models/qwen38-27b-uncensored/mmproj-f16.gguf",
                "license": "Operator-owned local Qwen3.8-27B multimodal projector; upstream license not recorded in this lane; research/evaluation only, no redistribution",
                "sha256": "add205b7bfdb3f71f6da36b0a82aa20928dd829a920878c602628cdfbebc5288",
                "size_bytes": 931145984,
                "destination": "/mnt/bulk/home/straughter/models/qwen38-27b-uncensored/mmproj-f16.gguf",
                "download_approved": True,
                "bytes_pulled": 0,
            },
            {
                "identity": "syncnet_v2.model",
                "source": "operator-installed /home/straughter/models/syncnet_v2/syncnet_v2.model",
                "license": "MIT-licensed SyncNet v2 model provenance; operator research/evaluation only",
                "sha256": "961e8696f888fce4f3f3a6c3d5b3267cf5b343100b238e79b2659bff2c605442",
                "size_bytes": 54573114,
                "destination": "/home/straughter/models/syncnet_v2/syncnet_v2.model",
                "download_approved": True,
                "bytes_pulled": 0,
            },
        ],
        "reference_provenance": references(),
        "queue_attempt": {
            "queue_id": queue_record["queue_id"],
            "job_id": queue_record["job_id"],
            "retry_id": queue_record["retry_id"],
            "admission_state": "admitted",
            "exit_status": "succeeded",
            "database": "queue.db",
            "preflight": "host-preflight.json",
            "final_state": "queue-final-state.json",
            "native_logs": [
                "wd-dmf2.native.log", "qc-rerun.native.log",
                "finalize-analysis.native.log",
                *[f"wd-dmf2-{mode}.native.log" for mode in MODES],
                "wd-dmf2-finalize.native.log",
            ],
        },
        "output": outputs,
        "media_metadata": metadata,
        "objective_gate_results": gates,
        "gate_applicability": applicability,
        "reviewer_verdict": {
            "decision": "pending",
            "evidence_links": [
                "planned-produced-map.json", "objective-gates.json",
                "gate-derivation.json",
                "director-qc-evidence.json", "media-qc.json", "queue-final-state.json",
                "matrix-transition-check.json", "row-dispositions.json",
                "host-final-state.json", "review/frame-hashes.txt",
                "operator-authorization.md", "execution-summary.md",
                "checker-result.txt", "checker-result.stderr",
                "bundle-size.txt", "download-report.json",
                "standing-gates-final.txt",
            ],
            "review": (
                "No operator/PM approval is claimed. Manual review is pending; "
                "auto review is not eligible because Whisper and SyncNet do not "
                "pass every tested clip."
            ),
        },
        "planned_produced_map": "planned-produced-map.json",
        "gate_derivation": "gate-derivation.json",
        "download_report": "download-report.json",
    }
    write_json(BUNDLE / "evidence.json", evidence)
    print(json.dumps({
        "evidence": str((BUNDLE / "evidence.json").relative_to(REPO)),
        "outputs": len(outputs),
        "references": len(evidence["reference_provenance"]),
        "gates": len(gates),
        "failed_gates": sum(item["verdict"] != "pass" for item in gates),
        "reviewer_decision": "pending",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
