# Content Brief Gateway

The Content Brief Gateway is the operator-facing, no-GPU entry to Wangp film
planning. It validates a typed JSON brief, resolves cast plates and optional
turn audio, invokes the existing `run_film(..., dry_run=True)` planner, and
writes a canonical plan with repository provenance.

## Input

```json
{
  "schema_version": "wangp-dspy.content-brief/v1",
  "title": "Harbor Signal",
  "premise": "Two keepers discover an automated lighthouse has begun hiding ships.",
  "characters": [
    {
      "name": "Tess",
      "sn_tag": "S1",
      "description": "a calm project architect with salt-gray hair"
    },
    {
      "name": "Rho",
      "sn_tag": "S2",
      "description": "a rugged horizon scout with weathered hands"
    }
  ],
  "dialogue": [
    {"speaker": "Tess", "text": "Tomorrow's sunrise is only a project."},
    {"speaker": "Rho", "text": "Give me a real horizon."}
  ],
  "durations_s": [2.3333333333333335, 2.3333333333333335]
}
```

`durations_s` may be omitted; every turn then receives the deterministic
56-frame / 24 fps duration. `audio_paths` may also be omitted. When omitted,
the existing dry planner materializes deterministic silence guides. When
supplied, the list must contain one existing WAV file per dialogue turn.
Relative paths resolve against the brief file.

The plates directory must contain exactly one `anchor.*` file and exactly one
`<CharacterName>.*` file per character.

## CLI

```bash
uv run --frozen --extra dev python scripts/run_content_brief.py \
  --brief brief.json \
  --plates plates/ \
  --output plans/harbor-signal.json
```

Use `--run-dir PATH` to choose where the equivalent script, run ledger, and
generated silence guides are written. The default run directory is the output
file's sibling `run/` directory.

The command performs no model inference, SSH, queue submission, host call, or
GPU work. It always calls the existing run planner in dry-run mode.

## Output

The canonical output records:

- content-brief hash,
- repository root, commit, and dirty-tree identity,
- resolved brief, plates, audio, and script paths,
- cast roster,
- dialogue,
- emitted clips,
- planned duration,
- explicit `gpu_work: false` and `queue_submitted: false` flags.

Invalid schema, unknown fields, duplicate cast tags, unknown speakers, missing
plates, bad durations, or missing audio fail before output media guides are
created.
