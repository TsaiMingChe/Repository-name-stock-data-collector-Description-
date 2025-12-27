
"""
每日台股數據收集主程式
"""

import os
import json
import sys
from datetime import datetime

# 添加 src 目錄到路徑
sys.path.insert(0, os.path.dirname(__file__))

from data_collector import StockDataCollector


def load_stock_list(file_path: str = "config/stock_list.json"):
    """載入股票清單"""
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config.get('symbols', [])
    except FileNotFoundError:
        return ['0050', '0056', '2330', '2317', '2454']


def main():
    """主程式"""
    
    print("\n" + "🚀" * 35)
    print("  台股數據自動收集系統")
    print("🚀" * 35)
    
    now = datetime.now()
    print(f"\n執行時間：{now.strftime('%Y-%m-%d %H:%M:%S')}")
    
    google_creds = os.getenv('GOOGLE_CREDENTIALS_JSON')
    collector = StockDataCollector(google_creds)
    
    if not collector.is_trading_day():
        print("\n⚠️  今天不是交易日，跳過執行")
        return
    
    print("\n✅ 今天是交易日，開始收集數據")
    
    symbols = load_stock_list()
    print(f"\n📋 股票清單：{', '.join(symbols)}")
    
    results = collector.collect_and_save(
        symbols=symbols,
        spreadsheet_name="台股歷史數據",
        months_back=1
    )
    
    print("\n" + "=" * 70)
    print("  執行報告")
    print("=" * 70)
    print(f"總計：{results['total']} 支股票")
    print(f"成功：{results['success']} 支")
    print(f"失敗：{results['failed']} 支")
    
    print("\n✅ 執行完成")
    print("=" * 70)


if __name__ == "__main__":
    main()
