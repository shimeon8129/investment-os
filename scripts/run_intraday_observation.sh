#!/usr/bin/env bash
# Manual trigger for Investment OS intraday observation runner v0.1.
# Usage: scripts/run_intraday_observation.sh <slot>
# Slots: pre_market | market_open | mid_morning | noon_review | pre_close | post_close_review
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/.."

if [ -d "venv" ]; then
    source venv/bin/activate
fi

export PYTHONPATH="$PWD"

python3 jobs/intraday_observation.py "$1"
