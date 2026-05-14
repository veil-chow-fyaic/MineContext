#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HARNESS_DIR="${MINECONTEXT_CLI_HARNESS_DIR:-$ROOT_DIR/agent-harness}"

if [[ ! -f "$HARNESS_DIR/setup.py" ]]; then
  BUNDLED_HARNESS="$SCRIPT_DIR/agent-harness"
  if [[ -f "$BUNDLED_HARNESS/setup.py" ]]; then
    HARNESS_DIR="$BUNDLED_HARNESS"
  fi
fi

if [[ ! -f "$HARNESS_DIR/setup.py" ]]; then
  APP_HARNESS="/Applications/MineContext.app/Contents/Resources/cli/agent-harness"
  if [[ -f "$APP_HARNESS/setup.py" ]]; then
    HARNESS_DIR="$APP_HARNESS"
  fi
fi

if [[ ! -f "$HARNESS_DIR/setup.py" ]]; then
  echo "MineContext CLI harness not found." >&2
  echo "Set MINECONTEXT_CLI_HARNESS_DIR, run this script from the MineContext repository, or run the bundled app resource script." >&2
  exit 1
fi

PYTHON_BIN="${PYTHON:-python3}"

if [[ -z "${VIRTUAL_ENV:-}" ]]; then
  "$PYTHON_BIN" -m pip install --user "$HARNESS_DIR"
else
  "$PYTHON_BIN" -m pip install "$HARNESS_DIR"
fi

cat <<EOF
MineContext CLI installed from:
  $HARNESS_DIR

Then verify with:
  cli-anything-minecontext --json service doctor
EOF
