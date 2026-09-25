#!/usr/bin/env python3
"""Run the existing remote preflight with the lane-derived disk floor."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from services.jobs.preflight import run_preflight
from wangp.config import load_host_config, render_host
from wangp.doctor import remote_model_specs


def main() -> int:
    root = Path(__file__).resolve().parents[4]
    models = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    min_free_gb = float(sys.argv[2])
    environment = os.environ.copy()
    config = load_host_config(repository_root=root, environ=environment)
    host = render_host(config)
    report = run_preflight(
        host,
        models=remote_model_specs(models, wgp_root=config.wgp_root.value),
        min_free_gb=min_free_gb,
        disk_path=config.wgp_root.value,
        qc_url=environment.get("WANGP_QC_URL", "http://localhost:8000/health"),
    )
    payload = {
        "passed": report.passed,
        "checks": [check.__dict__ for check in report.checks],
        "detail": report.detail,
        "min_free_gb": min_free_gb,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
