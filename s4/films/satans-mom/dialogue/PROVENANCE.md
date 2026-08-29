Provenance (authored-honest) for dialogue/timeline.json:

Line texts and speaker labels authored by the orchestrator (sol-max, WD-h25b).
Segment start/end MEASURED from edge-tts output durations via ffprobe
(no whisper/pyannote anywhere in repo paths).
audio_sha256 = hash of the concatenated full-film dialogue track once assembled.
The provenance note rides OUTSIDE timeline.json because schema_v1 rejects
unknown top-level keys (R0 forward-compat discipline, WD-j9nx).
