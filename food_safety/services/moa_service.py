import requests
from requests import RequestException
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

MOA_API_BASE_URL = "https://data.moa.gov.tw/Service/OpenData/DataFileService.aspx"
MOA_API_TRANS_URL = "https://data.moa.gov.tw/Service/OpenData/TransService.aspx"
MOA_PESTICIDE_DATA_URL = "https://data.moa.gov.tw/Service/OpenData/FromM/PesticideData.aspx"
MOA_UNIT_ID_INSPECTION = "271"
MOA_UNIT_ID_ORGANIC = "270"
MOA_UNIT_ID_CAS = "qNRePfOf8YMS"


def _moa_request(url: str, params: dict | None = None) -> list[dict] | None:
    """
    Internal helper with retry logic for MOA API calls.
    Only retries on RequestException (network errors, 5xx), not on 4xx.
    """
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        retry=retry_if_exception_type(RequestException),
        reraise=True,
    )
    def _request():
        res = requests.get(url, params=params, timeout=10)
        res.raise_for_status()
        return res.json()

    return _request()


def query_inspection_result(crop_name: str) -> list[dict]:
    """
    用作物名稱查農藥殘留檢驗結果。
    過濾樣品名稱包含 crop_name 的資料，最多回傳 20 筆。
    """
    params = {"UnitId": MOA_UNIT_ID_INSPECTION}
    try:
        data = _moa_request(MOA_API_BASE_URL, params)
    except (RequestException, ValueError):
        return []

    if not data:
        return []

    matched = [
        record
        for record in data
        if crop_name.lower() in record.get("樣品名稱", "").lower()
    ]
    return matched[:20]


def query_organic_cert(producer_name: str) -> list[dict]:
    """
    用業者名稱查有機農產品驗證資料。
    過濾農產品經營業者_進口業者包含 producer_name 的資料，最多回傳 20 筆。
    """
    params = {"UnitId": MOA_UNIT_ID_ORGANIC}
    try:
        data = _moa_request(MOA_API_BASE_URL, params)
    except (RequestException, ValueError):
        return []

    if not data:
        return []

    matched = [
        record
        for record in data
        if producer_name.lower() in record.get("農產品經營業者_進口業者", "").lower()
    ]
    return matched[:20]


def query_cas_product(product_name: str) -> list[dict]:
    """
    用產品名稱查 CAS 驗證資料。
    過濾 Product_Name 包含 product_name 的資料，最多回傳 20 筆。
    """
    params = {"UnitId": MOA_UNIT_ID_CAS}
    try:
        data = _moa_request(MOA_API_TRANS_URL, params)
    except (RequestException, ValueError):
        return []

    if not data:
        return []

    matched = [
        record
        for record in data
        if product_name.lower() in record.get("Product_Name", "").lower()
    ]
    return matched[:20]


def query_pesticide_info(pesticide_name: str) -> list[dict]:
    """
    用農藥名稱查農藥資訊資料。
    過濾中文名稱包含 pesticide_name 的資料，最多回傳 20 筆。
    """
    try:
        data = _moa_request(MOA_PESTICIDE_DATA_URL)
    except (RequestException, ValueError):
        return []

    if not data:
        return []

    matched = [
        record
        for record in data
        if pesticide_name.lower() in record.get("中文名稱", "").lower()
    ]
    return matched[:20]
