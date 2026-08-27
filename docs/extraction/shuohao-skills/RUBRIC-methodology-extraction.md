# Reviewer Rubric — shuohao-skills METHODOLOGY extraction (epic WD-j9nx)

Reviewer: glm-reviewer (independent). Source of truth: /tmp/shuohao-skills @ main (read 2026-08-27).
Discipline: same as WD-4k56 (capture-20260827T064539Z). RULE: any fabricated file:line citation or non-verbatim "verbatim" excerpt presented as exact = automatic BLOCK of the artifact and the story.

## Scope note
Story names "seven target areas" listing eight pass files. Canonical split used here (7 artifacts):
A1 outline methodology = outline-pass.md + volume-pass.md + episode-pass.md (one pipeline);
A2 roster-pass.md; A3 profile-pass.md; A4 script-pass.md; A5 scene-pass.md + prop-pass.md (novel-art method);
A6 sheet.md (characters) + sheet.md (art) + frame.md (image-gen calling contract); A7 storyboard-pass.md + h3-prompt.md.
If the implementer ships a different split, verdicts map to whatever artifacts land; the must-contain lists below apply per area regardless.

## Global axes (apply to every artifact)
G1 Mechanism fidelity: the doc must state the WHY behind each rule as the source states it (the source gives reasons, not just rules). Paraphrase allowed; invented rationale = fabrication.
G2 file:line accuracy: every citation must resolve in /tmp/shuohao-skills. I spot-check ALL citations myself (not sampling). Soft-reflow of verbatim excerpts is acceptable ONLY if marked as normalized — WD-4k56 precedent.
G3 Attribution + NOTICE: source is Apache-2.0, (c) 2026 烁皓 (NOTICE). Every derived doc/skill must carry source URL/repo, license, holder. H3 prompt methodology must be attributed to the MiniMax-H3 official guide (h3-prompt.md:3 says "methodology learned from MiniMax-H3 official prompt guide"), NOT to shuohao.
G4 Honest adopt/adapt/pass, pipeline-specific (see per-area), explicitly separating novel-specific craft (Chinese short-drama tropes: 爽点/beat spacing, face-slap genre) from generalizable method.
G5 No silent lifting of the sample story 《渡口》 content (it is a licensed original work — NOTICE covers it; we may cite as evidence, not reuse creatively).

## Per-area must-contain lists

### A1 Outline (outline-pass / volume-pass / episode-pass)
1. Order-as-method: cut lines → merge characters → collect scenes → place beats → collect props, WITH the reason ordering matters (outline-pass.md:5-11; esp. props AFTER beats, :11-13 "the judgment criterion for a narrative prop is which 爽点 it supports").
2. Tiering as asset budget: lead 1-5 / support ≤10 / functional ≤10, functional = face-no-name; rationale = per-tier consistency cost (outline-pass.md:8; novel-outline 1.0.0 changelog).
3. Dynamic scene cap 4+⌈episodes/10⌉ clamp 5-15 with the AI-native rationale (generated scenes are cheap, cap guards cross-episode consistency) (outline-pass.md:9).
4. Beat spacing hard rules: adjacent ≤3 episodes, no vacuum at ends, earliest major not in final episode (outline-pass.md:10).
5. Narrative-prop litmus: "if it broke/lost/were swapped, does the plot collapse" + ≤8, function required (outline-pass.md:11-13).
6. Two-round doctrine: cheap skeleton round for user sign-off BEFORE episode synopses; stage-gated validate (outline-pass.md:19-26; changelog: stage beats must pass before episodes).
7. Volume-pass: summary is the ONLY downstream input ("the person doing the outline can't see the original text"); beatMaterial.evidence verbatim from source, no translation; aliases collected for cross-volume merge (volume-pass.md:5,27-28).
8. Episode-pass: batch ≤10 with drift rationale; three columns synopsis/hook/suspense; ids only from skeleton; crowdPlan; generation-difficulty warnings enum (episode-pass.md:15-22).

### A2 Roster pass
1. Two-pass architecture: scan pass never sees other chunks; note density is mandatory because downstream sees only the note (roster-pass.md:10).
2. No fabrication of characters; places/organizations/animals excluded unless they act (roster-pass.md:9).
3. Alias merging rule: same person → one entry, name = most-used form (roster-pass.md:8); aliases are the join key for cross-chunk merge (changelog 1.7.0).
4. quotes verbatim, original language, no translation, no stitching across narration breaks (roster-pass.md:11) — this is the anti-hallucination evidence chain.
5. Chunking numbers: 40k-char chunks, ~930k cap, overlap accounted; mergeCandidates + deterministic --apply split (model judges, script lands) (changelog 1.7.0).

