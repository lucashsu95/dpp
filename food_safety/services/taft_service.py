import os
import requests
from django.conf import settings

TAFT_API_KEY = os.getenv("TAFT_API_KEY")
TAFT_API_BASE_URL = os.getenv("TAFT_API_BASE_URL")
USE_MOCK_API = os.getenv("USE_MOCK_API", "False").lower() == "true"


def query_by_trace_code(trace_code: str) -> dict | None:
    """
    用追溯碼查產銷履歷
    回傳原始 API 資料，查無資料回傳 None
    """
    if USE_MOCK_API:
        return _mock_trace_code(trace_code)

    url = f"{TAFT_API_BASE_URL}/TraceabilityData"
    params = {
        "$filter": f"TraceCode eq '{trace_code}'",
        "ApiKey": TAFT_API_KEY,
        "$format": "json",
    }
    try:
        res = requests.get(url, params=params, timeout=10)
        res.raise_for_status()
        data = res.json().get("value", [])
        return data[0] if data else None
    except requests.RequestException as e:
        print(f"[TAFT API Error] {e}")
        return None


def query_by_crop_name(crop_name: str) -> list[dict]:
    """
    用作物名稱查，可能回傳多筆
    """
    if USE_MOCK_API:
        return _mock_crop_name(crop_name)

    url = f"{TAFT_API_BASE_URL}/TraceabilityData"
    params = {
        "$filter": f"contains(CropName, '{crop_name}')",
        "ApiKey": TAFT_API_KEY,
        "$format": "json",
        "$top": 10,
    }
    try:
        res = requests.get(url, params=params, timeout=10)
        res.raise_for_status()
        return res.json().get("value", [])
    except requests.RequestException as e:
        print(f"[TAFT API Error] {e}")
        return []


def _mock_trace_code(trace_code: str) -> dict | None:
    """Mock data for development"""
    mock_data = {
        "TW00123456789": {
            "TraceCode": "TW00123456789",
            "CropName": "有機青江菜",
            "FarmerName": "陳農夫",
            "FarmLocation": "台中市大肚區",
            "PlantDate": "2024-01-15",
            "HarvestDate": "2024-03-20",
            "Certification": "有機農產品",
            "CertificateNo": "ORG-2024-001234",
        },
        "TW00123456790": {
            "TraceCode": "TW00123456790",
            "CropName": "青江菜",
            "FarmerName": "林農夫",
            "FarmLocation": "彰化縣員林市",
            "PlantDate": "2024-02-01",
            "HarvestDate": "2024-04-10",
            "Certification": "優良農產品",
            "CertificateNo": "GAP-2024-005678",
        },
        "TW00123456791": {
            "TraceCode": "TW00123456791",
            "CropName": "高麗菜",
            "FarmerName": "王農夫",
            "FarmLocation": "雲林縣斗六市",
            "PlantDate": "2023-11-01",
            "HarvestDate": "2024-02-15",
            "Certification": "優良農產品",
            "CertificateNo": "GAP-2023-009999",
        },
    }
    return mock_data.get(trace_code)


def _mock_crop_name(crop_name: str) -> list[dict]:
    """Mock data for development"""
    mock_data = {
        "青江菜": [
            {
                "TraceCode": "TW00123456789",
                "CropName": "有機青江菜",
                "FarmerName": "陳農夫",
                "FarmLocation": "台中市大肚區",
                "PlantDate": "2024-01-15",
                "HarvestDate": "2024-03-20",
                "Certification": "有機農產品",
                "CertificateNo": "ORG-2024-001234",
            },
            {
                "TraceCode": "TW00123456790",
                "CropName": "青江菜",
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
                "CropName": "高麗菜",
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
        if key in crop_name:
            return value
    return []