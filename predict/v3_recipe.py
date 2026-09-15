"""Versioned September 6 v3 pair recipe, recovered from the original script.

This is a baseline for comparison, not a promise of quality for new content.
Output dimensions depend on WanGP's reference-image handling: the *request*
was 480x832; the measured original output was 704x576. Do not conflate them.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class V3Recipe:
    version: str = 'v3-pair-2026-09-06-native-v1'
    resolution: str = '480x832'
    profile: int = 2
    attention: str = 'sdpa'
    seed: int = 904
    frames: int = 56
    fps: int = 24
    refs: int = 2
    audio_carrier: str = 'native_h3'
    audio_filter: str = ('silenceremove=start_periods=1:start_threshold=-40dB,'
                         'highpass=f=100,volume=9dB,atrim=0:2.4')
    tail_seek: str = '-0.05'
    golden_sha256: tuple = (
        ('cut1', 'c790452320e6893227caa0827c941a3e610403e776d7b833ae94d5ef135439a6'),
        ('cut2', '617aa35d7ed542ef75be6b89594f249220559dbeeff809a9cadc2d38556bda65'),
        ('pair', '0146285a9ea6441b4688e1651a467c9af189e9b63e1403ffbf92938825294a51'),
        ('seed', 'f40f44155a8d61862bf96b136108fd262a9a7f612bcaa04b8fa9becc32861656'),
    )


V3_RECIPE = V3Recipe()


def build_v3_prompt(*, scene: str, identities: str, speaker: str,
                    delivery: str, silent: str, silent_noun: str,
                    speaker_noun: str, soundscape: str,
                    first: bool, gesture: str = '', silent_pronoun: str = '') -> str:
    """S1/S2 are per-cut roles, not global roster identifiers.

    The speaking identity is described in prose; Picture 2 always holds the
    silent face. The audio supplies dialogue, not a second text speech track.
    """
    fields = (scene, identities, speaker, delivery, silent, silent_noun,
              speaker_noun, soundscape)
    if any(not isinstance(x, str) or not x.strip() for x in fields):
        raise ValueError('v3 prompt requires scene, identity, delivery and sound descriptions')
    seam = ('continuing from the pinned frame' if first else
            'continuing directly from the previous frame')
    pronoun = silent_pronoun or ('her' if silent_noun == 'woman' else 'his')
    return (
        'integrated_multimodal_description:\n'
        f'{scene}, {seam}. The same two people: {identities}.\n'
        f'(S1) {speaker}, on-screen speaker: {delivery}, '
        f'mouth in exact sync with the audio{gesture}.\n'
        f'(S2) {silent} shown in Picture 2 stays silent: '
        f'{pronoun} lips are pressed closed '
        'and motionless for the entire shot.\n'
        f'Closed-mouth instruction: the {silent_noun} in Picture 2 keeps '
        f'{pronoun} mouth fully closed while '
        f'the {speaker_noun} speaks.\n'
        f'overall_soundscape: {soundscape}.\n'
        'non_diegetic_music: N/A'
    )


def golden_prompt(cut: int) -> str:
    common = dict(
        scene='Same fiery torture chamber',
        identities=('the elderly grandmother with round glasses and cardigan, '
                    'and the skinny tormented soul on the rack'),
        soundscape='crackling fire, bubbling cauldron',
    )
    if cut == 1:
        return build_v3_prompt(
            **common, first=True, speaker='The elderly grandmother',
            delivery='she speaks warm coaxing English',
            gesture=', gesturing with the cookie plate',
            silent='The tormented soul', silent_noun='man', speaker_noun='grandmother')
    if cut == 2:
        return build_v3_prompt(
            **common, first=False, speaker='The tormented soul',
            delivery='he protests in exasperated English',
            silent='The elderly grandmother', silent_noun='woman', speaker_noun='soul')
    raise ValueError('golden pair has exactly cuts 1 and 2')
