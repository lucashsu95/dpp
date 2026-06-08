import os
from unittest.mock import patch
from django.test import TestCase, Client
from django.urls import reverse
import requests

os.environ["USE_MOCK_API"] = "True"


class TestIndexView(TestCase):
    """Tests for the index view."""

    def setUp(self):
        self.client = Client()

    def test_index_returns_200(self):
        """GET / → 200 status, renders index.html"""
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "食安查詢 Agent")

    def test_index_contains_initial_query_param(self):
        """GET /?q=test → initial_query in context"""
        response = self.client.get(reverse("index"), {"q": "test"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="test"')

    def test_index_contains_products_in_context(self):
        """Index view should have products in context"""
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "product-cards-section")


class TestSearchView(TestCase):
    """Tests for the search view."""

    def setUp(self):
        self.client = Client()

    def test_search_with_valid_query_returns_200(self):
        """GET /search/?q=青江菜 → 200, contains 產銷履歷"""
        response = self.client.get(reverse("search"), {"q": "青江菜"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "產銷履歷")

    def test_search_with_empty_query_returns_message(self):
        """GET /search/?q= → returns error message HTML"""
        response = self.client.get(reverse("search"), {"q": ""})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "請輸入查詢內容")

    def test_search_with_no_query_returns_message(self):
        """GET /search/ → returns error message HTML"""
        response = self.client.get(reverse("search"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "請輸入查詢內容")

    def test_search_handles_exception_gracefully(self):
        """Mock run_food_agent to raise requests.RequestException, verify error HTML returned"""
        with patch("food_safety.views.run_food_agent") as mock_run:
            mock_run.side_effect = requests.RequestException("Connection failed")
            response = self.client.get(reverse("search"), {"q": "青江菜"})
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "無法連線至外部服務")

    def test_search_handles_unexpected_exception(self):
        """Mock run_food_agent to raise generic Exception, verify error HTML returned"""
        with patch("food_safety.views.run_food_agent") as mock_run:
            mock_run.side_effect = Exception("Unexpected error")
            response = self.client.get(reverse("search"), {"q": "青江菜"})
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "查詢發生錯誤")

    def test_search_with_special_chars(self):
        """GET /search/?q=%E8%BE%B2%E8%80%95 (non-ASCII) → 200"""
        # %E8%BE%B2%E8%80%95 is URL-encoded "農耕"
        response = self.client.get(reverse("search"), {"q": "農耕"})
        self.assertEqual(response.status_code, 200)
        # Should render result template without crashing
        self.assertContains(response, "Agent 分析")

    def test_search_renders_result_template(self):
        """Search with valid query should render partials/result.html"""
        response = self.client.get(reverse("search"), {"q": "小白菜"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Agent 分析")
        self.assertContains(response, "模擬回應")

    def test_search_result_context_has_answer(self):
        """Search result context should contain answer key"""
        response = self.client.get(reverse("search"), {"q": "青江菜"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "模擬回應")
