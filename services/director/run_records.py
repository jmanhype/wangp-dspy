"""Append-only dataset run emission with checkout attribution."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Mapping, Optional

from services.director.run_ledger import repository_identity


class DatasetRunError(ValueError):
    """Typed rejection for a run record that cannot be attributed."""


def append_dataset_run(path: str | Path, *, run_id: str, status: str,
                       payload: Optional[Mapping] = None,
                       repo_root: Optional[str] = None) -> dict:
    """Append one deterministic JSONL record; never overwrite prior runs."""
    if not isinstance(run_id, str) or not run_id.strip():
        raise DatasetRunError("run_id: required")
    if not isinstance(status, str) or not status.strip():
        raise DatasetRunError("status: required")
    identity = repository_identity(repo_root)
    record = {
        "schema_version": 1,
        "run_id": run_id,
        "status": status,
        "repository": {"repo_root": identity["repo_root"],
                        "commit_sha": identity["commit_sha"]},
        "payload": dict(payload or {}),
    }
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
        fh.flush()
        os.fsync(fh.fileno())
    return record


def read_dataset_runs(path: str | Path) -> list[dict]:
    target = Path(path)
    if not target.is_file():
        return []
    rows = []
    for line in target.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


__all__ = ["DatasetRunError", "append_dataset_run", "read_dataset_runs"]
