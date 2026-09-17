# 76 — Preserve rejected VibeVoice audio and Whisper evidence

Status: implemented locally; model-free validation only.

## Failure boundary

The coordinator reported a live Nell pass (0.857) followed by an Orin
pre-gate rejection (0.000). Previously the gate raised without retaining its
structured transcript evidence, and remote supply stopped at the nonzero
exit code without retrieving the failed report or listening artifacts.
These live scores are coordinator-provided context, not reproduced here.

## Change

`WhisperGateError.evidence` retains the actual scored transcript, score,
pass bar and `passed=False` for scored rejections. Transcription/validation
errors still raise without fabricated transcript or score. Local VibeVoice
failure reports include scored evidence and prepared-file provenance.

After a nonzero host result and successful GPU lease restoration, remote
supply retrieves and validates the failed report. A valid rejection consists
of a complete prefix, one scored pre-gate rejection, and pending remaining
turns. The existing identity, preparation, transcript recomputation and SHA-256
checks apply to both passed and rejected generated artifacts. Missing or
inconsistent evidence aborts without retaining a validated bundle.

Validated artifacts are installed together under
`<report-parent>/rejected/<unique-remote-run-name>/`, never the canonical
output/report paths. This includes raw/prepared WAVs, localized provenance,
unaltered remote provenance, the original failed remote report and a localized
`status=failed` audit report. The call still raises. Existing publication
rejects that failed audit report, including its passing prefix.

This does not regenerate audio or retroactively recover the earlier live run.
Generation failures, unscored transcription failures, transport exceptions,
and GPU lease failures remain closed errors without a validated listening
bundle. No transcript score, gate threshold or success criterion is weakened.

## Verification

Model-free tests cover structured scored rejection, no invented transport
evidence, retrieval on failed host execution, failed-report publication denial,
pending later turns, missing report/raw/prepared files, and tampered
raw/prepared/provenance/gate evidence. No host/GPU call, commit or push was made.

`.venv/bin/python -m pytest tests/test_whisper_gate.py tests/test_vibevoice.py
tests/test_render_host.py -q` exited 0 (68 passing cases). `git diff --check`
exited 0.
