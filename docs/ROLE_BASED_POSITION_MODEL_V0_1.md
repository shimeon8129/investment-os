# Investment OS｜Role-Based Position Model v0.1

**建立日期：** 2026-05-10
**修訂日期：** 2026-05-10（含 Owner 決策）
**狀態：** APPROVED_WITH_CHANGES — AWAITING_IMPLEMENTATION
**邊界：** 設計文件。不修改排名引擎、EntryLock、runtime 或任何交易邏輯。

---

## Purpose

目前 Investment OS 對所有標的使用同一套排名與 EntryLock 評估邏輯，不區分持倉目的與操作時間框架。這會造成：

- CORE 持倉（長期 AI 主線曝險）被短線雜訊觸發不必要的訊號
- WAVE_SWING 標的（短波段）進出時間框架與 CORE 混用，難以評估有效性
- 難以向 owner 解釋「為什麼今天系統說 HOLD 但不說 ADD」

**本模型目標：** 為每個標的定義 `base_role`（長期策略身份）與 `active_role`（當前操作模式），讓系統用角色對應的評估視窗輸出更有意義的行動建議。

---

## Role Structure：base_role vs active_role

每個標的同時具備兩個角色欄位：

| 欄位 | 說明 |
| --- | --- |
| `base_role` | 長期策略身份，由 watchlist layer 與持倉目的決定，相對穩定 |
| `active_role` | 當前操作模式，可隨市場結構、動能、趨勢狀態動態調整 |

**設計意圖：** 一支 CORE 股票在特定市場階段也可以用 WAVE_SWING 模式操作。兩者不衝突。

```
範例：
  2345.TW 智邦
    base_role   = CORE          ← 長期 AI 交換機主線，策略上不輕易出場
    active_role = SATELLITE     ← 目前籌碼偏弱，以觀察模式持有
    upgrade_path = WAVE_SWING   ← 若量價突破，轉以 WAVE_SWING 規格進場

  6830.TW 汎銓
    base_role   = SATELLITE     ← 非第一線 AI 主線，中期輪動標的
    active_role = WAVE_SWING    ← 近期出現技術型態，以短波段規格操作
```

---

## Roles

### CORE_ETF

| 項目 | 說明 |
| --- | --- |
| **目的** | 核心曝險停泊 / 分散主題曝險（009816、00992A） |
| **持有週期** | 長期，非主動交易 |
| **期望行為** | 不觸發個股 EntryLock；不參與 WAVE_SWING 評估；僅監控 NAV 趨勢與市場狀態 |
| **系統輸出** | `HOLD_ETF` / `WATCH_ETF_TREND` |

> ETF 不進入三角色（CORE/SATELLITE/WAVE_SWING）框架，獨立管理。

---

### CORE

| 項目 | 說明 |
| --- | --- |
| **目的** | 長期持有 AI 主線核心曝險（台積電、日月光、聯發科等第一層標的） |
| **持有週期** | 3 個月以上，不主動操作 |
| **期望行為** | 趨勢完整時 HOLD；僅在明確趨勢損壞或極度超買時才考慮減碼 |
| **評估視窗** | MA20 / MA60 趨勢方向；相對大盤強度（RS）；月線是否仍朝上 |
| **有用指標** | 60 日 RS、MA60 斜率、法人持股變化（月均） |
| **不應觸發出場** | 日內短暫跌破 MA5、單日成交量異常、短期震盪回測 |
| **系統輸出** | `HOLD_CORE` / `ADD_ON_PULLBACK` / `WATCH_TREND_DAMAGE` / `TRIM_OVEREXTENDED` |

**CORE 判定原則：** 不是「今天訊號最強」，而是「長期結構仍完整」。

---

### SATELLITE

| 項目 | 說明 |
| --- | --- |
| **目的** | 主線延伸曝險，跟隨 CORE 主題的相關標的（AI 散熱、光連接、封測等第二～三層） |
| **持有週期** | 1～6 週，根據訊號強弱決定留倉長度 |
| **期望行為** | 主題輪動時進場；相對強度轉弱或主題降溫時減碼 |
| **評估視窗** | MA10 / MA20 趨勢；相對 sector 強度；近 10 日籌碼變化 |
| **有用指標** | 10 日 RS vs sector、法人連續買賣、成交量相對放大倍率 |
| **升級條件** | 突破型態 + 量能放大 + L2/L3 全 PASS → `active_role` 轉為 WAVE_SWING |
| **系統輸出** | `WATCH_SATELLITE` / `UPGRADE_TO_WAVE` / `ADD_SMALL` / `WAIT_FOR_CONFIRMATION` / `REDUCE_SATELLITE` |

