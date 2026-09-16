import json
from pathlib import Path

import pytest

from scripts.run_acceptance import AcceptanceBundleError, run_bundle
from scripts.run_acceptance import _stage_media_inputs
from scripts.run_acceptance import _submit_completed_prefix


def _bundle(tmp_path):
    audio = []
    for i in range(6):
        p = tmp_path / f"turn{i + 1}.wav"
        p.write_bytes(b"wav")
        audio.append(str(p))
    anchor = tmp_path / "plate.png"
    grandma = tmp_path / "face_grandma.png"
    soul = tmp_path / "face_soul.png"
    for p in (anchor, grandma, soul):
        p.write_bytes(b"png")
    script = [{"speaker": "Grandma" if i % 2 == 0 else "Soul",
               "text": f"Turn {i + 1}."} for i in range(6)]
    return {
        "run_id": "acceptance-test",
        "premise": {
            "id": "dg-acceptance", "title": "Devil's Grandma",
            "logline": "A grandmother bargains with a flaming soul.",
            "characters": [
                {"name": "Grandma", "sn_tag": "S1",
                 "description": "elderly grandmother with round glasses"},
                {"name": "Soul", "sn_tag": "S2",
                 "description": "skeletal flaming soul"},
            ],
        },
        "media_manifest": {
            "premise_id": "dg-acceptance",
            "plates": {"anchor": str(anchor), "grandma": str(grandma),
                        "soul": str(soul)},
            "audio": [{"path": path,
                       "speaker": "Grandma" if i % 2 == 0 else "Soul"}
                      for i, path in enumerate(audio)],
        },
        "script_lines": script,
        "audio_paths": audio,
        "plate_paths": [[str(anchor), str(soul)] if i % 2 == 0
                        else [str(anchor), str(grandma)]
                        for i in range(6)],
    }


def test_bundle_runner_refuses_unregistered_premise(tmp_path):
    bundle = _bundle(tmp_path)
    bundle.pop("premise")
    bundle["media_manifest"]["premise_id"] = "dg-not-registered"
    path = tmp_path / "staging.json"
    path.write_text(json.dumps(bundle))
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(
        "scripts.run_acceptance.repository_identity",
        lambda _root: {"clean_tree": True, "dirty_tree": False})
    with pytest.raises(AcceptanceBundleError, match="not registered"):
        run_bundle(path, db_path=tmp_path / "jobs.db")
    monkeypatch.undo()


def test_bundle_runner_refuses_unexplained_dirty_tree(
        tmp_path, monkeypatch):
    bundle = _bundle(tmp_path)
    path = tmp_path / "staging.json"
    path.write_text(json.dumps(bundle))
    monkeypatch.setattr(
        "scripts.run_acceptance.repository_identity",
        lambda _root: {
            "repo_root": str(tmp_path), "commit_sha": "a" * 40,
            "clean_tree": False, "dirty_tree": True,
            "status_sha256": "b" * 64, "tracked_diff_sha256": "c" * 64,
            "changed_path_count": 1, "untracked_path_count": 0,
        })
    monkeypatch.delenv("WANGP_ALLOW_DIRTY_RUN", raising=False)
    monkeypatch.delenv("WANGP_DIRTY_RUN_REASON", raising=False)
    with pytest.raises(AcceptanceBundleError, match="clean repository"):
        run_bundle(path, db_path=tmp_path / "jobs.db")

    monkeypatch.setenv("WANGP_ALLOW_DIRTY_RUN", "1")
    monkeypatch.delenv("WANGP_DIRTY_RUN_REASON", raising=False)
    with pytest.raises(AcceptanceBundleError, match="DIRTY_RUN_REASON"):
        run_bundle(path, db_path=tmp_path / "jobs.db")


