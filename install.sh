#!/bin/sh
set -eu

DEFAULT_REPOSITORY=https://github.com/jmanhype/wangp-dspy.git
DEFAULT_SOURCE=git+$DEFAULT_REPOSITORY@main
SOURCE=$DEFAULT_SOURCE
CLONE_SOURCE=$DEFAULT_REPOSITORY
CHECKOUT=
DRY_RUN=false
CLEAN_PROOF=
CLEAN_GENERATED=
GENERATED_AUTHORIZATION=
GENERATED_MANIFEST=
ARGV_FILE=
INSTALLER_PATH=$0

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
  --clean-proof <dir>   Run the complete no-GPU clean-machine proof in an
                        isolated workspace at <dir>, then fail closed with the
                        missing generation inputs. The workspace must be absent.
  --clean-generated-proof <dir>
                        Run the separately authorized real H3 generated-proof
                        mode in an absent isolated workspace. Requires explicit
                        relative authorization, host, and manifest inputs.
  --generated-authorization <path>
                        Committed authorization JSON for --clean-generated-proof.
  --generated-manifest <path>  Committed exact model manifest.

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

fail_clean_proof_exists() {
    printf '%s\n' \
        "INVALID_CLEAN_PROOF_WORKSPACE: destination already exists: $CLEAN_PROOF" \
        'Choose an absent disposable directory and rerun install.sh.' >&2
    exit 8
}

fail_clean_generated_exists() {
    printf '%s\n' \
        "INVALID_CLEAN_GENERATED_WORKSPACE: destination already exists: $CLEAN_GENERATED" \
        'Choose an absent disposable directory and rerun install.sh.' >&2
    exit 10
}

