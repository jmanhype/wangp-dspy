"""Chain controller tests — plan builder + render-order manifest (RED first)."""
import pytest

from services.chain.controller import (
    OVERLAP_FRAMES,
    ChainPlanError,
    build_chain_plan,
    emit_render_manifest,
)
from services.chain.plan import validate_chain_plan


def _script():
    return [
        {"speaker": "Ada", "text": "The reactor is waking up."},
        {"speaker": "Bo", "text": "Then we leave now."},
        {"speaker": "Ada", "text": "Not without the core."},
    ]


def _characters():
    return [
        {"name": "Ada", "sn_tag": "S1", "description": "engineer, red jacket"},
        {"name": "Bo", "sn_tag": "S2", "description": "pilot, gray coat"},
    ]


DURATIONS = [2.3333333333333335, 2.3333333333333335, 2.3333333333333335]
# on-grid frames @24fps: 56, 56, 56 (17k+5 grid); later clips -22 overlap


class TestBuildChainPlan:
    def test_plan_validates(self):
        plan = build_chain_plan(_script(), _characters(), DURATIONS)
        validate_chain_plan(plan)

    def test_global_prompt_pins_identity(self):
        plan = build_chain_plan(_script(), _characters(), DURATIONS)
        assert "Throughout every scene" in plan.global_prompt
        assert "S1" in plan.global_prompt and "red jacket" in plan.global_prompt

    def test_shot_prompts_speaker_attributed_with_sn(self):
        plan = build_chain_plan(_script(), _characters(), DURATIONS)
        assert "S1" in plan.clips[0].shot_prompt
        assert "The reactor is waking up." in plan.clips[0].shot_prompt
        assert "S2" in plan.clips[1].shot_prompt

    def test_clip1_full_frames_later_minus_overlap(self):
        plan = build_chain_plan(_script(), _characters(), DURATIONS)
        assert plan.clips[0].frames == 56
        assert plan.clips[1].frames == 56 - OVERLAP_FRAMES
        assert plan.clips[2].frames == 56 - OVERLAP_FRAMES

    def test_audio_cumulative_starts(self):
        plan = build_chain_plan(_script(), _characters(), DURATIONS)
        assert plan.clips[0].audio.start_s == 0.0
        assert plan.clips[1].audio.start_s == pytest.approx(56 / 24)
        expected2 = 56 / 24 + (56 - OVERLAP_FRAMES) / 24
        assert plan.clips[2].audio.start_s == pytest.approx(expected2)

    def test_audio_paths_and_padding(self):
        plan = build_chain_plan(_script(), _characters(), DURATIONS,
                                audio_paths=[f"a{i}.wav" for i in range(3)])
        for i, clip in enumerate(plan.clips):
            assert clip.audio.path == f"a{i}.wav"
            assert clip.audio.padded_duration_s == pytest.approx(
                clip.frames / 24)  # apad to clip length

    def test_chaining_refs_point_at_previous_last_frame(self):
        plan = build_chain_plan(_script(), _characters(), DURATIONS)
        assert plan.clips[0].previous_clip_end_frame is None
        assert plan.clips[1].previous_clip_end_frame == {
            "clip_index": 1, "frame": 55}
        assert plan.clips[2].previous_clip_end_frame == {
            "clip_index": 2, "frame": 55 - OVERLAP_FRAMES}

    def test_seeds_deterministic_and_distinct(self):
        p1 = build_chain_plan(_script(), _characters(), DURATIONS)
        p2 = build_chain_plan(_script(), _characters(), DURATIONS)
        assert [c.seed for c in p1.clips] == [c.seed for c in p2.clips]
        assert len({c.seed for c in p1.clips}) == 3

    def test_len_mismatch_rejected(self):
        with pytest.raises(ChainPlanError):
            build_chain_plan(_script(), _characters(), DURATIONS[:2])
        with pytest.raises(ChainPlanError):
            build_chain_plan(_script()[:1], _characters(), DURATIONS)

    def test_unknown_speaker_rejected(self):
        script = [{"speaker": "Zed", "text": "hi"}]
        with pytest.raises(ChainPlanError):
            build_chain_plan(script, _characters(), [2.3333333333333335])

    def test_off_grid_duration_rejected(self):
        with pytest.raises(ChainPlanError):
            build_chain_plan(_script(), _characters(), [3.0, 3.0, 3.0])

    def test_status_starts_pending(self):
        plan = build_chain_plan(_script(), _characters(), DURATIONS)
        assert all(c.status == "pending" for c in plan.clips)

    def test_overlap_frames_configurable(self):
        plan = build_chain_plan(_script(), _characters(), DURATIONS,
                                overlap_frames=20)
        assert plan.overlap_frames == 20
        assert plan.clips[1].frames == 56 - 20


class TestRenderManifest:
    def test_shot1_uses_proven_three_ref_recipe(self):
        plan = build_chain_plan(_script(), _characters(), DURATIONS)
        manifest = emit_render_manifest(plan)
        assert len(manifest) == 3
        cfg1 = manifest[0]
        assert cfg1["image_start"] is None
        refs = cfg1["image_refs"]
        assert len(refs) == 3  # two-shot anchor + charA + charB plates
        assert cfg1["steps"] == 20
        assert cfg1["spectrum_cache"] is True
        assert cfg1["resolution"] == [480, 832]
        assert cfg1["frames"] == 56
        assert cfg1["force_fps"] == 24
        # programmatic (SN) speaker template in the prompt
        assert "S1" in cfg1["prompt"]
        assert cfg1["audio"]["apad"] is True

    def test_shot2_plus_first_frame_continuation_no_refs(self):
        plan = build_chain_plan(_script(), _characters(), DURATIONS)
        manifest = emit_render_manifest(plan)
        for cfg in manifest[1:]:
            assert cfg["image_refs"] is None  # plates stand down
            assert cfg["image_start"]["clip_index"] >= 1
            assert cfg["image_start"]["kind"] == "last_frame"
        cfg2 = manifest[1]
        assert cfg2["image_start"]["clip_index"] == 1
        assert cfg2["image_start"]["frame"] == 55
        assert cfg2["frames"] == 56 - OVERLAP_FRAMES
        assert cfg2["steps"] == 20  # recipe steps carry over
        assert cfg2["prompt"].startswith(plan.global_prompt)

    def test_shot1_prompt_prefixed_with_global(self):
        plan = build_chain_plan(_script(), _characters(), DURATIONS)
        cfg1 = emit_render_manifest(plan)[0]
        assert cfg1["prompt"].startswith(plan.global_prompt)

    def test_audio_paths_flow_into_configs(self):
        paths = [f"a{i}.wav" for i in range(3)]
        plan = build_chain_plan(_script(), _characters(), DURATIONS,
                                audio_paths=paths)
        manifest = emit_render_manifest(plan)
        assert [c["audio"]["path"] for c in manifest] == paths

    def test_seeds_flow_into_configs(self):
        plan = build_chain_plan(_script(), _characters(), DURATIONS)
        manifest = emit_render_manifest(plan)
        assert [c["seed"] for c in manifest] == [c.seed for c in plan.clips]
