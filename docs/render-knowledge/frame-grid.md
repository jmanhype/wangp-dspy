# Frame Grid Unlock — `verified`

H3 valid clip lengths are **17k+5 frames**: 5 / 22 / 39 / 56 / 73 / 90 /
107 / … (k=0,1,2,3,…).

- The 107 floor in WanGP `minimax_h3_handler.py` (`frames_minimum`) is a
  **wrapper default, not an architecture limit**. The upstream pipeline
  already accepts k=0 (5 frames).
- Patching `frames_minimum` 107 → 56 unlocks **k=3 (56 frames ≈ 2.33s
  native at 24fps)**.

## Evidence

- RENDER-LOGS-0830: our live controlled renders 2026-08-30/31 at 56
  frames succeeded after the patch; pre-patch attempts at non-grid
  lengths were rejected/quantized.
- COMFYUI-H3: MiniMaxH3AddGuide documents valid clip lengths
  5/22/39/… (same 17k+5 grid).
- Code: `models/minimax_h3/minimax_h3_handler.py` in Wan2GP
  (`frames_minimum`).

## Consequences

- 2.33s native shots (56f) are the shortest practical narrative unit.
- Any frame count not on the grid gets snapped; set frames explicitly
  or patch the wrapper floor.
