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


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_HOLDINGS_PATH = PROJECT_ROOT / "data" / "portfolio" / "current_holdings.json"

DEFAULT_CANDIDATE_PATHS = [
    PROJECT_ROOT / "data" / "candidates.json",
    PROJECT_ROOT / "data" / "decision.json",
    PROJECT_ROOT / "data" / "candidates_smoke_test.json",
]

DEFAULT_REPORT_PATH = (
    PROJECT_ROOT
    / "docs"
    / f"PORTFOLIO_CANDIDATE_REVIEW_{datetime.now().strftime('%Y%m%d')}.md"
)


def _load_json(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def find_existing_candidate_file(paths=None) -> Path:
    paths = paths or DEFAULT_CANDIDATE_PATHS

    for path in paths:
        if path.exists():
            return path

    checked = "\n".join(str(p) for p in paths)
    raise FileNotFoundError(f"No candidate file found. Checked:\n{checked}")


def normalize_candidates(raw_data) -> list:
    """
    Normalize possible candidate output formats into a list of dicts.

    Supported shapes:
    1. list[dict]
    2. {"candidates": list[dict]}
    3. {"top_candidates": list[dict]}
    4. {"results": list[dict]}
    5. {"data": list[dict]}
    """

    if isinstance(raw_data, list):
        return raw_data

    if isinstance(raw_data, dict):
        for key in ["candidates", "top_candidates", "results", "data"]:
            value = raw_data.get(key)
            if isinstance(value, list):
                return value

    raise ValueError("Unsupported candidate data format")


def build_review_rows(holdings: list, candidates: list) -> list:
    holdings_by_base = {
        normalize_ticker(item.get("ticker")): item
        for item in holdings
        if item.get("ticker")
    }

    candidates_by_base = {
        normalize_ticker(item.get("ticker")): item
        for item in candidates
        if item.get("ticker")
    }

    all_tickers = sorted(set(holdings_by_base.keys()) | set(candidates_by_base.keys()))

    ticker_master = load_ticker_master()
    rows = []

    for base_ticker in all_tickers:
        holding = holdings_by_base.get(base_ticker)
        candidate = candidates_by_base.get(base_ticker)

        is_held = holding is not None
        is_candidate = candidate is not None

        if is_held and is_candidate:
            position_status = "HELD_AND_CANDIDATE"
            review_note = "Already held and also selected by scanner."
        elif is_held and not is_candidate:
            position_status = "HELD_NOT_CANDIDATE"
            review_note = "Currently held but not selected by scanner."
        elif not is_held and is_candidate:
            position_status = "CANDIDATE_NOT_HELD"
            review_note = "Scanner candidate but not currently held."
        else:
            position_status = "UNKNOWN"
            review_note = "Unexpected comparison state."

        fallback_name = (
            holding.get("name") if holding and holding.get("name")
            else candidate.get("name", None) if candidate
            else None
        )
        canonical_name = resolve_canonical_name(
            base_ticker,
            fallback_name=fallback_name,
            master=ticker_master,
        )
        asset_type = resolve_asset_type(
            base_ticker,
            fallback_asset_type=holding.get("asset_type") if holding else None,
            master=ticker_master,
        )

        raw_score = candidate.get("score", "-") if candidate else "-"
        raw_level = candidate.get("level", "-") if candidate else "-"
        scanner_score = candidate.get("scanner_score", raw_score) if candidate else "-"
        signal = candidate.get("signal", raw_level) if candidate else "-"

        row = {
            "ticker": base_ticker,
            "holding_ticker": holding.get("ticker") if holding else "-",
            "candidate_ticker": candidate.get("ticker") if candidate else "-",
            "name": canonical_name,
            "candidate_raw_name": candidate.get("name", "-") if candidate else "-",
            "shares": holding.get("shares", 0) if holding else 0,
            "asset_type": asset_type,
            "is_held": is_held,
            "is_candidate": is_candidate,
            "scanner_score": scanner_score,
            "signal": signal,
            "volume_ratio": candidate.get("volume_ratio", "-") if candidate else "-",
            "breakout_20d": candidate.get("breakout_20d", "-") if candidate else "-",
            "blocked_reason": candidate.get("blocked_reason", "-") if candidate else "-",
            "position_status": position_status,
            "review_note": review_note,
        }

        rows.append(row)

    return rows


def build_summary(rows: list) -> str:
    total = len(rows)

    status_counts = {}
    for row in rows:
        status = row.get("position_status", "UNKNOWN")
        status_counts[status] = status_counts.get(status, 0) + 1

    lines = [
        "## Summary",
        "",
        f"- Total compared tickers: {total}",
        "",
        "### Position Status Counts",
        "",
    ]

    for status, count in sorted(status_counts.items()):
        lines.append(f"- {status}: {count}")

    return "\n".join(lines)


def build_markdown_table(rows: list) -> str:
    headers = [
        "ticker",
        "name",
        "shares",
        "asset_type",
        "is_held",
        "is_candidate",
        "scanner_score",
        "signal",
        "volume_ratio",
        "breakout_20d",
        "blocked_reason",
        "position_status",
        "review_note",
    ]

    lines = []
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

    for row in rows:
        values = []
        for field in headers:
            value = row.get(field, "-")
            if value is None:
                value = "-"
            value = str(value).replace("|", "/")
            values.append(value)

        lines.append("| " + " | ".join(values) + " |")

    return "\n".join(lines)


def build_action_sections(rows: list) -> str:
    held_not_candidate = [r for r in rows if r.get("position_status") == "HELD_NOT_CANDIDATE"]
    candidate_not_held = [r for r in rows if r.get("position_status") == "CANDIDATE_NOT_HELD"]
    held_and_candidate = [r for r in rows if r.get("position_status") == "HELD_AND_CANDIDATE"]

    lines = [
        "## Review Buckets",
        "",
        "### Held and also candidate",
        "",
    ]

    if held_and_candidate:
        for row in held_and_candidate:
            lines.append(
                f"- {row['ticker']} {row['name']} — shares: {row['shares']}, "
                f"score: {row['scanner_score']}, signal: {row['signal']}"
            )
    else:
        lines.append("- None")

    lines.extend([
        "",
        "### Held but not candidate",
        "",
    ])

    if held_not_candidate:
        for row in held_not_candidate:
            lines.append(
                f"- {row['ticker']} {row['name']} — shares: {row['shares']}; "
                "review whether position still matches trend logic."
            )
    else:
        lines.append("- None")

    lines.extend([
        "",
        "### Candidate but not held",
        "",
    ])

    if candidate_not_held:
        for row in candidate_not_held:
            lines.append(
                f"- {row['ticker']} {row['name']} — score: {row['scanner_score']}, "
                f"signal: {row['signal']}; review for watchlist or future entry."
            )
    else:
        lines.append("- None")

    return "\n".join(lines)


def generate_portfolio_candidate_review(
    holdings_path=DEFAULT_HOLDINGS_PATH,
    candidate_path=None,
    report_path=DEFAULT_REPORT_PATH,
) -> Path:
    holdings_data = load_current_holdings(holdings_path)
    holdings = holdings_data["holdings"]

    if candidate_path is None:
        candidate_path = find_existing_candidate_file()
    else:
        candidate_path = Path(candidate_path)

    raw_candidates = _load_json(candidate_path)
    candidates = normalize_candidates(raw_candidates)

    rows = build_review_rows(holdings=holdings, candidates=candidates)

    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        f"# Portfolio vs Candidate Review — {datetime.now().strftime('%Y-%m-%d')}",
        "",
        "## Source",
        "",
        f"- Holdings file: `{holdings_path}`",
        f"- Candidate file: `{candidate_path}`",
        f"- Holdings as_of: `{holdings_data.get('as_of', '-')}`",
        "",
        build_summary(rows),
        "",
        build_action_sections(rows),
        "",
        "## Full Comparison Table",
        "",
        build_markdown_table(rows),
        "",
        "## Human Review Checklist",
        "",
        "- [ ] Held and candidate names are aligned",
        "- [ ] Held but not candidate positions are reviewed",
        "- [ ] Candidate but not held names are reviewed",
        "- [ ] No execution decision is made directly from this report",
        "",
    ]

    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def main():
    candidate_path = find_existing_candidate_file()
    report_path = generate_portfolio_candidate_review(candidate_path=candidate_path)

    print(f"Candidate source: {candidate_path}")
    print(f"Portfolio candidate review written to: {report_path}")


if __name__ == "__main__":
    main()
