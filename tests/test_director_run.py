import json
import pathlib

import pytest

from services.director.premises import (
    PremiseIndexError, load_lost_futures_index, resolve_premise,
)
from services.director.run import DirectorRun, DirectorRunError


def _script():
    return [{"speaker": "Mara" if i % 2 == 0 else "Ivo",
             "text": f"Turn {i + 1} is ready."} for i in range(6)]


def test_lost_futures_index_resolves_a_premise():
    index = load_lost_futures_index()
    assert index
    assert resolve_premise(index=index).id == index[0].id
    assert all(len(p.characters) >= 2 for p in index)


def test_director_run_plans_six_exact_continuation_jobs(tmp_path):
    audio = []
    for i in range(6):
        path = pathlib.Path(tmp_path) / f"turn{i + 1}.wav"
        path.write_bytes(b"wav")
        audio.append(str(path))
    plates = []
    for name in ("anchor.png", "Mara.png", "Ivo.png"):
        path = pathlib.Path(tmp_path) / name
        path.write_bytes(b"png")
        plates.append(str(path))
    dataset = pathlib.Path(tmp_path) / "runs.jsonl"
    run = DirectorRun(run_id="audit-001", premise="lf-001",
                      dataset_run_path=dataset)
    planned = run.plan(_script(), audio_paths=audio, plate_paths=plates)
    assert planned.premise_id == "lf-001"
    assert len(planned.clips) == 6
    assert all(c["frames"] == 48 for c in planned.clips)
    assert all(c["continuation_extras"]["requested_frames"] == 48
               for c in planned.clips)
    record = json.loads(dataset.read_text().splitlines()[0])
    assert record["status"] == "planned"
    assert len(record["repository"]["commit_sha"]) == 40
    assert len(record["record_sha256"]) == 64


def test_director_run_rejects_non_six_cut_input(tmp_path):
    run = DirectorRun(run_id="audit-002", premise="lf-001")
    with pytest.raises(DirectorRunError, match="exactly 6"):
        run.plan(_script()[:2], audio_paths=[], plate_paths=[])


def test_run_film_strict_flag_uses_repo_chain_path(tmp_path):
    from scripts.run_film import run_film

    script = pathlib.Path(tmp_path) / "dialogue.txt"
    script.write_text("\n".join(
        f"{'Mara' if i % 2 == 0 else 'Ivo'}: Turn {i + 1} is ready."
        for i in range(6)))
    plates_dir = pathlib.Path(tmp_path) / "plates"
    plates_dir.mkdir()
    for name in ("anchor.png", "Mara.png", "Ivo.png"):
        (plates_dir / name).write_bytes(b"png")
    audio = []
    for i in range(6):
        path = pathlib.Path(tmp_path) / f"turn{i + 1}.wav"
        path.write_bytes(b"wav")
        audio.append(str(path))
    clips = run_film(
        script, plates_dir, characters=[
            {"name": "Mara", "sn_tag": "S1", "description": "keeper"},
            {"name": "Ivo", "sn_tag": "S2", "description": "engineer"},
        ], audio_paths=audio, durations=[2.0] * 6,
        dry_run=True, continuation_mode=True)
    assert len(clips) == 6
    assert all(clip["kind"] == "ref2va_render" for clip in clips)
    assert all(clip["frames"] == 48 for clip in clips)


def test_director_run_accepts_per_cut_silent_face_pairs(tmp_path):
    audio = []
    for i in range(6):
        path = pathlib.Path(tmp_path) / f"turn{i + 1}.wav"
        path.write_bytes(b"wav")
        audio.append(str(path))
    anchor = pathlib.Path(tmp_path) / "plate.png"
    face_a = pathlib.Path(tmp_path) / "face_a.png"
    face_b = pathlib.Path(tmp_path) / "face_b.png"
    for path in (anchor, face_a, face_b):
        path.write_bytes(b"png")
    pairs = [[str(anchor), str(face_b)] if i % 2 == 0
             else [str(anchor), str(face_a)] for i in range(6)]
    premise = __import__("services.director.premises",
                         fromlist=["Premise"]).Premise(
        id="pair-test", title="Pair test", logline="pair test",
        characters=tuple({"name": "Mara" if i == 0 else "Ivo",
                           "sn_tag": f"S{i + 1}", "description": "person"}
                          for i in range(2)))
    run = DirectorRun(run_id="pair-001", premise=premise)
    planned = run.plan(_script(), audio_paths=audio, plate_paths=pairs)
    assert planned.clips[0]["image_refs"][1] == str(face_b)
    assert planned.clips[1]["image_refs"][1] == str(face_a)
