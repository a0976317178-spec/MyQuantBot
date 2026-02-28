import os
import re
import requests
import telebot
from dotenv import load_dotenv
import backup_manager

# 1. 讀取密碼本 (包含 TG 與 OpenRouter 的 Key)
load_dotenv()
bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
api_key = os.getenv("OPENROUTER_API_KEY")

bot = telebot.TeleBot(bot_token)

# ==========================================
# 指令 1：學習新技能 (/learn)
# ==========================================
@bot.message_handler(commands=['learn'])
def command_learn(message):
    # 先安撫老闆，表示開始工作了
    bot.reply_to(message, "⏳ 收到指令！大腦正在前往抓取網頁內容與分析，請稍候...")

    # 用正則表達式自動找出老闆丟的網址
    urls = re.findall(r'(https?://[^\s]+)', message.text)
    if not urls:
        bot.reply_to(message, "❌ 找不到網址，請在指令中提供技能的網址！")
        return

    target_url = urls[0]

    try:
        # 【動作 1：去網站抓資料】
        web_response = requests.get(target_url)
        skill_content = web_response.text

        # 【動作 2：呼叫大腦分析】
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "anthropic/claude-3.5-sonnet",
            "messages": [
                {"role": "user", "content": f"我是小許。請幫我分析以下 OpenClaw 技能的 Markdown 代碼，並用繁體中文簡短總結它具體能做什麼事。代碼如下：\n\n{skill_content[:3000]}"}
            ]
        }
        ai_response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        ai_summary = ai_response.json()['choices'][0]['message']['content']

        # 【動作 3：安全檢疫與存檔】
        save_dir = "/home/quantbot/MyQuantBot/pending_skills"
        os.makedirs(save_dir, exist_ok=True)

        file_name = target_url.split('/')[-1].replace('.md', '_review.txt')
        file_path = os.path.join(save_dir, file_name)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"【AI 分析總結】\n{ai_summary}\n\n")
            f.write("【原始技能代碼】\n")
            f.write(skill_content)

        # 【動作 4：回報 TG】
        bot.reply_to(message, f"✅ 報告小許！技能已成功抓取並分析完畢。\n\n📝 檔案已安全隔離至：\n`{file_path}`\n\n🧠 大腦總結：\n{ai_summary}", parse_mode="Markdown")

    except Exception as e:
        bot.reply_to(message, f"❌ 學習過程中發生錯誤：{e}")

# ==========================================
# 指令 2：手動啟動雙軌備份 (/backup)
# ==========================================
@bot.message_handler(commands=['backup'])
def command_backup(message):
    bot.reply_to(message, "⏳ 收到小許的指令！正在啟動雙軌備份程序 (GitHub + R2)...")
    
    # 執行 GitHub 備份
    git_status = backup_manager.backup_code_to_github()
    
    # 執行 R2 備份 (備份我們剛才建立的假交易紀錄 my_trades.csv)
    r2_status = backup_manager.backup_data_to_r2("my_trades.csv", "TradingLog")
    
    msg = "📊 **備份報告**\n"
    msg += "✅ GitHub 程式碼備份成功！\n" if git_status else "❌ GitHub 備份失敗（可能沒新進度）\n"
    msg += "✅ R2 數據備份成功！\n" if r2_status else "❌ R2 備份失敗！\n"
    
    bot.reply_to(message, msg)

# ==========================================
# 預設對話狀態
# ==========================================
@bot.message_handler(func=lambda msg: True)
def echo_all(message):
    welcome_msg = (
        "🤖 我目前在待命狀態！\n\n"
        "你可以對我下達以下指令：\n"
        "👉 `/learn [網址]` - 讓我學習新技能\n"
        "👉 `/backup` - 立即將交易數據備份至 R2"
    )
    bot.reply_to(message, welcome_msg, parse_mode="Markdown")

print("👂 Quant-Bot 已經裝上耳朵與大腦，正在 Telegram 監聽你的指令...")
bot.infinity_polling()
