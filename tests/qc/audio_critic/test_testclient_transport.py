from __future__ import annotations

import subprocess
import sys


def test_fastapi_testclient_import_fails_on_legacy_httpx_warning() -> None:
    """Keep the real TestClient import on its non-deprecated transport."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import warnings; from starlette.exceptions import StarletteDeprecationWarning; warnings.simplefilter('error', StarletteDeprecationWarning); import fastapi.testclient",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, (result.stdout, result.stderr)
