"""Production-runtime closure RED — host/ref2va_runtime.py.

Wires the existing Ref2VA primitives end-to-end:
profile.build_settings -> injected render callable (exactly once) ->
write_audio_manifest + readback -> plan_remux_command (explicit
source, argv list) -> injected argv runner -> evaluate_audio_artifact
-> JSON-serializable evidence with hashes + eligibility.

Fails at import until host/ref2va_runtime.py exists.
"""
import hashlib
import json
import os
import pathlib
import sys

import pytest

from host.ref2va_runtime import (  # RED: module does not exist yet
    Ref2VARuntimeError, Ref2VARuntimeInput, run_ref2va_runtime,
)


# ── fixtures ─────────────────────────────────────────────────────────

def _brief():
    from predict.prompt_director import RenderBrief
    return RenderBrief(subject="a detective", motion="walks",
                       camera="dolly in", style="16mm grain")


def _decision():
    from predict.profile_selector import ProfileDecision
    return ProfileDecision(model="h3", resolution="768p",
                           shot_length_frames=96,
                           seed_policy="fixed_per_story",
                           wangp_profile="profile3")


def _audio_env(tmp_path):
    from predict.audio_dataplane import AudioGuideProvenance
    tmp = pathlib.Path(tmp_path)
    shots = tmp / "shots"
    shots.mkdir(exist_ok=True)
    keep = tmp / "keepers"
    keep.mkdir(exist_ok=True)
    out = tmp / "out"
    out.mkdir(exist_ok=True)
    files = {}
    for name in ("guide.wav", "master.wav", "vocal.wav", "wmap.json"):
        f = keep / name
        f.write_bytes(name.encode() * 4)
        files[name] = str(f)
    refs = []
    for i in range(1):
        f = keep / f"ref{i+1}.png"
        f.write_bytes(b"png")
        refs.append(str(f))
    prov = AudioGuideProvenance(
        source_master=files["master.wav"], vocal_stem=files["vocal.wav"],
        whisper_map=files["wmap.json"], keeper_window_s=(1.0, 5.0))
    kwargs = dict(image_refs=refs, audio_prompt_type="A",
                  guide_duration_s=4.0, shot_duration_s=4.0,
                  audio_guide=files["guide.wav"],
                  audio_provenance=prov)
    return kwargs, str(keep), str(out), str(shots), files


def _mk_input(tmp_path, *, render=None, runner=None, judge=None, **over):
    kwargs, keep, out, shots, files = _audio_env(tmp_path)
    tmp = pathlib.Path(tmp_path)
    raw = tmp / "out" / "raw.mp4"
    remux = tmp / "out" / "remux.mp4"
    settings = tmp / "out" / "settings.json"
    calls = []

    def _render(inp):
        calls.append("render")
        raw.write_bytes(b"RAWH3RENDER" * 8)
        return str(raw)

    def _runner(argv):
        calls.append("remux")
        assert isinstance(argv, list), "runner must receive an argv LIST"
        assert all(isinstance(a, str) for a in argv)
        remux.write_bytes(b"REMUXEDARTIFACT" * 8)
        return 0

    inp = Ref2VARuntimeInput(
        briefs=[_brief()], decision=_decision(),
        profile_build_kwargs=kwargs,
        raw_render_path=raw,
        audio_source_path=pathlib.Path(files["master.wav"]),
        remux_output_path=remux,
        settings_path=settings,
        sanctioned_dirs=[keep, out, shots],
        render=render if render is not None else _render,
        runner=runner if runner is not None else _runner,
        judge=judge, critic_version="qwen2audio-7b-test",
    )
    return inp, calls, (keep, out, shots), files


# ── happy path ───────────────────────────────────────────────────────

def test_happy_path_order_and_evidence(tmp_path):
    inp, calls, dirs, files = _mk_input(tmp_path, judge=lambda **kw: dict(
        mouth_sync=8.0, audio_fidelity=7.5, visual_motion_match=8.0,
        audio_artifacts=7.0))
    res = run_ref2va_runtime(inp)
    # exact call order through the injected seams
    assert calls == ["render", "remux"]
    # evidence shape
    assert res["settings_hash"] == hashlib.sha256(
        pathlib.Path(inp.settings_path).read_bytes()).hexdigest()
    assert res["raw_render_hash"] == res["artifact_hashes"]["render"]
    assert res["manifest_hash"] == res["artifact_hashes"]["manifest"]
    assert res["remux_hash"] == res["artifact_hashes"]["remux"]
    assert res["verdict"] == "judged"
    assert res["eligible_for_qc"] is True
    assert res["eligible_for_gepa"] is True
    # deterministic JSON round-trip
    assert json.loads(json.dumps(res, sort_keys=True)) == res


