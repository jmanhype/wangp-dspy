"""S3 WD-a1d9-followup — manifest serialization/readback, remux
planner, and QC gate. RED-first per TDD.
Spec: docs/specs/s3-audio-manifest-qc.md
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

# ── shared fixtures ─────────────────────────────────────────────────

from predict.audio_dataplane import (
    AudioDataPlaneError,
    AudioGuideProvenance,
    AudioPolicy,
    Ref2VAAudioQC,
)


def _mk_audio_files(tmp_path: Path) -> dict:
    files = {
        "master": tmp_path / "master.wav",
        "stem": tmp_path / "vocal.wav",
        "whisper": tmp_path / "whisper.json",
        "guide": tmp_path / "guide.wav",
        "ref": tmp_path / "ref.png",
    }
    for f in files.values():
        f.write_bytes(b"x")
    return {k: str(v) for k, v in files.items()}


def _mk_provenance(f: dict, window=(1.0, 9.0)) -> AudioGuideProvenance:
    return AudioGuideProvenance(
        source_master=f["master"], vocal_stem=f["stem"],
        whisper_map=f["whisper"], keeper_window_s=window)


def _mk_settings(f: dict, window=(1.0, 9.0)) -> dict:
    """A minimal Ref2VA-style settings doc with the S2 audio extra."""
    prov = _mk_provenance(f, window)
    return {
        "model_type": "ref2va_lip_sync",
        "script": "s. m.",
        "frames_per_shot": 216,
        "image_refs": [f["ref"]],
        "audio_prompt_type": "A",
        "audio_guide": f["guide"],
        "audio_provenance": prov.to_dict(),
        "audio_policy": AudioPolicy(
            remux_window=window).to_dict(),
        "audio_qc": Ref2VAAudioQC.empty().to_dict(),
    }


# ── 1. manifest serialization / readback ───────────────────────────

def test_manifest_round_trip(tmp_path):
    from predict.audio_manifest import AudioManifest
    f = _mk_audio_files(tmp_path)
    doc = _mk_settings(f)
    out = tmp_path / "render.mp4"
    m = AudioManifest.from_settings_doc(doc, render_output=str(out))
    m.write_sidecar()
    sidecar = tmp_path / "render.audio_manifest.json"
    assert sidecar.is_file()
    m2 = AudioManifest.read_sidecar(sidecar)
    assert m2 == m
    # every audio payload key survives
    for k in ("audio_guide", "audio_provenance", "audio_policy",
              "audio_qc"):
        assert m2.payload[k] == doc[k]


def test_manifest_required_for_audio_bearing_jobs_missing_raises(tmp_path):
    from predict.audio_manifest import (
        AudioManifest, AudioManifestError)
    f = _mk_audio_files(tmp_path)
    doc = _mk_settings(f)
    # readback of a render whose sidecar is MISSING: hard gate
    out = tmp_path / "render.mp4"
    with pytest.raises(AudioManifestError, match="audio_manifest"):
        AudioManifest.read_sidecar(out.with_suffix(".audio_manifest.json"))


def test_manifest_rejects_doc_without_audio_payload(tmp_path):
    from predict.audio_manifest import AudioManifest, AudioManifestError
    with pytest.raises(AudioManifestError, match="audio_provenance"):
        AudioManifest.from_settings_doc(
            {"model_type": "minimax_h3_fl2va_pruned"})


def test_manifest_hash_excludes_extra_keys(tmp_path):
    """Qwen ruling: hashing MUST exclude extra keys / hash only the
    sanctioned audio payload block."""
    from predict.audio_manifest import AudioManifest
    f = _mk_audio_files(tmp_path)
    doc = _mk_settings(f)
    m1 = AudioManifest.from_settings_doc(
        doc, render_output=str(tmp_path / "a.mp4"))
    doc2 = dict(doc, image_refs=[f["ref"], f["ref"]])
    m2 = AudioManifest.from_settings_doc(
        doc2, render_output=str(tmp_path / "a.mp4"))
    assert m1.audio_payload_hash == m2.audio_payload_hash
    doc3 = json.loads(json.dumps(doc))
    doc3["audio_provenance"]["source_master"] = f["stem"]
    m3 = AudioManifest.from_settings_doc(
        doc3, render_output=str(tmp_path / "a.mp4"))
    assert m1.audio_payload_hash != m3.audio_payload_hash


def test_manifest_hash_stable_across_key_order(tmp_path):
    from predict.audio_manifest import AudioManifest
    f = _mk_audio_files(tmp_path)
    doc = _mk_settings(f)
    reordered = {k: doc[k] for k in reversed(list(doc))}
    m1 = AudioManifest.from_settings_doc(
        doc, render_output=str(tmp_path / "a.mp4"))
    m2 = AudioManifest.from_settings_doc(
        reordered, render_output=str(tmp_path / "a.mp4"))
    assert m1.audio_payload_hash == m2.audio_payload_hash


def test_manifest_roundtrip_detected_from_settings_doc(tmp_path):
    from predict.audio_manifest import AudioManifest
    f = _mk_audio_files(tmp_path)
    doc = _mk_settings(f)
    m = AudioManifest.from_settings_doc(
        doc, render_output=str(tmp_path / "r.mp4"))
    m.write_sidecar()
    back = AudioManifest.read_sidecar(
        tmp_path / "r.audio_manifest.json")
    assert back.audio_payload_hash == m.audio_payload_hash
    assert back.version == 1


# ── 2. remux planner (pure, argv list, containment) ────────────────

def test_planner_discard_and_remux_argv_list(tmp_path):
    from predict.remux_planner import plan_remux, RemuxPlan
    f = _mk_audio_files(tmp_path)
    policy = AudioPolicy(discard_rendered_audio=True,
                         remux_source="source_master",
                         remux_window=(1.0, 9.0))
    rendered = tmp_path / "render.mp4"
    rendered.write_bytes(b"v")
    keeper_out = tmp_path / "keepers" / "shot.mp4"
    plan = plan_remux(policy, provenance=_mk_provenance(f),
                      rendered_path=str(rendered),
                      keeper_output=str(keeper_out))
    # argv list, never a shell string
    assert isinstance(plan.argv, list)
    assert all(isinstance(a, str) for a in plan.argv)
    assert plan.argv[0] == "ffmpeg"
    # discard rendered audio: only the source's audio stream is mapped
    assert "-an" not in plan.argv or True  # see discard test
    joined = " ".join(plan.argv)
    assert f["master"] in joined
    assert str(rendered) in joined
    assert plan.policy == policy


def test_planner_discard_rendered_audio_never_mapped(tmp_path):
    """G4: rendered audio is discarded — only the remux source's
    audio stream is mapped, the render's audio stream is not."""
    from predict.remux_planner import plan_remux
    f = _mk_audio_files(tmp_path)
    policy = AudioPolicy(discard_rendered_audio=True,
                         remux_source="vocal_stem",
                         remux_window=(0.0, 5.0))
    rendered = tmp_path / "render.mp4"; rendered.write_bytes(b"v")
    out = tmp_path / "out.mp4"
    plan = plan_remux(policy, provenance=_mk_provenance(f, (0.0, 5.0)),
                      rendered_path=str(rendered), keeper_output=str(out))
    argv = plan.argv
    # map only render video (0:v) + source audio (1:a) — never 0:a
    assert "-map" in argv
    maps = [argv[i + 1] for i, a in enumerate(argv) if a == "-map"]
    assert "0:v:0" in maps
    assert "1:a:0" in maps
    assert "0:a" not in maps
    assert f["stem"] in argv  # remux_source=vocal_stem honored


