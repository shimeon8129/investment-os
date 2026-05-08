#!/usr/bin/env bash
# Investment OS — Run Observation Replay for a given trading date
#
# Usage: scripts/run_observation_replay.sh YYYY-MM-DD

set -euo pipefail

DATE="${1:-}"
if [[ -z "$DATE" ]]; then
    echo "Usage: $0 YYYY-MM-DD" >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"

PYTHON="${ROOT}/venv/bin/python3"
if [[ ! -x "$PYTHON" ]]; then
    PYTHON="python3"
fi

echo "[run_observation_replay] DATE=${DATE}"
echo "[run_observation_replay] Step 1: Build daily observation summary..."
PYTHONPATH="$ROOT" "$PYTHON" "$ROOT/jobs/observation_replay_builder.py" "$DATE"

echo "[run_observation_replay] Step 2: Generate replay report..."
PYTHONPATH="$ROOT" "$PYTHON" -m reporting.observation_replay_report "$DATE"

echo "[run_observation_replay] Done."
