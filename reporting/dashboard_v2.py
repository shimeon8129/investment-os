#!/usr/bin/env python3
"""Investment OS — 戰情表板 v2 generator (mobile-first)."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB_DIR = ROOT / "reports" / "web"
MAINLINE_SNAPSHOT = ROOT / "data" / "processed" / "mainline_snapshot.json"
SIGNAL_SNAPSHOT = ROOT / "data" / "processed" / "signal_snapshot.json"
CANDIDATES_FILE = ROOT / "data" / "candidates.json"
UNIVERSE_FILE = ROOT / "data" / "universe_tw.csv"

# ─── CSS (mobile-first) ───────────────────────────────────────────────────────

_CSS = """
:root {
  --bg:#0d1117;--card:#161b22;--card2:#1c2128;--border:#30363d;
  --text:#e6edf3;--muted:#8b949e;
  --green:#3fb950;--green-bg:rgba(63,185,80,.13);--green-bd:rgba(63,185,80,.4);
  --red:#f85149;--red-bg:rgba(248,81,73,.13);--red-bd:rgba(248,81,73,.4);
  --yellow:#e3b341;--yellow-bg:rgba(227,179,65,.13);--yellow-bd:rgba(227,179,65,.4);
  --blue:#58a6ff;--blue-bg:rgba(88,166,255,.13);--blue-bd:rgba(88,166,255,.4);
  --purple:#a371f7;--purple-bg:rgba(163,113,247,.13);--purple-bd:rgba(163,113,247,.4);
  --orange:#fb8f44;--orange-bg:rgba(251,143,68,.13);--orange-bd:rgba(251,143,68,.4);
}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
  background:var(--bg);color:var(--text);font-size:15px;-webkit-text-size-adjust:100%}

