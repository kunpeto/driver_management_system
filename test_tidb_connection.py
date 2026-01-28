#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""測試 TiDB 資料庫連線"""

import sys
import os

# 設定輸出編碼為 UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_connection():
    """測試資料庫連線"""

    # 連線資訊
    config = {
        'host': 'gateway01.ap-northeast-1.prod.aws.tidbcloud.com',
        'port': 4000,
        'user': '3SQWVrWh5DieHsr.root',
        'password': 'pA6LsowKCFAVVJm2',
        'database': 'test'
    }

    print("=" * 60)
    print("TiDB 連線測試")
    print("=" * 60)
    print(f"Host: {config['host']}")
    print(f"Port: {config['port']}")
    print(f"User: {config['user']}")
    print(f"Database: {config['database']}")
    print("=" * 60)

    # 嘗試使用 pymysql
    try:
        import pymysql
        print("\n[OK] 使用 pymysql 連線...")

        connection = pymysql.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            database=config['database'],
            ssl_verify_cert=True,
            ssl_verify_identity=True
        )

        print("[OK] 連線成功！")

        # 執行測試查詢
        with connection.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"[OK] 資料庫版本: {version[0]}")

            cursor.execute("SELECT DATABASE()")
            db = cursor.fetchone()
            print(f"[OK] 當前資料庫: {db[0]}")

            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            print(f"[OK] 資料表數量: {len(tables)}")
            if tables:
                print("  資料表列表:")
                for table in tables:
                    print(f"    - {table[0]}")

        connection.close()
        print("\n[OK] 測試完成！連線正常。")
        return True

    except ImportError:
        print("[ERROR] pymysql 未安裝")
        print("\n嘗試使用 mysql.connector...")

        try:
            import mysql.connector
            print("[OK] 使用 mysql.connector 連線...")

            connection = mysql.connector.connect(
                host=config['host'],
                port=config['port'],
                user=config['user'],
                password=config['password'],
                database=config['database'],
                ssl_disabled=False
            )

            print("[OK] 連線成功！")

            cursor = connection.cursor()
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"[OK] 資料庫版本: {version[0]}")

            cursor.execute("SELECT DATABASE()")
            db = cursor.fetchone()
            print(f"[OK] 當前資料庫: {db[0]}")

            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            print(f"[OK] 資料表數量: {len(tables)}")
            if tables:
                print("  資料表列表:")
                for table in tables:
                    print(f"    - {table[0]}")

            cursor.close()
            connection.close()
            print("\n[OK] 測試完成！連線正常。")
            return True

        except ImportError:
            print("[ERROR] mysql.connector 未安裝")
            print("\n請安裝其中一個 MySQL 連線套件：")
            print("  pip install pymysql")
            print("  或")
            print("  pip install mysql-connector-python")
            return False

    except Exception as e:
        print(f"\n[ERROR] 連線失敗: {e}")
        print(f"錯誤類型: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_connection()
    sys.exit(0 if success else 1)
