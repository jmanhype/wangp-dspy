"""Pipeline — the top-level dspy.Module chaining every stage.

WD-pt60 (j9nx-1): intent -> briefs -> profile -> assemble -> render ->
QC in ONE call, with typed failures at each stage boundary. This is
the module the whole epic (WD-j9nx) is named for: the stages existed
and were individually tested; this wires them so the WHOLE program is
one traceable, optimizable unit (per the dspy multi-stage pattern —
forward() composes sub-modules; optimizers see the chain, not leaves).

Failure contract (epic AC #2): every stage boundary raises
PipelineStageError naming the stage — no silent no-ops (the WD-yyj9
class of bug is structurally excluded here).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional, Sequence
from types import SimpleNamespace

import dspy

from predict.prompt_director import PromptDirector, RenderBrief
from predict.profile_selector import ProfileSelector, ProfileDecision
from predict.assembler import MultiShotAssembler, ShotPlan, AssembledChain
from predict.caption import CaptionSpec, build_captions, \
    CaptionValidationError
from evaluate.render_qc import RenderQC, QCVerdict
from host.wangp_adapter import WanGPAdapter, RenderResult
from services.jobs.compile_guard import assert_not_compiling


class PipelineStageError(Exception):
    """A pipeline stage failed; `stage` names which boundary."""

    def __init__(self, stage: str, message: str,
                 cause: Optional[Exception] = None):
        self.stage = stage
        super().__init__(f"[{stage}] {message}")
        if cause is not None:
            self.__cause__ = cause


@dataclass
class PipelineResult:
    """One call's full artifact chain (epic AC #1)."""
    briefs: List[RenderBrief]
    decisions: List[ProfileDecision]
    chain: Optional[AssembledChain] = None
    render: Optional[RenderResult] = None
    # Per-cut job/render records. The render field remains the legacy
    # first result for one-shot callers; multi-shot callers consume this.
    jobs: List[dict] = field(default_factory=list)
    renders: List[object] = field(default_factory=list)
    verdicts: List[QCVerdict] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
    # WD-obun: the caption stage's artifact (None = stage not run)
    captions: Optional[object] = None
    # replayable evidence trail: append-only (stage, note) records


