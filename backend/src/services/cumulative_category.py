"""
累計類別判定邏輯服務
對應 tasks.md T167: 實作累計類別判定邏輯
對應 spec.md: User Story 9 - 考核系統
對應 data-model-phase12.md: R 類合併累計規則（P1 修正）

此模組定義了 R 類合併累計群組及相關判定函數。
P1 修正：明確定義 R02-R05 為合併群組，避免未來新增 R01/R06 時誤判。
"""

from typing import Final

# R 類合併累計群組（P1 修正：明確定義，避免未來新增 R01/R06 時誤判）
R_CUMULATIVE_GROUP: Final[frozenset[str]] = frozenset({'R02', 'R03', 'R04', 'R05'})


def get_cumulative_category(standard_code: str, category: str) -> str:
    """
    取得累計計算的類別（處理 R 類特殊規則）

    規則：
    - R02/R03/R04/R05: 合併計算為 'R' 類別
    - 其他所有項目: 依原始類別獨立計算

    Args:
        standard_code: 考核標準代碼（如 D01, R03, +M01）
        category: 原始類別（如 D, R, +M）

    Returns:
        累計計算的類別

    Examples:
        >>> get_cumulative_category('D01', 'D')
        'D'
        >>> get_cumulative_category('R02', 'R')
        'R'
        >>> get_cumulative_category('R03', 'R')
        'R'
        >>> get_cumulative_category('R06', 'R')  # 假設未來新增 R06
        'R06'  # 不在合併群組中，獨立計算
    """
    if standard_code in R_CUMULATIVE_GROUP:
        return 'R'  # R02-R05 合併計算
    else:
        return category  # D, W, O, S 及其他項目各自獨立


def is_r_cumulative_group_member(standard_code: str) -> bool:
    """
    判斷標準代碼是否屬於 R 類合併群組

    Args:
        standard_code: 考核標準代碼

    Returns:
        是否屬於 R02-R05 合併群組
    """
    return standard_code in R_CUMULATIVE_GROUP


def get_r_cumulative_group() -> list[str]:
    """
    取得 R 類合併群組的代碼列表

    Returns:
        R02-R05 代碼列表
    """
    return list(R_CUMULATIVE_GROUP)


def calculate_cumulative_multiplier(count: int) -> float:
    """
    計算累計倍率

    公式：累計倍率 = 1 + 0.5 × (count - 1)

    Args:
        count: 累計次數（第 N 次）

    Returns:
        累計倍率（最小為 1.0）

    Examples:
        >>> calculate_cumulative_multiplier(1)
        1.0
        >>> calculate_cumulative_multiplier(2)
        1.5
        >>> calculate_cumulative_multiplier(3)
        2.0
        >>> calculate_cumulative_multiplier(4)
        2.5
    """
    if count <= 0:
        return 1.0
    return 1.0 + 0.5 * (count - 1)


def calculate_next_cumulative_multiplier(current_count: int) -> float:
    """
    計算下一次違規的累計倍率

    Args:
        current_count: 當前累計次數

    Returns:
        下一次的累計倍率

    Examples:
        >>> calculate_next_cumulative_multiplier(0)  # 首次違規
        1.0
        >>> calculate_next_cumulative_multiplier(1)  # 第二次違規
        1.5
        >>> calculate_next_cumulative_multiplier(2)  # 第三次違規
        2.0
    """
    return calculate_cumulative_multiplier(current_count + 1)
