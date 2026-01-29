"""
Google OAuth API 端點
對應 tasks.md T096-T098: 實作 OAuth 授權流程

功能：
- GET /api/google/auth-url: 生成 OAuth 授權 URL
- GET /api/auth/google/callback: OAuth 回調處理
- POST /api/google/get-access-token: 取得 Access Token
- GET /api/google/oauth-status: 檢查 OAuth 狀態
- DELETE /api/google/revoke: 撤銷授權
"""

import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.config.settings import get_settings
from src.middleware.auth import get_current_user, require_roles
from src.models.google_oauth_token import GoogleOAuthToken
from src.models.oauth_state import OAuthState
from src.models.user import User
from src.utils.encryption import encrypt_token, decrypt_token

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Google OAuth"])


# ============================================================
# Constants
# ============================================================

# Google OAuth 端點
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

# OAuth Scopes（僅需要 Drive 寫入權限）
OAUTH_SCOPES = [
    "https://www.googleapis.com/auth/drive.file",  # 僅存取應用程式建立的檔案
    "https://www.googleapis.com/auth/userinfo.email",  # 取得使用者 Email
]

# 有效部門
VALID_DEPARTMENTS = ["淡海", "安坑"]


# ============================================================
# Pydantic Models
# ============================================================

class AuthUrlResponse(BaseModel):
    """授權 URL 回應"""
    auth_url: str
    state: str
    department: str


class OAuthStatusResponse(BaseModel):
    """OAuth 狀態回應"""
    department: str
    is_authorized: bool
    authorized_email: Optional[str] = None
    access_token_valid: bool = False
    expires_at: Optional[datetime] = None


class AccessTokenResponse(BaseModel):
    """Access Token 回應"""
    success: bool
    department: str
    access_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    error_message: Optional[str] = None


class RevokeResponse(BaseModel):
    """撤銷授權回應"""
    success: bool
    department: str
    message: str


# ============================================================
# Helper Functions
# ============================================================

def _get_oauth_credentials():
    """取得 OAuth 憑證設定"""
    settings = get_settings()

    client_id = getattr(settings, 'google_oauth_client_id', None)
    client_secret = getattr(settings, 'google_oauth_client_secret', None)
    redirect_uri = getattr(settings, 'google_oauth_redirect_uri', None)

    if not all([client_id, client_secret]):
        raise HTTPException(
            status_code=500,
            detail="Google OAuth 未設定。請在環境變數中設定 GOOGLE_OAUTH_CLIENT_ID 和 GOOGLE_OAUTH_CLIENT_SECRET"
        )

    return client_id, client_secret, redirect_uri


def _generate_state_token(department: str, db: Session) -> str:
    """
    生成並儲存 state token 到資料庫

    Args:
        department: 部門名稱
        db: 資料庫 session

    Returns:
        str: 生成的 state token
    """
    state = secrets.token_urlsafe(32)

    # 建立 state token 記錄
    oauth_state = OAuthState.create_state(
        state=state,
        department=department,
        expires_in_minutes=10
    )

    db.add(oauth_state)
    db.commit()

    # 清理過期的 state tokens
    OAuthState.cleanup_expired(db)

    return state


def _validate_state_token(state: str, db: Session) -> Optional[str]:
    """
    驗證 state token 並標記為已使用

    Args:
        state: State token
        db: 資料庫 session

    Returns:
        Optional[str]: 部門名稱，驗證失敗則返回 None
    """
    # 查詢 state token
    oauth_state = db.query(OAuthState).filter(
        OAuthState.state == state
    ).first()

    if not oauth_state:
        return None

    # 檢查是否有效
    if not oauth_state.is_valid():
        return None

    # 標記為已使用
    department = oauth_state.department
    oauth_state.mark_as_used()
    db.commit()

    return department


# ============================================================
# API Endpoints
# ============================================================

@router.get("/api/google/auth-url", response_model=AuthUrlResponse)
async def get_auth_url(
    department: str = Query(..., description="部門名稱（淡海 或 安坑）"),
    current_user: User = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db)
):
    """
    生成 Google OAuth 授權 URL

    僅限 Admin 角色使用。
    使用者將被導向 Google 授權頁面，授權後會回調到本系統。
    """
    if department not in VALID_DEPARTMENTS:
        raise HTTPException(
            status_code=400,
            detail=f"無效的部門: {department}，僅支援 淡海 或 安坑"
        )

    client_id, client_secret, redirect_uri = _get_oauth_credentials()

    if not redirect_uri:
        # 自動生成預設 redirect URI
        settings = get_settings()
        base_url = getattr(settings, 'api_base_url', 'http://localhost:8000')
        redirect_uri = f"{base_url}/api/auth/google/callback"

    # 生成 state token
    state = _generate_state_token(department, db)

    # 建立授權 URL
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(OAUTH_SCOPES),
        "access_type": "offline",  # 取得 refresh_token
        "prompt": "consent",  # 強制顯示同意畫面（確保取得 refresh_token）
        "state": state,
    }

    auth_url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"

    logger.info(f"已生成 OAuth 授權 URL for {department}")

    return AuthUrlResponse(
        auth_url=auth_url,
        state=state,
        department=department
    )


