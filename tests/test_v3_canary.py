"""Read-only golden artifact gate, including the original A/V timing bug."""
import hashlib
import json
from types import SimpleNamespace

import pytest

from predict import v3_canary
from predict.v3_recipe import V3_RECIPE


@pytest.fixture
def artifacts(tmp_path):
    paths = {}
    for key in ('cut1', 'cut2', 'pair', 'seed'):
        paths[key] = tmp_path / key
        paths[key].write_bytes(key.encode())
    return paths


def mock_golden(monkeypatch, artifacts):
    monkeypatch.setattr(v3_canary, 'V3_RECIPE', SimpleNamespace(
        golden_sha256=tuple((key, hashlib.sha256(path.read_bytes()).hexdigest())
                            for key, path in artifacts.items()),
        frames=56, fps=24, version='test-fixtures-only'))


def streams(path):
    return [
        {'codec_type': 'video', 'nb_read_frames': '112' if path.name == 'pair' else '56',
         'r_frame_rate': '24/1', 'start_time': '0.000000'},
        {'codec_type': 'audio', 'start_time': '0.000000'},
    ]


def test_production_golden_hashes_are_original_artifacts():
    assert dict(V3_RECIPE.golden_sha256) == {
        'cut1': 'c790452320e6893227caa0827c941a3e610403e776d7b833ae94d5ef135439a6',
        'cut2': '617aa35d7ed542ef75be6b89594f249220559dbeeff809a9cadc2d38556bda65',
        'pair': '0146285a9ea6441b4688e1651a467c9af189e9b63e1403ffbf92938825294a51',
        'seed': 'f40f44155a8d61862bf96b136108fd262a9a7f612bcaa04b8fa9becc32861656',
    }


def test_hash_mismatch_records_failure_without_probing(monkeypatch, artifacts, tmp_path):
    monkeypatch.setattr(v3_canary, '_probe', lambda _: pytest.fail('must not probe wrong bytes'))
    report_path = tmp_path / 'report.json'
    with pytest.raises(v3_canary.GoldenCanaryError, match='SHA256 mismatch'):
        v3_canary.verify_v3_canary(**artifacts, report_path=report_path)
    report = json.loads(report_path.read_text())
    assert report['passed'] is False
    assert len(report['errors']) == 4
    assert artifacts['cut1'].read_bytes() == b'cut1'


def test_report_cannot_overwrite_input(artifacts):
    with pytest.raises(v3_canary.GoldenCanaryError, match='overwrite'):
        v3_canary.verify_v3_canary(**artifacts, report_path=artifacts['pair'])
    assert artifacts['pair'].read_bytes() == b'pair'


def test_matching_hashes_and_stream_contract_pass(monkeypatch, artifacts, tmp_path):
    mock_golden(monkeypatch, artifacts)
    monkeypatch.setattr(v3_canary, '_probe', streams)
    report = v3_canary.verify_v3_canary(**artifacts, report_path=tmp_path / 'report.json')
    assert report['passed'] is True
    assert report['errors'] == []
    assert report['artifacts']['pair']['streams'][0]['nb_read_frames'] == '112'


@pytest.mark.parametrize('defect', ['video_shift', 'audio_shift', 'wrong_frames', 'wrong_fps', 'no_audio'])
def test_stream_regressions_fail_closed(monkeypatch, artifacts, tmp_path, defect):
    mock_golden(monkeypatch, artifacts)

    def bad_probe(path):
        result = streams(path)
        if path.name == 'pair':
            if defect == 'video_shift':
                result[0]['start_time'] = '0.041992'
            elif defect == 'audio_shift':
                result[1]['start_time'] = '0.041992'
            elif defect == 'wrong_frames':
                result[0]['nb_read_frames'] = '106'
            elif defect == 'wrong_fps':
                result[0]['r_frame_rate'] = '25/1'
            elif defect == 'no_audio':
                result.pop()
        return result

    monkeypatch.setattr(v3_canary, '_probe', bad_probe)
    report_path = tmp_path / 'report.json'
    with pytest.raises(v3_canary.GoldenCanaryError, match='pair:'):
        v3_canary.verify_v3_canary(**artifacts, report_path=report_path)
    assert json.loads(report_path.read_text())['passed'] is False


def test_missing_artifact_records_failure(artifacts, tmp_path):
    artifacts['seed'].unlink()
    report_path = tmp_path / 'report.json'
    with pytest.raises(v3_canary.GoldenCanaryError, match='seed: unreadable'):
        v3_canary.verify_v3_canary(**artifacts, report_path=report_path)
    assert json.loads(report_path.read_text())['passed'] is False


@pytest.mark.parametrize('canary_passes', [True, False])
def test_runner_checks_canary_before_success_record(monkeypatch, tmp_path, canary_passes):
    from scripts import run_v3_native_control as runner

    jobs = []
    for index in (1, 2):
        directory = tmp_path / str(index)
        directory.mkdir()
        (directory / 'raw.mp4').write_bytes(b'native fixture')
        jobs.append(SimpleNamespace(job_id=str(index), state='done', clips=[{
            'mp4': str(directory / 'remux.mp4'),
            'image_start': str(tmp_path / 'chain.png'),
        }]))
    closed, records, checked = [], [], []
    queue = SimpleNamespace(get=lambda jid: jobs[int(jid)-1], close=lambda: closed.append(True))
    monkeypatch.setattr(runner, '_host', lambda _: object())
    monkeypatch.setattr(runner, '_ensure_assets', lambda *_: {})
    monkeypatch.setattr(runner, 'JobQueue', lambda _: queue)
    monkeypatch.setattr(runner, '_resume_jobs', lambda *_: ['1', '2'])
    monkeypatch.setattr(runner.run_jobs, '_default_vision_judge', lambda **_: object())
    monkeypatch.setattr(runner.run_jobs, 'drain_once', lambda *_, **__: 0)
    monkeypatch.setattr(runner, 'assemble_media', lambda _, output, **__: {'output_path': output})
    monkeypatch.setattr(runner, 'append_dataset_run', lambda *_, **kw: records.append(kw) or kw)

    def verify(**kwargs):
        checked.append(kwargs)
        assert records == []
        if not canary_passes:
            raise v3_canary.GoldenCanaryError('pair: golden SHA256 mismatch')
        return {'passed': True, 'fixture': True}

    monkeypatch.setattr(v3_canary, 'verify_v3_canary', verify)
    args = dict(run_id='test', db=tmp_path/'jobs.db', ledger=tmp_path/'runs.jsonl',
                output=tmp_path/'assembled.mp4', resume=True)
    if canary_passes:
        runner.run_control(**args)
        assert records[0]['payload']['golden_canary']['passed'] is True
        assert records[0]['payload']['verdict'] == 'NEEDS REVIEW'
    else:
        with pytest.raises(v3_canary.GoldenCanaryError, match='SHA256 mismatch'):
            runner.run_control(**args)
        assert records == []
    assert len(checked) == 1
    assert checked[0]['cut1'] == str(tmp_path/'1'/'raw.mp4')
    assert checked[0]['cut2'] == str(tmp_path/'2'/'raw.mp4')
    assert checked[0]['seed'] == str(tmp_path/'chain.png')
    assert closed == [True]