fail_clean_generated_input() {
    printf '%s\n' \
        "INVALID_CLEAN_GENERATED_INPUT: $1" \
        'The generated-proof mode requires committed relative authorization, host, and manifest paths.' >&2
    exit 11
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

prepare_clean_proof_workspace() {
    [ ! -e "$CLEAN_PROOF" ] || fail_clean_proof_exists
    mkdir -p "$CLEAN_PROOF/home/.config" "$CLEAN_PROOF/cache" \
        "$CLEAN_PROOF/tools" "$CLEAN_PROOF/bin" "$CLEAN_PROOF/proof"
    HOME=$CLEAN_PROOF/home
    XDG_CONFIG_HOME=$CLEAN_PROOF/home/.config
    XDG_DATA_HOME=$CLEAN_PROOF/home/.local/share
    UV_CACHE_DIR=$CLEAN_PROOF/cache
    UV_TOOL_DIR=$CLEAN_PROOF/tools
    UV_TOOL_BIN_DIR=$CLEAN_PROOF/bin
    export HOME XDG_CONFIG_HOME XDG_DATA_HOME UV_CACHE_DIR UV_TOOL_DIR UV_TOOL_BIN_DIR
    PATH=$CLEAN_PROOF/bin:$PATH
    export PATH
    unset WANGP_SSH_TARGET WANGP_WGP_ROOT WANGP_PULL_ROOT WANGP_WGP_PYTHON WANGP_3090
    WANGP_CONFIG=$CLEAN_PROOF/proof/empty-config.toml
    export WANGP_CONFIG
    : > "$WANGP_CONFIG"
    git config --file "$CLEAN_PROOF/proof/git-config" init.defaultBranch main
    GIT_CONFIG_GLOBAL=$CLEAN_PROOF/proof/git-config
    export GIT_CONFIG_GLOBAL
    if [ -z "$CHECKOUT" ]; then
        CHECKOUT=$CLEAN_PROOF/checkout
    fi
}

prepare_clean_generated_workspace() {
    CLEAN_PROOF=$CLEAN_GENERATED
    prepare_clean_proof_workspace
    CLEAN_GENERATED=$CLEAN_PROOF
    CLEAN_PROOF=
    mkdir -p "$CLEAN_GENERATED/pull"
}

run_clean_proof() {
    proof=$CLEAN_PROOF/proof
    cp "$ARGV_FILE" "$proof/argv.nul"
    git -C "$CHECKOUT" rev-parse HEAD > "$proof/resolved-commit.txt"
    git --version > "$proof/git-version.txt"
    uv --version > "$proof/uv-version.txt"

    printf '%s\n' 'Clean-machine no-GPU lane: syncing the disposable checkout.'
    (cd "$CHECKOUT" && uv sync --extra dev) > "$proof/uv-sync.log" 2>&1

    printf '%s\n' 'Clean-machine no-GPU lane: emitting the deterministic plan.'
    (cd "$CHECKOUT" && uv run --frozen --extra dev python scripts/run_content_brief.py \
        --brief datasets/content_briefs/lf004-operator-dogfood-56f/brief.json \
        --plates datasets/content_briefs/lf004-operator-dogfood/plates \
        --output "$proof/plan.json" \
        --run-dir "$proof/plan-run") > "$proof/plan.log" 2>&1
    cat "$proof/plan.log"
    git -C "$CHECKOUT" status --short > "$proof/repository-status.txt"

    remote_rc=0
    (cd "$CHECKOUT" && "$WGP_BIN/wgp" first-run remote --json) \
        > "$proof/host-refusal.json" 2> "$proof/host-refusal.stderr" || remote_rc=$?
    if [ "$remote_rc" -ne 3 ]; then
        printf '%s\n' \
            "INSTALLER_ERROR: expected typed host refusal exit 3, got $remote_rc." \
            'No generation, queue admission, SSH, model download, or fallback was attempted.' >&2
        exit 9
    fi

    (cd "$CHECKOUT" && "$WGP_BIN/wgp" doctor --capabilities --json) \
        > "$proof/capabilities.json" 2> "$proof/capabilities.stderr"

    refusal_rc=0
    (cd "$CHECKOUT" && uv run --frozen --extra dev python \
        scripts/record_clean_machine_refusal.py \
        --proof-dir "$proof" \
        --source "$SOURCE" \
        --clone-source "$CLONE_SOURCE" \
        --checkout "$CHECKOUT" \
        --installer "$INSTALLER_PATH") || refusal_rc=$?
    rm -f "$proof/argv.nul"
    exit "$refusal_rc"
}

run_clean_generated_proof() {
    proof=$CLEAN_GENERATED/proof
    cp "$ARGV_FILE" "$proof/argv.nul"
    git -C "$CHECKOUT" rev-parse HEAD > "$proof/resolved-commit.txt"
    git -C "$CHECKOUT" status --short > "$proof/repository-status.txt"
    uv --version > "$proof/uv-version.txt"

    printf '%s\n' 'Clean-machine generated lane: syncing the disposable checkout.'
    (cd "$CHECKOUT" && uv sync --extra dev) > "$proof/uv-sync.log" 2>&1

    printf '%s\n' 'Clean-machine generated lane: running preflight, one governed create, and evidence gates.'
    generated_rc=0
    (cd "$CHECKOUT" && uv run --frozen --extra dev python scripts/record_clean_generated_proof.py \
        --proof-dir "$proof" --checkout "$CHECKOUT" --installer "$INSTALLER_PATH" \
        --authorization "$CHECKOUT/$GENERATED_AUTHORIZATION" \
        --model-manifest "$CHECKOUT/$GENERATED_MANIFEST") \
        > "$proof/generated.stdout" 2> "$proof/generated.stderr" || generated_rc=$?
    cat "$proof/generated.stdout"
    cat "$proof/generated.stderr" >&2
    exit "$generated_rc"
}

command -v uv >/dev/null 2>&1 || fail_missing_uv
ARGV_FILE=$(mktemp "${TMPDIR:-/tmp}/wangp-install-argv.XXXXXX")
trap 'rm -f "$ARGV_FILE"' EXIT HUP INT TERM
printf '%s\0' "$@" > "$ARGV_FILE"

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
        --clean-proof)
            [ "$#" -ge 2 ] || { usage >&2; exit 2; }
            CLEAN_PROOF=$2
            shift 2
            ;;
        --clean-proof=*)
            CLEAN_PROOF=${1#--clean-proof=}
            shift
            ;;
        --clean-generated-proof)
            [ "$#" -ge 2 ] || { usage >&2; exit 2; }
            CLEAN_GENERATED=$2
            shift 2
            ;;
        --generated-authorization)
            [ "$#" -ge 2 ] || { usage >&2; exit 2; }
            GENERATED_AUTHORIZATION=$2
            shift 2
            ;;
        --generated-manifest)
            [ "$#" -ge 2 ] || { usage >&2; exit 2; }
            GENERATED_MANIFEST=$2
            shift 2
            ;;
        *)
            printf '%s\n' "Unknown argument: $1" >&2
            usage >&2
            exit 2
            ;;
    esac
done