def test_completed_prefix_adopts_verified_cut_and_dependencies(tmp_path):
    from services.jobs.queue import JobQueue

    raw = tmp_path / "raw.mp4"
    final = tmp_path / "remux.mp4"
    log = tmp_path / "render.log"
    payload = b"native-av"
    raw.write_bytes(payload)
    final.write_bytes(payload)
    log.write_bytes(b"log")
    import hashlib
    digest = hashlib.sha256(payload).hexdigest()
    (tmp_path / "runtime-evidence.json").write_text(json.dumps({
        "raw_render_hash": digest,
        "remux_hash": digest,
        "runtime": {"audio_carrier": "native_h3",
                    "native_preserved": True},
    }))

    effective = {"kind": "ref2va_render", "prompt": "same",
                 "seed": 905, "image_start": "seed.png",
                 "image_refs": ["seed.png", "silent.png"],
                 "audio_guide": "turn.wav", "video_length": 56}
    source = JobQueue(tmp_path / "source.db")
    qc_evidence = tmp_path / "qc.json"
    qc_evidence.write_text(json.dumps({
        "whisper_gates": {}, "vision_judge": {}}))
    source_jid = source.submit_completed(plan_ref="source-run", clips=[{
        "clip_index": 1, **effective, "status": "done", "log": str(log),
        "mp4": str(final),
        "qc_verdict": {"verdict": "NEEDS REVIEW",
                       "path": str(qc_evidence)},
    }])
    source.close()

    class Plan:
        run_id = "prefix-run"
        clips = ({ "clip_index": 1, **effective },
                 { "clip_index": 2, **effective, "seed": 905 })

    target = JobQueue(tmp_path / "target.db")
    try:
        ids = _submit_completed_prefix(
            Plan(), target, {
                "jobs_db": str(tmp_path / "source.db"),
                "job_id": source_jid,
                "expected_sha256": digest,
            }, root=Path.cwd())
        assert target.get(ids[0]).state == "done"
        successor = target.get(ids[1])
        assert successor.state == "pending"
        assert successor.clips[0]["needs"] == ids[0]
        assert target.get(ids[0]).clips[0][
            "completed_prefix_source"]["sha256"] == digest
    finally:
        target.close()


def test_completed_prefix_chains_every_later_cut(tmp_path):
    from services.jobs.queue import JobQueue

    raw = tmp_path / "raw.mp4"
    final = tmp_path / "remux.mp4"
    log = tmp_path / "render.log"
    payload = b"native-av"
    raw.write_bytes(payload)
    final.write_bytes(payload)
    log.write_bytes(b"log")
    import hashlib
    digest = hashlib.sha256(payload).hexdigest()
    qc_path = tmp_path / "qc.json"
    qc_path.write_text(json.dumps({"whisper_gates": {}, "vision_judge": {}}))
    (tmp_path / "runtime-evidence.json").write_text(json.dumps({
        "raw_render_hash": digest,
        "remux_hash": digest,
        "runtime": {"audio_carrier": "native_h3",
                    "native_preserved": True},
    }))
    effective = {"kind": "ref2va_render", "prompt": "same",
                 "seed": 905, "image_start": "seed.png",
                 "image_refs": ["seed.png", "silent.png"],
                 "audio_guide": "turn.wav", "video_length": 56}
    source = JobQueue(tmp_path / "source.db")
    source_jid = source.submit_completed(plan_ref="source-run", clips=[{
        "clip_index": 1, **effective, "status": "done", "log": str(log),
        "mp4": str(final),
        "qc_verdict": {"verdict": "NEEDS REVIEW", "path": str(qc_path)},
    }])
    source.close()

    class Plan:
        run_id = "prefix-chain"
        clips = tuple({"clip_index": index, **effective}
                      for index in range(1, 5))

    target = JobQueue(tmp_path / "target.db")
    try:
        ids = _submit_completed_prefix(
            Plan(), target, {
                "jobs_db": str(tmp_path / "source.db"),
                "job_id": source_jid,
                "expected_sha256": digest,
            }, root=Path.cwd())
        assert [target.get(jid).clips[0]["needs"] for jid in ids[1:]] == [
            ids[0], ids[1], ids[2]]
    finally:
        target.close()


