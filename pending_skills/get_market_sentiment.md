# 技能名稱: get_market_sentiment
## 描述: 獲取當前市場的恐懼與貪婪指數（Fear and Greed Index）。
## 需要的套件: requests

### 執行邏輯:
當你需要判斷市場情緒時，請執行以下代碼抓取 API：
```python
import requests
def get_fear_and_greed():
    url = "[https://api.alternative.me/fng/?limit=1](https://api.alternative.me/fng/?limit=1)"
    response = requests.get(url)
    data = response.json()
    return {
        "value": data['data'][0]['value'],
        "classification": data['data'][0]['value_classification']
    }
# print(get_fear_and_greed())
