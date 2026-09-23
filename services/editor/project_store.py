"""Portable project persistence, source verification, and undo/redo history."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path
from typing import Callable

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from wangp.editor_project import (
    PROJECT_SCHEMA,
    Clip,
    EditorProject,
    EditorProjectError,
    SourceAsset,
    TrackKind,
)


DOCUMENT_SCHEMA = "wangp-dspy.editor-document/v1"
SUPPORTED_PROJECT_SCHEMAS = frozenset({PROJECT_SCHEMA})
NEXT_COMMAND = "wgp editor validate --project <project> --json"


def _reject(code: str, observed: str, remediation: str, **metadata: object) -> EditorProjectError:
    return EditorProjectError(code, observed, remediation, next_command=NEXT_COMMAND, **metadata)


class HistoryEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    revision: int = Field(ge=0)
    operation: str = Field(min_length=1)
    project: EditorProject


class EditorProjectDocument(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str
    history: tuple[HistoryEntry, ...] = Field(min_length=1)
    history_cursor: int = Field(ge=0)

    @property
    def project(self) -> EditorProject:
        return self.history[self.history_cursor].project


class ProjectStore:
    """Atomic JSON persistence; imported source files are read-only inputs."""

    def __init__(self, path: str | Path):
        self.path = Path(path).expanduser().resolve()

    @classmethod
    def create(cls, path: str | Path, project: EditorProject) -> "ProjectStore":
        store = cls(path)
        if store.path.exists():
            raise _reject("EDITOR_PROJECT_EXISTS", f"project already exists: {store.path}", "Choose a new project path; the editor never overwrites one.")
        document = EditorProjectDocument(
            schema_version=DOCUMENT_SCHEMA,
            history=(HistoryEntry(revision=project.revision, operation="import", project=project),),
            history_cursor=0,
        )
        store._write(document)
        return store

    def import_source(self, source: str | Path, kind: TrackKind, asset_id: str) -> SourceAsset:
        original = Path(source).expanduser().resolve()
        if not original.is_file():
            raise _reject("EDITOR_SOURCE_IMPORT_MISSING", f"source does not exist: {original}", "Pass an existing immutable source; Wangp will not fetch it.", path=str(original))
        target = self.path.parent / "sources" / f"{asset_id}{original.suffix.lower()}"
        target.parent.mkdir(parents=True, exist_ok=True)
        digest = self._hash(original)
        if target.exists():
            if self._hash(target) != digest:
                raise _reject("EDITOR_SOURCE_IMPORT_COLLISION", f"portable source already exists with different bytes: {target}", "Use a unique asset_id or remove only a disposable temporary copy.", path=str(target))
        else:
            shutil.copyfile(original, target)
        return SourceAsset(
            asset_id=asset_id,
            kind=kind,
            path=target.relative_to(self.path.parent).as_posix(),
            sha256=digest,
            byte_size=target.stat().st_size,
        )

    def load(self) -> EditorProjectDocument:
        if not self.path.is_file():
            raise _reject("EDITOR_PROJECT_MISSING", f"project does not exist: {self.path}", "Pass an existing editor project JSON file.", path=str(self.path))
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            embedded = payload.get("history", ()) if isinstance(payload, dict) else ()
            versions = {
                entry.get("project", {}).get("schema_version")
                for entry in embedded
                if isinstance(entry, dict) and isinstance(entry.get("project"), dict)
            }
            if versions and not versions <= SUPPORTED_PROJECT_SCHEMAS:
                raise _reject("EDITOR_PROJECT_SCHEMA_UNSUPPORTED", f"unsupported project schema {sorted(versions)!r}", "Recreate the project with the supported editor schema.", supported=sorted(SUPPORTED_PROJECT_SCHEMAS))
            document = EditorProjectDocument.model_validate(payload)
        except (OSError, UnicodeError, json.JSONDecodeError, ValidationError) as exc:
            raise _reject("EDITOR_PROJECT_INVALID", f"cannot load project {self.path}: {exc}", "Use a project emitted by the editor store; do not edit it by hand.") from exc
        if document.project.schema_version not in SUPPORTED_PROJECT_SCHEMAS:
            raise _reject("EDITOR_PROJECT_SCHEMA_UNSUPPORTED", f"unsupported project schema {document.project.schema_version!r}", "Recreate the project with the supported editor schema.", supported=sorted(SUPPORTED_PROJECT_SCHEMAS))
        if document.history_cursor >= len(document.history):
            raise _reject("EDITOR_PROJECT_INVALID", "history_cursor is outside the decision history", "Use a project emitted by the editor store.")
        return document

    def save(self, project: EditorProject, operation: str) -> EditorProjectDocument:
        document = self.load()
        latest = document.history[-1]
        if project.revision != latest.revision + 1:
            raise _reject("EDITOR_PROJECT_REVISION_INVALID", f"new revision {project.revision} must follow {latest.revision}", "Apply one modeled edit to the currently selected project state.")
        if document.history_cursor != len(document.history) - 1:
            history = document.history[:document.history_cursor + 1]
        else:
            history = document.history
        entry = HistoryEntry(revision=project.revision, operation=operation, project=project)
        changed = EditorProjectDocument(
            schema_version=DOCUMENT_SCHEMA,
            history=(*history, entry),
            history_cursor=len(history),
        )
        self._write(changed)
        return changed

    def edit(self, operation: str, callback: Callable[[EditorProject], EditorProject]) -> EditorProjectDocument:
        current = self.load().project
        return self.save(callback(current), operation)

    def undo(self) -> EditorProjectDocument:
        document = self.load()
        if document.history_cursor == 0:
            raise _reject("EDITOR_UNDO_UNAVAILABLE", "no prior decision is selected for undo", "Edit the project before undoing; imported sources are never rewritten.")
        changed = document.model_copy(update={"history_cursor": document.history_cursor - 1})
        self._write(changed)
        return changed

    def redo(self) -> EditorProjectDocument:
        document = self.load()
        if document.history_cursor >= len(document.history) - 1:
            raise _reject("EDITOR_REDO_UNAVAILABLE", "no later decision is selected for redo", "Undo an edit before redoing it; imported sources are never rewritten.")
        changed = document.model_copy(update={"history_cursor": document.history_cursor + 1})
        self._write(changed)
        return changed

    def resolve_source(self, asset: SourceAsset) -> Path:
        candidate = Path(asset.path).expanduser()
        if not candidate.is_absolute():
            candidate = self.path.parent / candidate
        return candidate.resolve()

    def verify_sources(self, project: EditorProject | None = None) -> list[SourceAsset]:
        selected = self.load().project if project is None else project
        for asset in selected.sources:
            path = self.resolve_source(asset)
            if not path.is_file():
                raise _reject("EDITOR_SOURCE_MISSING", f"source is not readable: {path}", "Restore the pinned source bytes; Wangp will not fetch or regenerate them.", asset_id=asset.asset_id, path=str(path), expected_sha256=asset.sha256)
            actual = self._hash(path)
            if actual != asset.sha256 or path.stat().st_size != asset.byte_size:
                raise _reject("EDITOR_SOURCE_HASH_MISMATCH", f"source hash mismatch for {asset.asset_id}: expected {asset.sha256}, got {actual}", "Restore the exact imported bytes or create a new pinned source asset.", asset_id=asset.asset_id, path=str(path), expected_sha256=asset.sha256, actual_sha256=actual)
        return list(selected.sources)

    def source_manifest(self, project: EditorProject | None = None) -> dict[str, str]:
        selected = self.load().project if project is None else project
        return {
            asset.asset_id: asset.sha256
            for asset in self.verify_sources(selected)
        }

    def _write(self, document: EditorProjectDocument) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        staging = self.path.parent / f".{self.path.name}.{os.urandom(8).hex()}.tmp"
        try:
            staging.write_text(
                json.dumps(document.model_dump(mode="json"), sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            os.replace(staging, self.path)
        finally:
            staging.unlink(missing_ok=True)

    @staticmethod
    def _hash(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()


__all__ = ["EditorProjectDocument", "HistoryEntry", "ProjectStore", "DOCUMENT_SCHEMA", "SUPPORTED_PROJECT_SCHEMAS"]