@router.get("/api/auth/google/callback")
async def oauth_callback(
    request: Request,
    code: Optional[str] = Query(None, description="授權碼"),
    state: Optional[str] = Query(None, description="State token"),
    error: Optional[str] = Query(None, description="錯誤代碼"),
    error_description: Optional[str] = Query(None, description="錯誤描述"),
    db: Session = Depends(get_db)
):
    """
    Google OAuth 回調端點

    處理 Google 授權後的回調，換取 refresh_token 並加密儲存。
    """
    import httpx

    # 處理授權拒絕
    if error:
        logger.warning(f"OAuth 授權被拒絕: {error} - {error_description}")
        return HTMLResponse(
            content=f"""
            <html>
            <head><title>授權失敗</title></head>
            <body>
                <h1>授權失敗</h1>
                <p>錯誤: {error}</p>
                <p>描述: {error_description or '使用者拒絕授權'}</p>
                <p>請關閉此視窗並重試。</p>
                <script>
                    setTimeout(function() {{ window.close(); }}, 5000);
                </script>
            </body>
            </html>
            """,
            status_code=400
        )

    # 驗證必要參數
    if not code or not state:
        raise HTTPException(
            status_code=400,
            detail="缺少必要參數: code 或 state"
        )

    # 驗證 state token
    department = _validate_state_token(state, db)
    if not department:
        raise HTTPException(
            status_code=400,
            detail="無效或過期的 state token"
        )

    # 取得 OAuth 憑證
    client_id, client_secret, redirect_uri = _get_oauth_credentials()

    if not redirect_uri:
        settings = get_settings()
        base_url = getattr(settings, 'api_base_url', 'http://localhost:8000')
        redirect_uri = f"{base_url}/api/auth/google/callback"

    try:
        # 換取 tokens
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri,
                }
            )

            if token_response.status_code != 200:
                logger.error(f"Token 交換失敗: {token_response.text}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Token 交換失敗: {token_response.json().get('error_description', 'Unknown error')}"
                )

            tokens = token_response.json()

        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")
        expires_in = tokens.get("expires_in", 3600)

        if not refresh_token:
            raise HTTPException(
                status_code=400,
                detail="未取得 refresh_token。請確保授權時使用 access_type=offline 和 prompt=consent"
            )

        # 取得使用者資訊
        async with httpx.AsyncClient() as client:
            userinfo_response = await client.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"}
            )

            if userinfo_response.status_code == 200:
                userinfo = userinfo_response.json()
                user_email = userinfo.get("email")
            else:
                user_email = None

        # 加密並儲存 tokens
        encrypted_refresh = encrypt_token(refresh_token).encode('utf-8')
        encrypted_access = encrypt_token(access_token).encode('utf-8') if access_token else None
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

        # 檢查是否已存在
        existing_token = db.query(GoogleOAuthToken).filter(
            GoogleOAuthToken.department == department
        ).first()

        if existing_token:
            # 更新
            existing_token.encrypted_refresh_token = encrypted_refresh
            existing_token.encrypted_access_token = encrypted_access
            existing_token.access_token_expires_at = expires_at
            existing_token.authorized_user_email = user_email
        else:
            # 新增
            new_token = GoogleOAuthToken(
                department=department,
                encrypted_refresh_token=encrypted_refresh,
                encrypted_access_token=encrypted_access,
                access_token_expires_at=expires_at,
                authorized_user_email=user_email
            )
            db.add(new_token)

        db.commit()

        logger.info(f"OAuth 授權成功: {department} by {user_email}")

        # 返回成功頁面
        return HTMLResponse(
            content=f"""
            <html>
            <head><title>授權成功</title></head>
            <body>
                <h1>授權成功！</h1>
                <p>部門: {department}</p>
                <p>授權帳號: {user_email or '未知'}</p>
                <p>此視窗將在 3 秒後自動關閉...</p>
                <script>
                    setTimeout(function() {{ window.close(); }}, 3000);
                </script>
            </body>
            </html>
            """
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth 回調處理失敗: {e}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"OAuth 處理失敗: {str(e)}"
        )


