"""WD-a1d9-followup — S3 audio manifest: serialize the Ref2VA
settings-doc audio payloads into a sidecar audio_manifest.json with a
typed readback validator (fail loud on any mismatch).

Spec: docs/specs/s3-audio-manifest-qc.md (D1).

Qwen ruling (S2 spec): any manifest hashing MUST hash ONLY the
sanctioned audio payload block, never the full settings extra —
audio_payload_hash enforces exactly that (non-audio extra keys are
invisible to the hash).

Zero-model, deterministic: same input bytes -> same manifest bytes
(no timestamps, sorted-key JSON serialization).
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

__all__ = [
    "AUDIO_MANIFEST_KEYS", "AudioManifestError", "build_audio_manifest",
    "audio_payload_hash", "readback_validate", "write_audio_manifest",
    "require_manifest_for_render", "MANIFEST_FILENAME",
]

AUDIO_MANIFEST_KEYS = ("audio_guide", "audio_provenance",
                       "audio_policy", "audio_qc")

MANIFEST_FILENAME = "audio_manifest.json"


class AudioManifestError(ValueError):
    """Typed rejection. Messages name the offending key/condition."""


def build_audio_manifest(settings_doc: dict) -> dict:
    """Extract the sanctioned audio payload block from a Ref2VA
    settings doc. Rejects docs missing any audio payload key — an
    audio-bearing job MUST carry all four."""
    if not isinstance(settings_doc, dict):
        raise AudioManifestError(
            f"settings doc must be a dict, got {type(settings_doc).__name__}")
    missing = [k for k in AUDIO_MANIFEST_KEYS if k not in settings_doc]
    if missing:
        raise AudioManifestError(
            f"settings doc missing audio payload key(s) {missing} — "
            "audio-bearing Ref2VA jobs carry all four")
    return {k: settings_doc[k] for k in AUDIO_MANIFEST_KEYS}


def _canonical_payload_bytes(manifest: dict) -> bytes:
    return json.dumps(manifest, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def audio_payload_hash(settings_doc: dict) -> str:
    """sha256 over ONLY the sanctioned audio payload block. Non-audio
    extra keys (script, image_refs, ...) never influence the hash
    (Qwen ruling: hash the sanctioned block, never full extra)."""
    m = build_audio_manifest(settings_doc)
    return hashlib.sha256(_canonical_payload_bytes(m)).hexdigest()


def readback_validate(manifest: dict, settings_doc: dict) -> bool:
    """Confirm round-trip: the read-back manifest must equal the
    manifest rebuilt from the settings doc, byte-for-byte on the
    canonical form. Fails LOUD (typed) on any mismatch, naming the
    first differing key."""
    expected = build_audio_manifest(settings_doc)
    e_canon = json.loads(_canonical_payload_bytes(expected).decode())
    m_canon = json.loads(_canonical_payload_bytes(manifest).decode())
    for k in AUDIO_MANIFEST_KEYS:
        if m_canon.get(k) != e_canon.get(k):
            raise AudioManifestError(
                f"readback mismatch on {k!r}: manifest has "
                f"{m_canon.get(k)!r}, settings doc has {e_canon.get(k)!r}")
    return True


def write_audio_manifest(settings_doc: dict, render_output: Path) -> Path:
    """Write the sidecar manifest next to the render output.
    Deterministic serialization (sorted keys, fixed separators) —
    same input produces byte-identical files."""
    m = build_audio_manifest(settings_doc)
    path = Path(render_output).parent / MANIFEST_FILENAME
    path.write_text(json.dumps(m, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")
    return path


def require_manifest_for_render(render_output: Path) -> dict:
    """Hard gate at readback: an audio-bearing Ref2VA render REQUIRES
    the sidecar manifest. Missing manifest = typed rejection."""
    path = Path(render_output).parent / MANIFEST_FILENAME
    if not path.is_file():
        raise AudioManifestError(
            f"manifest required but missing: {path} — audio-bearing "
            "Ref2VA renders must ship an audio_manifest.json sidecar")
    return json.loads(path.read_text(encoding="utf-8"))
