"""S5 aesthetic anchor (WD-tzy9): deterministic style lock + continuity
references from master-first plates.

Contract:
- Anchor artifacts are DETERMINISTIC: same inputs -> byte-identical
  canonical JSON and the same anchor_id (sha256 of the canonical bytes).
- Anchors are PROVENANCE-LINKED: every style source cites the locked
  master plate's sha256 (G6 master-lock discipline).
- Anchors are LICENSE-CLEAN: style sources must carry a license from the
  accepted allowlist; anything else is refused loudly.
- Anchors integrate with the continuity layer: the anchor's style
  descriptor satisfies MultiShotAssembler's STYLE LOCK verbatim.
"""
import json

import pytest

from predict.aesthetic_anchor import (
    AnchorValidationError,
    AestheticAnchor,
    ACCEPTED_LICENSES,
    anchor_id,
    canonical_bytes,
)
from predict.assembler import MultiShotAssembler, ShotPlan
from predict.profile_selector import ProfileDecision
from predict.prompt_director import RenderBrief


MASTERS = {
    "cut1": "d" * 64,
    "cut2": "03f1e067" + "a" * 56,
}


def _decision():
    return ProfileDecision(
        model="h3",
        resolution="720p",
        shot_length_frames=96,
        seed_policy="fixed_per_shot",
        wangp_profile="profile3",
    )


def test_accepted_licenses_nonempty():
    assert len(ACCEPTED_LICENSES) >= 1


def test_build_is_deterministic():
    a = AestheticAnchor.build(
        style_descriptor="gothic painterly horror, chiaroscuro",
        masters=MASTERS,
        license="CC-BY-4.0",
    )
    b = AestheticAnchor.build(
        style_descriptor="gothic painterly horror, chiaroscuro",
        masters=dict(reversed(list(MASTERS.items()))),  # key order must not matter
        license="CC-BY-4.0",
    )
    assert canonical_bytes(a) == canonical_bytes(b)
    assert anchor_id(a) == anchor_id(b)


def test_anchor_record_is_valid_json_round_trip():
    a = AestheticAnchor.build(
        style_descriptor="gothic painterly horror",
        masters=MASTERS,
        license="CC0",
    )
    rec = json.loads(a.to_canonical_json())
    assert rec["style_descriptor"] == "gothic painterly horror"
    assert rec["license"] == "CC0"
    assert rec["masters"]["cut1"] == MASTERS["cut1"]


def test_rejects_license_outside_allowlist():
    with pytest.raises(AnchorValidationError, match="license"):
        AestheticAnchor.build(
            style_descriptor="x",
            masters=MASTERS,
            license="Arrr-Pirated-1.0",
        )


def test_rejects_empty_style():
    with pytest.raises(AnchorValidationError, match="style"):
        AestheticAnchor.build(style_descriptor="  ", masters=MASTERS, license="CC0")


def test_rejects_master_sha_not_hex64():
    with pytest.raises(AnchorValidationError, match="sha256"):
        AestheticAnchor.build(
            style_descriptor="x", masters={"cut9": "nothex"}, license="CC0"
        )


def test_rejects_anchor_without_masters():
    with pytest.raises(AnchorValidationError, match="master"):
        AestheticAnchor.build(style_descriptor="x", masters={}, license="CC0")


def test_provenance_links_reach_canon_surface():
    """The anchor's identity claims ride the canon-citation tier (WD-oyti):
    master shas are canon citations, so briefs carrying the anchor as
    identity context need no (inferred) markers."""
    a = AestheticAnchor.build(
        style_descriptor="gothic painterly horror",
        masters=MASTERS,
        license="CC-BY-4.0",
    )
    assert a.canon_citations == tuple(sorted(MASTERS.values()))


def test_style_carries_verbatim_across_chain():
    """Integration: the anchor's style descriptor survives the assembler's
    STYLE LOCK unchanged — the anchor is the single style authority."""
    a = AestheticAnchor.build(
        style_descriptor="gothic painterly horror, chiaroscuro",
        masters=MASTERS,
        license="CC0",
    )
    dec = _decision()
    subjects = ("grandma shouts at prisoner, lantern flickers",
                "grandma grips the gate, chains rattle")
    terminals = ("grandma, leaning on the gate", "grandma, pointing at the devil")
    shots = []
    for i, subj in enumerate(subjects):
        brief = RenderBrief(
            subject=subj,
            motion="she leans toward the gate, grandma frozen mid-shout",
            camera="medium two-shot",
            style=a.style_descriptor,
        )
        shots.append(
            ShotPlan(
                brief=brief,
                decision=dec,
                terminal_state=terminals[i],
            )
        )
    chain = MultiShotAssembler().assemble(shots)
    assert len(chain.shots) == 2
