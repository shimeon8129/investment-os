# Investment OS Integration Audit

Generated at: 2026-05-01 15:42:06

## Python Module List
controller/main.py
data_node/fetch_news.py
data_node/fetch_tw.py
data_node/fetch_us.py
data_node/__init__.py
data_node/loader.py
data_node/sources/finmind.py
data_node/sources/news_api.py
data_node/sources/yfinance.py
decision/decision_engine.py
decision/entry_engine.py
decision/entry_lock.py
decision/entry_tracker.py
decision/lock.py
decision/market.py
decision/mode.py
decision/position_lock.py
decision/ready_predictor.py
decision/risk_lock.py
decision/risk.py
execution/broker.py
execution/exit.py
execution/notifier.py
execution/portfolio_dashboard.py
execution/portfolio.py
execution/risk.py
execution/trade_log_writer.py
execution/trade.py
feedback/performance.py
feedback/review.py
feedback/trade_log.py
jobs/daily_run.py
pipeline/chips_loader.py
pipeline/main_backup.py
pipeline/main.py
pipeline/narrative_loader.py
pipeline/news_heat_loader.py
pipeline/ranking_engine.py
processing/ai_interpret.py
processing/features.py
processing/__init__.py
processing/structuring.py
processing/transform.py
reporting/candidate_review.py
reporting/daily_decision_dashboard.py
reporting/__init__.py
reporting/portfolio_candidate_review.py
scanner/alpha.py
scanner/basic_scanner.py
scanner/breakout_scan.py
scanner/minervini_scanner.py
scanner/pre_scanner.py
scanner/ranking.py
scanner/universe.py
signal_engine/breakout.py
signal_engine/entry.py
signal_engine/gear_shift.py
signal_engine/inference.py
signal_engine/__init__.py
signal_engine/reversal.py
signal_engine/rotation.py

## Data File Status
FOUND  data/watchlist.json
FOUND  data/master/ai_watchlist_source.csv
FOUND  data/portfolio/current_holdings.json
FOUND  data/candidates.json
FOUND  data/final_narrative.json
FOUND  data/decision.json
FOUND  data/processed/signal_snapshot.json

## Main Entrypoints
FOUND  jobs/daily_run.py
FOUND  docker/hermes-agent/run_investment_os_daily.sh
FOUND  reporting/daily_decision_dashboard.py
FOUND  decision/decision_engine.py
FOUND  pipeline/main.py
FOUND  controller/main.py

