from pathlib import Path
import json
from datetime import datetime

from portfolio.holdings_loader import load_current_holdings
from metadata.ticker_master import (
    load_ticker_master,
    normalize_ticker,
    resolve_canonical_name,
    resolve_asset_type,
)
from reporting.candidate_review import (
    find_existing_candidates_file,
    normalize_candidates,
    adapt_candidate_schema,
)
from reporting.portfolio_candidate_review import build_review_rows


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_HOLDINGS_PATH = PROJECT_ROOT / "data" / "portfolio" / "current_holdings.json"
DEFAULT_REPORT_PATH = (
    PROJECT_ROOT
    / "docs"
    / f"DAILY_DECISION_DASHBOARD_{datetime.now().strftime('%Y%m%d')}.md"
)


def _load_json(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def safe_value(value, default="-"):
    if value is None:
        return default
    if isinstance(value, float):
        return round(value, 4)
    return value


def load_candidates(candidate_path=None):
    if candidate_path is None:
        candidate_path = find_existing_candidates_file()
    else:
        candidate_path = Path(candidate_path)

    ticker_master = load_ticker_master()
    raw_data = _load_json(candidate_path)
    raw_candidates = normalize_candidates(raw_data)

    candidates = [
        adapt_candidate_schema(row, ticker_master=ticker_master)
        for row in raw_candidates
    ]

    return candidate_path, candidates


def load_holdings(holdings_path=DEFAULT_HOLDINGS_PATH):
    holdings_path = Path(holdings_path)
    data = load_current_holdings(holdings_path)

    ticker_master = load_ticker_master()
    holdings = []

    for item in data.get("holdings", []):
        ticker = normalize_ticker(item.get("ticker"))
        name = resolve_canonical_name(
            ticker,
            fallback_name=item.get("name"),
            master=ticker_master,
        )
        asset_type = resolve_asset_type(
            ticker,
            fallback_asset_type=item.get("asset_type"),
            master=ticker_master,
        )

        holdings.append({
            **item,
            "ticker": ticker,
            "name": name,
            "asset_type": asset_type,
        })

    return holdings_path, data, holdings


def sort_candidates(candidates: list) -> list:
    def score_key(row: dict):
        score = row.get("scanner_score")
        if isinstance(score, (int, float)):
            return score
        return -999

    return sorted(candidates, key=score_key, reverse=True)


def build_market_state_section(candidates: list) -> str:
    """
    Dashboard v0 does not infer true market regime.
    It only summarizes candidate signal distribution.
    """
    signal_counts = {}

    for row in candidates:
        signal = str(row.get("signal", "UNKNOWN"))
        signal_counts[signal] = signal_counts.get(signal, 0) + 1

    lines = [
        "## 1. Market / Signal State",
        "",
        "Dashboard v0 does not make a new market regime decision.",
        "It summarizes current candidate output only.",
        "",
        "### Candidate Signal Counts",
        "",
    ]

    if signal_counts:
        for signal, count in sorted(signal_counts.items()):
            lines.append(f"- {signal}: {count}")
    else:
        lines.append("- No candidates found")

    return "\n".join(lines)


def build_top_candidates_section(candidates: list, top_n: int = 10) -> str:
    rows = sort_candidates(candidates)[:top_n]

    headers = [
        "rank",
        "ticker",
        "name",
        "asset_type",
        "close",
        "scanner_score",
        "signal",
        "raw_score",
        "raw_level",
        "raw_price",
    ]

    lines = [
        "## 2. Top Candidates",
        "",
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]

    for idx, row in enumerate(rows, start=1):
        values = [
            idx,
            safe_value(row.get("ticker")),
            safe_value(row.get("name")),
            safe_value(row.get("asset_type")),
            safe_value(row.get("close")),
            safe_value(row.get("scanner_score")),
            safe_value(row.get("signal")),
            safe_value(row.get("raw_score")),
            safe_value(row.get("raw_level")),
            safe_value(row.get("raw_price")),
        ]

        values = [str(v).replace("|", "/") for v in values]
        lines.append("| " + " | ".join(values) + " |")

    if not rows:
        lines.append("")
        lines.append("No candidate data available.")

    return "\n".join(lines)


def build_current_holdings_section(holdings_data: dict, holdings: list) -> str:
    headers = [
        "ticker",
        "name",
        "shares",
        "asset_type",
        "market",
    ]

    lines = [
        "## 3. Current Holdings",
        "",
        f"- Holdings as_of: `{holdings_data.get('as_of', '-')}`",
        f"- Currency: `{holdings_data.get('currency', '-')}`",
        "",
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]

    for row in holdings:
        values = [
            safe_value(row.get("ticker")),
            safe_value(row.get("name")),
            safe_value(row.get("shares")),
            safe_value(row.get("asset_type")),
            safe_value(row.get("market")),
        ]

        values = [str(v).replace("|", "/") for v in values]
        lines.append("| " + " | ".join(values) + " |")

    return "\n".join(lines)


def build_portfolio_candidate_sections(review_rows: list) -> str:
    buckets = {
        "HELD_AND_CANDIDATE": [],
        "HELD_NOT_CANDIDATE": [],
        "CANDIDATE_NOT_HELD": [],
    }

    for row in review_rows:
        status = row.get("position_status")
        if status in buckets:
            buckets[status].append(row)

    lines = [
        "## 4. Portfolio vs Candidate Buckets",
        "",
        "### 4.1 Held and Candidate",
        "",
    ]

    if buckets["HELD_AND_CANDIDATE"]:
        for row in buckets["HELD_AND_CANDIDATE"]:
            lines.append(
                f"- {row.get('ticker')} {row.get('name')} — "
                f"shares: {row.get('shares')}, "
                f"score: {row.get('scanner_score')}, "
                f"signal: {row.get('signal')}"
            )
    else:
        lines.append("- None")

    lines.extend([
        "",
        "### 4.2 Held but Not Candidate",
        "",
    ])

    if buckets["HELD_NOT_CANDIDATE"]:
        for row in buckets["HELD_NOT_CANDIDATE"]:
            lines.append(
                f"- {row.get('ticker')} {row.get('name')} — "
                f"shares: {row.get('shares')}; "
                "manual review required."
            )
    else:
        lines.append("- None")

    lines.extend([
        "",
        "### 4.3 Candidate but Not Held",
        "",
    ])

    if buckets["CANDIDATE_NOT_HELD"]:
        for row in buckets["CANDIDATE_NOT_HELD"][:20]:
            lines.append(
                f"- {row.get('ticker')} {row.get('name')} — "
                f"score: {row.get('scanner_score')}, "
                f"signal: {row.get('signal')}"
            )

        if len(buckets["CANDIDATE_NOT_HELD"]) > 20:
            lines.append(f"- ... {len(buckets['CANDIDATE_NOT_HELD']) - 20} more")
    else:
        lines.append("- None")

    return "\n".join(lines)


def build_risk_notes_section(review_rows: list) -> str:
    held_not_candidate = [
        row for row in review_rows
        if row.get("position_status") == "HELD_NOT_CANDIDATE"
    ]

    candidate_not_held = [
        row for row in review_rows
        if row.get("position_status") == "CANDIDATE_NOT_HELD"
    ]

    lines = [
        "## 5. Risk Notes",
        "",
        "This section is informational only.",
        "No automatic buy/sell decision is made.",
        "",
        f"- Held but not candidate count: {len(held_not_candidate)}",
        f"- Candidate but not held count: {len(candidate_not_held)}",
        "",
        "Manual interpretation:",
        "",
        "- Held but not candidate: check whether the position still matches current trend logic.",
        "- Candidate but not held: check whether it deserves watchlist status, not immediate entry.",
        "- Held and candidate: check whether it deserves continued hold, add, or no action.",
    ]

    return "\n".join(lines)


def build_manual_action_checklist() -> str:
    return """## 6. Manual Action Checklist

- [ ] Check whether market condition supports new entries
- [ ] Review Held and Candidate names
- [ ] Review Held but Not Candidate names
- [ ] Review Candidate but Not Held names
- [ ] Confirm no ticker-name mismatch
- [ ] Confirm no direct execution is triggered by this report
- [ ] Write manual decision notes before any trade
"""


def generate_daily_decision_dashboard(
    holdings_path=DEFAULT_HOLDINGS_PATH,
    candidate_path=None,
    report_path=DEFAULT_REPORT_PATH,
) -> Path:
    holdings_path, holdings_data, holdings = load_holdings(holdings_path)
    candidate_path, candidates = load_candidates(candidate_path)

    review_rows = build_review_rows(holdings=holdings, candidates=candidates)

    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        f"# Daily Decision Dashboard v0 — {datetime.now().strftime('%Y-%m-%d')}",
        "",
        "## Source",
        "",
        f"- Holdings file: `{holdings_path}`",
        f"- Candidate file: `{candidate_path}`",
        f"- Holdings as_of: `{holdings_data.get('as_of', '-')}`",
        "",
        "## Purpose",
        "",
        "This dashboard summarizes current candidates and current holdings for human review.",
        "It does not execute trades and does not change any strategy logic.",
        "",
        build_market_state_section(candidates),
        "",
        build_top_candidates_section(candidates),
        "",
        build_current_holdings_section(holdings_data, holdings),
        "",
        build_portfolio_candidate_sections(review_rows),
        "",
        build_risk_notes_section(review_rows),
        "",
        build_manual_action_checklist(),
    ]

    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def main():
    candidate_path, _ = load_candidates()
    report_path = generate_daily_decision_dashboard(candidate_path=candidate_path)

    print(f"Candidate source: {candidate_path}")
    print(f"Daily decision dashboard written to: {report_path}")


if __name__ == "__main__":
    main()