def test_manifest_written_and_readback(tmp_path):
    inp, calls, dirs, files = _mk_input(tmp_path)
    run_ref2va_runtime(inp)
    mpath = pathlib.Path(inp.raw_render_path).parent / "audio_manifest.json"
    assert mpath.is_file()
    doc = json.loads(mpath.read_text())
    assert set(doc) == {"audio_guide", "audio_provenance",
                        "audio_policy", "audio_qc"}


def test_explicit_source_second_input_never_render_audio(tmp_path):
    seen = {}

    def runner(argv):
        seen["argv"] = argv
        pathlib.Path(inp.remux_output_path).write_bytes(b"r" * 16)
        return 0

    inp, calls, dirs, files = _mk_input(tmp_path, runner=runner)
    run_ref2va_runtime(inp)
    argv = seen["argv"]
    assert argv[0] == "ffmpeg"
    inputs = [a for i, a in enumerate(argv) if i and argv[i - 1] == "-i"]
    assert len(inputs) == 2
    assert inputs[0] == str(inp.raw_render_path)
    assert inputs[1] == str(inp.audio_source_path)
    assert inputs[1] != inputs[0]
    # argv LIST, no shell metacharacters anywhere
    assert isinstance(argv, list)
    assert not any(c in "".join(argv) for c in "|;&$`><")


def test_settings_doc_persisted_deterministic(tmp_path):
    inp, _, _, _ = _mk_input(tmp_path)
    a = run_ref2va_runtime(inp)
    doc = json.loads(pathlib.Path(inp.settings_path).read_text())
    # host truth (fix 9): the EMITTED model_type is the wgp handler
    # name, never the rejected 'ref2va_lip_sync'
    assert doc["model_type"] == "minimax_h3_ref2va_pruned"
    # same artifact bytes + settings -> identical evidence (minus nothing:
    # fully deterministic)
    inp2, _, _, _ = _mk_input(tmp_path)
    b = run_ref2va_runtime(inp2)
    assert a == b


# ── judge semantics ──────────────────────────────────────────────────

def test_judge_none_not_eligible(tmp_path):
    inp, _, _, _ = _mk_input(tmp_path, judge=None)
    res = run_ref2va_runtime(inp)
    assert res["eligible_for_qc"] is False
    assert res["eligible_for_gepa"] is False
    qc = res["qc"]
    assert qc["critic_model"] == "Qwen2-Audio-7B"
    assert all(qc[f] is None for f in (
        "mouth_sync", "audio_fidelity", "visual_motion_match",
        "audio_artifacts"))
    assert res["verdict"] == "pending"


def test_judged_requires_remux_evidence(tmp_path):
    def runner(argv):
        # rc=0 but NO remux file produced
        return 0

    inp, _, _, _ = _mk_input(tmp_path, runner=runner, judge=lambda **kw: dict(
        mouth_sync=8.0, audio_fidelity=7.5, visual_motion_match=8.0,
        audio_artifacts=7.0))
    with pytest.raises(Ref2VARuntimeError, match="[Rr]emux"):
        run_ref2va_runtime(inp)


# ── fail-closed typed failures ───────────────────────────────────────

def test_raw_render_missing_fails_closed(tmp_path):
    def render(inp):
        return str(inp.raw_render_path)  # never writes it

    inp, _, _, _ = _mk_input(tmp_path, render=render)
    with pytest.raises(Ref2VARuntimeError, match="raw render"):
        run_ref2va_runtime(inp)


def test_ffmpeg_nonzero_fails_closed(tmp_path):
    inp, _, _, _ = _mk_input(tmp_path, runner=lambda argv: 1)
    with pytest.raises(Ref2VARuntimeError, match="ffmpeg|remux"):
        run_ref2va_runtime(inp)


def test_path_escape_fails_closed(tmp_path):
    inp, calls, dirs, files = _mk_input(tmp_path)
    inp = Ref2VARuntimeInput(
        **{**inp.__dict__,
           "audio_source_path": pathlib.Path("/etc/hosts")})
    with pytest.raises(Ref2VARuntimeError, match="containment"):
        run_ref2va_runtime(inp)


