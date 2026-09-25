# Maestro image capability planning

`wgp image` is a deterministic, typed, no-GPU planning surface. It follows the governed video seam: immutable typed input, operator-supplied model provenance, fail-closed backend adapters, normalized backend settings, and a separate SQLite plan table. A successful plan proves request shape and durable planning only; it never proves that an image exists.

## Request schema

Requests use `wangp-dspy.image-capability-request/v1`. Operations are `generate`, `edit`, `upscale`, `outpaint`, and `identity_edit`.

```json
{
  "schema_version": "wangp-dspy.image-capability-request/v1",
  "model": {"family": "qwen_image", "preset": "qwen-professional"},
  "operation": "identity_edit",
  "prompt": "preserve this person while changing the jacket color",
  "license": "operator-recorded output license",
  "references": [
    {"path": "person.png", "sha256": "64-hex", "role": "identity", "license": "input license"},
    {"path": "scene.png", "sha256": "64-hex", "role": "subject", "license": "input license"}
  ],
  "mask": {"path": "edit-mask.png", "sha256": "64-hex"},
  "edit_region": {"x": 32, "y": 32, "width": 256, "height": 256, "source_width": 512, "source_height": 512},
  "prompt_enhancement": {"mode": "operator_authorized", "provider": "declared-provider", "authorization_ref": "run-record"},
  "output": {"format": "png", "transparency": true, "width": 1024, "height": 1024},
  "identity_gate": {"metric": "face_embedding_cosine", "threshold": 0.75},
  "recipe_seed": 904
}
```

The separately supplied manifest must contain matching backend/preset `sha256`, license, explicit `license_accepted`, and VRAM profile. Wangp never downloads a model or calls a provider during planning.

Reference rules are immutable and order-sensitive:

- At most ten image references are accepted; an eleventh is rejected before a durable record is created.
- Every reference must be locally readable and byte-for-byte hash-matched, with a role (`subject`, `style`, `identity`, or `composition`) and recorded license.
- `edit`, `outpaint`, and `identity_edit` require at least one reference and a PNG edit mask whose bytes match its hash.
- `upscale` requires exactly one reference, source dimensions, and factor 2 or 4; output dimensions must equal source dimensions multiplied by that factor.
- `outpaint` requires source dimensions and output dimensions larger than the source on both axes.
- `identity_edit` requires at least one `identity` reference and an objective identity gate (`face_embedding_cosine` plus threshold). The gate is only declared here; identity preservation is not claimed without an authorized run bundle and recorded metric evidence.

Prompt enhancement is immutable metadata, not quiet rewriting. `mode=off` must omit provider and authorization fields. `mode=operator_authorized` requires both a provider and an authorization reference; no provider is contacted by this surface. Transparency requires PNG and is recorded as `alpha_mode=8_bit_alpha`; a plan declares that requested output contract but does not claim that pixels or alpha were produced.

## Commands

```text
wgp image plan --request generate.json --models models.json --dry-run --json
wgp image edit --request edit.json --models models.json --db run/image-plan.db --json
wgp image upscale --request upscale.json --models models.json --dry-run
wgp image outpaint --request outpaint.json --models models.json --dry-run
wgp image plan --db run/image-plan.db --reconstruct --json
```

`wgp image edit` accepts `edit` and `identity_edit`; the other verbs enforce their matching operation. Durable writes go only to `image_plan_records`, not the executable `jobs` table. Every record carries immutable backend identity/hash/license/VRAM metadata, ordered reference hashes and licenses, reference limit/count, mask hash, edit/upscale/outpaint controls, output and alpha declaration, enhancement metadata, identity gate declaration, recipe seed, normalized settings, and hashes of the recipe and settings. `queue_submitted=false`, `plan_only=true`, and `executable=false` mean no renderer admission or host submission occurred.

Reconstruction independently validates the frozen recipe, regenerates settings from its seed, and compares canonical SHA-256 values. Absent, empty, or damaged databases fail closed with typed exit 2 diagnostics.

## Capability matrix

| Family/preset | Generate | Edit | Upscale | Outpaint | Identity edit |
| --- | --- | --- | --- | --- | --- |
| qwen_image/qwen-standard | host_run_verified ([WD-m0r5 evidence](../datasets/runs/maestro-parity/WD-m0r5/evidence.json)) | host_run_verified ([WD-m0r5 evidence](../datasets/runs/maestro-parity/WD-m0r5/evidence.json)) | host_run_verified ([WD-m0r5 evidence](../datasets/runs/maestro-parity/WD-m0r5/evidence.json)) | host_run_verified ([WD-m0r5 evidence](../datasets/runs/maestro-parity/WD-m0r5/evidence.json)) | host_run_verified ([WD-m0r5 evidence](../datasets/runs/maestro-parity/WD-m0r5/evidence.json)) |
| qwen_image/qwen-professional | host_run_verified ([WD-m0r5 evidence](../datasets/runs/maestro-parity/WD-m0r5/evidence.json)) | host_run_verified ([WD-m0r5 evidence](../datasets/runs/maestro-parity/WD-m0r5/evidence.json)) | host_run_verified ([WD-m0r5 evidence](../datasets/runs/maestro-parity/WD-m0r5/evidence.json)) | host_run_verified ([WD-m0r5 evidence](../datasets/runs/maestro-parity/WD-m0r5/evidence.json)) | host_run_verified ([WD-m0r5 evidence](../datasets/runs/maestro-parity/WD-m0r5/evidence.json)) |
| flux_kontext/flux-standard | host_run_verified ([WD-m0r5 evidence](../datasets/runs/maestro-parity/WD-m0r5/evidence.json)) | host_run_verified ([WD-m0r5 evidence](../datasets/runs/maestro-parity/WD-m0r5/evidence.json)) | unsupported | unsupported | host_run_verified ([WD-m0r5 evidence](../datasets/runs/maestro-parity/WD-m0r5/evidence.json)) |
| flux_kontext/flux-kontext | host_run_verified ([WD-m0r5 evidence](../datasets/runs/maestro-parity/WD-m0r5/evidence.json)) | host_run_verified ([WD-m0r5 evidence](../datasets/runs/maestro-parity/WD-m0r5/evidence.json)) | unsupported | unsupported | host_run_verified ([WD-m0r5 evidence](../datasets/runs/maestro-parity/WD-m0r5/evidence.json)) |

The supported Qwen and Flux cells above are `host_run_verified` from the independently approved [WD-m0r5 evidence bundle](../datasets/runs/maestro-parity/WD-m0r5/evidence.json); the Flux upscale and outpaint boundaries remain `unsupported`. A row can become `host_run_verified` only from a separately authorized bundle recording operator authorization, command, repository commit, model/reference provenance, queue attempt, output hash, image metadata/dimensions/alpha mode, objective identity-gate result where applicable, and reviewer verdict. The verified bundle records the authorized GPU/download work; it does not claim a GUI, registry publication, training run, or protected engine change.
