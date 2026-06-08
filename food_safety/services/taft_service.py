import os
import requests
from django.conf import settings

TAFT_API_BASE_URL = os.getenv("TAFT_API_BASE_URL")
TAFT_UNIT_ID = os.getenv("TAFT_UNIT_ID", "063")
USE_MOCK_API = os.getenv("USE_MOCK_API", "False").lower() == "true"


def query_by_trace_code(trace_code: str) -> dict | None:
    """
    用追溯碼查產銷履歷
    回傳原始 API 資料，查無資料回傳 None
    """
    if USE_MOCK_API:
        return _mock_trace_code(trace_code)

    url = TAFT_API_BASE_URL
    params = {
        "Tracecode": trace_code,
        "UnitId": TAFT_UNIT_ID,
    }
    try:
        res = requests.get(url, params=params, timeout=10)
        res.raise_for_status()
        data = res.json()
        return data[0] if data else None
    except requests.RequestException as e:
        print(f"[TAFT API Error] {e}")
        return None


def query_by_product_name(product_name: str) -> list[dict]:
    """
    用產品名稱查，可能回傳多筆
    最多回傳 20 筆
    """
    if USE_MOCK_API:
        return _mock_product_name(product_name)

    url = TAFT_API_BASE_URL
    params = {
        "ProductName": product_name,
        "UnitId": TAFT_UNIT_ID,
    }
    try:
        res = requests.get(url, params=params, timeout=10)
        res.raise_for_status()
        data = res.json()
        return data[:20]
    except requests.RequestException as e:
        print(f"[TAFT API Error] {e}")
        return []


def _mock_trace_code(trace_code: str) -> dict | None:
    """Mock data for development"""
    mock_data = {
        "TW00123456789": {
            "TraceCode": "TW00123456789",
            "ProductName": "有機青江菜",
            "FarmerName": "陳農夫",
            "FarmLocation": "台中市大肚區",
            "PlantDate": "2024-01-15",
            "HarvestDate": "2024-03-20",
            "Certification": "有機農產品",
            "CertificateNo": "ORG-2024-001234",
        },
        "TW00123456790": {
            "TraceCode": "TW00123456790",
            "ProductName": "青江菜",
            "FarmerName": "林農夫",
            "FarmLocation": "彰化縣員林市",
            "PlantDate": "2024-02-01",
            "HarvestDate": "2024-04-10",
            "Certification": "優良農產品",
            "CertificateNo": "GAP-2024-005678",
        },
        "TW00123456791": {
            "TraceCode": "TW00123456791",
            "ProductName": "高麗菜",
            "FarmerName": "王農夫",
            "FarmLocation": "雲林縣斗六市",
            "PlantDate": "2023-11-01",
            "HarvestDate": "2024-02-15",
            "Certification": "優良農產品",
            "CertificateNo": "GAP-2023-009999",
        },
    }
    return mock_data.get(trace_code)


def _mock_product_name(product_name: str) -> list[dict]:
    """Mock data for development"""
    mock_data = {
        "青江菜": [
            {
                "TraceCode": "TW00123456789",
                "ProductName": "有機青江菜",
                "FarmerName": "陳農夫",
                "FarmLocation": "台中市大肚區",
                "PlantDate": "2024-01-15",
                "HarvestDate": "2024-03-20",
                "Certification": "有機農產品",
                "CertificateNo": "ORG-2024-001234",
            },
            {
                "TraceCode": "TW00123456790",
                "ProductName": "青江菜",
                "FarmerName": "林農夫",
                "FarmLocation": "彰化縣員林市",
                "PlantDate": "2024-02-01",
                "HarvestDate": "2024-04-10",
                "Certification": "優良農產品",
                "CertificateNo": "GAP-2024-005678",
            },
        ],
        "高麗菜": [
            {
                "TraceCode": "TW00123456791",
                "ProductName": "高麗菜",
                "FarmerName": "王農夫",
                "FarmLocation": "雲林縣斗六市",
                "PlantDate": "2023-11-01",
                "HarvestDate": "2024-02-15",
                "Certification": "優良農產品",
                "CertificateNo": "GAP-2023-009999",
            }
        ],
    }
    for key, value in mock_data.items():
        if key in product_name:
            return value
    return []