def test_completed_prefix_requires_qc_evidence(tmp_path):
    from services.jobs.queue import JobQueue

    raw = tmp_path / "raw.mp4"
    final = tmp_path / "remux.mp4"
    log = tmp_path / "render.log"
    payload = b"native-av"
    raw.write_bytes(payload)
    final.write_bytes(payload)
    log.write_bytes(b"log")
    import hashlib
    digest = hashlib.sha256(payload).hexdigest()
    (tmp_path / "runtime-evidence.json").write_text(json.dumps({
        "raw_render_hash": digest,
        "remux_hash": digest,
        "runtime": {"audio_carrier": "native_h3",
                    "native_preserved": True},
    }))
    effective = {"kind": "ref2va_render", "prompt": "same",
                 "seed": 905, "image_start": "seed.png",
                 "image_refs": ["seed.png", "silent.png"],
                 "audio_guide": "turn.wav", "video_length": 56}
    source = JobQueue(tmp_path / "source.db")
    qc_evidence = tmp_path / "initial-qc.json"
    qc_evidence.write_text(json.dumps({
        "whisper_gates": {}, "vision_judge": {}}))
    source_jid = source.submit(plan_ref="source-no-qc", clips=[{
        "clip_index": 1, **effective, "status": "done", "log": str(log),
        "mp4": str(final),
        "qc_verdict": {"verdict": "NEEDS REVIEW",
                       "path": str(qc_evidence)},
    }])
    stored = json.loads(source._db.execute(
        "SELECT clips FROM jobs WHERE job_id=?",
        (source_jid,)).fetchone()["clips"])
    stored[0]["qc_verdict"] = None
    source._db.execute(
        "UPDATE jobs SET state='done', clips=? WHERE job_id=?",
        (json.dumps(stored), source_jid))
    source._db.commit()
    source.close()

    class Plan:
        run_id = "prefix-no-qc"
        clips = ({ "clip_index": 1, **effective },
                 { "clip_index": 2, **effective })

    target = JobQueue(tmp_path / "target.db")
    try:
        with pytest.raises(AcceptanceBundleError, match="QC"):
            _submit_completed_prefix(
                Plan(), target, {
                    "jobs_db": str(tmp_path / "source.db"),
                    "job_id": source_jid,
                    "expected_sha256": digest,
                }, root=Path.cwd())
    finally:
        target.close()


def test_completed_prefix_resolves_relative_qc_from_producer_root(tmp_path):
    from scripts.run_acceptance import _require_completed_qc_evidence

    evidence = tmp_path / "qc" / "1.json"
    evidence.parent.mkdir()
    evidence.write_text("{}")
    _require_completed_qc_evidence(
        {"qc_verdict": {"verdict": "NEEDS REVIEW", "path": "qc/1.json"}},
        producer_root=tmp_path)


def test_acceptance_stages_all_media_through_render_host(tmp_path):
    from types import SimpleNamespace

    from scripts.run_acceptance import _stage_media_inputs

    calls = []

    for name in ("anchor.png", "silent.png", "speaker.png", "turn.wav"):
        (tmp_path / name).write_bytes(name.encode())

    def map_asset(path):
        calls.append(("map", path))
        return f"/remote/{Path(path).name}"

    host = SimpleNamespace(
        map_asset=map_asset,
        makedirs=lambda path: calls.append(("mkdir", path)),
        push_asset=lambda path: calls.append(("push", path)),
    )
    inputs = {
        "plates": [[str(tmp_path / "anchor.png"),
                    str(tmp_path / "silent.png")]],
        "media": {
            "plates": {
                "anchor": str(tmp_path / "anchor.png"),
                "Speaker": str(tmp_path / "speaker.png"),
            },
            "audio": [{"path": str(tmp_path / "turn.wav")}],
        },
    }
    _stage_media_inputs(inputs, host)
    assert calls == [
        ("map", str(tmp_path / "anchor.png")),
        ("mkdir", "/remote"),
        ("push", str(tmp_path / "anchor.png")),
        ("map", str(tmp_path / "silent.png")),
        ("mkdir", "/remote"),
        ("push", str(tmp_path / "silent.png")),
        ("map", str(tmp_path / "speaker.png")),
        ("mkdir", "/remote"),
        ("push", str(tmp_path / "speaker.png")),
        ("map", str(tmp_path / "turn.wav")),
        ("mkdir", "/remote"),
        ("push", str(tmp_path / "turn.wav")),
    ]


