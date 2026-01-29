"""
Google Drive 上傳服務
對應 tasks.md T093: 實作 Google Drive 上傳服務

功能：
- 上傳檔案到 Google Drive
- 使用 OAuth 令牌（從本機憑證管理器取得）
- 依部門上傳到對應資料夾

依賴：
- google-api-python-client
- google-auth
"""

import logging
import mimetypes
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class UploadResult:
    """上傳結果"""
    success: bool                 # 是否成功
    file_id: Optional[str]        # Google Drive 檔案 ID
    web_view_link: Optional[str]  # 網頁檢視連結
    web_content_link: Optional[str]  # 下載連結
    file_name: str                # 檔案名稱
    folder_id: Optional[str]      # 上傳到的資料夾 ID
    error_message: Optional[str] = None  # 錯誤訊息


class GoogleDriveUploader:
    """Google Drive 上傳器"""

    # MIME 類型對應
    MIME_TYPES = {
        '.pdf': 'application/pdf',
        '.doc': 'application/msword',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.xls': 'application/vnd.ms-excel',
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.txt': 'text/plain',
    }

    def __init__(self, credentials=None):
        """
        初始化上傳器

        Args:
            credentials: Google OAuth 憑證物件，None 則需要在上傳時提供
        """
        self.credentials = credentials
        self._service = None

    def _get_service(self, credentials=None):
        """
        取得 Google Drive API 服務

        Args:
            credentials: OAuth 憑證，None 則使用初始化時的憑證

        Returns:
            Google Drive API 服務物件
        """
        from googleapiclient.discovery import build

        creds = credentials or self.credentials
        if not creds:
            raise ValueError("未提供 Google 憑證")

        return build('drive', 'v3', credentials=creds)

    def upload_file(
        self,
        file_path: str | Path,
        folder_id: Optional[str] = None,
        file_name: Optional[str] = None,
        credentials=None,
        description: Optional[str] = None
    ) -> UploadResult:
        """
        上傳檔案到 Google Drive

        Args:
            file_path: 本機檔案路徑
            folder_id: 目標資料夾 ID，None 則上傳到根目錄
            file_name: 在 Drive 上的檔案名稱，None 則使用原檔名
            credentials: OAuth 憑證，None 則使用初始化時的憑證
            description: 檔案描述

        Returns:
            UploadResult
        """
        from googleapiclient.http import MediaFileUpload
        from googleapiclient.errors import HttpError

        file_path = Path(file_path)
        if not file_path.exists():
            return UploadResult(
                success=False,
                file_id=None,
                web_view_link=None,
                web_content_link=None,
                file_name=str(file_path.name),
                folder_id=folder_id,
                error_message=f"檔案不存在: {file_path}"
            )

        # 決定檔案名稱
        upload_name = file_name or file_path.name

        # 決定 MIME 類型
        suffix = file_path.suffix.lower()
        mime_type = self.MIME_TYPES.get(suffix)
        if not mime_type:
            mime_type, _ = mimetypes.guess_type(str(file_path))
            mime_type = mime_type or 'application/octet-stream'

        try:
            service = self._get_service(credentials)

            # 建立檔案元數據
            file_metadata = {
                'name': upload_name,
            }

            if folder_id:
                file_metadata['parents'] = [folder_id]

            if description:
                file_metadata['description'] = description

            # 建立媒體上傳物件
            media = MediaFileUpload(
                str(file_path),
                mimetype=mime_type,
                resumable=True
            )

            # 執行上傳
            logger.info(f"開始上傳: {file_path} -> {upload_name}")
            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink, webContentLink'
            ).execute()

            logger.info(f"上傳成功: {file.get('name')} (ID: {file.get('id')})")

            return UploadResult(
                success=True,
                file_id=file.get('id'),
                web_view_link=file.get('webViewLink'),
                web_content_link=file.get('webContentLink'),
                file_name=file.get('name'),
                folder_id=folder_id
            )

        except HttpError as e:
            error_msg = f"Google Drive API 錯誤: {e.reason}"
            logger.error(error_msg)
            return UploadResult(
                success=False,
                file_id=None,
                web_view_link=None,
                web_content_link=None,
                file_name=upload_name,
                folder_id=folder_id,
                error_message=error_msg
            )
        except Exception as e:
            error_msg = f"上傳失敗: {str(e)}"
            logger.error(error_msg)
            return UploadResult(
                success=False,
                file_id=None,
                web_view_link=None,
                web_content_link=None,
                file_name=upload_name,
                folder_id=folder_id,
                error_message=error_msg
            )

    def upload_bytes(
        self,
        data: bytes,
        file_name: str,
        folder_id: Optional[str] = None,
        mime_type: str = 'application/octet-stream',
        credentials=None,
        description: Optional[str] = None
    ) -> UploadResult:
        """
        上傳 bytes 資料到 Google Drive

        Args:
            data: 檔案內容
            file_name: 檔案名稱
            folder_id: 目標資料夾 ID
            mime_type: MIME 類型
            credentials: OAuth 憑證
            description: 檔案描述

        Returns:
            UploadResult
        """
        import io
        from googleapiclient.http import MediaIoBaseUpload
        from googleapiclient.errors import HttpError

        try:
            service = self._get_service(credentials)

            file_metadata = {
                'name': file_name,
            }

            if folder_id:
                file_metadata['parents'] = [folder_id]

            if description:
                file_metadata['description'] = description

            # 建立媒體上傳物件
            media = MediaIoBaseUpload(
                io.BytesIO(data),
                mimetype=mime_type,
                resumable=True
            )

            # 執行上傳
            logger.info(f"開始上傳 bytes 資料: {file_name}")
            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink, webContentLink'
            ).execute()

            logger.info(f"上傳成功: {file.get('name')} (ID: {file.get('id')})")

            return UploadResult(
                success=True,
                file_id=file.get('id'),
                web_view_link=file.get('webViewLink'),
                web_content_link=file.get('webContentLink'),
                file_name=file.get('name'),
                folder_id=folder_id
            )

        except HttpError as e:
            error_msg = f"Google Drive API 錯誤: {e.reason}"
            logger.error(error_msg)
            return UploadResult(
                success=False,
                file_id=None,
                web_view_link=None,
                web_content_link=None,
                file_name=file_name,
                folder_id=folder_id,
                error_message=error_msg
            )
        except Exception as e:
            error_msg = f"上傳失敗: {str(e)}"
            logger.error(error_msg)
            return UploadResult(
                success=False,
                file_id=None,
                web_view_link=None,
                web_content_link=None,
                file_name=file_name,
                folder_id=folder_id,
                error_message=error_msg
            )

    def set_permissions(
        self,
        file_id: str,
        role: str = 'reader',
        type: str = 'domain',
        domain: Optional[str] = None,
        email: Optional[str] = None,
        credentials=None
    ) -> bool:
        """
        設定檔案權限

        Args:
            file_id: 檔案 ID
            role: 角色 (reader, writer, commenter, owner)
            type: 類型 (user, group, domain, anyone)
            domain: 網域（type='domain' 時必填）
            email: 電子郵件（type='user' 或 'group' 時必填）
            credentials: OAuth 憑證

        Returns:
            是否成功
        """
        from googleapiclient.errors import HttpError

        try:
            service = self._get_service(credentials)

            permission = {
                'role': role,
                'type': type,
            }

            if domain and type == 'domain':
                permission['domain'] = domain

            if email and type in ('user', 'group'):
                permission['emailAddress'] = email

            service.permissions().create(
                fileId=file_id,
                body=permission,
                fields='id'
            ).execute()

            logger.info(f"已設定權限: {file_id} -> {role}/{type}")
            return True

        except HttpError as e:
            logger.error(f"設定權限失敗: {e.reason}")
            return False
        except Exception as e:
            logger.error(f"設定權限失敗: {str(e)}")
            return False

    def create_folder(
        self,
        folder_name: str,
        parent_folder_id: Optional[str] = None,
        credentials=None
    ) -> Optional[str]:
        """
        建立資料夾

        Args:
            folder_name: 資料夾名稱
            parent_folder_id: 父資料夾 ID
            credentials: OAuth 憑證

        Returns:
            新資料夾的 ID，失敗則返回 None
        """
        from googleapiclient.errors import HttpError

        try:
            service = self._get_service(credentials)

            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }

            if parent_folder_id:
                file_metadata['parents'] = [parent_folder_id]

            folder = service.files().create(
                body=file_metadata,
                fields='id'
            ).execute()

            folder_id = folder.get('id')
            logger.info(f"已建立資料夾: {folder_name} (ID: {folder_id})")
            return folder_id

        except HttpError as e:
            logger.error(f"建立資料夾失敗: {e.reason}")
            return None
        except Exception as e:
            logger.error(f"建立資料夾失敗: {str(e)}")
            return None

    def list_files(
        self,
        folder_id: Optional[str] = None,
        query: Optional[str] = None,
        page_size: int = 100,
        credentials=None
    ) -> list[dict]:
        """
        列出檔案

        Args:
            folder_id: 資料夾 ID，None 則列出所有檔案
            query: 額外的查詢條件
            page_size: 每頁數量
            credentials: OAuth 憑證

        Returns:
            檔案資訊列表
        """
        from googleapiclient.errors import HttpError

        try:
            service = self._get_service(credentials)

            # 建立查詢條件
            q_parts = []
            if folder_id:
                q_parts.append(f"'{folder_id}' in parents")
            if query:
                q_parts.append(query)

            q = ' and '.join(q_parts) if q_parts else None

            results = service.files().list(
                q=q,
                pageSize=page_size,
                fields="files(id, name, mimeType, size, createdTime, webViewLink)"
            ).execute()

            files = results.get('files', [])
            logger.info(f"找到 {len(files)} 個檔案")
            return files

        except HttpError as e:
            logger.error(f"列出檔案失敗: {e.reason}")
            return []
        except Exception as e:
            logger.error(f"列出檔案失敗: {str(e)}")
            return []


