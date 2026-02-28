import os
import subprocess
import boto3
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()

# ==========================================
# 任務 1：備份程式碼到 GitHub
# ==========================================
def backup_code_to_github():
    print("🔄 開始備份程式碼到 GitHub...")
    try:
        subprocess.run(["git", "add", "*.py", "*.md", "requirements.txt"], check=True)
        subprocess.run(["git", "commit", "-m", "🤖 自動備份：更新策略與程式碼"], check=True)
        subprocess.run(["git", "push"], check=True)
        print("✅ GitHub 程式碼備份完成！")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ GitHub 備份失敗（可能沒有新變更，或尚未初始化 Git）。")
        return False

# ==========================================
# 任務 2：【大數據專用】精確到秒的 R2 備份
# ==========================================
def backup_data_to_r2(local_file_path, data_category):
    print(f"🔄 準備將 {data_category} 備份至 Cloudflare R2...")
    
    if not os.path.exists(local_file_path):
        print(f"⚠️ 找不到本地檔案 {local_file_path}，跳過備份。")
        return False

    # 1. 取得精確的台灣時間 (UTC+8)
    tw_tz = timezone(timedelta(hours=8))
    now = datetime.now(tw_tz)
    
    # 2. 建立大數據檔名 (格式: YYYYMMDD_HHMMSS_分類.csv)
    time_stamp = now.strftime("%Y%m%d_%H%M%S")
    
    # 3. 建立 R2 裡面的資料夾結構 (格式: 分類/YYYY/MM/檔名)
    year_month = now.strftime("%Y/%m")
    r2_target_path = f"{data_category}/{year_month}/{time_stamp}_{data_category}.csv"
    
    # 4. 連線到 Cloudflare R2
    s3_client = boto3.client(
        's3',
        endpoint_url=os.getenv('R2_ENDPOINT_URL'),
        aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY')
    )
    
    bucket_name = os.getenv('R2_BUCKET_NAME')
    
    # 5. 執行上傳
    try:
        s3_client.upload_file(local_file_path, bucket_name, r2_target_path)
        print(f"✅ R2 備份成功！")
        print(f"📂 儲存路徑為: {r2_target_path}")
        return True
    except Exception as e:
        print(f"❌ R2 備份失敗。錯誤：{e}")
        return False
# 測試與自動執行區塊
if __name__ == "__main__":
    print("🚀 啟動雙軌自動備份系統...")
    # 1. 備份程式碼到 GitHub
    backup_code_to_github()
    
    # 2. 備份大數據到 R2
    backup_data_to_r2("my_trades.csv", "TradingLog")
