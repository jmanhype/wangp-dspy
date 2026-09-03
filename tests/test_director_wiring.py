"""Director wiring — plan_to_clips + chain advance (PR feat/director-wiring).

The director's ignition: script text in -> planner -> clips -> renders,
with ZERO hand-written job dicts. Pins the EXACT proven job shape from
the 2026-09-02 live smoke (mode REF2VA_IDENTITY_AUDIO, recipe template
prompt in cleaned runtime form, seed 904, on-grid durations,
audio_provenance with the whisper map, match-cut chaining).
"""
from __future__ import annotations

import json

import pytest

from services.director.renderers.h3_recipe import SEED as RECIPE_SEED

# ── the proven case (live smoke 2026-09-02, user-"perfect" x4) ────────

GRANDMA_LINE = "No ma'am. But the devil's been expecting you."

SCRIPT = [
    {"speaker": "Grandma", "text": GRANDMA_LINE},
    {"speaker": "Seth",
     "text": "Then I will not keep the devil waiting either."},
    {"speaker": "Grandma", "text": "Sit down, boy."},
    {"speaker": "Seth", "text": "Ma'am."},
]

CHARACTERS = [
    {"name": "Grandma", "sn_tag": "S1",
     "description": "a weathered woman with silver braids, seated left"},
    {"name": "Seth", "sn_tag": "S2",
     "description": "a lean man with soot-streaked cheeks, standing right"},
]

DURATIONS = [4.042, 2.3333333333333335, 2.3333333333333335,
             2.3333333333333335]
FRAMES = [97, 56, 56, 56]

WHISPER_MAP = "s4/films/satans-mom/qc/whisper_map.json"


def _plates(tmp_path):
    return {
        "anchor": str(tmp_path / "anchor.png"),
        "Grandma": str(tmp_path / "grandma.png"),
        "Seth": str(tmp_path / "seth.png"),
    }


def _audio_paths(tmp_path):
    return [str(tmp_path / f"clip{i:04d}.wav") for i in range(1, 5)]


def _clips(tmp_path, **kw):
    from services.director.wiring import plan_to_clips
    d = dict(
        script_lines=SCRIPT, characters=CHARACTERS,
        plates=_plates(tmp_path), audio_paths=_audio_paths(tmp_path),
        durations=DURATIONS, whisper_map=WHISPER_MAP,
    )
    d.update(kw)
    return plan_to_clips(**d)


# ── golden shape vs the proven job dict ──────────────────────────────

class TestGoldenProvenShape:
    def test_golden_first_clip_shape(self, tmp_path):
        clips = _clips(tmp_path)
        c = clips[0]
        assert c["mode"] == "REF2VA_IDENTITY_AUDIO"
        assert c["kind"] == "REF2VA_IDENTITY_AUDIO"
        # image_refs = [anchor plate, identity plates...]
        assert c["image_refs"] == [
            _plates(tmp_path)["anchor"],
            _plates(tmp_path)["Grandma"],
            _plates(tmp_path)["Seth"],
        ]
        assert c["seed"] == RECIPE_SEED == 904
        assert c["frames"] == FRAMES[0]
        assert c["fps"] == 24
        assert c["audio_guide"] == _audio_paths(tmp_path)[0]
        # audio_provenance dict with the S4 whisper map path
        prov = c["audio_provenance"]
        assert prov["whisper_map"] == WHISPER_MAP
        assert prov["keeper_window_s"][0] == 0.0
        assert prov["keeper_window_s"][1] == pytest.approx(DURATIONS[0],
                                                           abs=1e-3)

    def test_golden_prompt_template_content(self, tmp_path):
        """Prompt is the PROVEN template (cleaned runtime form)."""
        c = _clips(tmp_path)[0]
        p = c["prompt"]
        # Summary structure from the proven template (cleaned form)
        assert "[reference generation] The composition of the " \
               "composition anchor holds" in p
        assert f"(S1) says: <d>[English] {GRANDMA_LINE}</d>" in p
        # listener clause: other char listens, mouth closed
        assert "(S2) listens, mouth closed" in p
        # footer
        assert "Non-diegetic music: none" in p
        # head carries anchor staging + character definitions
        assert "two-shot composition anchor" in p
        assert "a weathered woman with silver braids" in p
        assert "a lean man with soot-streaked cheeks" in p

    def test_runtime_safe_no_tokens(self, tmp_path):
        """Cleaned form: NO <Picture N>/<Subject N> tokens, ever."""
        for c in _clips(tmp_path):
            assert "<Picture" not in c["prompt"]
            assert "<Subject" not in c["prompt"]

    def test_all_clips_share_the_proven_envelope(self, tmp_path):
        for i, c in enumerate(_clips(tmp_path)):
            assert c["mode"] == "REF2VA_IDENTITY_AUDIO"
            assert c["seed"] == 904
            assert c["frames"] == FRAMES[i]
            assert c["audio_guide"] == _audio_paths(tmp_path)[i]
            assert len(c["image_refs"]) == 3


