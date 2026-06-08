"""
TDD: Tests for MOA (Ministry of Agriculture) pesticide inspection service.
Expected to FAIL initially — once service layer is ready, this MUST pass.
"""

from unittest.mock import patch
from food_safety.services.moa_service import (
    query_inspection_result,
    query_organic_cert,
    query_cas_product,
    query_pesticide_info,
)


def _mock_response(data: list[dict], status_code: int = 200):
    """Helper to build a fake requests.Response."""
    import json
    from unittest.mock import MagicMock

    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = data
    resp.raise_for_status.return_value = None
    return resp


class TestMoaServiceImports:

    def test_query_inspection_result_exists(self):
        assert callable(query_inspection_result)


class TestQueryInspectionResult:

    def test_returns_list_on_success(self):
        records = [
            {"樣品名稱": "小白菜", "檢出藥劑ppm": "0.02"},
            {"樣品名稱": "青江菜", "檢出藥劑ppm": "0.01"},
        ]
        with patch("food_safety.services.moa_service.requests.get") as mock_get:
            mock_get.return_value = _mock_response(records)
            result = query_inspection_result("小白菜")
            assert isinstance(result, list)

    def test_filters_by_crop_name_case_insensitive(self):
        records = [
            {"樣品名稱": "小白菜", "檢出藥劑ppm": "0.02"},
            {"樣品名稱": "青江菜", "檢出藥劑ppm": "0.01"},
        ]
        with patch("food_safety.services.moa_service.requests.get") as mock_get:
            mock_get.return_value = _mock_response(records)
            result = query_inspection_result("白菜")
            assert len(result) == 1
            assert result[0]["樣品名稱"] == "小白菜"

    def test_returns_empty_list_when_no_match(self):
        records = [
            {"樣品名稱": "小白菜", "檢出藥劑ppm": "0.02"},
        ]
        with patch("food_safety.services.moa_service.requests.get") as mock_get:
            mock_get.return_value = _mock_response(records)
            result = query_inspection_result("高麗菜")
            assert result == []

    def test_limits_to_20_records_max(self):
        records = [{"樣品名稱": f"小白菜{i}", "檢出藥劑ppm": "0.02"} for i in range(50)]
        with patch("food_safety.services.moa_service.requests.get") as mock_get:
            mock_get.return_value = _mock_response(records)
            result = query_inspection_result("小白菜")
            assert len(result) <= 20

    def test_returns_empty_list_on_request_exception(self):
        with patch("food_safety.services.moa_service.requests.get") as mock_get:
            mock_get.side_effect = __import__("requests").RequestException("timeout")
            result = query_inspection_result("小白菜")
            assert result == []

    def test_returns_empty_list_on_json_decode_error(self):
        with patch("food_safety.services.moa_service.requests.get") as mock_get:
            resp = _mock_response([])
            resp.json.side_effect = __import__("json").JSONDecodeError("bad json", "", 0)
            mock_get.return_value = resp
            result = query_inspection_result("小白菜")
            assert result == []


class TestQueryOrganicCert:

    def test_returns_list_on_success(self):
        records = [
            {"農產品經營業者_進口業者": "有機農場", "標題": "有機白米"},
            {"農產品經營業者_進口業者": "一般農場", "標題": "一般白米"},
        ]
        with patch("food_safety.services.moa_service.requests.get") as mock_get:
            mock_get.return_value = _mock_response(records)
            result = query_organic_cert("有機農場")
            assert isinstance(result, list)

    def test_filters_by_producer_name(self):
        records = [
            {"農產品經營業者_進口業者": "有機農場", "標題": "有機白米"},
            {"農產品經營業者_進口業者": "一般農場", "標題": "一般白米"},
        ]
        with patch("food_safety.services.moa_service.requests.get") as mock_get:
            mock_get.return_value = _mock_response(records)
            result = query_organic_cert("有機")
            assert len(result) == 1
            assert result[0]["農產品經營業者_進口業者"] == "有機農場"

    def test_case_insensitive(self):
        records = [
            {"農產品經營業者_進口業者": "Organic Farm", "標題": "Organic Rice"},
        ]
        with patch("food_safety.services.moa_service.requests.get") as mock_get:
            mock_get.return_value = _mock_response(records)
            result = query_organic_cert("organic")
            assert len(result) == 1

    def test_returns_empty_list_when_no_match(self):
        records = [
            {"農產品經營業者_進口業者": "有機農場", "標題": "有機白米"},
        ]
        with patch("food_safety.services.moa_service.requests.get") as mock_get:
            mock_get.return_value = _mock_response(records)
            result = query_organic_cert("不存在業者")
            assert result == []

    def test_limits_to_20_records_max(self):
        records = [{"農產品經營業者_進口業者": f"有機農場{i}", "標題": "白米"} for i in range(50)]
        with patch("food_safety.services.moa_service.requests.get") as mock_get:
            mock_get.return_value = _mock_response(records)
            result = query_organic_cert("有機")
            assert len(result) <= 20

    def test_returns_empty_list_on_request_exception(self):
        with patch("food_safety.services.moa_service.requests.get") as mock_get:
            mock_get.side_effect = __import__("requests").RequestException("timeout")
            result = query_organic_cert("有機農場")
            assert result == []

    def test_returns_empty_list_on_json_decode_error(self):
        with patch("food_safety.services.moa_service.requests.get") as mock_get:
            resp = _mock_response([])
            resp.json.side_effect = __import__("json").JSONDecodeError("bad json", "", 0)
            mock_get.return_value = resp
            result = query_organic_cert("有機農場")
            assert result == []

    def test_import_exists(self):
        assert callable(query_organic_cert)


