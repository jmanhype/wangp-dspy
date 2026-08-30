"""WD-a1d9/S3 — typed audio_manifest.json sidecar for Ref2VA
audio-bearing jobs. Spec: docs/specs/s3-audio-manifest-qc.md.

Code + tests only — NO GPU/render/ffmpeg execution. The manifest is a
REQUIRED sidecar: readback of a render without it is a typed failure
(safe policy for NEW audio-bearing Ref2VA jobs; legacy non-audio H3
is untouched — this module is only consulted by the Ref2VA lane).

Qwen ruling honored: the payload hash covers ONLY the sanctioned audio
payload block (audio_guide / audio_provenance / audio_policy /
audio_qc) — never the ``extra``-adjacent keys like image_refs — and is
canonicalized (sorted keys) so key order cannot change it.
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

__all__ = [
    "AudioManifestError", "AudioManifest", "SIDE_SUFFIX",
    "AUDIO_PAYLOAD_KEYS",
]

MANIFEST_VERSION = 1
SIDE_SUFFIX = ".audio_manifest.json"
AUDIO_PAYLOAD_KEYS = ("audio_guide", "audio_provenance",
                      "audio_policy", "audio_qc")


class AudioManifestError(ValueError):
    """Typed manifest failure. Messages name the offending field."""


@dataclass(frozen=True)
class AudioManifest:
    version: int
    render_output: str
    payload: dict           # the four sanctioned audio payload blocks
    audio_payload_hash: str

    @classmethod
    def from_settings_doc(cls, settings_doc: dict, *,
                          render_output: str = "") -> "AudioManifest":
        """Build a manifest from a Ref2VA settings doc. Audio-bearing
        jobs (audio_prompt_type=='A') MUST carry the full audio payload
        — missing blocks are typed rejections."""
        missing = [k for k in AUDIO_PAYLOAD_KEYS if k not in settings_doc]
        if missing:
            raise AudioManifestError(
                "audio_manifest: settings doc for an audio-bearing "
                f"Ref2VA job is missing audio payload keys: {missing}")
        payload = {k: settings_doc[k] for k in AUDIO_PAYLOAD_KEYS}
        return cls(
            version=MANIFEST_VERSION,
            render_output=str(render_output),
            payload=payload,
            audio_payload_hash=_hash_payload(payload))

    def sidecar_path(self) -> str:
        base = self.render_output
        for suf in (".mp4", ".mov", ".mkv", ".webm"):
            if base.endswith(suf):
                return base[: -len(suf)] + SIDE_SUFFIX
        return base + SIDE_SUFFIX

    def write_sidecar(self) -> str:
        path = self.sidecar_path()
        doc = {
            "version": self.version,
            "render_output": self.render_output,
            "audio_payload": self.payload,
            "audio_payload_hash": self.audio_payload_hash,
        }
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=2, sort_keys=True)
        return path

    @classmethod
    def read_sidecar(cls, path) -> "AudioManifest":
        """REQUIRED readback gate: a missing sidecar is a typed
        failure for audio-bearing jobs (safe policy)."""
        p = str(path)
        if not os.path.isfile(p):
            raise AudioManifestError(
                "audio_manifest: REQUIRED sidecar missing — audio-"
                f"bearing Ref2VA renders must ship {p}")
        with open(p, encoding="utf-8") as fh:
            doc = json.load(fh)
        payload = doc.get("audio_payload")
        if payload is None:
            raise AudioManifestError(
                "audio_manifest: sidecar has no audio_payload block")
        m = cls(version=int(doc.get("version", 0)),
                render_output=str(doc.get("render_output", "")),
                payload=payload,
                audio_payload_hash=str(doc.get("audio_payload_hash", "")))
        expect = _hash_payload(m.payload)
        if m.audio_payload_hash != expect:
            raise AudioManifestError(
                "audio_manifest: payload hash mismatch on readback "
                f"(stored {m.audio_payload_hash!r} != {expect!r})")
        return m

    @classmethod
    def for_render(cls, render_output: str) -> "AudioManifest":
        """Locate + read the sidecar for a render output path."""
        base = str(render_output)
        for suf in (".mp4", ".mov", ".mkv", ".webm"):
            if base.endswith(suf):
                base = base[: -len(suf)] + SIDE_SUFFIX
                break
        else:
            base = base + SIDE_SUFFIX
        return cls.read_sidecar(base)


def _hash_payload(payload: dict) -> str:
    """Canonical (sorted-key) sha256 over ONLY the sanctioned audio
    payload block — Qwen ruling: hashing must exclude extra keys."""
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()
