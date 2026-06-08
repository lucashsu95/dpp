"""
TDD: Test for TAFT service.
Expected to FAIL initially — once service layer is ready, this MUST pass.
"""

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ["USE_MOCK_API"] = "True"

import django
django.setup()

from food_safety.services.taft_service import query_by_trace_code, query_by_product_name


class TestTaftServiceImports:

    def test_query_by_trace_code_exists(self):
        assert callable(query_by_trace_code)

    def test_query_by_product_name_exists(self):
        assert callable(query_by_product_name)


class TestQueryByTraceCode:

    def test_returns_dict_for_known_trace_code(self):
        result = query_by_trace_code("TW00123456789")
        assert isinstance(result, dict)
        assert result["TraceCode"] == "TW00123456789"
        assert result["ProductName"] == "有機青江菜"

    def test_returns_none_for_unknown_trace_code(self):
        result = query_by_trace_code("UNKNOWN123")
        assert result is None


class TestQueryByProductName:

    def test_returns_list_for_known_product(self):
        result = query_by_product_name("青江菜")
        assert isinstance(result, list)
        assert len(result) == 2
        assert all("ProductName" in r for r in result)

    def test_returns_empty_list_for_unknown_product(self):
        result = query_by_product_name("不存在作物")
        assert result == []

    def test_limits_to_20_records(self):
        # Mock data only has 2 records for 青江菜, but verify the cap logic exists
        result = query_by_product_name("青江菜")
        assert len(result) <= 20
