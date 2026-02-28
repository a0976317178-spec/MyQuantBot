import yfinance as yf
import pandas as pd

def get_stock_analysis(stock_id):
    try:
        # 台灣上市股票通常字尾是 .TW
        ticker = f"{stock_id}.TW"
        stock = yf.Ticker(ticker)
        
        # 抓取最近 30 天的歷史資料
        hist = stock.history(period="30d")
        
        if hist.empty:
            return f"❌ 找不到股票代號 {stock_id} 的資料，請確認代號是否正確。"

        # 取得最新收盤價與漲跌幅
        latest_close = hist['Close'].iloc[-1]
        prev_close = hist['Close'].iloc[-2]
        change_pct = ((latest_close - prev_close) / prev_close) * 100

        # 計算均線
        hist['5MA'] = hist['Close'].rolling(window=5).mean()
        hist['20MA'] = hist['Close'].rolling(window=20).mean()
        
        ma5 = hist['5MA'].iloc[-1]
        ma20 = hist['20MA'].iloc[-1]

        # 判斷趨勢
        trend = "📈 多頭排列 (5MA > 20MA，適合做多)" if ma5 > ma20 else "📉 空頭排列 (5MA < 20MA，請小心)"

        # 準備回報給 Telegram 的訊息
        report = f"📊 **【{stock_id}】 個股速報**\n"
        report += f"🔹 最新收盤價：**{latest_close:.2f}** (漲跌: {change_pct:.2f}%)\n"
        report += f"🔹 5日均線 (5MA)：{ma5:.2f}\n"
        report += f"🔹 20日均線 (20MA)：{ma20:.2f}\n"
        report += f"💡 **目前趨勢：{trend}**\n"
        
        return report
    
    except Exception as e:
        return f"❌ 抓取資料時發生錯誤：{e}"