---

### WAVE_SWING

| 項目 | 說明 |
| --- | --- |
| **目的** | 捕捉短波段動能行情（3～20 個交易日） |
| **持有週期** | 3～20 個交易日，嚴格停損 |
| **期望行為** | 訊號出現後快速進場；達到目標或型態破壞即出場 |
| **評估視窗** | MA5 / MA10；成交量確認；近 5 日漲幅與型態 |
| **有用指標** | VCP 型態分數、ATR 波動率、法人短期淨買超、突破前高 |
| **失敗條件** | 進場後跌破 MA5 且成交量縮，或 3D 報酬 < -3%，或型態無效 |
| **系統輸出** | `WAVE_READY` / `WAVE_ENTRY` / `ENTRY_REDUCED` / `WAIT_PULLBACK` / `OVEREXTENDED` / `WAVE_FAILED_WARN` |

> **注意：** `WAVE_FAILED_WARN` 為**建議通知**，不觸發自動交易。見下方輸出訊號說明。

---

## Dynamic Role Transitions

`active_role` 可在以下條件下轉換，`base_role` 不變：

| 轉換路徑 | 觸發條件 |
| --- | --- |
| `SATELLITE → WAVE_SWING` | L2/L3 全 PASS + 突破型態 + 量確認 |
| `CORE → active: SATELLITE` | MA20 跌破 + RS 轉弱，但 base_role 維持 CORE |
| `CORE active → WATCH_TREND_DAMAGE` | MA20 跌破且量放大，系統輸出警示 |
| `WAVE_SWING → WAVE_FAILED_WARN` | 進場後跌破 MA5 + 量縮，或 3D < -3% |
| `WAVE_FAILED_WARN → exit` | **由 owner 決定**，系統僅輸出建議，不執行 |

**動態切換原則：** 系統記錄每次 `active_role` 變更的時間與原因，供 owner 審核。

---

## Owner-Approved Initial Role Mappings

以下為 owner 確認的現有持倉初始角色：

| Ticker | 名稱 | base_role | active_role | 備注 |
| --- | --- | --- | --- | --- |
| 2330.TW | 台積電 | CORE | CORE | 長期 AI 晶圓代工主線，不輕易操作 |
| 6830.TW | 汎銓 | SATELLITE | WAVE_SWING | 近期有技術型態，以短波段規格追蹤 |
| 2345.TW | 智邦 | CORE | SATELLITE | 目前以觀察模式持有；若突破則 upgrade_path = WAVE_SWING，意圖 HOLD_OR_ADD_ON_PULLBACK |
| 3711.TW | 日月光投控 | CORE | CORE | 第一層封裝龍頭，長期持有 |
| 2408.TW | 南亞科 | SATELLITE | SATELLITE | 記憶體週期，中期輪動持有 |
| 009816 | 凱基台灣TOP50 | CORE_ETF | CORE_ETF | 分散曝險停泊 |
| 00992A | 主動群益科技創新 | CORE_ETF | CORE_ETF | AI 主題 ETF 曝險 |

---

## Automatic Classification Inputs

| 輸入特徵 | 資料來源 | 目前可用？ |
| --- | --- | --- |
| 是否在 `current_holdings.json` | `data/portfolio/current_holdings.json` | ✅ |
| 持倉成本與市值 | `current_holdings.json`.cost_basis | ✅ |
| Watchlist 層級（第一～五層） | `data/watchlist.json`.meta.layer | ✅ |
| 排名分數（ranking score） | `mainline_snapshot.json`.ranked[].score | ✅ |
| 訊號類型（BUY / level） | `mainline_snapshot.json`.signals[].level | ✅ |
| EntryLock 結果（L0–L4） | `p1_audit_report.json`.audit_entries[] | ✅ (當日) |
| P1 audit 結果 | `p1_audit_report.json`.p1_audit_action | ✅ (當日) |
| 近期漲跌（1D/3D return） | yfinance 衍生 | ⚙️ 需計算 |
| MA5 / MA10 / MA20 斜率 | price data 衍生 | ⚙️ 需計算 |
| 相對大盤強度（RS） | price + 加權指數衍生 | ⚙️ 需計算 |
| **進場日期（entry_date）** | **需補入 current_holdings.json** | ❌ 必填（見下方） |

