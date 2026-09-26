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
