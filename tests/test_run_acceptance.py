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
    with pytest.raises(AcceptanceBundleError, match="not registered"):
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
    result = run_bundle(
        path, db_path=tmp_path / "jobs.db", output_path=output,
        host=object(), vision_judge=lambda **_: {})
    assert result["run_id"] == "acceptance-test"
    assert len(result["job_ids"]) == 6
    assert output.is_file()
    assert Path(result["ledger_path"]).is_file()
