import os
import requests
from dotenv import load_dotenv

# 讀取密碼本
load_dotenv()
bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")

# 1. 先去跟你的機器人說聲嗨
print("⏳ 準備發送 Telegram 訊息...")

# 2. 發送的內容
message = "✅ 報告小許：Quant-Bot 的大腦與嘴巴已在本地端成功連線！我已經準備好隨時登陸 VPS 伺服器了！"

# 3. 透過 Telegram API 發送
url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
data = {"chat_id": chat_id, "text": message}

try:
    response = requests.post(url, data=data)
    if response.json().get('ok'):
        print("🎉 發送成功！快去看你的手機 Telegram！")
    else:
        print(f"❌ 發送失敗，錯誤訊息：{response.json()}")
except Exception as e:
    print(f"❌ 發生錯誤：{e}")