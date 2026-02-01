"""
共用列舉定義

提供系統各模組使用的 Enum 類別。
"""

from enum import Enum as PyEnum


class Department(str, PyEnum):
    """部門列舉（僅淡海、安坑，不含 global）"""
    DANHAI = "淡海"
    ANKENG = "安坑"
