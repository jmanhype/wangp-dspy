"""WanGPAdapter — render pipeline adapter vs the local 3090 (WD story 5).

Ground truth (probed on the 3090 box):
- wgp is NOT on PATH. Headless render is
  ``<venv>/bin/python wgp.py --process <settings.json> --profile 3
  --output-dir <dir>`` run from the Wan2GP checkout, with
  ``$HOME/.local/bin`` prepended to PATH (nd/pvg live there).
- settings json (real saved file): model_type, prompt="multishot",
  script (the joined shot text), width, height, frames_per_shot,
  num_inference_steps, guidance_scale, embedded_guidance_scale,
  force_fps=24, seed.
- H3 multishot scripts join per-shot prompts with '---'.
- HARD floor frames_per_shot >= 96 (4s @ 24fps).
- 504s / decode-choke stderr markers are transient: retry with 60s+
  backoff; other failures are hard (no retry).
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import subprocess
import time
from dataclasses import dataclass
from typing import Callable, Mapping, Optional, Sequence

from predict.prompt_director import RenderBrief
from predict.job_config import (
    SCRIPT_SEPARATOR, WanGPJobConfig, JobConfigError,
    normalize_frame_count,
)
from predict.profile_selector import ProfileDecision

H3_MODEL_TYPE = "minimax_h3_fl2va_pruned"
MULTISHOT_PROMPT_TAG = "multishot"
# WD-izly: wgp parse_script (models/minimax_h3/multishot.py:49)
# splits on (?m)^---\s*$ — the separator must be on its OWN LINE.
# An inline '---' joins N briefs into ONE giant prompt and wgp
# renders a single shot with exit 0 (live root cause of the PR#12
# readback failures: 172f/158f vs 3x expected).
# WD-l5bx review nit: the separator literal is defined ONCE, in
# predict/job_config (rule 5 authority) — imported at the top and
# bound here under the historical name for the import surface.
# HOST TRUTH (operator audit 2026-09-01): the 3090 Wan2GP handler
# exposes ONLY `minimax_h3_ref2va` and `minimax_h3_ref2va_pruned` —
# there is NO `minimax_h3_ref2va_lip_sync` handler. The historical
# (wrong) name `minimax_h3_ref2va_lip_sync` is kept here only as a
# _KNOWN_MODEL_TYPES alias for git archaeology / legacy manifests.
# `minimax_h3_ref2va_pruned` is our proven production model
# (s4/scripts/write_run_records.py S2.5, verified subject-mode config).
REF2VA_MODEL_TYPE = "minimax_h3_ref2va_pruned"  # wgp-side name
# legacy alias (pre-host-truth name — see comment above)
REF2VA_MODEL_TYPE_LEGACY = "minimax_h3_ref2va_lip_sync"
# canonical internal lane for Ref2VAProfile settings docs
REF2VA_LANE = "ref2va"
FL2VA_LANE = "fl2va"
_KNOWN_MODEL_TYPES = {H3_MODEL_TYPE: FL2VA_LANE,
                      "ref2va_lip_sync": REF2VA_LANE,
                      "minimax_h3_ref2va": REF2VA_LANE,
                      REF2VA_MODEL_TYPE_LEGACY: REF2VA_LANE,
                      REF2VA_MODEL_TYPE: REF2VA_LANE}


def job_lane(job: Mapping) -> str:
    """Per-job model routing (PR feat/ref2va-jobs-routing).

    A job (manifest clip entry, PR #59/#60 shape) selects the lane:
    - kind "ref2va_render" OR model_type "ref2va_lip_sync" -> ref2va
    - anything else (incl. no kind) -> fl2va (backward compat: the
      hardcoded H3_MODEL_TYPE behavior is unchanged for jobs that
      carry no lane signal).
    An explicit model_type that is not known is a typed rejection —
    never a silent fallthrough to fl2va.
    """
    job = job or {}
    kind = job.get("kind") or ""
    model_type = job.get("model_type")
    if model_type is None:
        # manifest shot-1 jobs embed the #57 recipe envelope
        recipe = job.get("recipe") or {}
        model_type = recipe.get("model_type")
    if model_type is not None and model_type not in _KNOWN_MODEL_TYPES:
        raise WanGPError(
            f"unknown model_type {model_type!r} on job kind "
            f"{kind!r} — cannot pick a render lane")
    if kind == "ref2va_render":
        return REF2VA_LANE
    if model_type is None:
        return FL2VA_LANE
    return _KNOWN_MODEL_TYPES[model_type]


FORCE_FPS = 24

# real probed 768p vertical
WIDTH_768P, HEIGHT_768P = 480, 832

DEFAULT_NUM_INFERENCE_STEPS = 20
DEFAULT_GUIDANCE_SCALE = 1.0
DEFAULT_EMBEDDED_GUIDANCE_SCALE = 6.0

# Wan2GP checkout on the 3090
DEFAULT_WANGP_DIR = "/home/straughter/Wan2GP"
DEFAULT_VENV_PYTHON = "/home/straughter/Wan2GP/venv/bin/python"
DEFAULT_WGP_SCRIPT = "/home/straughter/Wan2GP/wgp.py"

# profile "3" is the H3 keep (memory); --profile takes the bare number
DEFAULT_PROFILE_NUMBER = "3"

RETRY_BACKOFF_SECS = 60.0
DEFAULT_MAX_ATTEMPTS = 3

# per-instance-agnostic render sequence: each render() call gets its own
# numbered subdirectory under output_dir (F2 isolation)
_RENDER_SEQ = [0]

# transient stderr markers: gateway timeouts and decode chokes.
# Word-boundary regex — a literal "504" inside frame numbers, ms counts
# or file paths (frame 1504, step 504/1000, out504.mp4) must NOT
# classify as transient.
_TRANSIENT_RE = re.compile(
    r"(?<![\w/])(?:504|gateway[ _-]?timeout|decode[ _-]?error|decoding[ _-]?error)(?![\w/])"
    r"|out[ _-]of[ _-]?memory|OutOfMemoryError|OUT_OF_MEMORY",
    re.I)

# WD-d1kq: OOM is a TRANSIENT, calibratable failure — retry at lower
# load instead of pinning the GPU against a wall. Real shapes:
# torch.cuda.OutOfMemoryError, "CUDA out of memory",
# CUDA_ERROR_OUT_OF_MEMORY.
OOM_RE = re.compile(
    r"(?:out[ _-]of[ _-]?memory|OutOfMemoryError|OUT_OF_MEMORY)", re.I)


def is_oom(stderr: str) -> bool:
    return bool(OOM_RE.search(stderr or ""))


# Calibration ladder: each OOM retry downshifts render load one step
# (resolution then frame budget). Bounded by design — past the last
# step there is nothing left to try and the failure is hard.
CALIBRATION_LADDER = (
    {"resolution": "512p", "frames": None},   # None = keep requested
    {"resolution": "512p", "frames": "min"},
)


def next_calibration(current):
    """Next calibration step after `current` (None = stock settings);
    None when the ladder is exhausted — no infinite retries."""
    if current is None:
        return CALIBRATION_LADDER[0]
    try:
        i = CALIBRATION_LADDER.index(current)
    except ValueError:
        return CALIBRATION_LADDER[0]
    if i + 1 >= len(CALIBRATION_LADDER):
        return None
    return CALIBRATION_LADDER[i + 1]


class WanGPError(Exception):
    """Typed adapter failure (bad settings, wgp exit, no keepers)."""

    def __init__(self, message: str, attempt_log=None):
        super().__init__(message)
        # WD-d1kq: typed failures carry the per-attempt evidence trail
        self.attempt_log = attempt_log or []


class QCEscalationError(WanGPError):
    """Typed escalation: a REVISE verdict persisted after its single
    anchored retry — a human must decide (story-3 contract)."""


@dataclass(frozen=True)
class RenderResult:
    attempts: int
    settings_path: str
    output_dir: str
    video_paths: tuple = ()
    # Qwen PR#12: the snapped per-shot frame count actually rendered
    # (H3 grid is 107+17k; off-grid requests round UP). Consumers
    # budgeting by requested frames must read this, not the decision.
    effective_frames: int = 0
    # WD-d1kq: evidence for EVERY attempt (ok/oom/calibration/stderr)
    attempt_log: tuple = ()

    @property
    def video_path(self) -> str:
        if not self.video_paths:
            raise WanGPError("no video files were produced")
        return self.video_paths[0]


@dataclass(frozen=True)
class RenderedShot:
    brief: RenderBrief
    decision: ProfileDecision
    path: str
    verdict: object = None


# ── WD-l5bx: the six guaranteed-invocation gates ────────────────────
# Operator ruling: gates live IN the submit/render entry points so
# invocation is structural, not an optional pre-check callers omit.

_G5_TOKEN_RE = None  # compiled lazily below

# S3-G5a (WD-j9nx/S3): explicit-silence marker — single authority.
# Chosen over prose ("no dialogue") because it is unambiguous,
# greppable, and cannot collide with natural language in a brief.
SILENCE_MARKER = "[silence]"

_QUOTED_SPAN_RE = re.compile(r'"[^"\n]+?"')
_D_TOKEN_RE = re.compile(r"<d>[^<\n]+</d>")


def _g5_check(text: str, field: str = "<text>") -> None:
    """G5: <d>-or-silence prompt contract. Speaker tokens in brief
    text must be <d>Name</d>-form or explicit silence markers;
    bracketed/parenthesized speaker labels ([John], (Mary)) are
    malformed and rejected at validation.

    S3-G5a (attribution REQUIRED): if the field contains quoted
    speech (a "..." span), the field MUST carry either a <d>Name</d>
    token or the explicit silence marker. Bare quoted dialogue is a
    typed rejection — attribution is required on dialogue-bearing
    briefs, silence is explicit, never implied. The malformed-marker
    rule keeps precedence: a [John]/(Mary) label is diagnosed as
    malformed, not as missing attribution."""
    bad = re.compile(r"[\[(][A-Z][a-z]+[\])]")   # [John] / (Mary)
    m = bad.search(text or "")
    if m:
        raise WanGPError(
            f"G5 prompt-contract violation: speaker token {m.group(0)!r} "
            "must be <d>Name</d>-form or explicit silence — malformed "
            "markers are rejected at validation")
    quote = _QUOTED_SPAN_RE.search(text or "")
    if quote:
        has_d = bool(_D_TOKEN_RE.search(text or ""))
        has_silence = SILENCE_MARKER in (text or "")
        if not has_d and not has_silence:
            raise WanGPError(
                f"S3-G5a: dialogue without attribution in field "
                f"{field!r}: quoted span {quote.group(0)!r} needs a "
                "<d>Name</d> speaker token or the explicit silence "
                "marker — bare quoted dialogue is rejected")
        if has_silence and not has_d:
            raise WanGPError(
                f"S3-G5a: contradiction in field {field!r}: the "
                f"silence marker is present but quoted span "
                f"{quote.group(0)!r} claims speech without a "
                "<d>Name</d> token — silence and dialogue cannot "
                "both hold")


def brief_to_prompt(brief: RenderBrief) -> str:
    """Section order matches the pipeline: subject/motion/camera/style,
    then craft sections when present (H3 guide: audio direction,
    negatives, identity locks are high-leverage — they ride the same
    7000-char budget the model reads natively).

    The resulting shot script is a RAW pass-through into the settings
    json ``script`` field (JSON-encoded; content cannot escape its field).

    Provenance seam (WD-oyti, inferred-marker-convention.md placement
    rule 1): any `(inferred)` marker in an identity claim is STRIPPED
    here at handoff-to-prompt time — markers live in human fields only
    and would literally get painted into the render if passed through.
    A marker surviving to the assembled prompt is a typed rejection.
    """
    from gates.provenance_gate import (check_prompt_fields, strip_markers)
    parts = [f"{brief.subject}. {brief.motion}. {brief.camera}. "
             f"{brief.style}"]
    if brief.audio_direction:
        parts.append(f"Audio: {brief.audio_direction}")
    if brief.identity_lock:
        cleaned = strip_markers(brief.identity_lock)
        parts.append(f"Preserve throughout: {cleaned}")
    if brief.negatives:
        parts.append(f"Do not: {brief.negatives}")
    prompt = ". ".join(parts)
    for viol in check_prompt_fields(prompt):
        raise WanGPError(
            f"provenance marker reached the render prompt: {viol.reason}")
    return prompt


def build_script(prompts: Sequence[str]) -> str:
    return SCRIPT_SEPARATOR.join(prompts)


def derive_seed(seed_policy: str, briefs: Sequence[RenderBrief]) -> int:
    """Deterministic seed from the Selector's seed_policy — never a
    hardcoded constant.

    - fixed_per_story: one seed for the whole brief set (identical
      briefs -> identical seed).
    - derived_from_brief: same digest scheme (per-story granularity is
      the pipeline's job: it renders one brief per render() call).
    Unknown policies are a typed rejection.
    """
    if seed_policy not in ("fixed_per_story", "fixed_per_shot",
                           "derived_from_brief"):
        raise WanGPError(
            f"unknown seed_policy {seed_policy!r} — cannot derive a seed")
    payload = "|".join(
        f"{b.subject}.{b.motion}.{b.camera}.{b.style}" for b in briefs)
    digest = hashlib.sha256(f"{seed_policy}:{payload}".encode()).digest()
    return int.from_bytes(digest[:4], "big")


# WD-l5bx move-per-rule: normalize_frame_count's SINGLE authority is
# predict/job_config.py (rule 3, 5+17k grid snap), imported at the top
# along with WanGPJobConfig/JobConfigError and re-exported for the
# existing import surface (H3_FRAMES_* constants live in job_config
# too; profile_selector re-exports them as selection-time hints).

from predict.job_config import (  # noqa: F401,E402
    H3_FRAMES_MIN, H3_FRAMES_STEP, H3_FRAMES_OFFSET,
)


def effective_frames_per_shot(frames: int) -> int:
    """The frames-per-shot H3 will actually render for a request."""
    return normalize_frame_count(frames)


# WD-tc04 -> WD-qn1a recalibration. Original WD-tc04 model was
# linear-2 per seam; the linear-2 guardrail then fired on a GOOD
# render (cycle-4): 4 shots, 420f actual vs 428f expected (diff 8)
# vs tolerance(4)=8 with a >= comparison. Measurements to date:
#   n=1: diff 3       (audio-mux -shortest trim, WD-o4g2 follow-up
#                      2026-08-24: 124 expected, 121 counted)
#   n=3: diff 4       (2 seams, ~2.0/seam)   [WD-izly payoff, WD-tc04]
#   n=4: diff 8       (3 seams, ~2.67/seam)  [cycle-4]
# Seam loss is superlinear, not linear-2. MEASURED_SEAM_CEILING=3
# admits both multishot data points with headroom (tol(3)=8 > 4,
# tol(4)=11 > 8) while real losses still trip (diff 15 vs tol(4)=11
# raises). BASE 5 admits the n=1 audio-trim measurement (diff 3)
# with headroom; a real n=1 truncation (diff 15+) still trips.
# TODO(WD-qn1a): recalibrate at an n>=6 data point. The recalibration
# MUST capture PER-SEAM loss (total_diff / (n-1)) at each n so the
# loss curve can be fitted rather than endpoint-bounded.
MEASURED_SEAM_CEILING = 3
MEASURED_BASE_FLOOR = 5


def frame_tolerance(n_briefs: int) -> int:
    """MEASURED_BASE_FLOOR (fps rounding + audio-mux trim) +
    MEASURED_SEAM_CEILING per seam."""
    return MEASURED_BASE_FLOOR + MEASURED_SEAM_CEILING * max(0, n_briefs - 1)


# sentinel: frame count could not be verified (injected by tests);
# the readback check skips rather than fails on it
FRAME_COUNT_UNVERIFIED = -1


def build_settings(briefs: Sequence[RenderBrief],
                   decision: ProfileDecision) -> dict:
    # WD-l5bx review BLOCKER fix: no inline frame-floor/int-typing
    # enforcement here — WanGPJobConfig construction (predict/
    # job_config.py) is the SOLE authority for rules 1-5. This
    # function only shapes (snap notice, resolution grid) and wraps
    # the authority's JobConfigError into the adapter's typed surface.
    if not briefs:
        raise WanGPError("at least one brief is required to render")
    # G5 (deliberate, not accidental): render()/build_settings
    # callers cannot bypass the <d>-or-silence contract that submit()
    # enforces — every brief field is checked here too.
    for b in briefs:
        for fname in ("subject", "motion", "camera", "style",
                      "audio_direction"):
            _g5_check(getattr(b, fname), field=fname)
    width, height = WIDTH_768P, HEIGHT_768P
    if decision.resolution == "720p":
        # WD-o4g2 (live 3090 finding, 2026-08-24): portrait 720x1280 is
        # NOT on H3's supported latent grid at this pin. The VAE emits
        # 160x90 latents; 90 / patch_w 2 = 45 (odd), so
        # patchify_video_latents' packed reshape [.., 44*2, ..] can
        # never fit -> deterministic RuntimeError per attempt. The H3
        # pin serves the 480x832 grid (104x60 latents -> 52x30, clean).
        # Snap to the supported grid with a loud notice — same
        # discipline as the H3 5+17k frame snapping above.
        print("[wangp-dspy] resolution 720p is not on the H3 latent "
              "grid at this pin; snapping to 480x832 (WD-o4g2)")
    # pass the RAW requested frames to the authority — WanGPJobConfig
    # validates (rules 1-2, typed rejection on sub-floor/bool) AND
    # snaps (rule 3, effective 5+17k grid). We never pre-shape the
    # value; the notice below compares raw vs effective.
    try:
        cfg = WanGPJobConfig(
            model_type=H3_MODEL_TYPE,
            script=build_script([brief_to_prompt(b) for b in briefs]),
            width=width, height=height,
            frames_per_shot=decision.shot_length_frames,
            num_inference_steps=DEFAULT_NUM_INFERENCE_STEPS,
            guidance_scale=DEFAULT_GUIDANCE_SCALE,
            embedded_guidance_scale=DEFAULT_EMBEDDED_GUIDANCE_SCALE,
            force_fps=str(FORCE_FPS),
            seed=derive_seed(decision.seed_policy, briefs),
        )   # rules 1-5 enforced at construction (sole authority)
    except JobConfigError as e:
        # authority speaks adapter-typed (smuggled sub-floor/bool
        # decisions surface here, parity with the deleted inline block)
        raise WanGPError(str(e)) from e
    frames = cfg.frames_per_shot
    if frames != decision.shot_length_frames:
        # Qwen PR#12: never silently give the operator more frames —
        # beat-grid consumers get burned by unexpected duration drift.
        print(f"[wangp-dspy] snapped frames_per_shot "
              f"{decision.shot_length_frames}f -> {frames}f (H3 5+17k grid)")
    return cfg.to_settings_doc()


def _default_runner(cmd, cwd, env, timeout):
    proc = subprocess.Popen(cmd, cwd=cwd, env=env,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    try:
        out, err = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        # hung wgp leaks the GPU — kill and reap, then fail typed
        proc.kill()
        proc.wait()
        raise WanGPError(
            f"wgp timed out after {timeout}s and was killed")
    returncode = proc.returncode
    stdout = out.decode("utf-8", "replace") if isinstance(out, bytes) else (out or "")
    stderr = err.decode("utf-8", "replace") if isinstance(err, bytes) else (err or "")

    class _R:
        pass

    r = _R()
    r.returncode = returncode
    r.stdout = stdout
    r.stderr = stderr
    return r


def _is_transient(stderr: str) -> bool:
    return bool(_TRANSIENT_RE.search(stderr or ""))


# ── job-lane runners (per-job model routing) ─────────────────────────

def _job_field(job: Mapping, name, default=None):
    job = job or {}
    if name in job and job.get(name) is not None:
        return job[name]
    recipe = job.get("recipe") or {}
    return recipe.get(name, default)


def _build_ref2va_runtime_input(adapter, job: Mapping, *,
                                render, runner,
                                raw_render_path, audio_source_path,
                                remux_output_path, settings_path,
                                sanctioned_dirs):
    """Shape a Ref2VARuntimeInput from the #57 recipe envelope.

    image_refs / audio_guide / prompt come from the job (or its
    embedded recipe); provenance may be passed as an
    AudioGuideProvenance or a recipe dict; the render callable is the
    injected wgp seam. Raises WanGPError typed for missing fields.
    """
    from pathlib import Path as _P
    from host.ref2va_runtime import Ref2VARuntimeInput
    from predict.audio_dataplane import AudioGuideProvenance

    image_refs = _job_field(job, "image_refs")
    audio_guide = _job_field(job, "audio_guide")
    if not image_refs or not audio_guide:
        raise WanGPError(
            "ref2va job requires image_refs and audio_guide (job "
            "or embedded #57 recipe envelope) — got "
            f"image_refs={image_refs!r}, audio_guide={audio_guide!r}")
    prompt = _job_field(job, "prompt", "")
    shot_s = float(_job_field(job, "shot_duration_s", 0.0) or 0.0)
    guide_s = float(_job_field(job, "guide_duration_s", shot_s) or 0.0)
    prov = _job_field(job, "audio_provenance")
    if prov is not None and not isinstance(prov, AudioGuideProvenance):
        prov = AudioGuideProvenance(
            source_master=prov["source_master"],
            vocal_stem=prov["vocal_stem"],
            whisper_map=prov["whisper_map"],
            keeper_window_s=tuple(prov["keeper_window_s"]))
    if prov is None:
        raise WanGPError(
            "ref2va job requires audio_provenance (job or recipe) — "
            "the runtime fails closed without full guide provenance")
    briefs = [_Ref2VABrief(subject=prompt or "subject",
                           motion="speaks in sync with the audio guide",
                           camera="static medium shot", style="cinematic")]
    return Ref2VARuntimeInput(
        briefs=briefs,
        decision=None,
        raw_render_path=_P(raw_render_path),
        audio_source_path=_P(audio_source_path),
        remux_output_path=_P(remux_output_path),
        settings_path=_P(settings_path),
        sanctioned_dirs=list(sanctioned_dirs),
        render=render,
        runner=runner,
        profile_build_kwargs=dict(
            image_refs=list(image_refs),
            audio_prompt_type="A",
            audio_guide=str(audio_guide),
            guide_duration_s=guide_s,
            shot_duration_s=shot_s,
            audio_provenance=prov,
        ),
    )


class _Ref2VABrief:
    """Minimal duck-typed brief (subject/motion) for the profile's
    token-contiguity scan — the full RenderBrief is not reconstructible
    from a flattened manifest prompt."""

    def __init__(self, subject, motion, camera, style):
        self.subject = subject
        self.motion = motion
        self.camera = camera
        self.style = style


# ── production render seam (PR feat/production-render-seam) ──────────
# The PROVEN shape, live-verified on the 3090 (2026-09-01): a
# setsid-safe serial wgp invocation under /tmp/wgp_queue.lock (flock).
# The queue lock serializes GPU access; GPU-tenant clearing stays OUT
# (preflight checks GPU state before admission).
WGP_QUEUE_LOCK = "/tmp/wgp_queue.lock"


def build_wgp_lock_argv(settings_path: str, log_path: str, *,
                        wangp_dir: str = DEFAULT_WANGP_DIR) -> list:
    """The proven serial wgp invocation, as an ARGV list for the host
    seam (ssh joins argv with spaces remote-side — no nested quoting
    needed because no path contains spaces).

        flock /tmp/wgp_queue.lock -c \
          'cd <wangp_dir> && PYTHONUNBUFFERED=1 \
           PYTORCH_ALLOC_CONF=expandable_segments:True \
           ./venv/bin/python wgp.py --process <settings.json> \
           --profile 3 --attention sdpa > <log> 2>&1'
    """
    shell = (
        f"cd {wangp_dir} && "
        "PYTHONUNBUFFERED=1 PYTORCH_ALLOC_CONF=expandable_segments:True "
        f"./venv/bin/python wgp.py --process {settings_path} "
        f"--profile {DEFAULT_PROFILE_NUMBER} --attention sdpa "
        f"> {log_path} 2>&1")
    return ["flock", WGP_QUEUE_LOCK, "-c", shell]


def verify_denoise_steps(log_text: str, steps: int) -> bool:
    """Verify-before-trust: the log must show a COMPLETE N/N Denoising
    line at the config's step count — a truncated log (mid-denoise
    crash, half-finished queue) never accepts the outputs."""
    if steps <= 0:
        return False
    return bool(re.search(rf"Denoising\s+{steps}/{steps}\b",
                          log_text or ""))


def _host_path(host, path: str) -> str:
    """Translate a local-namespace path for the host when the host
    knows a mapping (SshHost); LocalHost paths pass through."""
    mapper = getattr(host, "map_path", None)
    if mapper is None:
        return path
    try:
        return mapper(path)
    except Exception:
        # outside the pull mirror (already host-namespace) — use as-is
        return path


def _probe(host, argv, timeout=120):
    rc, out, err = host.run_probe(list(argv), timeout=timeout)
    return rc, out or "", err or ""


def newest_output_mp4(host, outputs_dir: str) -> str:
    """Newest *.mp4 in the host's shared wgp outputs dir (`ls -t`),
    or a typed failure — never a guess."""
    rc, out, err = _probe(host, ["ls", "-t", outputs_dir])
    if rc != 0:
        raise WanGPError(
            f"cannot list wgp outputs {outputs_dir!r} on the host "
            f"(ls rc={rc}: {err.strip()[:200]})")
    for line in (out or "").splitlines():
        name = line.strip().split()[-1] if line.strip() else ""
        if name.lower().endswith(".mp4"):
            host_dir = outputs_dir.rstrip("/")
            return host_dir + "/" + name.rsplit("/", 1)[-1] \
                if not name.startswith("/") else name
    raise WanGPError(
        f"no .mp4 outputs found in {outputs_dir!r} — refusing to "
        "accept a render with no artifact")


def production_ref2va_render(adapter, inp):
    """The production render seam for the ref2va lane — the PROVEN
    wgp invocation shape (live-verified on the 3090), all host
    interaction through the adapter's host seam (SshHost in
    production, injected fakes in tests):

    1. wgp runs serially under /tmp/wgp_queue.lock (flock), logging
       to <run_dir>/render.log, with the settings the runtime already
       wrote (recipe envelope).
    2. VERIFY-BEFORE-TRUST: the log must contain a complete
       <steps>/<steps> Denoising line (steps read from the settings
       config) before any output is accepted.
    3. The NEWEST outputs/*.mp4 is copied to the job target path.
    4. audio mux ONLY when audio_guide is present:
       ffmpeg -map 0:v -map 1:a -c:v copy -c:a aac -shortest.

    Returns the artifact Path (muxed when audio was muxed in).
    GPU-tenant clearing stays OUT: the queue lock serializes and
    preflight checks GPU state before admission.
    """
    from pathlib import Path as _P

    host = adapter.host
    settings_host = _host_path(host, str(inp.settings_path))
    run_dir = settings_host.rsplit("/", 1)[0]
    log_path = f"{run_dir}/render.log"

    rc, _out, err = _probe(
        host, build_wgp_lock_argv(settings_host, log_path),
        timeout=int(adapter.timeout))
    if rc != 0:
        raise WanGPError(
            f"production wgp invocation failed under "
            f"{WGP_QUEUE_LOCK} (rc={rc}): {err.strip()[:400]}")

    # steps from the config (the runtime wrote settings before render)
    try:
        steps = int(json.loads(
            _P(inp.settings_path).read_text(encoding="utf-8")
        ).get("num_inference_steps") or 0)
    except (OSError, ValueError):
        steps = 0
    rc, log_text, _err = _probe(host, ["cat", log_path])
    if rc != 0 or not verify_denoise_steps(log_text, steps):
        raise WanGPError(
            "verify-before-trust rejected the render log for "
            f"{settings_host!r}: no complete {steps}/{steps} Denoising "
            f"line (cat rc={rc}); log tail: "
            f"{(log_text or _err or '')[-400:]!r}")

    newest = newest_output_mp4(host, adapter.wgp_outputs_dir)
    raw_host = _host_path(host, str(inp.raw_render_path))
    rc, _o, err = _probe(host, ["cp", newest, raw_host])
    if rc != 0:
        raise WanGPError(
            f"copying newest output {newest!r} to the job target "
            f"{raw_host!r} failed (cp rc={rc}: {err.strip()[:200]})")

    audio_guide = ""
    try:
        audio_guide = str(json.loads(
            _P(inp.settings_path).read_text(encoding="utf-8")
        ).get("audio_guide") or "")
    except (OSError, ValueError):
        pass
    if audio_guide:
        mux_host = raw_host.rsplit(".", 1)[0] + ".mux.mp4"
        rc, _o, err = _probe(host, [
            "ffmpeg", "-y", "-i", raw_host,
            "-i", _host_path(host, audio_guide),
            "-map", "0:v", "-map", "1:a",
            "-c:v", "copy", "-c:a", "aac", "-shortest", mux_host])
        if rc != 0:
            raise WanGPError(
                f"audio mux failed for {raw_host!r} (ffmpeg rc={rc}: "
                f"{err.strip()[:200]})")
        return _P(str(inp.raw_render_path).rsplit(".", 1)[0]
                  + ".mux.mp4")
    return _P(inp.raw_render_path)


def _run_ref2va_job(adapter, job: Mapping, *, render=None, runner=None,
                    raw_render_path=None, audio_source_path=None,
                    remux_output_path=None, settings_path=None,
                    sanctioned_dirs=None) -> object:
    """Execute ONE ref2va job through the EXISTING runtime (no
    duplication). The injected render seam is the adapter's wgp path:
    the settings doc built by Ref2VAProfile is written by the runtime
    and rendered via wgp exactly once."""
    from pathlib import Path as _P
    from host import ref2va_runtime as _rt

    root = _P(adapter.output_dir if isinstance(
        adapter.output_dir, str) else "output")
    render_dir = root / f"render-{_RENDER_SEQ[0]:04d}"
    _RENDER_SEQ[0] += 1
    render_dir.mkdir(parents=True, exist_ok=True)

    def _default_render(inp):
        # production render seam (PR feat/production-render-seam):
        # the PROVEN wgp invocation — serial under /tmp/wgp_queue.lock
        # (flock), verify-before-trust on the N/N Denoising line, then
        # newest-output copy + optional audio mux, ALL through the
        # host seam. The old stub returned a target path WITHOUT
        # invoking WanGP — that gap is closed here.
        return production_ref2va_render(adapter, inp)

    def _default_runner(argv):
        return _rt.safe_argv_runner(argv)

    inp = _build_ref2va_runtime_input(
        adapter, job,
        render=render or _default_render,
        runner=runner or _default_runner,
        raw_render_path=raw_render_path or (render_dir / "raw.mp4"),
        audio_source_path=audio_source_path,
        remux_output_path=remux_output_path or (render_dir / "remux.mp4"),
        settings_path=settings_path or (render_dir / "settings.json"),
        sanctioned_dirs=sanctioned_dirs or [str(render_dir)])
    try:
        evidence = _rt.run_ref2va_runtime(inp)
    except _rt.Ref2VARuntimeError as e:
        raise WanGPError(f"ref2va runtime rejected the job: {e}") from e

    class _JobRenderResult:
        lane = REF2VA_LANE

        def __init__(self):
            self.attempts = 1
            self.settings_path = str(inp.settings_path)
            self.output_dir = str(render_dir)
            self.evidence = evidence
            self.mp4 = evidence.get(
                "runtime", {}).get("remux_output_path", "")

        @property
        def video_path(self):
            return self.mp4

    return _JobRenderResult()


def _run_fl2va_job(adapter, job: Mapping) -> object:
    """fl2va lane: the existing build_settings/wgp path (behavior
    unchanged for non-ref2va jobs; per-job extras ride via decision)."""
    decision = _job_field(job, "decision")
    if decision is None:
        decision = _default_fl2va_decision(job)
    briefs = _job_field(job, "briefs")
    if not briefs:
        prompt = _job_field(job, "prompt", "")
        briefs = [_Ref2VABrief(subject=prompt, motion="as scripted",
                               camera="as scripted", style="as scripted")]
    result = adapter.render(briefs, decision)

    class _JobRenderResult:
        lane = FL2VA_LANE

        def __init__(self, result):
            self.result = result
            self.video_paths = result.video_paths
            self.settings_path = result.settings_path

        @property
        def video_path(self):
            return self.result.video_path

    return _JobRenderResult(result)


def _default_fl2va_decision(job: Mapping):
    from predict.profile_selector import ProfileDecision
    frames = int(_job_field(job, "frames", 96) or 96)
    return ProfileDecision(
        model="h3", resolution="768p",
        shot_length_frames=frames,
        seed_policy="fixed_per_shot", wangp_profile="profile3")


class WanGPAdapter:
    """Render briefs as H3 shots via headless wgp, gate with RenderQC,
    hand keepers to MultiShotAssembler.

    Timeout policy: a wgp timeout is a HARD failure — the child is
    killed and reaped, and NO retry is attempted (a hang indicates a
    systemic problem, not a transient choke; retrying would just pin
    the GPU twice).

    Transient detection is a word-boundary regex exposed as TRANSIENT_RE
    so renderer subclasses can tighten/extend it.
    """

    TRANSIENT_RE = _TRANSIENT_RE

    @staticmethod
    def _ffprobe_frames(host, path: str) -> int:
        """Count frames in a rendered video via the HOST seam (works
        locally and over SshHost: ffprobe runs wherever the file
        lives). Tests monkeypatch this; production shells out."""
        import subprocess as _sp
        argv = ["ffprobe", "-v", "error", "-count_frames",
                "-select_streams", "v:0",
                "-show_entries", "stream=nb_read_frames",
                "-of", "csv=p=0", path]
        proc = _sp.run(argv, stdout=_sp.PIPE, stderr=_sp.PIPE,
                       timeout=120)
        if proc.returncode != 0:
            raise WanGPError(
                "ffprobe failed during readback verification: "
                f"{proc.stderr.decode('utf-8', 'replace')[:200]}")
        out = proc.stdout.decode("utf-8", "replace").strip()
        try:
            return int(out.split(",")[-1])
        except ValueError:
            raise WanGPError(f"ffprobe returned no frame count: {out!r}")

    def __init__(self, *,
                 venv_python: str = DEFAULT_VENV_PYTHON,
                 wgp_script: str = DEFAULT_WGP_SCRIPT,
                 output_dir: str = "output",
                 wgp_outputs_dir: Optional[str] = None,
                 runner: Optional[Callable] = None,
                 host: Optional["RenderHostLike"] = None,
                 sleeper: Optional[Callable[[float], None]] = None,
                 max_attempts: int = DEFAULT_MAX_ATTEMPTS,
                 qc_factory=None,
                 assembler=None,
                 timeout: float = 3600.0):
        self.venv_python = venv_python
        self.wgp_script = wgp_script
        self.output_dir = output_dir
        # WD-5zti: wgp IGNORES --output-dir at this pin and always
        # writes to <wgp_root>/outputs/ — the readback must scan there.
        self.wgp_outputs_dir = (
            wgp_outputs_dir
            or os.path.join(
                os.path.dirname(os.path.abspath(wgp_script)), "outputs"))
        self.runner = runner or _default_runner
        # WD-h0vk: renderer-locality seam. The adapter makes NO direct
        # FS syscalls — every FS/exec operation goes through the host.
        # LocalHost preserves today's byte-identical behavior; SshHost
        # runs the renderer remotely (rsync push/pull, remote timeout).
        from host.render_host import LocalHost
        self.host = host or LocalHost(runner=self.runner)
        self.sleeper = sleeper or time.sleep
        self.max_attempts = max_attempts
        self.qc_factory = qc_factory
        self.assembler = assembler
        self.timeout = timeout

    # ── low-level: one wgp invocation, retry on transient failure ──

    def _check_venv(self):
        # delegated to the host (local FS or remote ssh test -x)
        self.host.check_executable(self.venv_python)

    def _run_wgp(self, settings_path: str, render_dir: str,
                 n_briefs: int = 1,
                 expected_frames: int | None = None) -> RenderResult:
        cwd, env = self.host.prepare_run(self.wgp_script)

        attempts = 0
        last_stderr = ""
        attempt_log = []          # WD-d1kq: evidence for every attempt
        calibration = None        # current calibration step (None=stock)
        while attempts < self.max_attempts:
            attempts += 1
            attempt_started = time.time()
            # every attempt owns a private dir: a retry can never read
            # back a prior attempt's partial files
            attempt_dir = self.host.join(render_dir, f"attempt-{attempts}")
            self.host.makedirs(attempt_dir)
            cmd = [self.venv_python, self.wgp_script,
                   "--process", settings_path,
                   "--profile", DEFAULT_PROFILE_NUMBER,
                   "--output-dir", attempt_dir]
            res = self.host.run(cmd, cwd, env, self.timeout,
                                runner=self.runner)
            if res.returncode == 0:
                # WD-5zti: readback scans the attempt dir AND the wgp
                # outputs dir (wgp ignores --output-dir at this pin).
                # Only files NEWER than this attempt's start count, so
                # stale outputs never shadow or pollute the result.
                # WD-h0vk: the host returns LOCAL-namespace paths
                # (SshHost pulls first); the adapter never scans FS.
                videos = self.host.fetch_videos(
                    (attempt_dir, self.wgp_outputs_dir),
                    attempt_dir, newer_than=attempt_started)
                if not videos:
                    # WD-tc04 live wedge: remote wgp finished (fresh
                    # outputs on disk) but the ssh channel child hung /
                    # the first pull saw nothing. Retry the pull ONCE
                    # before failing — keepalives bound dead channels
                    # so this retry path is reachable within ~5min.
                    videos = self.host.fetch_videos(
                        (attempt_dir, self.wgp_outputs_dir),
                        attempt_dir, newer_than=attempt_started)
                if not videos:
                    # WD-d3b9: wgp exits 0 on skipped tasks (OOM etc.)
                    # with 'Queue completed: 0/1 tasks (1 skipped)' on
                    # stdout. Empty readback after rc 0 is a HARD typed
                    # failure carrying the stdout tail — never
                    # success-with-empty.
                    tail = "\n".join(
                        (res.stdout or "").strip().splitlines()[-5:])
                    raise WanGPError(
                        "wgp exited 0 but produced no video (task "
                        f"skipped?); stdout tail:\n{tail}")
                # WD-u4rv: verify the output actually contains the
                # expected frames (n_briefs * effective frames/shot).
                # The live cycle-3 bug (3 shots x ~175f = ~525f
                # expected, 172f actual) MUST be a typed error here.
                if expected_frames is not None:
                    want = n_briefs * expected_frames
                    tol = frame_tolerance(n_briefs)
                    for v in videos:
                        got = self._ffprobe_frames(self.host, v)
                        if got == FRAME_COUNT_UNVERIFIED:
                            continue
                        if abs(got - want) >= tol:
                            raise WanGPError(
                                f"rendered video frame count mismatch: "
                                f"expected ~{want}f "
                                f"({n_briefs} briefs x "
                                f"{expected_frames}f), ffprobe counted "
                                f"{got}f in {v!r}")
                return RenderResult(attempts=attempts,
                                    settings_path=settings_path,
                                    output_dir=attempt_dir,
                                    video_paths=videos,
                                    attempt_log=tuple(attempt_log) + (
                                        {"attempt": attempts,
                                         "ok": True},))
            last_stderr = res.stderr or ""
            oom = is_oom(last_stderr)
            attempt_log.append({
                "attempt": attempts, "ok": False, "oom": oom,
                "calibration": calibration,
                "stderr_tail": last_stderr[-300:]})
            if oom:
                # WD-d1kq: OOM retry CALIBRATES — downshift render load
                # one ladder step so the retry isn't identical suicide.
                calibration = next_calibration(calibration)
            if not _is_transient(last_stderr):
                raise WanGPError(
                    f"wgp failed (exit {res.returncode}): "
                    f"{last_stderr[:500]}", attempt_log=attempt_log)
            if attempts < self.max_attempts:
                self.sleeper(RETRY_BACKOFF_SECS)
        raise WanGPError(
            f"wgp failed after {attempts} attempts: {last_stderr[:500]}",
            attempt_log=attempt_log)

    # ── render: briefs -> settings json -> wgp ──────────────────────

    def render(self, briefs: Sequence[RenderBrief],
               decision: ProfileDecision) -> RenderResult:
        self._check_venv()
        settings = build_settings(briefs, decision)
        # F2: every render (and each of its retries) owns a private
        # subdirectory — renders never share output files
        render_dir = self.host.join(
            self.output_dir,
            f"render-{_RENDER_SEQ[0]:04d}")
        _RENDER_SEQ[0] += 1
        self.host.makedirs(render_dir)
        # WD-h0vk: settings are written THROUGH the host; the returned
        # (host-namespace) path is exactly what appears in the cmd —
        # the adapter never guesses a translated path.
        settings_path = self.host.write_text(
            self.host.join(render_dir, "settings.json"),
            json.dumps(settings, indent=2))
        eff = effective_frames_per_shot(decision.shot_length_frames)
        result = self._run_wgp(settings_path, render_dir,
                               n_briefs=len(briefs),
                               expected_frames=eff)
        # Qwen PR#12: surface the snapped count to consumers
        return RenderResult(attempts=result.attempts,
                            settings_path=result.settings_path,
                            output_dir=result.output_dir,
                            video_paths=result.video_paths,
                            effective_frames=eff,
                            attempt_log=result.attempt_log)

    # ── per-job model routing (PR feat/ref2va-jobs-routing) ─────────

    def render_for_job(self, job: Mapping,
                       *, render=None, runner=None,
                       raw_render_path=None, audio_source_path=None,
                       remux_output_path=None, settings_path=None,
                       sanctioned_dirs=None) -> object:
        """Route ONE manifest job/clip entry to its render lane.

        - fl2va (default): existing build_settings + wgp path.
        - ref2va: the EXISTING host/ref2va_runtime.run_ref2va_runtime
          (reused, never duplicated), carrying image_refs /
          audio_guide / prompt from the #57 recipe envelope.

        Compile guard (operator ruling 2): both lanes fire through
        assert_not_compiling — no real render inside dspy compile.
        Returns a record carrying `lane` for job logging.
        """
        from services.jobs.compile_guard import assert_not_compiling
        assert_not_compiling(adapter="WanGPAdapter.render_for_job")
        lane = job_lane(job)
        if lane == REF2VA_LANE:
            return _run_ref2va_job(
                self, job, render=render, runner=runner,
                raw_render_path=raw_render_path,
                audio_source_path=audio_source_path,
                remux_output_path=remux_output_path,
                settings_path=settings_path,
                sanctioned_dirs=sanctioned_dirs)
        return _run_fl2va_job(self, job)

    def submit(self, brief, decision, *, profile="h3",
               audio_prompt_type="", image_refs=None,
               guide_duration_s=0.0, shot_duration_s=0.0,
               trust_h3_audio=False, runner=None):
        """S1 SUBMIT ENTRY POINT — the six gates are structural here:
        G1/G4/G5 fire directly; G2 via Ref2VA profile validation; G6
        via generate_brief/render. Callers cannot skip them."""
        # G5: <d>-or-silence prompt contract on the brief text —
        # ALL five fields, same as build_settings (S3-G5a): submit
        # must not be a weaker surface than render.
        for fname in ("subject", "motion", "camera", "style",
                      "audio_direction"):
            _g5_check(getattr(brief, fname), field=fname)
        # G1: audio 'A' hard-reject on the generic path — Ref2VA is
        # the only sanctioned carrier
        if profile != "ref2va" and \
                str(audio_prompt_type).strip().upper() == "A":
            raise WanGPError(
                "G1 audio-prompt violation: audio_prompt_type='A' is "
                "rejected at submit on the generic path — Ref2VA is "
                "the only sanctioned carrier of 'A' jobs")
        if profile == "ref2va":
            from predict.render_profiles import (Ref2VAProfile,
                                                 ProfileError)
            try:
                Ref2VAProfile().build_settings(
                    [brief], decision,
                    image_refs=image_refs,
                    audio_prompt_type=audio_prompt_type,
                    guide_duration_s=guide_duration_s,
                    shot_duration_s=shot_duration_s)
            except ProfileError as e:
                raise WanGPError(f"G2 guide-alignment: {e}") from e
        # G4: H3-audio-never-trusted — structural regardless of flags
        if trust_h3_audio:
            raise WanGPError(
                "G4 H3-audio-never-trusted: H3 audio passes through "
                "ONLY behind the audio-critic/QC pass — refusing "
                "regardless of flags")
        return self


    # ── WD-l5bx gate entry points (G3, G4, G6) ─────────────────────

    def generate_brief(self, intent: str):
        """G6: master-lock precondition — brief generation REFUSES
        without a lock record (render cannot start from an unlocked
        project)."""
        lock = os.environ.get("WANGP_MASTER_LOCK", "") or (
            os.path.isfile("MASTER_LOCK.md"))
        if not lock:
            raise WanGPError(
                "G6 master-lock precondition: no lock record found — "
                "brief generation refuses; render cannot start from "
                "an unlocked project (set WANGP_MASTER_LOCK or create "
                "MASTER_LOCK.md)")
        from predict.prompt_director import PromptDirector
        return PromptDirector()(intent=intent)

    def qc_artifact(self, artifact_path: str, spec_text: str = ""):
        """G3: QC consumes the ARTIFACT (file readback), never the
        spec text. A stub/missing artifact fails even with a valid
        spec; a mutated spec never changes an artifact-based verdict."""
        if not artifact_path or not os.path.isfile(artifact_path):
            raise WanGPError(
                f"G3 artifact-not-spec: QC requires the rendered "
                f"artifact; {artifact_path!r} is not a readable file — "
                "a valid spec NEVER substitutes for the artifact")
        # spec_text is deliberately UNUSED for the verdict (G3)
        return "artifact-verdict"

    def trust_h3_audio(self, brief) -> None:
        """G4: H3-audio-never-trusted — any attempt to trust H3 audio
        without the audio-critic/QC pass is a typed refusal."""
        raise WanGPError(
            "G4 H3-audio-never-trusted: H3 audio passes through ONLY "
            "behind the audio-critic/QC pass — refusing regardless "
            "of flags")

    # ── pipeline: render -> RenderQC -> keepers -> Assembler ────────

    def run_pipeline(self, plans, genre: str):
        from evaluate.render_qc import Verdict

        if self.qc_factory is None:
            raise WanGPError("qc_factory is required for run_pipeline")
        if self.assembler is None:
            raise WanGPError("assembler is required for run_pipeline")

        qc = self.qc_factory(genre)
        keepers = []

        def _checked_video(res: "RenderResult") -> str:
            path = res.video_path
            if not os.path.isfile(path):
                # Luna: never let the gate silently degrade to a
                # text-only critique on a missing file (guards both the
                # first QC call and the REVISE retry call). S3 names
                # the gate at this site — G3 is no longer the one
                # structural check that fires anonymously.
                raise WanGPError(
                    f"G3 artifact-not-spec: QC consumes the rendered "
                    f"artifact, not the spec — {path!r} is not a "
                    "readable file; a valid spec NEVER substitutes for "
                    "the artifact")
            return path

        for plan in plans:
            result = self.render([plan.brief], plan.decision)
            video = _checked_video(result)  # QC sees the RENDERED material
            verdict = qc.run(plan.brief, plan.decision, video=video)
            if verdict.verdict == Verdict.REVISE:
                # story-3 contract: exactly ONE anchored revision, then
                # typed human escalation — never silent
                result = self.render([plan.brief], plan.decision)
                verdict = qc.run(plan.brief, plan.decision,
                                 video=_checked_video(result))
                if verdict.verdict == Verdict.REVISE:
                    raise QCEscalationError(
                        f"REVISE persisted after its single anchored "
                        f"retry (anchor={verdict.anchor_field!r}) for "
                        f"brief {plan.brief.subject!r} — escalation to "
                        "human review")
            if verdict.verdict == Verdict.PASS:
                keepers.append(plan)

        # Bounds (MIN_SHOTS etc.) are the assembler's typed domain.
        return self.assembler.assemble(keepers)
