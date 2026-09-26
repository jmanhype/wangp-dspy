# 86 — Wan2GP saves media after optional mutagen metadata failures

Status: root cause classified and locally owned. No SSH, GPU, inference,
download, accepted media artifact, accepted log, or host environment was
changed.
Story: WD-f0vk
Date: 2026-09-26

## Symptom

Accepted WD-9t9o and WD-isg9 runs record `No module named 'mutagen'` while
attempting MP4 metadata and cover-art operations. Every affected task exits
zero after saving its media bytes and completing its queue.

## Evidence and source site

The active process is `/home/straughter/Wan2GP/venv/bin/python` running
`wgp.py --process` on host `straughter-Z690-Steel-Legend`; preserved stack
frames identify the monolithic media dispatcher as
`/home/straughter/Wan2GP/wgp.py::generate_media` (`wgp.py:7583` and
`wgp.py:7870` in accepted same-source boundary logs). The edit and repaint
errors occur immediately before `Video file saved to Path`; the upscale errors
occur immediately after `Postprocessed video saved to Path`. The exact
mutagen statement line is not present in preserved logs, so this finding does
not invent one.

The interpreter is Python 3.11 and reports `mutagen` absent. The user-level
Python 3.12 inventory from accepted WD-m0r5 evidence independently records
`mutagen 1.47.0` under `~/.local`; that installation is not the active Wan2GP
venv and must not be used as permission for an undocumented host install.

## Classification

`mutagen` is required for the embedded metadata and cover-art operations to
succeed, but optional to saved media-byte generation in the observed control
flow: Wan2GP catches the import failure, logs it, and continues. Wangp does not
declare the package. Accepted evidence does not preserve Wan2GP's dependency
manifest, so this finding does not claim whether upstream omitted it or the
host environment drifted. A durable upstream correction would declare/disable
the feature through its own environment contract; Wangp cannot repair that
external venv by an ad hoc install.

## Wangp-owned correction

The canonical Maestro-parity verifier now reads referenced native logs and
computes their exact SHA-256. It emits
`WAN2GP_OPTIONAL_MUTAGEN_MISSING` for only the exact successful-save metadata
and cover-art signatures. It fails closed on a missing/non-regular log, hash
mismatch, a mutagen warning without a save marker, or an unrelated Python
import error. Thus a pass explicitly reports the warning instead of normalizing
it as ordinary success output.

Machine-readable diagnosis and all six relevant log hashes are retained in
`datasets/diagnostics/wan2gp-mutagen/WD-f0vk.json`.
