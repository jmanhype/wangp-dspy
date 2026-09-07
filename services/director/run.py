"""Repo-owned DirectorRun orchestration for a disposable continuation film.

This is the narrow production seam between creative planning and the durable
jobs queue.  It owns premise resolution, exact six-cut/grid-aligned chain
planning, dataset-run emission, and job submission; rendering remains in
``JobExecutor``/``WanGPAdapter.render_for_job``.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional, Sequence

from services.chain.controller import build_chain_plan, emit_render_manifest
from services.director.premises import Premise, resolve_premise
from services.director.run_records import append_dataset_run
from predict.job_config import CONTINUATION_FRAMES_MIN


class DirectorRunError(ValueError):
    """Typed DirectorRun input or queue-emission rejection."""


@dataclass(frozen=True)
class DirectorRunPlan:
    run_id: str
    premise_id: str
    chain_plan: object
    clips: tuple[dict, ...]


class DirectorRun:
    """One repo-attributed, six-cut grid-aligned dialogue run."""

    def __init__(self, *, run_id: str, premise: Premise | str | None = None,
                 dataset_run_path: str | Path | None = None,
                 premise_index=None):
        if not isinstance(run_id, str) or not run_id.strip():
            raise DirectorRunError("run_id: required")
        self.run_id = run_id
        self.premise = (resolve_premise(premise, index=premise_index)
                        if isinstance(premise, str) or premise is None
                        else premise)
        if not isinstance(self.premise, Premise):
            raise DirectorRunError("premise: must be a Premise or premise id")
        self.dataset_run_path = (Path(dataset_run_path)
                                 if dataset_run_path is not None else None)

    def plan(self, script_lines: Sequence[dict], *, audio_paths: Sequence[str],
             plate_paths: Sequence[str | Sequence[str]]) -> DirectorRunPlan:
        """Build the strict ContinuationExtras manifest (no GPU/subprocess)."""
        if len(script_lines) != 6:
            raise DirectorRunError(
                f"script_lines: acceptance run requires exactly 6 cuts, got {len(script_lines)}")
        if len(audio_paths) != 6:
            raise DirectorRunError(
                "audio_paths: six single-speaker turn wavs are required")
        if len(plate_paths) < 2:
            raise DirectorRunError(
                "plate_paths: anchor plus at least one silent-character face ref required")
        if isinstance(plate_paths[0], (list, tuple)):
            if len(plate_paths) != 6 or any(
                    len(pair) != 2 for pair in plate_paths):
                raise DirectorRunError(
                    "plate_paths: per-cut form must contain six [anchor, silent_face] pairs")
        cut_duration_s = CONTINUATION_FRAMES_MIN / 24.0
        durations = [cut_duration_s] * 6
        characters = [dict(c) for c in self.premise.characters]
        try:
            chain = build_chain_plan(
                script_lines, characters, durations,
                audio_paths=audio_paths, continuation_mode=True)
            clips = tuple(emit_render_manifest(
                chain, plate_paths=plate_paths))
        except Exception as exc:
            raise DirectorRunError(f"continuation planning failed: {exc}") from exc
        # A strict continuation manifest has one render job per dialogue turn.
        if len(clips) != 6 or any(
                c.get("frames") != CONTINUATION_FRAMES_MIN for c in clips):
            raise DirectorRunError(
                "continuation plan did not emit six grid-aligned "
                f"{CONTINUATION_FRAMES_MIN}-frame jobs")
        if self.dataset_run_path is not None:
            append_dataset_run(
                self.dataset_run_path, run_id=self.run_id, status="planned",
                payload={"premise_id": self.premise.id, "clip_count": len(clips),
                         "durations_s": durations})
        return DirectorRunPlan(self.run_id, self.premise.id, chain, clips)

    @staticmethod
    def submit(plan: DirectorRunPlan, queue) -> list[str]:
        """Submit each planned clip with a durable previous-cut dependency."""
        if not isinstance(plan, DirectorRunPlan):
            raise DirectorRunError("plan: expected DirectorRunPlan")
        ids = []
        previous = None
        for clip in plan.clips:
            job = dict(clip)
            if previous is not None:
                job["needs"] = previous
            jid = queue.submit(plan_ref=plan.run_id, clips=[job])
            ids.append(jid)
            previous = jid
        return ids

    def pipeline_plan(self, intent: str, *, n_shots: int = 6,
                      pipeline_factory: Optional[Callable] = None):
        """Expose the DSPy Pipeline/PromptDirector planning seam.

        This method is deliberately render-free: ``Pipeline`` receives no
        adapter, so a compile/optimization pass cannot spend GPU time.
        """
        if not isinstance(intent, str) or not intent.strip():
            raise DirectorRunError("intent: required")
        if n_shots < 1:
            raise DirectorRunError("n_shots: must be positive")
        if pipeline_factory is None:
            from predict.pipeline import Pipeline
            pipeline_factory = lambda: Pipeline(genre="dialogue")
        pipeline = pipeline_factory()
        return pipeline.forward(intent, n_shots=n_shots)


__all__ = ["DirectorRunError", "DirectorRunPlan", "DirectorRun"]
