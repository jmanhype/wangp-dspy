#!/usr/bin/env python3
"""S4 STEP 2b — emit per-cut wgp `prompt` strings (full scene + motion,
Larson style, <Picture 1>/<Audio 1> markers per wgp's multishot parser)
from the gated jobs.json. Mirrors the S2.5-proven prompt format."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILM = ROOT / "films" / "satans-mom"
jobs = json.loads((FILM / "jobs/jobs.json").read_text())

SUBJECT = (
    "A dim stone dungeon cell lit by a single hanging lantern casting a "
    "warm flickering glow; an elderly woman with gray hair in a bun, in a "
    "tattered brownish cloak, stands gripping the metal gate; a gaunt "
    "disheveled young man in a dirty light-colored shirt sits on a low "
    "stool, wrists and ankles bound in chains; a tall pale horned figure "
    "in a long dark coat leans against the far stone wall, arms crossed, "
    "smirking. <Picture 1>")

STYLE_TAIL = (
    "Larson-style painterly gothic horror: dark browns, blacks and muted "
    "earth tones, stark chiaroscuro lamplight carving the faces out of "
    "black shadow, cinematic 16mm grain, matte dark corners. Locked-off "
    "medium shot, portrait framing, no camera movement. Keep all three "
    "characters, the dungeon set and the lantern lighting unchanged for "
    "the entire shot. No text, no watermarks, no extra figures, no "
    "morphing or flicker.")

MOTION = {
    "GRANDMA": "The old woman leans toward the chained man, gesturing sharply, speaking angrily. <Audio 1>",
    "PRISONER": "The chained young man lifts his head and looks up, answering warily in a low voice. <Audio 1>",
    "DEVIL": "The horned figure tilts his head slowly, smirk widening as he speaks in a mocking drawl. <Audio 1>",
}

outdir = FILM / "jobs"
for j in jobs:
    prompt = (f"{SUBJECT}. {j['speaker']} says: \"{j['text']}\" "
              f"{MOTION[j['speaker']]}. {STYLE_TAIL}")
    (outdir / f"cut{j['cut']}_prompt.json").write_text(
        json.dumps({"cut": j["cut"], "speaker": j["speaker"],
                    "prompt": prompt}, indent=2))
    print(f"cut{j['cut']} prompt: {len(prompt)} chars")
print("done")