def test_g4_violation_fails_closed(tmp_path):
    inp, _, _, files = _mk_input(tmp_path)

    def bad_render(inp):
        p = pathlib.Path(inp.raw_render_path)
        p.write_bytes(b"RAWH3RENDER" * 8)
        return str(p)

    # tamper: rewrite manifest after write is hard; instead corrupt the
    # settings doc G4 field post-build via a builder override
    import host.ref2va_runtime as rt
    orig = rt.Ref2VAProfile.build_settings

    def g4_builder(self, briefs, decision, **kw):
        doc = orig(self, briefs, decision, **kw)
        doc["audio_policy"]["discard_rendered_audio"] = False
        return doc

    rt.Ref2VAProfile.build_settings = g4_builder
    try:
        with pytest.raises(Ref2VARuntimeError, match="G4"):
            run_ref2va_runtime(inp)
    finally:
        rt.Ref2VAProfile.build_settings = orig


def test_judge_exception_fails_closed(tmp_path):
    def boom(**kw):
        raise RuntimeError("judge exploded")

    inp, _, _, _ = _mk_input(tmp_path, judge=boom)
    with pytest.raises(Ref2VARuntimeError):
        run_ref2va_runtime(inp)


def test_render_called_exactly_once(tmp_path):
    n = {"i": 0}

    def render(inp):
        n["i"] += 1
        pathlib.Path(inp.raw_render_path).write_bytes(b"x" * 16)
        return str(inp.raw_render_path)

    inp, _, _, _ = _mk_input(tmp_path, render=render, judge=lambda **kw: dict(
        mouth_sync=5.0, audio_fidelity=5.0, visual_motion_match=5.0,
        audio_artifacts=5.0))
    run_ref2va_runtime(inp)
    assert n["i"] == 1


def test_render_source_same_as_raw_rejected(tmp_path):
    inp, _, _, _ = _mk_input(tmp_path)
    inp = Ref2VARuntimeInput(
        **{**inp.__dict__,
           "audio_source_path": pathlib.Path(inp.raw_render_path)})
    with pytest.raises(Ref2VARuntimeError, match="G4|render"):
        run_ref2va_runtime(inp)


def test_settings_doc_instead_of_builder(tmp_path):
    """Validated settings doc may be supplied directly."""
    kwargs, keep, out, shots, files = _audio_env(tmp_path)
    from predict.render_profiles import Ref2VAProfile
    doc = Ref2VAProfile().build_settings([_brief()], _decision(), **kwargs)
    tmp = pathlib.Path(tmp_path)
    raw = tmp / "out" / "raw.mp4"
    remux = tmp / "out" / "remux.mp4"

    def render(inp):
        raw.write_bytes(b"Z" * 32)
        return str(raw)

    def runner(argv):
        remux.write_bytes(b"Y" * 32)
        return 0

    inp = Ref2VARuntimeInput(
        briefs=[_brief()], decision=_decision(), settings_doc=doc,
        raw_render_path=raw,
        audio_source_path=pathlib.Path(files["master.wav"]),
        remux_output_path=remux,
        settings_path=tmp / "out" / "settings.json",
        sanctioned_dirs=[keep, out, shots],
        render=render, runner=runner, judge=None, critic_version=None)
    res = run_ref2va_runtime(inp)
    assert res["eligible_for_qc"] is False


# ── preservation: generic H3 lane untouched ──────────────────────────

def test_generic_h3_untouched_and_no_gepa(tmp_path):
    import inspect
    import host.wangp_adapter as adapter
    src_before = inspect.getsource(adapter.build_settings)
    from host.ref2va_runtime import Ref2VAProfile  # noqa: F401 re-import
    assert inspect.getsource(adapter.build_settings) == src_before
    # no GEPA/training machinery pulled in by THIS runtime module:
    # import it in a fresh interpreter and check its transitive roots
    import subprocess
    code = ("import sys, host.ref2va_runtime as rt; "
            "roots = {m.split('.')[0] for m in sys.modules "
            "if not m.startswith('_')}; "
            "assert 'training' not in roots, sorted(roots)")
    r = subprocess.run([sys.executable, "-c", code], capture_output=True,
                       text=True, cwd=os.getcwd(),
                       env={"PYTHONPATH": os.getcwd(), "PATH": "/usr/bin:/bin"})
    assert r.returncode == 0, r.stderr
    # H3 settings snapshot: identical to the adapter's generic build
    from predict.render_profiles import H3Profile
    doc = H3Profile().build_settings([_brief()], _decision())
    direct = adapter.build_settings([_brief()], _decision())
    assert doc == direct
    assert doc["model_type"] == "minimax_h3_fl2va_pruned"


def test_runtime_does_not_hardcode_3090():
    import host.ref2va_runtime as rt
    src = inspect_src = open(rt.__file__).read()
    for bad in ("3090", "ssh ", "StraughterG", "/mnt/bulk"):
        assert bad not in src, f"runtime hardcodes {bad!r}"
