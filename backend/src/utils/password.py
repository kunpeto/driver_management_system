"""
密碼雜湊工具
對應 tasks.md T020: 實作密碼雜湊工具

使用 bcrypt 進行密碼雜湊，成本因子為 12。
"""

import bcrypt


# bcrypt 成本因子（值越高越安全，但驗證越慢）
# 12 是目前推薦的平衡值，每次驗證約 0.3 秒
BCRYPT_COST_FACTOR = 12


def hash_password(password: str) -> str:
    """
    對密碼進行雜湊處理

    Args:
        password: 明文密碼

    Returns:
        str: bcrypt 雜湊後的密碼（包含 salt）
    """
    # 將密碼編碼為 bytes
    password_bytes = password.encode("utf-8")

    # 生成 salt 並進行雜湊
    salt = bcrypt.gensalt(rounds=BCRYPT_COST_FACTOR)
    hashed = bcrypt.hashpw(password_bytes, salt)

    # 返回字串格式的雜湊值
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    驗證密碼是否正確

    Args:
        plain_password: 使用者輸入的明文密碼
        hashed_password: 資料庫中儲存的雜湊密碼

    Returns:
        bool: True 表示密碼正確
    """
    try:
        # 將密碼編碼為 bytes
        password_bytes = plain_password.encode("utf-8")
        hashed_bytes = hashed_password.encode("utf-8")

        # 驗證密碼
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except (ValueError, TypeError):
        # 如果雜湊格式無效，返回 False
        return False


def is_password_strong(password: str) -> tuple[bool, str]:
    """
    檢查密碼強度

    規則：
    - 至少 8 個字元
    - 至少包含一個大寫字母
    - 至少包含一個小寫字母
    - 至少包含一個數字

    Args:
        password: 要檢查的密碼

    Returns:
        tuple[bool, str]: (是否符合要求, 錯誤訊息)
    """
    if len(password) < 8:
        return False, "密碼長度至少需要 8 個字元"

    if not any(c.isupper() for c in password):
        return False, "密碼需要包含至少一個大寫字母"

    if not any(c.islower() for c in password):
        return False, "密碼需要包含至少一個小寫字母"

    if not any(c.isdigit() for c in password):
        return False, "密碼需要包含至少一個數字"

    return True, ""


def needs_rehash(hashed_password: str) -> bool:
    """
    檢查密碼雜湊是否需要重新計算

    當成本因子變更時，舊的雜湊可能需要更新。

    Args:
        hashed_password: 資料庫中儲存的雜湊密碼

    Returns:
        bool: True 表示需要重新雜湊
    """
    try:
        hashed_bytes = hashed_password.encode("utf-8")

        # 從雜湊中提取成本因子
        # bcrypt 格式: $2b$XX$... 其中 XX 是成本因子
        parts = hashed_password.split("$")
        if len(parts) >= 3:
            current_cost = int(parts[2])
            return current_cost < BCRYPT_COST_FACTOR

        return True  # 無法解析格式，建議重新雜湊
    except (ValueError, IndexError):
        return True
