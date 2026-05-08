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
