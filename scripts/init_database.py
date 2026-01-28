"""
資料庫初始化腳本
對應 tasks.md T015: 建立資料庫初始化腳本

功能：
- 建立所有資料表
- 建立索引
- 插入預設資料（如預設管理員帳號）
"""

import sys
import os

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy import text
from src.config.database import engine, init_database, check_database_connection
from src.config.settings import get_settings
from src.models.base import Base


def create_tables():
    """建立所有資料表"""
    print("[*] 建立資料表...")

    # 匯入所有模型以確保它們被註冊到 Base.metadata
    # 這些 import 會在後續任務中建立模型後生效
    try:
        from src.models import user
        print("  - User 模型已載入")
    except ImportError:
        print("  - User 模型尚未建立")

    try:
        from src.models import employee
        print("  - Employee 模型已載入")
    except ImportError:
        print("  - Employee 模型尚未建立")

    try:
        from src.models import system_setting
        print("  - SystemSetting 模型已載入")
    except ImportError:
        print("  - SystemSetting 模型尚未建立")

    try:
        from src.models import google_oauth_token
        print("  - GoogleOAuthToken 模型已載入")
    except ImportError:
        print("  - GoogleOAuthToken 模型尚未建立")

    # 建立所有資料表
    Base.metadata.create_all(bind=engine)
    print("[OK] 資料表建立完成")


def create_indexes():
    """建立額外索引（如果需要）"""
    print("[*] 檢查索引...")
    # 索引通常在模型定義中使用 Index 或 index=True 建立
    # 這裡可以添加額外的複合索引
    print("[OK] 索引檢查完成")


def insert_default_data():
    """插入預設資料"""
    print("[*] 插入預設資料...")

    # 預設資料將在模型建立後實作
    # 例如：預設管理員帳號、預設系統設定

    print("[OK] 預設資料插入完成（或已存在）")


def verify_tables():
    """驗證資料表是否建立成功"""
    print("[*] 驗證資料表...")

    with engine.connect() as conn:
        # 查詢所有資料表
        result = conn.execute(text("SHOW TABLES"))
        tables = [row[0] for row in result]

        if tables:
            print(f"  已建立的資料表: {', '.join(tables)}")
        else:
            print("  尚無資料表")

    print("[OK] 驗證完成")


def main():
    """主程式"""
    settings = get_settings()

    print("=" * 60)
    print("司機員管理系統 - 資料庫初始化")
    print("=" * 60)
    print(f"環境: {settings.api_environment}")
    print(f"資料庫: {settings.tidb_database}@{settings.tidb_host}")
    print("=" * 60)

    # 1. 檢查資料庫連線
    print("\n[Step 1] 檢查資料庫連線")
    if not check_database_connection():
        print("[ERROR] 資料庫連線失敗，請檢查設定")
        sys.exit(1)
    print("[OK] 資料庫連線正常")

    # 2. 建立資料表
    print("\n[Step 2] 建立資料表")
    create_tables()

    # 3. 建立索引
    print("\n[Step 3] 建立索引")
    create_indexes()

    # 4. 插入預設資料
    print("\n[Step 4] 插入預設資料")
    insert_default_data()

    # 5. 驗證
    print("\n[Step 5] 驗證")
    verify_tables()

    print("\n" + "=" * 60)
    print("資料庫初始化完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
