import os
import requests
from dotenv import load_dotenv

load_dotenv()

def ask_ai(prompt, mode="reader"):
    """
    mode="coder": 使用 Claude 3.5 寫程式
    mode="reader": 使用 Gemini/DeepSeek 讀 Log
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    
    # 根據模式選擇模型
    if mode == "coder":
        model = os.getenv("MODEL_CODER", "anthropic/claude-3.5-sonnet")
    else:
        model = os.getenv("MODEL_LOG_READER", "google/gemini-pro-1.5")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}]
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"❌ AI 調用出錯：{e}"

def analyze_error(error_log):
    """專門給 Gemini 讀 Log 的接口"""
    prompt = f"你現在是 Quant-Bot 的運維專家。請分析以下報錯內容，用繁體中文告知原因及修復建議：\n\n{error_log}"
    return ask_ai(prompt, mode="reader")
