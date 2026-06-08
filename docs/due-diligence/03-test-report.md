# 測試報告 — Due Diligence Package

## Test Suite 總覽

| 指標 | 數值 |
|---|---|
| **Tests** | 76 |
| **Passed** | 76 (100%) |
| **Failed** | 0 |
| **Coverage** | 91% |
| **CI Status** | 76/76 ✅ |
| **Mutation Testing** | ❌ Not configured |
| **Python** | 3.12.3 |
| **pytest** | 9.0.3 |

## Coverage 明細

| Module | Statements | Covered | Missed | Coverage |
|---|---|---|---|---|
| `food_safety/views.py` | 44 | 38 | 6 | 86% |
| `food_safety/services/agent_service.py` | 64 | 49 | 15 | 77% |
| `food_safety/services/fda_service.py` | 6 | 6 | 0 | 100% |
| `food_safety/services/moa_service.py` | 55 | 51 | 4 | 93% |
| `food_safety/services/taft_service.py` | 46 | 24 | 22 | 52% |
| `food_safety/services/qr_service.py` | 25 | 21 | 4 | 84% |
| `food_safety/management/commands/sync_fda_data.py` | 32 | 27 | 5 | 84% |
| `food_safety/models.py` | 13 | 12 | 1 | 92% |
| `food_safety/admin.py` | 8 | 8 | 0 | 100% |
| `food_safety/urls.py` | 3 | 3 | 0 | 100% |
| **Total** | **874** | **793** | **81** | **91%** |

> 詳細 HTML 報告: `docs/due-diligence/coverage_html/index.html`

## Test 類別分布

| 套件 | 數量 | 說明 |
|---|---|---|
| Views | 11 | index, search, health, error handling, special chars |
| Agent Service | 15 | mock mode, error paths, 7-key return, mixed results |
| FDA Service | 9 | name/id query, partial match, empty, limit, fields |
| MOA Service | 34 | 4 APIs × (success, filter, no-match, limit, network error, JSON error, import) |
| Sync FDA Command | 5 | create, update, empty CSV, missing fields, network failure |
| TAFT Service | 7 | trace code, product name, mock data, unknown, limit |
| **Total** | **76** | |

## 邊界值分析 (BVA)

- **空字串**: `""` query → 即時返回提示，不呼叫外部 API
- **特殊字元**: 非 ASCII URL-encoded 中文 → 正常處理
- **結果上限**: FDA 10 筆, MOA 20 筆, TAFT 20 筆 — 皆有測試驗證
- **網路錯誤**: 超時 → tenacity 3 次重試 → 優雅降級 (None/[])
- **JSON 解析錯誤**: → 空 list
- **大量資料**: 50 筆 → slice 20 → 正確截斷

## CI 建議設定 (待實作)

```yaml
# .github/workflows/test.yml (建議)
name: Test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r requirements.txt pytest pytest-cov
      - run: pytest --cov=food_safety --cov-fail-under=80
```

## 涵蓋缺口

| 項目 | 狀態 | 說明 |
|---|---|---|
| E2E / Integration | ❌ | 所有外部 API 皆 mock，無真實 API 測試 |
| Performance / Load | ❌ | 無基準測試 |
| Mutation Testing | ❌ | 未配置 (建議: mutmut) |
| Security Tests | ❌ | 無 SQL injection / XSS 測試 |
| Scheduler Unit Tests | ❌ | `scheduler.py` 無獨立測試 |
| QR Service Tests | ❌ | `qr_service.py` 無測試 |
