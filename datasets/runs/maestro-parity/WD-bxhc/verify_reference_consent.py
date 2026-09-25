#!/usr/bin/env python3
"""Fail closed unless corrected reference anchors and hashes resolve exactly."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from rework_reference_provenance import RECORDS


BUNDLE = Path(__file__).resolve().parent
EXPECTED = {
    "inputs/voice-primary-vibe.wav": "b013bad88be5b44609304764aaa6b10afb9f0299d768c8abc48c2d1afd4bed18",
    "inputs/voice-secondary.wav": "e371ebe7ee1ce9964657b4f34f61d32fbff2a5345bdb90add6c3e7dba1ee2175",
}
CONSENT_REFS = {item["consent_ref"] for item in RECORDS.values()}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    markdown = (BUNDLE / "reference-consent-rework.md").read_text(encoding="utf-8")
    headings = re.findall(r"^## ([^\n]+)$", markdown, flags=re.MULTILINE)
    problems: list[str] = []
    checks: dict[str, bool] = {}
    for relative, expected in EXPECTED.items():
        heading = next((item for item in headings if expected in item), None)
        checks[f"{relative}_hash"] = sha256(BUNDLE / relative) == expected
        checks[f"{relative}_anchor_exists"] = heading is not None
        if heading is None:
            problems.append(f"missing anchor for {expected}")
        else:
            slug = re.sub(r"[^a-z0-9-]+", "-", heading.lower()).strip("-")
            expected_ref = f"reference-consent-rework.md#{slug}"
            checks[f"{relative}_anchor_slug"] = (
                slug.endswith(expected)
                and f"reference-consent-rework.md#{slug}" in CONSENT_REFS
            )
            if not checks[f"{relative}_anchor_slug"]:
                problems.append(f"anchor slug mismatch: {slug}")
    for sidecar_name in (
        "wd_bxhc_vibevoice_speech.wav.vibevoice.json",
        "wd_bxhc_vibevoice_clone_one.wav.vibevoice.json",
        "wd_bxhc_vibevoice_clone_two.wav.vibevoice.json",
    ):
        payload = json.loads((BUNDLE / "outputs" / sidecar_name).read_text(encoding="utf-8"))
        for reference in payload["references"]:
            expected = EXPECTED.get(str(Path(reference["path"]).name))
            if expected is None and reference["sha256"] in EXPECTED.values():
                expected = reference["sha256"]
            checks[f"{sidecar_name}_{reference['sha256'][:8]}_anchor"] = (
                reference["consent_ref"].startswith("reference-consent-rework.md#")
                and reference["sha256"] in EXPECTED.values()
                and reference["consent_ref"] in CONSENT_REFS
                and reference["consent_status"] == "rights_evidence_present; wd_bxhc_cloning_reuse_consent_not_evidenced"
            )
            if reference["license"].lower().startswith("operator-owned synthetic wd-bxhc"):
                problems.append(f"{sidecar_name}: stale WD-bxhc/Chatterbox licence")
            if "chatterbox" in reference["source"].lower():
                problems.append(f"{sidecar_name}: stale Chatterbox attribution")
    payload = {
        "schema": "wangp-dspy.wd-bxhc.reference-consent-rework/v1",
        "passed": not problems and all(checks.values()),
        "checks": checks,
        "problems": problems,
        "consent_decision": "not_evidenced_for_wd_bxhc_cloning_reuse",
    }
    (BUNDLE / "reference-consent-verification.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload, sort_keys=True))
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