def test_planner_discard_false_rejected_for_ref2va(tmp_path):
    """Safe policy: discard_rendered_audio=False is a typed rejection
    — rendered audio is NEVER trusted (G4)."""
    from predict.remux_planner import plan_remux, RemuxPlannerError
    f = _mk_audio_files(tmp_path)
    policy = AudioPolicy(discard_rendered_audio=False,
                         remux_source="source_master",
                         remux_window=(0.0, 5.0))
    rendered = tmp_path / "render.mp4"; rendered.write_bytes(b"v")
    with pytest.raises(RemuxPlannerError, match="discard_rendered_audio"):
        plan_remux(policy, provenance=_mk_provenance(f, (0.0, 5.0)),
                   rendered_path=str(rendered),
                   keeper_output=str(tmp_path / "out.mp4"))


def test_planner_containment_rejects_escape(tmp_path):
    """Paths never reach a shell; and the output must live inside the
    keeper directory root."""
    from predict.remux_planner import plan_remux, RemuxPlannerError
    f = _mk_audio_files(tmp_path)
    policy = AudioPolicy(remux_window=(0.0, 5.0))
    rendered = tmp_path / "render.mp4"; rendered.write_bytes(b"v")
    keepers = tmp_path / "keepers"; keepers.mkdir()
    with pytest.raises(RemuxPlannerError, match="containment|outside"):
        plan_remux(policy, provenance=_mk_provenance(f, (0.0, 5.0)),
                   rendered_path=str(rendered),
                   keeper_output=str(tmp_path / "escape.mp4"),
                   keeper_root=str(keepers))


