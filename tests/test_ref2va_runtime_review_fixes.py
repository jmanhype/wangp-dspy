"""PR #51 review blockers — RED suite for host/ref2va_runtime.py.

Blocker 1: containment ordering (validate BEFORE any write/render).
Blocker 2: post-render path substitution revalidation + replan.
Blocker 3: critic_version actually reaches QC (runtime side).
Blocker 4: settings_doc runtime validation before render/write.
Blocker 5: policy/AudioDataPlaneError wrapped as Ref2VARuntimeError.
Blocker 6: safe default argv runner helper.
"""
import json
import pathlib
import subprocess

import pytest

from host.ref2va_runtime import (
    Ref2VARuntimeError, Ref2VARuntimeInput, run_ref2va_runtime,
)

from tests.test_ref2va_runtime import (  # reuse the existing fixtures
    _audio_env, _brief, _decision, _mk_input,
)

_JUDGE = lambda **kw: dict(  # noqa: E731
    mouth_sync=8.0, audio_fidelity=7.5, visual_motion_match=8.0,
    audio_artifacts=7.0)


# ── Blocker 1: containment BEFORE any filesystem write / render ──────

@pytest.mark.parametrize("field", [
    "settings_path", "raw_render_path", "audio_source_path",
    "remux_output_path",
])
def test_uncontained_path_fails_before_any_write_or_render(
        tmp_path, field):
    tmp = pathlib.Path(tmp_path)
    evil = tmp / "evil"          # NEVER inside sanctioned dirs
    inp, calls, dirs, files = _mk_input(tmp_path, judge=_JUDGE)
    over = {field: evil / "x.bin"}
    inp2 = Ref2VARuntimeInput(**{**inp.__dict__, **over})
    with pytest.raises(Ref2VARuntimeError, match="containment"):
        run_ref2va_runtime(inp2)
    # NOTHING escaped: no dir, no file, no injected call
    assert not evil.exists()
    assert calls == []
    # even the settings file was not written
    assert not pathlib.Path(inp.settings_path).exists()


def test_settings_parent_not_created_on_escape(tmp_path):
    """settings_path outside root must fail before mkdir of its parent."""
    tmp = pathlib.Path(tmp_path)
    outside = tmp / "outside" / "deep" / "settings.json"
    inp, calls, dirs, files = _mk_input(tmp_path)
    inp2 = Ref2VARuntimeInput(
        **{**inp.__dict__, "settings_path": outside})
    with pytest.raises(Ref2VARuntimeError, match="containment"):
        run_ref2va_runtime(inp2)
    assert not (tmp / "outside").exists()
    assert calls == []


# ── Blocker 2: post-render path substitution ─────────────────────────

def test_render_returns_uncontained_path_rejected(tmp_path):
    tmp = pathlib.Path(tmp_path)
    inp, calls, dirs, files = _mk_input(tmp_path, judge=_JUDGE)
    mine = []
    outside = tmp / "evil" / "raw.mp4"
    outside.parent.mkdir()
    outside.write_bytes(b"x" * 16)

    def render(i):
        mine.append("render")
        pathlib.Path(i.raw_render_path).write_bytes(b"R" * 16)
        return str(outside)

    inp2 = Ref2VARuntimeInput(**{**inp.__dict__, "render": render})
    with pytest.raises(Ref2VARuntimeError, match="containment"):
        run_ref2va_runtime(inp2)
    # no manifest, no remux
    assert not (pathlib.Path(inp.raw_render_path).parent
                / "audio_manifest.json").exists()
    assert mine == ["render"]
    assert not pathlib.Path(inp.remux_output_path).exists()


def test_render_returns_audio_source_as_raw_rejected(tmp_path):
    inp, calls, dirs, files = _mk_input(tmp_path, judge=_JUDGE)
    mine = []

    def render(i):
        mine.append("render")
        pathlib.Path(i.raw_render_path).write_bytes(b"R" * 16)
        return str(pathlib.Path(i.audio_source_path))

    inp2 = Ref2VARuntimeInput(**{**inp.__dict__, "render": render})
    with pytest.raises(Ref2VARuntimeError, match="G4"):
        run_ref2va_runtime(inp2)
    assert mine == ["render"]
    assert not pathlib.Path(inp.remux_output_path).exists()


def test_remux_argv_replanned_against_actual_raw(tmp_path):
    inp, _, dirs, files = _mk_input(tmp_path, judge=_JUDGE)
    tmp = pathlib.Path(tmp_path)
    raw2 = tmp / "out" / "actual_raw.mp4"
    seen = {}

    def render(i):
        raw2.write_bytes(b"ACTUAL" * 8)
        return str(raw2)

    def runner(argv):
        seen["argv"] = argv
        pathlib.Path(inp.remux_output_path).write_bytes(b"M" * 16)
        return 0

    inp2 = Ref2VARuntimeInput(**{**inp.__dict__, "render": render,
                                 "runner": runner})
    res = run_ref2va_runtime(inp2)
    assert seen == {}  # no mux is permitted
    assert inp.remux_output_path.read_bytes() == raw2.read_bytes()
    assert res["runtime"]["raw_render_path"] == str(raw2)


