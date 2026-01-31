"""
建立預設管理員帳號腳本

使用方式：
    python scripts/create_admin.py

功能：
- 檢查是否已有管理員帳號
- 建立預設管理員帳號（admin / admin123）
- 或自訂管理員帳號
"""

import sys
import os
import getpass

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy.orm import Session
from src.config.database import sync_engine, SyncSessionLocal
from src.models.user import User
from src.services.user_service import UserService, DuplicateUsernameError, WeakPasswordError


def check_existing_users(db: Session) -> int:
    """檢查現有使用者數量"""
    count = db.query(User).count()
    return count


def create_default_admin(db: Session, custom: bool = False):
    """建立預設管理員帳號"""

    if custom:
        print("\n=== 建立自訂管理員帳號 ===")
        username = input("使用者名稱 (至少 3 個字元): ").strip()
        display_name = input("顯示名稱: ").strip()
        email = input("電子郵件 (可選): ").strip() or None

        while True:
            password = getpass.getpass("密碼 (至少 8 個字元): ")
            password_confirm = getpass.getpass("確認密碼: ")

            if password != password_confirm:
                print("❌ 密碼不一致，請重新輸入")
                continue

            if len(password) < 8:
                print("❌ 密碼至少需要 8 個字元")
                continue

            break
    else:
        print("\n=== 建立預設管理員帳號 ===")
        username = "admin"
        password = "admin123"
        display_name = "系統管理員"
        email = None
        print(f"帳號: {username}")
        print(f"密碼: {password}")
        print(f"顯示名稱: {display_name}")

    try:
        user_service = UserService(db)

        # 建立管理員帳號
        user = user_service.create(
            username=username,
            password=password,
            display_name=display_name,
            email=email,
            role="admin",
            department=None,
            is_active=True,
            check_password_strength=False  # 允許簡單密碼用於預設帳號
        )

        print(f"\n[OK] 管理員帳號建立成功！")
        print(f"   ID: {user.id}")
        print(f"   使用者名稱: {user.username}")
        print(f"   顯示名稱: {user.display_name}")
        print(f"   角色: {user.role}")

        if not custom:
            print(f"\n[WARN] 請登入後立即修改預設密碼！")

        return user

    except DuplicateUsernameError:
        print(f"\n[ERROR] 使用者名稱 '{username}' 已存在")
        return None
    except WeakPasswordError as e:
        print(f"\n[ERROR] 密碼強度不足: {str(e)}")
        return None
    except Exception as e:
        print(f"\n[ERROR] 建立失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """主程式"""
    print("=" * 60)
    print("司機員管理系統 - 建立管理員帳號")
    print("=" * 60)

    # 建立資料庫連線
    db = SyncSessionLocal()

    try:
        # 檢查現有使用者
        user_count = check_existing_users(db)
        print(f"\n目前系統中有 {user_count} 個使用者")

        if user_count > 0:
            print("\n現有使用者列表：")
            users = db.query(User).all()
            for user in users:
                print(f"  - {user.username} ({user.display_name}) - {user.role}")

            confirm = input("\n是否要建立新的管理員帳號？(y/n): ").strip().lower()
            if confirm != 'y':
                print("取消建立")
                return

        # 選擇建立方式
        print("\n請選擇：")
        print("1. 建立預設管理員帳號 (admin / admin123)")
        print("2. 建立自訂管理員帳號")

        choice = input("請輸入選項 (1 或 2): ").strip()

        if choice == "1":
            create_default_admin(db, custom=False)
        elif choice == "2":
            create_default_admin(db, custom=True)
        else:
            print("無效的選項")
            return

        # 提交變更
        db.commit()

    except Exception as e:
        print(f"\n❌ 發生錯誤: {str(e)}")
        db.rollback()
    finally:
        db.close()

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
