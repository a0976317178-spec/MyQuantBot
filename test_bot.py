import os
import requests
from dotenv import load_dotenv

# 1. 喚醒密碼本，讀取 API Key
load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")

if not api_key:
    print("❌ 找不到 API Key，請檢查 .env 檔案是否有存檔！")
    exit()

# 2. 準備給大腦的指令
print("⏳ 正在呼叫大腦 (Claude 3.5 Sonnet)... 請稍候...")

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# 這裡就是我們對 AI 說的話，我已經幫你寫好 Quant-Bot 的專屬打招呼語了
data = {
    "model": "anthropic/claude-3.5-sonnet",
    "messages": [
        {"role": "user", "content": "你好，Claude！我是小許，我正在開發專屬的 Quant-Bot 準備輔助我做美股與台股的交易。請用繁體中文簡短地跟我打聲招呼，並給我一句鼓勵的話！"}
    ]
}

# 3. 發送請求並印出大腦的回答
try:
    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
    result = response.json()
    
    # 抓取回傳的文字
    ai_message = result['choices'][0]['message']['content']
    
    print("\n====================================")
    print("🤖 AI 大腦回覆：")
    print(ai_message)
    print("====================================")
    print("\n✅ 測試大成功！大腦連線正常，且 API 扣款機制順利運作！")

except Exception as e:
    print(f"\n❌ 發生錯誤，請檢查網路或 API 鑰匙：{e}")