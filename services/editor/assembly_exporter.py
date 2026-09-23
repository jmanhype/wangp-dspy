"""Deterministic translation from an editor project into governed planning."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping

from predict.assembler import AssembledChain, MultiShotAssembler, ShotPlan
from predict.profile_selector import ProfileDecision
from predict.prompt_director import RenderBrief
from services.director.composition import (
    DirectorMode,
    DirectorRequest,
    PacingControl,
    ReviewControl,
    ReviewMode,
)
from services.director.plan_compiler import compile_director_request
from services.editor.project_store import ProjectStore
from wangp.editor_project import Clip, EditorProject, EditorProjectError, TrackKind, project_sha256


EXPORT_SCHEMA = "wangp-dspy.editor-export/v1"
DIRECTOR_IMPORT = "services.director.plan_compiler.compile_director_request"
ASSEMBLER_IMPORT = "predict.assembler.MultiShotAssembler.assemble"
QUEUE_IMPORT = "services.jobs.queue.JobQueue.submit"


def _video_clips(project: EditorProject) -> list[Clip]:
    clips = [
        clip
        for track in sorted(project.tracks, key=lambda item: item.order)
        if track.kind is TrackKind.video
        for clip in track.clips
    ]
    if len(clips) < 2:
        raise EditorProjectError(
            "EDITOR_EXPORT_SHOTS_INVALID",
            f"governed export requires at least two ordered video clips, got {len(clips)}",
            "Arrange at least two video clips before exporting through the assembler.",
            next_command="wgp editor export --project <project> --out <export.json> --json",
        )
    return clips


def _director_request(project: EditorProject, clips: list[Clip]) -> DirectorRequest:
    source_by_id = {source.asset_id: source for source in project.sources}
    source_ids = [source_by_id[clip.source_id].sha256 for clip in clips if clip.source_id]
    prompt = (
        f"{project.name}: ordered pinned visuals "
        + ", ".join(f"{clip.label}={clip.clip_id}" for clip in clips)
        + f"; source_hashes={','.join(source_ids)}"
    )
    return DirectorRequest(
        schema_version="wangp-dspy.director-request/v1",
        mode=DirectorMode.prompt,
        title=project.name,
        prompt=prompt,
        pacing=PacingControl(strategy="even", target_duration_s=sum(clip.timeline_duration_s for clip in clips), clip_count=len(clips)),
        review=ReviewControl(mode=ReviewMode.manual, manual_checkpoint_required=True, reviewer=project.reviewer),
        recipe_seed=int(project_sha256(project)[:8], 16) % 2_147_483_647,
    )


def _shot_plan(project: EditorProject, clip: Clip) -> ShotPlan:
    source = next(item for item in project.sources if item.asset_id == clip.source_id)
    brief = RenderBrief(
        subject=f"pinned source {source.sha256[:12]} clip {clip.clip_id} {clip.label}",
        motion="pinned visual continues forward in continuous time",
        camera=f"{clip.label} medium framing with stable perspective",
        style="consistent observational film texture with restrained color",
    )
    decision = ProfileDecision(
        model="h3",
        resolution="720p",
        shot_length_frames=56,
        seed_policy="fixed_per_story",
        wangp_profile="profile3",
    )
    return ShotPlan(
        brief=brief,
        decision=decision,
        terminal_state="pinned visual continues",
        declared_deviations=(f"editor_decision={project.revision}",),
    )


def _assemble(project: EditorProject, clips: list[Clip]) -> AssembledChain:
    return MultiShotAssembler().assemble(tuple(_shot_plan(project, clip) for clip in clips))


def export_project(store: ProjectStore, project: EditorProject | None = None) -> dict[str, Any]:
    selected = store.load().project if project is None else project
    sources = store.verify_sources(selected)
    clips = _video_clips(selected)
    request = _director_request(selected, clips)
    director_plan = compile_director_request(request).mapping()
    assembled = _assemble(selected, clips)
    payload: dict[str, Any] = {
        "schema_version": EXPORT_SCHEMA,
        "project_sha256": project_sha256(selected),
        "source_manifest": {source.asset_id: source.sha256 for source in sources},
        "tracks": [
            {
                "track_id": track.track_id,
                "kind": track.kind.value,
                "order": track.order,
                "clip_ids": [clip.clip_id for clip in track.clips],
            }
            for track in sorted(selected.tracks, key=lambda item: item.order)
        ],
        "director": {
            "import": DIRECTOR_IMPORT,
            "request": request.model_dump(mode="json"),
            "plan": director_plan,
            "invoked": True,
        },
        "assembly": {
            "import": ASSEMBLER_IMPORT,
            "invoked": True,
            "continuity_digest": assembled.continuity_digest,
            "clip_ids": [clip.clip_id for clip in clips],
        },
        "queue_contract": {
            "import": QUEUE_IMPORT,
            "invoked_on_export_command": False,
            "state": "pending",
            "renderer_admission_unchanged": True,
        },
        "summary": {
            "gpu_work": False,
            "host_contact": False,
            "media_generated": False,
            "generated_media_reviewed": False,
            "non_destructive": True,
        },
    }
    return payload


def write_export(payload: Mapping[str, Any], destination: str | Path) -> Path:
    output = Path(destination).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = output.parent / f".{output.name}.{os.urandom(8).hex()}.tmp"
    try:
        staging.write_text(
            json.dumps(dict(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        os.replace(staging, output)
    finally:
        staging.unlink(missing_ok=True)
    return output


def enqueue_export(payload: Mapping[str, Any], export_path: str | Path, database: str | Path) -> str:
    from services.jobs.queue import JobQueue

    output = Path(export_path).expanduser().resolve()
    queue_path = Path(database).expanduser().resolve()
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    queue = JobQueue(queue_path)
    try:
        return queue.submit(
            plan_ref=str(output),
            clips=[{
                "kind": "editor_export",
                "status": "planned",
                "editor_export_sha256": payload["project_sha256"],
                "director_request_sha256": payload["director"]["plan"]["request_sha256"],
                "assembly_continuity_digest": payload["assembly"]["continuity_digest"],
                "gpu_work": False,
                "host_contact": False,
                "media_generated": False,
            }],
        )
    finally:
        queue.close()


__all__ = ["EXPORT_SCHEMA", "enqueue_export", "export_project", "write_export"]
