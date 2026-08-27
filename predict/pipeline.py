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

import dspy

from predict.prompt_director import PromptDirector, RenderBrief
from predict.profile_selector import ProfileSelector, ProfileDecision
from predict.assembler import MultiShotAssembler, ShotPlan, AssembledChain
from evaluate.render_qc import RenderQC, QCVerdict
from host.wangp_adapter import WanGPAdapter, RenderResult


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
    verdicts: List[QCVerdict] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
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
                 creative_lm=None):
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

    def forward(self, intent: str, *, n_shots: int = 1) -> PipelineResult:
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
                    ShotPlan(brief=b, decision=d, terminal_state="")
                    for b, d in zip(result.briefs, result.decisions)]
                result.chain = self.assembler.assemble(shots)
            except Exception as exc:
                raise PipelineStageError(
                    "assemble", f"chain validation failed: {exc}", exc)
            record("assemble", "chain validated")

        # ── stage 4: render (adapter injected; optional for dry runs) ──
        if self.adapter is not None:
            try:
                render = self.adapter.render(
                    result.briefs, result.decisions[0])
                result.render = render
            except Exception as exc:
                raise PipelineStageError(
                    "render", f"WanGP render failed: {exc}", exc)
            record("render",
                   f"{len(render.video_paths)} video(s)")

            # ── stage 5: QC every video ─────────────────────────────
            if self.qc_factory is not None:
                qc = self.qc_factory(self.genre)
                for brief, video in zip(result.briefs,
                                        result.render.video_paths):
                    try:
                        verdicts = qc.run(brief=brief,
                                          decision=result.decisions[0],
                                          video=video)
                        result.verdicts.append(verdicts)
                    except Exception as exc:
                        raise PipelineStageError(
                            "qc", f"QC failed on {video!r}: {exc}", exc)
                record("qc", f"{len(result.verdicts)} verdict(s)")

        return result