def test_acceptance_staging_requires_render_host_seams():
    from scripts.run_acceptance import _stage_media_inputs

    with pytest.raises(AcceptanceBundleError, match="RenderHost"):
        _stage_media_inputs(
            {"plates": [], "media": {"plates": {}, "audio": []}}, object())


def test_staging_requires_local_bundle_inputs_before_remote_fallback():
    from types import SimpleNamespace

    calls = []
    host = SimpleNamespace(
        map_asset=lambda path: f"/remote/{path}",
        makedirs=lambda path: calls.append(("mkdir", path)),
        push_asset=lambda path: calls.append(("push", path)),
    )
    inputs = {
        "plates": [],
        "media": {
            "plates": {"anchor": "missing.png"},
            "audio": [],
        },
    }
    with pytest.raises(AcceptanceBundleError, match="missing.png"):
        _stage_media_inputs(inputs, host)
    assert calls == []


def test_staging_handles_slashless_relative_mapping(tmp_path):
    from types import SimpleNamespace

    source = tmp_path / "asset.png"
    source.write_bytes(b"asset")
    calls = []
    host = SimpleNamespace(
        map_asset=lambda _path: "remote.png",
        makedirs=lambda path: calls.append(("mkdir", path)),
        push_asset=lambda path: calls.append(("push", path)),
    )
    _stage_media_inputs({
        "plates": [], "media": {
            "plates": {"anchor": str(source)}, "audio": []}
    }, host)
    assert calls == [("push", str(source))]


def test_invalid_bundle_plans_before_staging_and_emits_no_ledger(
        tmp_path, monkeypatch):
    bundle = _bundle(tmp_path)
    bundle["expected_cuts"] = 2
    bundle["script_lines"] = bundle["script_lines"][:1]
    path = tmp_path / "staging.json"
    path.write_text(json.dumps(bundle))

    def forbidden(_inputs, _host):
        raise AssertionError("invalid bundle must not reach staging")

    monkeypatch.setattr(
        "scripts.run_acceptance._stage_media_inputs", forbidden)
    monkeypatch.setattr(
        "scripts.run_acceptance.repository_identity",
        lambda _root: {"clean_tree": True, "dirty_tree": False})
    ledger = tmp_path / "runs.jsonl"
    with pytest.raises(AcceptanceBundleError, match="script_lines"):
        run_bundle(path, db_path=tmp_path / "jobs.db", ledger_path=ledger,
                   output_path=tmp_path / "out.mp4", host=object(),
                   vision_judge=lambda **_: {})
    assert not ledger.exists()
    assert not (tmp_path / "jobs.db").exists()


def test_invalid_completed_prefix_validates_before_staging(
        tmp_path, monkeypatch):
    bundle = _bundle(tmp_path)
    bundle["expected_cuts"] = 2
    bundle["script_lines"] = bundle["script_lines"][:2]
    bundle["audio_paths"] = bundle["audio_paths"][:2]
    bundle["plate_paths"] = bundle["plate_paths"][:2]
    bundle["media_manifest"]["audio"] = (
        bundle["media_manifest"]["audio"][:2])
    bundle["completed_prefix"] = "not-an-object"
    path = tmp_path / "staging.json"
    path.write_text(json.dumps(bundle))

    def forbidden(_inputs, _host):
        raise AssertionError("invalid prefix must not reach staging")

    monkeypatch.setattr(
        "scripts.run_acceptance._stage_media_inputs", forbidden)
    monkeypatch.setattr(
        "scripts.run_acceptance.repository_identity",
        lambda _root: {"clean_tree": True, "dirty_tree": False})
    ledger = tmp_path / "runs.jsonl"
    with pytest.raises(AcceptanceBundleError, match="completed_prefix"):
        run_bundle(path, db_path=tmp_path / "jobs.db", ledger_path=ledger,
                   output_path=tmp_path / "out.mp4", host=object(),
                   vision_judge=lambda **_: {})
    assert not ledger.exists()


