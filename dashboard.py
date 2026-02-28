import streamlit as st
import pandas as pd
import time
import os
from ai_manager import ask_ai, analyze_error

# --- 1. 安全設定：登入密碼鎖 ---
def check_password():
    """驗證使用者是否為小許本人"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.title("🛡️ Quant-Bot 安全登入")
        password = st.text_input("請輸入管理員密碼：", type="password")
        if st.button("登入"):
            if password == "hsukai666": # 👈 小許，這裡可以改掉你的專屬密碼！
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("❌ 密碼錯誤，拒絕存取。")
        return False
    return True

# --- 2. 介面與功能實作 ---
if check_password():
    st.set_page_config(page_title="OpenClaw 監控中心", layout="wide")
    
    # 頂部狀態列
    st.title("🚀 OpenClaw 量化機器人監控中心")
    st.sidebar.header("系統選單")
    status_placeholder = st.sidebar.empty()
    status_placeholder.success("🟢 系統連線中")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("🧠 Agent 思考過程與操作紀錄")
        # 模擬影片中 Agent 的思考對話
        chat_container = st.container(height=400, border=True)
        
        # 這裡未來會從你的資料庫(DuckDB/R2)讀取真實Log
        mock_logs = [
            {"time": "08:30:01", "role": "Agent", "msg": "正在掃描 VOO 與 QQQ 的均線趨勢..."},
            {"time": "08:30:05", "role": "System", "msg": "獲取 yfinance 數據成功。"},
            {"time": "08:30:10", "role": "Agent", "msg": "檢測到黃金交叉，考慮進行 DCA 操作。"}
        ]
        
        for log in mock_logs:
            chat_container.chat_message(log["role"]).write(f"**[{log['time']}]** {log['msg']}")

    with col2:
        st.subheader("🤖 運維專家 (Gemini)")
        if st.button("請 Gemini 分析目前系統健康度"):
            with st.spinner("Gemini 正在讀取日誌..."):
                # 這邊直接呼叫你設定好的省錢 Reader 模式
                report = ask_ai("請根據目前的 mock_logs 狀態，給小許一個簡短的投資組合健康回報。", mode="reader")
                st.info(report)

    # 數據可視化區塊
    st.divider()
    st.subheader("📈 即時行情監控")
    # 這裡放一個簡單的示意圖表，未來會對接你的數據
    chart_data = pd.DataFrame({
        "VOO": [500, 505, 502, 508, 510],
        "QQQ": [440, 442, 441, 445, 448]
    })
    st.line_chart(chart_data)

    # 底部控制台
    st.sidebar.divider()
    if st.sidebar.button("🚨 緊急強制停機 (Kill Switch)"):
        st.sidebar.warning("已發送停機指令至 VPS...")
        # 這裡會結合 pm2 stop
