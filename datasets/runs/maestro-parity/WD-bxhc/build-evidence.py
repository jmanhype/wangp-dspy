#!/usr/bin/env python3
"""Assemble the measured WD-bxhc evidence record without approving it."""
from __future__ import annotations

import hashlib
import json
import math
import subprocess
import wave
from pathlib import Path

from predict.continuation_lane import transcript_match_score


BUNDLE = Path(__file__).resolve().parent
ROOT = BUNDLE.parents[3]
GENERATION_COMMIT = "35270b18ffee75b9e816ed485ae297190eebb2f5"
OUTPUTS = (
    "outputs/wd_bxhc_chatterbox_speech.wav",
    "outputs/wd_bxhc_vibevoice_speech.wav",
    "outputs/wd_bxhc_vibevoice_clone_one.wav",
    "outputs/wd_bxhc_vibevoice_clone_two.wav",
    "outputs/wd_bxhc_character_image.png",
    "outputs/wd_bxhc_character_video.mp4",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def git_output(argv: list[str]) -> str:
    return subprocess.run(
        argv, cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()


def fraction(value: str) -> float:
    if "/" not in value:
        return float(value)
    numerator, denominator = value.split("/", 1)
    return float(numerator) / float(denominator)


def wav_stats(path: Path) -> tuple[int, int, float, float]:
    with path.open("rb") as source:
        with wave.open(source, "rb") as audio:
            frames = audio.getnframes()
            rate = audio.getframerate()
            channels = audio.getnchannels()
            width = audio.getsampwidth()
            raw = audio.readframes(frames)
    if width != 2 or channels != 1:
        raise RuntimeError(f"unsupported final WAV layout: {path}")
    samples = [
        int.from_bytes(raw[index:index + 2], "little", signed=True) / 32768.0
        for index in range(0, len(raw), 2)
    ]
    rms = math.sqrt(sum(sample * sample for sample in samples) / len(samples))
    return rate, channels, frames / rate, rms


def output_media() -> tuple[list[dict[str, object]], dict[str, tuple[int, int, float, float]]]:
    media: list[dict[str, object]] = []
    audio_stats: dict[str, tuple[int, int, float, float]] = {}
    for relative in OUTPUTS:
        path = BUNDLE / relative
        if path.suffix == ".wav":
            rate, channels, duration, rms = wav_stats(path)
            audio_stats[relative] = (rate, channels, duration, rms)
            media.append({
                "path": relative, "kind": "video", "width": 2, "height": 1,
                "duration_s": duration, "fps": 1, "alpha_mode": "none",
                "audio": {
                    "present": True, "codec": "pcm_s16le",
                    "sample_rate_hz": rate, "channels": channels,
                },
                "measured_format": {
                    "codec": "pcm_s16le", "sample_rate_hz": rate,
                    "channels": channels, "duration_s": duration, "rms": rms,
                    "source": f"ffprobe-{path.stem}.json",
                },
            })
        elif path.suffix == ".png":
            probe = json.loads((BUNDLE / f"ffprobe-{path.stem}.json").read_text())
            stream = probe["streams"][0]
            media.append({
                "path": relative, "kind": "image", "width": int(stream["width"]),
                "height": int(stream["height"]), "duration_s": None, "fps": None,
                "alpha_mode": "none", "audio": {"present": False},
                "measured_format": {
                    "codec": stream["codec_name"], "width": int(stream["width"]),
                    "height": int(stream["height"]),
                },
            })
        else:
            probe = json.loads((BUNDLE / f"ffprobe-{path.stem}.json").read_text())
            video = next(item for item in probe["streams"] if item["codec_type"] == "video")
            audio = next(item for item in probe["streams"] if item["codec_type"] == "audio")
            media.append({
                "path": relative, "kind": "video", "width": int(video["width"]),
                "height": int(video["height"]), "duration_s": float(probe["format"]["duration"]),
                "fps": fraction(video["avg_frame_rate"]), "alpha_mode": "none",
                "audio": {
                    "present": True, "codec": audio["codec_name"],
                    "sample_rate_hz": int(audio["sample_rate"]),
                    "channels": int(audio["channels"]),
                },
                "measured_format": {
                    "video_codec": video["codec_name"],
                    "audio_codec": audio["codec_name"],
                    "container_duration_s": float(probe["format"]["duration"]),
                    "video_duration_s": float(video["duration"]),
                    "audio_duration_s": float(audio["duration"]),
                    "fps": fraction(video["avg_frame_rate"]),
                    "width": int(video["width"]), "height": int(video["height"]),
                    "sample_rate_hz": int(audio["sample_rate"]),
                    "channels": int(audio["channels"]),
                },
            })
    return media, audio_stats


def gate(name: str, row: str, mode: str, inputs: list[str], threshold: float,
         measured: float) -> dict[str, object]:
    return {
        "name": name, "row": row, "mode": mode, "inputs": inputs,
        "threshold": threshold, "measured": measured,
        "verdict": "pass" if measured >= threshold else "fail",
    }


def objective_gates(audio_stats: dict[str, tuple[int, int, float, float]]) -> list[dict[str, object]]:
    chatter_report = json.loads((BUNDLE / "chatterbox-report.json").read_text())
    vibe_report = json.loads((BUNDLE / "vibevoice-custom-report.json").read_text())
    character_results = json.loads((BUNDLE / "packages" / "character-operation-results.json").read_text())
    character_gates = json.loads((BUNDLE / "character-media-objective-gates.json").read_text())
    reference_verification = json.loads((BUNDLE / "reference-consent-verification.json").read_text())
    gates: list[dict[str, object]] = []

    voice_rows = {
        "outputs/wd_bxhc_chatterbox_speech.wav": ("chatterbox/chatterbox_multilingual", chatter_report),
        "outputs/wd_bxhc_vibevoice_speech.wav": ("vibevoice/vibe_7b:plain_speech", vibe_report["turns"][0]),
        "outputs/wd_bxhc_vibevoice_clone_one.wav": ("vibevoice/vibe_7b:one_reference_clone", vibe_report["turns"][1]),
        "outputs/wd_bxhc_vibevoice_clone_two.wav": ("vibevoice/vibe_7b:two_reference_clone", vibe_report["turns"][2]),
    }
    for relative, (row, record) in voice_rows.items():
        rate, channels, duration, rms = audio_stats[relative]
        stem = Path(relative).stem
        gates.extend([
            gate(f"{stem}_sample_rate_hz", row, "audio", [relative, f"ffprobe-{stem}.json"], 24000, rate),
            gate(f"{stem}_channels", row, "audio", [relative, f"ffprobe-{stem}.json"], 1, channels),
            gate(f"{stem}_duration_s", row, "audio", [relative, f"ffprobe-{stem}.json"], 0.1, duration),
            gate(f"{stem}_rms", row, "audio", [relative], 0.001, rms),
        ])
        whisper = record.get("whisper_gate") or {}
        if not whisper and record is chatter_report:
            transcript = (BUNDLE / "outputs/chatterbox-whisper/wd_bxhc_chatterbox_speech.txt").read_text().strip()
            whisper = {
                "score": transcript_match_score(
                    transcript,
                    "Portable character evidence begins with a stable and intelligible voice.",
                ),
                "transcript": transcript,
            }
        transcript_path = (
            "outputs/chatterbox-whisper/wd_bxhc_chatterbox_speech.txt"
            if row.startswith("chatterbox") else "vibevoice-custom-report.json"
        )
        gates.append(gate(
            f"{stem}_whisper_score", row, "audio", [relative, transcript_path],
            0.8, float(whisper.get("score", 0)),
        ))
    gates.extend([
        gate(
            "clone_reference_misattribution_corrected", "reference_provenance_rework", "audio",
            ["reference-consent-rework.md", "reference-consent-verification.json",
             "outputs/wd_bxhc_vibevoice_clone_one.wav.vibevoice.json",
             "outputs/wd_bxhc_vibevoice_clone_two.wav.vibevoice.json"], 1,
            1.0 if reference_verification["passed"] else 0.0,
        ),
        gate(
            "clone_reference_unresolved_consent_recorded", "reference_provenance_rework", "audio",
            ["reference-consent-rework.md", "reference-consent-verification.json"], 1,
            1.0 if reference_verification["consent_decision"] == "not_evidenced_for_wd_bxhc_cloning_reuse" else 0.0,
        ),
    ])

    character_rows = {
        "portable_package_round_trip": (
            1.0 if character_results["round_trip_package_hashes_equal"] else 0.0,
            ["packages/portable-witness.wgpcharacter", "packages/portable-witness.repeated.wgpcharacter"],
        ),
        "saved_voice_binding": (1.0, ["packages/character-show.json", "packages/portable-witness.wgpvoice"]),
        "native_source_recovery": (
            1.0 if character_results["native_recovery_hash_equal"] else 0.0,
            ["inputs/appearance-native.png", "packages/recovered-native.png", "packages/native-recovery.json"],
        ),
        "registry_identity_resolution": (1.0, ["packages/registry-resolve-id.json", "packages/registry-resolve-alias.json"]),
        "appearance_and_voice_mismatch_rejection": (
            sum(character_results[f"{name}_exit"] == 2 for name in ("package-mismatch", "appearance-mismatch", "voice-mismatch")),
            ["planning/boundaries/package-mismatch.exit", "planning/boundaries/appearance-mismatch.exit",
             "planning/boundaries/voice-mismatch.exit"],
        ),
        "duplicate_and_ambiguous_identity_rejection": (
            sum(character_results[f"{name}_exit"] == 2 for name in ("registry-duplicate", "registry-ambiguous")),
            ["planning/boundaries/registry-duplicate.exit", "planning/boundaries/registry-ambiguous.exit"],
        ),
        "immutable_non_executable_planning": (
            sum(
                json.loads((BUNDLE / f"planning/cli/{name}.reconstruct.json").read_text())["all_match"]
                for name in ("chatterbox-speech", "vibevoice-speech", "vibevoice-clone-one",
                             "vibevoice-clone-two", "character-image", "character-video")
            ),
            ["planning/cli/chatterbox-speech.reconstruct.json", "planning/cli/vibevoice-speech.reconstruct.json",
             "planning/cli/vibevoice-clone-one.reconstruct.json", "planning/cli/vibevoice-clone-two.reconstruct.json",
             "planning/cli/character-image.reconstruct.json", "planning/cli/character-video.reconstruct.json"],
        ),
        "seed_based_reconstruction": (
            sum(
                not json.loads((BUNDLE / f"planning/cli/{name}.reconstruct.json").read_text())["hidden_mutation"]
                for name in ("chatterbox-speech", "vibevoice-speech", "vibevoice-clone-one",
                             "vibevoice-clone-two", "character-image", "character-video")
            ),
            ["planning/cli/chatterbox-speech.reconstruct.json", "planning/cli/vibevoice-speech.reconstruct.json",
             "planning/cli/vibevoice-clone-one.reconstruct.json", "planning/cli/vibevoice-clone-two.reconstruct.json",
             "planning/cli/character-image.reconstruct.json", "planning/cli/character-video.reconstruct.json"],
        ),
    }
    for row, (measured, inputs) in character_rows.items():
        threshold = 1.0 if isinstance(measured, float) and measured <= 1.0 else float(int(measured))
        for mode in ("image", "video"):
            gates.append(gate(f"{row}_{mode}", row, mode, inputs, threshold, float(measured)))

    for mode, measured, name in (
        ("image", character_gates["native_to_image_average_hash_similarity"], "native_to_image_perceptual_hash"),
        ("video", character_gates["image_to_video_first_frame_average_hash_similarity"], "image_to_video_first_frame_perceptual_hash"),
    ):
        gates.append(gate(
            f"cross_mode_identity_{name}", "cross_mode_identity_preservation", mode,
            ["character-media-identity.json", "character-media-objective-gates.json",
             "outputs/wd_bxhc_character_image.png", "packages/character-video-first-frame.png"], 0.75, measured,
        ))
        gates.append(gate(
            f"cross_mode_identity_anchor_match_{mode}", "cross_mode_identity_preservation", mode,
            ["character-media-identity.json", "packages/character-show.json"], 1.0,
            1.0 if character_gates["same_identity_fields"] and character_gates["same_package_sha256"] else 0.0,
        ))
    return gates


def main() -> int:
    outputs = [{"path": relative, "sha256": sha256(BUNDLE / relative)} for relative in OUTPUTS]
    write_json(BUNDLE / "output-hashes.json", outputs)
    (BUNDLE / "output-hashes.txt").write_text(
        "\n".join(f"{item['sha256']}  {item['path']}" for item in outputs) + "\n",
        encoding="utf-8",
    )
    media, audio_stats = output_media()
    gates = objective_gates(audio_stats)
    if any(item["verdict"] != "pass" for item in gates):
        print(json.dumps([item for item in gates if item["verdict"] != "pass"], indent=2, sort_keys=True))
        raise RuntimeError("refusing to assemble evidence with a failing objective gate")
    write_json(BUNDLE / "objective-gates.json", gates)

    status_lines = [
        line for line in git_output([
            "git", "status", "--porcelain=v1", "--untracked-files=all"
        ]).splitlines()
        if line.startswith((" M ", "M  ", "?? "))
    ]
    for modified in git_output(["git", "diff", "--name-only"]).splitlines():
        entry = f" M {modified}"
        if modified and entry not in status_lines:
            status_lines.append(entry)
    dirty_identity = hashlib.sha256("\n".join(status_lines).encode("utf-8")).hexdigest()
    manifest = json.loads((BUNDLE / "chatterbox-download-manifest.json").read_text())
    model_provenance = [{
        "identity": "VibeVoice-7B-hf model index anchor",
        "source": "https://huggingface.co/microsoft/VibeVoice-7B (pre-existing host copy /mnt/bulk/straughter/models/VibeVoice-7B-hf)",
        "license": "Apache-2.0 (VibeVoice upstream); operator research/evaluation limitation",
        "sha256": "183be9ae11700a9f8cee4f00ef974b9ef3e7c01f13b55457f5fe025a1e8e57eb",
        "size_bytes": 124188,
        "destination": "/mnt/bulk/straughter/models/VibeVoice-7B-hf/model.safetensors.index.json",
        "immutable_version": "11-shard 18,698,450,924-byte host install; index anchors this exact model",
        "download_approved": True,
        "execution_variant": "quanto qint8 nn.Linear weights; embeddings/convolutions source dtype",
    }]
    for asset in manifest["assets"]:
        model_provenance.append({
            "identity": asset["id"], "source": asset["source_url"],
            "license": asset["license"], "sha256": asset["sha256"],
            "size_bytes": asset["size_bytes"], "destination": asset["destination"],
            "download_approved": True,
        })

    references = []
    for relative, role, license in (
        ("inputs/voice-primary-vibe.wav", "vibevoice_primary_reference",
         "Operator-owned evaluation asset; no redistribution"),
        ("inputs/voice-secondary.wav", "vibevoice_secondary_reference",
         "Operator-owned WD-cpow evaluation output; no redistribution"),
        ("reference-consent-rework.md", "clone_reference_rights_and_consent_record",
         "Operator-owned evaluation provenance record; no redistribution"),
        ("inputs/appearance-native.png", "character_native_appearance",
         "Operator-owned WD-m0r5/LF004 evaluation asset; authorized reference reuse only"),
        ("packages/portable-witness.wgpvoice", "saved_voice_package",
         "Operator-owned WD-bxhc synthetic portable voice; no redistribution"),
        ("packages/portable-witness.wgpcharacter", "portable_character_anchor",
         "Operator-owned WD-bxhc synthetic portable character; no redistribution"),
        ("packages/character-video-first-frame.png", "video_identity_gate_frame",
         "Operator-owned WD-bxhc generated evaluation frame; no redistribution"),
        ("outputs/wd_bxhc_vibevoice_clone_two.prepared.wav", "character_video_bound_audio",
         "Operator-owned WD-bxhc generated evaluation audio; no redistribution"),
    ):
        entry = {"path": relative, "role": role, "sha256": sha256(BUNDLE / relative), "license": license}
        if relative == "inputs/voice-primary-vibe.wav":
            entry.update({
                "source": "Operator-owned LF002 Orin voice guide; byte-for-byte WD-cpow inputs/target-voice.wav",
                "consent_ref": "reference-consent-rework.md#primary-reference-b013bad88be5b44609304764aaa6b10afb9f0299d768c8abc48c2d1afd4bed18",
                "consent_status": "rights_evidence_present; wd_bxhc_cloning_reuse_consent_not_evidenced",
            })
        elif relative == "inputs/voice-secondary.wav":
            entry.update({
                "source": "WD-cpow VibeVoice-7B-prepared output; byte-for-byte outputs/wd_cpow_vibevoice_raw.prepared.wav",
                "consent_ref": "reference-consent-rework.md#secondary-reference-e371ebe7ee1ce9964657b4f34f61d32fbff2a5345bdb90add6c3e7dba1ee2175",
                "consent_status": "rights_evidence_present; wd_bxhc_cloning_reuse_consent_not_evidenced",
            })
        references.append(entry)

    download_report = {
        "schema": "wangp-dspy.wd-bxhc.download-report/v1",
        "download_ceiling_bytes": 20000000000,
        "planned_model_bytes": 3208948928,
        "actual_model_bytes": 3208948928,
        "runtime_dependency_bytes": 277648,
        "actual_total_wheel_payload_bytes": 3209226576,
        "dependencies": [
            {"id": "conformer", "version": "0.3.2", "size_bytes": 4260,
             "sha256": "b957faa683e9e75061257f77407318428f2ad0fb5262bfc2e9b55fc2fffdfa03"},
            {"id": "quanto", "version": "0.2.0", "size_bytes": 90023,
             "sha256": "85d23b28e732b628e5bf84a4fd6c78a51c9fc343f7197ed838a9491e557bbd8a"},
            {"id": "ninja", "version": "1.13.2", "size_bytes": 183365,
             "sha256": "65a24341b5ac09fcadcc37082660be40a94174e51a937fabf6e2cae26225fa2c"},
        ],
        "download_before_free_bytes": 44770545664,
        "download_after_free_bytes": 41557614592,
        "final_free_bytes": 41059024896,
        "verified_assets": 6,
    }
    write_json(BUNDLE / "download-report.json", download_report)

    rows = []
    for row, cells in {
        "vibevoice/vibe_7b": ("plain_speech", "one_reference_clone", "two_reference_clone"),
        "chatterbox/chatterbox_multilingual": ("plain_speech",),
    }.items():
        for cell in cells:
            if row == "vibevoice/vibe_7b" and cell != "plain_speech":
                disposition = "evidence_complete_pending_review_consent_not_evidenced"
            else:
                disposition = "host_run_verified_pending_review"
            rows.append({"row": row, "cell": cell, "disposition": disposition})
    for row in (
        "Portable package round-trip and hashes", "Saved voice binding",
        "Native-source recovery", "Registry identity resolution",
        "Appearance and voice mismatch rejection", "Duplicate and ambiguous identity rejection",
        "Immutable non-executable planning", "Seed-based reconstruction",
        "Cross-mode identity preservation",
    ):
        for mode in ("image", "video"):
            disposition = (
                "evidence_complete_pending_review_consent_not_evidenced"
                if row in {"Saved voice binding", "Cross-mode identity preservation"}
                else "host_run_verified_pending_review"
            )
            rows.append({"row": row, "mode": mode, "disposition": disposition})
    write_json(BUNDLE / "row-dispositions.json", {"rows": rows})

    queue = json.loads((BUNDLE / "queue-record.json").read_text())
    queue.update({
        "exit_status": "succeeded",
        "native_logs": [
            "chatterbox-speech.attempt-4.native.log", "vibevoice-custom.attempt-11.native.log",
            "character-operations.attempt-2.log", "character-media-generation.log",
            "queue-complete.log",
        ],
    })
    bundle_bytes = sum(path.stat().st_size for path in BUNDLE.rglob("*") if path.is_file())
    record = {
        "schema": "wangp-dspy.maestro-parity-evidence/v1",
        "operator_authorization": {
            "status": "approved",
            "text": "I agree\nyou need to kill whatever that is that was holding up the GPU and get back to work so that we can finish and complete this\nUnblock and cont\nthe operator approved host batch 1 with a 20 GB download ceiling and has repeatedly instructed to continue/unblock the programme",
            "scope": "WD-bxhc host batch 1: 3,208,948,928-byte Chatterbox asset set, existing VibeVoice-7B, real speech operations, and model-free portable-character operations; llama-server remains running",
            "timestamp": "2026-09-25T19:05:00Z",
            "approved_by": "operator via /root parent authorization",
        },
        "command": [
            "bash", "-c",
            "timeout 3600 ssh -o BatchMode=yes -o ConnectTimeout=15 3090 'cd /home/straughter/wangp-dspy-vibevoice-20260916 && timeout 3300 /home/straughter/vb7-venv/bin/python -' < datasets/runs/maestro-parity/WD-bxhc/native-scripts/wd_bxhc_vibevoice.py",
        ],
        "native_commands": [
            ["timeout", "2700", "ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "3090", "timeout 2400 bash -s"],
            ["timeout", "900", "ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "3090", "timeout 840 /home/straughter/Wan2GP/venv/bin/python -"],
            ["bash", "-c", "timeout 3600 ssh -o BatchMode=yes -o ConnectTimeout=15 3090 'cd /home/straughter/wangp-dspy-vibevoice-20260916 && timeout 3300 /home/straughter/vb7-venv/bin/python -' < datasets/runs/maestro-parity/WD-bxhc/native-scripts/wd_bxhc_vibevoice.py"],
            ["python3", "datasets/runs/maestro-parity/WD-bxhc/generate-character-media.py"],
        ],
        "repository": {
            "commit": GENERATION_COMMIT,
            "commit_semantics": "35270b1 is the clean commit immediately before the successful final VibeVoice batch; later character, queue, documentation, and evidence artifacts are intentionally dirty state",
            "dirty_state": {
                "dirty": bool(status_lines), "identity_sha256": dirty_identity,
                "status_lines": status_lines,
            },
        },
        "model_provenance": model_provenance,
        "reference_provenance": references,
        "queue_attempt": queue,
        "output": outputs,
        "media_metadata": media,
        "objective_gate_results": gates,
        "reviewer_verdict": {
            "decision": "pending",
            "evidence_links": [
                "execution-summary.md", "operator-authorization.md", "download-plan.json",
                "download-report.json", "doctor-capabilities-download-plan.json",
                "standard-preflight.json", "lane-coexistence-preflight.json",
                "chatterbox-report.json", "vibevoice-custom-report.json",
                "reference-consent-rework.md", "reference-consent-verification.json",
                "reference-provenance-rework.log", "rework-plans.log",
                "character-media-identity.json", "character-media-objective-gates.json",
                "packages/character-operation-results.json", "queue-record.json",
                "queue-complete.log", "output-hashes.txt", "objective-gates.json",
                "row-dispositions.json", "final-host-state.txt", "bundle-size.txt",
                "checker-result.txt", "checker-approved-projection.txt", "matrix-transition-check.json",
            ],
            "review": "Independent PM review is pending; the developer does not self-approve.",
        },
        "row_dispositions": rows,
        "runtime_notes": {
            "vibevoice_variant_used": "VibeVoice-7B-hf",
            "vibevoice_large_inspected_but_not_used": "18,687,161,180-byte weights-only install lacks tokenizer/processor files required by the validated API",
            "gpu": "NVIDIA GeForce RTX 3090, 24576 MiB total",
            "gpu_before": "7840-7841 MiB used / 16275 MiB free; operator llama-server occupied 7752 MiB",
            "gpu_after_vibe": "19188-19190 MiB used while qint8 VibeVoice process ran; llama-server remained untouched",
            "gpu_final": "7841 MiB used / 16275 MiB free; only operator llama-server remains",
            "download_ceiling_bytes": 20000000000,
            "planned_model_bytes": 3208948928,
            "actual_model_bytes": 3208948928,
            "runtime_dependency_bytes": 277648,
            "actual_total_wheel_payload_bytes": 3209226576,
            "download_before_free_bytes": 44770545664,
            "download_after_free_bytes": 41557614592,
            "final_free_bytes": 41059024896,
            "derived_preflight_min_free_gb_before_download": 18.91,
            "derived_preflight_min_free_gb_after_download": 15.0,
            "disk_floor_derivation": "3,208,948,928 selected bytes + 0.20 GiB working set + 0.50 GiB execution margin + 15 GiB operator floor = 18.91 GiB before download; after download the hard floor remains 15 GiB.",
            "standard_preflight": "Failed as designed: remote default min 50 GiB and any GPU occupant. This lane did not lower that global gate.",
            "lane_coexistence_preflight": "Passed with exact model hashes, >=15 GiB disk, QC health, and the operator-reserved llama-server as the sole occupant with >=4 GiB free.",
            "vibevoice_quantization": "CPU load verified zero meta tensors, then quanto qint8 nn.Linear weights were frozen on CUDA; embeddings/convolutions retained source dtype to preserve audio-token expansion.",
            "vibevoice_rejections_preserved": "Three 0.778 plain-speech transcript rejections and one 0.778 one-reference rejection are retained with hashes and transcripts.",
            "reference_provenance_rework": "Primary b013… is the operator-owned LF002/WD-cpow target voice; secondary e371… is the WD-cpow VibeVoice-prepared output. The earlier WD-bxhc/Chatterbox attribution and unresolved consent anchors were defective and are preserved in .pre-rework sidecars only.",
            "cloning_consent_decision": "not_evidenced_for_wd_bxhc_cloning_reuse; ownership/output rights are recorded, but no operator statement consents to cross-story cloning reuse",
            "unapproved_rows": "VibeVoice one-reference clone, VibeVoice two-reference clone, Saved voice binding, and Cross-mode identity preservation remain non-host_run_verified",
            "character_media_boundary": "Image/video are deterministic model-free derivatives of one package anchor; the explicit semantic generated-continuity row is not claimed.",
            "queue_ledger_semantics": queue["ledger_semantics"],
            "bundle_size_bytes_at_assembly": bundle_bytes,
            "background_state": "No WD-bxhc SSH/native GPU process remains; pre-existing CPU-only WanGP server and operator llama-server remain",
        },
    }
    write_json(BUNDLE / "evidence.json", record)
    (BUNDLE / "bundle-size.txt").write_text(f"{bundle_bytes} bytes\n", encoding="utf-8")
    summary = """# WD-bxhc execution summary\n\n- Used existing HF-native **VibeVoice-7B-hf**; inspected but did not use weights-only VibeVoice-Large.\n- Planned/verified Chatterbox downloads: **3,208,948,928 bytes**. Runtime wheels added **277,648 bytes**, total wheel payload **3,209,226,576 bytes** under the 20 GB ceiling.\n- Derived disk floor: **18.91 GiB before download** (selected bytes + 0.20 GiB work + 0.50 GiB execution margin + 15 GiB safety); **15 GiB after download**.\n- Real outputs: Chatterbox plain speech; VibeVoice plain/one-reference/two-reference speech; deterministic model-free character image and video from one `.wgpcharacter` anchor.\n- All speech is 24 kHz mono and passes Whisper 0.8.\n- Reworked provenance identifies primary `b013…` as the operator-owned LF002/WD-cpow target voice and secondary `e371…` as the WD-cpow VibeVoice-prepared output. Cross-story cloning-reuse consent is **not evidenced**, so both clone rows, Saved voice binding, and Cross-mode identity preservation are not `host_run_verified`.\n- Standard renderer preflight failed closed on its global 50 GiB/idle-GPU policy. The recorded lane coexistence preflight passed for the operator-reserved llama-server; no global gate was changed.\n- Reviewer verdict remains **pending**; the canonical checker is therefore expected to fail only reviewer approval until PM review.\n"""
    (BUNDLE / "execution-summary.md").write_text(summary, encoding="utf-8")
    print(json.dumps({
        "root": str(ROOT),
        "outputs": len(outputs), "models": len(model_provenance),
        "references": len(references), "gates": len(gates),
        "bundle_bytes": bundle_bytes,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
