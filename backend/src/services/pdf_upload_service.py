"""
PDF 上傳服務
對應 tasks.md T187: 實作 PDF 上傳服務

功能：
- 取得上傳參數（資料夾 ID、檔案命名規則）
- 驗證上傳權限
- 更新 Profile.gdrive_link 和 conversion_status

架構說明：
由於後端部署在雲端（Render），無法直接呼叫用戶桌面的本機 API。
實際的 PDF 上傳流程：
1. 前端呼叫後端取得上傳參數（本服務提供）
2. 前端呼叫本機 API 上傳 PDF 到 Google Drive
3. 前端將 Drive 連結回傳給後端更新 Profile
"""

from typing import Optional
from dataclasses import dataclass
from datetime import date
from sqlalchemy.orm import Session

from src.models.profile import Profile, ProfileType, ConversionStatus
from src.services.profile_service import ProfileService, ProfileNotFoundError
from src.utils.logger import logger


# 履歷類型對應的資料夾名稱
PROFILE_TYPE_FOLDER_NAMES = {
    ProfileType.EVENT_INVESTIGATION.value: "事件調查",
    ProfileType.PERSONNEL_INTERVIEW.value: "人員訪談",
    ProfileType.CORRECTIVE_MEASURES.value: "矯正措施",
    ProfileType.ASSESSMENT_NOTICE.value: "考核通知",
    ProfileType.BASIC.value: "其他",
}


@dataclass
class UploadParams:
    """上傳參數"""
    profile_id: int
    profile_type: str
    employee_id: str
    employee_name: str
    event_date: Optional[date]
    department: str
    suggested_folder_name: str
    suggested_file_name: str
    can_upload: bool
    error_message: Optional[str] = None


@dataclass
class UploadCompleteResult:
    """上傳完成結果"""
    success: bool
    profile_id: int
    gdrive_link: Optional[str]
    conversion_status: str
    error_message: Optional[str] = None


class PdfUploadService:
    """
    PDF 上傳服務

    提供 PDF 上傳所需的參數計算和狀態更新功能。
    實際的檔案上傳由本機 API 執行。
    """

    def __init__(self, db: Session):
        self.db = db
        self.profile_service = ProfileService(db)

    def _generate_file_name(self, profile: Profile) -> str:
        """
        生成建議的檔案名稱

        格式：{類型}_{員工編號}_{日期}.pdf
        例如：事件調查_A12345_20260130.pdf
        """
        type_name = PROFILE_TYPE_FOLDER_NAMES.get(
            profile.profile_type,
            "履歷"
        )

        employee_no = ""
        if profile.employee:
            employee_no = profile.employee.employee_no or str(profile.employee_id)
        else:
            employee_no = str(profile.employee_id)

        date_str = ""
        if profile.event_date:
            date_str = profile.event_date.strftime("%Y%m%d")
        else:
            date_str = date.today().strftime("%Y%m%d")

        return f"{type_name}_{employee_no}_{date_str}.pdf"

    def _generate_folder_name(self, profile: Profile) -> str:
        """
        生成建議的資料夾名稱

        格式：{年月}/{類型}
        例如：202601/事件調查
        """
        year_month = ""
        if profile.event_date:
            year_month = profile.event_date.strftime("%Y%m")
        else:
            year_month = date.today().strftime("%Y%m")

        type_name = PROFILE_TYPE_FOLDER_NAMES.get(
            profile.profile_type,
            "其他"
        )

        return f"{year_month}/{type_name}"

    def get_upload_params(self, profile_id: int) -> UploadParams:
        """
        取得上傳參數

        Args:
            profile_id: 履歷 ID

        Returns:
            UploadParams: 上傳所需參數
        """
        profile = self.profile_service.get_by_id(
            profile_id,
            load_relations=True
        )

        if not profile:
            return UploadParams(
                profile_id=profile_id,
                profile_type="",
                employee_id="",
                employee_name="",
                event_date=None,
                department="",
                suggested_folder_name="",
                suggested_file_name="",
                can_upload=False,
                error_message=f"履歷 ID {profile_id} 不存在"
            )

        # 檢查是否可上傳
        can_upload = True
        error_message = None

        # 只有 converted 狀態才能上傳
        if profile.conversion_status != ConversionStatus.CONVERTED.value:
            can_upload = False
            if profile.conversion_status == ConversionStatus.COMPLETED.value:
                error_message = "此履歷已完成，無需再次上傳"
            else:
                error_message = "此履歷尚未產生文件，請先轉換類型"

        # 已有 gdrive_link 則不需再上傳
        if profile.gdrive_link:
            can_upload = False
            error_message = "此履歷已有 Google Drive 連結"

        # 取得員工資訊
        employee_id = ""
        employee_name = ""
        if profile.employee:
            employee_id = profile.employee.employee_no or str(profile.employee_id)
            employee_name = profile.employee.name or ""

        return UploadParams(
            profile_id=profile_id,
            profile_type=profile.profile_type,
            employee_id=employee_id,
            employee_name=employee_name,
            event_date=profile.event_date,
            department=profile.department or "",
            suggested_folder_name=self._generate_folder_name(profile),
            suggested_file_name=self._generate_file_name(profile),
            can_upload=can_upload,
            error_message=error_message
        )

    def complete_upload(
        self,
        profile_id: int,
        gdrive_link: str,
        gdrive_file_id: Optional[str] = None
    ) -> UploadCompleteResult:
        """
        完成上傳（更新 Profile 狀態）

        Args:
            profile_id: 履歷 ID
            gdrive_link: Google Drive 連結
            gdrive_file_id: Google Drive 檔案 ID（可選）

        Returns:
            UploadCompleteResult: 完成結果
        """
        try:
            profile = self.profile_service.mark_completed(
                profile_id,
                gdrive_link
            )

            logger.info(
                "PDF 上傳完成，Profile 已更新",
                profile_id=profile_id,
                gdrive_link=gdrive_link
            )

            return UploadCompleteResult(
                success=True,
                profile_id=profile_id,
                gdrive_link=gdrive_link,
                conversion_status=profile.conversion_status
            )

        except ProfileNotFoundError as e:
            return UploadCompleteResult(
                success=False,
                profile_id=profile_id,
                gdrive_link=None,
                conversion_status="",
                error_message=str(e)
            )
        except Exception as e:
            logger.error(f"更新 Profile 失敗: {e}")
            return UploadCompleteResult(
                success=False,
                profile_id=profile_id,
                gdrive_link=None,
                conversion_status="",
                error_message=f"更新失敗: {str(e)}"
            )


# 工廠函數
def get_pdf_upload_service(db: Session) -> PdfUploadService:
    """取得 PDF 上傳服務實例"""
    return PdfUploadService(db)