@pytest.mark.parametrize("mutation,message", [
    ({"script_lines": [None]}, "script_lines"),
    ({"durations_s": 2.333}, "durations_s"),
])
def test_malformed_bundle_values_are_typed(
        tmp_path, monkeypatch, mutation, message):
    bundle = _bundle(tmp_path)
    bundle["expected_cuts"] = 1
    bundle["script_lines"] = bundle["script_lines"][:1]
    bundle["audio_paths"] = bundle["audio_paths"][:1]
    bundle["plate_paths"] = bundle["plate_paths"][:1]
    bundle["plate_paths"] = [bundle["plate_paths"][0][0],
                             bundle["plate_paths"][0][1]]
    bundle["media_manifest"]["audio"] = (
        bundle["media_manifest"]["audio"][:1])
    bundle.update(mutation)
    path = tmp_path / "staging.json"
    path.write_text(json.dumps(bundle))

    def forbidden(_inputs, _host):
        raise AssertionError("malformed values must not reach staging")

    monkeypatch.setattr(
        "scripts.run_acceptance._stage_media_inputs", forbidden)
    monkeypatch.setattr(
        "scripts.run_acceptance.repository_identity",
        lambda _root: {"clean_tree": True, "dirty_tree": False})
    with pytest.raises(AcceptanceBundleError, match=message):
        run_bundle(path, db_path=tmp_path / "jobs.db",
                   ledger_path=tmp_path / "runs.jsonl",
                   output_path=tmp_path / "out.mp4", host=object(),
                   vision_judge=lambda **_: {})


def test_bundle_runner_executes_repo_seams_and_records_assembly(
        tmp_path, monkeypatch):
    bundle = _bundle(tmp_path)
    path = tmp_path / "staging.json"
    path.write_text(json.dumps(bundle))
    output = tmp_path / "assembled.mp4"
    def fake_drain(queue, *, host, vision_judge):
        for jid in queue.list_state("pending"):
            job = queue.get(jid)
            for state in ("preflight", "rendering"):
                queue.set_state(jid, state)
            mp4 = tmp_path / f"{jid}.mp4"
            mp4.write_bytes(b"mp4")
            Path(mp4).with_name("raw.mp4").write_bytes(b"raw")
            queue.update_clip(jid, job.clips[0]["clip_index"], status="rendered",
                              log="render.log", mp4=str(mp4),
                              qc_verdict=None)
            for state in ("rendered_pending_qc", "qc", "done"):
                queue.set_state(jid, state)
        return queue.list_state("done")

    monkeypatch.setattr("scripts.run_acceptance.run_jobs.drain_once",
                        fake_drain)
    assemble_calls = []

    def fake_assemble(paths, out, host=None, *, ffmpeg_executable="ffmpeg",
                      expected_ffmpeg_version=None):
        assemble_calls.append((
            list(paths), out, host, ffmpeg_executable,
            expected_ffmpeg_version))
        Path(out).write_bytes(b"assembled")
        return {"output_path": str(out), "video_paths": list(paths)}
    monkeypatch.setattr("scripts.run_acceptance.assemble_media",
                        fake_assemble)
    monkeypatch.setattr(
        "scripts.run_acceptance.repository_identity",
        lambda _root: {"clean_tree": True, "dirty_tree": False})
    host = type("RenderHostStub", (), {
        "map_asset": staticmethod(lambda path: f"/remote/{path}"),
        "makedirs": staticmethod(lambda _path: None),
        "push_asset": staticmethod(lambda _path: None),
    })()
    result = run_bundle(
        path, db_path=tmp_path / "jobs.db", output_path=output,
        host=host, vision_judge=lambda **_: {})
    assert result["run_id"] == "acceptance-test"
    assert len(result["job_ids"]) == 6
    assert output.is_file()
    assert Path(result["ledger_path"]).is_file()


