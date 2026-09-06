# HANDOFF — SGFLIX Marathon v2 / wangp-dspy Production Studio

**Date:** 2026-09-05, ~21:45
**From:** Hermes agent (marathon operator)
**To:** Codex (continuation agent)
**Repo:** https://github.com/jmanhype/wangp-dspy (branch `main`, HEAD `4a471c3`)
**Render host:** `ssh 3090` (Tailscale, user straughter) — unstable HW, see §6

---

## 1. WHAT THIS PROJECT IS

An AI film production studio competing with Maestro v2.0.1 (Blizaine/Maestro,
public repo — do NOT integrate; only shared component is WanGP). Our moat is the
**learning loop**: every film → QC verdict → dataset row → GEPA optimization of
DSPy prompt signatures. Maestro has no loop. Films are the training data.

Doctrine (operator-set, BINDING):
- Everything runs through the wangp-dspy repo — not side-scripts.
- Proof by artifacts, never process claims. No "done" without a file + QC verdict.
- Rendered audio is NEVER trusted (G4 rule) — dialogue comes from VibeVoice,
  remuxed under policy.
- Operator (user) watches every film personally; VLM/Whisper gates are advisory
  filters, his eyes are the final verdict.
- Full lists, never curated. Failures documented, root-caused.

## 2. CURRENT STATE (as of handoff)

**Films banked (7, all on 3090 at `/home/straughter/marathon/v2/films/`):**
| film | length | QC |
|---|---|---|
| devilgrandma_dialogue.mp4 | ~19s dialogue | Whisper PASS |
| devilgrandma_45s.mp4 | 45s 3-act | banked (vision QC pending) |
| devilgrandma_dialogue_15s.mp4 | earlier mixed-audio version | PASS |
| aisle13_dialogue.mp4 | ~18s | Whisper PASS |
| aisle13_45s.mp4 | 45s 3-act | banked |
| (+ copies harvested to operator Mac: `~/Downloads/SGFLIX_Marathon/`) | | |

**In flight:** the v2 orchestrator (`~/marathon/bin/v2_full.py` on the 3090,
launched from the PERSISTENT path — never /tmp) is rendering the catalog:
aisle13 dialogue film (t3/5 at handoff), then magnitude, toddlertv, grovestreet,
curriculum, proximity, blockmission — each gets a 15s dialogue film + 45s
3-act film. ~7h GPU time remaining if the box stays up.

**A reboot-guard loop runs from the operator's Mac** (`/tmp/rebootguard.sh`,
process may have died with this session — re-launch if needed): every SSH
window it (1) relaunches the orchestrator if dead, from
`~/marathon/bin/v2_full.py`, (2) harvests finished films to the Mac Downloads.

## 3. THE VALIDATED PIPELINE (empirically proven, do not re-derive)

### Dialogue generation — VibeVoice-7B
- Model: `/home/straughter/models/VibeVoice-7B-hf` (symlink → /mnt/bulk)
- venv: `/home/straughter/vb7-venv` (transformers from SOURCE, 5.17.0.dev0)
- **CRITICAL API (7 attempts to find — use exactly this):**
  ```python
  from transformers import AutoProcessor, AutoModelForTextToWaveform, set_seed
  proc = AutoProcessor.from_pretrained(MODEL)
  model = AutoModelForTextToWaveform.from_pretrained(MODEL, device_map="auto")
  conv = [{"role":"0","content":[{"type":"audio","url":"<voice ref wav>"},
                                  {"type":"text","text":"<line>"}]}]
  inputs = proc.apply_chat_template(conv, return_dict=True, tokenize=True,
                                    add_generation_prompt=True).to(model.device, model.dtype)
  audio = model.generate(**inputs)
  proc.save_audio(audio, out_wav)
  ```
- **ONE turn = ONE call with ONE speaker's ref** (per-turn isolation; the
  operator's explicit fix — never mix speakers in a file).
- Voice refs: grandma `/home/straughter/grandma_2s.wav`; male soul
  `/home/straughter/good_prisoner.wav`.
- Output is LOW AMPLITUDE (mean -20dB); slices get `highpass=f=100,volume=6dB`.
- wgp rejects audio guides <2s (pad short lines with `apad`).

### Render — H3 Ref2VA (Mode B chain, per-turn dialogue cuts)
Per cut (see `predict/continuation_lane.py` in the repo — now first-class):
```
model_type minimax_h3_ref2va_pruned, image_prompt_type "S",
image_start = previous cut's LAST frame (ffmpeg -sseof -0.05),
video_prompt_type "I", image_refs=[same frame],
audio_prompt_type "A", audio_guide = that turn's wav,
video_length = 17k+5 grid snapped, resolution "480x832", seed 904,
prompt: (S1)=speaker exact-sync / (S2) silent closed-mouth, swapped per turn
```
Render: `cd ~/Wan2GP && ./venv/bin/python wgp.py --process <settings.json> --profile 3 --attention sdpa`
(spawn via Python subprocess start_new_session=True; profile 2 for 362f packs).
Seam measured 3.0→2.1/255 across 5-cut chains.

