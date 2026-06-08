"""
TDD: Tests for sync_fda_data management command.
"""

from io import StringIO
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.core.management import call_command
from food_safety.models import FoodOperator


class TestSyncFdaData(TestCase):
    """Tests for the sync_fda_data management command."""

    def setUp(self):
        FoodOperator.objects.all().delete()

    def _mock_csv_response(self, csv_text: str) -> MagicMock:
        """Create a mock requests.Response with CSV content."""
        resp = MagicMock()
        resp.text = csv_text
        resp.encoding = "utf-8-sig"
        return resp

    def test_import_creates_records(self):
        """CSV with 2 rows creates 2 FoodOperator records."""
        csv_data = "統一編號,業者名稱,業別,地址,登錄日期\n12345678,開心農場,農產品批發,台北市中正區,2023-01-15\n87654321,快樂食品,食品製造,新北市板橋區,2022-06-20\n"
        patcher_url = patch("food_safety.management.commands.sync_fda_data.FDA_DATASET_URL", "https://example.com/fake.csv")
        patcher_get = patch("food_safety.management.commands.sync_fda_data.requests.get")
        mock_get = patcher_get.start()
        patcher_url.start()
        mock_get.return_value = self._mock_csv_response(csv_data)
        out = StringIO()
        call_command("sync_fda_data", stdout=out)
        patcher_get.stop()
        patcher_url.stop()

        self.assertEqual(FoodOperator.objects.count(), 2)
        self.assertIn("新增 2 筆", out.getvalue())

    def test_import_updates_existing(self):
        """Same business_id but new name updates existing record."""
        FoodOperator.objects.create(
            business_id="12345678",
            name="舊名稱",
            category="舊類別",
            address="舊地址",
        )

        csv_data = "統一編號,業者名稱,業別,地址,登錄日期\n12345678,新名稱,新類別,新地址,2024-01-01\n"
        patcher_url = patch("food_safety.management.commands.sync_fda_data.FDA_DATASET_URL", "https://example.com/fake.csv")
        patcher_get = patch("food_safety.management.commands.sync_fda_data.requests.get")
        mock_get = patcher_get.start()
        patcher_url.start()
        mock_get.return_value = self._mock_csv_response(csv_data)
        out = StringIO()
        call_command("sync_fda_data", stdout=out)
        patcher_get.stop()
        patcher_url.stop()

        self.assertEqual(FoodOperator.objects.count(), 1)
        op = FoodOperator.objects.get(business_id="12345678")
        self.assertEqual(op.name, "新名稱")
        self.assertEqual(op.category, "新類別")
        self.assertIn("更新 1 筆", out.getvalue())

    def test_import_empty_csv(self):
        """CSV with only headers creates 0 records."""
        csv_data = "統一編號,業者名稱,業別,地址,登錄日期\n"
        patcher_url = patch("food_safety.management.commands.sync_fda_data.FDA_DATASET_URL", "https://example.com/fake.csv")
        patcher_get = patch("food_safety.management.commands.sync_fda_data.requests.get")
        mock_get = patcher_get.start()
        patcher_url.start()
        mock_get.return_value = self._mock_csv_response(csv_data)
        out = StringIO()
        call_command("sync_fda_data", stdout=out)
        patcher_get.stop()
        patcher_url.stop()

        self.assertEqual(FoodOperator.objects.count(), 0)

    def test_import_handles_missing_fields(self):
        """CSV row with missing optional fields is handled gracefully."""
        csv_data = "統一編號,業者名稱,業別,地址,登錄日期\n12345678,開心農場,,\n"
        patcher_url = patch("food_safety.management.commands.sync_fda_data.FDA_DATASET_URL", "https://example.com/fake.csv")
        patcher_get = patch("food_safety.management.commands.sync_fda_data.requests.get")
        mock_get = patcher_get.start()
        patcher_url.start()
        mock_get.return_value = self._mock_csv_response(csv_data)
        out = StringIO()
        call_command("sync_fda_data", stdout=out)
        patcher_get.stop()
        patcher_url.stop()

        self.assertEqual(FoodOperator.objects.count(), 1)
        op = FoodOperator.objects.get(business_id="12345678")
        self.assertEqual(op.name, "開心農場")

    def test_import_network_failure(self):
        """Network failure doesn't crash the command."""
        patcher_url = patch("food_safety.management.commands.sync_fda_data.FDA_DATASET_URL", "https://example.com/fake.csv")
        patcher_get = patch("food_safety.management.commands.sync_fda_data.requests.get")
        mock_get = patcher_get.start()
        patcher_url.start()
        mock_get.side_effect = __import__("requests").RequestException("Connection refused")
        out = StringIO()
        call_command("sync_fda_data", stdout=out)
        patcher_get.stop()
        patcher_url.stop()

        self.assertEqual(FoodOperator.objects.count(), 0)
