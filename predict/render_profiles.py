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

from predict.job_config import SCRIPT_SEPARATOR, WanGPJobConfig
from predict.prompt_director import RenderBrief
from predict.profile_selector import ProfileDecision

# HOST TRUTH (operator audit 2026-09-01; live smoke 2026-09-02): wgp
# rejected 'ref2va_lip_sync' as a model_type — the 3090 Wan2GP
# handler exposes only 'minimax_h3_ref2va' and
# 'minimax_h3_ref2va_pruned'. This MUST stay in lockstep with
# host.wangp_adapter.REF2VA_MODEL_TYPE (a cross-check test enforces
# no 'ref2va_lip_sync' string is ever EMITTED as a model_type).
from host.wangp_adapter import REF2VA_MODEL_TYPE  # noqa: E402
REF2VA_MIN_SHOT_S = 4.0
REF2VA_MAX_SHOT_S = 15.0


from predict.audio_dataplane import (  # noqa: E402  (WD-a1d9)
    AudioGuideProvenance, AudioPolicy, Ref2VAAudioQC,
)


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
                       audio_guide: Optional[str] = None,
                       audio_provenance: Optional[AudioGuideProvenance] = None,
                       audio_policy: Optional[AudioPolicy] = None,
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
        # WD-a1d9: audio data plane — audio_guide readable at submit
        # (same treatment as image_refs), provenance required+typed,
        # policy default-constructed (discard=True, source_master).
        if not audio_guide or not str(audio_guide).strip():
            raise ProfileError(
                "Ref2VA requires audio_guide (path to the audio guide "
                "asset, readable at submit) — got none")
        if not os.path.isfile(audio_guide):
            raise ProfileError(
                f"Ref2VA audio_guide not readable at submit: {audio_guide}")
        if audio_provenance is None:
            raise ProfileError(
                "Ref2VA requires audio_provenance "
                "(AudioGuideProvenance) — got None")
        if not isinstance(audio_provenance, AudioGuideProvenance):
            raise ProfileError(
                "audio_provenance must be an AudioGuideProvenance, got "
                f"{type(audio_provenance).__name__}")
        if audio_policy is None:
            audio_policy = AudioPolicy(
                remux_window=tuple(audio_provenance.keeper_window_s))
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
        # LIVE SMOKE BOUNDARY (fix 11): <Subject N> tokens belong to
        # the RENDERER-LEVEL TEMPLATE ONLY — the runtime contiguity
        # check rejects them (no <Subject N> is ever resolvable from
        # a flattened manifest prompt). <Picture N>/<Audio N> are the
        # sanctioned brief-level tokens (validated above); token
        # EXPANSION of <Subject N> happens in the renderer template,
        # after this seam hands the text over. A brief carrying
        # <Subject N> raises here, before the render.
        _BRIEF_TOKEN_RE = re.compile(r"<Subject\s+\d+>", re.I)
        for b in briefs:
            for _f in (b.subject, b.motion):
                m = _BRIEF_TOKEN_RE.search(_f or "")
                if m:
                    raise ProfileError(
                        f"Ref2VA brief text carries {m.group(0)!r} — "
                        "<Subject N> tokens belong to the renderer-"
                        "level template ONLY, never the brief text "
                        "the runtime hands to the render (the runtime "
                        "contiguity check rejects them)")
        frames = int(round(shot_duration_s * 24))
        cfg = WanGPJobConfig(
            model_type=REF2VA_MODEL_TYPE,
            script=SCRIPT_SEPARATOR.join(
                f"{b.subject}. {b.motion}." for b in briefs),
            prompt="ref2va",
            width=480, height=832,
            frames_per_shot=max(frames, 96),
            force_fps="24",
        )
        # WD-l5bx review strong-rec: image_refs/audio_prompt_type ride
        # INSIDE the settings build (``extra``) and rule 4 (flat JSON)
        # is explicitly scoped to the GENERIC lane — the Ref2VA reader
        # consumes a list of image paths, a sanctioned non-scalar
        # extension of the wgp settings schema, not a rule violation.
        #
        # LIVE SMOKE fix 10: video_prompt_type "I" and
        # multi_prompts_gen_type "FG" must ride in extra= — the
        # WanGPJobConfig dataclass has NO such fields, so passing them
        # to the ctor is silently dropped and wgp runs with wrong
        # prompt-shape defaults.
        return cfg.to_settings_doc(
            flat=False,
            extra={"image_refs": list(image_refs),
                   "audio_prompt_type": "A",
                   "audio_guide": str(audio_guide),
                   "audio_provenance": audio_provenance.to_dict(),
                   "audio_policy": audio_policy.to_dict(),
                   "audio_qc": Ref2VAAudioQC.empty().to_dict(),
                   "video_prompt_type": "I",
                   "multi_prompts_gen_type": "FG"})
