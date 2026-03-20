import json
from pipeline import run_pipeline
from datetime import datetime

def main():

    data = [
        {
            "title": "輝達新一代 AI 晶片延遲出貨，美系雲端業者下修資本支出預期",
            "content": "根據供應鏈消息指出，輝達（NVIDIA）新架構 AI 處理器因封裝技術調整..."
        },
        {
            "title": "台積電 2 奈米試產進度超前，獲蘋果與聯發科搶先預約產能",
            "content": "台積電（TSMC）最新製程研發取得突破..."
        },
        {
            "title": "HBM 記憶體市場供過於求？三星與海力士展開產能價格戰",
            "content": "隨著記憶體廠商大舉擴張 HBM 產線..."
        },
        {
            "title": "歐盟加強 AI 晶片出口管制審查，不排除納入伺服器零組件",
            "content": "歐盟執行委員會宣布將對先進半導體出口進行更嚴格的合規審查..."
        },
        {
            "title": "美光宣布推出次世代儲存解決方案，瞄準邊際 AI 裝置應用",
            "content": "記憶體大廠美光（Micron）今日發表全新高效能 LPDDR5X 記憶體..."
        }
    ]

    result = run_pipeline(data)

    print("🧠 Narrative:", result["narrative"])
    print("📤 Signal:", result["signal"])

if __name__ == "__main__":
    main()