### Mode A (45s films)
3× 362f "act" renders (SHOT 1 / CUT TO prompt structure inside each), chained
last-frame, concat'd raw. Acts pull their narrative from the same premise turns.

### QC gate
- Whisper (`~/.local/bin/whisper <wav> --model small`) transcript vs intended
  script per turn; word-match ≥0.5 = PASS. Live implementation:
  `~/marathon/bin/qc_gate.py` + `~/marathon/bin/build_turns.py` (premise table).
- Repo-side: `predict/continuation_lane.py::transcript_judge` plugs into
  `qc/audio_critic/ref2va_stage.py::run_ref2va_qc_stage(judge=...)`.
- **NOT YET BUILT:** Qwen3.8-Max vision judge (right mouth moving / right
  action on screen, per-cut frames). ModelScope API token for
  Qwen3.8-Max is in operator's env (memory: ms-7025bdc7...). Build this next
  as a judge callable; the operator explicitly wants both lanes.

## 4. REPO WORK (the "bake-back" — partially done)

Commits pushed tonight: `4f56093` (recipe doc), `c554609` (marathon infra),
`4a471c3` (continuation lane + transcript judge, 9 tests green).

**Remaining bake (priority order):**
1. Port `v2_full.py` orchestration into `services/` as a module (premise
   table → per-turn jobs → chain → concat → QC → dataset record). The
   3090 script stays as a thin launcher of the repo version.
2. Qwen3.8 vision judge (above).
3. Wire magnitude-and-later films through `WanGPAdapter.render_for_job()`
   with `ContinuationExtras` — first fully-repo-executed film since August.
4. Emit `datasets/runs/` records per film (GEPA pass #2 needs ~16+ rows).
5. Speaker-ID manifest port (idea from Maestro: immutable per-character
   speaker binding at job-config level).
6. PDD 8-step acceleration: handler supports it (`models/minimax_h3/minimax_h3_handler.py`
   PDD_INFOS) but PDD weights are NOT on disk. Search HF for MiniMax H3 PDD
   checkpoints; A/B against 20-step (same premise+seed, operator judges parity).

## 5. CONTENT LIBRARY

- Premise index: skill `sgflix-lost-futures-index` (186 entries). The 8 in the
  current marathon are the ranked ownable lanes. Next candidates: Inner Voltage,
  Darkknight Sentai, FNAF CCTV.
- Aesthetics: gist `800478c20f021a8a06c22800f36ee7e3` (Film Science Bible —
  stocks/lenses/degradation as prompt payload).
- Plates: generated via gpt-image (operator's Hermes `image_generate`),
  VLM-QC'd BEFORE render (flat-fill anti-tiling prompts; style ref image at
  `~/Library/Application Support/Hermes/composer-images/composer_2026-08-27_05-01-44-923_a95023.png`
  for Far Side style). Plates live at `/home/straughter/marathon/*_plate.png`.

## 6. OPS RUNBOOK (3090 hardware is UNSTABLE)

- The z690 hard-hangs under sustained GPU load (~every 15-150 min; one 5h+
  stable window occurred). Journal of a dead boot shows NO panic/OOM/thermal —
  logs just stop → suspected PSU sag or board-level freeze. WiFi connected
  (wpa_supplicant) — ethernet would fix the network-blip layer. Zombie services
  dark-factory-watcher / df7-autofire / claude-proxy were crash-looping;
  user-level ones disabled (`systemctl --user disable --now dark-factory-watcher
  df7-autofire`); claude-proxy needs sudo.
- On any SSH window: check `tail ~/marathon/v2/full.log`, `pgrep -f bin/v2_full`,
  relaunch from `~/marathon/bin/v2_full.py` if dead, harvest films.
- Disk: root was 91%; ~200GB moved to /mnt/bulk/straughter with symlinks
  (Maestro, ACE-Step, ComfyUI, ai-toolkit, qwen38, VibeVoice weights). Root
  still tight (~30G free) — gzip old Wan2GP/outputs if needed.
- WanGP zombie renders + `/tmp/wgp_queue.lock` = false "Queue completed":
  check log mtime vs clock, `pkill -9 -f wgp`, rm lock.

## 7. DO NOT

- Do not integrate Maestro (operator decision). Port ideas only.
- Do not touch the operator's X profile (standing rule).
- Do not trust FL2VA GV+K chaining — anchors frame 0 (wgp.py:7479
  start_frame=0; a tail patch exists but content tests preferred Ref2VA).
- Do not run mixed-speaker audio into a render.
- Do not claim a film is done without the QC verdict + file on disk.

## 8. SESSION CONTEXT

Full history: Hermes session `20260825_151359_d2a96f` (searchable). Key
artifacts on 3090: `~/marathon/` (v1 films + manifest), `~/marathon/v2/`
(dialogue era: films/, dialogue/, qc_verdicts.json, premise_turns.json,
driver.log, recovery.log). Mac: `~/Downloads/SGFLIX_Marathon/`.

The operator's morning spec (current target): all 8 premises in BOTH shapes —
15s films = 5 chained dialogue cuts; 45s films = three 15s packs stitched —
per-speaker isolated audio, QC-gated, then continue the index with dialogue.
