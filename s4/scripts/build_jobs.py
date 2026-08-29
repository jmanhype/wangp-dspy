#!/usr/bin/env python3
"""S4 STEP 2 — build the six Ref2VA job configs through the repo's
gated path (Ref2VAProfile.build_settings + adapter.submit gates), then
generate the remote render driver script for the 3090.

Discipline: guide audio is per-line TTS (real audio, auth by author);
model_type per S2.5 = ref2va_lip_sync; frames = round(dur*24) clamp>=96.
"""
import json, hashlib, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # s4/
FILM = ROOT / "films" / "satans-mom"
REPO = ROOT.parent                                     # wangp-dspy
sys.path.insert(0, str(REPO))
import os
os.chdir(REPO)  # G6: MASTER_LOCK.md cwd-relative

from predict.render_profiles import Ref2VAProfile
from predict.prompt_director import RenderBrief
from predict.profile_selector import ProfileDecision
from host.wangp_adapter import WanGPAdapter, WanGPError

cut_map = json.loads((FILM / "dialogue/cut_map.json").read_text())
script = json.loads((FILM / "dialogue/script.json").read_text())
text_by_wav = {}
for c in script["cuts"]:
    for i, ln in enumerate(c["lines"], 1):
        text_by_wav[f"cut{c['cut']}_{i}.wav"] = (ln["speaker"], ln["text"])

SUBJECT = (
    "A dim stone dungeon cell lit by a single hanging lantern with a "
    "warm flickering glow; an elderly woman with gray hair in a bun in "
    "a tattered brownish cloak stands at the metal gate; a gaunt "
    "disheveled young man sits chained by wrists and ankles on a low "
    "stool; a tall pale horned figure in a long dark coat leans "
    "against the far wall, arms crossed, smirking. <Picture 1>")
STYLE = ("Larson-style painterly gothic horror: dark browns, blacks, "
         "muted earth tones, stark chiaroscuro lamplight, cinematic "
         "16mm grain, matte dark corners")

MOTION = {
    "GRANDMA": ("The old woman leans toward him, gesturing sharply "
                "with one hand, speaking angrily. <Audio 1>"),
    "PRISONER": ("The chained young man looks up at her warily, "
                 "answering in a low voice. <Audio 1>"),
    "DEVIL": ("The horned figure tilts his head, smirk widening as he "
              "speaks in a slow mocking tone. <Audio 1>"),
}
CAMERA = ("Locked-off medium shot, 480x832 portrait framing, no camera "
          "movement")

MASTER = {
    1: "/tmp/s25/master.png",
    2: str(FILM / "masters/cut2_master.png"),
    3: str(FILM / "masters/cut3_master.png"),
}
# cut_map cuts 1-2 = film cut 1, 3-4 = film cut 2, 5-6 = film cut 3
film_cut = {1: 1, 2: 1, 3: 2, 4: 2, 5: 3, 6: 3}

adapter = WanGPAdapter(output_dir=str(FILM / "renders"))
profile = Ref2VAProfile()
jobs = []
PAD_DIR = FILM / "dialogue/lines_padded"
PAD_DIR.mkdir(exist_ok=True)
import subprocess as _sp
for c in cut_map:
    wav = c["lines"][0]
    speaker, text = text_by_wav[wav]
    dur = c["duration_s"]
    # Ref2VA floor: 4s. Lines shorter are padded with TRAILING SILENCE
    # to 4.0s (declared in job meta; assembly audio = the padded wav so
    # A/V stays in sync). Only cut1 (2.808s) needs this.
    pad_note = None
    if dur < 4.0:
        src = FILM / "dialogue/lines" / wav
        dst = PAD_DIR / wav
        _sp.run(["ffmpeg", "-y", "-i", str(src), "-af",
                 "apad=whole_dur=4.0", str(dst)],
                capture_output=True, check=True)
        d = float(_sp.run(["ffprobe", "-v", "error", "-show_entries",
                           "format=duration", "-of", "csv=p=0", str(dst)],
                          capture_output=True, text=True).stdout.strip())
        dur = round(d, 3)
        guide_rel = f"lines_padded/{wav}"
        pad_note = f"padded from {c['duration_s']}s with trailing silence to {dur}s (4s Ref2VA floor)"
    else:
        guide_rel = f"lines/{wav}"
    brief = RenderBrief(
        subject=SUBJECT,
        motion=f"The {speaker.lower()} speaks: {text} " + MOTION[speaker],
        camera=CAMERA, style=STYLE,
        audio_direction=("Guide audio is this line's real TTS voice "
                         f"({speaker}); H3 audio never trusted (G4)."))
    decision = ProfileDecision(
        model="h3", resolution="768p",
        shot_length_frames=max(int(round(dur * 24)), 96),
        seed_policy="fixed_per_shot", wangp_profile="profile3")
    # gates fire here (G1/G2/G4/G5); G6 via MASTER_LOCK.md at cwd
    adapter.submit(brief, decision, profile="ref2va",
                   audio_prompt_type="A",
                   image_refs=[MASTER[film_cut[c["cut"]]]],
                   guide_duration_s=dur, shot_duration_s=dur)
    settings = profile.build_settings(
        [brief], decision,
        image_refs=[MASTER[film_cut[c["cut"]]]],
        audio_prompt_type="A",
        guide_duration_s=dur, shot_duration_s=dur)
    settings["seed"] = 42 + c["cut"]
    audio_bytes = (FILM / "dialogue" / guide_rel).read_bytes()
    jobs.append({
        "cut": c["cut"],
        "film_cut": film_cut[c["cut"]],
        "speaker": speaker,
        "text": text,
        "duration_s": dur,
        "guide_wav": guide_rel,
        "pad_note": pad_note,
        "guide_sha256": hashlib.sha256(audio_bytes).hexdigest(),
        "master": MASTER[film_cut[c["cut"]]],
        "settings": settings,
    })
    print(f"cut{c['cut']}: gates OK, frames={settings['frames_per_shot']}, "
          f"seed={settings['seed']}, {dur}s {speaker}")

out = FILM / "jobs"
out.mkdir(exist_ok=True)
(out / "jobs.json").write_text(json.dumps(jobs, indent=2))
print("saved", out / "jobs.json")