@router.post("/api/google/get-access-token", response_model=AccessTokenResponse)
async def get_access_token(
    department: str = Query(..., description="部門名稱"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    取得 Access Token

    如果已快取的 access_token 未過期，直接返回；
    否則使用 refresh_token 刷新並返回新的 access_token。
    """
    import httpx

    if department not in VALID_DEPARTMENTS:
        return AccessTokenResponse(
            success=False,
            department=department,
            error_message=f"無效的部門: {department}"
        )

    # 查詢儲存的 token
    token_record = db.query(GoogleOAuthToken).filter(
        GoogleOAuthToken.department == department
    ).first()

    if not token_record:
        return AccessTokenResponse(
            success=False,
            department=department,
            error_message=f"部門 {department} 尚未完成 OAuth 授權"
        )

    # 檢查 access_token 是否有效
    if (
        token_record.encrypted_access_token and
        token_record.access_token_expires_at and
        token_record.access_token_expires_at > datetime.now(timezone.utc) + timedelta(minutes=5)
    ):
        # 使用快取的 access_token
        access_token = decrypt_token(token_record.encrypted_access_token.decode('utf-8'))
        return AccessTokenResponse(
            success=True,
            department=department,
            access_token=access_token,
            expires_at=token_record.access_token_expires_at
        )

    # 需要刷新 token
    try:
        refresh_token = decrypt_token(token_record.encrypted_refresh_token.decode('utf-8'))

        client_id, client_secret, _ = _get_oauth_credentials()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                }
            )

            if response.status_code != 200:
                error_data = response.json()
                logger.error(f"Token 刷新失敗: {error_data}")
                return AccessTokenResponse(
                    success=False,
                    department=department,
                    error_message=f"Token 刷新失敗: {error_data.get('error_description', 'Unknown error')}"
                )

            tokens = response.json()

        new_access_token = tokens.get("access_token")
        expires_in = tokens.get("expires_in", 3600)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

        # 更新快取
        token_record.encrypted_access_token = encrypt_token(new_access_token).encode('utf-8')
        token_record.access_token_expires_at = expires_at
        db.commit()

        logger.info(f"已刷新 {department} 的 access_token")

        return AccessTokenResponse(
            success=True,
            department=department,
            access_token=new_access_token,
            expires_at=expires_at
        )

    except Exception as e:
        logger.error(f"取得 access_token 失敗: {e}")
        return AccessTokenResponse(
            success=False,
            department=department,
            error_message=str(e)
        )


@router.get("/api/google/oauth-status", response_model=list[OAuthStatusResponse])
async def get_oauth_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    檢查所有部門的 OAuth 狀態
    """
    results = []

    for dept in VALID_DEPARTMENTS:
        token_record = db.query(GoogleOAuthToken).filter(
            GoogleOAuthToken.department == dept
        ).first()

        if token_record:
            access_token_valid = (
                token_record.encrypted_access_token is not None and
                token_record.access_token_expires_at is not None and
                token_record.access_token_expires_at > datetime.now(timezone.utc)
            )

            results.append(OAuthStatusResponse(
                department=dept,
                is_authorized=True,
                authorized_email=token_record.authorized_user_email,
                access_token_valid=access_token_valid,
                expires_at=token_record.access_token_expires_at
            ))
        else:
            results.append(OAuthStatusResponse(
                department=dept,
                is_authorized=False
            ))

    return results


@router.delete("/api/google/revoke", response_model=RevokeResponse)
async def revoke_oauth(
    department: str = Query(..., description="部門名稱"),
    current_user: User = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db)
):
    """
    撤銷 OAuth 授權

    僅限 Admin 角色使用。
    """
    import httpx

    if department not in VALID_DEPARTMENTS:
        raise HTTPException(
            status_code=400,
            detail=f"無效的部門: {department}"
        )

    token_record = db.query(GoogleOAuthToken).filter(
        GoogleOAuthToken.department == department
    ).first()

    if not token_record:
        return RevokeResponse(
            success=False,
            department=department,
            message=f"部門 {department} 沒有已授權的 OAuth 憑證"
        )

    try:
        # 嘗試撤銷 Google 端的授權
        if token_record.encrypted_access_token:
            access_token = decrypt_token(token_record.encrypted_access_token.decode('utf-8'))

            async with httpx.AsyncClient() as client:
                await client.post(
                    "https://oauth2.googleapis.com/revoke",
                    params={"token": access_token}
                )
                # 忽略撤銷結果（可能已過期）

        # 刪除資料庫記錄
        db.delete(token_record)
        db.commit()

        logger.info(f"已撤銷 {department} 的 OAuth 授權")

        return RevokeResponse(
            success=True,
            department=department,
            message=f"已成功撤銷 {department} 的 OAuth 授權"
        )

    except Exception as e:
        logger.error(f"撤銷 OAuth 授權失敗: {e}")
        db.rollback()
        return RevokeResponse(
            success=False,
            department=department,
            message=f"撤銷失敗: {str(e)}"
        )
