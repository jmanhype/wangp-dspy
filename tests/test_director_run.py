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


def test_director_run_rejects_non_six_cut_input(tmp_path):
    run = DirectorRun(run_id="audit-002", premise="lf-001")
    with pytest.raises(DirectorRunError, match="exactly 6"):
        run.plan(_script()[:2], audio_paths=[], plate_paths=[])
