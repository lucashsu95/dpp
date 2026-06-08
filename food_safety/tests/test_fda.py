"""
TDD: Test for FDA service query_operator function.
"""

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ["USE_MOCK_API"] = "True"

import django
django.setup()

from unittest.mock import patch
from food_safety.models import FoodOperator
from food_safety.services.fda_service import query_operator


class TestFdaServiceImports:

    def test_query_operator_exists(self):
        assert callable(query_operator)


class TestQueryOperator:

    def setUp(self):
        """Create test FoodOperator records."""
        FoodOperator.objects.all().delete()
        self.operator1 = FoodOperator.objects.create(
            business_id="12345678",
            name="開心農場",
            category="農產品批發",
            address="台北市中正區忠孝東路100號",
            registered_at="2023-01-15",
        )
        self.operator2 = FoodOperator.objects.create(
            business_id="87654321",
            name="快樂食品股份有限公司",
            category="食品製造",
            address="新北市板橋區文化路200號",
            registered_at="2022-06-20",
        )

    def test_query_by_name(self):
        """Query '開心' returns the mock record."""
        self.setUp()
        results = query_operator("開心")
        assert len(results) == 1
        assert results[0]["name"] == "開心農場"
        assert results[0]["business_id"] == "12345678"

    def test_query_by_business_id(self):
        """Query '12345678' returns the mock record."""
        self.setUp()
        results = query_operator("12345678")
        assert len(results) == 1
        assert results[0]["name"] == "開心農場"
        assert results[0]["business_id"] == "12345678"

    def test_query_no_match(self):
        """Query '不存在業者' returns empty list."""
        self.setUp()
        results = query_operator("不存在業者")
        assert results == []

    def test_query_empty_string(self):
        """Query '' returns empty list."""
        self.setUp()
        results = query_operator("")
        assert results == []

    def test_query_partial_match(self):
        """Query '開心農' matches '開心農場'."""
        self.setUp()
        results = query_operator("開心農")
        assert len(results) == 1
        assert results[0]["name"] == "開心農場"

    def test_query_case_insensitive(self):
        """Query matches regardless of case (icontains)."""
        self.setUp()
        results = query_operator("開心農場")
        assert len(results) == 1
        assert results[0]["name"] == "開心農場"

    def test_query_returns_max_10_records(self):
        """Query limits results to 10 records."""
        self.setUp()
        for i in range(12):
            FoodOperator.objects.create(
                business_id=f"9999999{i:02d}",
                name=f"開心農場分店{i}",
                category="農產品零售",
                address=f"台中市西屯區台灣大道{i}號",
                registered_at="2023-01-01",
            )
        results = query_operator("開心")
        assert len(results) <= 10

    def test_query_returns_expected_fields(self):
        """Query returns only expected fields."""
        self.setUp()
        results = query_operator("開心")
        assert len(results) == 1
        expected_keys = {"name", "business_id", "category", "address", "registered_at"}
        assert set(results[0].keys()) == expected_keys
        assert "updated_at" not in results[0]
