"""
部門判斷服務
對應 tasks.md T092: 實作部門判斷服務

功能：
- 根據條碼前綴判斷部門
- TH → 淡海
- AK → 安坑
- 支援自訂前綴映射
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class Department(str, Enum):
    """部門枚舉"""
    TANHAI = "淡海"
    ANKENG = "安坑"


@dataclass
class DepartmentDetectionResult:
    """部門判斷結果"""
    department: Optional[Department]  # 判斷出的部門
    prefix: Optional[str]             # 識別到的前綴
    confidence: float                 # 信心度（0-1）
    original_data: str                # 原始條碼資料
    matched_pattern: Optional[str] = None  # 匹配到的模式


class DepartmentDetector:
    """部門判斷器"""

    # 預設前綴映射
    DEFAULT_PREFIX_MAP = {
        'TH': Department.TANHAI,
        '淡海': Department.TANHAI,
        'TANHAI': Department.TANHAI,
        'AK': Department.ANKENG,
        '安坑': Department.ANKENG,
        'ANKENG': Department.ANKENG,
    }

    # 預設條碼模式（正則表達式）
    # 格式: {前綴}-{編號} 或 {前綴}_{編號}
    DEFAULT_PATTERNS = [
        r'^(TH|AK)[-_]?\d+',           # TH-12345, AK12345
        r'^(淡海|安坑)[-_]?\d+',        # 淡海-12345
        r'^(TANHAI|ANKENG)[-_]?\d+',   # TANHAI_12345
    ]

    def __init__(
        self,
        prefix_map: Optional[dict[str, Department]] = None,
        patterns: Optional[list[str]] = None,
        case_sensitive: bool = False
    ):
        """
        初始化部門判斷器

        Args:
            prefix_map: 前綴到部門的映射字典，None 則使用預設
            patterns: 條碼模式正則表達式列表，None 則使用預設
            case_sensitive: 是否區分大小寫
        """
        self.prefix_map = prefix_map or self.DEFAULT_PREFIX_MAP.copy()
        self.patterns = patterns or self.DEFAULT_PATTERNS.copy()
        self.case_sensitive = case_sensitive

        # 編譯正則表達式
        flags = 0 if case_sensitive else re.IGNORECASE
        self._compiled_patterns = [re.compile(p, flags) for p in self.patterns]

    def detect(self, barcode_data: str) -> DepartmentDetectionResult:
        """
        從條碼資料判斷部門

        Args:
            barcode_data: 條碼內容

        Returns:
            DepartmentDetectionResult
        """
        if not barcode_data:
            return DepartmentDetectionResult(
                department=None,
                prefix=None,
                confidence=0.0,
                original_data=barcode_data
            )

        # 清理資料
        data = barcode_data.strip()
        if not self.case_sensitive:
            data_upper = data.upper()
        else:
            data_upper = data

        # 方法 1: 直接前綴匹配
        for prefix, department in self.prefix_map.items():
            check_prefix = prefix if self.case_sensitive else prefix.upper()
            check_data = data if self.case_sensitive else data_upper

            if check_data.startswith(check_prefix):
                logger.info(f"條碼 '{barcode_data}' 判斷為 {department.value} (前綴: {prefix})")
                return DepartmentDetectionResult(
                    department=department,
                    prefix=prefix,
                    confidence=1.0,
                    original_data=barcode_data,
                    matched_pattern="prefix_match"
                )

        # 方法 2: 正則表達式匹配
        for pattern, compiled in zip(self.patterns, self._compiled_patterns):
            match = compiled.match(data)
            if match:
                # 取得匹配的前綴
                matched_prefix = match.group(1)
                matched_prefix_check = matched_prefix if self.case_sensitive else matched_prefix.upper()

                # 查找對應的部門
                for prefix, department in self.prefix_map.items():
                    prefix_check = prefix if self.case_sensitive else prefix.upper()
                    if matched_prefix_check == prefix_check:
                        logger.info(
                            f"條碼 '{barcode_data}' 判斷為 {department.value} "
                            f"(模式: {pattern})"
                        )
                        return DepartmentDetectionResult(
                            department=department,
                            prefix=matched_prefix,
                            confidence=0.9,
                            original_data=barcode_data,
                            matched_pattern=pattern
                        )

        # 未能判斷
        logger.warning(f"無法判斷條碼 '{barcode_data}' 的部門")
        return DepartmentDetectionResult(
            department=None,
            prefix=None,
            confidence=0.0,
            original_data=barcode_data
        )

    def detect_batch(
        self,
        barcode_data_list: list[str]
    ) -> list[DepartmentDetectionResult]:
        """
        批次判斷部門

        Args:
            barcode_data_list: 條碼內容列表

        Returns:
            DepartmentDetectionResult 列表
        """
        return [self.detect(data) for data in barcode_data_list]

    def add_prefix_mapping(self, prefix: str, department: Department):
        """
        新增前綴映射

        Args:
            prefix: 前綴
            department: 對應的部門
        """
        self.prefix_map[prefix] = department
        logger.info(f"已新增前綴映射: {prefix} → {department.value}")

    def add_pattern(self, pattern: str):
        """
        新增條碼模式

        Args:
            pattern: 正則表達式模式
        """
        flags = 0 if self.case_sensitive else re.IGNORECASE
        self.patterns.append(pattern)
        self._compiled_patterns.append(re.compile(pattern, flags))
        logger.info(f"已新增條碼模式: {pattern}")

    @staticmethod
    def get_folder_id_for_department(
        department: Department,
        settings: dict[str, str]
    ) -> Optional[str]:
        """
        根據部門取得對應的 Google Drive 資料夾 ID

        Args:
            department: 部門
            settings: 系統設定字典，包含 drive_folder_id_淡海 和 drive_folder_id_安坑

        Returns:
            資料夾 ID，找不到則返回 None
        """
        key = f"drive_folder_id_{department.value}"
        return settings.get(key)


# 單例模式
_department_detector: Optional[DepartmentDetector] = None


def get_department_detector() -> DepartmentDetector:
    """取得部門判斷器實例（單例）"""
    global _department_detector
    if _department_detector is None:
        _department_detector = DepartmentDetector()
    return _department_detector


# 便利函式
def detect_department(barcode_data: str) -> DepartmentDetectionResult:
    """判斷部門的便利函式"""
    detector = get_department_detector()
    return detector.detect(barcode_data)


def is_tanhai(barcode_data: str) -> bool:
    """判斷是否為淡海部門"""
    result = detect_department(barcode_data)
    return result.department == Department.TANHAI


def is_ankeng(barcode_data: str) -> bool:
    """判斷是否為安坑部門"""
    result = detect_department(barcode_data)
    return result.department == Department.ANKENG