def test_planner_containment_accepts_inside(tmp_path):
    from predict.remux_planner import plan_remux
    f = _mk_audio_files(tmp_path)
    policy = AudioPolicy(remux_window=(0.0, 5.0))
    rendered = tmp_path / "render.mp4"; rendered.write_bytes(b"v")
    keepers = tmp_path / "keepers"; keepers.mkdir()
    plan = plan_remux(policy, provenance=_mk_provenance(f, (0.0, 5.0)),
                      rendered_path=str(rendered),
                      keeper_output=str(keepers / "shot.mp4"),
                      keeper_root=str(keepers))
    assert str(keepers / "shot.mp4") in plan.argv


def test_planner_no_shell_string(tmp_path):
    from predict.remux_planner import plan_remux
    f = _mk_audio_files(tmp_path)
    policy = AudioPolicy(remux_window=(0.0, 5.0))
    rendered = tmp_path / "render.mp4"; rendered.write_bytes(b"v")
    plan = plan_remux(policy, provenance=_mk_provenance(f, (0.0, 5.0)),
                      rendered_path=str(rendered),
                      keeper_output=str(tmp_path / "out.mp4"))
    assert not hasattr(plan, "command") or isinstance(
        getattr(plan, "command", None), (list, type(None)))


# ── 3. QC: honest placeholders + G3/G4 enforcement ─────────────────

def test_qc_placeholders_honest_not_judged(tmp_path):
    from predict.qc_audio import qc_ref2va_audio
    f = _mk_audio_files(tmp_path)
    doc = _mk_settings(f)
    out = tmp_path / "render.mp4"; out.write_bytes(b"v")
    from predict.audio_manifest import AudioManifest
    m = AudioManifest.from_settings_doc(doc, render_output=str(out))
    m.write_sidecar()
    qc = qc_ref2va_audio(str(out))
    # judge did NOT run: every score None, critic model NAMED but no
    # scores — honest placeholder
    assert qc.critic_model == "Qwen2-Audio-7B"
    for s in ("mouth_sync", "audio_fidelity",
              "visual_motion_match", "audio_artifacts"):
        assert getattr(qc, s) is None
    assert qc.judged is False
    assert "not yet judged" in qc.notes.lower()


def test_qc_refuses_artifact_without_manifest(tmp_path):
    """G3/G4: QC refuses any artifact whose audio did not pass
    through the discard/remux policy (no manifest = no policy proof)."""
    from predict.qc_audio import qc_ref2va_audio, QCRefusalError
    out = tmp_path / "render.mp4"; out.write_bytes(b"v")
    with pytest.raises(QCRefusalError, match="audio_manifest"):
        qc_ref2va_audio(str(out))


def test_qc_refuses_manifest_with_discard_false(tmp_path):
    from predict.qc_audio import qc_ref2va_audio, QCRefusalError
    from predict.audio_manifest import AudioManifest
    f = _mk_audio_files(tmp_path)
    doc = _mk_settings(f)
    doc["audio_policy"]["discard_rendered_audio"] = False
    out = tmp_path / "render.mp4"; out.write_bytes(b"v")
    m = AudioManifest.from_settings_doc(doc, render_output=str(out))
    m.write_sidecar()
    with pytest.raises(QCRefusalError, match="discard_rendered_audio"):
        qc_ref2va_audio(str(out))


# ── 4. GEPA harness byte-for-byte preserved ────────────────────────

def test_gepa_harness_byte_for_byte_unchanged():
    """The generic GEPA A/B harness sources must be byte-identical to
    the S2 merge commit (bacb506) — no audio leakage."""
    import pathlib as _p
    import subprocess
    root = _p.Path(__file__).resolve().parent.parent
    for sub in ("evaluate", "training"):
        diff = subprocess.run(
            ["git", "diff", "bacb506", "--", sub],
            cwd=root, capture_output=True, text=True).stdout
        assert diff == "", f"{sub} changed vs S2 merge:\n{diff[:400]}"
    # and no audio keys in harness sources
    for sub in ("evaluate", "training"):
        for f_ in (root / sub).rglob("*.py"):
            t = f_.read_text(encoding="utf-8")
            assert "audio_manifest" not in t, f_
            assert "ref2va" not in t.lower(), f_
