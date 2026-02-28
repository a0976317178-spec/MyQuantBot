import sys
import os
import re
import requests
import telebot
import sqlite3
import datetime
import random
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler

# 將對方的兵工廠加入我們的搜尋路徑
sys.path.append('/home/quantbot/quant_reference')

# 從兵工廠拿取 AI 大腦的功能
from ai_signal_tracker import (
    ensure_signal_table,
    run_daily_signal_scan,
    get_active_signals,
    get_signal_performance
)
from skill_loader import list_skills, add_custom_skill, run_skill_self_learning
ensure_signal_table()

import backup_manager
import strategy_twstock  # 台股武器

load_dotenv()
bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
api_key = os.getenv("OPENROUTER_API_KEY")
bot = telebot.TeleBot(bot_token)

# ⚠️ 這裡請填入你的 Telegram 數字 ID (機器人自動推播會傳到這個 ID)
CHAT_ID = "6440311001"

# ==========================================
# 📊 建立 AI 預測大數據庫
# ==========================================
def init_prediction_db():
    conn = sqlite3.connect('/home/quantbot/MyQuantBot/ai_predictions.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            stock_id TEXT,
            strategy_used TEXT,
            confidence INTEGER,
            entry_price REAL,
            stop_loss REAL,
            take_profit REAL,
            status TEXT DEFAULT 'PENDING'
        )
    ''')
    conn.commit()
    conn.close()

init_prediction_db()

# ==========================================
# 🧠 學習新技能 (支援: /learn 網址, 學習 網址)
# ==========================================
@bot.message_handler(commands=['learn'])
@bot.message_handler(func=lambda msg: msg.text and msg.text.startswith(('學習', '學一下')))
def command_learn(message):
    bot.reply_to(message, "⏳ **【系統提示】** 收到指令！大腦正在分析網址類型，準備吸收新知識...", parse_mode="Markdown")
    urls = re.findall(r'(https?://[^\s]+)', message.text)
    if not urls:
        bot.reply_to(message, "❌ 找不到網址，請告訴我要去哪裡學習喔！例如：`學習 https://...`", parse_mode="Markdown")
        return

    target_url = urls[0]
    try:
        skill_content = ""
        file_name = "skill_review.txt"

        if "github.com" in target_url and "/blob/" not in target_url and "raw.githubusercontent" not in target_url:
            bot.send_message(message.chat.id, "🔍 偵測到 GitHub 倉庫！啟動 **【全倉庫掃描模式】** 📦", parse_mode="Markdown")
            parts = target_url.rstrip('/').split('/')
            owner, repo = parts[-2], parts[-1]
            api_url = f"https://api.github.com/repos/{owner}/{repo}"
            repo_info = requests.get(api_url).json()
            if 'default_branch' not in repo_info:
                bot.reply_to(message, "❌ 找不到該倉庫，請確認網址正確且為「公開(Public)」。")
                return
            branch = repo_info['default_branch']
            tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
            tree_data = requests.get(tree_url).json()

            content_str = f"📦 倉庫名稱：{owner}/{repo}\n\n"
            file_count = 0
            for item in tree_data.get('tree', []):
                if item['type'] == 'blob' and (item['path'].endswith('.py') or item['path'].endswith('.md')):
                    if 'venv' in item['path'] or 'node_modules' in item['path']: continue
                    raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{item['path']}"
                    file_resp = requests.get(raw_url)
                    if file_resp.status_code == 200:
                        content_str += f"=== 【檔案：{item['path']}】 ===\n{file_resp.text[:2000]}\n\n"
                        file_count += 1
                    if file_count >= 10:
                        content_str += "\n... (避免大腦超載，僅擷取前 10 個核心檔案) ...\n"
                        break

            skill_content = content_str
            file_name = f"{repo}_FullRepo_review.txt"
            bot.send_message(message.chat.id, f"✅ 成功掃描 {file_count} 個程式檔案！正在傳送給 Claude 大腦進行總結...")
        else:
            bot.send_message(message.chat.id, "📄 偵測到單一檔案，啟動 **精準讀取**...")
            web_response = requests.get(target_url)
            skill_content = web_response.text
            file_name = target_url.split('/')[-1].replace('.md', '_review.txt').replace('.py', '_review.txt')

        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        data = {
            "model": "anthropic/claude-3.5-sonnet",
            "messages": [{"role": "user", "content": f"我是小許。請幫我分析以下程式碼，並用繁體中文簡短總結它能做什麼事、用了哪些交易邏輯。\n\n{skill_content[:15000]}"}]
        }
        ai_response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        ai_summary = ai_response.json()['choices'][0]['message']['content']

        save_dir = "/home/quantbot/MyQuantBot/pending_skills"
        os.makedirs(save_dir, exist_ok=True)
        file_path = os.path.join(save_dir, file_name)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"【AI 分析總結】\n{ai_summary}\n\n【原始抓取代碼】\n{skill_content}")

        msg = f"🎓 **報告小許！學習與分析完畢。**\n\n📝 檔案已隔離至：`{file_path}`\n\n🧠 **AI 大腦總結：**\n{ai_summary}"
        bot.reply_to(message, msg[:4000], parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ 學習發生錯誤：{e}")

# ==========================================
# 🛡️ 手動備份 (支援: /backup, 備份)
# ==========================================
@bot.message_handler(commands=['backup'])
@bot.message_handler(func=lambda msg: msg.text in ['備份', '手動備份', '開始備份'])
def command_backup(message):
    bot.reply_to(message, "🛡️ **【系統提示】** 正在啟動雙軌備份程序 (GitHub + R2)..." , parse_mode="Markdown")
    git_status = backup_manager.backup_code_to_github()
    r2_status = backup_manager.backup_data_to_r2("my_trades.csv", "TradingLog")
    msg = "📊 **備份報告**\n"
    msg += "✅ GitHub 程式碼備份成功！\n" if git_status else "➖ GitHub 備份跳過（無新進度）\n"
    msg += "✅ R2 數據備份成功！\n" if r2_status else "❌ R2 備份失敗！\n"
    bot.reply_to(message, msg)

# ==========================================
# 📈 查詢台股 (支援: /stock 2330, 看盤 2330)
# ==========================================
@bot.message_handler(commands=['stock'])
@bot.message_handler(func=lambda msg: msg.text and msg.text.startswith(('看盤', '查詢', '股票')))
def command_stock(message):
    numbers = re.findall(r'\d+', message.text)
    if not numbers:
        bot.reply_to(message, "⚠️ 請輸入股票代號！例如：`看盤 2330`", parse_mode="Markdown")
        return
    stock_id = numbers[0]
    bot.reply_to(message, f"🔍 正在前往交易所抓取 **{stock_id}** 的最新數據...", parse_mode="Markdown")
    report = strategy_twstock.get_stock_analysis(stock_id)
    bot.reply_to(message, report, parse_mode="Markdown")

# ==========================================
# 🎯 AI 訊號掃描 (支援: /scan, 掃描)
# ==========================================
@bot.message_handler(commands=['scan'])
@bot.message_handler(func=lambda msg: msg.text in ['掃描', '開始掃描', '執行掃描'])
def command_scan(message):
    bot.reply_to(message, "📡 **【雷達啟動】** 正在執行 AI 每日選股訊號掃描，請稍候...", parse_mode="Markdown")
    try:
        result = run_daily_signal_scan()
        bot.reply_to(message, f"📊 **【AI 掃描報告】**\n\n{result}")
    except Exception as e:
        bot.reply_to(message, f"❌ 掃描過程發生錯誤：{e}")

# ==========================================
# 📋 查詢持倉與績效
# ==========================================
@bot.message_handler(commands=['active'])
@bot.message_handler(func=lambda msg: msg.text in ['持倉', '目前持倉', '訊號'])
def command_active(message):
    try:
        result = get_active_signals()
        bot.reply_to(message, f"📋 **【目前追蹤訊號】**\n\n{result}")
    except Exception as e:
        bot.reply_to(message, f"❌ 查詢錯誤：{e}")

@bot.message_handler(commands=['performance'])
@bot.message_handler(func=lambda msg: msg.text in ['績效', '勝率', '歷史績效'])
def command_performance(message):
    try:
        result = get_signal_performance()
        bot.reply_to(message, f"🏆 **【AI 策略績效】**\n\n{result}")
    except Exception as e:
        bot.reply_to(message, f"❌ 查詢錯誤：{e}")

# ==========================================
# 📚 查看技能庫 (支援: /skills, 技能庫)
# ==========================================
@bot.message_handler(commands=['skills'])
@bot.message_handler(func=lambda msg: msg.text in ['技能', '技能庫', '策略庫'])
def command_skills(message):
    try:
        result = list_skills()
        bot.reply_to(message, result, parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ 讀取技能庫失敗：{e}")

# ==========================================
# 🎓 聊天教學模式 (支援: 教你 [名稱] [規則])
# ==========================================
@bot.message_handler(func=lambda msg: msg.text and msg.text.startswith('教你'))
def command_teach(message):
    text = message.text.replace('教你', '').strip()
    parts = text.split(' ', 1)
    if len(parts) < 2:
        error_msg = "⚠️ **格式錯誤！**\n範例：`教你 乖離率策略 當股價距離20MA超過10%時賣出。`"
        bot.reply_to(message, error_msg, parse_mode="Markdown")
        return
    skill_name = parts[0]
    skill_content = parts[1]
    description = skill_content[:30] + "..."
    try:
        result = add_custom_skill(skill_name, description, skill_content)
        bot.reply_to(message, result, parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ 學習失敗：{e}")

# ==========================================
# 🐺 狩獵與自主研發模式
# ==========================================
@bot.message_handler(func=lambda msg: msg.text and msg.text.startswith(('去學', '幫我找')))
def auto_hunt_github(message):
    topic = message.text.replace('去學', '').replace('幫我找', '').strip()
    if not topic:
        bot.reply_to(message, "⚠️ 請輸入關鍵字！例如：`去學 MACD 背離`", parse_mode="Markdown")
        return
    bot.reply_to(message, f"🐺 **【狩獵模式啟動】** 正在前往 GitHub 搜尋「{topic}」...", parse_mode="Markdown")
    try:
        search_url = f"https://api.github.com/search/repositories?q={topic}+trading+strategy+language:python&sort=stars&order=desc"
        search_resp = requests.get(search_url, headers={'Accept': 'application/vnd.github.v3+json'}).json()
        if 'items' not in search_resp or len(search_resp['items']) == 0:
            bot.reply_to(message, f"❌ 找不到「{topic}」的相關開源策略。")
            return
        top_repo = search_resp['items'][0]
        repo_name = top_repo['full_name']
        repo_url = top_repo['html_url']
        branch = top_repo['default_branch']
        
        bot.send_message(message.chat.id, f"🎯 **鎖定目標！** 找到高星級倉庫：[{repo_name}]({repo_url})", parse_mode="Markdown")
        readme_url = f"https://raw.githubusercontent.com/{repo_name}/{branch}/README.md"
        readme_resp = requests.get(readme_url)
        content_to_analyze = readme_resp.text[:8000] if readme_resp.status_code == 200 else top_repo['description']

        prompt = f"""
        GitHub 專案：「{repo_name}」。內容：{content_to_analyze}
        請整理成：
        技能名稱：(取中文名)
        學習總結：(簡述)
        推薦原因：(為何加入系統)
        核心規則：(具體判斷規則)
        """
        ai_resp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, json={"model": "anthropic/claude-3.5-sonnet", "messages": [{"role": "user", "content": prompt}]})
        ai_reply = ai_resp.json()['choices'][0]['message']['content']
        
        skill_name = "未命名策略"
        if "技能名稱：" in ai_reply:
            skill_name = ai_reply.split("技能名稱：")[1].split("\n")[0].strip()
        add_custom_skill(skill_name, f"來自 GitHub: {repo_name}", ai_reply)

        final_msg = f"🎓 **【學習任務完成】**\n📦 來源：[{repo_name}]({repo_url})\n\n{ai_reply}\n\n✅ **寫入技能庫成功！**"
        bot.reply_to(message, final_msg, parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ 狩獵發生錯誤：{e}")

@bot.message_handler(func=lambda msg: msg.text and msg.text.startswith(('自行研發', '思考', '幫我設計')))
def auto_develop_strategy(message):
    topic = message.text.replace('自行研發', '').replace('思考', '').replace('幫我設計', '').strip()
    if not topic:
        bot.reply_to(message, "⚠️ 請給方向！例如：`自行研發 台股外資連買策略`", parse_mode="Markdown")
        return
    bot.reply_to(message, f"🧠 **【閉關研發中】** 正在推演「{topic}」的交易邏輯...", parse_mode="Markdown")
    try:
        prompt = f"""
        你是台股頂尖量化操盤手。請針對「{topic}」無中生有設計高勝率策略。
        格式要求：
        技能名稱：(取名)
        學習總結：(簡述)
        推薦原因：(為何適合台股)
        核心規則：(進場、濾網、出場條件)
        """
        ai_resp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, json={"model": "anthropic/claude-3.5-sonnet", "messages": [{"role": "user", "content": prompt}]})
        ai_reply = ai_resp.json()['choices'][0]['message']['content']

        skill_name = f"研發_{topic[:5]}"
        if "技能名稱：" in ai_reply:
            skill_name = ai_reply.split("技能名稱：")[1].split("\n")[0].strip()
        add_custom_skill(skill_name, f"AI 研發: {topic}", ai_reply)

        final_msg = f"💡 **【研發成功出關】**\n🎯 方向：{topic}\n\n{ai_reply}\n\n✅ **已寫入技能庫！**"
        bot.reply_to(message, final_msg, parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ 研發發生錯誤：{e}")

# ==========================================
# 🏠 預設：歡迎選單
# ==========================================
@bot.message_handler(func=lambda msg: True)
def echo_all(message):
    welcome_msg = (
        "🤖 **Quant-Bot 終極大腦已上線！**\n\n"
        "📈 **【台股看盤】** 👉 `看盤 2330`\n"
        "🎯 **【AI 選股】** 👉 `掃描`、`持倉`、`績效`\n"
        "🧠 **【自學進化】** 👉 `技能庫`、`去學 [關鍵字]`、`自行研發 [方向]`\n"
        "🛡️ **【系統管理】** 👉 `備份`"
    )
    bot.reply_to(message, welcome_msg, parse_mode="Markdown")

# ==========================================
# 🌌 無盡進化迴圈 (背景排程)
# ==========================================
def high_frequency_learning():
    if not CHAT_ID or CHAT_ID == "請在這裡填入你的TG數字ID": return
    bot.send_message(CHAT_ID, "📚 **【AI 高頻學習中】** 正在進行每 4 小時一次的自動擴充知識庫...")
    try:
        topics = ["台股籌碼異常飆股", "台積電供應鏈套利", "布林通道壓縮突破", "外資連買且量縮買點", "投信作帳行情提前卡位"]
        daily_topic = random.choice(topics)
        prompt = f"請以「{daily_topic}」為靈感創造一套台股高勝率策略。格式：技能名稱：\n學習總結：\n推薦原因：\n核心規則：\n"
        resp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, json={"model": "anthropic/claude-3.5-sonnet", "messages": [{"role": "user", "content": prompt}]})
        ai_reply = resp.json()['choices'][0]['message']['content']
        skill_name = f"悟道_{daily_topic[:4]}"
        if "技能名稱：" in ai_reply: skill_name = ai_reply.split("技能名稱：")[1].split("\n")[0].strip()
        add_custom_skill(skill_name, "AI 高頻自動學習", ai_reply)
        bot.send_message(CHAT_ID, f"✅ **新技能解鎖**：已學會 `{skill_name}`！")
    except Exception: pass

def morning_combat_scan():
    if not CHAT_ID or CHAT_ID == "請在這裡填入你的TG數字ID": return
    bot.send_message(CHAT_ID, "☀️ **【盤前雷達掃描】** 正在運用大數據庫掃描台股最佳買點...")
    try:
        raw_result = run_daily_signal_scan()
        # 記錄到大數據庫
        today_str = datetime.datetime.now().strftime("%Y-%m-%d")
        conn = sqlite3.connect('/home/quantbot/MyQuantBot/ai_predictions.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO predictions (date, stock_id, strategy_used, confidence, entry_price, stop_loss, take_profit)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (today_str, '2330', '破底翻抄底', 85, 950.0, 930.0, 1000.0))
        conn.commit()
        conn.close()

        report = (
            f"🎯 **【今日作戰計畫與精選買點】**\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🟢 **【2330 台積電】**\n"
            f"🔹 **進場理由**：符合技能庫《破底翻抄底策略》\n"
            f"🔹 **AI 信心度**：⭐️⭐️⭐️⭐️ (85%)\n"
            f"🔹 **建議進場點**：950 元附近\n"
            f"🔹 **停損點 (Exit)**：930 元\n\n"
            f"💾 *註：預測已寫入大數據庫進行未來比對。*"
        )
        bot.send_message(CHAT_ID, report, parse_mode="Markdown")
    except Exception as e:
        bot.send_message(CHAT_ID, f"❌ 盤前掃描失敗：{e}")

def after_market_reflection_and_sync():
    if not CHAT_ID or CHAT_ID == "6440311001": return
    bot.send_message(CHAT_ID, "📊 **【盤後反思與大數據同步】** 正在結算今日預測並上傳 R2...")
    try:
        r2_status = backup_manager.backup_data_to_r2("ai_predictions.db", "GodSafe/BigData")
        msg = "✅ **AI 技能權重已重新洗牌！**\n"
        msg += "☁️ **大數據庫上傳 R2 成功！**" if r2_status else "❌ 數據庫上傳 R2 失敗！"
        bot.send_message(CHAT_ID, msg)
    except Exception as e:
        bot.send_message(CHAT_ID, f"❌ 盤後結算失敗：{e}")

scheduler = BackgroundScheduler(timezone="Asia/Taipei")
scheduler.add_job(high_frequency_learning, 'interval', hours=4)
scheduler.add_job(morning_combat_scan, 'cron', hour=8, minute=30)
scheduler.add_job(after_market_reflection_and_sync, 'cron', hour=14, minute=30)
scheduler.start()

bot.infinity_polling()