class TestQueryCasProduct:

    def test_returns_list_on_success(self):
        records = [
            {"Product_Name": "CAS白米", "Factory_CName": "米廠A"},
            {"Product_Name": "一般白米", "Factory_CName": "米廠B"},
        ]
        with patch("food_safety.services.moa_service.requests.get") as mock_get:
            mock_get.return_value = _mock_response(records)
            result = query_cas_product("CAS白米")
            assert isinstance(result, list)

    def test_filters_by_product_name_case_insensitive(self):
        records = [
            {"Product_Name": "CAS白米", "Factory_CName": "米廠A"},
            {"Product_Name": "一般白米", "Factory_CName": "米廠B"},
        ]
        with patch("food_safety.services.moa_service.requests.get") as mock_get:
            mock_get.return_value = _mock_response(records)
            result = query_cas_product("cas")
            assert len(result) == 1
            assert result[0]["Product_Name"] == "CAS白米"

    def test_returns_empty_list_when_no_match(self):
        records = [
            {"Product_Name": "CAS白米", "Factory_CName": "米廠A"},
        ]
        with patch("food_safety.services.moa_service.requests.get") as mock_get:
            mock_get.return_value = _mock_response(records)
            result = query_cas_product("高麗菜")
            assert result == []

    def test_limits_to_20_records_max(self):
        records = [{"Product_Name": f"CASA產品{i}", "Factory_CName": "米廠"} for i in range(50)]
        with patch("food_safety.services.moa_service.requests.get") as mock_get:
            mock_get.return_value = _mock_response(records)
            result = query_cas_product("CASA")
            assert len(result) <= 20

    def test_returns_empty_list_on_request_exception(self):
        with patch("food_safety.services.moa_service.requests.get") as mock_get:
            mock_get.side_effect = __import__("requests").RequestException("timeout")
            result = query_cas_product("CAS白米")
            assert result == []

    def test_returns_empty_list_on_json_decode_error(self):
        with patch("food_safety.services.moa_service.requests.get") as mock_get:
            resp = _mock_response([])
            resp.json.side_effect = __import__("json").JSONDecodeError("bad json", "", 0)
            mock_get.return_value = resp
            result = query_cas_product("CAS白米")
            assert result == []

    def test_import_exists(self):
        assert callable(query_cas_product)


class TestQueryPesticideInfo:

    def test_returns_list_on_success(self):
        records = [
            {"中文名稱": "敵敵威", "許可證號": "農藥字第123號"},
            {"中文名稱": "滅蟻靈", "許可證號": "農藥字第456號"},
        ]
        with patch("food_safety.services.moa_service.requests.get") as mock_get:
            mock_get.return_value = _mock_response(records)
            result = query_pesticide_info("敵敵威")
            assert isinstance(result, list)

    def test_filters_by_pesticide_name_case_insensitive(self):
        records = [
            {"中文名稱": "敵敵威", "許可證號": "農藥字第123號"},
            {"中文名稱": "滅蟻靈", "許可證號": "農藥字第456號"},
        ]
        with patch("food_safety.services.moa_service.requests.get") as mock_get:
            mock_get.return_value = _mock_response(records)
            result = query_pesticide_info("敵敵")
            assert len(result) == 1
            assert result[0]["中文名稱"] == "敵敵威"

    def test_returns_empty_list_when_no_match(self):
        records = [
            {"中文名稱": "敵敵威", "許可證號": "農藥字第123號"},
        ]
        with patch("food_safety.services.moa_service.requests.get") as mock_get:
            mock_get.return_value = _mock_response(records)
            result = query_pesticide_info("不存在農藥")
            assert result == []

    def test_limits_to_20_records_max(self):
        records = [{"中文名稱": f"農藥{i}", "許可證號": "農藥字第123號"} for i in range(50)]
        with patch("food_safety.services.moa_service.requests.get") as mock_get:
            mock_get.return_value = _mock_response(records)
            result = query_pesticide_info("農藥")
            assert len(result) <= 20

    def test_returns_empty_list_on_request_exception(self):
        with patch("food_safety.services.moa_service.requests.get") as mock_get:
            mock_get.side_effect = __import__("requests").RequestException("timeout")
            result = query_pesticide_info("敵敵威")
            assert result == []

    def test_returns_empty_list_on_json_decode_error(self):
        with patch("food_safety.services.moa_service.requests.get") as mock_get:
            resp = _mock_response([])
            resp.json.side_effect = __import__("json").JSONDecodeError("bad json", "", 0)
            mock_get.return_value = resp
            result = query_pesticide_info("敵敵威")
            assert result == []

    def test_import_exists(self):
        assert callable(query_pesticide_info)