### entry_date 必填聲明

`entry_date` 是 v0.1 分類器的**必要欄位**，需在 `current_holdings.json` 每筆持倉中補入：

```json
{
  "ticker": "2330",
  "entry_date": "2025-11-01",
  ...
}
```

用途：
- 持倉天數 > 60D → 向 CORE active_role 靠攏
- 持倉天數 < 20D → 傾向 WAVE_SWING active_role
- 支援未來 role transition 時間軸記錄

---

## Classification Logic v0.1

### 流程概覽

```
1. asset_type == "ETF"?
   → YES → base_role = active_role = CORE_ETF，結束

2. 有 owner-approved 初始 role mapping？
   → YES → 直接套用，結束（override 所有自動邏輯）

3. 自動分類流程（watchlist layer 為 initial prior）：
   → 走「持倉 / 候選」分支
```

### Watchlist Layer 作為 Initial Prior（非最終角色）

```
Layer 1       → base_role prior = CORE
Layer 2–3     → base_role prior = SATELLITE
Layer 4–5     → base_role prior = WAVE_SWING
不在 watchlist → base_role prior = WAVE_SWING（信心分數 LOW）
```

**Prior 可被以下特徵修正（active_role 決定）：**

```
持倉天數 > 60D       → active_role 向 CORE 靠攏
MA20 斜率向上        → active_role 向 CORE 靠攏
近 5D 報酬 > +5%    → active_role 向 WAVE_SWING 靠攏
RS(10D) > 1.05      → active_role 向 WAVE_SWING 靠攏
L2/L3 PASS + 突破   → active_role = WAVE_SWING（SATELLITE 升級）
資料不足            → active_role = UNKNOWN，輸出 WATCH_SATELLITE
```

### 候選標的分類（未持倉）

```
Layer 1 + ranking_score 高
    → base_role = CORE，active_role = SATELLITE
    → 輸出 WATCH_SATELLITE（等待持倉條件成立）

Layer 2–4 + signal=BUY + level=READY + L2/L3 PASS
    → base_role = SATELLITE，active_role = WAVE_SWING
    → 輸出 WAVE_READY / WAVE_ENTRY

L0 WARN（RANGE 市場）
    → active_role = WAVE_SWING，輸出 ENTRY_REDUCED

資料不完整
    → active_role = UNKNOWN，輸出 WATCH_SATELLITE
```

### 信心分數

| 分數 | 說明 |
| --- | --- |
| HIGH | ≥ 3 個特徵支持該角色 |
| MEDIUM | 2 個特徵支持 |
| LOW | 1 個特徵支持 |
| UNKNOWN | 資料不足，無法判定 |

輸出欄位：`base_role`、`active_role`、`role_confidence`、`role_reason`（列出支持特徵）

---

## Role-Specific Evaluation Windows

| 角色 | 主要視窗 | 關鍵均線 | 報酬評估週期 |
| --- | --- | --- | --- |
| CORE_ETF | 月線趨勢 | MA20 | — |
| CORE | 月線趨勢 | MA20 / MA60 | 20D / 60D |
| SATELLITE | 週線趨勢 | MA10 / MA20 | 5D / 10D |
| WAVE_SWING | 日線動能 | MA5 / MA10 | 1D / 3D / 5D |

---

## Role-Specific System Outputs

每個輸出訊號包含：`action`、`base_role`、`active_role`、`reason`、`confidence`

### CORE_ETF

| 訊號 | 觸發條件 |
| --- | --- |
| `HOLD_ETF` | 市場非 BEAR，持續持有 |
| `WATCH_ETF_TREND` | 市場轉 BEAR 或 NAV 跌破 MA20 |

