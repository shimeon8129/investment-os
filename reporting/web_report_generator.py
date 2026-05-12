#!/usr/bin/env python3
"""Investment OS — Web Status Dashboard generator."""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB_DIR = ROOT / "reports" / "web"
SIGNAL_SNAPSHOT = ROOT / "data" / "processed" / "signal_snapshot.json"
MAINLINE_SNAPSHOT = ROOT / "data" / "processed" / "mainline_snapshot.json"
ROLE_MAP_FILE = ROOT / "data" / "portfolio" / "role_map.json"
OBSERVATION_DIR = ROOT / "reports" / "observation"
DAILY_REPORT_DIR = ROOT / "reports" / "daily"
INTRADAY_DAILY_DIR = ROOT / "data" / "observations" / "daily"
INTRADAY_SLOT_DIR = ROOT / "data" / "observations" / "intraday"

_CSS = """
body{font-family:monospace;background:#1a1a1a;color:#d4d4d4;margin:0;padding:0}
nav{background:#2a2a2a;padding:10px 20px;border-bottom:1px solid #444;display:flex;align-items:center;gap:20px;flex-wrap:wrap}
.brand{font-weight:bold;color:#fff;margin-right:10px}
nav a{color:#aaa;text-decoration:none}
nav a.active{color:#fff;border-bottom:2px solid #5af}
nav a:hover{color:#fff}
.ts{margin-left:auto;color:#666;font-size:.85em}
main{padding:20px;max-width:960px}
h1{color:#ccc;margin-bottom:4px}
h2{color:#aaa;border-bottom:1px solid #333;padding-bottom:4px;margin-top:24px}
table{border-collapse:collapse;width:100%;margin-bottom:16px}
th{text-align:left;color:#888;border-bottom:1px solid #333;padding:4px 8px}
td{padding:4px 8px;border-bottom:1px solid #222}
.badge{padding:2px 8px;border-radius:3px;font-size:.85em}
.green{background:#1a3d1a;color:#5f5}
.red{background:#3d1a1a;color:#f55}
.orange{background:#3d2a00;color:#fa5}
.grey{background:#2a2a2a;color:#888}
details>summary{cursor:pointer;color:#aaa;padding:4px 8px}
details[open]{background:#222;padding:8px;margin-bottom:8px}
.banner{background:#2a2a2a;color:#888;padding:20px;text-align:center;margin:20px 0;border:1px solid #333}
select{background:#2a2a2a;color:#d4d4d4;border:1px solid #444;padding:4px 8px}
"""


def _load_role_index() -> dict:
    data = _load_json(ROLE_MAP_FILE)
    if not data:
        return {}
    return {e["ticker"]: e for e in data.get("entries", []) if e.get("ticker")}


def _role_badge(role: str) -> str:
    color = {
        "CORE": "green", "CORE_ETF": "green",
        "SATELLITE": "orange", "WAVE_SWING": "orange",
        "UNKNOWN": "grey",
    }.get((role or "").upper(), "grey")
    return f'<span class="badge {color}">{role or "—"}</span>'


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _nav_bar(active: str) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    pages = [("status", "status.html", "今日狀態"),
             ("history", "history.html", "歷史記錄"),
             ("replay", "replay.html", "Replay")]
    links = ""
    for key, href, label in pages:
        cls = ' class="active"' if key == active else ""
        links += f'<a href="{href}"{cls}>{label}</a> '
    return f'<nav><span class="brand">Investment OS</span>{links}<span class="ts">最後更新: {now}</span></nav>'


def _badge(status: str) -> str:
    s = (status or "").upper()
    color = {"PASS": "green", "FAIL": "red", "WARN": "orange",
             "SKIPPED": "grey", "SKIP": "grey", "UNKNOWN": "grey"}.get(s, "grey")
    return f'<span class="badge {color}">{status}</span>'