# ── speaker-tag consistency ─────────────────────────────────────────

class TestSpeakerTagConsistency:
    def test_speaker_tag_matches_speaking_character(self, tmp_path):
        clips = _clips(tmp_path)
        # clip 2: Seth speaks -> (S2) says:
        p2 = clips[1]["prompt"]
        assert "(S2) says: <d>[English] Then I will not keep the " \
               "devil waiting either.</d>" in p2
        assert "(S1) says:" not in p2
        assert "(S1) listens, mouth closed" in p2
        # clip 3: Grandma again -> (S1) says:
        p3 = clips[2]["prompt"]
        assert "(S1) says: <d>[English] Sit down, boy.</d>" in p3
        assert "(S2) says:" not in p3

    def test_unknown_speaker_rejected(self, tmp_path):
        from services.director.wiring import plan_to_clips, WiringError
        with pytest.raises(WiringError, match="unknown speaker"):
            plan_to_clips(
                [{"speaker": "Ghost", "text": "boo"}],
                CHARACTERS, _plates(tmp_path),
                audio_paths=["a.wav"], whisper_map=WHISPER_MAP)

    def test_mismatched_sn_tag_cannot_smuggle_speech(self, tmp_path):
        """A roster whose sn_tags disagree with plate order must still
        attribute speech to the actual speaking character's tag."""
        chars = [
            {"name": "Grandma", "sn_tag": "S2",
             "description": "a weathered woman with silver braids"},
            {"name": "Seth", "sn_tag": "S1",
             "description": "a lean man with soot-streaked cheeks"},
        ]
        from services.director.wiring import plan_to_clips
        clips = plan_to_clips(
            SCRIPT[:1], chars, _plates(tmp_path),
            audio_paths=_audio_paths(tmp_path)[:1],
            durations=DURATIONS[:1], whisper_map=WHISPER_MAP)
        # Grandma speaks; her tag is S2
        assert "(S2) says:" in clips[0]["prompt"]
        assert "(S1) says:" not in clips[0]["prompt"]


# ── chain order and re-anchor cadence ────────────────────────────────

class TestChainOrderAndReAnchor:
    def test_clip1_uses_anchor_plate(self, tmp_path):
        c = _clips(tmp_path)[0]
        assert c["image_refs"][0] == _plates(tmp_path)["anchor"]

    def test_chained_cuts_point_at_previous_last_frame(self, tmp_path):
        clips = _clips(tmp_path)
        for prev, cur in zip(clips, clips[1:]):
            if cur["chain"]["re_anchor"]:
                continue  # re-anchor cuts revert to the anchor plate
            assert cur["image_refs"][0] == \
                f"chain://clip{prev['clip_index']:04d}/last_frame"

    def test_re_anchor_every_3(self, tmp_path):
        """Cuts 4, 7, ... revert to the original anchor plate."""
        clips = _clips(tmp_path)
        assert clips[3]["image_refs"][0] == _plates(tmp_path)["anchor"]

    def test_re_anchor_cadence_configurable(self, tmp_path):
        clips = _clips(tmp_path, re_anchor_every=2)
        assert clips[2]["image_refs"][0] == _plates(tmp_path)["anchor"]

    def test_chain_metadata_present(self, tmp_path):
        for c in _clips(tmp_path):
            ch = c["chain"]
            assert ch["index"] == c["clip_index"]
            assert isinstance(ch["re_anchor"], bool)
            if ch["index"] > 1:
                assert ch["previous"] == ch["index"] - 1


# ── last-frame extraction wiring (fake host) ─────────────────────────

class _FakeHost:
    def __init__(self):
        self.calls = []

    def run_probe(self, argv, timeout=30):
        self.calls.append(list(argv))
        return 0, "", ""


def _finish(q, jid, clip_index, mp4):
    """Walk a job through the LEGAL state chain to done, stamping the
    render artifacts at the rendering phase."""
    for st in ("preflight", "rendering"):
        q.set_state(jid, st)
    q.update_clip(jid, clip_index, status="rendered",
                  log="render.log", mp4=mp4, qc_verdict=None)
    for st in ("rendered_pending_qc", "qc", "done"):
        q.set_state(jid, st)


