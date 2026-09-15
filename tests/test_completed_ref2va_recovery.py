import hashlib
import json
from pathlib import Path

import pytest

from host.ref2va_recovery import recover_completed_render
from host.wangp_adapter import WanGPError


@pytest.fixture
def case(tmp_path):
    old, new = tmp_path/'render-old', tmp_path/'render-new'
    old.mkdir(); new.mkdir()
    native = b'native audiovisual bytes'
    digest = hashlib.sha256(native).hexdigest()
    wire = {'video_length':56, 'prompt':'the correct prompt'}
    evidence = {'mapped_asset_sha256': {'guide.wav':'a'*64},
                'wgp_code_sha256': {'wgp.py':'b'*64}, 'wire_settings_sha256':'c'*64}
    log = ('Encoding H3 prompt and references\nDenoising 20/20\n'
           'Video file saved to Path: outputs/2026 Grandma speaks, dear.mp4\n'
           'Queue completed: 1/1 tasks in 18m 34s\n')
    (old/'wgp-settings.json').write_text(json.dumps(wire))
    (old/'conditioning-evidence.json').write_text(json.dumps(evidence))
    (old/'render.log').write_text(log)
    class Host:
        def __init__(self): self.calls=[]
        def map_path(self, path): return '/w/new'
        def run_probe(self, argv, timeout):
            self.calls.append(argv)
            if argv[0]=='readlink': return 0, argv[-1]+'\n', ''
            if argv[0]=='sha256sum': return 0, digest+'  native\n', ''
            if argv[0]=='ffprobe': return 0, '56\n', ''
            assert argv[0] in {'test','cp'}, 'recovery must never launch WanGP'
            return 0, '', ''
        def fetch_file(self, remote, local): Path(local).write_bytes(native)
        def write_text(self, path, text): self.mirrored_log=(path,text)
    return dict(host=Host(), recovery={'source_dir':str(old), 'native_sha256':digest,
                'reason':'operator-approved recovery after filename fix'}, wire=wire,
                conditioning=evidence, settings_local=new/'settings.json',
                raw_local=new/'raw.mp4', wgp_root='/w', outputs_dir='/w/outputs')


def test_recovers_exact_saved_native_without_render_or_evidence_mutation(case):
    old = Path(case['recovery']['source_dir'])
    before = {p.name:p.read_bytes() for p in old.iterdir()}
    result = recover_completed_render(**case)
    assert result.read_bytes() == b'native audiovisual bytes'
    assert before == {p.name:p.read_bytes() for p in old.iterdir()}
    proof = json.loads(result.with_name('recovery-evidence.json').read_text())
    assert proof['re_rendered'] is False and proof['qc_waived'] is False
    assert ['cp','/w/outputs/2026 Grandma speaks, dear.mp4','/w/new/raw.mp4'] in case['host'].calls
    assert 'Queue completed: 1/1' in case['host'].mirrored_log[1]


@pytest.mark.parametrize('changed', ['wire','mapped_asset_sha256','wgp_code_sha256','wire_settings_sha256'])
def test_changed_conditioning_refused_before_copy(case, changed):
    if changed == 'wire': case['wire'] = {**case['wire'], 'prompt':'other film'}
    else: case['conditioning'] = {**case['conditioning'], changed:'changed'}
    with pytest.raises(WanGPError, match='differ|changed'):
        recover_completed_render(**case)
    assert not case['host'].calls


@pytest.mark.parametrize('invalid', ['incomplete','multishot','path_escape','ambiguous','not_save_line'])
def test_invalid_log_never_adopts(case, invalid):
    log_path = Path(case['recovery']['source_dir'])/'render.log'
    log = log_path.read_text()
    if invalid == 'incomplete': log = log.replace('Queue completed:', 'Queue unfinished:')
    if invalid == 'multishot': log += '[MULTISHOT]\n'
    if invalid == 'path_escape': log = log.replace('outputs/2026', '../2026')
    if invalid == 'ambiguous': log += 'Video file saved to Path: outputs/another.mp4\n'
    if invalid == 'not_save_line': log = log.replace('Video file saved to Path:', 'Prompt mentions:')
    log_path.write_text(log)
    with pytest.raises(WanGPError): recover_completed_render(**case)
    assert not case['host'].calls


def test_expected_hash_is_required_and_checked(case):
    case['recovery']['native_sha256'] = 'd'*64
    with pytest.raises(WanGPError, match='SHA256'): recover_completed_render(**case)
    assert not any(c[0]=='cp' for c in case['host'].calls)


def test_source_namespace_escape_rejected(case, tmp_path):
    case['recovery']['source_dir'] = str(tmp_path.parent)
    with pytest.raises(WanGPError, match='namespace'): recover_completed_render(**case)
    assert not case['host'].calls


def test_recovery_requires_reason(case):
    case['recovery']['reason']=''
    with pytest.raises(WanGPError, match='reason'): recover_completed_render(**case)


def test_still_prompt_requires_observations_not_copyable_zero_scores():
    from qc.audio_critic.modelscope_vision_judge import ModelScopeVisionJudge
    prompt=ModelScopeVisionJudge._prompt('grandma','speaking')
    assert '"mouth_activity": 0.0' not in prompt
    assert 'notes' in prompt and 'visible observations' in prompt
    assert 'no default scores' in prompt.replace('there are no ', 'no ')


def test_resume_appends_attempt_and_keeps_failed_history(tmp_path):
    from services.jobs.queue import JobQueue
    from scripts.run_v3_native_control import _resume_jobs
    from predict.v3_recipe import golden_prompt
    queue=JobQueue(str(tmp_path/'jobs.db'))
    try:
        ids=[]
        for idx in [1,2]:
            clip={'clip_index':idx,'recipe_name':'golden_v3','seed':904,'prompt':golden_prompt(idx)}
            if ids: clip['needs']=ids[0]
            ids.append(queue.submit(plan_ref='canary', clips=[clip]))
        queue.set_state(ids[0], 'preflight'); queue.set_state(ids[0], 'rendering')
        queue.record_failure(ids[0], failure_class='render_error')
        queue.set_failure_detail(ids[0], 'filename discovery failed')
        queue.record_attempt_failure(ids[0],failure_class='render_error',failure_detail='filename discovery failed')
        queue.set_state(ids[0], 'failed')
        history=queue.attempt_history(ids[0])
        recovery={'source_dir':'/prior', 'native_sha256':'a'*64,'reason':'after filename fix'}
        assert _resume_jobs(queue,'canary',recovery)==ids
        after=queue.attempt_history(ids[0])
        assert after[:len(history)]==history
        assert len(after)==len(history)+1
        assert queue.get(ids[0]).state=='pending'
        assert queue.get(ids[1]).clips[0]['needs']==ids[0]
        assert queue.get(ids[0]).clips[0]['completed_render_recovery']==recovery
    finally: queue.close()
