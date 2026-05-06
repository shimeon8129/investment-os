import json
import os
import sys
from datetime import datetime, timedelta
from urllib.parse import urlencode
from urllib.request import Request, urlopen


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


OUTPUT_DIR = "data/chips"
LATEST_PATH = os.path.join(OUTPUT_DIR, "latest.json")


def parse_int(value) -> int:
    if value is None:
        return 0
    text = str(value).replace(",", "").replace("--", "0").strip()
    if not text:
        return 0
    return int(float(text))


def request_json(url: str) -> dict:
    req = Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0 Safari/537.36"
            )
        },
    )
    with urlopen(req, timeout=15) as response:
        return json.load(response)


def twse_url(day: datetime) -> str:
    params = urlencode({
        "date": day.strftime("%Y%m%d"),
        "selectType": "ALLBUT0999",
        "response": "json",
    })
    return f"https://www.twse.com.tw/rwd/zh/fund/T86?{params}"


def tpex_url(day: datetime) -> str:
    params = urlencode({
        "date": day.strftime("%Y/%m/%d"),
        "type": "Daily",
        "response": "json",
    })
    return f"https://www.tpex.org.tw/www/zh-tw/insti/dailyTrade?{params}"


def fetch_with_backoff(url_builder, max_lookback_days=10) -> tuple[dict, str]:
    today = datetime.now()

    for offset in range(max_lookback_days + 1):
        day = today - timedelta(days=offset)
        data = request_json(url_builder(day))
        stat = str(data.get("stat", "")).lower()

        if stat in {"ok", "ok.", "ok "} or data.get("data") or data.get("tables"):
            return data, day.strftime("%Y-%m-%d")

    raise RuntimeError("No institutional data found in lookback window")


def parse_twse(data: dict) -> dict:
    rows = {}
    fields = data.get("fields", [])
    field_index = {name: idx for idx, name in enumerate(fields)}

    def value(row, field_name):
        idx = field_index.get(field_name)
        if idx is None or idx >= len(row):
            return 0
        return row[idx]

    for row in data.get("data", []):
        code = row[0].strip()
        rows[code] = {
            "ticker": f"{code}.TW",
            "code": code,
            "name": row[1].strip(),
            "market": "TWSE",
            "foreign_net_buy": parse_int(value(row, "外陸資買賣超股數(不含外資自營商)")),
            "trust_net_buy": parse_int(value(row, "投信買賣超股數")),
            "dealer_net_buy": parse_int(value(row, "自營商買賣超股數")),
            "institutional_net_buy": parse_int(value(row, "三大法人買賣超股數")),
        }

    return rows


def parse_tpex(data: dict) -> dict:
    table = data.get("tables", [{}])[0]
    rows = {}

    for row in table.get("data", []):
        code = row[0].strip()
        rows[code] = {
            "ticker": f"{code}.TWO",
            "code": code,
            "name": row[1].strip(),
            "market": "TPEX",
            "foreign_net_buy": parse_int(row[10]),
            "trust_net_buy": parse_int(row[13]),
            "dealer_net_buy": parse_int(row[22]),
            "institutional_net_buy": parse_int(row[23]),
        }

    return rows


def score_chip_flow(row: dict) -> int:
    foreign = row.get("foreign_net_buy", 0)
    trust = row.get("trust_net_buy", 0)
    dealer = row.get("dealer_net_buy", 0)
    total = row.get("institutional_net_buy", 0)

    score = 0

    if total > 0:
        score += 25
    if foreign > 0:
        score += 25
    if trust > 0:
        score += 20
    if dealer > 0:
        score += 10

    positive_magnitude = max(total, 0)
    if positive_magnitude >= 5_000_000:
        score += 20
    elif positive_magnitude >= 1_000_000:
        score += 15
    elif positive_magnitude >= 300_000:
        score += 10
    elif positive_magnitude >= 50_000:
        score += 5

    if total < 0:
        score = max(score - 20, 0)
    if foreign < 0 and trust < 0:
        score = max(score - 20, 0)

    return min(score, 100)


def normalize_code(ticker: str) -> str:
    return str(ticker).split(".")[0]


def load_candidates(path="data/candidates.json") -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_chips_report(candidates: list[dict]) -> dict:
    twse_data, twse_date = fetch_with_backoff(twse_url)
    tpex_data, tpex_date = fetch_with_backoff(tpex_url)

    twse_rows = parse_twse(twse_data)
    tpex_rows = parse_tpex(tpex_data)

    items = []

    for candidate in candidates:
        ticker = candidate.get("ticker", "")
        code = normalize_code(ticker)

        row = tpex_rows.get(code) if ticker.endswith(".TWO") else twse_rows.get(code)
        if not row:
            row = twse_rows.get(code) or tpex_rows.get(code)

        if not row:
            continue

        chip_score = score_chip_flow(row)
        bias = "BUY" if row["institutional_net_buy"] > 0 else "SELL" if row["institutional_net_buy"] < 0 else "FLAT"

        items.append({
            **row,
            "chip_score": chip_score,
            "institutional_bias": bias,
        })

    items.sort(key=lambda row: row["chip_score"], reverse=True)

    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "source": "twse_tpex_institutional",
        "market_dates": {
            "TWSE": twse_date,
            "TPEX": tpex_date,
        },
        "items": items,
    }


def save_report(report: dict):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    dated_path = os.path.join(OUTPUT_DIR, f"{report['date']}.json")

    for path in [dated_path, LATEST_PATH]:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"✅ saved: {LATEST_PATH}")
    print(f"✅ saved: {dated_path}")


def main():
    limit = None
    if len(sys.argv) > 1:
        limit = int(sys.argv[1])

    candidates = load_candidates()
    selected = candidates[:limit] if limit else candidates
    report = build_chips_report(selected)
    save_report(report)

    print("\n=== TOP CHIP SCORES ===")
    for row in report["items"][:10]:
        print(
            f"{row['ticker']} {row['name']} | chip={row['chip_score']} | "
            f"foreign={row['foreign_net_buy']:,} trust={row['trust_net_buy']:,} "
            f"dealer={row['dealer_net_buy']:,} total={row['institutional_net_buy']:,}"
        )


if __name__ == "__main__":
    main()
