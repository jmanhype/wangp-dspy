"""Director wiring — script text in, proven job clips out (PR feat/director-wiring).

The director's ignition layer. Tonight's smoke renders were hand-driven;
this module is the programmatic path with ZERO hand-written job dicts.

Single template authority: prompts are built by
services/director/renderers/h3_recipe.py::_build_prompt (the proven
2026-09-01/02 template) and then SANITIZED into the runtime-cleaned
form: <Picture N>/<Subject N> tokens are replaced by (SN)-form tags
(the cleaned form is the proven one — the token form bit us twice,
see PR feat/ops-hardening which strips them again at the host boundary).

Match-cut chaining (live-proven): each cut's image_refs[0] is the
PREVIOUS cut's extracted last frame; every `re_anchor_every` cuts the
chain re-anchors on the original anchor plate to stop drift.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from services.director.renderers.h3_recipe import (
    FPS,
    SEED,
    WIDTH,
    HEIGHT,
    _build_prompt,
    _check_retention_language,
    _check_turbo_gate,
    _reject_blank,
)

__all__ = ["WiringError", "plan_to_clips", "advance_chain",
           "sanitize_runtime_tokens", "chain_last_frame_ref",
           "DEFAULT_RE_ANCHOR_EVERY"]

DEFAULT_RE_ANCHOR_EVERY = 3

# Chain-placeholder ref: resolved by advance_chain() when the previous
# cut's last frame has been extracted on the host.
chain_last_frame_ref = "chain://clip{index:04d}/last_frame"


class WiringError(ValueError):
    """Typed director-wiring rejection (bad roster, off-grid, etc.)."""


# ── runtime token sanitization (the proven cleaned form) ─────────────

def _sn_num(tag: str) -> float:
    """Numeric part of an SN tag for ordering (S2 < S10)."""
    import re as _re
    m = _re.search(r"(\d+)$", tag or "")
    return float(m.group(1)) if m else float("inf")


def sanitize_runtime_tokens(prompt: str, characters: Sequence[dict]) -> str:
    """Replace <Picture N>/<Subject N> template tokens with the
    runtime-safe (SN)-form tags keyed by the roster's sn_tag order.

    <Subject i> maps to characters[i-1]["sn_tag"] (S1, S2, ... in
    plate order, exactly the order _build_prompt emits Subjects in).
    Picture references ("<Picture 1> is the two-shot composition
    anchor") become a plain phrase. The cleaned form is the proven
    one: raw tokens in the runtime prompt have caused two bad renders.
    """
    import re

    if len(characters) < 1:
        raise WiringError("characters must be nonempty")
    if len({c["sn_tag"] for c in characters}) != len(characters):
        raise WiringError(
            "characters sn_tags must be unique — the (SN) prompt tags "
            "are keyed by sn_tag, duplicates make attribution ambiguous")
    tags = [c["sn_tag"] for c in characters]
    order = sorted(range(len(tags)), key=lambda i: _sn_num(tags[i]))
    out = prompt
    # <Subject i> -> (SN) with SN ordered by numeric part (S2 before
    # S10), i ascending — the template emits Subjects in roster order.
    for subject_no, roster_idx in enumerate(order, start=1):
        out = out.replace(f"<Subject {subject_no}>", f"({tags[roster_idx]})")
    # any residual subject/picture token of the template family
    out = re.sub(r"<Subject \d+>", "(character)", out)
    out = re.sub(r"<Picture \d+>", "the composition anchor", out)
    return out


# ── plan_to_clips ────────────────────────────────────────────────────

def plan_to_clips(
    script_lines: Sequence[Dict[str, str]],
    characters: Sequence[dict],
    plates: Dict[str, Any],
    *,
    audio_paths: Optional[Sequence[str]] = None,
    durations: Optional[Sequence[float]] = None,
    whisper_map: str = "",
    scene_staging: str = "two characters framed left and right",
    listening_detail: str = "head tilted, eyes on the speaker",
    ambience: str = "room tone, faint brazier crackle",
    loras: Optional[Sequence[str]] = None,
    re_anchor_every: int = DEFAULT_RE_ANCHOR_EVERY,
) -> List[Dict[str, Any]]:
    """Script lines -> clip dicts in the EXACT proven job shape.

    plates: {"anchor": <anchor plate path>, "<name>": <identity plate
    path>} — image_refs are [anchor, identity plates...] in roster
    order. durations default to 56/24 s per line when not supplied.
    Every prompt goes through h3_recipe's proven template builder
    (single template authority) and is sanitized to the cleaned
    runtime form before emit.
    """
    if not script_lines:
        raise WiringError("script_lines must be nonempty")
    if not characters:
        raise WiringError("characters must be nonempty")
    if re_anchor_every < 1:
        raise WiringError(
            f"re_anchor_every must be >= 1: {re_anchor_every!r}")
    name_to_sn: Dict[str, str] = {}
    for c in characters:
        try:
            name_to_sn[c["name"]] = c["sn_tag"]
        except (KeyError, TypeError) as e:
            raise WiringError(
                f"characters entries need name/sn_tag/description: {e}"
            ) from e
    if not str(plates.get("anchor", "")).strip():
        raise WiringError("plates must carry a nonempty 'anchor'")

    n = len(script_lines)
    if durations is not None and len(durations) != n:
        raise WiringError(
            f"durations ({len(durations)}) must match script length "
            f"({n}) when given")
    if audio_paths is not None and len(audio_paths) != n:
        raise WiringError(
            f"audio_paths ({len(audio_paths)}) must match script "
            f"length ({n}) when given")

    sn_order = [c["sn_tag"] for c in characters]
    # NORMALIZATION: identity plates and Subject numbering follow SN
    # TAG order (S1, S2, ... numeric), independent of roster order —
    # the template's <Subject i> is then ALWAYS (S{i}), so the
    # speaker-tag assertion is sound even for shuffled rosters.
    order = sorted(range(len(characters)), key=lambda i: _sn_num(sn_order[i]))
    character_plates = []
    for roster_idx in order:
        c = characters[roster_idx]
        path = plates.get(c["name"])
        if not str(path or "").strip():
            raise WiringError(
                f"no plate for character {c['name']!r} in plates")
        character_plates.append({"path": str(path),
                                 "description": c["description"]})

    clips: List[Dict[str, Any]] = []
    for i, line in enumerate(script_lines, start=1):
        speaker = line.get("speaker", "")
        sn = name_to_sn.get(speaker)
        if sn is None:
            raise WiringError(
                f"script line {i}: unknown speaker {speaker!r} "
                f"(roster: {sorted(name_to_sn)})")
        duration_s = (durations[i - 1] if durations is not None
                      else 56 / FPS)
        audio_path = (audio_paths[i - 1] if audio_paths is not None
                      else f"audio/clip{i:04d}.wav")
        # REF2VA frame authority (settings-parity, PR #65): frames =
        # round(duration_s * 24). The 17k+5 grid is the fl2va/multishot
        # constraint; the proven smoke job was 4.042s -> 97f.
        frames = int(round(float(duration_s) * FPS))
        if frames <= 0:
            raise WiringError(
                f"script line {i}: duration {duration_s}s rounds to a "
                f"nonpositive frame count")

        re_anchor = ((i - 1) % re_anchor_every) == 0  # cuts 1, N+1, ...
        if re_anchor:
            first_ref = str(plates["anchor"])
        else:
            first_ref = chain_last_frame_ref.format(index=i - 1)

        # SINGLE TEMPLATE AUTHORITY: h3_recipe._build_prompt (the
        # proven template), called directly so Ref2VA durations can be
        # any round(duration*24) frame count (the 4.042s/97f proven
        # case is off the 17k+5 multishot grid). All hard gates still
        # run: retention language, turbo-on-multi-ref, blank fields.
        _reject_blank(line.get("text", ""), f"script line {i} text")
        _check_retention_language(
            line.get("text", ""), scene_staging, listening_detail,
            ambience, *[p["description"] for p in character_plates])
        if loras is not None:
            _check_turbo_gate(list(loras),
                              multi_ref=len(character_plates) > 1)
        prompt_tokens = _build_prompt(
            anchor_plate=str(plates["anchor"]),
            character_plates=character_plates,
            speaker_index=order.index(
                next(i for i, c in enumerate(characters)
                     if c["name"] == speaker)),
            line=line.get("text", ""),
            scene_staging=scene_staging,
            listening_detail=listening_detail,
            ambience=ambience,
            continuous_lines=None,
        )
        # Runtime-cleaned prompt: the proven form carries no
        # <Picture N>/<Subject N> tokens.
        prompt = sanitize_runtime_tokens(prompt_tokens, characters)
        # Speaker-tag consistency: the (SN) of the speaking character
        # must be the one "says:", and no other (SM) may.
        speaker_tag = f"({sn})"
        summary_seg = prompt.split("\n\n", 1)[1].split("\n[Shot")[0]
        if f"{speaker_tag} says:" not in summary_seg:
            raise WiringError(
                f"clip {i}: summary does not attribute speech to "
                f"{speaker_tag} ({speaker!r})")
        for other in sn_order:
            if other != sn and f"({other}) says:" in summary_seg:
                raise WiringError(
                    f"clip {i}: summary wrongly attributes speech to "
                    f"({other})")

        config = {"width": WIDTH, "height": HEIGHT}
        clips.append({
            "clip_index": i,
            "kind": "REF2VA_IDENTITY_AUDIO",
            "mode": "REF2VA_IDENTITY_AUDIO",
            "speaker": speaker,
            "speaker_sn": sn,
            "prompt": prompt,
            # match-cut chain: anchor plate OR previous last frame
            "image_refs": [first_ref] + [p["path"] for p in
                                         character_plates],
            "seed": SEED,
            "frames": frames,
            "fps": FPS,
            "width": config["width"],
            "height": config["height"],
            "audio_guide": audio_path,
            "audio_provenance": {
                "source_master": audio_path,
                "vocal_stem": audio_path,
                "whisper_map": whisper_map,
                "keeper_window_s": (0.0, frames / FPS),
            },
            "chain": {
                "index": i,
                "re_anchor": re_anchor,
                "previous": (i - 1) if i > 1 else None,
            },
        })
    return clips


# ── chain advance (worker path) ───────────────────────────────────────

def advance_chain(queue, host, job_id: str) -> Optional[str]:
    """After a successful render of a chain clip: extract its LAST
    FRAME on the host (proven ffmpeg -sseof machinery from run_jobs)
    into the run dir and patch the NEXT clip's image_refs[0].

    No-op for jobs with no chain metadata, re-anchor boundaries (the
    next cut wants the anchor plate, not a last frame), and the last
    clip. Returns the patched png path or None.
    """
    import scripts.run_jobs as rj

    job = queue.get(job_id)
    if job.state != "done":
        return None
    for clip in job.clips:
        ch = clip.get("chain") or {}
        idx = ch.get("index")
        if not idx:
            continue
        # find the dependent job (the clip whose chain.previous == idx)
        dep = _find_dependent(queue, idx)
        if dep is None:
            continue
        dep_job, dep_clip = dep
        if dep_clip.get("chain", {}).get("re_anchor"):
            continue  # re-anchor cut: keep the anchor plate
        if not str(dep_clip.get("image_refs", [""])[0] or "").startswith(
                "chain://"):
            continue  # already patched
        mp4 = clip.get("mp4")
        if not mp4:
            continue
        png = _chain_png(str(queue.db_path), dep_clip)
        rj.extract_last_frame(host, mp4, png)
        refs = list(dep_clip["image_refs"])
        refs[0] = png
        dep_job_clips = [dict(c) for c in dep_job.clips]
        for c in dep_job_clips:
            if c.get("clip_index") == dep_clip.get("clip_index"):
                c["image_refs"] = refs
        queue.update_clips(dep_job.job_id, dep_job_clips)
        return png
    return None


def _find_dependent(queue, clip_index):
    """The pending job whose single clip has chain.previous == index."""
    for jid in queue.list_state("pending"):
        job = queue.get(jid)
        for c in job.clips:
            if (c.get("chain", {}).get("previous") == clip_index
                    and c.get("image_refs")
                    and str(c["image_refs"][0]).startswith("chain://")):
                return job, c
    return None


def _chain_png(db_path: str, clip) -> str:
    """<run_dir>/render/clipNNNN/chain_last_frame.png (run dir is the
    queue db's parent, matching the r2i convention)."""
    from pathlib import Path
    idx = int(clip.get("clip_index", 0))
    run_dir = str(Path(db_path).parent)
    return f"{run_dir}/render/clip{idx:04d}/chain_last_frame.png"