/* ── TOPBAR ── */
.topbar{
  background:#0d1117;border-bottom:1px solid var(--border);
  padding:10px 16px;
  display:flex;align-items:center;gap:10px;flex-wrap:wrap;
  position:sticky;top:0;z-index:100;
}
.brand{
  font-size:15px;font-weight:800;letter-spacing:.3px;
  background:linear-gradient(135deg,#58a6ff,#a371f7);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
  white-space:nowrap;
}
.topbar nav{display:flex;gap:2px;flex-wrap:wrap}
.topbar nav a{
  color:var(--muted);text-decoration:none;
  padding:6px 10px;border-radius:6px;font-size:13px;
}
.topbar nav a.active{color:var(--text);background:var(--card2)}
.ts{margin-left:auto;color:var(--muted);font-size:11px;white-space:nowrap}

/* ── MARKET BAR ── */
.mktbar{
  background:var(--card2);border-bottom:1px solid var(--border);
  padding:10px 16px;
  display:flex;align-items:center;gap:14px;overflow-x:auto;
  scrollbar-width:none;
}
.mktbar::-webkit-scrollbar{display:none}
.mkt-state{
  font-size:18px;font-weight:800;padding:4px 14px;border-radius:8px;
  white-space:nowrap;flex-shrink:0;
}
.mkt-state.bull{color:var(--green);background:var(--green-bg);border:1px solid var(--green-bd)}
.mkt-state.bear{color:var(--red);background:var(--red-bg);border:1px solid var(--red-bd)}
.mkt-state.range{color:var(--yellow);background:var(--yellow-bg);border:1px solid var(--yellow-bd)}
.mkt-divider{width:1px;height:32px;background:var(--border);flex-shrink:0}
.mkt-item{display:flex;flex-direction:column;align-items:center;flex-shrink:0}
.mkt-item .lbl{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.4px}
.mkt-item .val{font-size:16px;font-weight:700;margin-top:1px}
.val.green{color:var(--green)}.val.red{color:var(--red)}
.val.yellow{color:var(--yellow)}.val.blue{color:var(--blue)}
.val.muted{color:var(--muted)}

/* ── CONTAINER ── */
.container{padding:14px 12px;max-width:700px;margin:0 auto}

/* ── SECTION HEADER ── */
.sec-hdr{
  display:flex;align-items:center;gap:8px;
  margin:20px 0 10px;
}
.sec-hdr h2{font-size:15px;font-weight:700;color:var(--text);white-space:nowrap}
.sec-cnt{
  font-size:11px;font-weight:600;padding:2px 8px;border-radius:20px;
  background:var(--blue-bg);color:var(--blue);border:1px solid var(--blue-bd);
  white-space:nowrap;
}
.sec-line{flex:1;height:1px;background:var(--border)}

/* ── MARKET CARD (collapsible summary) ── */
.mkt-card{
  background:var(--card);border:1px solid var(--border);
  border-radius:12px;padding:14px;margin-bottom:14px;
}
.mkt-card-row{display:flex;gap:10px;flex-wrap:wrap}
.mkt-mini{
  background:var(--card2);border-radius:8px;padding:10px 12px;
  flex:1;min-width:120px;
}
.mkt-mini .label{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.4px}
.mkt-mini .value{font-size:22px;font-weight:800;margin-top:2px}
.mkt-mini .sub{font-size:11px;color:var(--muted);margin-top:2px}
.guidance{
  background:rgba(88,166,255,.07);
  border-left:3px solid var(--blue);border-radius:0 8px 8px 0;
  padding:10px 12px;font-size:13px;line-height:1.6;color:var(--text);
  margin-top:10px;
}

/* ── CANDIDATE CARD ── */
.cand-card{
  background:var(--card);border:1px solid var(--border);
  border-radius:12px;overflow:hidden;
  margin-bottom:10px;
}
.cand-card.buy{border-top:3px solid var(--green)}
.cand-card.caution{border-top:3px solid var(--yellow)}
.cand-card.satellite{border-top:3px solid var(--purple)}
.cand-card.exit{border-top:3px solid var(--red)}

/* card top row */
.card-top{
  padding:12px 14px 8px;
  display:flex;justify-content:space-between;align-items:flex-start;
}
.card-name{font-size:17px;font-weight:800;color:var(--text)}
.card-sub{display:flex;align-items:center;gap:6px;margin-top:3px;flex-wrap:wrap}
.card-ticker{font-size:12px;color:var(--muted);font-family:monospace}
.card-role-badge{
  font-size:10px;font-weight:600;padding:1px 6px;border-radius:20px;
}
.card-role-badge.satellite{
  background:var(--purple-bg);color:var(--purple);border:1px solid var(--purple-bd)
}
.card-right{display:flex;flex-direction:column;align-items:flex-end;gap:4px}
.card-rank{font-size:20px;font-weight:800;color:var(--blue);opacity:.3}
.card-signal{font-size:13px;font-weight:700}
.card-signal.green{color:var(--green)}.card-signal.red{color:var(--red)}
.card-signal.yellow{color:var(--yellow)}

/* score row */
.card-score{padding:0 14px 10px}
.score-hdr{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:5px}
.score-num{font-size:26px;font-weight:800;color:var(--text)}
.score-unit{font-size:12px;color:var(--muted)}
.score-badge{font-size:11px;font-weight:700;padding:2px 9px;border-radius:20px}
.score-badge.strong{background:var(--green-bg);color:var(--green);border:1px solid var(--green-bd)}
.score-badge.moderate{background:var(--yellow-bg);color:var(--yellow);border:1px solid var(--yellow-bd)}
.score-badge.weak{background:var(--red-bg);color:var(--red);border:1px solid var(--red-bd)}
.progress-track{height:5px;background:var(--card2);border-radius:3px;overflow:hidden}
.progress-fill{height:100%;border-radius:3px;
  background:linear-gradient(90deg,var(--blue),var(--purple))}
.progress-fill.green{background:linear-gradient(90deg,#1a7f37,var(--green))}
.progress-fill.yellow{background:linear-gradient(90deg,#8a6200,var(--yellow))}
.score-subs{display:flex;justify-content:space-between;font-size:11px;color:var(--muted);margin-top:3px}

/* price + key metrics row */
.card-metrics{
  padding:8px 14px;border-top:1px solid var(--border);
  display:grid;grid-template-columns:repeat(4,1fr);gap:6px;
}
.metric{display:flex;flex-direction:column;align-items:center;gap:1px;text-align:center}
.metric .ml{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.3px}
.metric .mv{font-size:14px;font-weight:700}
.mv.green{color:var(--green)}.mv.red{color:var(--red)}
.mv.yellow{color:var(--yellow)}.mv.blue{color:var(--blue)}.mv.muted{color:var(--muted)}

/* institutional flow */
.card-inst{
  padding:8px 14px;border-top:1px solid var(--border);
  display:grid;grid-template-columns:repeat(3,1fr);gap:4px;
}
.inst-col{display:flex;flex-direction:column;align-items:center;gap:1px}
.inst-lbl{font-size:10px;color:var(--muted)}
.inst-val{font-size:13px;font-weight:700}
.inst-val.pos{color:var(--green)}.inst-val.neg{color:var(--red)}.inst-val.neu{color:var(--muted)}

/* chips row */
.card-chips{
  padding:8px 14px;border-top:1px solid var(--border);
  display:flex;gap:5px;flex-wrap:wrap;align-items:center;
}
.chip{font-size:11px;font-weight:600;padding:3px 8px;border-radius:20px}
.chip.green{background:var(--green-bg);color:var(--green);border:1px solid var(--green-bd)}
.chip.red{background:var(--red-bg);color:var(--red);border:1px solid var(--red-bd)}
.chip.yellow{background:var(--yellow-bg);color:var(--yellow);border:1px solid var(--yellow-bd)}
.chip.blue{background:var(--blue-bg);color:var(--blue);border:1px solid var(--blue-bd)}
.chip.purple{background:var(--purple-bg);color:var(--purple);border:1px solid var(--purple-bd)}
.chip.grey{background:#21262d;color:var(--muted);border:1px solid var(--border)}
.chip.orange{background:var(--orange-bg);color:var(--orange);border:1px solid var(--orange-bd)}

/* action + invalid */
.card-action{
  padding:8px 14px;border-top:1px solid var(--border);
  font-size:12px;
}
.action-mode{font-size:13px;font-weight:600;color:var(--text);margin-bottom:2px}
.action-note{color:var(--muted)}
.invalid-row{
  margin-top:5px;padding-top:5px;border-top:1px dashed var(--border);
  font-size:11px;color:var(--muted);
}
.invalid-row .il{color:var(--red);font-weight:600;margin-right:3px}

/* ── HOLDINGS TABLE ── */
.hold-wrap{
  background:var(--card);border:1px solid var(--border);border-radius:12px;overflow:hidden;
}
.hold-row{
  display:grid;grid-template-columns:auto 1fr auto;
  align-items:center;gap:8px;
  padding:12px 14px;border-bottom:1px solid var(--border);
}
.hold-row:last-child{border-bottom:none}
.hold-ticker{font-size:14px;font-weight:700;font-family:monospace;color:var(--text)}
.hold-name{font-size:13px;color:var(--muted);margin-top:1px}
.hold-role{font-size:10px;font-weight:600;padding:1px 6px;border-radius:20px}
.hold-role.core{background:var(--green-bg);color:var(--green);border:1px solid var(--green-bd)}
.hold-role.core_etf{background:var(--blue-bg);color:var(--blue);border:1px solid var(--blue-bd)}
.hold-role.satellite{background:var(--yellow-bg);color:var(--yellow);border:1px solid var(--yellow-bd)}
.hold-role.wave_swing{background:var(--purple-bg);color:var(--purple);border:1px solid var(--purple-bd)}
.hold-right{display:flex;flex-direction:column;align-items:flex-end;gap:4px}
.rec{font-size:11px;font-weight:700;padding:3px 9px;border-radius:20px;white-space:nowrap}
.rec.hold_core,.rec.hold_etf{background:var(--blue-bg);color:var(--blue);border:1px solid var(--blue-bd)}
.rec.hold_satellite,.rec.hold{background:var(--yellow-bg);color:var(--yellow);border:1px solid var(--yellow-bd)}
.rec.review_exit,.rec.trim_overextended,.rec.reduce{
  background:var(--orange-bg);color:var(--orange);border:1px solid var(--orange-bd)}
.rec.exit,.rec.watch_trend_damage{
  background:var(--red-bg);color:var(--red);border:1px solid var(--red-bd)}
.rec.other{background:#21262d;color:var(--muted);border:1px solid var(--border)}
.hold-note{font-size:11px;color:var(--muted);text-align:right;max-width:180px}

/* ── EARLY WATCHLIST ── */
.watchlist-grid{
  display:grid;grid-template-columns:repeat(2,1fr);gap:8px;
}
@media(min-width:420px){.watchlist-grid{grid-template-columns:repeat(3,1fr)}}
.wi{
  background:var(--card);border:1px solid var(--border);
  border-radius:8px;padding:10px 12px;
}
.wi-ticker{font-size:13px;font-weight:700;font-family:monospace;color:var(--text)}
.wi-name{font-size:11px;color:var(--muted);margin-top:1px}
.wi-price{font-size:16px;font-weight:700;color:var(--blue);margin-top:4px}
.wi-sector{
  font-size:10px;font-weight:600;padding:1px 5px;border-radius:4px;
  background:var(--purple-bg);color:var(--purple);width:fit-content;margin-top:3px;
}

/* ── SUMMARY STRIP ── */
.sum-strip{
  display:grid;grid-template-columns:repeat(2,1fr);gap:8px;margin-bottom:14px;
}
.sum-card{
  background:var(--card);border:1px solid var(--border);border-radius:10px;
  padding:12px 14px;
}
.sum-label{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.4px}
.sum-val{font-size:26px;font-weight:800;margin-top:2px}
.sum-sub{font-size:11px;color:var(--muted);margin-top:1px}

/* ── CLOSED BANNER ── */
.closed-banner{
  background:var(--yellow-bg);border:1px solid var(--yellow-bd);
  border-radius:8px;padding:9px 14px;margin-bottom:14px;
  font-size:13px;color:var(--yellow);
}

/* ── SECTION NOTE ── */
.sec-note{
  font-size:12px;color:var(--muted);
  background:var(--card2);border-left:3px solid var(--border);
  border-radius:0 6px 6px 0;padding:8px 12px;
  margin-bottom:10px;line-height:1.6;
}
.sec-note strong{color:var(--text)}

/* ── LEGEND ── */
.legend-wrap{
  margin-top:24px;
  border:1px solid var(--border);border-radius:12px;overflow:hidden;
}
.legend-summary{
  padding:12px 16px;cursor:pointer;
  display:flex;align-items:center;justify-content:space-between;
  background:var(--card);font-size:13px;font-weight:600;color:var(--muted);
  user-select:none;list-style:none;
}
.legend-summary::after{content:"▼";font-size:10px}
details[open] .legend-summary::after{content:"▲"}
.legend-body{
  background:var(--card2);padding:14px 16px;
  display:grid;gap:14px;
}
.legend-group{margin-bottom:4px}
.legend-group-title{
  font-size:11px;font-weight:700;text-transform:uppercase;
  letter-spacing:.5px;color:var(--blue);margin-bottom:6px;
}
.legend-item{
  font-size:12px;line-height:1.7;
  display:grid;grid-template-columns:120px 1fr;gap:6px;
  padding:3px 0;border-bottom:1px solid rgba(48,54,61,.5);
}
.legend-item:last-child{border-bottom:none}
.legend-key{font-weight:600;color:var(--text);font-family:monospace}
.legend-val{color:var(--muted)}
@media(max-width:400px){
  .legend-item{grid-template-columns:1fr;gap:1px}
}

/* ── MODULE STATUS ── */
.mod-status-bar{
  display:flex;gap:6px;flex-wrap:wrap;margin-bottom:12px;
}
.mod-pill{
  font-size:11px;font-weight:600;padding:3px 9px;border-radius:20px;
  display:flex;align-items:center;gap:4px;
}
.mod-pill.ok{background:var(--green-bg);color:var(--green);border:1px solid var(--green-bd)}
.mod-pill.warn{background:var(--yellow-bg);color:var(--yellow);border:1px solid var(--yellow-bd)}
.mod-pill.stale{background:var(--red-bg);color:var(--red);border:1px solid var(--red-bd)}
.mod-pill.wip{background:var(--purple-bg);color:var(--purple);border:1px solid var(--purple-bd)}

/* ── HOLD ROW with PnL ── */
.hold-pnl{font-size:12px;font-weight:700;margin-top:2px}
.hold-cost{font-size:10px;color:var(--muted)}

/* ── STALE TAG ── */
.stale-tag{
  font-size:9px;font-weight:600;padding:1px 5px;border-radius:10px;
  background:var(--yellow-bg);color:var(--yellow);border:1px solid var(--yellow-bd);
  vertical-align:middle;margin-left:3px;
}

/* ── DISCLAIMER ── */
.disclaimer{
  margin:16px 0 12px;padding:10px 14px;
  background:var(--card2);border:1px solid var(--border);
  border-radius:8px;font-size:11px;color:var(--muted);text-align:center;
}

/* ── DESKTOP TWEAKS ── */
@media(min-width:700px){
  .container{padding:20px}
  .card-metrics{grid-template-columns:repeat(4,1fr)}
  .watchlist-grid{grid-template-columns:repeat(4,1fr)}
  .sum-strip{grid-template-columns:repeat(4,1fr)}
}
"""

# ─── DATA HELPERS ─────────────────────────────────────────────────────────────

def _load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _load_universe_map() -> dict:
    import csv
    result: dict = {}
    if not UNIVERSE_FILE.exists():
        return result
    try:
        with UNIVERSE_FILE.open(encoding="utf-8") as f:
            for row in csv.DictReader(f):
                t = row.get("ticker", "")
                if t:
                    result[t] = {"name": row.get("name",""), "sector": row.get("sector","")}
    except Exception:
        pass
    return result


def _load_price_map() -> dict:
    """Build ticker→price lookup from candidates.json."""
    raw = _load_json(CANDIDATES_FILE)
    if not isinstance(raw, list):
        return {}
    return {c["ticker"]: c.get("price", 0) for c in raw if c.get("ticker")}


def _narrative_staleness() -> tuple[int, bool]:
    """Returns (days_since_update, is_stale). Stale = older than 3 days."""
    import os
    files = [
        ROOT / "data" / "narrative_raw" / "gemini.json",
        ROOT / "data" / "narrative_raw" / "claude.json",
        ROOT / "data" / "narrative_raw" / "perplexity.json",
    ]
    mtimes = []
    for f in files:
        try:
            mtimes.append(os.path.getmtime(f))
        except OSError:
            pass
    if not mtimes:
        return 999, True
    latest = max(mtimes)
    from datetime import timezone
    days = (datetime.now().timestamp() - latest) / 86400
    return int(days), days > 3


def _load_portfolio_pnl(price_map: dict) -> dict:
    """Returns ticker→{entry_price, shares, pnl_pct, pnl_label, pnl_cls} using portfolio data."""
    portfolio_path = ROOT / "data" / "portfolio" / "current_holdings.json"
    raw = _load_json(portfolio_path)
    if not raw:
        return {}
    result = {}
    for h in raw.get("holdings", []):
        raw_ticker = h.get("ticker", "")
        ticker = raw_ticker + ".TW" if "." not in raw_ticker else raw_ticker
        entry = h.get("entry_price", 0)
        shares = h.get("shares", 0)
        current = price_map.get(ticker, 0)
        if entry and current:
            pnl = (current - entry) / entry * 100
            pnl_label = f"{pnl:+.1f}%"
            pnl_cls = "green" if pnl >= 0 else "red"
        else:
            pnl_label = "—"
            pnl_cls = "muted"
        result[ticker] = {
            "entry_price": entry,
            "shares": shares,
            "current_price": current,
            "pnl_label": pnl_label,
            "pnl_cls": pnl_cls,
        }
    return result


def _load_early_candidates(uni: dict) -> list:
    raw = _load_json(CANDIDATES_FILE)
    if not isinstance(raw, list):
        return []
    result = []
    for c in raw:
        if c.get("score") == 1:
            t = c.get("ticker", "")
            info = uni.get(t, {})
            result.append({
                "ticker": t,
                "name": info.get("name") or t,
                "sector": info.get("sector",""),
                "price": c.get("price", 0),
            })
    # sort by sector then ticker for logical grouping
    result.sort(key=lambda x: (x.get("sector",""), x["ticker"]))
    return result


# ─── RENDERING HELPERS ────────────────────────────────────────────────────────

def _chip(text: str, color: str = "grey") -> str:
    return f'<span class="chip {color}">{text}</span>'


def _format_flow(val: float) -> str:
    if not val or val == 0:
        return "—"
    sign = "+" if val > 0 else ""
    av = abs(val)
    if av >= 1e8:
        return f"{sign}{val/1e8:.1f}億"
    if av >= 1e7:
        return f"{sign}{val/1e7:.1f}千萬"
    if av >= 1e6:
        return f"{sign}{val/1e6:.1f}百萬"
    return f"{sign}{val/1e4:.0f}萬"


def _flow_cls(val: float) -> str:
    return "pos" if val > 0 else ("neg" if val < 0 else "neu")


def _score_grade(score: float, max_val: float = 200.0) -> tuple[str, str, str]:
    """Returns (badge_class, bar_color, label)."""
    pct = score / max_val * 100
    if pct >= 70:
        return "strong", "green", "強力"
    if pct >= 45:
        return "moderate", "yellow", "穩健"
    return "weak", "yellow", "待確認"


def _chip_status_display(cs: str) -> tuple[str, str]:
    return {
        "STRONG_POSITIVE": ("強力買超", "green"),
        "POSITIVE": ("買超", "green"),
        "NEUTRAL": ("法人中性", "grey"),
        "DIVERGENCE": ("籌碼分歧", "yellow"),
        "NEGATIVE": ("法人賣超", "red"),
        "STRONG_NEGATIVE": ("強力賣超", "red"),
    }.get(cs, (cs, "grey"))


def _chase_display(cr: str) -> tuple[str, str]:
    return {
        "LOW": ("追價風險低", "green"),
        "MEDIUM": ("追價風險中", "yellow"),
        "HIGH": ("追價風險高", "red"),
    }.get(cr, (cr, "grey"))


def _signal_cls(sig: str) -> str:
    return {"BUY": "green", "SELL": "red"}.get(sig, "yellow")


def _mkt_cls(state: str) -> str:
    s = state.upper()
    if "BULL" in s:
        return "bull"
    if "BEAR" in s:
        return "bear"
    return "range"


def _vix_cls(v: float) -> str:
    return "green" if v < 20 else ("yellow" if v < 30 else "red")


ROLE_ORDER = {"CORE_ETF": 0, "CORE": 1, "SATELLITE": 2, "WAVE_SWING": 3}


def _role_sort_key(h: dict) -> int:
    return ROLE_ORDER.get((h.get("role") or "").upper(), 9)


def _role_badge_cls(role: str) -> str:
    return role.lower().replace("-", "_")


def _rec_cls(rec: str) -> str:
    return rec.lower().replace("-", "_")


_REC_LABEL = {
    "hold_core": "核心持有", "hold_etf": "ETF持有",
    "hold_satellite": "衛星持有", "hold": "持有",
    "review_exit": "考慮出場", "exit": "立即出場",
    "reduce": "減碼", "trim_overextended": "修剪過熱",
    "watch_trend_damage": "趨勢受損",
}

_ROLE_LABEL = {
    "core_etf": "核心ETF", "core": "核心",
    "satellite": "衛星", "wave_swing": "波段",
}

# ─── SECTION BUILDERS ─────────────────────────────────────────────────────────

def _cand_card(c: dict, rank: int, price_map: dict, tag: str = "", nar_stale: bool = False, nar_days: int = 0) -> str:
    ticker = c.get("ticker", "")
    name = c.get("name", ticker)
    sector = c.get("sector", "")
    score = c.get("score", 0)
    nar = c.get("narrative_score", 0)
    chip = c.get("chip_score", 0)
    vol = c.get("vol_ratio", 0)
    action_mode = c.get("action_mode", "")
    action_label = c.get("action_label", action_mode)
    suggested = c.get("suggested_action", "")
    chase = c.get("chase_risk", "")
    chip_status = c.get("chip_status", "")
    chip_fresh = c.get("chip_freshness", "")
    signal = c.get("signal", "")
    invalid_if = c.get("invalid_if", [])
    foreign = c.get("foreign_net_buy", 0)
    trust = c.get("trust_net_buy", 0)
    dealer = c.get("dealer_net_buy", 0)

    # price from lookup
    price = price_map.get(ticker, 0)

    card_cls = "satellite" if tag == "satellite" else (
        "buy" if "BUY" in action_mode and "CAUTION" not in action_mode else
        "caution" if "CAUTION" in action_mode or "WATCH" in action_mode else
        "exit"
    )

    badge_cls, bar_color, grade_label = _score_grade(score)
    bar_pct = min(100, score / 200 * 100)
    sig_cls = _signal_cls(signal)

    cs_label, cs_color = _chip_status_display(chip_status)
    ch_label, ch_color = _chase_display(chase)
    fresh_chip = _chip("籌碼新鮮", "green") if chip_fresh == "FRESH" else _chip("籌碼待更新", "grey")

    satellite_badge = '<span class="card-role-badge satellite">衛星觀察</span>' if tag == "satellite" else ""

    # invalid conditions — only show if meaningful (skip if all empty)
    invalid_html = ""
    if invalid_if:
        items = "・".join(invalid_if)
        invalid_html = f'<div class="invalid-row"><span class="il">失效：</span>{items}</div>'

    # vol color
    vol_cls = "green" if vol >= 1.0 else ("yellow" if vol >= 0.7 else "muted")

    price_str = f"{price:,.0f}" if price else "—"

    return f"""
<div class="cand-card {card_cls}">
  <div class="card-top">
    <div>
      <div class="card-name">{name}</div>
      <div class="card-sub">
        <span class="card-ticker">{ticker}</span>
        {f'<span class="chip purple" style="font-size:10px">{sector}</span>' if sector else ""}
        {satellite_badge}
      </div>
    </div>
    <div class="card-right">
      <span class="card-rank">#{rank}</span>
      <span class="card-signal {sig_cls}">{signal}</span>
    </div>
  </div>

  <div class="card-score">
    <div class="score-hdr">
      <div><span class="score-num">{score:.0f}</span><span class="score-unit"> 分</span></div>
      <span class="score-badge {badge_cls}">{grade_label}</span>
    </div>
    <div class="progress-track">
      <div class="progress-fill {bar_color}" style="width:{bar_pct:.0f}%"></div>
    </div>
    <div class="score-subs">
      <span>敘事 {nar:.0f}{"<span class='stale-tag'>⚠ "+str(nar_days)+"天前</span>" if nar_stale else ""}</span><span>籌碼 {chip}</span><span>量比 {vol:.2f}x</span>
    </div>
  </div>

  <div class="card-metrics">
    <div class="metric"><span class="ml">收盤</span><span class="mv blue">{price_str}</span></div>
    <div class="metric"><span class="ml">量比</span><span class="mv {vol_cls}">{vol:.2f}x</span></div>
    <div class="metric"><span class="ml">敘事{"⚠" if nar_stale else ""}</span><span class="mv {'yellow' if nar_stale else ('green' if nar>=80 else 'yellow')}">{nar:.0f}</span></div>
    <div class="metric"><span class="ml">籌碼分</span><span class="mv {'green' if chip>=70 else 'yellow'}">{chip}</span></div>
  </div>

  <div class="card-inst">
    <div class="inst-col">
      <span class="inst-lbl">外資</span>
      <span class="inst-val {_flow_cls(foreign)}">{_format_flow(foreign)}</span>
    </div>
    <div class="inst-col">
      <span class="inst-lbl">投信</span>
      <span class="inst-val {_flow_cls(trust)}">{_format_flow(trust)}</span>
    </div>
    <div class="inst-col">
      <span class="inst-lbl">自營商</span>
      <span class="inst-val {_flow_cls(dealer)}">{_format_flow(dealer)}</span>
    </div>
  </div>

  <div class="card-chips">
    {_chip(cs_label, cs_color)}
    {_chip(ch_label, ch_color)}
    {fresh_chip}
  </div>

  <div class="card-action">
    <div class="action-mode">{action_label}</div>
    <div class="action-note">{suggested}</div>
    {invalid_html}
  </div>
</div>"""


def _holdings_section(holdings: list, uni: dict, pnl_map: dict | None = None) -> str:
    if not holdings:
        return '<p style="color:var(--muted);padding:14px">無持倉資料</p>'
    pnl_map = pnl_map or {}
    sorted_h = sorted(holdings, key=_role_sort_key)
    rows = ""
    for h in sorted_h:
        ticker = h.get("ticker", "")
        raw_name = h.get("name", "")
        name = raw_name if (raw_name and raw_name != ticker) else uni.get(ticker, {}).get("name", "") or ticker
        role = h.get("role", "")
        rec = h.get("recommendation", "")
        note = h.get("note", "")
        role_cls = _role_badge_cls(role)
        role_label = _ROLE_LABEL.get(role_cls, role)
        rec_cls = _rec_cls(rec)
        rec_label = _REC_LABEL.get(rec_cls, rec)

        # P&L from portfolio
        pnl = pnl_map.get(ticker, {})
        pnl_html = ""
        if pnl:
            entry = pnl.get("entry_price", 0)
            current = pnl.get("current_price", 0)
            label = pnl.get("pnl_label", "—")
            cls = pnl.get("pnl_cls", "muted")
            if entry:
                pnl_html = f'<div class="hold-cost">成本 {entry:,.1f}</div>'
                if current:
                    pnl_html += f'<div class="hold-pnl {cls}">{label} (現 {current:,.0f})</div>'
                else:
                    pnl_html += '<div class="hold-pnl muted">無現價</div>'

        # highlight exit urgency
        is_exit = rec_cls in ("exit", "review_exit", "watch_trend_damage", "reduce", "trim_overextended")
        row_style = ' style="border-left:3px solid var(--red);padding-left:11px"' if rec_cls == "exit" else \
                    ' style="border-left:3px solid var(--orange);padding-left:11px"' if is_exit else ""

        rows += f"""
<div class="hold-row"{row_style}>
  <div>
    <div class="hold-ticker">{ticker}</div>
    <div class="hold-name">{name}</div>
    {pnl_html}
  </div>
  <span class="hold-role {role_cls}">{role_label}</span>
  <div class="hold-right">
    <span class="rec {rec_cls}">{rec_label}</span>
    <span class="hold-note">{note}</span>
  </div>
</div>"""
    return f'<div class="hold-wrap">{rows}</div>'


def _early_section(items: list) -> str:
    if not items:
        return '<p style="color:var(--muted)">無早期候選</p>'
    cards = ""
    for item in items[:24]:
        ticker = item.get("ticker", "")
        name = item.get("name", ticker)
        price = item.get("price", 0)
        sector = item.get("sector", "")
        price_str = f"{price:,.1f}" if price else "—"
        cards += f"""
<div class="wi">
  <div class="wi-ticker">{ticker}</div>
  <div class="wi-name">{name if name != ticker else "—"}</div>
  <div class="wi-price">{price_str}</div>
  {f'<div class="wi-sector">{sector}</div>' if sector else ""}
</div>"""
    return f'<div class="watchlist-grid">{cards}</div>'


def _market_card(data: dict) -> str:
    state = data.get("market_state", "UNKNOWN")
    score = data.get("market_score", 0)
    vix = data.get("vix_value", 0)
    vix_alert = data.get("vix_alert", "NORMAL")
    guidance = data.get("market_guidance", {})
    summary = guidance.get("summary", "")
    holding_action = guidance.get("holding_action", "")
    new_entry = guidance.get("new_entry_ok", False)

    state_label = {"BULL": "多頭趨勢 ▲", "BEAR": "空頭趨勢 ▼", "RANGE": "盤整格局 ◆"}.get(state, state)
    vix_cls = _vix_cls(vix)
    vix_label = {"NORMAL": "正常", "ELEVATED": "偏高", "HIGH": "高", "EXTREME": "極高"}.get(vix_alert, vix_alert)
    entry_chip = _chip("可進場", "green") if new_entry else _chip("暫停進場", "red")

    role_chips = " ".join(_chip(r, "purple") for r in guidance.get("role_filter", []))

    return f"""
<div class="mkt-card">
  <div class="mkt-card-row">
    <div class="mkt-mini">
      <div class="label">VIX</div>
      <div class="value {vix_cls}">{vix:.1f}</div>
      <div class="sub">{vix_label}</div>
    </div>
    <div class="mkt-mini">
      <div class="label">Market Score</div>
      <div class="value {'green' if score>0 else 'red'}" style="font-size:18px">{score:+.4f}</div>
      <div class="sub" style="margin-top:4px">{entry_chip} {role_chips}</div>
    </div>
  </div>
  {f'<div class="guidance">{summary}</div>' if summary else ""}
  {f'<div class="guidance" style="border-left-color:var(--purple);margin-top:6px">{holding_action}</div>' if holding_action else ""}
</div>"""


def _summary_strip(data: dict, price_map: dict) -> str:
    wave = data.get("wave_swing_candidates", [])
    satellite = data.get("satellite_watch", [])
    holdings = data.get("holdings_guidance", [])
    exits = sum(1 for h in holdings if "EXIT" in h.get("recommendation","").upper()
                or "REDUCE" in h.get("recommendation","").upper())
    total_entry = len(wave) + len(satellite)

    cards = [
        ("進場候選", total_entry, "green", "WAVE + 衛星"),
        ("持倉警示", exits, "red" if exits else "muted", "需檢視"),
        ("VIX", f"{data.get('vix_value',0):.1f}", _vix_cls(data.get('vix_value',0)), data.get('vix_alert','NORMAL')),
        ("市場", data.get('market_state','?'), _mkt_cls(data.get('market_state','')), data.get('system_mode','')[:20]),
    ]
    html = ""
    for label, val, color, sub in cards:
        html += f"""
<div class="sum-card">
  <div class="sum-label">{label}</div>
  <div class="sum-val {color}">{val}</div>
  <div class="sum-sub">{sub}</div>
</div>"""
    return f'<div class="sum-strip">{html}</div>'


def _legend_section() -> str:
    return """
<div class="legend-wrap">
<details>
<summary class="legend-summary">📖 欄位說明 — 點擊展開</summary>
<div class="legend-body">

  <div class="legend-group">
    <div class="legend-group-title">📊 總覽指標</div>
    <div class="legend-item"><span class="legend-key">VIX</span><span class="legend-val">美國市場恐慌指數。&lt;20 = 低波動（綠）；20–30 = 偏高（黃）；&gt;30 = 極高風險（紅）</span></div>
    <div class="legend-item"><span class="legend-key">市場分數</span><span class="legend-val">系統綜合技術指標計算的多空分數，正值偏多、負值偏空</span></div>
    <div class="legend-item"><span class="legend-key">進場候選</span><span class="legend-val">同時符合技術訊號 + 籌碼條件的波段操作候選檔數（WAVE + 衛星觀察合計）</span></div>
    <div class="legend-item"><span class="legend-key">持倉警示</span><span class="legend-val">現有持倉中建議考慮出場或減碼的檔數</span></div>
  </div>

  <div class="legend-group">
    <div class="legend-group-title">🎯 進場候選 — 各欄說明</div>
    <div class="legend-item"><span class="legend-key">總分</span><span class="legend-val">敘事分 × 0.2 + 籌碼分 × 0.2 + 技術/量能加分，最高約 200 分。強力 ≥ 140、穩健 ≥ 90</span></div>
    <div class="legend-item"><span class="legend-key">敘事分</span><span class="legend-val">由 Gemini / Claude / Perplexity 三個 AI 獨立評估產業主題強度（AI Server、HBM、半導體…）後取共識平均分，0–100</span></div>
    <div class="legend-item"><span class="legend-key">籌碼分</span><span class="legend-val">依外資/投信/自營商當日買賣超加總計算，0–100。資料來源：TWSE（上市）與 TPEX（上櫃）官方 API</span></div>
    <div class="legend-item"><span class="legend-key">量比</span><span class="legend-val">當日成交量 ÷ 近期均量。≥ 1.0 = 放量（綠）；0.7–1.0 = 正常；&lt;0.7 = 縮量（灰）</span></div>
    <div class="legend-item"><span class="legend-key">外資／投信／自營</span><span class="legend-val">當日法人買賣超張數（正 = 買超，負 = 賣超）。原始數字來自交易所，單位為股，顯示轉換為萬／千萬／億</span></div>
    <div class="legend-item"><span class="legend-key">強力買超／分歧</span><span class="legend-val">籌碼狀態：STRONG_POSITIVE（外資+總量均大幅買超）/ POSITIVE（整體買超）/ DIVERGENCE（外資賣但投信買，或反之）/ NEGATIVE（整體賣超）</span></div>
    <div class="legend-item"><span class="legend-key">追價風險</span><span class="legend-val">LOW = 技術面顯示尚未過熱可試單；MEDIUM = 短線漲幅偏大需謹慎；HIGH = 不建議追高</span></div>
    <div class="legend-item"><span class="legend-key">籌碼新鮮</span><span class="legend-val">FRESH = 籌碼資料為今日或昨日；STALE/待更新 = 資料超過 2 個交易日未更新</span></div>
    <div class="legend-item"><span class="legend-key">失效條件</span><span class="legend-val">如果這些條件發生，代表進場訊號可能失效，應重新評估或停損出場</span></div>
    <div class="legend-item"><span class="legend-key">衛星觀察</span><span class="legend-val">已進入觀察名單但尚未達到主力進場條件，屬輕倉試探或追蹤</span></div>
  </div>

  <div class="legend-group">
    <div class="legend-group-title">📋 持倉建議 — 角色與操作</div>
    <div class="legend-item"><span class="legend-key">核心ETF</span><span class="legend-val">指數型 ETF，長期配置核心，不輕易動</span></div>
    <div class="legend-item"><span class="legend-key">核心</span><span class="legend-val">基本面強、長期持有，趨勢未壞則維持</span></div>
    <div class="legend-item"><span class="legend-key">衛星</span><span class="legend-val">主題型持倉，靈活調整，依市場環境加減碼</span></div>
    <div class="legend-item"><span class="legend-key">波段</span><span class="legend-val">短中期技術操作，有明確停損條件，不適合長抱</span></div>
    <div class="legend-item"><span class="legend-key">考慮出場／修剪</span><span class="legend-val">技術面或籌碼面出現疑慮，建議評估減碼或設定出場計畫</span></div>
  </div>

  <div class="legend-group">
    <div class="legend-group-title">📡 早期候選 — 條件說明</div>
    <div class="legend-item"><span class="legend-key">score = 1</span><span class="legend-val">已通過初步宇宙篩選（universe_tw.csv 覆蓋範圍內），但尚未同時滿足技術訊號 + 籌碼條件，屬「潛力觀察名單」</span></div>
    <div class="legend-item"><span class="legend-key">排列方式</span><span class="legend-val">依產業分組後再依代號排序，方便同產業比較。相同產業的標的集中顯示</span></div>
    <div class="legend-item"><span class="legend-key">何時升級</span><span class="legend-val">當技術訊號（BUY + READY level）與籌碼條件同時達標，score 升為 2，進入「進場候選」區塊</span></div>
  </div>

</div>
</details>
</div>"""


# ─── MAIN BUILD ───────────────────────────────────────────────────────────────

def build_dashboard() -> str:
    main_data = _load_json(MAINLINE_SNAPSHOT) or {}
    signal_data = _load_json(SIGNAL_SNAPSHOT) or {}
    uni = _load_universe_map()
    price_map = _load_price_map()

    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    data_date = (main_data.get("generated_at") or ts)[:10]

    # closed banner
    closed_banner = ""
    if signal_data.get("market_closed"):
        reason = signal_data.get("reason","")
        latest = signal_data.get("latest_full_trading_day","")
        closed_banner = f'<div class="closed-banner">⚠ 市場休市（{reason}）｜以下為 {latest} 分析結果</div>'

    nar_days, nar_stale = _narrative_staleness()
    pnl_map = _load_portfolio_pnl(price_map)

    wave = main_data.get("wave_swing_candidates", [])
    satellite = main_data.get("satellite_watch", [])
    holdings = main_data.get("holdings_guidance", [])
    early = _load_early_candidates(uni)

    state = main_data.get("market_state", "UNKNOWN")
    vix = main_data.get("vix_value", 0)
    score = main_data.get("market_score", 0)
    vix_alert = main_data.get("vix_alert", "NORMAL")
    vix_label = {"NORMAL":"正常","ELEVATED":"偏高","HIGH":"高","EXTREME":"極高"}.get(vix_alert, vix_alert)
    exits_n = sum(1 for h in holdings if "EXIT" in h.get("recommendation","").upper()
                  or "REDUCE" in h.get("recommendation","").upper())

    # module status pills
    chips_path = ROOT / "data" / "chips" / "latest_chips.json"
    chips_mtime_days = 999
    try:
        import os as _os
        chips_mtime_days = int((datetime.now().timestamp() - _os.path.getmtime(chips_path)) / 86400)
    except Exception:
        pass
    chips_cls = "ok" if chips_mtime_days < 2 else ("warn" if chips_mtime_days < 5 else "stale")
    chips_label = f"籌碼 {'今日' if chips_mtime_days==0 else str(chips_mtime_days)+'天前'}"
    nar_cls = "stale" if nar_stale else "ok"
    nar_pill_label = f"敘事 {nar_days}天前 (建置中)"
    snap_days = int((datetime.now().timestamp() - (ROOT / "data" / "processed" / "mainline_snapshot.json").stat().st_mtime) / 86400) if (ROOT / "data" / "processed" / "mainline_snapshot.json").exists() else 999
    snap_cls = "ok" if snap_days < 2 else "warn"
    snap_label = f"快照 {'今日' if snap_days==0 else str(snap_days)+'天前'}"

    mod_status_bar = f"""
<div class="mod-status-bar">
  <span class="mod-pill {snap_cls}">{snap_label}</span>
  <span class="mod-pill {chips_cls}">{chips_label}</span>
  <span class="mod-pill {nar_cls}">{nar_pill_label}</span>
</div>"""

    # merge wave + satellite into one ranked list
    wave_cards = ""
    for i, c in enumerate(wave[:12], 1):
        wave_cards += _cand_card(c, i, price_map, nar_stale=nar_stale, nar_days=nar_days)
    for i, c in enumerate(satellite[:4], len(wave)+1):
        wave_cards += _cand_card(c, i, price_map, tag="satellite", nar_stale=nar_stale, nar_days=nar_days)

    total_entry = len(wave) + len(satellite)

    return f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Investment OS 戰情表板</title>
<style>{_CSS}</style>
</head>
<body>

<div class="topbar">
  <span class="brand">Investment OS</span>
  <nav>
    <a href="status.html">狀態</a>
    <a href="dashboard.html" class="active">戰情</a>
    <a href="history.html">歷史</a>
    <a href="replay.html">Replay</a>
  </nav>
  <span class="ts">{ts}</span>
</div>

<div class="mktbar">
  <div class="mkt-state {_mkt_cls(state)}">
    {"多頭 ▲" if "BULL" in state else "空頭 ▼" if "BEAR" in state else "盤整 ◆"}
  </div>
  <div class="mkt-divider"></div>
  <div class="mkt-item">
    <span class="lbl">VIX</span>
    <span class="val {_vix_cls(vix)}">{vix:.1f}</span>
  </div>
  <div class="mkt-item">
    <span class="lbl">市場分數</span>
    <span class="val {'green' if score>0 else 'red'}">{score:+.3f}</span>
  </div>
  <div class="mkt-divider"></div>
  <div class="mkt-item">
    <span class="lbl">進場候選</span>
    <span class="val green">{total_entry}</span>
  </div>
  <div class="mkt-item">
    <span class="lbl">持倉警示</span>
    <span class="val {'red' if exits_n else 'muted'}">{exits_n}</span>
  </div>
  <div class="mkt-item">
    <span class="lbl">VIX狀態</span>
    <span class="val {_vix_cls(vix)}">{vix_label}</span>
  </div>
</div>

<div class="container">
  {closed_banner}
  {mod_status_bar}
  {_summary_strip(main_data, price_map)}
  {_market_card(main_data)}

  <div class="sec-hdr">
    <h2>🎯 進場候選</h2>
    <span class="sec-cnt">{total_entry} 檔</span>
    <div class="sec-line"></div>
  </div>
  <div class="sec-note">
    <strong>波段技術操作候選</strong>：技術訊號（BUY + READY）與籌碼條件同時達標。策略為「強者恆強動能追蹤」，在技術突破點試單，非低估值買進。每張卡片附有<strong>失效條件</strong>與建議停損，操作前請確認個人風險承受度。
  </div>
  {"<p style='color:var(--muted);padding:14px'>目前無進場候選</p>" if not wave and not satellite else wave_cards}

  <div class="sec-hdr">
    <h2>📋 現有持倉建議</h2>
    <span class="sec-cnt">{len(holdings)} 檔</span>
    <div class="sec-line"></div>
  </div>
  <div class="sec-note">
    依角色排列：<strong>核心ETF → 核心 → 衛星 → 波段</strong>。操作建議由 pipeline 根據技術面與籌碼面產生，「考慮出場」不代表立即停損，請結合個人成本自行判斷。
  </div>
  {_holdings_section(holdings, uni, pnl_map)}

  {"" if not early else f'''
  <div class="sec-hdr">
    <h2>📡 早期候選（觀察名單）</h2>
    <span class="sec-cnt">{len(early)} 檔</span>
    <div class="sec-line"></div>
  </div>
  <div class="sec-note">
    <strong>篩選條件：</strong>已通過初步宇宙篩選（score = 1），但技術訊號或籌碼條件尚未同時達標。<br>
    <strong>排列方式：</strong>依產業分組後再依代號排序，便於同產業比較。<br>
    <strong>升級時機：</strong>當技術（BUY + READY）與籌碼同時達標 → score 升為 2 → 進入「進場候選」區塊。
  </div>
  {_early_section(early)}
  '''}

  {_legend_section()}

  <div class="disclaimer">
    ⚠ 本系統為技術分析與籌碼整理，不代表保證獲利，操作前請依個人資金控管與風險承受度判斷。<br>
    籌碼資料來源：TWSE（台灣證券交易所）與 TPEX（上櫃）官方公開資料。敘事分由 Gemini / Claude / Perplexity 三方 AI 共識產生。
  </div>
</div>
</body>
</html>"""


def write_dashboard() -> Path:
    WEB_DIR.mkdir(parents=True, exist_ok=True)
    out = WEB_DIR / "dashboard.html"
    out.write_text(build_dashboard(), encoding="utf-8")
    return out


if __name__ == "__main__":
    path = write_dashboard()
    print(f"✅ 戰情表板已生成：{path}")
