"""Director orchestrator — plan in, validated job configs + evidence
manifests out. Emission only: no GPU, no render execution, no
subprocess. Pattern reimplemented from Maestro's director orchestrator
(WanGP NCE 1.1; see docs/render-knowledge/maestro-port.md).

Lineage: each manifest carries the plan hash (planner output) and the
job hash (renderer output), so any rendered artifact can be traced to
the exact plan and job config that produced it.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Dict, List

from services.director.renderers.h3_ref2va import H3Ref2VARenderer
from services.director.schema import ProductionPlan


def _sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True)
class ShotManifest:
    """Per-shot evidence: hashes + plan lineage."""

    shot_index: int
    film_id: str
    plan_sha256: str
    job_sha256: str
    prompt_sha256: str
    guide_sha256: str
    plate_sha256: str
    lineage: Dict[str, str]

    def to_json(self) -> Dict:
        return {
            "shot_index": self.shot_index,
            "film_id": self.film_id,
            "plan_sha256": self.plan_sha256,
            "job_sha256": self.job_sha256,
            "prompt_sha256": self.prompt_sha256,
            "guide_sha256": self.guide_sha256,
            "plate_sha256": self.plate_sha256,
            "lineage": dict(self.lineage),
        }


@dataclass(frozen=True)
class DirectorResult:
    jobs: List[Dict]
    manifests: List[Dict]


class DirectorOrchestrator:
    """plan -> render -> emit. Every shot renders through the SAME
    policy-gated renderer; a rejection fails the whole emission
    (atomic: no partial job lists)."""

    def __init__(self, renderer: H3Ref2VARenderer | None = None) -> None:
        self._renderer = renderer or H3Ref2VARenderer()

    def execute(self, plan: ProductionPlan) -> DirectorResult:
        plan_sha = _sha256_bytes(_canonical(plan.to_json()).encode())
        jobs: List[Dict] = []
        manifests: List[Dict] = []
        for shot in plan.shots:
            job = self._renderer.render(plan, shot)
            guide_hash = self._file_sha(shot.audio_guide_ref["path"])
            plate_hash = self._file_sha(shot.start_image_ref)
            job_sha = _sha256_bytes(_canonical(job).encode())
            manifest = ShotManifest(
                shot_index=shot.index,
                film_id=plan.film_id,
                plan_sha256=plan_sha,
                job_sha256=job_sha,
                prompt_sha256=_sha256_bytes(job["prompt"].encode()),
                guide_sha256=guide_hash,
                plate_sha256=plate_hash,
                lineage={
                    "planner": "short_film_3pass",
                    "renderer": self._renderer.name,
                    "prompt_builder": "predict.subject_prompt/build_subject_prompt",
                },
            )
            jobs.append(job)
            manifests.append(manifest.to_json())
        return DirectorResult(jobs=jobs, manifests=manifests)

    @staticmethod
    def _file_sha(path: str) -> str:
        try:
            with open(path, "rb") as fh:
                return _sha256_bytes(fh.read())
        except OSError:
            return "unavailable"


__all__ = ["DirectorOrchestrator", "DirectorResult", "ShotManifest"]
