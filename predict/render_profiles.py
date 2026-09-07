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
    """Second profile: image-refs + audio 'A' lip-sync lane.

    Contract (spec): image_refs present+readable at submit;
    audio_prompt_type 'A' typed; guide duration == shot duration
    (exact, typed rejection naming BOTH); 4-15s shot-duration cap;
    <Picture N>/<Audio N> token contiguity (every referenced index
    has a ref, numbering contiguous from 1).
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
                       seed: Optional[int] = None,
                       audio_length_frames: Optional[int] = None,
                       image_start: Optional[str] = None,
                       video_prompt_type: str = "I",
                       continuation: bool = False,
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
        # guide == shot duration (G2 source; exact match)
        if abs(float(guide_duration_s) - float(shot_duration_s)) > 1e-9:
            raise ProfileError(
                f"Ref2VA guide duration {guide_duration_s}s != shot "
                f"duration {shot_duration_s}s — must match EXACTLY "
                "(G2 guide-alignment; both durations named)")
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
        # SETTINGS PARITY (live smoke 2026-09-02): the emitted doc must
        # match the proven manual recipe shape (h3_recipe), which
        # rendered grandma-perfect lip sync on the 3090. Three
        # divergences broke the pipeline smoke:
        #
        # (1) prompt carried the WanGPJobConfig profile-tag default
        #     ("ref2va") while the real speaker template went to
        #     `script` — WanGP reads `prompt`, so the model got the
        #     literal string "ref2va" and the mouth had nothing to
        #     articulate. The FULL speaker template (subject
        #     definitions + "(S1) says: <d>[English] ...</d>" +
        #     listener mouth-closed clause) must reach `prompt`.
        #     `script` is preserved for the multishot lane's own use
        #     but is never the only carrier.
        # (2) frames_per_shot snapped to the multishot grid (107 for
        #     4.042s) with no video_length — the model paced mouth
        #     motion for a different duration than the speech. The
        #     recipe's frame math is round(duration_s*24) at 24fps
        #     (h3_recipe: "frames = round(duration_s * 24)"), matching
        #     the padded audio exactly. video_length is that value —
        #     whole-frame aligned with the audio guide. frames_per_shot
        #     rides the multishot 5+17k grid for the multishot lane's
        #     own use and is never the Ref2VA authority.
        video_length = int(round(shot_duration_s * self.FPS))
        if continuation:
            aligned = normalize_continuation_frame_count(video_length)
            if video_length != aligned:
                raise ProfileError(
                    "Ref2VA continuation duration must be grid-aligned "
                    f"(5+17k, minimum {CONTINUATION_FRAMES_MIN}f); got "
                    f"{video_length}f from {shot_duration_s}s (use "
                    f"{aligned}f / {aligned / self.FPS:.3f}s)")
            if not image_start:
                raise ProfileError(
                    "Ref2VA continuation requires image_start (the "
                    "previous cut's resolved last-frame artifact)")
            requested_frames = aligned
            effective_video_length = aligned
        else:
            requested_frames = video_length
            effective_video_length = None
        # NIGHT TWO / frames handling for sub-4s shots: WanGP SNAPS the
        # requested frames onto its own grid regardless of what we emit
        # (live: 56 requested -> 107 rendered on the multishot grid).
        # The emitted `video_length` must be the SNAPPED value the
        # render will actually produce, so audio muxing matches the
        # real output duration; the caller's raw request is preserved
        # verbatim in `requested_frames` for audit/budgeting.
        from predict.job_config import normalize_frame_count
        if effective_video_length is None:
            video_length = normalize_frame_count(video_length)
        else:
            video_length = effective_video_length
        # audio-length == frame-count invariant: when the caller
        # passes the actual (padded) audio-guide frame length, it
        # MUST equal round(shot_duration_s*24) — a mismatch means the
        # guide was sliced for a different duration than the shot.
        if audio_length_frames is not None:
            if int(audio_length_frames) != int(round(shot_duration_s * 24)):
                raise ProfileError(
                    f"Ref2VA audio guide length {audio_length_frames}f "
                    f"!= shot duration frames "
                    f"{int(round(shot_duration_s * 24))}f "
                    f"({shot_duration_s}s @ {self.FPS}fps) — audio "
                    "guide and video must cover the SAME duration for "
                    "lip sync")
        # speaker template: required carrier of the real prompt text.
        # Brief subject+motion is NOT sufficient (verified live) — the
        # "(SN) says:" / listener mouth-closed structure must reach
        # WanGP's prompt field. Fallback is a deterministic derivation
        # from the briefs so the seam never ships the bare tag.
        if speaker_prompt is not None:
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
        cfg = WanGPJobConfig(
            model_type=REF2VA_MODEL_TYPE,
            script=SCRIPT_SEPARATOR.join(
                f"{b.subject}. {b.motion}." for b in briefs),
            prompt=prompt_text,
            width=480, height=832,
            frames_per_shot=(video_length if continuation
                             else max(video_length, 96)),
            force_fps="24",
            seed=effective_seed,
            snap_frames=not continuation,
            frames_floor=(CONTINUATION_FRAMES_MIN if continuation else 56),
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
        extra = {"image_refs": list(image_refs),
                   "audio_prompt_type": "A",
                   "audio_guide": str(audio_guide),
                   "image_prompt_type": "S" if continuation else "I",
                   "image_start": str(image_start) if image_start else None,
                   "video_prompt_type": str(video_prompt_type),
                   # SETTINGS PARITY (2): the recipe's frame carrier —
                   # on-grid frames from shot_duration_s, matching the
                   # padded audio exactly. video_length is the
                   # authoritative Ref2VA frame count; frames_per_shot
                   # above rides the same grid so the two never
                   # conflict.
                   "video_length": video_length,
                   "requested_frames": requested_frames,
                   "audio_provenance": audio_provenance.to_dict(),
                   "audio_policy": audio_policy.to_dict(),
                   "audio_qc": Ref2VAAudioQC.empty().to_dict(),
                   "multi_prompts_gen_type": "FG"}
        if speaker_manifest is not None:
            extra["speaker_manifest"] = speaker_manifest
        return cfg.to_settings_doc(flat=False, extra=extra)
