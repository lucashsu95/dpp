# 測試報告

## 總覽

| 指標 | 數值 |
|---|---|
| 測試總數 | 76 |
| 通過 | 76 |
| 失敗 | 0 |
| 錯誤 | 0 |
| 跳過 | 0 |
| 涵蓋套件數 | 7 |
| 執行時間 | ~50 秒 |
| Python | 3.12.3 |
| pytest | 9.0.3 |

---

## 測試套件分布

| 套件 | 測試數 | 說明 |
|---|---|---|
| `test_agent.py` | 15 | Agent 服務、Mock Agent、錯誤路徑 |
| `test_fda.py` | 9 | 食品業者本地查詢 |
| `test_moa.py` | 34 | 4 個 MOA 查詢函式 (農藥/有機/CAS/農藥資訊) |
| `test_sync_fda.py` | 5 | FDA CSV 匯入指令 |
| `test_taft.py` | 7 | 產銷履歷 API (mock 模式) |
| `test_views.py` | 11 | View 層 (index, search, health) |
| **總計** | **76** | **全數通過** |

---

## 詳細測試結果

### test_agent.py — 15 tests

**TestAgentServiceImports**
- `test_run_food_agent_exists` — 確認 run_food_agent 可呼叫

**TestRunFoodAgentMockMode** (mock 模式)
- `test_returns_dict_with_all_7_keys` — 回傳 7 個 key (answer, raw_taft, raw_fda, raw_inspection, raw_organic, raw_cas, raw_pesticide)
- `test_answer_contains_mock_marker` — 包含 "模擬回應" 標記
- `test_raw_taft_is_dict_or_list` — raw_taft 型別檢查
- `test_raw_fda_is_list` — raw_fda 型別檢查
- `test_raw_inspection_is_list` — raw_inspection 型別檢查
- `test_raw_organic_is_list` — raw_organic 型別檢查
- `test_raw_cas_is_list` — raw_cas 型別檢查
- `test_raw_pesticide_is_list` — raw_pesticide 型別檢查

**TestMockAgentDirect** (輸入組合)
- `test_mock_agent_taft_list` — taft_result 為 list 時正確處理
- `test_mock_agent_mixed_results` — 部分資料源有結果，部分無
- `test_mock_agent_all_empty` — 所有資料源皆空

**TestRunFoodAgentErrorPaths**
- `test_run_food_agent_all_sources_empty` — 全部空 → answer 含 "查無資料"
- `test_run_food_agent_taft_exception` — TAFT API 拋錯 → exception 傳遞
- `test_run_food_agent_moa_exception` — MOA API 拋錯 → exception 傳遞

---

### test_fda.py — 9 tests

**TestFdaServiceImports**
- `test_query_operator_exists`

**TestQueryOperator** (資料庫查詢)
- `test_query_by_name` — 名稱查詢
- `test_query_by_business_id` — 統編查詢
- `test_query_no_match` — 無匹配
- `test_query_empty_string` — 空字串安全處理
- `test_query_partial_match` — 部分匹配 (icontains)
- `test_query_case_insensitive` — 大小寫不敏感
- `test_query_returns_max_10_records` — 結果上限 10 筆
- `test_query_returns_expected_fields` — 回傳欄位正確 (排除 updated_at)

---

### test_moa.py — 34 tests

**TestMoaServiceImports**
- `test_query_inspection_result_exists`

**TestQueryInspectionResult** (農藥殘留檢驗)
- `test_returns_list_on_success`
- `test_filters_by_crop_name_case_insensitive`
- `test_returns_empty_list_when_no_match`
- `test_limits_to_20_records_max`
- `test_returns_empty_list_on_request_exception`
- `test_returns_empty_list_on_json_decode_error`

**TestQueryOrganicCert** (有機驗證) — 7 tests (同上結構)

**TestQueryCasProduct** (CAS 驗證) — 7 tests (同上結構)

**TestQueryPesticideInfo** (農藥資訊) — 7 tests (同上結構)

涵蓋情景: 成功 / 過濾 / 無匹配 / 上限 / 網路錯誤 / JSON 解析錯誤

---

### test_sync_fda.py — 5 tests

**TestSyncFdaData** (CSV 匯入)
- `test_import_creates_records` — 2 筆 CSV → 2 筆 DB 記錄
- `test_import_updates_existing` — 相同 business_id → update
- `test_import_empty_csv` — 僅表頭 → 0 筆
- `test_import_handles_missing_fields` — 空欄位優雅處理
- `test_import_network_failure` — 網路失敗不 crash

---

### test_taft.py — 7 tests

**TestTaftServiceImports**
- `test_query_by_trace_code_exists`
- `test_query_by_product_name_exists`

**TestQueryByTraceCode** (mock 模式)
- `test_returns_dict_for_known_trace_code`
- `test_returns_none_for_unknown_trace_code`

**TestQueryByProductName**
- `test_returns_list_for_known_product`
- `test_returns_empty_list_for_unknown_product`
- `test_limits_to_20_records`

---

### test_views.py — 11 tests

**TestIndexView**
- `test_index_returns_200`
- `test_index_contains_initial_query_param`
- `test_index_contains_products_in_context`

**TestSearchView**
- `test_search_with_valid_query_returns_200`
- `test_search_with_empty_query_returns_message`
- `test_search_with_no_query_returns_message`
- `test_search_handles_exception_gracefully` — requests.RequestException → 用戶友好訊息
- `test_search_handles_unexpected_exception` — 通用 Exception → 錯誤訊息
- `test_search_with_special_chars` — 非 ASCII 輸入安全
- `test_search_renders_result_template`
- `test_search_result_context_has_answer`

---

## 邊界值分析 (BVA)

### 字串輸入
- 空字串 `""` → 立即返回提示，不呼叫 agent
- 特殊字元 (URL encode 非 ASCII) → 正常處理
- 中文 / 英文混合 → 大小寫不敏感匹配

### 資料庫查詢
- 結果上限: 10 筆 (FDA) / 20 筆 (MOA) — 各皆有測試驗證
- 無匹配 → 空 list (不是 None)
- 部分匹配 → icontains 模糊查詢

### 錯誤路徑
- 網路超時 → 自動重試 3 次 → 優雅降級
- JSON 解析錯誤 → 空 list
- 外部 API 不可用 → view 層補獲 → 用戶友好錯誤 HTML

### 整數範圍
- 查詢筆數: `results[:20]` — slice 安全，不會 index error
- QR Code box_size: 預設 6，border: 預設 2

---

## 涵蓋缺口

| 項目 | 狀態 | 備註 |
|---|---|---|
| integrations/e2e tests | ❌ 未涵蓋 | 所有外部 API 皆 mock，無真實 API 測試 |
| performance/load tests | ❌ 未涵蓋 | 無基準測試 |
| security tests | ❌ 未涵蓋 | 無 SQL injection / XSS 測試 |
| scheduler unit tests | ❌ 未涵蓋 | scheduler.py 無獨立測試 |
| qr_service tests | ❌ 未涵蓋 | QR 產生邏輯無測試 |

---

## 執行方式

```bash
# 全部測試
source venv/bin/activate
python -m pytest food_safety/tests/ -v

# 僅某個套件
python -m pytest food_safety/tests/test_views.py -v

# 含覆蓋率 (需安裝 pytest-cov)
python -m pytest food_safety/tests/ --cov=food_safety
```
