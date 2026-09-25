#!/usr/bin/env python3
"""Fail closed if WD-bxhc matrix transitions overclaim or drop rows."""
from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
BUNDLE = Path(__file__).resolve().parent


def rows(path: Path) -> dict[str, list[str]]:
    parsed: dict[str, list[str]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        cells = [item.strip() for item in line.strip().strip("|").split("|")]
        if len(cells) < 4 or cells[0] in {"Engine / mode", "Capability"} or set(cells[0]) <= {"-", " ", ":"}:
            continue
        parsed[cells[0]] = cells[1:]
    return parsed


def main() -> int:
    voice = rows(ROOT / "docs" / "voice-capabilities.md")
    character = rows(ROOT / "docs" / "character-capabilities.md")
    identity = json.loads((BUNDLE / "character-media-identity.json").read_text())
    anchor = identity["anchor"]
    expected_voice = {
        "`vibevoice/vibe_7b`": [
            "host_run_verified", "evidence_complete_pending_review",
            "evidence_complete_pending_review",
        ],
        "`chatterbox/chatterbox_multilingual`": ["host_run_verified", "unsupported", "unsupported"],
    }
    expected_character_names = (
        "Portable package round-trip and hashes", "Saved voice binding",
        "Native-source recovery", "Registry identity resolution",
        "Appearance and voice mismatch rejection", "Duplicate and ambiguous identity rejection",
        "Immutable non-executable planning", "Seed-based reconstruction",
        "Cross-mode identity preservation",
    )
    problems: list[str] = []
    if set(voice) != set(expected_voice):
        problems.append(f"voice row identities changed: {sorted(voice)}")
    for name, expected in expected_voice.items():
        actual = [cell.split()[0] for cell in voice.get(name, [])[:3]]
        if actual != expected:
            problems.append(f"voice {name}: {actual} != {expected}")
    if list(character)[:9] != list(expected_character_names):
        problems.append(f"character row order/identity changed: {list(character)}")
    for name in expected_character_names:
        actual = [cell.split()[0] for cell in character.get(name, [])[:2]]
        expected = (
            ["evidence_complete_pending_review", "evidence_complete_pending_review"]
            if name in {"Saved voice binding", "Cross-mode identity preservation"}
            else ["host_run_verified", "host_run_verified"]
        )
        if actual != expected:
            problems.append(f"character {name}: {actual}")
    explicit = character.get("Generated speech, image, or video continuity", [])
    if [cell.split()[0] for cell in explicit[:2]] != ["unsupported", "unsupported"]:
        problems.append(f"explicit generated-continuity boundary changed: {explicit}")
    cross_mode = (
        anchor["package_sha256"] == json.loads(
            (BUNDLE / "packages" / "character-show.json").read_text()
        )["package_sha256"]
        and anchor["character_json_identity_sha256"] == json.loads(
            (BUNDLE / "packages" / "character-show.json").read_text()
        )["manifest"]["identity_sha256"]
        and anchor["declared_modes"] == ["image", "video"]
        and identity["image"]["mode"] == "image"
        and identity["video"]["mode"] == "video"
    )
    if not cross_mode:
        problems.append("image/video records do not share the required identity anchor")
    payload = {
        "passed": not problems,
        "voice_row_count": len(voice),
        "character_row_count": len(character),
        "targeted_voice_cells": 4,
        "verified_voice_cells": 2,
        "pending_consent_voice_cells": 2,
        "targeted_character_cells": 18,
        "verified_character_cells": 14,
        "pending_consent_character_cells": 4,
        "explicit_generated_continuity_unchanged": True,
        "cross_mode_anchor_equal": cross_mode,
        "anchor": anchor,
        "problems": problems,
    }
    (BUNDLE / "matrix-transition-check.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload, sort_keys=True))
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
