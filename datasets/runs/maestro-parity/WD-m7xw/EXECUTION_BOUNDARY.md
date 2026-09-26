# WD-m7xw fail-closed execution boundary

WD-m7xw stopped after successful asset, fixed-source, and tokenizer preflight and
before queue admission. The unrelated service below was already occupying the
authorized RTX 3090:

```text
PID 3213164
/home/straughter/llama.cpp/build/bin/llama-server
GPU memory: 18154 MiB
Free memory: 5873 MiB
```

The dispatcher authorization says to stop on GPU failure and explicitly forbids
killing or restarting unrelated services. Therefore no operation-specific
inference command was safe or authorized. This is an `authorized_host_state`
preflight boundary, not `unsupported_on_this_hardware`, not a model capability
verdict, and not a terminal operation disposition.

| Operation | Attempted | Queue admission | Output bytes | Boundary |
| --- | ---: | --- | ---: | --- |
| create | no | blocked | 0 | unrelated GPU occupancy |
| extend | no | blocked | 0 | unrelated GPU occupancy |
| retake | no | blocked | 0 | unrelated GPU occupancy |
| edit | no | blocked | 0 | unrelated GPU occupancy |
| outpaint | no | blocked | 0 | unrelated GPU occupancy |
| repaint | no | blocked | 0 | unrelated GPU occupancy |
| recast | no | blocked | 0 | unrelated GPU occupancy |
| upscale | no | blocked | 0 | unrelated GPU occupancy |

The preflight did prove the prerequisites needed to resume safely:

1. All fifteen required LTX-2.5 files matched their recorded SHA-256 values.
2. Wan2GP was deployed in an isolated worktree at the required
   `story/WD-i7qs` commit.
3. The real Gemma tokenizer loaded with vocabulary `262144` and mapped
   `<|video|>` to id `258884`.
4. The live Wan2GP dirty tree identity remained unchanged.
5. No model or dependency download occurred.

Resume requires the unrelated GPU service to terminate or receive separate
operator authorization to stop; it must not be killed by this story.

## Resolution after resumed authorization

On the resumed run, PID `3213164` was already absent and no compute process held
the GPU, so WD-m7xw killed no process. After the fifteen hashes and tokenizer
check passed again, all eight native operations were attempted serially:

| Operation | Native exit | Terminal result |
| --- | ---: | --- |
| create | 0 | hashed MP4 |
| extend | 0 | hashed, longer MP4 |
| retake | 0 | hashed, first-frame-anchored MP4 |
| edit | 0 | hashed video-to-video MP4 |
| outpaint | 1 | required LoRA absent; zero output bytes |
| repaint | 1 | required LoRA absent; zero output bytes |
| recast | 1 | required LoRA absent; zero output bytes |
| upscale | 1 | required LoRA absent; zero output bytes |

The resumed evidence is in `host-logs-resumed/`, `outputs/`, and
`dependency-boundaries.md`. The four exit-1 operations are dependency boundaries,
not hardware verdicts. The final isolated tree is the required commit with only
the expected `ckpts` symlink; the live tree identity is unchanged.
