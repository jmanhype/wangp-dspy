#!/usr/bin/env python3
"""Run real WD-dmf2 Whisper, local vision, and SyncNet evidence gates."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Sequence

from predict.continuation_lane import transcript_match_score
from qc.audio_critic.local_qwen_vision_judge import LocalQwenVisionJudge
from qc.audio_critic.syncnet_runner import run as run_syncnet
from qc.audio_critic.vision_judge import (
    VisionJudgeError, run_vision_judge,
)
from qc.audio_critic.whisper_cli import whisper_transcriber


class LocalHost:
    def run_probe(self, argv: Sequence[str], timeout: float):
        result = subprocess.run(
            list(argv), text=True, capture_output=True, check=False,
            timeout=timeout,
        )
        return result.returncode, result.stdout, result.stderr

    def write_text(self, path: str, content: str) -> str:
        destination = Path(path)
        destination.write_text(content, encoding="utf-8")
        return str(destination)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def whisper(path: Path, intended: str, output_root: Path, label: str) -> dict:
    isolated = output_root / label
    isolated.mkdir(parents=True, exist_ok=True)

    def runner(argv: Sequence[str]):
        return subprocess.run(
            list(argv), text=True, capture_output=True, check=False,
            timeout=900,
        )

    try:
        transcript = whisper_transcriber(
            str(path), runner=runner, model="small", output_dir=str(isolated)
        )
        score = transcript_match_score(transcript, intended)
        return {
            "video_path": str(path),
            "intended_text": intended,
            "transcript": transcript,
            "score": round(score, 3),
            "pass_bar": 0.6,
            "passed": score >= 0.6,
            "model": "whisper-small",
            "model_sha256": sha256(
                Path("/home/straughter/.cache/whisper/small.pt")
            ),
        }
    except Exception as exc:
        return {
            "video_path": str(path),
            "intended_text": intended,
            "passed": False,
            "error": f"{type(exc).__name__}: {exc}",
            "model": "whisper-small",
        }


def vision_and_sync(video: Path, speaker: str, action: Path | str,
                    output_root: Path, label: str,
                    reference: Path | None = None) -> dict:
    result = {
        "video_path": str(video),
        "expected_speaker": speaker,
        "expected_action": str(action),
        "identity_vision": None,
        "mouth_box_consensus": None,
        "syncnet_av": None,
    }
    judge = LocalQwenVisionJudge(
        host=LocalHost(),
        endpoint="http://127.0.0.1:8000/v1/chat/completions",
        model="q",
        timeout_s=180.0,
        max_tokens=1024,
    )
    raw = None
    try:
        kwargs = {
            "video_path": str(video),
            "expected_speaker": speaker,
            "expected_action": str(action),
        }
        if reference is not None:
            kwargs["reference_image_path"] = str(reference)
        raw = judge(**kwargs)
        (output_root / f"{label}.local-qwen-raw.json").write_text(
            json.dumps(raw, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        evidence = run_vision_judge(
            str(video), expected_speaker=speaker, expected_action=str(action),
            judge=lambda **_: raw, pass_bar=0.7,
            reference_image_path=str(reference) if reference is not None else None,
        ).to_dict()
        result["identity_vision"] = {
            "passed": evidence["passed"],
            "speaker_attribution": evidence["speaker_attribution"],
            "action_match": evidence["action_match"],
            "pass_bar": evidence["pass_bar"],
            "raw_response_sha256": hashlib.sha256(
                str(raw.get("raw_response", "")).encode()
            ).hexdigest(),
        }
        result["mouth_box_consensus"] = {
            "passed": evidence["passed"],
            "speaker_mouth_bboxes": evidence["speaker_mouth_bboxes"],
            "center_spread": evidence["speaker_mouth_center_spread"],
        }
        bbox = evidence["speaker_mouth_bbox"]
    except VisionJudgeError as exc:
        result["identity_vision"] = {
            "passed": False,
            "error": str(exc),
            "scores": dict(exc.scores),
        }
        result["mouth_box_consensus"] = {
            "passed": False,
            "error": "vision gate rejected before consensus acceptance",
        }
        if isinstance(raw, dict):
            boxes = raw.get("speaker_mouth_bboxes")
            if isinstance(boxes, list) and len(boxes) == 3:
                x, y, width, height = (float(value) for value in boxes[0])
                center_x = x + width / 2.0
                center_y = y + height / 2.0
                bbox = [
                    max(0.0, center_x - 0.04),
                    max(0.0, center_y - 0.02), 0.08, 0.04,
                ]
            else:
                bbox = None
        else:
            bbox = None
    except Exception as exc:
        result["identity_vision"] = {
            "passed": False,
            "error": f"{type(exc).__name__}: {exc}",
        }
        bbox = None

    if bbox is None:
        result["syncnet_av"] = {
            "passed": False,
            "error": "not run: no speaker mouth bbox from the vision localizer",
        }
        return result
    try:
        evidence = run_syncnet(
            video, bbox, "/home/straughter/models/syncnet_v2/syncnet_v2.model",
            video_sha256=sha256(video),
        )
        result["syncnet_av"] = evidence
    except Exception as exc:
        result["syncnet_av"] = {
            "passed": False,
            "bbox": list(bbox),
            "error": f"{type(exc).__name__}: {exc}",
        }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("lane_root", type=Path)
    arguments = parser.parse_args()
    root = arguments.lane_root.resolve()
    qc_root = root / "qc"
    qc_root.mkdir(parents=True, exist_ok=True)
    outputs = root / "outputs"

    whisper_targets = [
        (
            outputs / "clips/music_video/clip0001.mp4",
            "[Instrumental]",
            "music_video_clip1_whisper",
        ),
        (
            outputs / "clips/screenplay/clip0001.mp4",
            "The portable witness speaks plainly without claiming another voice.",
            "screenplay_clip1_whisper",
        ),
        (
            outputs / "clips/screenplay/clip0002.mp4",
            "This is the last rain we have.",
            "screenplay_clip2_whisper",
        ),
    ]
    whisper_results = [
        whisper(path, intended, qc_root, label)
        for path, intended, label in whisper_targets
    ]

    vision_targets = [
        (
            outputs / "clips/audio/clip0001.mp4",
            "elder woman with white hair holding a bowl",
            "an elder offers a bowl beside a restrained man in a firelit cave",
            None,
            "audio_clip1_vision",
        ),
        (
            outputs / "clips/screenplay/clip0001.mp4",
            "young astronomer in a dark star-ember jacket",
            "the witness speaks plainly in an observatory",
            root / "inputs/wd_bxhc_character_first_frame.png",
            "screenplay_clip1_vision",
        ),
        (
            outputs / "clips/screenplay/clip0002.mp4",
            "elder woman with white hair holding a bowl",
            "Orin says this is the last rain we have",
            None,
            "screenplay_clip2_vision",
        ),
    ]
    vision_results = [
        vision_and_sync(video, speaker, action, qc_root, label, reference)
        for video, speaker, action, reference, label in vision_targets
    ]
    auto_passed = all(
        item.get("passed") is True
        for results in (whisper_results, vision_results)
        for item in results
    ) and all(
        item["syncnet_av"].get("passed") is True for item in vision_results
    )
    payload = {
        "schema_version": "wangp-dspy.director-qc-evidence/v1",
        "whisper_gates": whisper_results,
        "vision_gates": vision_results,
        "auto_review": {
            "mandatory_gates": [
                "whisper_transcript", "identity_vision",
                "mouth_box_consensus", "syncnet_av",
            ],
            "all_passed": auto_passed,
            "bypassed": False,
        },
        "reviewer_verdict": {
            "decision": "pending",
            "reason": "operator/PM review has not been granted",
        },
    }
    destination = root / "director-qc-evidence.json"
    destination.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "path": str(destination),
        "auto_review_all_passed": auto_passed,
        "reviewer_decision": "pending",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
