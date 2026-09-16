import json
from pathlib import Path

import pytest

from scripts.run_acceptance import AcceptanceBundleError, run_bundle
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
    source_jid = source.submit_completed(plan_ref="source-run", clips=[{
        "clip_index": 1, **effective, "status": "done", "log": str(log),
        "mp4": str(final),
        "qc_verdict": {"verdict": "NEEDS REVIEW", "path": "qc.json"},
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


def test_acceptance_stages_all_media_through_render_host():
    from types import SimpleNamespace

    from scripts.run_acceptance import _stage_media_inputs

    calls = []

    def map_asset(path):
        calls.append(("map", path))
        return f"/remote/{path}"

    host = SimpleNamespace(
        map_asset=map_asset,
        makedirs=lambda path: calls.append(("mkdir", path)),
        push_asset=lambda path: calls.append(("push", path)),
    )
    inputs = {
        "plates": [["local/anchor.png", "local/silent.png"]],
        "media": {
            "plates": {
                "anchor": "local/anchor.png",
                "Speaker": "local/speaker.png",
            },
            "audio": [{"path": "local/turn.wav"}],
        },
    }
    _stage_media_inputs(inputs, host)
    assert calls == [
        ("map", "local/anchor.png"),
        ("mkdir", "/remote/local"),
        ("push", "local/anchor.png"),
        ("map", "local/silent.png"),
        ("mkdir", "/remote/local"),
        ("push", "local/silent.png"),
        ("map", "local/speaker.png"),
        ("mkdir", "/remote/local"),
        ("push", "local/speaker.png"),
        ("map", "local/turn.wav"),
        ("mkdir", "/remote/local"),
        ("push", "local/turn.wav"),
    ]


def test_acceptance_staging_requires_render_host_seams():
    from scripts.run_acceptance import _stage_media_inputs

    with pytest.raises(AcceptanceBundleError, match="RenderHost"):
        _stage_media_inputs(
            {"plates": [], "media": {"plates": {}, "audio": []}}, object())


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
            queue.update_clip(jid, job.clips[0]["clip_index"], status="rendered",
                              log="render.log", mp4=str(mp4),
                              qc_verdict=None)
            for state in ("rendered_pending_qc", "qc", "done"):
                queue.set_state(jid, state)
        return queue.list_state("done")

    monkeypatch.setattr("scripts.run_acceptance.run_jobs.drain_once",
                        fake_drain)
    def fake_assemble(paths, out):
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
