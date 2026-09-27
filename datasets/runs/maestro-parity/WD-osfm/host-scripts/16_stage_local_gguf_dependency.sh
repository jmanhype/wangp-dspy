#!/bin/bash
set -euo pipefail

RUN=/home/straughter/wd-osfm-run
PY=/home/straughter/Wan2GP/venv/bin/python
SOURCE_SITE=/home/straughter/.local/lib/python3.12/site-packages
SOURCE_PACKAGE=$SOURCE_SITE/gguf
SOURCE_METADATA=$SOURCE_SITE/gguf-0.17.1.dist-info
VENDOR=$RUN/vendor
LOG=$RUN/host-logs

test -d "$SOURCE_PACKAGE"
test -d "$SOURCE_METADATA"
grep -q '^Version: 0.17.1$' "$SOURCE_METADATA/METADATA"
grep -q '^Requires-Python: >=3.8$' "$SOURCE_METADATA/METADATA"
"$PY" - <<'PY'
import numpy, yaml, tqdm
print("dependency_prerequisites_ok", numpy.__version__, yaml.__version__, tqdm.__version__)
PY

mkdir -p "$VENDOR"
rm -rf "$VENDOR/gguf" "$VENDOR/gguf-0.17.1.dist-info"
cp -a "$SOURCE_PACKAGE" "$SOURCE_PACKAGE/../gguf-0.17.1.dist-info" "$VENDOR/"
find "$VENDOR" -type d -name __pycache__ -prune -exec rm -rf {} +
find "$VENDOR" -type f -name '*.pyc' -delete

source_hashes=$(
  cd "$SOURCE_SITE"
  find gguf gguf-0.17.1.dist-info -type f ! -name '*.pyc' -print0 | sort -z | xargs -0 sha256sum
)
staged_hashes=$(
  cd "$VENDOR"
  find gguf gguf-0.17.1.dist-info -type f ! -name '*.pyc' -print0 | sort -z | xargs -0 sha256sum
)
test "$source_hashes" = "$staged_hashes"

{
  printf 'source_site=%s\n' "$SOURCE_SITE"
  printf 'package=gguf\nversion=0.17.1\nnetwork_bytes=0\nlive_venv_mutation=0\n'
  printf '%s\n' "$source_hashes"
  printf -- '--- staged ---\n'
  printf '%s\n' "$staged_hashes"
} >"$LOG/05_isolated_gguf_staging.txt"
PYTHONPATH="$VENDOR" "$PY" - <<'PY'
import gguf
from gguf import GGUFReader
assert gguf.__file__.startswith("/home/straughter/wd-osfm-run/vendor/")
print("isolated_gguf_import_ok", gguf.__file__)
PY
printf 'LOCAL_GGUF_ISOLATED_DEPENDENCY_PASS\n'
