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

from predict.job_config import (
    CONTINUATION_FRAMES_MIN,
    normalize_continuation_frame_count,
    SCRIPT_SEPARATOR,
    WanGPJobConfig,
)
from predict.prompt_director import RenderBrief
from predict.profile_selector import ProfileDecision

# HOST TRUTH (operator audit 2026-09-01; live smoke 2026-09-02): wgp
# rejected 'ref2va_lip_sync' as a model_type — the 3090 Wan2GP
# handler exposes only 'minimax_h3_ref2va' and
# 'minimax_h3_ref2va_pruned'. This MUST stay in lockstep with
# host.wangp_adapter.REF2VA_MODEL_TYPE (a cross-check test enforces
# no 'ref2va_lip_sync' string is ever EMITTED as a model_type).
from predict.model_types import REF2VA_MODEL_TYPE  # noqa: E402
# NIGHT TWO (2026-09-03, live-verified): the 56f floor-truth clip is
# 2.3333...s. plan_to_clips wires durations as round(frames/24, 3) —
# 2.333 — and a 4.0 floor rejected it. Floor at 2.33 (below any 3dp
# rounding of 56/24) so the minimum WanGP-legal shot passes.
REF2VA_MIN_SHOT_S = 2.33
REF2VA_CONTINUATION_MIN_SHOT_S = CONTINUATION_FRAMES_MIN / 24.0
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
    """Second profile: image-refs + explicit audio-carrier 'A' lane.

    Contract (spec): image_refs present+readable at submit;
    audio_prompt_type 'A' typed; guide duration matches the ordinary
    shot exactly (continuations allow the typed +0.1s envelope);
    2.33s ordinary / 56/24s continuation floor and 15s cap;
    <Picture N>/<Audio N> token contiguity
    (every referenced index has a ref, numbering contiguous from 1).
    The emitted envelope is a single-cut job without multishot script
    fields, and ``ref2va_wire_settings`` enforces the wire shape. Native H3
    output is the only validated carrier.
    """

    name = "ref2va"

    # SETTINGS PARITY pins (single source with the proven recipe):
    # FPS is the frame math the recipe module uses; RECIPE_SEED is the
    # h3_recipe pin (imported, not duplicated — a recipe change
    # propagates here).
    FPS = 24
    from services.director.renderers.h3_recipe import SEED as _RECIPE_SEED  # noqa: E402
    RECIPE_SEED = _RECIPE_SEED

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
                      speaker_manifest: Optional[dict] = None,
                       speaker_prompt: Optional[str] = None,
                       legacy_prompt: Optional[str] = None,
                       seed: Optional[int] = None,
                       audio_length_frames: Optional[int] = None,
                       image_start: Optional[str] = None,
                       video_prompt_type: str = "I",
                       continuation: bool = False,
                       width: int = 480,
                       height: int = 832,
                       profile: int = 3,
                       recipe_name: str = "production",
                       **kw) -> dict:
        continuation = bool(continuation or
                           getattr(decision, "continuation", False))
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
        import math
        if not math.isfinite(float(guide_duration_s)) or not math.isfinite(float(shot_duration_s)):
            raise ProfileError("guide/shot duration must be finite")
        if not continuation and abs(float(guide_duration_s) - float(shot_duration_s)) > 1e-9:
            raise ProfileError(f"guide duration {guide_duration_s}s != shot duration {shot_duration_s}s")
        if float(guide_duration_s) < 2.0 or float(guide_duration_s) > float(shot_duration_s) + 0.1:
            raise ProfileError(
                f"Ref2VA guide duration {guide_duration_s}s outside the 2s minimum / shot "
                f"duration {shot_duration_s}s envelope (+0.1s tolerance)")
        # The ordinary Ref2VA profile keeps the proven 2.33s floor. The
        # continuation recipe uses the same H3 grid at its 56f minimum.
        min_shot_s = (REF2VA_CONTINUATION_MIN_SHOT_S
                      if continuation else REF2VA_MIN_SHOT_S)
        # 2.33-15s cap for both continuation and ordinary Ref2VA.
        if not (min_shot_s <= float(shot_duration_s)
                <= REF2VA_MAX_SHOT_S):
            raise ProfileError(
                f"Ref2VA shot duration {shot_duration_s}s outside the "
                f"{min_shot_s}-{REF2VA_MAX_SHOT_S}s cap")
        # WD-a1d9 audio data plane, updated for the native contract:
        # audio_guide readable at submit (same treatment as image_refs),
        # provenance required+typed, and policy defaults to preserving
        # generated audio (discard=False) with its provenance window.
        # Explicit discard=True remux belongs to non-Ref2VA external
        # audio lanes, not this profile.
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
                discard_rendered_audio=False, remux_window=tuple(audio_provenance.keeper_window_s))
        if audio_policy.discard_rendered_audio is not False:
            raise ProfileError("Ref2VA requires native audio; discard/remux is not this recipe")
        if continuation:
            if speaker_manifest is not None:
                from predict.speaker_manifest import (
                    SpeakerManifest, SpeakerManifestError,
                )
                try:
                    SpeakerManifest.from_dict(speaker_manifest)
                except SpeakerManifestError as exc:
                    raise ProfileError(str(exc)) from exc
        # token contiguity
        text = " ".join(b.subject + " " + b.motion for b in briefs)
        seen: dict = {"Picture": [], "Audio": []}
        for m in self._TOKEN_RE.finditer(text):
            seen[m.group(1).title()].append(int(m.group(2)))
        for kind, idxs in seen.items():
            n_refs = (len(image_refs) if kind == "Picture" else 1)
            # LIVE FIX (2026-09-03, roadmap-47 item 8): repeated
            # mentions of the SAME ref ("... from <Picture 1> ... from
            # <Picture 1> ...") are legal prompt grammar — dedupe
            # before the contiguity check ([1,1,1] is contiguous).
            unique = sorted(set(idxs))
            for i in unique:
                if i < 1 or i > n_refs:
                    raise ProfileError(
                        f"Ref2VA script references <{kind} {i}> but "
                        f"only {n_refs} {kind.lower()} "
                        f"{'ref' if n_refs == 1 else 'refs'} exist — "
                        "referenced indices must be contiguous from 1")
            if unique and unique != list(range(1, max(unique) + 1)):
                raise ProfileError(
                    f"Ref2VA <{kind} N> numbering not contiguous from "
                    f"1: {unique}")
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
        # Ref2VA uses the single-cut handler grid, never the multishot floor.
        video_length = int(round(shot_duration_s * self.FPS))
        requested_frames = video_length
        aligned = normalize_continuation_frame_count(video_length)
        if continuation and video_length != aligned:
            raise ProfileError(
                f"Ref2VA duration must be grid-aligned (5+17k); got {video_length}f; use {aligned}f")
        video_length = aligned
        if continuation and not image_start:
            raise ProfileError("Ref2VA continuation requires image_start")
        guide_frames = int(round(float(guide_duration_s) * self.FPS))
        if audio_length_frames is not None and int(audio_length_frames) != guide_frames:
            raise ProfileError(
                f"Ref2VA audio guide length {audio_length_frames}f != declared guide duration {guide_frames}f")
        # speaker template: required carrier of the real prompt text.
        # Brief subject+motion is NOT sufficient (verified live) — the
        # "(SN) says:" / listener mouth-closed structure must reach
        # WanGP's prompt field. Fallback is a deterministic derivation
        # from the briefs so the seam never ships the bare tag.
        if legacy_prompt is not None:
            prompt_text = str(legacy_prompt)
            if not prompt_text.strip():
                raise ProfileError(
                    "legacy_prompt must be nonempty when supplied")
        elif speaker_prompt is not None:
            prompt_text = str(speaker_prompt)
            if not prompt_text.strip():
                raise ProfileError(
                    "Ref2VA speaker_prompt must be nonempty when "
                    "supplied — never an empty carrier")
            if continuation:
                from predict.continuation_lane import (
                    validate_picture_n_speaker_prompt,
                )
                try:
                    validate_picture_n_speaker_prompt(prompt_text)
                except Exception as exc:
                    raise ProfileError(str(exc)) from exc
        else:
            head = SCRIPT_SEPARATOR.join(
                f"{b.subject}. {b.motion}." for b in briefs)
            prompt_text = (
                "Summary: [reference generation] All subjects retain "
                "their exact identities from their reference "
                f"pictures. {head} The speaker speaks with lively "
                "animated mouth movement, in sync with the audio "
                "guide. Listeners listen, mouths closed.")
        # (3) seed defaulted to 42; the recipe pins 904. The caller's
        #     seed wins; the DEFAULT is the recipe pin (imported from
        #     h3_recipe — single source).
        effective_seed = (int(seed) if seed is not None
                          else self.RECIPE_SEED)
        # Job metadata stays in the local settings/manifest envelope. The
        # transport serializes only ref2va_wire_settings() to WanGP.
        doc = {
            "model_type": REF2VA_MODEL_TYPE,
            "prompt": prompt_text,
            "resolution": f"{int(width)}x{int(height)}",
            "seed": effective_seed,
            "num_inference_steps": 20,
            "force_fps": "24",
            "image_refs": list(image_refs),
            "audio_prompt_type": "A",
            "audio_guide": str(audio_guide),
            "audio_guide2": None,
            "image_prompt_type": "S" if image_start else "I",
            "image_start": str(image_start) if image_start else None,
            "video_prompt_type": str(video_prompt_type),
            "video_source": None,
            "video_guide": None,
            "keep_frames_video_source": "",
            "video_length": video_length,
            "requested_frames": requested_frames,
            "audio_provenance": audio_provenance.to_dict(),
            "audio_policy": audio_policy.to_dict(),
            "audio_carrier": "native_h3",
            "audio_qc": Ref2VAAudioQC.empty().to_dict(),
            "profile": int(profile),
            "recipe_name": recipe_name,
        }
        if speaker_manifest is not None:
            doc["speaker_manifest"] = speaker_manifest
        if recipe_name == "golden_v3":
            from predict.v3_recipe import V3_RECIPE
            if len(image_refs) != 2 or image_start != image_refs[0]:
                raise ProfileError("golden_v3 requires [seed, silent_face] references")
            if int(profile) != V3_RECIPE.profile:
                raise ProfileError("golden_v3 requires profile 2")
            doc["resolution"] = V3_RECIPE.resolution
            # These keys were absent in the recovered baseline. Inherit
            # pinned WanGP handler defaults, not multishot overrides.
            doc.pop("num_inference_steps")
            doc.pop("force_fps")
            doc["recipe_version"] = V3_RECIPE.version
        from predict.ref2va_settings import ref2va_wire_settings
        ref2va_wire_settings(doc)
        return doc