def create_uploader_with_token(
    access_token: str,
    refresh_token: Optional[str] = None,
    token_uri: str = "https://oauth2.googleapis.com/token",
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None
) -> GoogleDriveUploader:
    """
    使用 Access Token 建立上傳器

    Args:
        access_token: Access Token
        refresh_token: Refresh Token（可選，用於自動刷新）
        token_uri: Token URI
        client_id: Client ID（自動刷新時需要）
        client_secret: Client Secret（自動刷新時需要）

    Returns:
        GoogleDriveUploader 實例
    """
    from google.oauth2.credentials import Credentials

    credentials = Credentials(
        token=access_token,
        refresh_token=refresh_token,
        token_uri=token_uri,
        client_id=client_id,
        client_secret=client_secret
    )

    return GoogleDriveUploader(credentials=credentials)


def create_uploader_from_credential_manager(
    department: str
) -> Optional[GoogleDriveUploader]:
    """
    從本機憑證管理器建立上傳器

    Args:
        department: 部門名稱（淡海 或 安坑）

    Returns:
        GoogleDriveUploader 實例，失敗則返回 None
    """
    from desktop_app.src.utils.credential_manager import get_credential_manager

    manager = get_credential_manager()

    # 檢查是否有該部門的令牌
    if department not in manager.list_departments():
        logger.error(f"找不到部門 {department} 的 OAuth 令牌")
        return None

    # 檢查令牌是否過期
    if manager.is_token_expired(department):
        logger.warning(f"部門 {department} 的令牌已過期，需要重新授權")
        return None

    # 取得令牌
    token_data = manager.get_token(department)
    if not token_data:
        logger.error(f"無法取得部門 {department} 的令牌")
        return None

    return create_uploader_with_token(
        access_token=token_data.get('access_token', ''),
        refresh_token=token_data.get('refresh_token'),
        client_id=token_data.get('client_id'),
        client_secret=token_data.get('client_secret')
    )
