"""Regressions at the WanGP dispatch/AV boundary, not mock score success."""
import ast
import json
from pathlib import Path

import pytest

from predict.ref2va_settings import ref2va_wire_settings, Ref2VASettingsError
from predict.v3_recipe import V3_RECIPE, golden_prompt

ROOT = Path(__file__).resolve().parents[1]


def wire_fixture(tmp_path, cut=1):
    return {
        'model_type': 'minimax_h3_ref2va_pruned', 'prompt': golden_prompt(cut),
        'image_prompt_type': 'S', 'image_start': str(tmp_path / 'seed.png'),
        'image_refs': [str(tmp_path / 'seed.png'), str(tmp_path / 'silent.png')],
        'video_prompt_type': 'I', 'audio_prompt_type': 'A',
        'audio_guide': str(tmp_path / 'guide.wav'), 'audio_guide2': None,
        'video_source': None, 'video_guide': None, 'keep_frames_video_source': '',
        'video_length': 56, 'resolution': '480x832', 'seed': 904,
    }


@pytest.mark.parametrize('cut', [1, 2])
def test_prompts_equal_recovered_generator_verbatim(cut):
    # Parse only: importing this historical script would generate audio/render.
    tree = ast.parse((ROOT / 'datasets/runs/provenance/v3_pair_generator.py').read_text())
    recovered = next(ast.literal_eval(n.value) for n in tree.body
                     if isinstance(n, ast.Assign)
                     and any(isinstance(t, ast.Name) and t.id == f'CUT{cut}' for t in n.targets))
    assert golden_prompt(cut) == recovered


@pytest.mark.parametrize('field', ['script', 'shots', 'shot_count', 'frames_per_shot'])
def test_ref2va_rejects_multishot_dispatch_even_empty_fields(tmp_path, field):
    doc = wire_fixture(tmp_path)
    doc[field] = ''
    with pytest.raises(Ref2VASettingsError, match='multishot dispatch'):
        ref2va_wire_settings(doc)


def test_wire_payload_retains_every_conditioning_input_not_metadata(tmp_path):
    doc = wire_fixture(tmp_path)
    expected = dict(doc)
    doc.update(audio_policy={'discard_rendered_audio': False},
               speaker_manifest={'turns': []}, recipe_name='golden_v3', profile=2,
               requested_frames=56, audio_provenance={'script': 'must not leak'})
    assert ref2va_wire_settings(doc) == expected
    assert not ref2va_wire_settings(doc).get('script')  # actual WanGP dispatch predicate


@pytest.mark.parametrize('field', ['image_start', 'audio_guide', 'image_refs'])
def test_unresolved_conditioning_refused_before_transport(tmp_path, field):
    doc = wire_fixture(tmp_path)
    doc[field] = ['chain://clip1/frame'] if field == 'image_refs' else 'chain://clip1/frame'
    with pytest.raises(Ref2VASettingsError):
        ref2va_wire_settings(doc)


def test_profile_golden_payload_has_no_multishot_defaults(tmp_path):
    from predict.render_profiles import Ref2VAProfile
    from predict.audio_dataplane import AudioGuideProvenance
    from types import SimpleNamespace
    doc = wire_fixture(tmp_path)
    for path in [*doc['image_refs'], doc['audio_guide']]:
        Path(path).write_bytes(b'unit-fixture')
    prov = AudioGuideProvenance(doc['audio_guide'], doc['audio_guide'], doc['audio_guide'], (0, 2.096))
    result = Ref2VAProfile().build_settings(
        [SimpleNamespace(subject='speaker', motion='talk')], None,
        image_refs=doc['image_refs'], image_start=doc['image_start'],
        audio_guide=doc['audio_guide'], audio_prompt_type='A',
        guide_duration_s=2.096, shot_duration_s=56/24,
        audio_provenance=prov, continuation=True, profile=2,
        recipe_name='golden_v3', legacy_prompt=golden_prompt(1), seed=904)
    assert ref2va_wire_settings(result) == doc
    assert result['audio_policy']['discard_rendered_audio'] is False
    assert result['recipe_version'] == V3_RECIPE.version


