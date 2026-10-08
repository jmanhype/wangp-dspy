# WD-bw0h clean-machine retry3 — 2026-10-08

## Outcome

The one-shot retry3 authorization was consumed and stopped fail-closed. It did **not** produce a generated artifact.

- Clean install, checkout, remote-root, storage, four-model identity, offline-wrapper, and queue preflight paths succeeded.
- Exactly one local queue job was admitted and attempted.
- The renderer launched in the default remote acceptance namespace and exited after WanGP reported:

```text
File not found: /home/straughter/Wan2GP/acceptance/worker-ba467cae944b/render-0000/settings.json
```

- The exact settings bytes existed only in the local pull mirror at:

```text
pull-mirror/acceptance/worker-ba467cae944b/render-0000/settings.json
```

- The preserved remote probe confirms the mapped remote `settings.json` was absent while the local mirror copy was present.
- The queue terminated `failed` with one render attempt and no output.

## Root cause and repair boundary

`production_fl2va_render()` wrote `settings.json` to the local pull mirror, mapped that local filename to a remote path, and passed the mapped path to WanGP without staging the file through the `RenderHost` transport.

The accompanying code change stages the identical serialized settings through `RenderHost.write_text()` after remote directory creation and uses the transport-returned path in the detached launch. This is a local repair and regression-test change only; it does not consume or grant another host attempt.

## No-retry boundary

The authorization canonical SHA-256 and consumed status are recorded in `authorization-consumption.json`. Replay is fail-closed. A future clean-machine attempt requires a new operator authorization bound to the repaired source bytes.
