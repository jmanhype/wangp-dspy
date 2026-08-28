"""Render profiles — Strategy surface over job-config shaping.

WD-l5bx Task 2: H3Profile (first implementation; the adapter's H3
settings shaping extracted) and Ref2VAProfile (second; image-refs +
audio-prompt 'A' lip-sync lane). G1 boundary: Ref2VA is the ONLY
sanctioned carrier of audio_prompt_type='A' — the generic/H3 path
refuses 'A' before any render work.

Clean-room: Maestro cited as spec only (non-commercial license).
"""
from __future__ import annotations

import os
import re
from typing import List, Optional, Sequence

from predict.job_config import WanGPJobConfig
from predict.prompt_director import RenderBrief
from predict.profile_selector import ProfileDecision

REF2VA_MODEL_TYPE = "ref2va_lip_sync"
REF2VA_MIN_SHOT_S = 4.0
REF2VA_MAX_SHOT_S = 15.0


class ProfileError(ValueError):
    """Typed render-profile validation failure."""


class RenderProfile:
    """Strategy base: build_settings shapes briefs+decision into a
    flat WanGP job settings doc (validated via WanGPJobConfig)."""

    name = "base"

    def build_settings(self, briefs: Sequence[RenderBrief],
                       decision: ProfileDecision, **kw) -> dict:
        raise NotImplementedError


class H3Profile(RenderProfile):
    """First profile: the H3 multishot lane (adapter behavior moved
    here; the adapter retains its entry points and delegates)."""

    name = "h3"

    def build_settings(self, briefs: Sequence[RenderBrief],
                       decision: ProfileDecision, *,
                       audio_prompt_type: str = "",
                       **kw) -> dict:
        # G1 boundary (one sentence): Ref2VA is the only sanctioned
        # carrier of 'A' audio-prompt jobs — this generic/H3 path
        # refuses them so H3 never receives a job it cannot honor.
        if str(audio_prompt_type).strip().upper() == "A":
            raise ProfileError(
                "audio_prompt_type='A' is rejected on the generic/H3 "
                "submit path — Ref2VA is the only sanctioned carrier "
                "of audio-prompt jobs (G1)")
        from host.wangp_adapter import (build_settings as _h3_build,
                                        derive_seed)
        return _h3_build(briefs, decision)


class Ref2VAProfile(RenderProfile):
    """Second profile: image-refs + audio 'A' lip-sync lane.

    Contract (spec): image_refs present+readable at submit;
    audio_prompt_type 'A' typed; guide duration == shot duration
    (exact, typed rejection naming BOTH); 4-15s shot-duration cap;
    <Picture N>/<Audio N> token contiguity (every referenced index
    has a ref, numbering contiguous from 1).
    """

    name = "ref2va"

    _TOKEN_RE = re.compile(r"<(Picture|Audio)\s+(\d+)>", re.I)

    def build_settings(self, briefs: Sequence[RenderBrief],
                       decision: ProfileDecision, *,
                       image_refs: Optional[List[str]] = None,
                       audio_prompt_type: str = "",
                       guide_duration_s: float = 0.0,
                       shot_duration_s: float = 0.0,
                       **kw) -> dict:
        # image refs: present + readable
        if not image_refs:
            raise ProfileError(
                "Ref2VA requires image_refs (present, readable at "
                "submit) — got none")
        missing = [r for r in image_refs if not os.path.isfile(r)]
        if missing:
            raise ProfileError(
                f"Ref2VA image_refs not readable at submit: {missing}")
        # audio prompt type: 'A' required
        if str(audio_prompt_type).strip().upper() != "A":
            raise ProfileError(
                "Ref2VA requires audio_prompt_type='A' (typed field; "
                f"got {audio_prompt_type!r})")
        # guide == shot duration (G2 source; exact match)
        if abs(float(guide_duration_s) - float(shot_duration_s)) > 1e-9:
            raise ProfileError(
                f"Ref2VA guide duration {guide_duration_s}s != shot "
                f"duration {shot_duration_s}s — must match EXACTLY "
                "(G2 guide-alignment; both durations named)")
        # 4-15s cap
        if not (REF2VA_MIN_SHOT_S <= float(shot_duration_s)
                <= REF2VA_MAX_SHOT_S):
            raise ProfileError(
                f"Ref2VA shot duration {shot_duration_s}s outside the "
                f"4-15s cap ({REF2VA_MIN_SHOT_S}-{REF2VA_MAX_SHOT_S}s)")
        # token contiguity
        text = " ".join(b.subject + " " + b.motion for b in briefs)
        seen: dict = {"Picture": [], "Audio": []}
        for m in self._TOKEN_RE.finditer(text):
            seen[m.group(1).title()].append(int(m.group(2)))
        for kind, idxs in seen.items():
            n_refs = (len(image_refs) if kind == "Picture" else 1)
            for i in sorted(idxs):
                if i < 1 or i > n_refs:
                    raise ProfileError(
                        f"Ref2VA script references <{kind} {i}> but "
                        f"only {n_refs} {kind.lower()} "
                        f"{'ref' if n_refs == 1 else 'refs'} exist — "
                        "referenced indices must be contiguous from 1")
            if idxs and sorted(idxs) != list(range(1, max(idxs) + 1)):
                raise ProfileError(
                    f"Ref2VA <{kind} N> numbering not contiguous from "
                    f"1: {sorted(idxs)}")
        frames = int(round(shot_duration_s * 24))
        cfg = WanGPJobConfig(
            model_type=REF2VA_MODEL_TYPE,
            script="\n---\n".join(
                f"{b.subject}. {b.motion}." for b in briefs),
            prompt="ref2va",
            width=480, height=832,
            frames_per_shot=max(frames, 96),
            force_fps="24",
        )
        doc = cfg.to_settings_doc()
        doc["image_refs"] = list(image_refs)   # refs list at top level
        doc["audio_prompt_type"] = "A"
        return doc
