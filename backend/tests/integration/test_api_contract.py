"""
API 契約測試

驗證 CRITICAL 端點的回應格式未被意外修改。
此測試失敗代表破壞了桌面應用的相容性。

參考文檔: docs/API_CONTRACT.md
"""

import pytest


class TestCriticalApiContract:
    """
    測試 CRITICAL 等級的 API 契約

    這些測試確保被桌面應用依賴的端點保持穩定。
    如果這些測試失敗，代表可能破壞了已部署的桌面應用。
    """

    def test_settings_value_endpoint_exists(self, client, admin_token):
        """
        驗證 GET /api/settings/value/{key} 端點存在

        API CONTRACT: CRITICAL
        CONSUMERS: desktop_app/src/utils/backend_api_client.py
        """
        response = client.get(
            "/api/settings/value/test_key",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # 端點應該存在（可能返回 200 或 404，但不應該是 405 Method Not Allowed）
        assert response.status_code != 405, \
            "端點 GET /api/settings/value/{key} 不存在，破壞 CRITICAL 契約"

    def test_settings_value_response_format(self, client, db_session, admin_token):
        """
        驗證 GET /api/settings/value/{key} 的回應格式

        API CONTRACT: CRITICAL
        回應必須包含: key, department, value 三個欄位
        """
        # 先建立測試設定
        from src.models.system_setting import SystemSetting

        setting = SystemSetting(
            key="contract_test_key",
            value="contract_test_value",
            department="淡海",
            description="API 契約測試用設定"
        )
        db_session.add(setting)
        db_session.commit()

        # 呼叫 API
        response = client.get(
            "/api/settings/value/contract_test_key",
            params={"department": "淡海"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200, \
            f"端點回應異常: {response.status_code}"

        data = response.json()

        # 嚴格驗證欄位存在性（這是契約的核心）
        assert "key" in data, \
            "缺少 'key' 欄位，破壞 CRITICAL 契約 - 桌面應用依賴此欄位"
        assert "department" in data, \
            "缺少 'department' 欄位，破壞 CRITICAL 契約 - 桌面應用依賴此欄位"
        assert "value" in data, \
            "缺少 'value' 欄位，破壞 CRITICAL 契約 - 桌面應用依賴此欄位"

    def test_settings_value_field_types(self, client, db_session, admin_token):
        """
        驗證 GET /api/settings/value/{key} 的欄位類型

        API CONTRACT: CRITICAL
        - key: string
        - department: string | null
        - value: string | null
        """
        from src.models.system_setting import SystemSetting

        setting = SystemSetting(
            key="type_test_key",
            value="type_test_value",
            department="安坑"
        )
        db_session.add(setting)
        db_session.commit()

        response = client.get(
            "/api/settings/value/type_test_key",
            params={"department": "安坑"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # 驗證欄位類型
        assert isinstance(data["key"], str), \
            "'key' 欄位類型錯誤，應為 string，破壞 CRITICAL 契約"
        assert data["department"] is None or isinstance(data["department"], str), \
            "'department' 欄位類型錯誤，應為 string | null，破壞 CRITICAL 契約"
        assert data["value"] is None or isinstance(data["value"], str), \
            "'value' 欄位類型錯誤，應為 string | null，破壞 CRITICAL 契約"

    def test_settings_value_with_default(self, client, admin_token):
        """
        驗證 GET /api/settings/value/{key} 支援 default 參數

        API CONTRACT: CRITICAL
        當設定不存在時，應返回 default 值
        """
        response = client.get(
            "/api/settings/value/nonexistent_key",
            params={"default": "fallback_value"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # 即使設定不存在，回應格式也必須符合契約
        assert "key" in data, "缺少 'key' 欄位"
        assert "department" in data, "缺少 'department' 欄位"
        assert "value" in data, "缺少 'value' 欄位"

    def test_settings_value_requires_authentication(self, client):
        """
        驗證端點需要認證

        雖然這不是回應格式的契約，但確保安全性也很重要
        """
        response = client.get("/api/settings/value/any_key")

        # 應該返回 401 或 403
        assert response.status_code in [401, 403], \
            "端點應該需要認證"


class TestContractDocumentation:
    """
    驗證契約文檔的完整性
    """

    def test_api_contract_document_exists(self):
        """
        驗證 API_CONTRACT.md 文檔存在
        """
        import os

        doc_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "..", "docs", "API_CONTRACT.md"
        )

        assert os.path.exists(doc_path), \
            "API_CONTRACT.md 文檔不存在，無法維護 API 穩定性"

    def test_changelog_api_document_exists(self):
        """
        驗證 CHANGELOG_API.md 文檔存在
        """
        import os

        doc_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "..", "docs", "CHANGELOG_API.md"
        )

        assert os.path.exists(doc_path), \
            "CHANGELOG_API.md 文檔不存在，無法追蹤 API 變更歷史"


class TestHealthEndpointContract:
    """
    測試健康檢查端點的契約（後端）

    注意：這是後端的 /health 端點，與桌面應用的 /health 不同
    """

    def test_health_endpoint_exists(self, client):
        """
        驗證 GET /health 端點存在
        """
        response = client.get("/health")

        assert response.status_code == 200, \
            "健康檢查端點應該返回 200"

    def test_health_response_format(self, client):
        """
        驗證健康檢查端點的回應格式
        """
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        # 後端健康檢查應包含基本資訊
        assert "status" in data, "缺少 'status' 欄位"