### CORE

| 訊號 | 觸發條件 |
| --- | --- |
| `HOLD_CORE` | 趨勢完整，MA20 朝上 |
| `ADD_ON_PULLBACK` | 回測 MA20 附近，RS 仍強，市場 BULL/RANGE |
| `WATCH_TREND_DAMAGE` | 跌破 MA20 且成交量放大，或 RS 轉弱 |
| `TRIM_OVEREXTENDED` | 距 MA60 漲幅超過 30% |

### SATELLITE

| 訊號 | 觸發條件 |
| --- | --- |
| `WATCH_SATELLITE` | 在候選宇宙但未達進場條件 |
| `ADD_SMALL` | L2/L3 PASS + 市場 RANGE 以上 |
| `UPGRADE_TO_WAVE` | 突破型態 + 量確認 → active_role 轉 WAVE_SWING |
| `WAIT_FOR_CONFIRMATION` | 訊號出現但量能未確認 |
| `REDUCE_SATELLITE` | 主題輪動轉弱，RS 持續衰退 |

### WAVE_SWING

| 訊號 | 觸發條件 |
| --- | --- |
| `WAVE_READY` | 型態完整，等待突破（L2/L3/L4 全 PASS，L0 BULL） |
| `WAVE_ENTRY` | 突破確認，EntryLock 全 PASS |
| `ENTRY_REDUCED` | L0 WARN（RANGE 市場），縮倉進場 |
| `WAIT_PULLBACK` | L2 BLOCK（price far above MA5） |
| `OVEREXTENDED` | 短期漲幅 > 10% |
| `WAVE_FAILED_WARN` | 跌破 MA5 + 量縮，或 3D < -3%：**通知 owner，建議出場** |
| `REDUCE_RECOMMENDED` | 部分失敗訊號，建議減碼（非全出） |
| `EXIT_RECOMMENDED` | 型態完全失效，建議出場（非強制執行） |

> 所有 `*_RECOMMENDED` 訊號均為**人工審核後決定**，系統不自動執行。

---

## Connection to Existing Modules

| 模組 | 目前職責 | 角色模型接點 |
| --- | --- | --- |
| `data/portfolio/current_holdings.json` | 持倉來源 | 讀取 + 需補 `entry_date` |
| `data/watchlist.json` | 候選宇宙 | `meta.layer` 作為 base_role prior |
| `pipeline/ranking_engine.py` | 排名分數 | ranking_score 作為分類信心輔助 |
| `audit/p1_entry_audit.py` | L0–L4 + P1 | WAVE_ENTRY 條件來源 |
| `decision/lock.py` | 市場狀態 | L0 WARN/PASS → ENTRY_REDUCED |
| `reporting/daily_decision_dashboard.py` | 每日摘要 | 未來加入 base_role / active_role 欄位 |
| `reports/validation/` | 訊號品質回放 | 未來 role-based replay 輸出位置 |

**新增模組（v0.2 實作）：**
```
portfolio/role_classifier.py   — 角色自動分類邏輯（含 base_role / active_role）
data/portfolio/role_map.json   — 分類快照（每日更新）
```

---

## Replay / Validation Implications

- `signal_quality_replay.py` 未來以 `active_role` 為分組維度，取代 Top 3/5/10
- WAVE_SWING 回放：1D/3D/5D 報酬，false negative 門檻 3D +3%
- CORE 回放：20D/60D 報酬（現行腳本不適用，需另建）
- SATELLITE 回放：5D/10D 報酬
- 現有 `signal_quality_replay.py` 結果（WARN）主要反映 WAVE_SWING 排名問題，不影響 CORE 評估

---

## Recommended Next Step

**Role Classifier Implementation v0.1**

建立 `portfolio/role_classifier.py`，每日輸出 `data/portfolio/role_map.json`，包含：
- 每個標的的 `base_role`、`active_role`、`role_confidence`、`role_reason`
- Owner-approved 初始 mapping 優先套用
- `entry_date` 補入後自動啟用持倉天數修正邏輯

**前提：** owner 在 `current_holdings.json` 補入 `entry_date` 後才能完整運作。可先以「無 entry_date」模式實作，日後 entry_date 補入後自動啟用。
