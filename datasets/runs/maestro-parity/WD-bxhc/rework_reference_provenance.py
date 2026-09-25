#!/usr/bin/env python3
"""Correct final WD-bxhc reference metadata without changing media bytes."""
from __future__ import annotations

import json
import zipfile
from pathlib import Path


BUNDLE = Path(__file__).resolve().parent
RECORDS = {
    "b013bad88be5b44609304764aaa6b10afb9f0299d768c8abc48c2d1afd4bed18": {
        "source": "Operator-owned LF002 Orin voice guide; byte-for-byte WD-cpow inputs/target-voice.wav",
        "license": "Operator-owned evaluation asset; no redistribution",
        "consent_ref": "reference-consent-rework.md#primary-reference-b013bad88be5b44609304764aaa6b10afb9f0299d768c8abc48c2d1afd4bed18",
        "consent_status": "rights_evidence_present; wd_bxhc_cloning_reuse_consent_not_evidenced",
    },
    "e371ebe7ee1ce9964657b4f34f61d32fbff2a5345bdb90add6c3e7dba1ee2175": {
        "source": "WD-cpow VibeVoice-7B-prepared output; byte-for-byte outputs/wd_cpow_vibevoice_raw.prepared.wav",
        "license": "Operator-owned WD-cpow evaluation output; no redistribution",
        "consent_ref": "reference-consent-rework.md#secondary-reference-e371ebe7ee1ce9964657b4f34f61d32fbff2a5345bdb90add6c3e7dba1ee2175",
        "consent_status": "rights_evidence_present; wd_bxhc_cloning_reuse_consent_not_evidenced",
    },
}
SIDECARS = (
    "outputs/wd_bxhc_vibevoice_speech.wav.vibevoice.json",
    "outputs/wd_bxhc_vibevoice_clone_one.wav.vibevoice.json",
    "outputs/wd_bxhc_vibevoice_clone_two.wav.vibevoice.json",
)
REQUESTS = (
    "planning/requests/vibevoice-clone-one.json",
    "planning/requests/vibevoice-clone-two.json",
    "planning/requests/vibevoice-clone-two-alias.json",
)


def correct(reference: dict) -> dict:
    record = RECORDS.get(reference["sha256"])
    if record is None:
        raise RuntimeError(f"unknown reference hash: {reference['sha256']}")
    updated = dict(reference)
    updated.update(record)
    return updated


def rewrite(path: Path, transform) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    backup = path.with_name(path.name + ".pre-rework.json")
    if not backup.exists():
        backup.write_bytes(path.read_bytes())
    transform(payload)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    for relative in SIDECARS:
        rewrite(BUNDLE / relative, lambda payload: payload.update(
            references=[correct(item) for item in payload.get("references", [])],
            provenance_rework="reference-consent-rework.md",
        ))
    for relative in REQUESTS:
        def transform(payload):
            payload["references"] = [
                {key: value for key, value in correct(item).items() if key != "consent_status"}
                for item in payload.get("references", [])
            ]
        if (BUNDLE / relative).exists():
            rewrite(BUNDLE / relative, transform)

    voice_package = BUNDLE / "packages" / "portable-witness.wgpvoice"
    with zipfile.ZipFile(voice_package) as archive:
        manifest = json.loads(archive.read("voice-package.json"))
    manifest["voice"]["references"] = [correct(item) for item in manifest["voice"]["references"]]
    manifest["rework"] = {
        "status": "reference_metadata_corrected_external_only",
        "reason": "package bytes retained to preserve the accepted cross-mode identity anchor; consent remains unevidenced",
        "record": "reference-consent-rework.md",
    }
    destination = BUNDLE / "packages" / "portable-witness.wgpvoice.rework-manifest.json"
    destination.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "corrected_sidecars": len(SIDECARS),
        "corrected_requests": sum((BUNDLE / item).exists() for item in REQUESTS),
        "external_rework_manifest": str(destination.relative_to(BUNDLE)),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