class Pipeline(dspy.Module):
    """intent -> briefs -> profile -> assemble -> render -> QC.

    Sub-modules (PromptDirector, ProfileSelector) are dspy modules so
    optimizers can target them; assembler/adapter/QC-judge are logic
    and IO injected as callables — the GPU seam stays swappable for
    tests (stubbed host) and for the real 3090 (WD-mhr2).
    """

    def __init__(self, *, genre: str,
                 director=None,
                 selector=None,
                 assembler: Optional[MultiShotAssembler] = None,
                 adapter=None,
                 qc_factory: Optional[Callable] = None,
                 creative_lm=None,
                 registry=None,
                 job_builder: Optional[Callable] = None):
        """Collaborators are duck-typed by design: tests inject stubs,
        the real run injects the dspy modules + 3090 adapter. Only the
        assembler keeps a concrete default (pure logic, no IO).

        creative_lm (WD-mhr2): when set, director/selector calls run
        under dspy.settings.context(lm=creative_lm) — the hosted API
        for creative stages while the critic keeps its own LM via
        qc_factory wiring. None = whatever dspy default is configured
        (single-LM behavior, backward compatible)."""
        super().__init__()
        self.genre = genre
        self.director = director or PromptDirector()
        self.selector = selector or ProfileSelector()
        self.assembler = assembler or MultiShotAssembler()
        self.adapter = adapter
        self.qc_factory = qc_factory
        self.creative_lm = creative_lm
        # WD-c4gw: entity registry threaded to the LM brief path
        self.registry = registry
        self.job_builder = job_builder

    def forward_with_skeleton(self, intent: str, *,
                                skeleton=None) -> PipelineResult:
        """WD-gq8y sign-off checkpoint: round-1 skeleton must be
        validated AND user-approved before any stage runs. The gate
        is the FIRST thing forward() does — a Boom stub for every
        collaborator proves no stage executes (test pins this)."""
        from predict.skeleton import (require_signoff,
                                      SkeletonValidationError)
        try:
            if skeleton is not None:
                require_signoff(skeleton)
        except SkeletonValidationError as e:
            raise PipelineStageError(
                "signoff",
                f"skeleton sign-off gate refused: {e}") from e
        return self.forward(intent)

    def forward(self, intent: str, *, n_shots: int = 1,
                caption_spec: Optional[CaptionSpec] = None) -> PipelineResult:
        if not isinstance(n_shots, int) or n_shots < 1:
            raise PipelineStageError(
                "briefs", f"n_shots must be a positive int, got {n_shots!r}")
        # ── stage 0: compile guard (jobs-preflight operator ruling 2)
        # A real (non-None) adapter firing GPU work inside a dspy
        # optimizer rollout burns 3090 hours during compile. The
        # guard fires BEFORE any stage runs — see
        # services/jobs/compile_guard.py for the signal analysis.
        if self.adapter is not None:
            assert_not_compiling(
                adapter=type(self.adapter).__name__)
        result = PipelineResult(briefs=[], decisions=[])

        def record(stage: str, note: str) -> None:
            result.evidence.append(f"{stage}: {note}")

        # ── stage 1: briefs ─────────────────────────────────────────
        import contextlib

        def creative_ctx():
            # fresh per stage: dspy.settings.context yields a
            # single-use generator contextmanager
            return (dspy.settings.context(lm=self.creative_lm)
                    if self.creative_lm is not None
                    else contextlib.nullcontext())
        try:
            with creative_ctx():
                for _ in range(n_shots):
                    # backward compat: only thread registry when
                    # present — stub directors (and old callers) take
                    # no registry kwarg
                    if self.registry is not None:
                        result.briefs.append(
                            self.director(intent=intent,
                                          registry=self.registry).brief)
                    else:
                        result.briefs.append(
                            self.director(intent=intent).brief)
        except Exception as exc:
            raise PipelineStageError(
                "briefs", f"intent -> RenderBrief failed: {exc}", exc)
        record("briefs", f"{len(result.briefs)} brief(s) from intent")

        # ── stage 2: profile decisions ──────────────────────────────
        try:
            with creative_ctx():
                for brief in result.briefs:
                    result.decisions.append(
                        self.selector.from_brief(brief).decision)
        except Exception as exc:
            raise PipelineStageError(
                "profile", f"brief -> ProfileDecision failed: {exc}", exc)
        record("profile", f"{len(result.decisions)} decision(s)")

        # ── stage 3: assemble (multi-shot only) ─────────────────────
        if n_shots > 1:
            try:
                shots = [
                    ShotPlan(
                        brief=b,
                        decision=d,
                        terminal_state=f"{b.subject}, {b.motion}",
                    )
                    for b, d in zip(result.briefs, result.decisions)]
                result.chain = self.assembler.assemble(shots)
            except Exception as exc:
                raise PipelineStageError(
                    "assemble", f"chain validation failed: {exc}", exc)
            record("assemble", "chain validated")

        # ── stage 4: render (adapter injected; optional for dry runs) ──
        if self.adapter is not None:
            try:
                result.jobs = [
                    self._build_job(
                        brief, decision, index=i + 1, total=n_shots)
                    for i, (brief, decision) in enumerate(
                        zip(result.briefs, result.decisions))
                ]
                render_for_job = getattr(
                    self.adapter, "render_for_job", None)
                if callable(render_for_job):
                    if self.job_builder is None and n_shots == 1:
                        render = self.adapter.render(
                            result.briefs, result.decisions[0])
                        result.renders = [render]
                    else:
                        if self.job_builder is None and n_shots > 1:
                            raise PipelineStageError(
                                "render",
                                "multi-shot Pipeline requires a "
                                "job_builder so every cut can carry its "
                                "render_for_job asset envelope")
                        result.renders = [
                            render_for_job(job) for job in result.jobs]
                        render = SimpleNamespace(
                            video_paths=tuple(
                                self._video_path(r)
                                for r in result.renders))
                    result.render = render
                else:
                    if n_shots > 1:
                        raise PipelineStageError(
                            "render",
                            "multi-shot Pipeline requires adapter."
                            "render_for_job(); legacy render() cannot "
                            "emit per-cut jobs")
                    render = self.adapter.render(
                        result.briefs, result.decisions[0])
                    result.renders = [render]
                    result.render = render
            except Exception as exc:
                if isinstance(exc, PipelineStageError):
                    raise
                raise PipelineStageError(
                    "render", f"WanGP render failed: {exc}", exc)
            record("render",
                   f"{len(render.video_paths)} video(s)")

            # ── stage 5: QC every video ─────────────────────────────
            if self.qc_factory is not None:
                qc = self.qc_factory(self.genre)
                for brief, decision, video in zip(
                        result.briefs, result.decisions,
                        result.render.video_paths):
                    try:
                        verdicts = qc.run(brief=brief,
                                          decision=decision,
                                          video=video)
                        result.verdicts.append(verdicts)
                    except Exception as exc:
                        raise PipelineStageError(
                            "qc", f"QC failed on {video!r}: {exc}", exc)
                record("qc", f"{len(result.verdicts)} verdict(s)")

        # ── stage 6: captions (WD-obun, explicit typed stage) ──────
        if caption_spec is not None:
            if result.render is None:
                raise PipelineStageError(
                    "captions", "caption stage needs a render stage "
                    "artifact to bind to — no videos to caption")
            videos = result.render.video_paths
            if not videos:
                raise PipelineStageError(
                    "captions", "render produced no videos to caption")
            try:
                result.captions = build_captions(caption_spec, videos[0])
            except CaptionValidationError as exc:
                raise PipelineStageError(
                    "captions", f"caption spec refused: {exc}", exc)
            record("captions",
                   f"artifact {result.captions.artifact_sha[:12]} bound "
                   f"to {videos[0]}")

        return result

    def _build_job(self, brief: RenderBrief, decision: ProfileDecision,
                   *, index: int, total: int) -> dict:
        """Build a deterministic per-cut envelope for render_for_job."""
        if self.job_builder is not None:
            try:
                job = self.job_builder(
                    brief, decision, index=index, total=total)
            except TypeError:
                job = self.job_builder(brief, decision, index, total)
            if not isinstance(job, dict):
                raise PipelineStageError(
                    "render",
                    f"job_builder returned {type(job).__name__}, expected dict")
            return dict(job)
        return {
            "clip_index": index,
            "kind": "ref2va_render",
            "briefs": [brief],
            "decision": decision,
            "prompt": brief.subject,
        }

    @staticmethod
    def _video_path(render) -> str:
        path = getattr(render, "video_path", None)
        if path:
            return str(path)
        paths = getattr(render, "video_paths", ())
        if paths:
            return str(paths[0])
        raise PipelineStageError(
            "render", "render_for_job result carries no video_path")
