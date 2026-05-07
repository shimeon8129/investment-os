#!/usr/bin/env bash
# Manual trigger for Investment OS daily observation run.
# Usage: bash scripts/run_observation_daily.sh
set -euo pipefail

cd "$(dirname "$0")/.."

if [ -d "venv" ]; then
    source venv/bin/activate
fi

export PYTHONPATH="$PWD"

python3 -m jobs.observation_daily
