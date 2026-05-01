#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "master" / "ai_watchlist_source.csv"
OUTPUT = ROOT / "data" / "watchlist.json"

LAYER_ORDER = {
    "第一層": 1,
    "第二層": 2,
    "第三層": 3,
    "第四層": 4,
    "第五層": 5,
    "未分類": 99,
}

OTC_SYMBOLS = {
    "3081", "3105", "3363", "3661", "4979",
    "6187", "6515", "6669", "7769", "8299",
}

def to_bool(value: str) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y", "啟用"}

def yf_symbol(code: str) -> str:
    code = str(code).strip()
    return f"{code}.TWO" if code in OTC_SYMBOLS else f"{code}.TW"

def main() -> int:
    if not SOURCE.exists():
        raise FileNotFoundError(f"Missing source file: {SOURCE}")

    tickers = []

    with SOURCE.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        required = [
            "股票代號",
            "股票名稱",
            "蛋糕第幾層",
            "產業類別",
            "核心角色與 AI 關鍵觀察點",
            "啟用",
        ]

        missing = [col for col in required if col not in reader.fieldnames]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        for row in reader:
            code = row["股票代號"].strip()
            name = row["股票名稱"].strip()
            layer = row["蛋糕第幾層"].strip() or "未分類"
            industry = row["產業類別"].strip() or "未分類"
            ai_note = row["核心角色與 AI 關鍵觀察點"].strip()
            active = to_bool(row["啟用"])

            if not code or not name:
                continue

            tickers.append({
                "symbol": code,
                "name": name,
                "yf_symbol": yf_symbol(code),
                "active": active,
                "meta": {
                    "layer": layer,
                    "layer_order": LAYER_ORDER.get(layer, 99),
                    "industry": industry,
                    "ai_note": ai_note,
                }
            })

    tickers.sort(
        key=lambda x: (
            x["meta"]["layer_order"],
            x["meta"]["industry"],
            x["symbol"],
        )
    )

    output = {
        "version": "0.4",
        "name": "AI Investment OS Watchlist",
        "market": "TW",
        "currency": "TWD",
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "editable_source": "data/master/ai_watchlist_source.csv",
        "schema": {
            "machine_fields": ["symbol", "name", "yf_symbol", "active"],
            "annotation_fields": ["meta.layer", "meta.industry", "meta.ai_note"],
        },
        "tickers": tickers,
    }

    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[PASS] wrote: {OUTPUT}")
    print(f"[PASS] ticker count: {len(tickers)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
