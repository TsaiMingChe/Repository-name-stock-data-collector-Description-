"""
台股數據收集器
"""

import requests
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time
from google_sheets_manager import GoogleSheetsManager


class StockDataCollector:
    """台股數據收集器"""
    
    def __init__(self, google_credentials_json: str = None):
        """初始化數據收集器"""
        
        self.twse_base_url = "https://www.twse.com.tw/rwd/zh"
        self.twse_stock_url = f"{self.twse_base_url}/afterTrading/STOCK_DAY"
        
        self.sheets_manager = GoogleSheetsManager(google_credentials_json)
        
        print("✅ 數據收集器初始化完成")
    
    def is_trading_day(self, date: datetime = None):
        """檢查是否為交易日"""
        
        if date is None:
            date = datetime.now()
        
        if date.weekday() >= 5:
            return False
        
        return True
    
    def collect_from_twse(self, symbol: str, year: int, month: int):
        """從證交所 API 收集數據"""
        
        try:
            params = {
                'date': f"{year}{month:02d}01",
                'stockNo': symbol,
                'response': 'json'
            }
            
            response = requests.get(
                self.twse_stock_url,
                params=params,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'data' in data and data['data']:
                    all_data = []
                    
                    for row in data['data']:
                        try:
                            date_str = row[0].strip()
                            date_parts = date_str.split('/')
                            
                            year_ad = int(date_parts[0]) + 1911
                            month_val = int(date_parts[1])
                            day = int(date_parts[2])
                            
                            date_obj = datetime(year_ad, month_val, day)
                            
                            all_data.append({
                                'Date': date_obj,
                                'Volume': int(row[1].replace(',', '')),
                                'Open': float(row[3].replace(',', '')),
                                'High': float(row[4].replace(',', '')),
                                'Low': float(row[5].replace(',', '')),
                                'Close': float(row[6].replace(',', ''))
                            })
                        except (ValueError, IndexError):
                            continue
                    
                    if all_data:
                        df = pd.DataFrame(all_data)
                        df = df.sort_values('Date').reset_index(drop=True)
                        return df
            
            return None
            
        except Exception as e:
            print(f"  ⚠️  證交所 API 錯誤：{e}")
            return None
    
    def collect_from_yfinance(self, symbol: str, start_date: str, end_date: str):
        """從 yfinance 收集數據"""
        
        try:
            yf_symbol = f"{symbol}.TW"
            ticker = yf.Ticker(yf_symbol)
            df = ticker.history(start=start_date, end=end_date)
            
            if df.empty:
                return None
            
            df = df.reset_index()
            df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
            
            return df
            
        except Exception as e:
            print(f"  ⚠️  yfinance 錯誤：{e}")
            return None
    
    def collect_and_save(self, symbols: List[str], 
                        spreadsheet_name: str = "台股歷史數據",
                        months_back: int = 1):
        """收集並保存數據"""
        
        print("\n" + "=" * 70)
        print(f"  開始收集數據：{len(symbols)} 支股票")
        print("=" * 70)
        
        results = {
            'total': len(symbols),
            'success': 0,
            'failed': 0,
            'details': []
        }
        
        today = datetime.now()
        
        for symbol in symbols:
            print(f"\n【{symbol}】")
            
            try:
                df = None
                
                for i in range(months_back):
                    target_date = today - timedelta(days=30 * i)
                    year = target_date.year
                    month = target_date.month
                    
                    print(f"  📥 收集 {year}/{month:02d} 數據...")
                    
                    month_df = self.collect_from_twse(symbol, year, month)
                    
                    if month_df is not None:
                        if df is None:
                            df = month_df
                        else:
                            df = pd.concat([df, month_df], ignore_index=True)
                    
                    time.sleep(3)
                
                if df is None or len(df) == 0:
                    print(f"  ⚠️  證交所 API 無數據，切換到 yfinance")
                    
                    start_date = (today - timedelta(days=30 * months_back)).strftime('%Y-%m-%d')
                    end_date = today.strftime('%Y-%m-%d')
                    
                    df = self.collect_from_yfinance(symbol, start_date, end_date)
                    source = "yfinance"
                else:
                    source = "TWSE"
                
                if df is not None and len(df) > 0:
                    success = self.sheets_manager.append_stock_data(
                        spreadsheet_name=spreadsheet_name,
                        symbol=symbol,
                        df=df,
                        source=source
                    )
                    
                    if success:
                        results['success'] += 1
                        results['details'].append({
                            'symbol': symbol,
                            'status': 'success',
                            'records': len(df),
                            'source': source
                        })
                        print(f"  ✅ 完成：{len(df)} 筆數據（來源：{source}）")
                    else:
                        results['failed'] += 1
                else:
                    results['failed'] += 1
                    print(f"  ❌ 失敗：無法獲取數據")
                    
            except Exception as e:
                results['failed'] += 1
                print(f"  ❌ 錯誤：{e}")
        
        print("\n" + "=" * 70)
        print(f"  收集完成")
        print(f"  成功：{results['success']} / 失敗：{results['failed']}")
        print("=" * 70)
        
        return results


print("✅ 數據收集器定義完成")
