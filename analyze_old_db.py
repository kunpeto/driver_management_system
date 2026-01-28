#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析舊系統資料庫結構
"""
import sqlite3
import os
import sys
from datetime import datetime

# 設定輸出編碼為 UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 舊資料庫路徑
OLD_DB_PATH = r"C:\Users\kunpe\claude專案\driver_profile_system_重構\database\driver_profiles.db"

def analyze_database():
    """分析資料庫結構與資料量"""

    if not os.path.exists(OLD_DB_PATH):
        print(f"[ERROR] 資料庫不存在: {OLD_DB_PATH}")
        return

    conn = sqlite3.connect(OLD_DB_PATH)
    cursor = conn.cursor()

    print("=" * 80)
    print("舊系統資料庫結構分析")
    print("=" * 80)
    print(f"資料庫路徑: {OLD_DB_PATH}")
    print(f"檔案大小: {os.path.getsize(OLD_DB_PATH) / 1024:.2f} KB")
    print()

    # 1. 列出所有資料表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]

    print(f"[INFO] 資料表數量: {len(tables)}")
    print()

    for table_name in tables:
        print("-" * 80)
        print(f"[TABLE] {table_name}")
        print("-" * 80)

        # 2. 取得資料表結構
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()

        print(f"\n欄位結構 ({len(columns)} 個欄位):")
        print(f"{'序號':<5} {'欄位名稱':<30} {'資料型別':<15} {'允許NULL':<10} {'預設值':<15} {'主鍵'}")
        print("-" * 100)

        for col in columns:
            cid, name, dtype, notnull, default_val, pk = col
            null_str = "NO" if notnull else "YES"
            default_str = str(default_val) if default_val else "-"
            pk_str = "PK" if pk else ""
            print(f"{cid:<5} {name:<30} {dtype:<15} {null_str:<10} {default_str:<15} {pk_str}")

        # 3. 統計資料量
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        total_count = cursor.fetchone()[0]
        print(f"\n[STAT] 總記錄數: {total_count}")

        # 4. 如果是履歷相關資料表，分析年度分佈
        if 'profile' in table_name.lower() or 'record' in table_name.lower():
            # 嘗試找日期欄位
            date_columns = [col[1] for col in columns if 'date' in col[1].lower() or 'time' in col[1].lower()]

            if date_columns:
                date_col = date_columns[0]
                print(f"\n[DATE] 根據 '{date_col}' 分析年度分佈:")

                try:
                    cursor.execute(f"""
                        SELECT
                            SUBSTR({date_col}, 1, 4) as year,
                            COUNT(*) as count
                        FROM {table_name}
                        WHERE {date_col} IS NOT NULL
                        GROUP BY year
                        ORDER BY year
                    """)

                    year_stats = cursor.fetchall()

                    records_before_2026 = 0
                    records_2026_after = 0

                    for year, count in year_stats:
                        indicator = "[KEEP]" if year and year < '2026' else "[SKIP]"
                        print(f"  {indicator} {year}: {count} 筆")

                        if year and year < '2026':
                            records_before_2026 += count
                        else:
                            records_2026_after += count

                    print(f"\n[MIGRATE] 2026年前需遷移: {records_before_2026} 筆")
                    print(f"[EXCLUDE] 2026年後排除: {records_2026_after} 筆")

                except Exception as e:
                    print(f"  [WARN] 無法分析年度分佈: {e}")

        # 5. 顯示前 3 筆樣本資料
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
        sample_rows = cursor.fetchall()

        if sample_rows:
            print(f"\n[SAMPLE] 樣本資料 (前 3 筆):")
            col_names = [col[1] for col in columns]

            for i, row in enumerate(sample_rows, 1):
                print(f"\n  樣本 {i}:")
                for col_name, value in zip(col_names, row):
                    # 截斷過長的內容
                    if value and isinstance(value, str) and len(value) > 50:
                        value_str = value[:50] + "..."
                    else:
                        value_str = str(value)
                    print(f"    {col_name}: {value_str}")

        print()

    conn.close()
    print("=" * 80)
    print("[SUCCESS] 分析完成")
    print("=" * 80)

if __name__ == "__main__":
    analyze_database()
