#!/usr/bin/env python3
"""Resolve marathon configuration as tab-separated shell values."""

from __future__ import annotations

import os
import sys

from wangp.config import (
    HostConfigError,
    load_host_config,
    require_host_config,
    require_wgp_python,
)


def main() -> int:
    try:
        config = require_host_config(
            load_host_config(environ=dict(os.environ))
        )
        python = require_wgp_python(config)
    except HostConfigError as exc:
        print(f"configuration error: {exc}", file=sys.stderr)
        return 2

    assert config.target is not None
    assert config.wgp_root is not None
    values = (config.target.value, config.wgp_root.value, python.value)
    print("\t".join(values))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
