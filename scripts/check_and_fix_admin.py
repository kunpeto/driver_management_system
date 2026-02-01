"""
檢查並修正管理員帳號

功能：
1. 查看數據庫中的所有用戶
2. 如果沒有 admin，則建立
3. 如果有 admin，則重置密碼
"""

import sys
import os

# 設定環境變數（TiDB 連線資訊）
os.environ["TIDB_HOST"] = "gateway01.ap-northeast-1.prod.aws.tidbcloud.com"
os.environ["TIDB_PORT"] = "4000"
os.environ["TIDB_USER"] = "3SQWVrWh5DieHsr.root"
os.environ["TIDB_PASSWORD"] = "pA6LsowKCFAVVJm2"
os.environ["TIDB_DATABASE"] = "test"

# 添加專案路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy.orm import Session
from src.config.database import sync_engine, SyncSessionLocal
from src.models.user import User
from src.utils.password import hash_password


def main():
    print("=" * 60)
    print("司機員管理系統 - 檢查並修正管理員帳號")
    print("=" * 60)

    db = SyncSessionLocal()

    try:
        # 查看所有用戶
        users = db.query(User).all()
        print(f"\n目前系統中有 {len(users)} 個使用者：")

        for user in users:
            print(f"  - ID: {user.id}")
            print(f"    帳號: {user.username}")
            print(f"    名稱: {user.display_name}")
            print(f"    角色: {user.role}")
            print(f"    部門: {user.department}")
            print(f"    啟用: {user.is_active}")
            print()

        # 檢查是否有 admin
        admin = db.query(User).filter(User.username == "admin").first()

        if admin:
            print("\n[INFO] 找到 admin 帳號，正在重置密碼...")
            admin.password_hash = hash_password("admin123")
            admin.is_active = True
            db.commit()
            print("[OK] admin 密碼已重置為: admin123")
        else:
            print("\n[INFO] 沒有找到 admin 帳號，正在建立...")
            new_admin = User(
                username="admin",
                password_hash=hash_password("admin123"),
                display_name="系統管理員",
                role="admin",
                department=None,
                is_active=True
            )
            db.add(new_admin)
            db.commit()
            print("[OK] admin 帳號已建立，密碼: admin123")

        print("\n" + "=" * 60)
        print("完成！請使用 admin / admin123 登入")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] 發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
