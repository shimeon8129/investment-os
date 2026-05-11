#!/usr/bin/env bash
# Manual trigger for Investment OS intraday observation runner v0.1.
# Usage: scripts/run_intraday_observation.sh <slot>
# TW slots: pre_market | market_open | mid_morning | noon_review | pre_close | post_close_review
# US slots:  us_market_open | us_midday | us_post_close_review
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/.."

if [ -d "venv" ]; then
    source venv/bin/activate
fi

export PYTHONPATH="$PWD"

SLOT="$1"
MARKET_FLAG=""
if [[ "$SLOT" == us_* ]]; then
    MARKET_FLAG="--market us"
fi

python3 jobs/intraday_observation.py "$SLOT" $MARKET_FLAG
