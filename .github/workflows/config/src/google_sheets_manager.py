"""
Google Sheets 雲端資料庫管理器
"""

import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional
import json
import os


class GoogleSheetsManager:
    """Google Sheets 資料庫管理器"""
    
    def __init__(self, credentials_json: str = None):
        """初始化 Google Sheets 管理器"""
        
        self.scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        
        if credentials_json is None:
            credentials_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
        
        if credentials_json:
            creds_dict = json.loads(credentials_json)
            self.credentials = Credentials.from_service_account_info(
                creds_dict,
                scopes=self.scopes
            )
        else:
            self.credentials = Credentials.from_service_account_file(
                'credentials.json',
                scopes=self.scopes
            )
        
        self.client = gspread.authorize(self.credentials)
        print("✅ Google Sheets 管理器初始化完成")
    
    def get_or_create_spreadsheet(self, spreadsheet_name: str = "台股歷史數據"):
        """獲取或創建試算表"""
        
        try:
            spreadsheet = self.client.open(spreadsheet_name)
            print(f"✅ 打開現有試算表：{spreadsheet_name}")
        except gspread.SpreadsheetNotFound:
            spreadsheet = self.client.create(spreadsheet_name)
            print(f"✅ 創建新試算表：{spreadsheet_name}")
        
        return spreadsheet
    
    def get_or_create_worksheet(self, spreadsheet, worksheet_name: str):
        """獲取或創建工作表"""
        
        try:
            worksheet = spreadsheet.worksheet(worksheet_name)
            print(f"  ✅ 打開工作表：{worksheet_name}")
        except gspread.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(
                title=worksheet_name,
                rows=1000,
                cols=10
            )
            
            headers = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Source', 'Updated']
            worksheet.append_row(headers)
            
            print(f"  ✅ 創建工作表：{worksheet_name}")
        
        return worksheet
    
    def append_stock_data(self, spreadsheet_name: str, symbol: str, 
                         df: pd.DataFrame, source: str = "TWSE"):
        """追加股票數據到 Google Sheets"""
        
        try:
            spreadsheet = self.get_or_create_spreadsheet(spreadsheet_name)
            worksheet = self.get_or_create_worksheet(spreadsheet, symbol)
            
            existing_data = worksheet.get_all_values()
            existing_dates = set()
            
            if len(existing_data) > 1:
                for row in existing_data[1:]:
                    if row[0]:
                        existing_dates.add(row[0])
            
            new_rows = []
            updated_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            for _, row in df.iterrows():
                date_str = row['Date'].strftime('%Y-%m-%d')
                
                if date_str not in existing_dates:
                    new_rows.append([
                        date_str,
                        float(row['Open']),
                        float(row['High']),
                        float(row['Low']),
                        float(row['Close']),
                        int(row['Volume']),
                        source,
                        updated_time
                    ])
            
            if new_rows:
                worksheet.append_rows(new_rows)
                print(f"  ✅ 寫入 {len(new_rows)} 筆新數據到 {symbol}")
                return True
            else:
                print(f"  ℹ️  {symbol} 無新數據需要寫入")
                return True
                
        except Exception as e:
            print(f"  ❌ 寫入失敗：{e}")
            return False
    
    def read_stock_data(self, spreadsheet_name: str, symbol: str,
                       start_date: str = None, end_date: str = None):
        """從 Google Sheets 讀取股票數據"""
        
        try:
            spreadsheet = self.client.open(spreadsheet_name)
            worksheet = spreadsheet.worksheet(symbol)
            
            data = worksheet.get_all_records()
            df = pd.DataFrame(data)
            
            if df.empty:
                return None
            
            df['Date'] = pd.to_datetime(df['Date'])
            
            if start_date:
                start_dt = pd.to_datetime(start_date)
                df = df[df['Date'] >= start_dt]
            
            if end_date:
                end_dt = pd.to_datetime(end_date)
                df = df[df['Date'] <= end_dt]
            
            df = df.sort_values('Date').reset_index(drop=True)
            
            print(f"✅ 從 Google Sheets 讀取 {len(df)} 筆數據：{symbol}")
            
            return df
            
        except Exception as e:
            print(f"❌ 讀取失敗：{e}")
            return None


print("✅ Google Sheets 管理器定義完成")
