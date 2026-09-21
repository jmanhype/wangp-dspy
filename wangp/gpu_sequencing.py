"""Resolve GPU sequencing inputs from the shared host configuration."""

from __future__ import annotations

import os
from typing import Mapping

from wangp.config import load_host_config, require_host_config


def gpu_sequence_environment(
    environ: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Return an environment carrying the resolved SSH target to helpers."""

    environment = os.environ if environ is None else environ
    config = require_host_config(load_host_config(environ=environment))
    assert config.target is not None
    return {
        **environment,
        "WANGP_SSH_TARGET": config.target.value,
    }
