# 技能名稱: get_stock_data
## 描述: 獲取指定股票（美股或台股）的即時價格與歷史 K 線數據。
## 需要的套件: yfinance

### 執行邏輯:
當你需要查詢股價時，請使用 python 執行以下代碼：
```python
import yfinance as yf
def get_price(ticker):
    stock = yf.Ticker(ticker)
    # 獲取最近一天的數據
    hist = stock.history(period="1d")
    return hist[['Open', 'High', 'Low', 'Close', 'Volume']].to_dict()

# 範例：查詢台積電 (2330.TW) 或 蘋果 (AAPL)
# print(get_price("2330.TW"))