## Imports Map
data_node/loader.py:import pandas as pd
data_node/loader.py:import yfinance as yf
decision/decision_engine.py:from data_node.loader import load_price_data
decision/decision_engine.py:from decision.entry_engine import generate_entry_signal
decision/decision_engine.py:from decision.entry_lock import apply_entry_lock
decision/decision_engine.py:    from decision.entry_tracker import track_entry_transition
decision/decision_engine.py:    from decision.ready_predictor import predict_ready_breakout
decision/decision_engine.py:import json
decision/decision_engine.py:import os
decision/entry_tracker.py:import json
decision/entry_tracker.py:import os
execution/portfolio.py:import json
execution/risk.py:import pandas as pd
execution/trade_log_writer.py:from datetime import datetime
execution/trade_log_writer.py:import json
execution/trade_log_writer.py:import os
feedback/performance.py:import json
jobs/daily_run.py:from datetime import datetime
jobs/daily_run.py:from __future__ import annotations
jobs/daily_run.py:from pathlib import Path
jobs/daily_run.py:import json
jobs/daily_run.py:import os
jobs/daily_run.py:import subprocess
jobs/daily_run.py:import sys
pipeline/chips_loader.py:import json
pipeline/chips_loader.py:import os
pipeline/main_backup.py:from data_node.loader import load_price_data
pipeline/main_backup.py:from decision.lock import apply_market_lock
pipeline/main_backup.py:from decision.market import market_filter
pipeline/main_backup.py:from decision.position_lock import apply_position_lock
pipeline/main_backup.py:from decision.risk_lock import apply_risk_lock
pipeline/main_backup.py:from execution.exit import check_exit
pipeline/main_backup.py:from execution.portfolio import load_portfolio
pipeline/main_backup.py:from execution.trade import execute_trade
pipeline/main_backup.py:from execution.trade_log_writer import write_trade_log
pipeline/main_backup.py:from feedback.performance import analyze_performance
pipeline/main_backup.py:from pipeline.ranking_engine import rank_stocks, print_top_picks
pipeline/main_backup.py:from processing.features import compute_features
pipeline/main_backup.py:from scanner.basic_scanner import scan_candidates
pipeline/main_backup.py:from scanner.universe import get_tw_universe, get_us_universe
pipeline/main_backup.py:from signal_engine.entry import generate_entry_signal
pipeline/main_backup.py:import os
pipeline/main_backup.py:import sys
pipeline/main.py:from data_node.loader import load_price_data
pipeline/main.py:from data_node.loader import load_price_data
pipeline/main.py:from decision.lock import apply_market_lock
pipeline/main.py:from decision.lock import apply_market_lock
pipeline/main.py:from decision.market import market_filter
pipeline/main.py:from decision.market import market_filter
pipeline/main.py:from decision.position_lock import apply_position_lock
pipeline/main.py:from decision.position_lock import apply_position_lock
pipeline/main.py:from decision.risk_lock import apply_risk_lock
pipeline/main.py:from execution.exit import check_exit
pipeline/main.py:from execution.exit import check_exit
pipeline/main.py:from execution.portfolio_dashboard import build_daily_dashboard
pipeline/main.py:from execution.portfolio import load_portfolio
pipeline/main.py:from execution.portfolio import load_portfolio
pipeline/main.py:from execution.risk import apply_risk_filters
pipeline/main.py:from execution.trade import execute_trade
pipeline/main.py:from execution.trade import execute_trade
pipeline/main.py:from execution.trade_log_writer import write_trade_log
pipeline/main.py:from execution.trade_log_writer import write_trade_log
pipeline/main.py:from feedback.performance import analyze_performance
pipeline/main.py:from feedback.performance import analyze_performance
pipeline/main.py:from pipeline.chips_loader import load_chips_map
pipeline/main.py:from pipeline.chips_loader import load_chips_map
pipeline/main.py:from pipeline.narrative_loader import load_narrative_map
pipeline/main.py:from pipeline.narrative_loader import load_narrative_map
pipeline/main.py:from pipeline.news_heat_loader import load_news_heat_map
pipeline/main.py:from pipeline.news_heat_loader import load_news_heat_map
pipeline/main.py:from pipeline.ranking_engine import rank_stocks, print_top_picks
pipeline/main.py:from pipeline.ranking_engine import rank_stocks, print_top_picks
pipeline/main.py:from processing.features import compute_features
pipeline/main.py:from processing.features import compute_features
pipeline/main.py:from scanner.basic_scanner import scan_candidates
pipeline/main.py:from scanner.basic_scanner import scan_candidates
pipeline/main.py:from scanner.minervini_scanner import build_minervini_map, scan_minervini_candidates
pipeline/main.py:from scanner.minervini_scanner import build_minervini_map, scan_minervini_candidates
pipeline/main.py:from scanner.universe import get_tw_universe, get_us_universe
pipeline/main.py:from scanner.universe import get_tw_universe, get_us_universe
pipeline/main.py:from signal_engine.entry import generate_entry_signal
pipeline/main.py:from signal_engine.entry import generate_entry_signal
pipeline/main.py:import os
pipeline/main.py:import os
pipeline/main.py:import sys
pipeline/main.py:import sys
pipeline/narrative_loader.py:import json
pipeline/narrative_loader.py:import os
pipeline/news_heat_loader.py:import json
pipeline/news_heat_loader.py:import os
reporting/candidate_review.py:from datetime import datetime
reporting/candidate_review.py:from metadata.ticker_master import (
reporting/candidate_review.py:from pathlib import Path
reporting/candidate_review.py:import json
reporting/candidate_review.py:    Preserves raw values and resolves canonical name from ticker master.
reporting/daily_decision_dashboard.py:from datetime import datetime
reporting/daily_decision_dashboard.py:from metadata.ticker_master import (
reporting/daily_decision_dashboard.py:from pathlib import Path
reporting/daily_decision_dashboard.py:from portfolio.holdings_loader import load_current_holdings
reporting/daily_decision_dashboard.py:from reporting.candidate_review import (
reporting/daily_decision_dashboard.py:from reporting.portfolio_candidate_review import build_review_rows
reporting/daily_decision_dashboard.py:import json
reporting/portfolio_candidate_review.py:from datetime import datetime
reporting/portfolio_candidate_review.py:from metadata.ticker_master import (
reporting/portfolio_candidate_review.py:from pathlib import Path
reporting/portfolio_candidate_review.py:from portfolio.holdings_loader import load_current_holdings
reporting/portfolio_candidate_review.py:import json
reporting/portfolio_candidate_review.py:        "- [ ] No execution decision is made directly from this report",
scanner/basic_scanner.py:from data_node.loader import load_price_data
scanner/basic_scanner.py:# from pre_scanner import run_pre_scanner
scanner/basic_scanner.py:# from scanner.pre_scanner import run_pre_scanner
scanner/basic_scanner.py:import json
scanner/basic_scanner.py:import os
scanner/basic_scanner.py:import pandas as pd
scanner/basic_scanner.py:import sys
scanner/minervini_scanner.py:from processing.features import compute_features
scanner/pre_scanner.py:import pandas as pd
scanner/universe.py:import pandas as pd
