# REPRODUCTION VERDICT — v3_pair bit-for-bit (2026-09-12)

The recovered generator (datasets/runs/provenance/v3_pair_generator.py) was
rerun verbatim on the same host, same wavs, same refs, same seed, same WanGP
commit. Result: ALL THREE ARTIFACTS BYTE-IDENTICAL.

| artifact | md5 (rerun = original) |
|---|---|
| v3_c1.mp4 | be96a3027d1fa8f4b14454118ab4d97a |
| v3_c2.mp4 | 6b485e84f875ccc30a87476b34bf38d3 |
| v3_pair.mp4 | c523919b6ac93a29edd43de75e424033 |

QC scores reproduced exactly: wav gates 0.86/0.80; post-render whisper
0.71 ("who hushed now, dear? have a cookie") / 0.60 ("matey, i am on
fight!") — identical transcripts including identical whisper-small quirks.

## Implications

1. The "perfect" run (operator verdict, ledger #4) is DETERMINISTIC and
   REPRODUCIBLE from the committed script. Provenance is total: the film
   can be rebuilt from repo state alone.
2. The recipe is pinned: seed 904 + profile 2 + 2 refs + isolated trimmed/
   boosted wavs + (S1)/(S2) prose + last-frame chain == same bytes.
3. Gold-standard control established: any A/B variation (official
   six-section prompt, 50-step sampling, phoneme QC) that produces
   different output is attributable to that change alone.
4. One caveat carried from the original: the script's `wav_raw` path
   needed the same one-line extension fix as on its original day —
   preserved in the provenance copy's note.

Originals additionally archived at 3090:/mnt/bulk/straughter/perfect-artifacts/
and ~/Downloads/SGFLIX_Marathon/v3_pair_PERFECT_original.mp4.
