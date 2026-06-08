import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ["USE_MOCK_API"] = "True"

import django
django.setup()

from unittest.mock import patch
from food_safety.services.agent_service import run_food_agent


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