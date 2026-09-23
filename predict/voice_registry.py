"""Portable, hash-verified character voice packages without audio claims."""
from __future__ import annotations

import json
import re
import zipfile
import hashlib
import wave
from pathlib import Path
from typing import Any, Mapping

from predict.speech_capabilities import (
    SpeechCapabilityError,
    SpeechMode,
    file_sha256,
)

PACKAGE_SCHEMA = "wangp-dspy.character-voice-package/v1"
_CHARACTER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _.-]*$")
_MAX_MEMBER_BYTES = 128 * 1024 * 1024


def _readable(
    path: Path,
    expected: str,
    *,
    code: str,
    label: str,
    duration_s: float | None = None,
) -> bytes:
    if not path.is_file():
        raise SpeechCapabilityError(
            code,
            f"{label} is not readable: {path}",
            "Restore the exact local asset; Wangp will not fetch or repair package bytes.",
        )
    actual = file_sha256(path)
    if actual != expected:
        raise SpeechCapabilityError(
            code,
            f"{label} hash mismatch: expected {expected}, got {actual}",
            "Restore the exact recorded bytes or update authorized provenance.",
            metadata={"expected": expected, "actual": actual},
        )
    if duration_s is not None:
        try:
            with wave.open(str(path), "rb") as audio:
                measured = audio.getnframes() / audio.getframerate()
        except (OSError, ValueError, wave.Error) as exc:
            raise SpeechCapabilityError(
                "SPEECH_REFERENCE_UNUSABLE",
                f"{label} is not readable RIFF/WAV audio: {exc}",
                "Supply a valid authorized WAV reference.",
            ) from exc
        if abs(measured - duration_s) > 0.05:
            raise SpeechCapabilityError(
                "SPEECH_REFERENCE_UNUSABLE",
                f"{label} duration is {measured:.3f}s, not declared {duration_s:.3f}s",
                "Correct the declared duration or supply the exact authorized WAV.",
            )
    return path.read_bytes()


