import time
import requests
import os
from dotenv import load_dotenv

# 讀取密碼本
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_alert(message):
    """發送緊急通知到小許的手機"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": message})
    except:
        pass # 如果連 TG 都壞了就略過，避免程式死當

def run_openclaw_task():
    """這裡未來會放你呼叫 OpenClaw 抓資料、分析 VOO/QQQ 的主邏輯"""
    # 這裡我們故意寫一個錯誤，來測試熔斷機制會不會生效！
    print("🧠 OpenClaw 嘗試分析市場中...")
    #raise Exception("API 呼叫超時或大腦語無倫次！") 

def main():
    MAX_FAILS = 3     # 容忍上限：連續錯 3 次
    fail_count = 0    # 錯誤計數器

    while True:
        try:
            print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] 🤖 Quant-Bot 啟動新一輪任務...")
            
            run_openclaw_task() # 執行大腦邏輯
            
            fail_count = 0 # 如果上面順利執行完沒有報錯，計數器就歸零！
            time.sleep(60) # 休息 60 秒再跑下一次迴圈

        except Exception as e:
            fail_count += 1
            error_msg = f"⚠️ 警告：機器人發生錯誤 ({fail_count}/{MAX_FAILS})\n錯誤內容: {e}"
            print(error_msg)
            
            if fail_count >= MAX_FAILS:
                fatal_msg = "🚨 【熔斷機制觸發】連續報錯達 3 次！為保護 API 餘額，機器人已強制拔除電源休眠。請小許盡速上 VPS 檢查！"
                print(fatal_msg)
                send_telegram_alert(fatal_msg)
                break # 🏆 關鍵指令：強制跳出死迴圈，程式完全停止運作，不再扣錢！

            time.sleep(10) # 如果還沒達到 3 次，先冷靜 10 秒再重試

if __name__ == "__main__":
    main()
