"""Hash-verified portable character packages without media generation."""
from __future__ import annotations

import hashlib
import json
import os
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from predict.character_packages import (
    PACKAGE_SCHEMA_VERSION,
    PACKAGE_SUFFIX,
    VOICE_MEMBER,
    AppearanceInput,
    AppearanceRole,
    CharacterDefinition,
    CharacterPackageError,
    CharacterPackageManifest,
    SavedVoiceInput,
    VoiceRecord,
    identity_digest,
)

MANIFEST_MEMBER = "character.json"
VOICE_PACKAGE_SCHEMA = "wangp-dspy.character-voice-package/v1"
MAX_MEMBER_BYTES = 128 * 1024 * 1024
_SAFE_MEMBER = re.compile(r"^(appearance/[A-Za-z0-9_.-]+|voice/character\.wgpvoice|character\.json)$")


def file_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read(path: Path, expected: str, *, code: str, label: str) -> bytes:
    if not path.is_file():
        raise CharacterPackageError(
            code,
            f"{label} is not readable: {path}",
            "Restore the exact authorized local asset; Wangp will not fetch or repair it.",
        )
    actual = file_sha256(path)
    if actual != expected:
        raise CharacterPackageError(
            code,
            f"{label} hash mismatch: expected {expected}, got {actual}",
            "Restore the exact recorded bytes or update authorized provenance.",
            metadata={"expected": expected, "actual": actual},
        )
    return path.read_bytes()


def load_definition(path: str | Path) -> CharacterDefinition:
    source = Path(path).expanduser()
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
        return CharacterDefinition.model_validate(payload)
    except FileNotFoundError as exc:
        raise CharacterPackageError(
            "CHARACTER_DEFINITION_MISSING",
            f"character definition does not exist: {source}",
            "Pass an existing typed character JSON file.",
        ) from exc
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise CharacterPackageError(
            "CHARACTER_DEFINITION_INVALID",
            f"cannot validate character definition {source}: {exc}",
            "Fix the typed definition, then rerun the portable character command.",
        ) from exc