def test_lf002_golden_canary_is_mandatory_when_requested(
        tmp_path, monkeypatch):
    bundle = _bundle(tmp_path)
    bundle["expected_cuts"] = 2
    bundle["golden_canary"] = {
        "recipe_version": "lf002-archive-of-rain-20260916-seed905-native-v1"}
    bundle["script_lines"] = bundle["script_lines"][:2]
    bundle["audio_paths"] = bundle["audio_paths"][:2]
    bundle["plate_paths"] = bundle["plate_paths"][:2]
    bundle["media_manifest"]["audio"] = (
        bundle["media_manifest"]["audio"][:2])
    path = tmp_path / "staging.json"
    path.write_text(json.dumps(bundle))
    output = tmp_path / "assembled.mp4"
    pinned_ffmpeg = tmp_path / "pinned-ffmpeg"
    pinned_ffmpeg.write_text("#!/bin/sh\nexit 0\n")
    pinned_ffmpeg.chmod(0o755)

    def fake_drain(queue, *, host, vision_judge):
        for jid in queue.list_state("pending"):
            job = queue.get(jid)
            for state in ("preflight", "rendering"):
                queue.set_state(jid, state)
            mp4 = tmp_path / f"{jid}.mp4"
            mp4.write_bytes(b"mp4")
            Path(mp4).with_name("raw.mp4").write_bytes(b"raw")
            queue.update_clip(jid, job.clips[0]["clip_index"],
                              status="rendered", log="render.log",
                              mp4=str(mp4), qc_verdict=None)
            for state in ("rendered_pending_qc", "qc", "done"):
                queue.set_state(jid, state)
        return queue.list_state("done")

    monkeypatch.setattr(
        "scripts.run_acceptance.run_jobs.drain_once", fake_drain)

    assemble_calls = []

    def fake_assemble(paths, out, host=None, *, ffmpeg_executable="ffmpeg",
                      expected_ffmpeg_version=None):
        assemble_calls.append((
            list(paths), out, host, ffmpeg_executable,
            expected_ffmpeg_version))
        Path(out).write_bytes(b"assembled")
        return {"output_path": str(out), "video_paths": list(paths)}

    monkeypatch.setattr(
        "scripts.run_acceptance.assemble_media", fake_assemble)
    monkeypatch.setattr(
        "scripts.run_acceptance.repository_identity",
        lambda _root: {"clean_tree": True, "dirty_tree": False})
    monkeypatch.setenv("WANGP_LF002_FFMPEG", str(pinned_ffmpeg))

    calls = []

    def verify(**kwargs):
        calls.append(kwargs)
        return {"passed": True, "fixture": True}

    monkeypatch.setattr(
        "predict.lf002_canary.verify_lf002_canary", verify)
    host = type("Host", (), {
        "map_asset": staticmethod(lambda path: f"/remote/{path}"),
        "makedirs": staticmethod(lambda _path: None),
        "push_asset": staticmethod(lambda _path: None),
    })()
    result = run_bundle(path, db_path=tmp_path / "jobs.db",
                        output_path=output, host=host,
                        vision_judge=lambda **_: {})
    assert len(calls) == 1
    assert calls[0]["pair"] == str(output)
    assert len(assemble_calls) == 1
    assert all(path.endswith("raw.mp4") for path in assemble_calls[0][0])
    assert assemble_calls[0][2] is None
    assert assemble_calls[0][3] == str(pinned_ffmpeg)
    assert assemble_calls[0][4] == "Lavf62.3.100"
    assert result["completed_record"]["payload"]["golden_canary"] == {
        "passed": True, "fixture": True}


def test_lf002_golden_run_requires_explicit_ffmpeg_configuration(
        monkeypatch):
    from scripts.run_acceptance import _lf002_ffmpeg_config

    monkeypatch.delenv("WANGP_LF002_FFMPEG", raising=False)
    monkeypatch.delenv("WANGP_LF002_FFMPEG_EXPECTED", raising=False)
    with pytest.raises(AcceptanceBundleError, match="WANGP_LF002_FFMPEG"):
        _lf002_ffmpeg_config()
