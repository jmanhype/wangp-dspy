# T0 Runbook — Story 6 (WD-t6i7): first cross-project dogfood render

Status: T0 PREP ONLY (no live render yet). Prepared by deepseek-fixer.
Target: render ONE 96-frame (4s) H3 shot on the 3090 through the
paivot-hermes adapter, inside a Hermes session, plugin tools ONLY.

Verified on 2026-08-22 (all probes live, see "Ground truth"):

- pvg/nd/vlt binaries at ~/.local/bin/ match the adapter pins
  (be1d179b…/7b818eec…/4ef09767…) — driver/launcher.py:45-50.
- pvg resolves the PROJECT from the git root of its cwd: `pvg loop
  status` fails in /tmp ("cannot determine project root"), succeeds in
  /Users/Shared/HermesWorkspace/wangp-dspy ("No active loop"). The
  executor spawns pvg with cwd=project_root (driver/executor.py:667),
  so an external project root binds CORRECTLY — no code gap.
- wangp-dspy perms drwxr-xr-x (not group/world-writable) — passes
  _validate_root_dir (executor.py:114-125).
- nd list shows: WD-j9nx [epic], WD-t6i7 [task] "Real 3090 smoke
  render" — story is seeded.
- 3090: GPU 23340/24576 MiB USED (the 27B critic is loaded), tmux
  window `vllm` exists; critic served at 127.0.0.1:11434 on the 3090
  (ollama, model q38u-v2:latest, 27.3B Q4_K_M).
- Wan2GP: venv /home/straughter/Wan2GP/venv/bin/python + wgp.py exist.

## GAPS FOUND (documented, NOT worked around)

1. **No critic wiring exists in wangp-dspy (REAL GAP, pre-render
   blocker for the live session).** Nothing in the repo configures an
   LM: no `dspy.configure(lm=…)`/`dspy.LM` anywhere in src/. RenderQC
   (wangp_dspy/render_qc.py:107) is a bare `dspy.ChainOfThought` —
   it raises "No LM is loaded" unless the CALLER configures one, and
   WanGPAdapter (wangp_adapter.py) takes `qc_factory` but has no
   production critic constructor. The dogfood session must configure
   the LM before invoking the pipeline (step 6 below) or story 6 must
   add a small wiring module in its own PR. NOT fixed in T0.
   Note: RenderQC accepts any dspy-compatible LM, including
   `ollama_chat/q38u-v2` via api_base. It is a TEXT critic — the video
   path is an input field (story-5 QB1 seam), the model does not watch
   frames. Acceptable for the smoke; a true VLM critic is a later story.
2. **GPU contention (operational, not code).** The 27B critic occupies
   23.3/24.5 GB. An H3 render cannot fit alongside it. The session MUST
   free the GPU before render and reload the critic after:
   `ssh 3090 'ollama stop q38u-v2'` (or stop the vllm tmux window),
   render, then re-serve. Render and QC are sequential by design.
3. **Critic endpoint is 3090-local.** Port 11434 is bound to 127.0.0.1
   on the 3090 only. From the Mac the session needs the tunnel from
   memory: `ssh -f -N -L 11434:127.0.0.1:11434 3090`, then
   api_base http://localhost:11434.

## T0 session steps (who runs what)

Pre-session (operator, once):
1. Create fresh private dirs for this dogfood run (0700, outside both
   repos), e.g. ~/paivot-dogfood/{evidence,index,registry,home}.
2. Write PAIVOT_LAUNCHER_CONFIG (JSON, one line) — the plugin's only
   binding surface (adapters/plugin/__init__.py:198-220 reads it):

```json
{
  "project_root": "/Users/Shared/HermesWorkspace/wangp-dspy",
  "home": "/Users/speed/paivot-dogfood/home",
  "evidence_root": "/Users/speed/paivot-dogfood/evidence",
  "index_dir": "/Users/speed/paivot-dogfood/index",
  "registry_dir": "/Users/speed/paivot-dogfood/registry",
  "role": "developer",
  "child_identity": "story6-dogfood",
  "profile": "default",
  "session_id": "sess-story6-t0",
  "run_id": "run-wd-t6i7-t0",
  "consent": true,
  "verify_command": null
}
```

   Notes: role=developer (claim + deliver + insight_append; accept
   needs a pm_acceptor executor — see step 8). project_root is the
   wangp-dspy repo — verified above that pvg binds to it via cwd.
   Do NOT point evidence_root at either repo's existing stores.

Session start (agent, in Hermes):
3. Operator enables the plugin:
   plugins.entries.paivot-driver.settings.enabled: true
   (or /paivot-enable). on_session_start injects the insight digest
   (ledger is empty in this fresh evidence root — expected).
4. Capability minting: the host/orchestrator issues a developer
   capability bound to run run-wd-t6i7-t0 / story WD-t6i7 (registry is
   injected via wiring; the plugin never mints —
   adapters/plugin/__init__.py:9-11).
5. Establish the critic tunnel (step 3 of GAPS) and SSH probe:
   `ssh 3090 nvidia-smi` — confirm free VRAM.
6. Configure the critic LM (GAP 1) in-session before any render:
   dspy LM ollama_chat/q38u-v2, api_base http://localhost:11434.
7. Claim the story THROUGH THE PLUGIN: paivot_story tool,
   operation=story_claim, role=developer, story_id=WD-t6i7.
   Free the GPU (GAPS 2), then run the smoke render via the
   WanGPAdapter: ONE RenderBrief, ProfileDecision(model="h3",
   shot_length_frames=96 (floor exactly), wangp_profile="profile3"),
   adapter defaults point at /home/straughter/Wan2GP/venv/bin/python +
   wgp.py on the 3090 (ssh-executed; the adapter's runner runs where
   the pipeline host runs — for the dogfood the render is invoked from
   the 3090 side or via an ssh runner the session provides).
   Keeper paths (render-NNNN/attempt-N/*.mp4) land under the
   adapter output_dir; commit them as story evidence.
8. QC: reload the critic (GAPS 2), run RenderQC.run(brief, decision,
   video=<readback path>) — the story-5 seam requires the file on disk.
   Then deliver: story_deliver via plugin; acceptance (story_accept)
   requires a SECOND executor wired as role=pm_acceptor with the same
   project_root but its own run/session ids (pre_verify gate will run
   the wangp-dspy suite — set verify_command to the repo's test
   runner script if the operator wants the gate live).
9. At least ONE insight_append during the story (mandate): e.g.
   kind=pitfall, title about GPU contention / critic wiring learned in
   this story, body <=4KB. Plugin: paivot_story,
   operation=insight_append, insight_kind/title/body args.
10. Evidence: paivot_audit via plugin — the chain must show claim,
    deliver, (accept), insight_append for run-wd-t6i7-t0 against
    project wangp-dspy.

Hard rules for the session: no direct `pvg`/`nd` from the terminal
after session start — everything through plugin tools; no vlt writes;
all renders capped 4s/96f minimum (floor), no longer than needed.