def _html_page(title: str, active: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="zh-TW">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — Investment OS</title>
<style>{_CSS}</style>
</head>
<body>
{_nav_bar(active)}
<main>{body}</main>
</body>
</html>"""


def generate_status_page(
    web_dir: Path = WEB_DIR,
    signal: dict | None = None,
    mainline: dict | None = None,
) -> None:
    web_dir.mkdir(parents=True, exist_ok=True)
    if signal is None:
        signal = _load_json(SIGNAL_SNAPSHOT)
    if mainline is None:
        mainline = _load_json(MAINLINE_SNAPSHOT)

    status = signal.get("status", "UNKNOWN")
    generated_at = signal.get("generated_at", "N/A")
    data_mode = signal.get("data_mode", "N/A")
    market_status = signal.get("market_status", "UNKNOWN")
    market_closed = market_status in ("CLOSED_WEEKEND", "CLOSED_HOLIDAY", "MARKET_CLOSED")

    markets = (signal.get("market_context") or {}).get("markets", {})
    tw_s = (markets.get("TW") or {}).get("status", "N/A")
    us_s = (markets.get("US") or {}).get("status", "N/A")

    m_state = mainline.get("market_state", "N/A")
    m_score = mainline.get("market_score", "N/A")
    vix = mainline.get("vix_value", "N/A")
    if isinstance(vix, float):
        vix = f"{vix:.2f}"

    ranked = mainline.get("ranked", [])
    decisions = mainline.get("decisions", {})
    checks = signal.get("checks", [])
    role_summary = signal.get("role_summary", {})
    role_index = _load_role_index()

    body = f"<h1>今日狀態 {_badge(status)}</h1>"
    body += f"<p>執行時間: {generated_at} &nbsp;|&nbsp; 模式: {data_mode}</p>"

    # Role Map Status block
    rs_loaded = role_summary.get("loaded", False)
    rs_count = role_summary.get("ticker_count", 0)
    rs_warn = role_summary.get("warning") or ""
    rs_badge = _badge("PASS") if rs_loaded else _badge("WARN")
    body += "<h2>Role Map 狀態</h2>"
    body += (f"<table><tr><th>role_map 載入</th><th>Ticker 數</th><th>警告</th></tr>"
             f"<tr><td>{rs_badge}</td><td>{rs_count}</td>"
             f"<td style='color:#fa5'>{rs_warn if rs_warn else '—'}</td></tr></table>")

    if market_closed:
        body += f'<div class="banner">市場休市 ({tw_s})</div>'
    else:
        body += "<h2>市場概況</h2>"
        body += ("<table><tr><th>市場狀態</th><th>Score</th><th>VIX</th>"
                 "<th>TW</th><th>US</th></tr>"
                 f"<tr><td>{m_state}</td><td>{m_score}</td><td>{vix}</td>"
                 f"<td>{tw_s}</td><td>{us_s}</td></tr></table>")

        body += "<h2>Top 候選</h2>"
        body += ("<table><tr><th>Rank</th><th>Ticker</th><th>Name</th>"
                 "<th>Score</th><th>Signal</th>"
                 "<th>base_role</th><th>active_role</th><th>role_conf</th><th>intent</th></tr>")
        for i, r in enumerate(ranked[:10], 1):
            ticker = r.get("ticker", "")
            re_entry = role_index.get(ticker, {})
            base_role = re_entry.get("base_role", "UNKNOWN")
            active_role = re_entry.get("active_role", "UNKNOWN")
            role_conf = re_entry.get("role_confidence", "UNKNOWN")
            intent = re_entry.get("intent") or "—"
            body += (f"<tr><td>{i}</td><td>{ticker}</td>"
                     f"<td>{r.get('name','')}</td><td>{r.get('score','')}</td>"
                     f"<td>{r.get('signal','')}</td>"
                     f"<td>{_role_badge(base_role)}</td><td>{_role_badge(active_role)}</td>"
                     f"<td>{role_conf}</td><td>{intent}</td></tr>")
        body += "</table>"

        if decisions:
            ranked_name_map = {r.get("ticker", ""): r.get("name", "") for r in ranked}
            body += "<h2>Decisions</h2>"
            body += "<table><tr><th>Ticker</th><th>Name</th><th>Action</th><th>Position</th><th>Reason</th></tr>"
            for ticker, d in decisions.items():
                pct = f"{d.get('position_size', 0)*100:.0f}%" if d.get('position_size') else "N/A"
                name = ranked_name_map.get(ticker) or role_index.get(ticker, {}).get("name", "—")
                body += (f"<tr><td>{ticker}</td><td>{name}</td><td>{d.get('action','')}</td>"
                         f"<td>{pct}</td><td>{d.get('reason','')}</td></tr>")
            body += "</table>"

    body += "<h2>Pipeline 子程序</h2>"
    body += "<table><tr><th>子程序</th><th>狀態</th></tr>"
    for c in checks:
        body += f"<tr><td>{c.get('label','')}</td><td>{_badge(c.get('status','UNKNOWN'))}</td></tr>"
    body += "</table>"

    (web_dir / "status.html").write_text(_html_page("今日狀態", "status", body), encoding="utf-8")


def _parse_obs_summary(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    date = re.search(r"Observation Summary - (\d{4}-\d{2}-\d{2})", text)
    status = re.search(r"## Final Status\s+(\w+)", text)
    stable_type = re.search(r"- Type: (.+)", text)
    generated = re.search(r"\*Generated at: (.+)\*", text)
    subproc_lines = re.findall(r"- (\w[\w_]+): (PASS|FAIL|UNKNOWN|SKIPPED[^)]*)", text)
    return {
        "date": date.group(1) if date else path.stem[:10],
        "status": status.group(1) if status else "UNKNOWN",
        "stable_type": stable_type.group(1).strip() if stable_type else "N/A",
        "generated_at": generated.group(1).strip() if generated else "N/A",
        "subproc": subproc_lines,
    }


def _parse_daily_report(path: Path) -> dict:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    market = re.search(r"Market state: \*\*(\w+)\*\*", text)
    score = re.search(r"Score: ([\d.]+)", text)
    vix = re.search(r"VIX: ([\d.]+)", text)
    top1 = re.search(r"1\. (\S+) (.+?) —", text)
    return {
        "market_state": market.group(1) if market else "N/A",
        "score": score.group(1) if score else "N/A",
        "vix": vix.group(1) if vix else "N/A",
        "top1": f"{top1.group(1)} {top1.group(2)}" if top1 else "N/A",
    }


def generate_history_page(
    web_dir: Path = WEB_DIR,
    obs_dir: Path = OBSERVATION_DIR,
    daily_dir: Path = DAILY_REPORT_DIR,
) -> None:
    web_dir.mkdir(parents=True, exist_ok=True)

    obs_files = sorted(obs_dir.glob("*_observation_summary.md"), reverse=True)

    body = "<h1>歷史觀測記錄</h1>"

    if not obs_files:
        body += '<div class="banner">尚無資料</div>'
        (web_dir / "history.html").write_text(_html_page("歷史記錄", "history", body), encoding="utf-8")
        return

    body += ("<table><tr><th>日期</th><th>狀態</th><th>市場狀態</th>"
             "<th>Score</th><th>VIX</th><th>Top 1 候選</th><th>觀測類型</th><th>Role-Aware</th></tr>")

    for obs_path in obs_files:
        obs = _parse_obs_summary(obs_path)
        date = obs["date"]
        daily_path = daily_dir / f"{date}_daily_report.md"
        daily = _parse_daily_report(daily_path)

        role_aware = "—"
        if daily_path.exists():
            text = daily_path.read_text(encoding="utf-8")
            role_aware = _badge("PASS") if "Role-Aware Candidate Summary" in text else _badge("WARN")

        detail = ""
        if obs["subproc"]:
            rows = "".join(
                f"<tr><td>{lbl}</td><td>{_badge(st)}</td></tr>"
                for lbl, st in obs["subproc"]
            )
            detail = (f"<details><summary>子程序詳情</summary>"
                      f"<table>{rows}</table></details>")

        body += (f"<tr><td>{date}</td><td>{_badge(obs['status'])}</td>"
                 f"<td>{daily.get('market_state','N/A')}</td>"
                 f"<td>{daily.get('score','N/A')}</td>"
                 f"<td>{daily.get('vix','N/A')}</td>"
                 f"<td>{daily.get('top1','N/A')}</td>"
                 f"<td>{obs['stable_type']}{detail}</td>"
                 f"<td>{role_aware}</td></tr>")
    body += "</table>"

    (web_dir / "history.html").write_text(_html_page("歷史記錄", "history", body), encoding="utf-8")


def generate_replay_page(
    web_dir: Path = WEB_DIR,
    daily_obs_dir: Path = INTRADAY_DAILY_DIR,
    slot_dir: Path = INTRADAY_SLOT_DIR,
) -> None:
    web_dir.mkdir(parents=True, exist_ok=True)

    daily_files = sorted(daily_obs_dir.glob("*_observation_summary.json"), reverse=True)

    body = "<h1>Intraday Replay</h1>"

    # Fall back to scanning slot_dir date folders when no daily summaries exist
    if not daily_files:
        slot_date_dirs = sorted(
            [d for d in slot_dir.iterdir() if d.is_dir()], reverse=True
        ) if slot_dir.exists() else []
        if not slot_date_dirs:
            body += '<div class="banner">尚無資料</div>'
            (web_dir / "replay.html").write_text(_html_page("Replay", "replay", body), encoding="utf-8")
            return
        dates = [d.name for d in slot_date_dirs]
        daily_files = []
    else:
        dates = [f.stem.replace("_observation_summary", "") for f in daily_files]
    latest = dates[0]
    options = "".join(
        f'<option value="{d}"{" selected" if d == latest else ""}>{d}</option>'
        for d in dates
    )
    body += (f'<h2>日期選擇</h2><select id="datesel" onchange="showDate(this.value)">'
             f'{options}</select>')

    for date in dates:
        daily_path = daily_obs_dir / f"{date}_observation_summary.json"
        summary = _load_json(daily_path) if daily_path.exists() else {}
        slot_date_dir = slot_dir / date
        slot_files = sorted(slot_date_dir.glob("*.json")) if slot_date_dir.exists() else []

        display = "block" if date == latest else "none"
        section = f'<div id="date-{date}" style="display:{display}">'

        sc = summary.get("status_counts", {})
        total = summary.get("total_slots", 0)
        section += (f"<h2>{date} — {total} slots "
                    f"(PASS:{sc.get('PASS',0)} FAIL:{sc.get('FAIL',0)})</h2>")

        if slot_files:
            role_aware_slots = sum(
                1 for sf in slot_files
                if (_load_json(sf).get("candidates") or [{}])[0].get("role_context")
            )
            pit_badge = _badge("PASS") if role_aware_slots == len(slot_files) else (
                _badge("WARN") if role_aware_slots > 0 else _badge("FAIL")
            )
            section += (f"<p>PIT Role-Aware 狀態: {pit_badge} "
                        f"({role_aware_slots}/{len(slot_files)} slots 含 role_context)</p>")

            section += ("<table><tr><th>Slot</th><th>時間</th><th>Top 1</th>"
                        "<th>Score</th><th>P1 結果</th><th>市場</th>"
                        "<th>active_role</th><th>role_conf</th><th>intent</th></tr>")
            for sf in slot_files:
                sd = _load_json(sf)
                cands = sd.get("candidates", [])
                top = cands[0] if cands else {}
                mkt = (sd.get("market") or {}).get("market_state", "N/A") or "—"
                raw_score = top.get("score")
                score_str = f"{float(raw_score):.2f}" if isinstance(raw_score, (int, float)) else "—"
                p1 = top.get("p1_result") or "—"
                rc = top.get("role_context") or {}
                active_role = rc.get("active_role", "—") or "—"
                role_conf = rc.get("role_confidence", "—") or "—"
                intent = rc.get("intent") or "—"
                section += (f"<tr><td>{sd.get('slot','')}</td>"
                             f"<td>{sd.get('run_time','')}</td>"
                             f"<td>{top.get('ticker','')} {top.get('name','') or ''}</td>"
                             f"<td>{score_str}</td>"
                             f"<td>{p1}</td>"
                             f"<td>{mkt}</td>"
                             f"<td>{_role_badge(active_role)}</td>"
                             f"<td>{role_conf}</td>"
                             f"<td>{intent}</td></tr>")
            section += "</table>"

        persist = summary.get("top_persistence", [])
        if persist:
            # Build name lookup: summary entries first, then scan slot files for backfill gaps
            name_map: dict[str, str] = {}
            for w in summary.get("next_day_watchlist", []):
                if w.get("name"):
                    name_map[w["ticker"]] = w["name"]
            for w in summary.get("warn_l1_l4_pass", []):
                if w.get("name"):
                    name_map.setdefault(w["ticker"], w["name"])
            for sf in slot_files:
                sd = _load_json(sf)
                for c in sd.get("candidates", []):
                    t = c.get("ticker", "")
                    if t and c.get("name") and t not in name_map:
                        name_map[t] = c["name"]

            section += (f"<h2>Persistence Ranking "
                        f"<small style='color:#666;font-size:.8em'>（出現/共{total}個slot）</small></h2>")
            section += "<table><tr><th>Ticker</th><th>名稱</th><th>出現次數</th><th>L0 WARN → L1-L4 PASS</th></tr>"
            warn_tickers = {w["ticker"] for w in summary.get("warn_l1_l4_pass", [])}
            for p in persist[:10]:
                name = name_map.get(p["ticker"], "—")
                warn = "✓" if p["ticker"] in warn_tickers else ""
                section += (f"<tr><td>{p['ticker']}</td><td>{name}</td>"
                             f"<td>{p['appearances']}/{total}</td>"
                             f"<td>{warn}</td></tr>")
            section += "</table>"

        wl = summary.get("next_day_watchlist", [])
        if wl:
            # Build last-seen rank/p1 from slot files for backfill entries
            slot_last: dict[str, dict] = {}
            for sf in sorted(slot_files):
                sd = _load_json(sf)
                for c in sd.get("candidates", []):
                    t = c.get("ticker", "")
                    if t:
                        slot_last[t] = {"rank": c.get("rank"), "p1": c.get("p1_result")}

            section += "<h2>明日 Watchlist</h2>"
            section += ("<table><tr><th>Ticker</th><th>Name</th><th>出現次數</th>"
                        "<th>最後排名</th><th>最後 P1</th><th>備註</th></tr>")
            for w in wl:
                ticker = w.get("ticker", "")
                name = w.get("name") or name_map.get(ticker, "—")
                rank = w.get("last_rank")
                p1 = w.get("last_p1")
                # Fill from slot data if summary is missing
                if rank is None and ticker in slot_last:
                    rank = slot_last[ticker].get("rank")
                if p1 is None and ticker in slot_last:
                    p1 = slot_last[ticker].get("p1")
                note = "backfill only — no mainline data" if w.get("last_rank") is None else ""
                section += (f"<tr><td>{ticker}</td><td>{name}</td>"
                             f"<td>{w.get('appearances','')}/{total}</td>"
                             f"<td>{rank if rank is not None else '—'}</td>"
                             f"<td>{p1 if p1 is not None else '—'}</td>"
                             f"<td style='color:#666;font-size:.85em'>{note}</td></tr>")
            section += "</table>"

        section += "</div>"
        body += section

    body += """<script>
function showDate(d){
  document.querySelectorAll('[id^="date-"]').forEach(el=>el.style.display='none');
  var el=document.getElementById('date-'+d);
  if(el) el.style.display='block';
}
</script>"""

    (web_dir / "replay.html").write_text(_html_page("Replay", "replay", body), encoding="utf-8")


def generate_all(web_dir: Path = WEB_DIR) -> None:
    for fn, kwargs in [
        (generate_status_page, {"web_dir": web_dir}),
        (generate_history_page, {"web_dir": web_dir}),
        (generate_replay_page, {"web_dir": web_dir}),
    ]:
        try:
            fn(**kwargs)
        except Exception as e:
            print(f"[WARN] web_report_generator: {fn.__name__} failed: {e}")