def write_definition(definition: CharacterDefinition, destination: str | Path) -> Path:
    output = Path(destination).expanduser().resolve()
    if output.exists():
        raise CharacterPackageError(
            "CHARACTER_OUTPUT_EXISTS",
            f"definition destination already exists: {output}",
            "Choose a new JSON path; creation never overwrites provenance.",
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        output.write_text(
            json.dumps(definition.model_dump(mode="json"), sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
    except Exception:
        output.unlink(missing_ok=True)
        raise
    return output


def bind_saved_voice(definition: CharacterDefinition, voice_path: str | Path) -> CharacterDefinition:
    path = Path(voice_path).expanduser().resolve()
    if not path.is_file() or path.suffix.lower() != ".wgpvoice":
        raise CharacterPackageError(
            "CHARACTER_VOICE_PACKAGE_INVALID",
            f"saved voice is not a readable .wgpvoice package: {path}",
            "Supply a package emitted by wgp voice export.",
        )
    manifest = _voice_manifest(path)
    character = manifest["character"]
    if (
        character["character_id"] != definition.character_id
        or character["speaker_label"] != definition.speaker_label
    ):
        raise CharacterPackageError(
            "CHARACTER_VOICE_BINDING_MISMATCH",
            "saved voice identity does not match the character definition",
            "Bind a .wgpvoice package exported for this character_id and speaker_label.",
            metadata={
                "character_id": character["character_id"],
                "speaker_label": character["speaker_label"],
            },
        )
    binding = SavedVoiceInput(path=str(path), voice_binding_id=character["voice_binding_id"])
    return definition.model_copy(update={"voice": binding})


def _voice_manifest(path: Path) -> dict[str, Any]:
    try:
        with zipfile.ZipFile(path) as archive:
            if any(info.flag_bits & 0x1 for info in archive.infolist()):
                raise ValueError("encrypted members are unsupported")
            raw = archive.read("voice-package.json")
    except (OSError, zipfile.BadZipFile, RuntimeError, ValueError) as exc:
        raise CharacterPackageError(
            "CHARACTER_VOICE_PACKAGE_INVALID",
            f"cannot read saved voice package {path}: {exc}",
            "Supply an unencrypted package emitted by wgp voice export.",
        ) from exc
    try:
        manifest = json.loads(raw)
        if manifest.get("schema_version") != VOICE_PACKAGE_SCHEMA:
            raise ValueError(f"unsupported schema {manifest.get('schema_version')!r}")
        character = manifest["character"]
        voice = manifest["voice"]
        for key in ("character_id", "speaker_label", "voice_binding_id"):
            if not isinstance(character.get(key), str) or not character[key]:
                raise ValueError(f"voice character is missing {key}")
        if not isinstance(voice.get("references"), list) or not voice["references"]:
            raise ValueError("voice package has no references")
        return manifest
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise CharacterPackageError(
            "CHARACTER_VOICE_PACKAGE_INVALID",
            f"saved voice manifest is unusable: {exc}",
            "Re-export the saved voice from its authorized source request.",
        ) from exc


def export_character_package(definition: CharacterDefinition, destination: str | Path) -> tuple[Path, CharacterPackageManifest]:
    output = Path(destination).expanduser().resolve()
    if output.exists() or output.suffix.lower() != PACKAGE_SUFFIX:
        raise CharacterPackageError(
            "CHARACTER_PACKAGE_OUTPUT_INVALID",
            f"package destination is new and ends in {PACKAGE_SUFFIX}: {output}",
            "Choose a nonexistent .wgpcharacter path.",
        )
    if definition.voice is None:
        raise CharacterPackageError(
            "CHARACTER_VOICE_BINDING_MISSING",
            "character definition has no saved voice binding",
            "Run wgp character bind-voice before export.",
        )
    members: list[tuple[str, bytes]] = []
    appearance: list[dict[str, Any]] = []
    for item in definition.appearance:
        source = Path(item.path).expanduser().resolve()
        data = _read(
            source,
            item.sha256,
            code="CHARACTER_APPEARANCE_UNUSABLE",
            label=f"{item.role.value} appearance",
        )
        member = f"appearance/{item.role.value}{source.suffix.lower()}"
        members.append((member, data))
        appearance.append({
            **item.model_dump(mode="json", exclude={"path"}),
            "member": member,
        })
    voice_path = Path(definition.voice.path).expanduser().resolve()
    voice_bytes = _read(
        voice_path,
        file_sha256(voice_path),
        code="CHARACTER_VOICE_PACKAGE_INVALID",
        label="saved character voice",
    )
    voice_manifest = _voice_manifest(voice_path)
    voice_character = voice_manifest["character"]
    if (
        voice_character["character_id"] != definition.character_id
        or voice_character["speaker_label"] != definition.speaker_label
        or voice_character["voice_binding_id"] != definition.voice.voice_binding_id
    ):
        raise CharacterPackageError(
            "CHARACTER_VOICE_BINDING_MISMATCH",
            "saved voice package identity/binding does not match the definition",
            "Export a matching voice package or update the character definition binding.",
        )
    _identity_json, identity_hash = identity_digest(
        definition.character_id,
        definition.speaker_label,
        definition.voice.voice_binding_id,
    )
    manifest = CharacterPackageManifest.model_validate({
        "schema_version": PACKAGE_SCHEMA_VERSION,
        "character_id": definition.character_id,
        "speaker_label": definition.speaker_label,
        "version": definition.version,
        "description": definition.description,
        "identity_sha256": identity_hash,
        "appearance": appearance,
        "voice": {
            "member": VOICE_MEMBER,
            "sha256": file_sha256(voice_path),
            "character_id": definition.character_id,
            "speaker_label": definition.speaker_label,
            "voice_binding_id": definition.voice.voice_binding_id,
            "engine_compatibility": voice_manifest["voice"]["engine_compatibility"],
            "source_path": str(voice_path),
        },
        "continuity": definition.continuity.model_dump(mode="json"),
        "recipe_seed": definition.recipe_seed,
    })
    members.append((VOICE_MEMBER, voice_bytes))
    members.append((MANIFEST_MEMBER, _manifest_bytes(manifest.model_dump(mode="json"))))
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for member, data in members:
                info = zipfile.ZipInfo(member, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, data)
    except Exception:
        output.unlink(missing_ok=True)
        raise
    return output, manifest


def _manifest_bytes(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False).encode("utf-8") + b"\n"


def inspect_character_package(package: str | Path) -> dict[str, Any]:
    source = Path(package).expanduser().resolve()
    if not source.is_file() or source.suffix.lower() != PACKAGE_SUFFIX:
        raise CharacterPackageError(
            "CHARACTER_PACKAGE_INVALID",
            f"portable character is not a readable {PACKAGE_SUFFIX} file: {source}",
            "Supply a package emitted by wgp character export.",
        )
    try:
        with zipfile.ZipFile(source) as archive:
            infos = archive.infolist()
            if any(info.flag_bits & 0x1 for info in infos):
                raise ValueError("encrypted members are unsupported")
            if any(info.file_size > MAX_MEMBER_BYTES for info in infos):
                raise ValueError("package member exceeds 128 MiB")
            unsafe = [info.filename for info in infos if _SAFE_MEMBER.fullmatch(info.filename) is None]
            if unsafe:
                raise ValueError(f"unsafe package member {unsafe[0]!r}")
            if len(infos) != len({info.filename for info in infos}):
                raise ValueError("duplicate package member")
            payload = {info.filename: archive.read(info.filename) for info in infos}
    except CharacterPackageError:
        raise
    except (OSError, zipfile.BadZipFile, RuntimeError, ValueError) as exc:
        raise CharacterPackageError(
            "CHARACTER_PACKAGE_INVALID",
            f"cannot open portable character package {source}: {exc}",
            "Use an unencrypted, undamaged package emitted by wgp character export.",
        ) from exc
    try:
        manifest = CharacterPackageManifest.model_validate(json.loads(payload[MANIFEST_MEMBER]))
        expected = {item.member: item.sha256 for item in manifest.appearance}
        expected[manifest.voice.member] = manifest.voice.sha256
        if set(expected) | {MANIFEST_MEMBER} != set(payload):
            raise ValueError("package members do not match manifest")
        for member, digest in expected.items():
            actual = hashlib.sha256(payload[member]).hexdigest()
            if actual != digest:
                raise ValueError(f"hash mismatch for {member}")
        identity_json, identity_hash = identity_digest(
            manifest.character_id, manifest.speaker_label, manifest.voice.voice_binding_id
        )
        if identity_hash != manifest.identity_sha256:
            raise ValueError("identity hash mismatch")
        inner = _voice_manifest_from_bytes(payload[manifest.voice.member])
        inner_character = inner["character"]
        if (
            inner_character["character_id"] != manifest.voice.character_id
            or inner_character["speaker_label"] != manifest.voice.speaker_label
            or inner_character["voice_binding_id"] != manifest.voice.voice_binding_id
        ):
            raise ValueError("saved voice identity does not match package")
    except KeyError as exc:
        raise CharacterPackageError(
            "CHARACTER_PACKAGE_INVALID",
            f"portable character package is missing {MANIFEST_MEMBER}",
            "Use a complete package emitted by wgp character export.",
        ) from exc
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise CharacterPackageError(
            "CHARACTER_PACKAGE_INVALID",
            f"portable character package is unusable: {exc}",
            "Restore or re-export the unchanged package; Wangp will not repair hashes.",
        ) from exc
    return {
        "schema_version": PACKAGE_SCHEMA_VERSION,
        "package": str(source),
        "package_sha256": file_sha256(source),
        "identity_json": identity_json,
        "identity_sha256": identity_hash,
        "manifest": manifest.model_dump(mode="json"),
        "member_sha256": expected,
        "generation_claimed": False,
        "host_contact": False,
        "execution_status": "planned",
    }


def _voice_manifest_from_bytes(data: bytes) -> dict[str, Any]:
    try:
        import io

        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            manifest = json.loads(archive.read("voice-package.json"))
        if manifest.get("schema_version") != VOICE_PACKAGE_SCHEMA:
            raise ValueError(f"unsupported voice schema {manifest.get('schema_version')!r}")
        character = manifest["character"]
        return {
            "character": {
                "character_id": character["character_id"],
                "speaker_label": character["speaker_label"],
                "voice_binding_id": character["voice_binding_id"],
            }
        }
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError(f"saved voice manifest is unusable: {exc}") from exc


def import_character_package(package: str | Path, destination: str | Path) -> dict[str, Any]:
    inspected = inspect_character_package(package)
    target = Path(destination).expanduser().resolve()
    if target.exists():
        raise CharacterPackageError(
            "CHARACTER_IMPORT_DESTINATION_EXISTS",
            f"import destination already exists: {target}",
            "Choose a new directory; import never merges or overwrites files.",
        )
    source = Path(package).expanduser().resolve()
    try:
        with zipfile.ZipFile(source) as archive:
            archive.extractall(target)
    except Exception:
        for path in sorted(target.rglob("*"), reverse=True):
            if path.is_file() or path.is_symlink():
                path.unlink()
            elif path.is_dir():
                path.rmdir()
        target.rmdir(missing_ok=True)
        raise CharacterPackageError(
            "CHARACTER_PACKAGE_INVALID",
            "package import could not write namespace-safe members",
            "Choose a new destination and retry with the unchanged package.",
        )
    return {
        **inspected,
        "destination": str(target),
        "imported_members": sorted(inspected["member_sha256"]),
    }


def recover_native_source(package: str | Path, destination: str | Path, *, role: str = "native") -> dict[str, str]:
    inspected = inspect_character_package(package)
    manifest = CharacterPackageManifest.model_validate(inspected["manifest"])
    match = next((item for item in manifest.appearance if item.role.value == role), None)
    if match is None:
        raise CharacterPackageError(
            "CHARACTER_NATIVE_SOURCE_MISSING",
            f"package has no {role} appearance source record",
            "Export a package with a native appearance source reference.",
        )
    source = Path(match.source_path).expanduser().resolve()
    if not source.is_file():
        raise CharacterPackageError(
            "CHARACTER_NATIVE_SOURCE_MISSING",
            f"recorded native source is unavailable: {source}",
            "Restore the exact authorized source; Wangp will not substitute a derivative.",
        )
    actual = file_sha256(source)
    if actual != match.sha256:
        raise CharacterPackageError(
            "CHARACTER_APPEARANCE_MISMATCH",
            f"native source hash mismatch: expected {match.sha256}, got {actual}",
            "Restore the exact recorded native bytes; no derivative is accepted.",
        )
    output = Path(destination).expanduser().resolve()
    if output.exists():
        raise CharacterPackageError(
            "CHARACTER_OUTPUT_EXISTS",
            f"native recovery destination already exists: {output}",
            "Choose a new output path; recovery never overwrites source media.",
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = output.parent / f".{output.name}.{os.urandom(8).hex()}.tmp"
    try:
        staging.write_bytes(source.read_bytes())
        os.replace(staging, output)
    except Exception:
        staging.unlink(missing_ok=True)
        output.unlink(missing_ok=True)
        raise
    return {
        "source": str(source),
        "recovered": str(output),
        "sha256": actual,
        "transcoded": "false",
        "substituted_derivative": "false",
    }


@dataclass(frozen=True)
class RegisteredCharacter:
    manifest: CharacterPackageManifest
    package_path: Path
    package_sha256: str


class CharacterRegistry:
    """A duplicate-free identity index over one explicit package set."""

    def __init__(self) -> None:
        self._by_id: dict[str, RegisteredCharacter] = {}
        self._by_speaker: dict[str, RegisteredCharacter] = {}

    def register(self, package: str | Path) -> RegisteredCharacter:
        inspected = inspect_character_package(package)
        manifest = CharacterPackageManifest.model_validate(inspected["manifest"])
        entry = RegisteredCharacter(
            manifest=manifest,
            package_path=Path(inspected["package"]),
            package_sha256=inspected["package_sha256"],
        )
        key = manifest.character_id.casefold()
        speaker = manifest.speaker_label.casefold()
        if key in self._by_id:
            raise CharacterPackageError(
                "CHARACTER_IDENTITY_DUPLICATE",
                f"registry already contains character_id {manifest.character_id!r}",
                "Remove the stale package or assign a unique character identity.",
            )
        if speaker in self._by_speaker:
            raise CharacterPackageError(
                "CHARACTER_IDENTITY_AMBIGUOUS",
                f"registry already contains speaker_label {manifest.speaker_label!r}",
                "Use distinct speaker labels so requests cannot resolve two characters.",
            )
        self._by_id[key] = entry
        self._by_speaker[speaker] = entry
        return entry

    @classmethod
    def from_directory(cls, directory: str | Path) -> "CharacterRegistry":
        registry = cls()
        root = Path(directory).expanduser().resolve()
        if not root.is_dir():
            raise CharacterPackageError(
                "CHARACTER_REGISTRY_MISSING",
                f"registry directory does not exist: {root}",
                "Import packages into an explicit registry directory first.",
            )
        for package in sorted(root.rglob(f"*{PACKAGE_SUFFIX}")):
            registry.register(package)
        return registry

    def resolve(self, identity: str) -> RegisteredCharacter:
        entry = self._by_id.get(identity.casefold()) or self._by_speaker.get(identity.casefold())
        if entry is None:
            raise CharacterPackageError(
                "CHARACTER_IDENTITY_UNRESOLVED",
                f"registry has no character or speaker identity {identity!r}",
                "Register the exact portable package before referencing the character.",
            )
        return entry


__all__ = [
    "CharacterRegistry",
    "RegisteredCharacter",
    "bind_saved_voice",
    "export_character_package",
    "file_sha256",
    "import_character_package",
    "inspect_character_package",
    "load_definition",
    "recover_native_source",
    "write_definition",
]
