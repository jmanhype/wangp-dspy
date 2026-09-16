"""Pinned LF002 golden-artifact gate.

This canary verifies the operator-accepted Archive of Rain two-cut control.
It performs no generation, audio replacement, queue mutation, or verdict
inference. A hash match proves artifact preservation only; the operator's
audiovisual “perfect” verdict remains the source acceptance record.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from fractions import Fraction
from pathlib import Path


class LF002CanaryError(ValueError):
    pass


LF002_RECIPE_VERSION = "lf002-archive-of-rain-20260916-seed905-native-v1"
LF002_GOLDEN_SHA256 = {
    "cut1": "64916cd42d40e0f81a51dd750d2134d194dd59c8318bf3d6f75fbc8649d97770",
    "cut2": "c3131c041a2b586e15ab19280a0ede64aa294b2e6bdc9f26fde0e353fbc29ceb",
    "pair": "ef4c3944ef728862119b065838ac1ec5f1e1452d1f8b4fdbb0d683f06272a527",
    "chain": "1c1d86b0108c31a8318d428fcf626d3af6ffd0c0ba6269a8a69859eca6fb53de",
}


def _probe(path: Path) -> list[dict]:
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-count_frames", "-show_entries",
         "stream=codec_type,nb_read_frames,start_time,r_frame_rate,duration",
         "-of", "json", str(path)],
        capture_output=True, text=True, timeout=60, check=False)
    if proc.returncode:
        raise LF002CanaryError(f"ffprobe failed: {proc.stderr[-240:]}")
    return json.loads(proc.stdout)["streams"]


def verify_lf002_canary(*, cut1: str, cut2: str, pair: str, chain: str,
                        report_path: str) -> dict:
    supplied = dict(cut1=cut1, cut2=cut2, pair=pair, chain=chain)
    paths = {key: Path(value).resolve() for key, value in supplied.items()}
    report = Path(report_path).resolve()
    if report in paths.values():
        raise LF002CanaryError("canary report must not overwrite an input")

    artifacts: dict[str, dict] = {}
    errors: list[str] = []
    for key, path in paths.items():
        try:
            data = path.read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            artifacts[key] = {
                "path": str(supplied[key]),
                "sha256": digest,
                "bytes": len(data),
            }
            if digest != LF002_GOLDEN_SHA256[key]:
                errors.append(f"{key}: LF002 golden SHA256 mismatch")
        except OSError as exc:
            errors.append(f"{key}: unreadable artifact: {exc}")

    if not errors:
        for key in ("cut1", "cut2", "pair"):
            try:
                streams = _probe(paths[key])
                artifacts[key]["streams"] = streams
                video = [s for s in streams if s.get("codec_type") == "video"]
                audio = [s for s in streams if s.get("codec_type") == "audio"]
                if len(video) != 1 or len(audio) != 1:
                    raise ValueError("one video and one audio stream required")
                expected_frames = 112 if key == "pair" else 56
                if int(video[0]["nb_read_frames"]) != expected_frames:
                    raise ValueError(
                        f"expected {expected_frames} frames, got "
                        f"{video[0]['nb_read_frames']}")
                if Fraction(video[0]["r_frame_rate"]) != 24:
                    raise ValueError("expected 24 fps")
                for stream in (video[0], audio[0]):
                    start = float(stream.get("start_time", "nan"))
                    if not math.isfinite(start) or abs(start) > 0.000001:
                        raise ValueError("A/V start timestamp must be zero")
            except (OSError, ValueError, KeyError,
                    subprocess.SubprocessError) as exc:
                errors.append(f"{key}: {exc}")

    result = {
        "schema": "wangp-dspy.lf002-golden-canary/v1",
        "recipe_version": LF002_RECIPE_VERSION,
        "passed": not errors,
        "artifacts": artifacts,
        "errors": errors,
        "operator_verdict": "perfect",
        "scope": (
            "Exact operator-accepted LF002 two-cut native artifacts and chain "
            "seed on the pinned environment; not a universal new-premise "
            "quality claim."
        ),
    }
    try:
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(
            json.dumps(result, indent=2) + "\n", encoding="utf-8")
    except OSError as exc:
        raise LF002CanaryError(
            f"unable to write LF002 canary report {report}: {exc}") from exc
    if errors:
        raise LF002CanaryError("; ".join(errors))
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("cut1", "cut2", "pair", "chain", "report"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args(argv)
    try:
        result = verify_lf002_canary(
            cut1=args.cut1, cut2=args.cut2, pair=args.pair,
            chain=args.chain, report_path=args.report)
    except LF002CanaryError as exc:
        print(f"LF002 golden canary refused: {exc}")
        return 2
    print(json.dumps({
        "passed": result["passed"],
        "report_path": str(Path(args.report).resolve()),
        "sha256": {key: value["sha256"]
                   for key, value in result["artifacts"].items()},
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