def test_continuation_post_remux_frame_loss_fails_closed(tmp_path):
    """A raw grid-aligned render cannot mask a truncated final remux."""
    kwargs, keep, out, shots, files = _audio_env(tmp_path)
    from predict.audio_dataplane import AudioGuideProvenance
    from predict.prompt_director import RenderBrief
    from predict.profile_selector import ProfileDecision
    from predict.render_profiles import Ref2VAProfile

    image = pathlib.Path(keep) / "ref1.png"
    prov = AudioGuideProvenance(
        source_master=files["master.wav"],
        vocal_stem=files["vocal.wav"],
        whisper_map=files["wmap.json"],
        keeper_window_s=(0.0, 56 / 24),
    )
    brief = RenderBrief(subject="speaker", motion="talks",
                        camera="static", style="cinematic")
    decision = ProfileDecision(
        model="h3", resolution="768p", shot_length_frames=56,
        seed_policy="fixed_per_shot", wangp_profile="profile3",
        continuation=True)
    doc = Ref2VAProfile().build_settings(
        [brief], decision, image_refs=[str(image)],
        audio_prompt_type="A", audio_guide=files["guide.wav"],
        guide_duration_s=56 / 24, shot_duration_s=56 / 24,
        audio_length_frames=56, image_start=str(image),
        audio_provenance=prov, continuation=True)
    raw = pathlib.Path(out) / "raw.mp4"
    remux = pathlib.Path(out) / "remux.mp4"

    def render(inp):
        raw.write_bytes(b"raw")
        return str(raw)

    def runner(argv):
        remux.write_bytes(b"remux")
        return 0

    inp = Ref2VARuntimeInput(
        briefs=[brief], decision=decision, settings_doc=doc,
        raw_render_path=raw, audio_source_path=pathlib.Path(files["master.wav"]),
        remux_output_path=remux,
        settings_path=pathlib.Path(out) / "settings.json",
        sanctioned_dirs=[keep, out, shots], render=render, runner=runner,
        continuation=True, frame_probe=lambda _path: 53)
    with pytest.raises(Ref2VARuntimeError, match="post-remux.*53f"):
        run_ref2va_runtime(inp)


# ── Blocker 3: critic_version reaches actual QC ──────────────────────

def test_judged_qc_carries_input_critic_version(tmp_path):
    inp, _, _, _ = _mk_input(tmp_path, judge=_JUDGE)
    res = run_ref2va_runtime(inp)
    assert res["qc"]["critic_version"] == "qwen2audio-7b-test"


def test_runtime_asserts_qc_version_matches_when_judged(tmp_path):
    """If the lane ever returns a mismatched version while judged,
    the runtime must fail closed — not silently report it."""
    import host.ref2va_runtime as rt

    def fake_eval(artifact, *, judge=None, critic_version=None):
        res = _real_eval(artifact, judge=judge,
                         critic_version=critic_version)
        res["qc"]["critic_version"] = "SOMETHING-ELSE"
        res["verdict"] = "judged"
        res["eligible_for_qc"] = True
        res["eligible_for_gepa"] = True
        return res

    inp, _, _, _ = _mk_input(tmp_path, judge=_JUDGE)
    _real_eval = rt.evaluate_audio_artifact
    rt.evaluate_audio_artifact = fake_eval
    try:
        with pytest.raises(Ref2VARuntimeError,
                           match="critic_version"):
            run_ref2va_runtime(inp)
    finally:
        rt.evaluate_audio_artifact = _real_eval


def test_critic_version_none_default_preserved(tmp_path):
    inp, _, _, _ = _mk_input(tmp_path, judge=_JUDGE)
    inp2 = Ref2VARuntimeInput(**{**inp.__dict__,
                                 "critic_version": None})
    res = run_ref2va_runtime(inp2)
    assert res["qc"]["critic_version"] is None
    assert res["verdict"] == "judged"


# ── Blocker 4: settings_doc runtime validation ───────────────────────

def _doc_env(tmp_path):
    kwargs, keep, out, shots, files = _audio_env(tmp_path)
    from predict.render_profiles import Ref2VAProfile
    doc = Ref2VAProfile().build_settings([_brief()], _decision(),
                                         **kwargs)
    tmp = pathlib.Path(tmp_path)
    raw = tmp / "out" / "raw.mp4"
    remux = tmp / "out" / "remux.mp4"
    calls = []

    def render(i):
        calls.append("render")
        raw.write_bytes(b"Z" * 32)
        return str(raw)

    def runner(argv):
        calls.append("remux")
        remux.write_bytes(b"Y" * 32)
        return 0

    def mk(doc):
        return Ref2VARuntimeInput(
            briefs=[_brief()], decision=_decision(), settings_doc=doc,
            raw_render_path=raw,
            audio_source_path=pathlib.Path(files["master.wav"]),
            remux_output_path=remux,
            settings_path=tmp / "out" / "settings.json",
            sanctioned_dirs=[keep, out, shots],
            render=render, runner=runner, judge=None), calls
    return mk, files, tmp


