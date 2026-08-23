"""RED tests: deterministic decoding for the audio-critic judge.

Live evidence (sol-max relay): the same wav scored 40 then 35, and
25 then 35 across runs — generation_kwargs() returns only
{max_new_tokens}, so decoding inherits the model's default
generation_config (SAMPLED). The judge must decode greedily by
default: do_sample=False. Kw-override semantics stay intact —
caller kwargs still win.
"""
from qc.audio_critic.criticize import generation_kwargs


def test_do_sample_false_by_default():
    kw = generation_kwargs()
    assert kw.get("do_sample") is False


def test_two_calls_identical_and_pinned():
    a, b = generation_kwargs(), generation_kwargs()
    assert a == b
    assert a["max_new_tokens"] == generation_kwargs()["max_new_tokens"]


def test_caller_overrides_still_win():
    # run_critique passes caller kwargs over the defaults — the
    # override seam stays open for future diversity-seeking evals
    base = generation_kwargs()
    merged = {**base, "do_sample": True}
    assert merged["do_sample"] is True and base["do_sample"] is False


def test_injected_fake_receives_deterministic_kwargs():
    """The seam test: a fake generate records the EXACT kwargs it
    was called with; two critique runs must hand it identical
    decoding args."""
    import base64 as _b64
    import io as _io
    import struct as _struct
    import wave as _wave

    from qc.audio_critic.criticize import run_critique

    def tiny_wav(seconds: float = 0.01) -> bytes:
        n = int(seconds * 16000)
        buf = _io.BytesIO()
        with _wave.open(buf, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(16000)
            w.writeframes(
                b"".join(_struct.pack("<h", 0) for _ in range(n)))
        return buf.getvalue()

    seen = []

    def fake_generate(prompt, **kwargs):
        seen.append(dict(kwargs))
        return ("The vocals are clear and on-beat. I would rate "
                "the flow, timing, and vocal clarity of this track "
                "as 36 out of 40.")

    audio = _b64.b64encode(tiny_wav()).decode()
    r1 = run_critique(
        "music", fake_generate, audio=audio,
        model="fake")
    r2 = run_critique(
        "music", fake_generate, audio=audio,
        model="fake")
    assert r1 and r2
    assert seen, "generate was never invoked"
    first = seen[0]
    assert first.get("do_sample") is False  # greedy by default
    # every recorded kwargs dict identical (deterministic decode)
    for later in seen[1:]:
        assert later == first