def export_voice_package(
    request: Mapping[str, Any] | object, destination: str | Path
) -> tuple[Path, dict[str, Any]]:
    """Write a deterministic portable package from a validated clone request."""

    if getattr(request, "mode", None) is not SpeechMode.voice_clone:
        raise SpeechCapabilityError(
            "VOICE_PACKAGE_UNSUPPORTED",
            "portable character export requires mode=voice_clone",
            "Use a one- or two-reference cloning request with a character binding.",
            next_command="wgp voice export --request <request> --models <models> --package <package>",
        )
    character = getattr(request, "character", None)
    appearance = getattr(character, "appearance", None)
    if character is None or appearance is None or not request.references:
        raise SpeechCapabilityError(
            "VOICE_PACKAGE_UNSUPPORTED",
            "portable character export requires a character, appearance, and voice references",
            "Bind an appearance asset and at least one authorized WAV reference before export.",
            next_command="wgp voice export --request <request> --models <models> --package <package>",
        )
    output = Path(destination).expanduser().resolve()
    if output.exists():
        raise SpeechCapabilityError(
            "VOICE_PACKAGE_OUTPUT_EXISTS",
            f"package destination already exists: {output}",
            "Choose a new .wgpvoice path; export must not overwrite a package.",
        )
    if output.suffix.lower() != ".wgpvoice":
        raise SpeechCapabilityError(
            "VOICE_PACKAGE_INVALID",
            f"package destination must end in .wgpvoice: {output}",
            "Use a portable .wgpvoice archive path.",
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    appearance_path = Path(appearance.path).expanduser().resolve()
    appearance_bytes = _readable(
        appearance_path,
        appearance.sha256,
        code="VOICE_APPEARANCE_MISSING",
        label="character appearance",
    )
    appearance_member = "appearance" + appearance_path.suffix.lower()
    references: list[dict[str, Any]] = []
    members: list[tuple[str, bytes]] = []
    for index, reference in enumerate(request.references):
        source = Path(reference.path).expanduser().resolve()
        data = _readable(
            source,
            reference.sha256,
            code="SPEECH_REFERENCE_MISSING",
            label=f"voice reference {index + 1}",
            duration_s=reference.duration_s,
        )
        member = f"references/{reference.role}.wav"
        members.append((member, data))
        references.append({
            "member": member,
            "sha256": reference.sha256,
            "role": reference.role,
            "duration_s": reference.duration_s,
            "source": reference.source,
            "license": reference.license,
            "consent_ref": reference.consent_ref,
        })
    manifest = {
        "schema_version": PACKAGE_SCHEMA,
        "character": {
            "character_id": character.character_id,
            "speaker_label": character.speaker_label,
            "voice_binding_id": character.voice_binding_id,
            "appearance": {
                "member": appearance_member,
                "sha256": appearance.sha256,
                "role": appearance.role,
                "visual_binding": "character_appearance",
            },
        },
        "voice": {
            "engine_compatibility": [request.model.family.value, request.model.preset.value],
            "references": references,
            "language": request.language,
            "style": request.style,
        },
        "audio_claimed": False,
        "host_contact": False,
        "execution_status": "planned",
    }
    members.append((appearance_member, appearance_bytes))
    manifest_bytes = json.dumps(manifest, sort_keys=True, indent=2, ensure_ascii=False).encode("utf-8") + b"\n"
    try:
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for member, data in members:
                info = zipfile.ZipInfo(member, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, data)
            info = zipfile.ZipInfo("voice-package.json", date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, manifest_bytes)
    except Exception:
        output.unlink(missing_ok=True)
        raise
    return output, manifest


def _safe_member(name: str) -> bool:
    path = Path(name)
    return (
        not path.is_absolute()
        and ".." not in path.parts
        and not name.endswith("/")
        and (path.parent == Path("references") or path.parent == Path("."))
    )


def import_voice_package(package: str | Path, destination: str | Path) -> dict[str, Any]:
    """Read a package into one new namespace-safe directory."""

    source = Path(package).expanduser().resolve()
    target = Path(destination).expanduser().resolve()
    if not source.is_file() or source.suffix.lower() != ".wgpvoice":
        raise SpeechCapabilityError(
            "VOICE_PACKAGE_INVALID",
            f"portable voice package is not a readable .wgpvoice file: {source}",
            "Supply a package emitted by wgp voice export.",
            next_command="wgp voice import --package <package.wgpvoice> --destination <directory> --json",
        )
    if target.exists():
        raise SpeechCapabilityError(
            "VOICE_PACKAGE_DESTINATION_EXISTS",
            f"import destination already exists: {target}",
            "Choose a new directory; import never merges or overwrites files.",
        )
    try:
        with zipfile.ZipFile(source) as archive:
            infos = archive.infolist()
            if any(info.flag_bits & 0x1 for info in infos):
                raise ValueError("encrypted members are unsupported")
            if any(info.file_size > _MAX_MEMBER_BYTES for info in infos):
                raise ValueError("package member exceeds 128 MiB")
            unsafe = [info.filename for info in infos if not _safe_member(info.filename)]
            if unsafe:
                raise ValueError(f"unsafe package member: {unsafe[0]!r}")
            if len(infos) != len({info.filename for info in infos}):
                raise ValueError("duplicate package member")
            try:
                raw_manifest = archive.read("voice-package.json")
            except KeyError as exc:
                raise ValueError("voice-package.json is missing") from exc
            payload = {info.filename: archive.read(info.filename) for info in infos}
    except (OSError, zipfile.BadZipFile, RuntimeError, ValueError) as exc:
        raise SpeechCapabilityError(
            "VOICE_PACKAGE_INVALID",
            f"cannot open portable voice package {source}: {exc}",
            "Use an unencrypted, undamaged package emitted by wgp voice export.",
            metadata={"path": str(source)},
        ) from exc
    try:
        manifest = json.loads(raw_manifest)
        if manifest.get("schema_version") != PACKAGE_SCHEMA:
            raise ValueError(f"unsupported schema {manifest.get('schema_version')!r}")
        character = manifest["character"]
        if not isinstance(character.get("character_id"), str) or not _CHARACTER_RE.fullmatch(character["character_id"]):
            raise ValueError("invalid character_id")
        appearance = character["appearance"]
        references = manifest["voice"]["references"]
        if not isinstance(references, list) or not 1 <= len(references) <= 2:
            raise ValueError("one or two voice references are required")
        expected = {appearance["member"]: appearance["sha256"]}
        expected.update({item["member"]: item["sha256"] for item in references})
        if set(expected) | {"voice-package.json"} != set(payload):
            raise ValueError("package members do not match the manifest")
        for member, digest in expected.items():
            actual = hashlib.sha256(payload[member]).hexdigest()
            if actual != digest:
                raise ValueError(f"hash mismatch for {member}")
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise SpeechCapabilityError(
            "VOICE_PACKAGE_INVALID",
            f"portable voice manifest is unusable: {exc}",
            "Re-export the portable character voice from its authorized source request.",
            metadata={"path": str(source)},
        ) from exc
    target.mkdir(parents=True)
    try:
        for member, data in payload.items():
            destination_path = target / member
            if destination_path.resolve().parent not in {target, (target / "references").resolve()}:
                raise ValueError(f"unsafe destination for {member}")
            destination_path.parent.mkdir(parents=True, exist_ok=True)
            destination_path.write_bytes(data)
    except Exception:
        if target.exists():
            for path in sorted(target.rglob("*"), reverse=True):
                if path.is_file() or path.is_symlink():
                    path.unlink()
                elif path.is_dir():
                    path.rmdir()
            target.rmdir()
        raise SpeechCapabilityError(
            "VOICE_PACKAGE_INVALID",
            "package import could not write its namespace-safe members",
            "Choose a new destination directory and retry with the unchanged package.",
        ) from exc
    return {
        "schema_version": PACKAGE_SCHEMA,
        "package_sha256": file_sha256(source),
        "destination": str(target),
        "manifest": manifest,
        "audio_claimed": False,
        "host_contact": False,
    }


__all__ = ["PACKAGE_SCHEMA", "export_voice_package", "import_voice_package"]