class TestChainAdvance:
    def _queue_with_chain_jobs(self, tmp_path):
        from services.jobs.queue import JobQueue
        q = JobQueue(str(tmp_path / "jobs.db"))
        clips = _clips(tmp_path)
        prev_id = None
        ids = []
        for c in clips:
            clip = dict(c)
            clip["needs"] = prev_id
            jid = q.submit(plan_ref="film", clips=[clip])
            ids.append(jid)
            prev_id = jid
        return q, ids, clips

    def test_advance_extracts_and_patches_next(self, tmp_path):
        from services.director.wiring import advance_chain
        from scripts.run_jobs import extract_last_frame
        q, ids, clips = self._queue_with_chain_jobs(tmp_path)
        host = _FakeHost()
        # mark job 1 done with an mp4
        _finish(q, ids[0], clips[0]["clip_index"],
                "render/clip0001/out.mp4")

        called = []
        real_extract = extract_last_frame
        import scripts.run_jobs as rj
        monkey = pytest.MonkeyPatch()
        monkey.setattr(rj, "extract_last_frame",
                       lambda host, mp4, png: (
                           called.append((mp4, png)),
                           real_extract(host, mp4, png)))
        try:
            advance_chain(q, host, ids[0])
        finally:
            monkey.undo()
        # ffmpeg extraction ran with the proven argv
        ffmpeg = [c for c in host.calls if c[:2] == ["ffmpeg", "-y"]]
        assert len(ffmpeg) == 1
        assert ffmpeg[0][2:6] == ["-sseof", "-0.1", "-i",
                                  "render/clip0001/out.mp4"]
        # next job's image_refs[0] patched to the extracted frame
        nxt = q.get(ids[1])
        assert nxt.clips[0]["image_refs"][0] == called[0][1]
        assert "chain://" not in nxt.clips[0]["image_refs"][0]

    def test_advance_noop_for_plain_jobs(self, tmp_path):
        from services.director.wiring import advance_chain
        from services.jobs.queue import JobQueue
        q = JobQueue(str(tmp_path / "jobs.db"))
        jid = q.submit(plan_ref="x", clips=[{
            "clip_index": 1, "kind": "r2i_pose_target", "mp4": "m.mp4"}])
        _finish(q, jid, 1, "m.mp4")
        host = _FakeHost()
        advance_chain(q, host, jid)
        assert host.calls == []  # no chain metadata -> no extraction

    def test_advance_skips_re_anchor_cut(self, tmp_path):
        """A re-anchor next cut needs NO last frame from its previous."""
        from services.director.wiring import advance_chain
        from services.jobs.queue import JobQueue
        q, ids, clips = self._queue_with_chain_jobs(tmp_path)
        # make clip 3 (whose next, clip 4, is a re-anchor cut) done
        _finish(q, ids[2], clips[2]["clip_index"],
                "render/clip0003/out.mp4")
        host = _FakeHost()
        advance_chain(q, host, ids[2])
        assert host.calls == []


# ── run_film dry-run ─────────────────────────────────────────────────

class TestRunFilm:
    def _script_file(self, tmp_path):
        f = tmp_path / "script.txt"
        f.write_text(
            "Grandma: No ma'am. But the devil's been expecting you.\n"
            "\n"
            "Seth: Then I will not keep the devil waiting either.\n"
            "Grandma: Sit down, boy.\n")
        return f

    def _plates_dir(self, tmp_path):
        d = tmp_path / "plates"
        d.mkdir()
        for n in ("anchor.png", "Grandma.png", "Seth.png"):
            (d / n).write_bytes(b"x" * 8)
        return d

    def test_dry_run_emits_n_jobs_no_host(self, tmp_path):
        from scripts.run_film import run_film
        out = run_film(self._script_file(tmp_path),
                       self._plates_dir(tmp_path),
                       characters=CHARACTERS, whisper_map=WHISPER_MAP,
                       dry_run=True)
        assert len(out) == 3
        assert out[0]["image_refs"][0].endswith("anchor.png")
        for c in out:
            assert c["mode"] == "REF2VA_IDENTITY_AUDIO"
            assert len(c["image_refs"]) == 3
        # prompts present, speaker order preserved
        assert "(S1) says:" in out[0]["prompt"]
        assert "(S2) says:" in out[1]["prompt"]
        assert "(S1) says:" in out[2]["prompt"]

    def test_parse_script_rows(self, tmp_path):
        from scripts.run_film import parse_script
        rows = parse_script(self._script_file(tmp_path))
        assert rows == [
            {"speaker": "Grandma",
             "text": "No ma'am. But the devil's been expecting you."},
            {"speaker": "Seth",
             "text": "Then I will not keep the devil waiting either."},
            {"speaker": "Grandma", "text": "Sit down, boy."},
        ]

    def test_plates_dir_discovery(self, tmp_path):
        from scripts.run_film import plates_from_dir
        plates = plates_from_dir(self._plates_dir(tmp_path),
                                 ["Grandma", "Seth"])
        assert plates["anchor"].endswith("anchor.png")
        assert plates["Grandma"].endswith("Grandma.png")
        assert plates["Seth"].endswith("Seth.png")

    def test_missing_plate_rejected(self, tmp_path):
        from scripts.run_film import run_film, RunFilmError
        d = tmp_path / "plates"
        d.mkdir()
        (d / "anchor.png").write_bytes(b"x")
        with pytest.raises(RunFilmError, match="plate"):
            run_film(self._script_file(tmp_path), d,
                     characters=CHARACTERS, whisper_map=WHISPER_MAP,
                     dry_run=True)
