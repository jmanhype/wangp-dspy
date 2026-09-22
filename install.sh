#!/bin/sh
set -eu

DEFAULT_SOURCE=https://github.com/jmanhype/wangp-dspy.git
SOURCE=$DEFAULT_SOURCE
DRY_RUN=false

usage() {
    cat <<'EOF'
Usage: install.sh [--dry-run] [--source <path-or-url>]

Installs Wangp as a uv user tool and runs `wgp doctor`.
Default source: https://github.com/jmanhype/wangp-dspy.git
No root or sudo is required.

Options:
  --dry-run             Print the exact commands without changing the machine.
  --source <path-or-url>
                        Install from an explicit checkout path or Git URL.

One-command install:
  curl -LsSf https://raw.githubusercontent.com/jmanhype/wangp-dspy/main/install.sh | sh

Wangp first verifies uv, then runs:
  uv tool install --upgrade --from <source> wangp-dspy
  <user-tool-bin>/wgp doctor
EOF
}

fail_missing_uv() {
    printf '%s\n' \
        'MISSING_PREREQUISITE: uv is required to install Wangp.' \
        'Install uv first with:' \
        '  curl -LsSf https://astral.sh/uv/install.sh | sh' >&2
    exit 127
}

while [ "$#" -gt 0 ]; do
    case $1 in
        --help)
            usage
            exit 0
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --source)
            [ "$#" -ge 2 ] || { usage >&2; exit 2; }
            SOURCE=$2
            shift 2
            ;;
        --source=*)
            SOURCE=${1#--source=}
            shift
            ;;
        *)
            printf '%s\n' "Unknown argument: $1" >&2
            usage >&2
            exit 2
            ;;
    esac
done

command -v uv >/dev/null 2>&1 || fail_missing_uv
WGP_BIN=${UV_TOOL_BIN_DIR:-$HOME/.local/bin}

if [ "$DRY_RUN" = true ]; then
    printf '%s\n' 'Dry run: no changes will be made.'
    printf '%s\n' "uv tool install --upgrade --from $SOURCE wangp-dspy"
    printf '%s\n' "$WGP_BIN/wgp doctor"
    exit 0
fi

uv tool install --upgrade --from "$SOURCE" wangp-dspy
"$WGP_BIN/wgp" doctor
