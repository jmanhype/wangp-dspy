"""Subject-mode prompt builder tests (Ref2VA full-reference format).

RED->GREEN TDD for predict/subject_prompt.py.
"""

import dataclasses

import pytest

from predict.subject_prompt import (
    SceneCast,
    SpeakerLine,
    SubjectPromptError,
    SubjectSpec,
    build_subject_prompt,
)


def make_cast(n_subjects=3):
    subs = [
        SubjectSpec(
            subject_id=1,
            name="village elder in a patched brown cloak",
            description="a weathered woman with silver braids, seated left of the brazier",
            ambient_actions="her cloak hem sways in the draft; she steadies the lantern",
        ),
        SubjectSpec(
            subject_id=2,
            name="young lamplighter",
            description="a lean boy with soot-streaked cheeks, standing center-right",
            is_speaker=True,
            ambient_actions="his hands tighten around the lamppole as he speaks",
        ),
        SubjectSpec(
            subject_id=3,
            name="market scribe",
            description="a stooped man with ink-stained fingers, seated far right",
            ambient_actions="he shuffles his ledger pages quietly",
        ),
    ]
    return SceneCast(
        subjects=subs[:n_subjects],
        style="Cinematic 16mm Ektachrome, warm tungsten palette.",
        shot_description="Medium-wide two-shot, camera locked on sticks, subjects framed left-to-right.",
        soundscape="The brazier crackles softly and wind hums through the alley.",
        music="N/A",
    )


def make_line():
    return SpeakerLine(
        subject_id=2,
        text="The lamp will hold till morning.",
        voice_description="low, unhurried, faintly hoarse",
    )


# ---------------------------------------------------------------- ordering


def test_section_order_exact():
    p = build_subject_prompt(make_cast(), make_line())
    i_sub1 = p.index("<Subject 1> (from <Picture 1>)")
    i_sub3 = p.index("<Subject 3> (from <Picture 1>)")
    i_summary = p.index("Summary: [reference generation]")
    i_ret = p.index("Retention analysis:")
    i_det = p.index("Detailed description:")
    i_shot = p.index("[Shot 1] Static Shot")
    i_sound = p.index("Overall soundscape:")
    i_music = p.index("Non-diegetic music: N/A")
    order = [i_sub1, i_sub3, i_summary, i_ret, i_det, i_shot, i_sound, i_music]
    assert order == sorted(order), f"sections out of order: {order}"
    # blank line block between subject definitions and Summary
    assert "\n\nSummary:" in p


def test_summary_and_retention_structure():
    p = build_subject_prompt(make_cast(), make_line())
    assert "Summary: [reference generation]" in p
    assert "Retention analysis:" in p
    assert "fully preserved" in p
    # every subject gets a retention line
    for sid in (1, 2, 3):
        assert f"<Subject {sid}>" in p.split("Retention analysis:")[1].split("Detailed description:")[0]


def test_detailed_description_has_style_then_shot():
    p = build_subject_prompt(make_cast(), make_line())
    det = p.split("Detailed description:")[1]
    assert det.index("Cinematic 16mm Ektachrome") < det.index("[Shot 1] Static Shot")
    assert "camera locked on sticks" in det


# ---------------------------------------------------------------- speaker binding


def test_speaker_binding_inline_d_block():
    p = build_subject_prompt(make_cast(), make_line())
    assert "<Subject 2> (S1) says: <d>[English] The lamp will hold till morning.</d>" in p


def test_speaker_binding_language_override():
    line = SpeakerLine(subject_id=2, language="Spanish", text="La lámpara aguantará.")
    p = build_subject_prompt(make_cast(), line)
    assert "<d>[Spanish] La lámpara aguantará.</d>" in p


def test_voice_description_present():
    p = build_subject_prompt(make_cast(), make_line())
    assert "low, unhurried, faintly hoarse" in p


# ---------------------------------------------------------------- non-speakers


def test_nonspeaker_lips_closed():
    p = build_subject_prompt(make_cast(), make_line())
    body = p
    for sid in (1, 3):
        seg = body.split(f"<Subject {sid}>")[1].split("<Subject ")[0]
        assert "lips completely closed" in seg
    # speaker must NOT get the clause
    spk = p.split("<Subject 2>")[1].split("<Subject 3>")[0]
    assert "lips completely closed" not in spk


# ---------------------------------------------------------------- validation


def test_missing_ambient_actions_rejected():
    cast = make_cast()
    cast.subjects[0] = dataclasses.replace(cast.subjects[0], ambient_actions="")
    with pytest.raises(SubjectPromptError, match="ambient"):
        build_subject_prompt(cast, make_line())


def test_zero_speakers_rejected():
    cast = make_cast()
    cast.subjects[1] = dataclasses.replace(cast.subjects[1], is_speaker=False)
    with pytest.raises(SubjectPromptError, match="exactly one"):
        build_subject_prompt(cast, make_line())


def test_multiple_speakers_rejected():
    cast = make_cast()
    cast.subjects[2] = dataclasses.replace(cast.subjects[2], is_speaker=True)
    with pytest.raises(SubjectPromptError, match="exactly one"):
        build_subject_prompt(cast, make_line())


def test_speaker_line_not_marked_is_speaker_rejected():
    line = SpeakerLine(subject_id=1, text="hi")
    with pytest.raises(SubjectPromptError, match="is_speaker"):
        build_subject_prompt(make_cast(), line)


def test_subject_count_limits():
    with pytest.raises(SubjectPromptError, match="1 to 9"):
        SceneCast(
            subjects=[], style="s.", shot_description="d.",
            soundscape="S.", music="N/A",
        )
    with pytest.raises(SubjectPromptError, match="1 to 9"):
        SceneCast(
            subjects=[
                SubjectSpec(subject_id=i + 1, name=f"n{i}", description="d", ambient_actions="a")
                for i in range(10)
            ],
            style="s.", shot_description="d.", soundscape="S.", music="N/A",
        )


def test_subject_ids_validated():
    with pytest.raises(SubjectPromptError):
        SubjectSpec(subject_id=0, name="x", description="y", ambient_actions="z")


def test_environment_subject_empty_ambient_ok():
    base = make_cast(2)
    cast = dataclasses.replace(
        base,
        environment_subject=True,
        subjects=[
            dataclasses.replace(base.subjects[0], ambient_actions=""),
            base.subjects[1],
        ],
    )
    p = build_subject_prompt(cast, make_line())
    assert "<Subject 1>" in p


# ---------------------------------------------------------------- determinism


def test_byte_determinism():
    a = build_subject_prompt(make_cast(), make_line())
    b = build_subject_prompt(make_cast(), make_line())
    assert a == b


def test_purity_no_training_imports():
    import inspect

    import predict.subject_prompt as m

    src = inspect.getsource(m)
    for banned in ("training", "metrics", "evaluate"):
        assert f"import {banned}" not in src
        assert f"from {banned}" not in src


# ---------------------------------------------------------------- golden


def test_golden_structure_markers():
    p = build_subject_prompt(make_cast(), make_line())
    for marker in (
        "<Subject 1> (from <Picture 1>)",
        "Retention analysis:",
        "(S1) says: <d>[English]",
        "lips completely closed",
        "Non-diegetic music: N/A",
    ):
        assert marker in p, marker
