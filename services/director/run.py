"""Repo-owned DirectorRun orchestration for a disposable continuation film.

This is the narrow production seam between creative planning and the durable
jobs queue.  It owns premise resolution, exact six-cut/grid-aligned chain
planning, dataset-run emission, and job submission; rendering remains in
``JobExecutor``/``WanGPAdapter.render_for_job``.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import hashlib
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
    media_manifest: dict


def _canonical_path(value, *, label: str) -> str:
    """Return a stable path identity for media-contract comparisons."""
    if not isinstance(value, (str, Path)) or not str(value).strip():
        raise DirectorRunError(f"{label}: non-empty path is required")
    return str(Path(value).expanduser().resolve())


def _canonical_speaker(value, *, by_name: Mapping[str, dict],
                       by_sn: Mapping[str, dict], label: str) -> str:
    """Resolve a manifest speaker name or SN to the premise name."""
    if not isinstance(value, str) or not value.strip():
        raise DirectorRunError(f"{label}: speaker is required")
    if value in by_name:
        return value
    if value in by_sn:
        return str(by_sn[value]["name"])
    raise DirectorRunError(
        f"{label}: speaker {value!r} is not in premise roster "
        f"{sorted(by_name)}")


def _sha256_file(path: str, *, label: str) -> str:
    """Hash a registered visual anchor without accepting a missing file."""
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    except OSError as exc:
        raise DirectorRunError(
            f"{label}: style anchor is unreadable: {path!r}") from exc


def _validate_media_coherence(*, premise: Premise,
                              script_lines: Sequence[dict],
                              audio_paths: Sequence[str],
                              plate_paths: Sequence[str | Sequence[str]],
                              media_manifest: Mapping | None) -> dict:
    """Validate the premise/script/audio/plate identity contract.

    A file path alone cannot prove who is pictured or speaking.  Production
    runs therefore carry an explicit media manifest that binds every turn and
    plate role to the resolved premise roster.  Validation happens before
    chain planning or queue submission, so an omitted or mismatched
    registration fails closed instead of rendering a coherent wrong film.
    """
    if not isinstance(media_manifest, Mapping):
        raise DirectorRunError(
            "media_manifest: required for production runs; it must bind "
            "premise_id, named plates, and per-turn audio speakers")
    if media_manifest.get("premise_id") != premise.id:
        raise DirectorRunError(
            "media_manifest.premise_id mismatch: expected "
            f"{premise.id!r}, got {media_manifest.get('premise_id')!r}")

    roster = [dict(c) for c in premise.characters]
    by_name = {str(c["name"]): c for c in roster}
    by_sn = {str(c["sn_tag"]): c for c in roster}
    names = list(by_name)

    raw_plates = media_manifest.get("plates")
    if not isinstance(raw_plates, Mapping):
        raise DirectorRunError(
            "media_manifest.plates: mapping with anchor and one path per "
            "premise character is required")
    expected_plate_keys = {"anchor", *names}
    if set(raw_plates) != expected_plate_keys:
        raise DirectorRunError(
            "media_manifest.plates keys must be exactly "
            f"{sorted(expected_plate_keys)}; got {sorted(raw_plates)}")
    canonical_plates = {
        key: _canonical_path(raw_plates[key], label=f"plates.{key}")
        for key in expected_plate_keys
    }

    # Style identity is separate from character identity.  When a premise
    # registers a master plate hash, production must bind that exact hash and
    # use matching anchor bytes. Legacy premises without style_ref remain
    # valid until their manifests are upgraded; stray refs are rejected.
    registered_style_ref = str(getattr(premise, "style_ref", "") or "").strip()
    declared_style_ref = str(media_manifest.get("style_ref", "") or "").strip()
    if registered_style_ref:
        if declared_style_ref != registered_style_ref:
            raise DirectorRunError(
                "media_manifest.style_ref mismatch: expected registered "
                f"style anchor {registered_style_ref!r}, got "
                f"{declared_style_ref!r}")
        actual_style_ref = _sha256_file(
            canonical_plates["anchor"], label="plates.anchor")
        if actual_style_ref != registered_style_ref:
            raise DirectorRunError(
                "plates.anchor does not match the premise's registered "
                f"style_ref {registered_style_ref!r}; got {actual_style_ref!r}")
    elif declared_style_ref:
        raise DirectorRunError(
            "media_manifest.style_ref is present but the premise has no "
            "registered style anchor")

    # Match the actual refs emitted into each job.  For per-cut pairs, the
    # second ref must be the silent character's declared identity plate.
    if not plate_paths:
        raise DirectorRunError("plate_paths: cannot be empty")
    if isinstance(plate_paths[0], (list, tuple)):
        if len(plate_paths) != len(script_lines):
            raise DirectorRunError(
                "plate_paths: one [anchor, silent_face] pair per script turn "
                "is required")
        for index, (line, pair) in enumerate(zip(script_lines, plate_paths), 1):
            if len(pair) != 2:
                raise DirectorRunError(
                    f"plate_paths[{index}]: expected [anchor, silent_face]")
            if _canonical_path(pair[0], label=f"plate_paths[{index}].anchor") \
                    != canonical_plates["anchor"]:
                raise DirectorRunError(
                    f"plate_paths[{index}].anchor does not match the media "
                    "manifest anchor")
            speaker = _canonical_speaker(
                line.get("speaker"), by_name=by_name, by_sn=by_sn,
                label=f"script_lines[{index}]")
            silent = [name for name in names if name != speaker]
            if len(silent) != 1:
                raise DirectorRunError(
                    "media coherence currently requires exactly one silent "
                    f"character per turn; turn {index} has speaker {speaker!r}")
            if _canonical_path(pair[1], label=f"plate_paths[{index}].silent") \
                    != canonical_plates[silent[0]]:
                raise DirectorRunError(
                    f"plate_paths[{index}].silent does not match declared "
                    f"plate identity for {silent[0]!r}")
    else:
        if len(plate_paths) != len(names) + 1:
            raise DirectorRunError(
                "plate_paths: flat form must be [anchor, one plate per "
                "premise character in roster order]")
        actual = [_canonical_path(p, label=f"plate_paths[{i}]")
                  for i, p in enumerate(plate_paths)]
        expected = [canonical_plates["anchor"]] + [
            canonical_plates[name] for name in names]
        if actual != expected:
            raise DirectorRunError(
                "plate_paths do not match media_manifest plate identities "
                "or premise roster order")

    raw_audio = media_manifest.get("audio")
    if not isinstance(raw_audio, (list, tuple)) \
            or len(raw_audio) != len(audio_paths):
        raise DirectorRunError(
            "media_manifest.audio: one {path, speaker} entry per audio turn "
            "is required")
    canonical_audio = []
    for index, (given_path, entry, line) in enumerate(
            zip(audio_paths, raw_audio, script_lines), 1):
        if not isinstance(entry, Mapping):
            raise DirectorRunError(
                f"media_manifest.audio[{index}]: expected an object")
        given = _canonical_path(given_path, label=f"audio_paths[{index}]")
        declared = _canonical_path(
            entry.get("path"), label=f"media_manifest.audio[{index}].path")
        if given != declared:
            raise DirectorRunError(
                f"audio turn {index} path does not match media manifest")
        script_speaker = _canonical_speaker(
            line.get("speaker"), by_name=by_name, by_sn=by_sn,
            label=f"script_lines[{index}]")
        audio_speaker = _canonical_speaker(
            entry.get("speaker"), by_name=by_name, by_sn=by_sn,
            label=f"media_manifest.audio[{index}]")
        if script_speaker != audio_speaker:
            raise DirectorRunError(
                f"audio turn {index} speaker {audio_speaker!r} does not "
                f"match script speaker {script_speaker!r}")
        canonical_audio.append({"path": declared, "speaker": audio_speaker})

    return {
        "premise_id": premise.id,
        "style_ref": registered_style_ref,
        "plates": canonical_plates,
        "audio": canonical_audio,
        "characters": [
            {"name": str(c["name"]), "sn_tag": str(c["sn_tag"])}
            for c in roster
        ],
    }


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
             plate_paths: Sequence[str | Sequence[str]],
             media_manifest: Mapping | None = None,
             expected_cuts: int = 6,
            recipe_name: str = "production",
            seed_override: int | None = None,
            durations_s: Sequence[float] | None = None,
            emit_record: bool = True) -> DirectorRunPlan:
        """Build the strict ContinuationExtras manifest (no GPU/subprocess).

        ``media_manifest`` is mandatory in practice (``None`` is rejected)
        because premise/audio/plate identity must be checked before queueing.
        """
        if isinstance(expected_cuts, bool) or not isinstance(expected_cuts, int) \
                or expected_cuts <= 0:
            raise DirectorRunError("expected_cuts: positive integer required")
        if len(script_lines) != expected_cuts:
            raise DirectorRunError(
                f"script_lines: expected exactly {expected_cuts} cuts, "
                f"got {len(script_lines)}")
        if len(audio_paths) != expected_cuts:
            raise DirectorRunError(
                f"audio_paths: {expected_cuts} single-speaker turn wavs "
                "are required")
        if not plate_paths:
            raise DirectorRunError(
                "plate_paths: anchor plus at least one silent-character face ref required")
        if isinstance(plate_paths[0], (list, tuple)):
            if len(plate_paths) != expected_cuts or any(
                    len(pair) != 2 for pair in plate_paths):
                raise DirectorRunError(
                    "plate_paths: per-cut form must contain "
                    "[anchor, silent_face] pairs for every cut")
        elif len(plate_paths) < 2:
            raise DirectorRunError(
                "plate_paths: anchor plus at least one silent-character face ref required")
        if durations_s is None:
            cut_duration_s = CONTINUATION_FRAMES_MIN / 24.0
            durations = [cut_duration_s] * expected_cuts
        else:
            if len(durations_s) != expected_cuts:
                raise DirectorRunError(
                    "durations_s: one duration is required per cut")
            try:
                durations = [float(value) for value in durations_s]
            except (TypeError, ValueError) as exc:
                raise DirectorRunError(
                    "durations_s: values must be numeric") from exc
            if any(value <= 0 for value in durations):
                raise DirectorRunError(
                    "durations_s: values must be positive")
        characters = [dict(c) for c in self.premise.characters]
        canonical_media = _validate_media_coherence(
            premise=self.premise, script_lines=script_lines,
            audio_paths=audio_paths, plate_paths=plate_paths,
            media_manifest=media_manifest)
        try:
            chain = build_chain_plan(
                script_lines, characters, durations,
                audio_paths=audio_paths, continuation_mode=True,
                seed_override=seed_override)
            clips = tuple({**clip, "premise_id": self.premise.id,
                           "media_manifest": canonical_media}
                          for clip in emit_render_manifest(
                              chain, plate_paths=plate_paths,
                              recipe_name=recipe_name))
        except Exception as exc:
            raise DirectorRunError(f"continuation planning failed: {exc}") from exc
        # A strict continuation manifest has one render job per dialogue turn.
        if len(clips) != expected_cuts:
            raise DirectorRunError(
                f"continuation plan did not emit {expected_cuts} jobs")
        plan = DirectorRunPlan(self.run_id, self.premise.id, chain, clips,
                               canonical_media)
        if emit_record:
            self.emit_plan_record(plan, durations_s=durations)
        return plan

    def emit_plan_record(self, plan: DirectorRunPlan,
                         *, durations_s: Sequence[float] | None = None) -> None:
        """Append the planned lifecycle record after preflight/staging."""
        if not isinstance(plan, DirectorRunPlan):
            raise DirectorRunError("plan: expected a DirectorRunPlan")
        if self.dataset_run_path is None:
            return
        if durations_s is None:
            durations = [CONTINUATION_FRAMES_MIN / 24.0] * len(plan.clips)
        else:
            durations = [float(value) for value in durations_s]
            if len(durations) != len(plan.clips) or any(
                    value <= 0 for value in durations):
                raise DirectorRunError(
                    "durations_s: one positive duration is required per clip")
        append_dataset_run(
            self.dataset_run_path, run_id=self.run_id, status="planned",
            payload={"premise_id": self.premise.id,
                     "clip_count": len(plan.clips),
                     "durations_s": durations,
                     "media_manifest": plan.media_manifest})

    @staticmethod
    def submit(plan: DirectorRunPlan, queue) -> list[str]:
        """Submit each planned clip with a durable previous-cut dependency."""
        if not isinstance(plan, DirectorRunPlan):
            raise DirectorRunError("plan: expected DirectorRunPlan")
        ids = []
        previous = None
        for clip in plan.clips:
            if clip.get("premise_id") != plan.premise_id:
                raise DirectorRunError(
                    "plan clip premise_id does not match the DirectorRun "
                    "premise; refusing queue submission")
            if clip.get("media_manifest") != plan.media_manifest:
                raise DirectorRunError(
                    "plan clip media_manifest does not match the validated "
                    "DirectorRun manifest; refusing queue submission")
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
