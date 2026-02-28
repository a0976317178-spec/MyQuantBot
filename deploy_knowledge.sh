#!/bin/bash
# ==========================================
# 🚀 一鍵部署腳本 - 知識庫 + 模擬交易系統
# ==========================================
# 使用方式：
#   cd /home/quantbot/MyQuantBot
#   bash deploy_knowledge.sh
# ==========================================

set -e
BOT_DIR="/home/quantbot/MyQuantBot"
cd "$BOT_DIR"

echo "🚀 開始部署知識庫 + 模擬交易系統..."
echo ""

# --- Step 1: 建立 knowledge 目錄 ---
echo "📁 Step 1: 建立知識庫目錄..."
mkdir -p "$BOT_DIR/knowledge"
echo "✅ 完成"

# --- Step 2: 備份原始檔案 ---
echo "📦 Step 2: 備份原始檔案..."
cp bot_listen.py bot_listen.py.bak.$(date +%Y%m%d_%H%M%S)
cp ai_manager.py ai_manager.py.bak.$(date +%Y%m%d_%H%M%S)
echo "✅ 已備份 bot_listen.py 和 ai_manager.py"

# --- Step 3: 確認新檔案存在 ---
echo "📋 Step 3: 確認新檔案..."
for f in knowledge_manager.py paper_trading.py ai_manager_new.py bot_listen_new.py; do
    if [ ! -f "$BOT_DIR/$f" ]; then
        echo "❌ 找不到 $f！請確認檔案已上傳到 $BOT_DIR/"
        echo "   需要的檔案："
        echo "   - knowledge_manager.py （知識庫核心）"
        echo "   - paper_trading.py    （模擬交易）"
        echo "   - ai_manager_new.py   （AI 模組升級版）"
        echo "   - bot_listen_new.py   （Bot 主程式升級版）"
        exit 1
    fi
done
echo "✅ 所有檔案就緒"

# --- Step 4: 替換檔案 ---
echo "🔄 Step 4: 替換檔案..."
cp ai_manager_new.py ai_manager.py
cp bot_listen_new.py bot_listen.py
echo "✅ 已更新 ai_manager.py 和 bot_listen.py"

# --- Step 5: 安裝缺少的套件 ---
echo "📦 Step 5: 確認 Python 套件..."
source /home/quantbot/venv/bin/activate 2>/dev/null || true
pip install yfinance pandas apscheduler python-dotenv pyTelegramBotAPI requests boto3 --quiet 2>/dev/null || \
pip3 install yfinance pandas apscheduler python-dotenv pyTelegramBotAPI requests boto3 --break-system-packages --quiet 2>/dev/null || true
echo "✅ 套件確認完成"

# --- Step 6: 推送到 GitHub ---
echo "📤 Step 6: 推送到 GitHub..."
git add -A
git commit -m "🧠 新增知識庫 + AI 模擬交易系統

新增檔案：
- knowledge_manager.py: 知識庫核心（交易紀錄、策略統計、市場洞察）
- paper_trading.py: AI 自動模擬交易（真實價格、模擬資金）

升級：
- ai_manager.py: 每次呼叫 Claude 自動帶入知識庫經驗
- bot_listen.py: 新增模擬交易、交易紀錄、筆記、洞察等指令

排程：
- 08:45 盤前 AI 選股建倉
- 10:30/12:00 盤中監控停損停利
- 14:00 盤後結算
- 週五 15:30 發週報" 2>/dev/null && echo "✅ Git commit 完成" || echo "⚠️ Git commit 跳過（可能無新變更）"

git push origin main 2>/dev/null && echo "✅ 推送 GitHub 完成！" || echo "⚠️ GitHub 推送失敗，請手動執行 git push"

# --- Step 7: 重啟 Bot ---
echo "🔄 Step 7: 重啟 Bot..."
pm2 restart TG-Bot
sleep 3
echo ""
echo "==========================================  "
echo "🎉 部署完成！"
echo "==========================================  "
echo ""
echo "📱 去 Telegram 試試以下指令："
echo "  模擬        → AI 自動掃描選股並模擬建倉"
echo "  模擬績效    → 查看模擬交易績效"
echo "  觀察清單    → 查看 AI 觀察的股票"
echo "  知識庫      → 查看累積的經驗"
echo "  週報        → 本週交易報告"
echo ""
echo "🤖 AI 每天自動執行："
echo "  08:45 盤前選股建倉"
echo "  10:30 盤中監控"
echo "  12:00 午盤監控"
echo "  14:00 盤後結算"
echo "  週五 15:30 發週報"
echo ""
pm2 logs TG-Bot --lines 5 --nostream
