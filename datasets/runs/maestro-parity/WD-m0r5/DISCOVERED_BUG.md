# DISCOVERED_BUG

`services/jobs/preflight.py:54` is:

```python
_GPU_PROC_RE = re.compile(r"^\s*(\d+)\s+\S+", re.M)
```

It requires whitespace after the PID. `nvidia-smi --query-compute-apps=pid,process_name --format=csv,noheader` emits a comma:

```text
1007225, /home/straughter/llama.cpp/build/bin/llama-server
```

Observed result: the GPU held 7,808 MiB, but `wgp doctor --probe-host --models ...` reported `gpu_state=idle`. A direct query with `used_memory` showed the holder and 7,896 MiB total GPU use.

Reproduction:

```text
ssh 3090 nvidia-smi --query-compute-apps=pid,process_name --format=csv,noheader
```

The protected-file story is WD-e4r7. WD-m0r5 does not modify `services/jobs/preflight.py`.
