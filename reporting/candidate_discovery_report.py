# reporting/candidate_discovery_report.py
"""
Generates reports/discovery/YYYY-MM-DD_candidate_discovery_report.md
from the discovery pool list produced by discovery_pool_builder.
"""
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = PROJECT_ROOT / "reports" / "discovery"


def _fmt_weight(w) -> str:
    if w is None:
        return "-"
    try:
        return f"{float(w)*100:.1f}%"
    except (TypeError, ValueError):
        return str(w)


def _fmt_price(v) -> str:
    if v is None or v == "DATA_MISSING":
        return "DATA_MISSING"
    try:
        return f"{float(v):.2f}"
    except (TypeError, ValueError):
        return "DATA_MISSING"


def _fmt_pct(v) -> str:
    if v is None or v == "DATA_MISSING":
        return "DATA_MISSING"
    try:
        return f"{float(v):+.2f}%"
    except (TypeError, ValueError):
        return "DATA_MISSING"


def _table_row(r: dict) -> str:
    return (
        f"| {r.get('industry', '-')} "
        f"| {r.get('ticker', '-')} "
        f"| {r.get('name', '-')} "
        f"| {_fmt_price(r.get('close'))} "
        f"| {_fmt_pct(r.get('pct_change'))} "
        f"| {r.get('source_ticker_or_etf', '-')} "
        f"| {_fmt_weight(r.get('source_weight'))} "
        f"| {r.get('note', '')} |"
    )


_TABLE_HEADER = (
    "| 產業 | 代號 | 名稱 | 本日收盤價 | 漲幅 | ETF來源 | 持股比例 | note |\n"
    "|---|---|---|---:|---|---:|---|---|"
)


def _filter_by_status(pool: list, status: str) -> list:
    return [r for r in pool if r.get("discovery_status") == status]


def generate_report(pool: list,
                    summary: dict,
                    gate_log: list,
                    run_date: str | None = None,
                    write_file: bool = True) -> str:
    """
    Generate markdown report text. Optionally write to file.
    Returns the markdown string.
    """
    if run_date is None:
        run_date = datetime.now().strftime("%Y-%m-%d")

    existing = _filter_by_status(pool, "EXISTING_UNIVERSE_REINFORCED")
    new_disc = _filter_by_status(pool, "NEW_DISCOVERY_CANDIDATE")
    conflicts = _filter_by_status(pool, "SOURCE_CONFLICT_REVIEW")
    theme_map = _filter_by_status(pool, "THEME_MAPPING_ONLY")
    rejected = _filter_by_status(pool, "REJECT_BAD_TICKER")
    ignored = _filter_by_status(pool, "IGNORE_LOW_RELEVANCE")

    missing_sources = [l for l in gate_log if "not found" in l or "skipping" in l or "MISSING" in l]
    conflict_logs = [l for l in gate_log if "NAME_MISMATCH" in l or "SOURCE_CONFLICT" in l]

    lines = [
        f"# Candidate Discovery Report — {run_date}",
        "",
        "## 1. Executive Summary",
        "",
        f"- Run date: `{run_date}`",
        f"- Total pool records: **{len(pool)}**",
        f"- Existing universe reinforced: **{len(existing)}**",
        f"- New discovery candidates: **{len(new_disc)}**",
        f"- Source conflict review: **{len(conflicts)}**",
        f"- Theme mapping only (US): **{len(theme_map)}**",
        f"- Ignored (low relevance): **{len(ignored)}**",
        f"- Rejected (bad ticker): **{len(rejected)}**",
        "",
        "> Discovery Score does NOT override P1 Entry Audit. Candidates require Owner Review before universe promotion.",
        "",
    ]

    lines += [
        "## 2. Existing Universe Reinforced",
        "",
        _TABLE_HEADER,
    ]
    for r in existing:
        lines.append(_table_row(r))
    if not existing:
        lines.append("_(none)_")
    lines.append("")

    lines += [
        "## 3. New Discovery Candidates",
        "",
        _TABLE_HEADER,
    ]
    for r in new_disc:
        lines.append(_table_row(r))
    if not new_disc:
        lines.append("_(none)_")
    lines.append("")

    lines += [
        "## 4. Source Conflict Review",
        "",
        _TABLE_HEADER,
    ]
    for r in conflicts:
        lines.append(_table_row(r))
    if not conflicts:
        lines.append("_(none)_")
    lines.append("")

    lines += [
        "## 5. Theme Mapping Only (US Symbols)",
        "",
        "These are US symbols. They must not be mixed into TW ranking.",
        "",
        _TABLE_HEADER,
    ]
    for r in theme_map:
        lines.append(_table_row(r))
    if not theme_map:
        lines.append("_(none)_")
    lines.append("")

    lines += [
        "## 6. Data Quality Gate Findings",
        "",
        f"- Gate log entries: {len(gate_log)}",
        f"- Missing sources: {len(missing_sources)}",
        f"- Conflict flags: {len(conflict_logs)}",
        f"- Rejected tickers: {len(rejected)}",
        "",
    ]
    if gate_log:
        lines.append("```")
        for entry in gate_log[:30]:
            lines.append(entry)
        if len(gate_log) > 30:
            lines.append(f"... ({len(gate_log) - 30} more)")
        lines.append("```")
    lines.append("")

    lines += [
        "## 7. Owner Review List",
        "",
        "Candidates recommended for universe promotion review:",
        "",
        _TABLE_HEADER,
    ]
    review_list = [r for r in new_disc if r.get("recommended_action") == "REVIEW_FOR_UNIVERSE_ADD"]
    for r in review_list:
        lines.append(_table_row(r))
    if not review_list:
        lines.append("_(none)_")
    lines.append("")
    lines.append(f"_Generated by Investment OS candidate_discovery_report.py — {run_date}_")

    text = "\n".join(lines)

    if write_file:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        report_path = REPORT_DIR / f"{run_date}_candidate_discovery_report.md"
        report_path.write_text(text, encoding="utf-8")

    return text