def test_three_stills_cannot_claim_lip_sync_even_with_perfect_scores():
    from qc.audio_critic.vision_judge import run_vision_judge
    result = run_vision_judge('clip.mp4', expected_speaker='grandma', expected_action='speaks',
        judge=lambda **kw: dict(mouth_sync=1, action_match=1, speaker_attribution=1))
    assert result.passed
    assert result.mouth_sync is None
    assert result.av_sync_verified is False


def test_native_post_whisper_rejects_wrong_speech_despite_correct_guide(tmp_path):
    from qc.audio_critic.ref2va_stage import run_ref2va_qc_stage, Ref2VAQCStageError
    guide, video = tmp_path / 'guide.wav', tmp_path / 'native.mp4'
    guide.write_bytes(b'guide'); video.write_bytes(b'native')
    def transcribe(path):
        return 'Oh hush now dear have a cookie' if Path(path) == guide else 'speaks the lard in your hung harrick'
    with pytest.raises(Ref2VAQCStageError, match='post'):
        run_ref2va_qc_stage({'model_type': 'minimax_h3_ref2va_pruned',
                            'audio_policy': {'discard_rendered_audio': False}}, judge=None,
                           pre_audio_path=str(guide), post_audio_path=str(video),
                           intended_text='Oh hush now dear have a cookie', whisper_transcriber=transcribe)


def test_last_frame_command_is_the_recovered_command():
    from scripts.run_jobs import extract_last_frame_argv
    assert extract_last_frame_argv('c1.mp4', 'seed.png') == [
        'ffmpeg', '-y', '-v', 'error', '-sseof', '-0.05', '-i', 'c1.mp4',
        '-update', '1', '-frames:v', '1', 'seed.png']


def test_assembly_uses_recovered_av_filter_not_packet_copy(tmp_path):
    from services.director.wiring import assemble_media
    paths = [tmp_path / 'c1.mp4', tmp_path / 'c2.mp4']
    for p in paths:
        p.write_bytes(b'fixture')
    output = tmp_path / 'pair.mp4'
    def runner(argv):
        output.write_bytes(b'assembled'); return 0
    result = assemble_media([str(p) for p in paths], str(output), runner=runner)
    assert result['command'] == [
        'ffmpeg','-y','-v','error','-i',str(paths[0]),'-i',str(paths[1]),
        '-filter_complex','[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[v][a]',
        '-map','[v]','-map','[a]','-c:v','libx264','-crf','18','-c:a','aac',str(output)]


def test_v3_audio_prep_retains_rate_and_does_not_force_grid_padding(tmp_path):
    import math, struct, wave, shutil
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
        pytest.skip('ffmpeg/ffprobe required for real audio prep test')
    from predict.audio_prep import prepare_v3_turn_audio
    source, out = tmp_path / 'source.wav', tmp_path / 'guide.wav'
    rate = 24000
    samples = [0] * int(.3 * rate) + [int(2000 * math.sin(2 * math.pi * 200 * i / rate))
                                     for i in range(int(2.1 * rate))]
    with wave.open(str(source), 'wb') as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(rate)
        f.writeframes(struct.pack('<' + 'h' * len(samples), *samples))
    result = prepare_v3_turn_audio(str(source), str(out), speaker_id='test')
    assert 2.0 <= result['measured_duration_s'] < 2.2
    assert result['tail_padding_s'] == 0
    assert V3_RECIPE.audio_filter in result['command']
    assert '-ar' not in result['command'] and '-t' not in result['command']
    with wave.open(str(out)) as f:
        assert f.getframerate() == rate


def test_missing_conditioning_on_host_fails_before_launch(tmp_path):
    from host.ref2va_evidence import measure_conditioning
    class Host:
        def run_probe(self, argv, timeout):
            return 1, '', 'missing'
    with pytest.raises(ValueError, match='conditioning probe'):
        measure_conditioning(Host(), wire_fixture(tmp_path), wgp_root='/wgp')


def test_golden_replay_never_reseeds_on_vision_failure():
    from services.jobs.executor import JobExecutor
    executor = JobExecutor(queue=None, preflight=lambda j: None,
                           render=lambda c: None, qc=lambda c: None)
    assert executor._retry_visual_gate(None, {'recipe_name': 'golden_v3', 'seed': 904}, 'bad') is False
