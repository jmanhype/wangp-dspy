# Wangp failure diagnostics

Wangp diagnostics are read-only. They never retry a job, mutate a queue or host,
download a model, delete an artifact, or change a gate decision. Every diagnostic
has the same JSON shape:

```json
{
  "code": "STABLE_FAILURE_CODE",
  "severity": "error",
  "title": "what happened",
  "observed": "the measured fact",
  "why": "one-line cause",
  "remediation": "the safe action",
  "next_command": "exact command or null",
  "evidence_refs": ["paths or durable check references"],
  "metadata": {"failure-specific scores, hashes, counts, and paths": true}
}
```

Human output uses the same vocabulary: `diagnostic code=…`, `observed`, `why`,
`remediation`, `next`, `evidence`, and `details`. Credential-shaped values are
redacted; paths, states, hashes, gate scores, and counts are retained.

## Failure catalog

### `HOST_UNREACHABLE`, `HOST_KEY_REJECTED`, `HOST_AUTHENTICATION_FAILED`

An explicit `wgp doctor --probe-host --models MANIFEST` classified the SSH result.
Unreachable, host-key, and authentication failures are separate codes. The
diagnostic names the resolved target (when configuration resolved one), retains
the probe result, and gives the next non-mutating command. A host-key problem
starts with `ssh-keygen -F TARGET`; never disable host-key checking.

For `HOST_CONFIGURATION_INCOMPLETE`, set every named key (`host.target`,
`host.wgp_root`, and `host.pull_root`) through the named environment variable,
user file, or repository file, then run `wgp doctor`. Partial configuration is
deliberately rejected.

### `MODEL_MISSING` and `MODEL_HASH_MISMATCH`

The diagnostic preserves the exact local or remote model path and the
manifest-recorded SHA-256 prefix. A missing file and a file with different bytes
are distinct. Restore the declared bytes or place the file at its recorded path;
Wangp does not download, overwrite, or relax the digest. Inspect with:

```bash
uv run --frozen --extra dev wgp doctor --models models.json
```

### `DISK_HEADROOM_BELOW_THRESHOLD`

The remote render volume must retain at least **50 GB**. The diagnostic records
the measured available GiB, minimum GiB, and mount path, and suggests only a
read-only `df` command. Free or select sanctioned storage manually after
preserving evidence; diagnostics never delete an artifact.

### `GATE_REJECTED`

The queue diagnostic reads the preserved `qc-evidence.json` and reports:

- Whisper pre/post `score`, `pass_bar`, transcript, and failed phase;
- identity/action vision `speaker_attribution`, `action_match`, `mouth_activity`,
  `pass_bar`, and three-frame mouth boxes/spread;
- mouth-box localization when three valid boxes are absent;
- SyncNet `confidence`, `offset_frames_25fps`, `offset_seconds`, model hash, and
  passed state.

It includes the exact recorded failure reason and the preserved evidence path.
Inspect it with `wgp review --db DB --job ID`. Fix the effective input or gate
implementation. Do not change a threshold, invent a score, or bypass a gate. An
eligible failed job may use the existing retry command shown by the diagnostic.

### `RETRY_EXHAUSTED`

A dead-letter row is terminal. The diagnostic names the job id, failure count,
immutable attempt-row count, failure class/detail, retryability, and retained
database/evidence paths. It explicitly states that no automatic retry occurs.
After reviewing the evidence and fixing the cause, reopen only with an audited
reason:

```bash
.venv/bin/python scripts/run_jobs.py --db jobs.db \
  --retry-dead-letter --reason "documented operator reason"
```

### `DETERMINISTIC_REPLAY_BLOCKED`

The queue detected the same failure signature on a retried attempt. Change an
effective input such as seed, prompt, references, or audio guide. Explicit
`allow_deterministic_replay` requires operator authorization; never set it merely
to create a retry loop.

### `RETRY_ELIGIBLE`

The job is failed but below the terminal policy and has not repeated its
signature. Inspect the attempt first; the diagnostic shows the existing
`scripts/run_jobs.py --retry-failed` command. Diagnostics do not execute it.

### `PROVENANCE_ARTIFACT_MISSING` and `PROVENANCE_HASH_MISMATCH`

`wgp review RUN` found a recorded path that is absent or whose SHA-256 differs
from `final-provenance.json`. Restore the durable artifact or create a new
provenance identity; do not edit the recorded hash. These use the same diagnostic
vocabulary as infrastructure and gate failures.

### `INPUT_INVALID` and `UNKNOWN_FAILURE`

Typed brief/configuration failures identify the field or path and the command to
rerun after correction. An unrecognized queue class remains `UNKNOWN_FAILURE`
with its original class/detail and evidence; file that class rather than
relabelling it as understood.

## Safety and exit codes

`doctor`, `status`, and `review` expose diagnostics in both human and `--json`
modes. Expected input/configuration/evidence failures exit `2`; a failed doctor
check exits `3`; an unexpected internal error remains `4` with a concise
containment message rather than a traceback. Queue reads use the immutable SQLite
read-only adapter and never advance state or retry eligibility.
