# Roadmap 47 — full capability map (recovered verbatim 2026-09-03)

Status legend: [x] done (user-verified) · [~] rendered, verdict pending · [ ] open

## A. Shot types & modes
1. [~] T2VA establishing shot — text-only, no plates; scene transitions unlocked (phase 3 of active goal-card)
2. [ ] Camera movement in-cut — push-in/pan/drift via camera grammar (phase 3)
3. [~] Strict FL2VA chain link — image_start pinned seam, A/B vs match-cut (phase 1)
4. [ ] FL2VA first+last (FLF) — both ends pinned; hit an exact pose (phase 3)
5. [ ] L2VA last-frame-only — free start, pinned ending ("payoff" shots)
6. [ ] R2I pose-target — 5-frame R2V synthesizes a keyframe, FLF into it (phase 3)
7. [ ] Shot-reverse-shot coverage — singles from character plates
8. [ ] Simultaneous speakers — (S1,S2) compound tag, overlapping dialogue
9. [ ] 3rd character — third plate, three-way speaker rotation
10. [ ] Singing take — sung line, same recipe
11. [ ] Emotion takes — same line, varied delivery (whisper/fury/breaking); A/B pick
12. [ ] Freeze-then-resume — hold pose, chain from frozen frame
13. [ ] Speed ramp — flow-shift / prompt-level slow-mo and speed-up
14. [ ] Frame injection — interior keyframes mid-shot at timestamps
15. [ ] Multi-seed lottery — N seeds per shot, QC picks best

## B. Continuity & structure
16. [x] Hard cuts / new scenes — fresh anchor plate per location (proven)
17. [ ] Multi-angle scene grammar — establish / coverage / re-establish sequencing
18. [ ] Cross-cutting (parallel action) — two chains interleaved at assembly
19. [ ] Flashback insert — alternate plate (younger/wardrobe state), drop mid-scene
20. [ ] Montage — T2VA shots under one voiceover line
21. [ ] Non-dialogue beats — silent action cuts, reaction shots with no line
22. [ ] Latent chaining — "Endless H3" port: latent save/load, lossless stitch, audio-continuous; 5-10 min takes
23. [ ] Sliding window — WanGP's native >15s single-generation path
24. [ ] Re-anchor cadence tuning — measure actual drift, tune every-N-cuts empirically

## C. Audio
25. [~] Alignment-mux — whisper both tracks, offset, lock user voice to mouth (merged #67, live test pending)
26. [ ] Voice-timbre audio refs — pin which voice via audio sample conditioning
27. [ ] Ambience/sfx audio refs — dungeon tone, chains as conditioning
28. [ ] Music-video mode — rhythm guide, movement cut to beat
29. [ ] Soundtrack from reference video ("K" mode) — lip-sync to a video's audio

## D. Identity & casting
30. [ ] Wardrobe/age states — multiple plates per character, per-scene selection
31. [ ] Video references — condition on a moving clip (walking cadence, mannerisms)
32. [ ] Style plates — illustrated/graphic anchor restyles the scene
33. [ ] Character LoRA — train a character adapter for bulletproof identity

## E. Format & resolution
34. [ ] Landscape/widescreen — 832x480 and cinema ratios
35. [ ] Higher resolution — 544p/768p class; sharper, slower
36. [ ] Vertical shorts vs landscape film — per-platform output selection

## F. Control & precision
37. [ ] Control-video (v2v) — motion transfer from real footage (camera paths, blocking)
38. [ ] Pose/depth ControlNet — the union controlnets for exact body framing
39. [ ] Masks/inpainting — fix a region without re-rendering the shot

## G. Studio / autonomy (meta-layer)
40. [x] Director's first render — script→film, no hands (user-approved 2026-09-03)
41. [ ] GEPA over verdict records — prompt-slot optimization against real renders (phase 5, LAST)
42. [ ] Automated QC gate — VLM pre-screen + user eyes only on finalists
43. [ ] Drift measurement — InsightFace cosine per cut; auto-trigger re-anchors
44. [ ] ComfyUI speed trial — 3-8x per-step; also the node-ecosystem on-ramp
45. [x] Turbo closeup lane — 4-step previews (user-approved; banned for multi-ref finals)
46. [x] Batch episodes overnight — queue durability proven
47. [ ] Audience signals loop — post, measure, feed back into GEPA (the SGOS bridge)

## Working order
Phase order for the active goal-card (t_18eacc8d) covers items 1,2,3,4,6,40-adjacent
work and the Satan's Mom batch. After the user's final review + GEPA (#41), work the
remaining items BY SCENE NEED — whichever capability the next episode demands is the
next test. Items 22 (latent chaining) and 44 (ComfyUI) are the two big strategic bets.
