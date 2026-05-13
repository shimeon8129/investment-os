# Role Classifier Report — 2026-05-11

**產生時間：** 2026-05-11T01:07:11.738340
**Seed Map 版本：** v0.1
**持倉資料截至：** 2026-05-07

---

## 角色分佈

### base_role

| 角色 | 筆數 |
| --- | --- |
| CORE | 7 |
| CORE_ETF | 2 |
| SATELLITE | 11 |
| WAVE_SWING | 16 |

### active_role

| 角色 | 筆數 |
| --- | --- |
| CORE | 6 |
| CORE_ETF | 2 |
| SATELLITE | 11 |
| WAVE_SWING | 17 |

### 信心度分佈

| 信心度 | 筆數 |
| --- | --- |
| HIGH | 7 |
| LOW | 6 |
| MEDIUM | 23 |

---

## 持倉分類（current_holdings）

共 7 筆持倉

| Ticker | 名稱 | base_role | active_role | 信心度 | entry_date | 來源 |
| --- | --- | --- | --- | --- | --- | --- |
| 009816 | 凱基台灣TOP50 | CORE_ETF | CORE_ETF | HIGH | UNKNOWN | owner_seed_mapping / current_holding / entry_date_missing |
| 00992A | 主動群益科技創新 | CORE_ETF | CORE_ETF | HIGH | UNKNOWN | owner_seed_mapping / current_holding / entry_date_missing |
| 2330.TW | 台積電 | CORE | CORE | HIGH | UNKNOWN | owner_seed_mapping / current_holding / entry_date_missing |
| 2345.TW | 智邦 | CORE | SATELLITE | HIGH | UNKNOWN | owner_seed_mapping / current_holding / entry_date_missing |
| 2408.TW | 南亞科 | SATELLITE | SATELLITE | HIGH | UNKNOWN | owner_seed_mapping / current_holding / entry_date_missing |
| 3711.TW | 日月光投控 | CORE | CORE | HIGH | UNKNOWN | owner_seed_mapping / current_holding / entry_date_missing |
| 6830.TW | 汎銓 | SATELLITE | WAVE_SWING | HIGH | UNKNOWN | owner_seed_mapping / current_holding / entry_date_missing |

### entry_date = UNKNOWN（7 筆持倉）

- 009816 凱基台灣TOP50
- 00992A 主動群益科技創新
- 2330.TW 台積電
- 2345.TW 智邦
- 2408.TW 南亞科
- 3711.TW 日月光投控
- 6830.TW 汎銓

---

## Seed Mapping 套用（7 筆）

| Ticker | 名稱 | base_role | active_role | intent | upgrade_path |
| --- | --- | --- | --- | --- | --- |
| 009816 | 凱基台灣TOP50 | CORE_ETF | CORE_ETF | — | — |
| 00992A | 主動群益科技創新 | CORE_ETF | CORE_ETF | — | — |
| 2330.TW | 台積電 | CORE | CORE | — | — |
| 2345.TW | 智邦 | CORE | SATELLITE | HOLD_OR_ADD_ON_PULLBACK | WAVE_SWING |
| 2408.TW | 南亞科 | SATELLITE | SATELLITE | — | — |
| 3711.TW | 日月光投控 | CORE | CORE | — | — |
| 6830.TW | 汎銓 | SATELLITE | WAVE_SWING | — | — |

---

## Watchlist Prior 分類（23 筆非持倉）

| Ticker | 名稱 | base_role | active_role | 信心度 |
| --- | --- | --- | --- | --- |
| 2059.TW | 川湖 | SATELLITE | SATELLITE | MEDIUM |
| 2308.TW | 台達電 | SATELLITE | SATELLITE | MEDIUM |
| 2317.TW | 鴻海 | WAVE_SWING | WAVE_SWING | MEDIUM |
| 2337.TW | 旺宏 | WAVE_SWING | WAVE_SWING | MEDIUM |
| 2376.TW | 技嘉 | WAVE_SWING | WAVE_SWING | MEDIUM |
| 2382.TW | 廣達 | WAVE_SWING | WAVE_SWING | MEDIUM |
| 2449.TW | 京元電子 | WAVE_SWING | WAVE_SWING | MEDIUM |
| 2454.TW | 聯發科 | CORE | CORE | MEDIUM |
| 3017.TW | 奇鋐 | SATELLITE | SATELLITE | MEDIUM |
| 3081.TWO | 聯亞 | SATELLITE | SATELLITE | MEDIUM |
| 3105.TWO | 穩懋 | SATELLITE | SATELLITE | MEDIUM |
| 3231.TW | 緯創 | WAVE_SWING | WAVE_SWING | MEDIUM |
| 3260.TW | 威剛 | WAVE_SWING | WAVE_SWING | MEDIUM |
| 3324.TW | 雙鴻 | SATELLITE | SATELLITE | MEDIUM |
| 3363.TWO | 上詮 | SATELLITE | SATELLITE | MEDIUM |
| 3661.TWO | 世芯-KY | CORE | CORE | MEDIUM |
| 4979.TWO | 華星光 | SATELLITE | SATELLITE | MEDIUM |
| 6187.TWO | 萬潤 | CORE | CORE | MEDIUM |
| 6515.TWO | 穎崴 | WAVE_SWING | WAVE_SWING | MEDIUM |
| 6669.TWO | 緯穎 | WAVE_SWING | WAVE_SWING | MEDIUM |
| 6781.TW | AES-KY | SATELLITE | SATELLITE | MEDIUM |
| 7769.TWO | 鴻勁 | CORE | CORE | MEDIUM |
| 8299.TWO | 群聯 | WAVE_SWING | WAVE_SWING | MEDIUM |

---

## 快照候選（非 watchlist，6 筆）

| Ticker | 名稱 | active_role | 信心度 | Score |
| --- | --- | --- | --- | --- |
| 2356.TW | 英業達 | WAVE_SWING | LOW | 145.534 |
| 2464.TW | 盟立 | WAVE_SWING | LOW | 151.4 |
| 3680.TWO | 家登 | WAVE_SWING | LOW | 124.0 |
| 3706.TW | 神達 | WAVE_SWING | LOW | 108.2 |
| 6147.TWO | 頎邦 | WAVE_SWING | LOW | 108.2 |
| 6257.TW | 矽格 | WAVE_SWING | LOW | 108.2 |

---

## 未知 / 不完整分類（0 筆）

（無）

---

## 開放問題

1. `entry_date` 全部為 UNKNOWN（待 owner 從券商後台補入後重新執行）
2. `2408 南亞科` active_role=SATELLITE — owner 確認中
3. 角色分類目前未接入 daily trading decisions（v0.2 規劃）
4. Watchlist 外的 snapshot 候選暫以 WAVE_SWING 分類，準確度 LOW

---

*分析腳本：`portfolio/role_classifier.py`*
*無任何持倉或交易資料被修改。*
*報告產生：2026-05-11 01:07:11*