#!/bin/sh
set -eu

DEFAULT_REPOSITORY=https://github.com/jmanhype/wangp-dspy.git
DEFAULT_SOURCE=git+$DEFAULT_REPOSITORY@main
SOURCE=$DEFAULT_SOURCE
CLONE_SOURCE=$DEFAULT_REPOSITORY
CHECKOUT=
DRY_RUN=false

usage() {
    cat <<'EOF'
Usage: install.sh [--dry-run] [--source <path-or-url>] [--checkout <dir>]

Installs Wangp as a uv user tool and runs `wgp doctor`.
Default source: git+https://github.com/jmanhype/wangp-dspy.git@main
No root or sudo is required.

Options:
  --dry-run             Print the exact commands without changing the machine.
  --source <path-or-url>
                        Install from an explicit checkout path or Git URL.
  --checkout <dir>      Clone the selected repository into <dir> after install
                        and print the exact quickstart commands.

One-command install:
  curl -LsSf https://raw.githubusercontent.com/jmanhype/wangp-dspy/main/install.sh -o install.sh
  sh install.sh

Wangp first verifies uv, then runs:
  uv tool install --upgrade --from <source> wangp-dspy
  <user-tool-bin>/wgp doctor
EOF
}

fail_missing_uv() {
    printf '%s\n' \
        'MISSING_PREREQUISITE: uv is required to install Wangp.' \
        'Install uv first with:' \
        '  curl -LsSf https://astral.sh/uv/install.sh -o uv-installer.sh' \
        '  sh uv-installer.sh' >&2
    exit 127
}

fail_tool_bin() {
    printf '%s\n' \
        'INSTALLER_ERROR: cannot resolve the uv tool executable directory.' \
        'Run uv tool dir --bin and set UV_TOOL_BIN_DIR to that directory.' >&2
    exit 5
}

fail_wgp_missing() {
    printf '%s\n' \
        "INSTALLER_ERROR: wgp executable is missing after installation." \
        "Checked: $WGP_BIN/wgp" \
        "Expected uv executable directory: $WGP_BIN" \
        'Remediation: run uv tool dir --bin, verify wgp there, and rerun install.sh.' >&2
    exit 6
}

fail_checkout_exists() {
    printf '%s\n' \
        "INVALID_CHECKOUT: destination already exists: $CHECKOUT" \
        'Choose an absent directory or remove that copy explicitly.' >&2
    exit 7
}

fail_missing_git() {
    printf '%s\n' \
        'MISSING_PREREQUISITE: git is required when --checkout is used.' \
        'Install Git from https://git-scm.com/book/en/v2/Getting-Started-Installing-Git' >&2
    exit 127
}

uv_requirement() {
    case $1 in
        git+*|/*|./*|../*) printf '%s\n' "$1" ;;
        http://*|https://*) printf 'git+%s\n' "$1" ;;
        *) printf '%s\n' "$1" ;;
    esac
}

clone_url() {
    case $1 in
        git+*)
            value=${1#git+}
            value=${value%@*}
            printf '%s\n' "$value"
            ;;
        *) printf '%s\n' "$1" ;;
    esac
}

print_follow_up() {
    printf '%s\n' 'Checkout ready. Next commands:'
    printf '  cd "%s"\n' "$CHECKOUT"
    printf '  uv sync --extra dev\n'
    printf '  uv run --frozen --extra dev python scripts/run_content_brief.py --brief datasets/content_briefs/lf004-operator-dogfood-56f/brief.json --plates datasets/content_briefs/lf004-operator-dogfood/plates --out "${TMPDIR:-/tmp}/wangp-quickstart/plan.json" --run-dir "${TMPDIR:-/tmp}/wangp-quickstart/run"\n'
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
            CLONE_SOURCE=$(clone_url "$SOURCE")
            shift 2
            ;;
        --source=*)
            SOURCE=${1#--source=}
            CLONE_SOURCE=$(clone_url "$SOURCE")
            shift
            ;;
        --checkout)
            [ "$#" -ge 2 ] || { usage >&2; exit 2; }
            CHECKOUT=$2
            shift 2
            ;;
        --checkout=*)
            CHECKOUT=${1#--checkout=}
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
if [ "${UV_TOOL_BIN_DIR+set}" = set ]; then
    [ -n "$UV_TOOL_BIN_DIR" ] || fail_tool_bin
    WGP_BIN=$UV_TOOL_BIN_DIR
else
    WGP_BIN=$(uv tool dir --bin 2>/dev/null) || fail_tool_bin
    [ -n "$WGP_BIN" ] || fail_tool_bin
fi
UV_SOURCE=$(uv_requirement "$SOURCE")

if [ -n "$CHECKOUT" ] && [ "$DRY_RUN" != true ] && [ -e "$CHECKOUT" ]; then
    fail_checkout_exists
fi
if [ -n "$CHECKOUT" ]; then
    command -v git >/dev/null 2>&1 || fail_missing_git
fi

if [ "$DRY_RUN" = true ]; then
    printf '%s\n' 'Dry run: no changes will be made.'
    printf '%s\n' "uv tool install --upgrade --from $UV_SOURCE wangp-dspy"
    printf '%s\n' "$WGP_BIN/wgp doctor"
    if [ -n "$CHECKOUT" ]; then
        printf '%s\n' "git clone $CLONE_SOURCE $CHECKOUT"
        print_follow_up
    fi
    exit 0
fi

uv tool install --upgrade --from "$UV_SOURCE" wangp-dspy
[ -x "$WGP_BIN/wgp" ] || fail_wgp_missing
"$WGP_BIN/wgp" doctor
if [ -n "$CHECKOUT" ]; then
    git clone "$CLONE_SOURCE" "$CHECKOUT"
    print_follow_up
fi