### A3 Profile pass
1. Language-split field table: human fields follow --lang; machine fields (image.prompt, negativePrompt, tags, sheet, voice.prompt) ALWAYS English; promptLocal omitted when lang=en; voice deliberately has NO promptLocal (the copy-the-wrong-button production incident) (profile-pass.md:9-20).
2. Inferred markers: (推断)/(inferred) in ONE language only, in persona.appearance/identity but NEVER inside image prompts (would get painted) (profile-pass.md:24,44).
3. No-names doctrine, full statement: names/aliases/author/title banned from image.prompt/promptLocal/sheet because models paint their memorized character; the complement = ethnicity/era/region MUST be inferred from source and written explicitly (default = contemporary western) (profile-pass.md:28-44). lang governs who reads, not where the story happens.
4. Anti-lazy-distinctiveness: pairwise word-overlap gate >75% fails and names the pair; measured thresholds (samples max 39%, lazy clone 98%); distinctiveness lives in the individual segment, not the boilerplate; image.sheet deliberately NOT checked (63% baseline) (profile-pass.md:134-140).
5. Voice prompt doctrine: static voice identity; 4 banned categories (literary metaphor / acting direction / conditional branch / quoted lines) — only quoted-lines gated because "a gate that mis-blocks is worse than no gate"; ≤400 chars, parameter-string shape with fixed order template; engine-compat table (Qwen3-TTS/ElevenLabs/MiniMax eat it; CosyVoice/IndexTTS don't — voice comes from reference audio) (profile-pass.md:92-132; changelog 1.10.0).
6. Sheet layout: 16:9 three zones, ~34% bust baseline, one face per sheet, zone-split lighting (left directional, right flat orthographic), proportions-critical, details give way not figures (profile-pass.md:57-90).

### A4 Script pass
1. Time budget precedes everything: 4.5 chars/sec dialogue, 2.5s/action beat, ±15% gate; over → cut action, under → add conflict not filler (script-pass.md:7).
2. Common-action principle — THE AI-generation lifeline: only actions the video model has seen millions of times; precise physics interaction / micro-expressions / inch-scale motion = rewrite; drama carried by combination+timing (script-pass.md:11-18). Judgment test: "is this action common in real-life video?"
3. Hook as beat 1 with motion, gated position ≤3 beats; motion requirement is writing discipline not a gate (semantic judgment, keyword gates mis-block) (script-pass.md:20; changelog 1.1.1 three-layer doctrine: rule / sample-as-spec / gate-untouched).
4. Single-edit discipline: change one beat, re-read three (position/prop-in-hand/who's-present state recovery) (script-pass.md:24-27).
5. Dialogue ≤35 chars/line, voice differentiation (blind-name test), subtext to delivery, VO cap, crowd per outline's crowdPlan, scene-switch-free-not-attention (script-pass.md:8,29-35).
6. Common-diseases table as diagnostic vocabulary (radio-drama / literary disease / dead opening / spatial jump / padding / speechifying / omniscience / flat ending) (script-pass.md:37-48).
7. Separation: script owns drama, storyboard owns shots — no shot numbers at this layer (changelog 1.0.0).

### A5 Scene + prop passes
1. Environment-as-generated-asset premise: same environment generated dozens of times must stay identical (scene-pass.md:5-13).
2. Anchor criteria: paintable / recognizable / checkable; bad anchors are adjectives (scene-pass.md:19); prop anchors survive close-up, 3-5 each (prop-pass.md:21).
3. Lighting states reverse-derived from episodes, not a default day/night bucket set (scene-pass.md:21); prop STATE VARIANTS follow the plot arc (prop-pass.md:23).
4. Variant-over-new-scene: variantOf + changes, mother image as generation reference — each new environment = another consistency liability (scene-pass.md:27).
5. Prop triage: close-up + cross-episode + plot-bearing, all three; scene-dressing and one-off hand props excluded with the reasoning (prop-pass.md:5-15).
6. Scale phrases mandatory in prompt AND sheet (handheld/tabletop/furniture) — AI drawing handheld as furniture is a high-frequency accident, gated (prop-pass.md:25).
7. Empty scenes, no people, white plate + no hands for props, English prompts, no names; environment realism = worn materials not skin pores (scene-pass.md:23-29, prop-pass.md:27,31).

### A6 Sheet/frame (image-gen calling contract)
1. $imagegen via codex login, zero API key; graceful skip when codex absent, deliverables still produced (sheet.md:3, frame.md:3).
2. Calling contract verbatim items: env -u NODE_OPTIONS crash; one image per call, never batch (PNG bytes blow the rollout); prompt via stdin with -i; explicit copy-to-path; single failure skips without blocking; never CLI fallback (needs OPENAI_API_KEY) (sheet.md:38-47, frame.md:22-32).
3. Reference-image discipline: prompt vs reference conflict → model follows the image; refs attached by WHAT IS IN FRAME, not by scene ownership (the boat-in-frame lesson); position-state written explicitly (already-boarded); chain-reference for missing sheets; master frame kept mounted (frame.md:9-20).
4. Detail panels = crops of master view, nothing invented (sheet.md:24); single space across panels; THE SPACE MUST BE IDENTICAL ACROSS ALL PANELS; warped-perspective negative (sheet.md:32-36).
5. First-segment preview doctrine: generate one full segment set, user confirms style/consistency before batch (frame.md:36).
6. Style chaining: first approved image becomes style reference for the rest; first image sets the tone, bad first = redo (sheet.md:53-55).

### A7 Storyboard + H3 prompt
1. Three-layer structure with the zero-marginal-cut premise: segment = one generation call ≤15s non-crossing-scene; cut 2-5s hard gate; keyframe per cut, master pinned 0.00s, subs at cut marks — composition controlled by images not text (storyboard-pass.md:5-10).
2. Claim intervals beats:[start,end] continuous, no overlap/gap (storyboard-pass.md:13); dialogue seconds must fit cut (≤, with 4.4s→5s example) (:15).
3. Seconds are an order not an estimate: change seconds → must change h3Prompt, verbatim audit gate (storyboard-pass.md:14; h3-prompt.md:28).
4. Language split in prompts: all-English default, names banned (generic identities), BUT dialogue/lyrics/on-screen text stay verbatim original language in <d> blocks — one punctuation guarded (h3-prompt.md:7-9; changelog 1.0.0). zh mode exists, official-recommended is en.
5. No-names doctrine applies to storyboard prompts too (storyboard-pass.md:17) — doc must connect it to A3's rationale.
6. Soundscape IS an action instruction (the bell actually got performed) — change action → change description+soundscape+zh-gloss together (h3-prompt.md:44-45; storyboard-pass.md:48).
7. Directing craft (ungated but decisive): 3s breathing rhythm, shot-reverse-shot, entrance triplet with moving subject first, insert for key action, reaction shots free, action-on-action cutting, last-cut hook, restrained camera vocab (≤2 moves/segment) (storyboard-pass.md:19-28).
8. Common-action principle inherited from script layer (h3-prompt.md:50) — cross-layer consistency of doctrine.
9. Common diseases incl. seconds-drift, dialogue-overflow, soundscape-miss, closeup-amnesia, scene-change-without-new-segment, edit-without-reading-neighbors (storyboard-pass.md:40-51).

## Cross-cutting design rationale (CHANGELOG) — must appear somewhere in the extraction set
- Gates philosophy: deterministic code > model self-discipline; every gate has a break-case in selftest; a mis-blocking gate is worse than no gate (gate credit > gate count); explicit loud SKIP when upstream missing (never silent, never fail).
- Checklist untrustworthy doctrine: model fills JSON only; render/validate/assembly are scripts; "explanation for humans, claims for machines to check".
- Sample-as-spec: bundled 渡口 examples are the strongest soft constraint (changelog 1.1.1).
- Measure-then-threshold: every numeric threshold (400 chars, 75% overlap, 3-episode gap, 4.5 chars/s) was measured against real samples, doc must cite the measurement where the source gives it.
- docs/superpowers spec+plan: repository-migration discipline — clean-snapshot migration, verify-before-delete, stage-only-explicit-paths, private-visibility check, old-repo decoupling with minimal fixtures. Extraction set should note this only if implementer claims migration-methodology content; otherwise optional.

## Our-pipeline application matrix (implementer must address per area)
- SGFLIX bible flow (character/environment bibles, multi-ref gen): A3 no-names + inferred era/ethnicity, A5 anchors/variants/scale, A6 ref discipline and preview-first — DIRECTLY applicable; adopt/adapt reasoning must name where in the SGFLIX factory pipeline each lands (bible → multi-ref → handoffs → QC).
- wangp-dspy dataset: A1/A2/A4 methodology (batching ≤10 with drift rationale, evidence-verbatim, two-round cheap-first) generalizes to dataset construction; 爽点 spacing is genre-specific craft — must be flagged novel-specific, not silently adopted.
- X content lanes: mostly PASS expected; any adoption claim needs a concrete mechanism (e.g., voice param-string for TTS clips), not vibes.
- Novel-specific vs generalizable labeling is MANDATORY per technique. Genre-trope rules (face-slash beats, male-freq/women-freq beat types) = craft; language-split, no-names, anchors, common-action, gate philosophy, batch discipline = generalizable.

## Verdict rules
Per artifact: ADOPT / ADAPT (into which skill, concretely) / PASS — I may override implementer recommendations. Story PASS requires: all artifacts pass G1-G5, zero fabricated citations, honest matrix above, and any derived skill selftest actually re-executed by me (zero-model verified). One fabrication anywhere = BLOCK story.