if [ -n "$CLEAN_GENERATED" ]; then
    if [ -n "$CLEAN_PROOF" ]; then
        printf '%s\n' 'INVALID_CLEAN_GENERATED_INPUT: --clean-proof and --clean-generated-proof are mutually exclusive.' >&2
        exit 11
    fi
    if [ -n "$CHECKOUT" ]; then
        fail_clean_generated_input '--checkout is incompatible with the isolated generated-proof workspace.'
    fi
    for input in "$GENERATED_AUTHORIZATION" "$GENERATED_MANIFEST"; do
        if [ -z "$input" ]; then
            fail_clean_generated_input 'all three explicit input paths are required.'
        fi
        case $input in
            /*|../*|*/../*) fail_clean_generated_input "$input must be a safe repository-relative path." ;;
        esac
        if [ "$DRY_RUN" != true ] && { [ ! -f "$input" ] || [ -L "$input" ]; }; then
            fail_clean_generated_input "$input is not a regular committed file."
        fi
    done
fi

if [ -n "$CLEAN_PROOF" ]; then
    case $CLEAN_PROOF in
        /*) ;;
        *) CLEAN_PROOF=$(pwd)/$CLEAN_PROOF ;;
    esac
    if [ -z "$CHECKOUT" ]; then
        CHECKOUT=$CLEAN_PROOF/checkout
    fi
    case $INSTALLER_PATH in
        /*) ;;
        *) INSTALLER_PATH=$(pwd)/$INSTALLER_PATH ;;
    esac
    if [ "$DRY_RUN" != true ]; then
        prepare_clean_proof_workspace
    fi
fi

if [ -n "$CLEAN_GENERATED" ]; then
    case $CLEAN_GENERATED in
        /*) ;;
        *) CLEAN_GENERATED=$(pwd)/$CLEAN_GENERATED ;;
    esac
    case $INSTALLER_PATH in
        /*) ;;
        *) INSTALLER_PATH=$(pwd)/$INSTALLER_PATH ;;
    esac
    if [ "$DRY_RUN" = true ]; then
        CHECKOUT=$CLEAN_GENERATED/checkout
    fi
    if [ "$DRY_RUN" != true ]; then
        prepare_clean_generated_workspace
    fi
fi

if [ -n "$CLEAN_PROOF" ] && [ "$DRY_RUN" = true ]; then
    WGP_BIN=$CLEAN_PROOF/bin
elif [ -n "$CLEAN_GENERATED" ] && [ "$DRY_RUN" = true ]; then
    WGP_BIN=$CLEAN_GENERATED/bin
elif [ "${UV_TOOL_BIN_DIR+set}" = set ]; then
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
        if [ -n "$CLEAN_PROOF" ]; then
            printf '%s\n' "mkdir -p $CLEAN_PROOF/home/.config $CLEAN_PROOF/cache $CLEAN_PROOF/tools $CLEAN_PROOF/bin $CLEAN_PROOF/proof"
            printf '%s\n' "HOME=$CLEAN_PROOF/home; XDG_CONFIG_HOME=$CLEAN_PROOF/home/.config; XDG_DATA_HOME=$CLEAN_PROOF/home/.local/share; UV_CACHE_DIR=$CLEAN_PROOF/cache; UV_TOOL_DIR=$CLEAN_PROOF/tools; UV_TOOL_BIN_DIR=$CLEAN_PROOF/bin; export HOME XDG_CONFIG_HOME XDG_DATA_HOME UV_CACHE_DIR UV_TOOL_DIR UV_TOOL_BIN_DIR"
            printf '%s\n' "unset WANGP_SSH_TARGET WANGP_WGP_ROOT WANGP_PULL_ROOT WANGP_WGP_PYTHON WANGP_3090"
            printf '%s\n' "WANGP_CONFIG=$CLEAN_PROOF/proof/empty-config.toml; export WANGP_CONFIG"
            printf '%s\n' "uv sync --extra dev"
            printf '%s\n' "uv run --frozen --extra dev python scripts/run_content_brief.py --brief datasets/content_briefs/lf004-operator-dogfood-56f/brief.json --plates datasets/content_briefs/lf004-operator-dogfood/plates --output $CLEAN_PROOF/proof/plan.json --run-dir $CLEAN_PROOF/proof/plan-run"
            printf '%s\n' "$WGP_BIN/wgp first-run remote --json"
            printf '%s\n' "$WGP_BIN/wgp doctor --capabilities --json"
            printf '%s\n' "uv run --frozen --extra dev python scripts/record_clean_machine_refusal.py ..."
        elif [ -z "$CLEAN_GENERATED" ]; then
            print_follow_up
        fi
        if [ -n "$CLEAN_GENERATED" ]; then
            printf '%s\n' "git clone $CLONE_SOURCE $CHECKOUT; uv sync --extra dev; uv run --frozen --extra dev python scripts/record_clean_generated_proof.py --proof-dir $CLEAN_GENERATED/proof --checkout $CHECKOUT --installer $INSTALLER_PATH --authorization $CHECKOUT/$GENERATED_AUTHORIZATION --model-manifest $CHECKOUT/$GENERATED_MANIFEST"
        fi
    fi
    exit 0
fi

uv tool install --upgrade --from "$UV_SOURCE" wangp-dspy
[ -x "$WGP_BIN/wgp" ] || fail_wgp_missing
"$WGP_BIN/wgp" doctor
if [ -n "$CHECKOUT" ]; then
    git clone "$CLONE_SOURCE" "$CHECKOUT"
    if [ -z "$CLEAN_PROOF" ] && [ -z "$CLEAN_GENERATED" ]; then
        print_follow_up
    fi
    if [ -n "$CLEAN_GENERATED" ]; then
        for input in "$GENERATED_AUTHORIZATION" "$GENERATED_MANIFEST"; do
            if [ ! -f "$CHECKOUT/$input" ] || [ -L "$CHECKOUT/$input" ]; then
                fail_clean_generated_input "cloned checkout is missing committed input $input."
            fi
        done
    fi
fi
if [ -n "$CLEAN_PROOF" ]; then
    run_clean_proof
fi
if [ -n "$CLEAN_GENERATED" ]; then
    run_clean_generated_proof
fi
