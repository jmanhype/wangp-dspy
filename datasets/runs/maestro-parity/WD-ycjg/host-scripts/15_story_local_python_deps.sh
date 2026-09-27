#!/bin/bash
set -euo pipefail

RUN=/home/straughter/wd-ycjg-run
SRC=$RUN/python-deps/src
MANIFEST=/tmp/wd-ycjg-python-deps.tsv
mkdir -p "$SRC" "$RUN/python-deps/packages"

while IFS=$'\t' read -r url destination expected_size expected_sha; do
  test -n "$url"
  if ! test -f "$destination"; then
    curl --fail --location --retry 5 --retry-delay 3 --output "$destination.wd-ycjg.part" "$url"
    test "$(stat -c %s "$destination.wd-ycjg.part")" = "$expected_size"
    test "$(sha256sum "$destination.wd-ycjg.part" | awk '{print $1}')" = "$expected_sha"
    mv "$destination.wd-ycjg.part" "$destination"
  else
    test "$(stat -c %s "$destination")" = "$expected_size"
    test "$(sha256sum "$destination" | awk '{print $1}')" = "$expected_sha"
  fi
done < <(tail -n +2 "$MANIFEST")

tar -xzf "$SRC/iopath-0.1.10.tar.gz" -C "$RUN/python-deps/packages"
cp -a "$RUN/python-deps/packages/iopath-0.1.10/iopath" "$RUN/python-deps/packages/iopath"
unzip -q -o "$SRC/portalocker-4.4.0-py3-none-any.whl" -d "$RUN/python-deps/packages"
unzip -q -o "$SRC/pycocotools-2.0.11-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl" -d "$RUN/python-deps/packages"
test -f "$RUN/python-deps/packages/iopath/common/file_io.py"
test -f "$RUN/python-deps/packages/portalocker/__init__.py"
test -f "$RUN/python-deps/packages/pycocotools/mask.py"
printf 'planned_bytes=664045\nactual_bytes=664045\nasset_count=3\nlive_dependency_mutation=0\n' >"$RUN/host-logs/15-story-local-download-accounting.txt"
PYTHONPATH="$RUN/python-deps/packages:/home/straughter/Wan2GP-story-WD-ycjg" \
  /home/straughter/Wan2GP/venv/bin/python -c 'from iopath.common.file_io import g_pathmgr; import portalocker; import pycocotools.mask; print("STORY_LOCAL_PYTHON_DEPS_PASS")' \
  >"$RUN/host-logs/15-story-local-python-deps.txt"
cat "$RUN/host-logs/15-story-local-python-deps.txt"