@pytest.mark.parametrize("mutate,match", [
    (lambda d: d.__setitem__("model_type", "minimax_h3_fl2va_pruned"),
     "model_type"),
    (lambda d: d.__setitem__("audio_prompt_type", "B"),
     "audio_prompt_type"),
    (lambda d: d.pop("audio_qc"), "audio"),
    (lambda d: d.__setitem__(
        "audio_guide", "/nonexistent/definitely/missing.wav"),
     "audio_guide"),
    (lambda d: d["audio_policy"].__setitem__(
        "discard_rendered_audio", True), "native|discard"),
])
def test_invalid_settings_doc_fails_before_render_or_write(
        tmp_path, mutate, match):
    mk, files, tmp = _doc_env(tmp_path)
    kwargs, keep, out, shots, files2 = _audio_env(tmp_path)
    from predict.render_profiles import Ref2VAProfile
    doc = Ref2VAProfile().build_settings([_brief()], _decision(),
                                         **kwargs)
    mutate(doc)
    inp, calls = mk(doc)
    with pytest.raises(Ref2VARuntimeError, match=match):
        run_ref2va_runtime(inp)
    assert calls == []
    assert not (tmp / "out" / "settings.json").exists()


def test_non_dict_settings_doc_fails_before_render(tmp_path):
    mk, files, tmp = _doc_env(tmp_path)
    inp, calls = mk(["not", "a", "dict"])
    with pytest.raises(Ref2VARuntimeError, match="dict"):
        run_ref2va_runtime(inp)
    assert calls == []


def test_settings_doc_audio_guide_outside_sanctioned(tmp_path):
    mk, files, tmp = _doc_env(tmp_path)
    kwargs, keep, out, shots, files2 = _audio_env(tmp_path)
    from predict.render_profiles import Ref2VAProfile
    outside = tmp / "outside"
    outside.mkdir()
    g = outside / "guide.wav"
    g.write_bytes(b"g" * 8)
    doc = Ref2VAProfile().build_settings(
        [_brief()], _decision(), **{**kwargs, "audio_guide": str(g)})
    inp, calls = mk(doc)
    with pytest.raises(Ref2VARuntimeError, match="containment"):
        run_ref2va_runtime(inp)
    assert calls == []


def test_valid_settings_doc_still_passes(tmp_path):
    mk, files, tmp = _doc_env(tmp_path)
    kwargs, keep, out, shots, files2 = _audio_env(tmp_path)
    from predict.render_profiles import Ref2VAProfile
    doc = Ref2VAProfile().build_settings([_brief()], _decision(),
                                         **kwargs)
    inp, calls = mk(doc)
    res = run_ref2va_runtime(inp)
    assert calls == ["render"]
    assert res["runtime"]["lane"] == "ref2va_runtime"


# ── Blocker 5: no raw ValueError / AudioDataPlaneError leaks ─────────

@pytest.mark.parametrize("policy", [
    {"remux_source": "bogus_source"},
    {"remux_window": [5.0, 1.0]},
    {"discard_rendered_audio": "yes-please"},
])
def test_bad_policy_in_doc_raises_typed_runtime_error(
        tmp_path, policy):
    mk, files, tmp = _doc_env(tmp_path)
    kwargs, keep, out, shots, files2 = _audio_env(tmp_path)
    from predict.render_profiles import Ref2VAProfile
    doc = Ref2VAProfile().build_settings([_brief()], _decision(),
                                         **kwargs)
    doc["audio_policy"].update(policy)
    inp, calls = mk(doc)
    with pytest.raises(Ref2VARuntimeError) as ei:
        run_ref2va_runtime(inp)
    assert not isinstance(ei.value, ValueError), (
        "raw ValueError/AudioDataPlaneError leaked from the runtime")
    assert calls == []


# ── Blocker 6: safe default argv runner helper ───────────────────────

def test_safe_argv_runner_executes_without_shell(tmp_path):
    from host.ref2va_runtime import safe_argv_runner
    tmp = pathlib.Path(tmp_path)
    f = tmp / "t.txt"
    argv = ["/bin/sh", "-c", f"echo hi > {f}"]  # crafted by caller
    rc = safe_argv_runner(argv)
    assert rc == 0
    assert f.read_text().strip() == "hi"
    # non-list / non-str argv rejected
    with pytest.raises(Ref2VARuntimeError):
        safe_argv_runner("echo hi")     # a shell STRING, not a list
    with pytest.raises(Ref2VARuntimeError):
        safe_argv_runner(["/bin/sh", "-c", 123])
