#!/usr/bin/env python3
"""Fail-closed replay verification for the approved LF004 56-frame plan."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from predict.content_brief import load_content_brief  # noqa: E402

BASE = ROOT / "datasets/content_briefs/lf004-operator-dogfood-56f"
SOURCE_BASE = BASE.parent / "lf004-operator-dogfood"
APPROVED_BRIEF_HASH = "sha256:67202d3597affeab4e5edcf15a1acef2f5e88ed00950ce17ff3012f5bb0472cd"
APPROVED_BRIEF_SHA256 = "bc213a4a524390f2afcb913e120f8cf87276db1dc04f3f1934b9c69871cec767"
APPROVED_PLAN_SHA256 = "d0650b2e6b9d6fdbb1807ef82622c9c9a17888a0d4896e0c245feab146013943"
APPROVED_LEDGER_SHA256 = "1ca179cf04fde53ccad4e8b9bf046fc4e121090bd29f7133fa9ad821ba61cbf7"
DURATION_S = 56.0 / 24.0


class VerificationError(AssertionError):
    """Raised when approved LF004 inputs or replay outputs do not match."""


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha(plan: dict[str, Any]) -> str:
    """Hash path-independent plan semantics using the accepted algorithm."""
    roots = {str(ROOT)}
    recorded_root = plan.get("repository", {}).get("repo_root")
    if isinstance(recorded_root, str):
        roots.add(recorded_root)

    def clean(value: Any) -> Any:
        if isinstance(value, dict):
            return {key: clean(item) for key, item in value.items() if key not in {"input", "repository"}}
        if isinstance(value, list):
            return [clean(item) for item in value]
        if isinstance(value, str):
            for root in sorted(roots, key=len, reverse=True):
                prefix = f"{root.rstrip('/')}/"
                if value.startswith(prefix):
                    return value[len(prefix):]
        return value

    encoded = json.dumps(clean(plan), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise VerificationError(message)


def verify_policy(plan: dict[str, Any]) -> None:
    clips = plan.get("clips")
    summary = plan.get("summary", {})
    require(isinstance(clips, list) and len(clips) == 4, "plan must contain exactly four clips")
    require(summary.get("planned_duration_s") == 9.332, "planned duration must be 9.332 seconds")
    for clip in clips:
        require(clip.get("frames") == 56, "every clip must request 56 frames")
        require(clip.get("audio_length_frames") == 56, "every audio guide must measure 56 frames")
        require(abs(float(clip.get("guide_duration_s", 0.0)) - DURATION_S) < 0.001, "guide duration must equal 56/24 seconds")
        require(abs(float(clip.get("shot_duration_s", 0.0)) - DURATION_S) < 0.001, "shot duration must equal 56/24 seconds")


def replay_and_verify(count: int = 2) -> list[str]:
    outputs: list[str] = []
    with tempfile.TemporaryDirectory(prefix="lf004-56f-replay-") as temporary:
        for index in range(count):
            output = Path(temporary) / f"plan-{index}.json"
            run_dir = Path(temporary) / f"run-{index}"
            command = [sys.executable, str(ROOT / "scripts/run_content_brief.py"), "--brief", str(BASE / "brief.json"), "--plates", str(SOURCE_BASE / "plates"), "--output", str(output), "--run-dir", str(run_dir)]
            subprocess.run(command, check=True, stdout=subprocess.DEVNULL)
            replay = json.loads(output.read_text(encoding="utf-8"))
            outputs.append(canonical_sha(replay))
            verify_policy(replay)
            require(not (run_dir / "jobs.db").exists(), "dry replay emitted a queue database")
    return outputs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--canonical-sha", required=True, help="operator-approved canonical plan SHA-256")
    args = parser.parse_args(argv)

    require(args.canonical_sha == "620f2ba44beb7d0bc920772c136aa0ce6f76df89acd286647c23e5a7c8015eb8", "unexpected operator hash argument")
    require(not (BASE / "run/jobs.db").exists(), "no-GPU planning directory contains jobs.db")
    require(sha(BASE / "brief.json") == APPROVED_BRIEF_SHA256, "raw corrected brief hash changed")
    brief = load_content_brief(BASE / "brief.json")
    require(brief.brief_hash == APPROVED_BRIEF_HASH, "semantic corrected brief hash changed")
    require(brief.durations_s == (DURATION_S,) * 4, "brief duration policy changed")

    guides = json.loads((SOURCE_BASE / "run/audio-guides.json").read_text(encoding="utf-8"))
    for name, item in guides["plates"].items():
        require(sha(SOURCE_BASE / "plates" / item["staged"]) == item["sha256"], f"plate hash changed: {name}")
    for turn, dialogue in zip(guides["turns"], brief.mapping()["dialogue"], strict=True):
        guide = (ROOT / turn["audio"]).resolve()
        require(guide.is_file(), f"guide is absent: {turn['audio']}")
        require(sha(guide) == turn["sha256"], f"guide hash changed: {turn['audio']}")
        require(turn["text"] == dialogue["text"], "guide/dialogue order changed")
        require(turn["speaker"] == dialogue["speaker"], "guide/dialogue speaker changed")

    plan = json.loads((BASE / "plan.json").read_text(encoding="utf-8"))
    require(sha(BASE / "plan.json") == APPROVED_PLAN_SHA256, "raw committed plan hash changed")
    require(plan.get("brief_hash") == brief.brief_hash, "plan semantic brief hash changed")
    verify_policy(plan)
    require(canonical_sha(plan) == args.canonical_sha, "canonical committed plan hash changed")

    ledger = BASE / "run/run_ledger.json"
    require(sha(ledger) == APPROVED_LEDGER_SHA256, "no-GPU run ledger hash changed")
    ledger_data = json.loads(ledger.read_text(encoding="utf-8"))
    require(ledger_data.get("schema_version") == 1, "run ledger schema changed")
    require(ledger_data.get("status") == "planned", "run ledger is not planned")
    require(ledger_data.get("clip_count") == 4 and ledger_data.get("dry_run") is True, "run ledger shape changed")

    rejected = copy.deepcopy(plan)
    for clip in rejected["clips"]:
        clip["frames"] = 107
        clip["audio_length_frames"] = 107
        clip["guide_duration_s"] = 4.458333
        clip["shot_duration_s"] = 4.458333
    rejected["summary"]["planned_duration_s"] = 17.832
    rejected_correctly = False
    try:
        verify_policy(rejected)
    except VerificationError:
        rejected_correctly = True
    require(rejected_correctly, "verifier failed to reject the retired 107-frame shape")

    replay_hashes = replay_and_verify(2)
    require(replay_hashes == [args.canonical_sha] * 2, "independent replay hashes differ")
    print(json.dumps({
        "brief_hash": brief.brief_hash,
        "brief_sha256": sha(BASE / "brief.json"),
        "plan_sha256": sha(BASE / "plan.json"),
        "canonical_plan_sha256": canonical_sha(plan),
        "run_ledger_sha256": sha(ledger),
        "guide_sha256": [turn["sha256"] for turn in guides["turns"]],
        "replay": replay_hashes,
        "status": "verified",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
