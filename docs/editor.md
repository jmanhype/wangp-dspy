# Non-destructive editor surface

`wgp editor` is the headless equivalent of the editing surface required by WD-gc09. It is deliberately not a GUI and performs no model inference, download, SSH, GPU, renderer admission, QC, or media generation. The CLI exercises the same typed project service that a later UI must use.

## Track and project model

A project uses `wangp-dspy.editor-project/v1`. It contains immutable `SourceAsset` records (`video`, `audio`, `image`, or `text` path plus SHA-256 and byte size), ordered `Track` records of those same kinds, `Clip` decisions with timeline and source in/out points, `Transition` decisions, and `ReviewMark` decisions. Media clips reference a pinned source ID. Text clips carry inline text. Track clip order and overlap are type-checked. Projects also name the reviewer used by the downstream manual review checkpoint.

`services.editor.project_store.ProjectStore` copies an imported source into the portable project workspace as `sources/<asset-id><suffix>`, records the hash, and thereafter only reads it. The JSON document is written atomically. Its history contains every project snapshot and a cursor, so undo and redo select prior decisions without changing source bytes. Load rejects malformed JSON, unsupported schemas, bad history cursors, missing sources, and hash/size mismatches with typed `EDITOR_*` diagnostics and exit code 2.

## Export semantics

`wgp editor export` verifies every pinned source, requires at least two ordered video clips, and emits canonical `wangp-dspy.editor-export/v1` JSON. The export actually invokes `services.director.plan_compiler.compile_director_request` with a `DirectorRequest` from `services.director.composition`; the accepted director lane in turn invokes the existing content planner. It also invokes `predict.assembler.MultiShotAssembler.assemble` on typed `ShotPlan` values derived from clip labels and source hashes. The output records both consumption paths, the director plan, the assembler continuity digest, and the complete source manifest. Repeated export and export after project round-trip are byte-identical because no timestamp, absolute output path, queue ID, or host state is embedded in the export file.

An optional `--queue-db` submits one pending `kind=editor_export` record through the real `services.jobs.queue.JobQueue.submit`. The existing queue computes its render fingerprint and owns admission and retry semantics unchanged. The queue ID is command output, not part of the deterministic export file. This local durable queue record is not host work and proves no media.

## Review and authorization boundary

The project model preserves explicit review marks, but those are editor decisions only. Director export carries a manual review checkpoint and names all existing mandatory gates without bypassing any. A later authorized host run must produce its own command, repository/model/source provenance, queue attempts, output hashes, QC evidence, review evidence, and recipe linkage. The WD-gc09 authorized-host export bundle is therefore **not verified - requires authorized host run**.

## Commands

```text
wgp editor validate --project project.wgp-editor.json --json
wgp editor export --project project.wgp-editor.json --out export.json --queue-db queue/jobs.db --json
```

Both commands run headlessly and use stable typed diagnostics with safe next commands. Missing, mutated, malformed, and schema-incompatible projects fail closed with exit code 2.

## Explicitly deferred UI

No graphical or browser UI is implemented in this no-GPU slice. The decision is deliberate: this lane has no GPU or display, CI must exercise project correctness without a browser, and the CLI already drives the same validation, history, source verification, director, assembler, and queue services. A future UI may only wrap this service; it must not create a second persistence or governance path.
