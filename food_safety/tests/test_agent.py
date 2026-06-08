import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ["USE_MOCK_API"] = "True"

import django
django.setup()

import requests
from unittest.mock import patch
from food_safety.services.agent_service import run_food_agent, _mock_agent


class TestAgentServiceImports:

    def test_run_food_agent_exists(self):
        assert callable(run_food_agent)


class TestRunFoodAgentMockMode:

    def _run(self, query):
        with patch("food_safety.services.agent_service.query_inspection_result") as mi:
            with patch("food_safety.services.agent_service.query_organic_cert") as mo:
                with patch("food_safety.services.agent_service.query_cas_product") as mc:
                    with patch("food_safety.services.agent_service.query_pesticide_info") as mp:
                        with patch("food_safety.services.agent_service.query_operator") as mf:
                            mi.return_value = []
                            mo.return_value = []
                            mc.return_value = []
                            mp.return_value = []
                            mf.return_value = []
                            return run_food_agent(query)

    def test_returns_dict_with_all_7_keys(self):
        result = self._run("青江菜")
        assert isinstance(result, dict)
        expected_keys = {
            "answer", "raw_taft", "raw_fda",
            "raw_inspection", "raw_organic", "raw_cas", "raw_pesticide"
        }
        assert set(result.keys()) == expected_keys

    def test_answer_contains_mock_marker(self):
        result = self._run("青江菜")
        assert "模擬回應" in result["answer"]

    def test_raw_taft_is_dict_or_list(self):
        result = self._run("青江菜")
        assert result["raw_taft"] is None or isinstance(result["raw_taft"], (dict, list))

    def test_raw_fda_is_list(self):
        result = self._run("青江菜")
        assert isinstance(result["raw_fda"], list)

    def test_raw_inspection_is_list(self):
        result = self._run("青江菜")
        assert isinstance(result["raw_inspection"], list)

    def test_raw_organic_is_list(self):
        result = self._run("青江菜")
        assert isinstance(result["raw_organic"], list)

    def test_raw_cas_is_list(self):
        result = self._run("青江菜")
        assert isinstance(result["raw_cas"], list)

    def test_raw_pesticide_is_list(self):
        result = self._run("青江菜")
        assert isinstance(result["raw_pesticide"], list)


class TestMockAgentDirect:
    """Direct tests for _mock_agent function with various input combinations."""

    def test_mock_agent_taft_list(self):
        """Test _mock_agent when taft_result is a list (common from query_by_product_name)."""
        taft_list = [
            {"ProductName": "青江菜", "FarmerName": "王小明", "FarmLocation": "雲林", "HarvestDate": "2024-01-15", "Certification": "優良農產品"}
        ]
        result = _mock_agent("青江菜", taft_list, [], [], [], [], [])
        assert "✅ **產銷履歷**" in result
        assert "青江菜" in result
        assert "王小明" in result
        assert "雲林" in result

    def test_mock_agent_mixed_results(self):
        """Test _mock_agent with some sources having data and others empty."""
        taft_data = {"ProductName": "小白菜", "FarmerName": "李大同", "FarmLocation": "彰化", "HarvestDate": "2024-02-01"}
        inspection_data = [{"樣品名稱": "小白菜", "檢出藥劑ppm": "未檢出"}]
        result = _mock_agent("小白菜", taft_data, [], inspection_data, [], [], [])
        assert "✅ **產銷履歷**" in result
        assert "✅ **農藥殘留檢驗**" in result
        assert "❌ **有機驗證**：查無資料" in result
        assert "❌ **CAS驗證**：查無資料" in result
        assert "❌ **農藥資訊**：查無資料" in result
        assert "❌ **食品業者**：查無資料" in result

    def test_mock_agent_all_empty(self):
        """Test _mock_agent when ALL sources are None/[]."""
        result = _mock_agent("不存在的作物", None, [], [], [], [], [])
        assert "❌ **產銷履歷**：查無資料" in result
        assert "❌ **農藥殘留檢驗**：查無資料" in result
        assert "❌ **有機驗證**：查無資料" in result
        assert "❌ **CAS驗證**：查無資料" in result
        assert "❌ **農藥資訊**：查無資料" in result
        assert "❌ **食品業者**：查無資料" in result


class TestRunFoodAgentErrorPaths:
    """Error path tests for run_food_agent function."""

    def _run_with_patches(self, query, taft_side_effect=None, moa_side_effects=None, fda_side_effect=None):
        """Helper to run with custom side effects for error testing."""
        patches = []
        
        # TAFT patches
        taft_patch = patch("food_safety.services.agent_service.query_by_trace_code")
        taft_mock = taft_patch.start()
        patches.append(taft_patch)
        if taft_side_effect:
            taft_mock.side_effect = taft_side_effect
        else:
            taft_mock.return_value = None
        
        taft_name_patch = patch("food_safety.services.agent_service.query_by_product_name")
        taft_name_mock = taft_name_patch.start()
        patches.append(taft_name_patch)
        taft_name_mock.return_value = None
        
        # MOA patches
        moa_funcs = [
            ("query_inspection_result", 0),
            ("query_organic_cert", 1),
            ("query_cas_product", 2),
            ("query_pesticide_info", 3),
        ]
        moa_mocks = {}
        for func_name, idx in moa_funcs:
            p = patch(f"food_safety.services.agent_service.{func_name}")
            m = p.start()
            patches.append(p)
            moa_mocks[func_name] = m
            if moa_side_effects and idx < len(moa_side_effects):
                m.side_effect = moa_side_effects[idx]
            else:
                m.return_value = []
        
        # FDA patch
        fda_patch = patch("food_safety.services.agent_service.query_operator")
        fda_mock = fda_patch.start()
        patches.append(fda_patch)
        if fda_side_effect:
            fda_mock.side_effect = fda_side_effect
        else:
            fda_mock.return_value = []
        
        try:
            return run_food_agent(query)
        finally:
            for p in patches:
                p.stop()

    def test_run_food_agent_all_sources_empty(self):
        """Mock ALL data sources to return empty/None, verify answer contains '查無資料'."""
        result = self._run_with_patches("不存在的查詢")
        assert "查無資料" in result["answer"]
        assert result["raw_taft"] is None
        assert result["raw_fda"] == []
        assert result["raw_inspection"] == []
        assert result["raw_organic"] == []
        assert result["raw_cas"] == []
        assert result["raw_pesticide"] == []

    def test_run_food_agent_taft_exception(self):
        """Patch query_by_trace_code to raise RequestException, verify exception propagates."""
        import pytest
        import requests
        with pytest.raises(requests.RequestException):
            self._run_with_patches(
                "追溯碼123",
                taft_side_effect=requests.RequestException("API timeout"),
                moa_side_effects=[[], [], [], []],
                fda_side_effect=None
            )

    def test_run_food_agent_moa_exception(self):
        """Patch query_inspection_result to raise RequestException, verify exception propagates."""
        import pytest
        import requests
        def inspection_raises(*args, **kwargs):
            raise requests.RequestException("MOA API down")
        
        organic_data = [{"農產品經營業者_進口業者": "有機農場", "標題": "有機認證"}]
        cas_data = [{"Product_Name": "測試產品", "Factory_CName": "測試工廠"}]
        pesticide_data = [{"中文名稱": "測試農藥", "許可證號": "許可123"}]
        
        with pytest.raises(requests.RequestException):
            self._run_with_patches(
                "測試查詢",
                taft_side_effect=None,
                moa_side_effects=[inspection_raises, organic_data, cas_data, pesticide_data],
                fda_side_effect=None
            )