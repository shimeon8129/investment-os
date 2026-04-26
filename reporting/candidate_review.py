from pathlib import Path
import json
from datetime import datetime

from metadata.ticker_master import (
    load_ticker_master,
    normalize_ticker,
    resolve_canonical_name,
    resolve_asset_type,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CANDIDATES_PATHS = [
    PROJECT_ROOT / "data" / "candidates.json",
    PROJECT_ROOT / "data" / "decision.json",
    PROJECT_ROOT / "data" / "candidates_smoke_test.json",
]
DEFAULT_REPORT_PATH = PROJECT_ROOT / "docs" / f"CANDIDATE_REVIEW_{datetime.now().strftime('%Y%m%d')}.md"


REVIEW_FIELDS = [
    "ticker",
    "name",
    "asset_type",
    "close",
    "scanner_score",
    "signal",
    "raw_score",
    "raw_level",
    "raw_price",
    "ma20",
    "ma60",
    "ma120",
    "volume_ratio",
    "breakout_20d",
    "market_lock",
    "position_lock",
    "risk_lock",
    "final_status",
    "blocked_reason",
]


def _load_json_file(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def find_existing_candidates_file(paths: list | None = None) -> Path:
    paths = paths or DEFAULT_CANDIDATES_PATHS

    for path in paths:
        if path.exists():
            return path

    checked = "\n".join(str(p) for p in paths)
    raise FileNotFoundError(f"No candidate file found. Checked:\n{checked}")


def adapt_candidate_schema(row: dict, ticker_master: dict | None = None) -> dict:
    """
    Normalize a single candidate row to the review schema.

    Maps pipeline-native fields to review fields:
      score  -> scanner_score
      level  -> signal
      price  -> close

    Preserves raw values and resolves canonical name from ticker master.
    """
    ticker = row.get("ticker", row.get("symbol", "-"))
    base_ticker = normalize_ticker(ticker)

    raw_score = row.get("score")
    raw_level = row.get("level")
    raw_price = row.get("price")

    scanner_score = row.get("scanner_score", raw_score)
    signal = row.get("signal", raw_level)
    close = row.get("close", raw_price)

    fallback_name = row.get("name")
    canonical_name = resolve_canonical_name(
        base_ticker,
        fallback_name=fallback_name,
        master=ticker_master,
    )

    asset_type = resolve_asset_type(
        base_ticker,
        fallback_asset_type=row.get("asset_type"),
        master=ticker_master,
    )

    return {
        **row,
        "ticker": base_ticker,
        "name": canonical_name,
        "asset_type": asset_type,
        "close": close,
        "scanner_score": scanner_score,
        "signal": signal,
        "raw_score": raw_score,
        "raw_level": raw_level,
        "raw_price": raw_price,
    }


def normalize_candidates(raw_data) -> list:
    """
    Normalize possible candidate output formats into a list of dicts.

    Supported shapes:
    1. list[dict]
    2. {"candidates": list[dict]}
    3. {"top_candidates": list[dict]}
    4. {"results": list[dict]}
    """

    if isinstance(raw_data, list):
        rows = raw_data
    elif isinstance(raw_data, dict):
        rows = None
        for key in ["candidates", "top_candidates", "results", "data"]:
            value = raw_data.get(key)
            if isinstance(value, list):
                rows = value
                break
        if rows is None:
            raise ValueError("Unsupported candidate data format")
    else:
        raise ValueError("Unsupported candidate data format")

    ticker_master = load_ticker_master()
    return [adapt_candidate_schema(row, ticker_master=ticker_master) for row in rows]


def safe_get(row: dict, key: str, default="-"):
    value = row.get(key, default)

    if value is None:
        return default

    if isinstance(value, float):
        return round(value, 4)

    return value


def build_markdown_table(candidates: list) -> str:
    headers = REVIEW_FIELDS
    lines = []

    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

    for row in candidates:
        values = [str(safe_get(row, field)) for field in headers]
        values = [v.replace("|", "/") for v in values]
        lines.append("| " + " | ".join(values) + " |")

    return "\n".join(lines)


def build_candidate_summary(candidates: list) -> str:
    total = len(candidates)

    signal_counts = {}
    for row in candidates:
        signal = str(row.get("signal", "UNKNOWN"))
        signal_counts[signal] = signal_counts.get(signal, 0) + 1

    score_values = [
        row.get("scanner_score")
        for row in candidates
        if isinstance(row.get("scanner_score"), (int, float))
    ]

    max_score = max(score_values) if score_values else "-"
    min_score = min(score_values) if score_values else "-"

    lines = [
        "## Summary",
        "",
        f"- Candidate count: {total}",
        f"- Max scanner_score: {max_score}",
        f"- Min scanner_score: {min_score}",
        "",
        "### Signal Counts",
        "",
    ]

    if signal_counts:
        for signal, count in sorted(signal_counts.items()):
            lines.append(f"- {signal}: {count}")
    else:
        lines.append("- No signal field found")

    return "\n".join(lines)


def build_top_candidate_notes(candidates: list, top_n: int = 10) -> str:
    lines = [
        "## Top Candidate Notes",
        "",
        "This section is for human review only. It does not change scoring logic.",
        "",
    ]

    for idx, row in enumerate(candidates[:top_n], start=1):
        ticker = safe_get(row, "ticker")
        name = safe_get(row, "name")
        score = safe_get(row, "scanner_score")
        signal = safe_get(row, "signal")
        volume_ratio = safe_get(row, "volume_ratio")
        breakout_20d = safe_get(row, "breakout_20d")
        blocked_reason = safe_get(row, "blocked_reason")

        lines.extend([
            f"### {idx}. {ticker} {name}",
            "",
            f"- scanner_score: {score}",
            f"- signal: {signal}",
            f"- volume_ratio: {volume_ratio}",
            f"- breakout_20d: {breakout_20d}",
            f"- blocked_reason: {blocked_reason}",
            "",
            "Human review:",
            "",
            "- [ ] Does this candidate match swing trading logic?",
            "- [ ] Is the signal caused by real market strength or by stub / smoke-test data?",
            "- [ ] Should this ticker remain in the watchlist?",
            "",
        ])

    return "\n".join(lines)


def generate_candidate_review_report(
    candidates_path=None,
    report_path=DEFAULT_REPORT_PATH,
) -> Path:
    if candidates_path is None:
        candidates_path = find_existing_candidates_file()
    else:
        candidates_path = Path(candidates_path)

    report_path = Path(report_path)

    raw_data = _load_json_file(candidates_path)
    candidates = normalize_candidates(raw_data)

    report_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        f"# Candidate Review Report — {datetime.now().strftime('%Y-%m-%d')}",
        "",
        "## Source",
        "",
        f"- Candidate file: `{candidates_path}`",
        "",
        build_candidate_summary(candidates),
        "",
        "## Candidate Review Table",
        "",
        build_markdown_table(candidates),
        "",
        build_top_candidate_notes(candidates),
        "",
        "## Review Conclusion",
        "",
        "- [ ] Candidate output is explainable",
        "- [ ] Candidate output matches swing trading logic",
        "- [ ] Scanner score should remain unchanged",
        "- [ ] Scanner score needs future review",
        "",
    ]

    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def main():
    candidates_path = find_existing_candidates_file()
    report_path = generate_candidate_review_report(candidates_path=candidates_path)

    print(f"Candidate source: {candidates_path}")
    print(f"Candidate review report written to: {report_path}")


if __name__ == "__main__":
    main()
