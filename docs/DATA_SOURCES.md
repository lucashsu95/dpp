# 資料來源

## 1. 產銷履歷（農業部）— 有官方 API

- **平台**：政府資料開放平台 [data.gov.tw](https://data.gov.tw)
- **資料集名稱**：產銷履歷農產品詳細資料
- **格式**：JSON / XML / CSV
- **串接方式**：帶參數查詢（追溯碼、作物名稱）

### API 端點

```
GET {TAFT_API_BASE_URL}/TraceabilityData
```

### 查詢參數

| 參數 | 範例 | 說明 |
|---|---|---|
| `$filter` | `TraceCode eq '12345'` | OData 過濾語法 |
| `ApiKey` | `your_api_key` | API 金鑰 |
| `$format` | `json` | 回傳格式 |
| `$top` | `10` | 限制回傳筆數 |

### 主要欄位

| 欄位 | 說明 |
|---|---|
| TraceCode | 追溯碼 |
| CropName | 作物名稱 |
| FarmerName | 農夫/農企業名稱 |
| Origin | 產地 |
| Certifier | 驗證機構 |
| PackDate | 包裝日期 |

### 查詢方式

```python
# 用追溯碼查（單筆）
query_by_trace_code(trace_code: str) -> dict | None

# 用作物名稱查（多筆）
query_by_crop_name(crop_name: str) -> list[dict]
```

## 2. 食品業者登錄平台（食藥署）— 無即時 API

- **方案**：定期下載官方 CSV/JSON 資料集，匯入本地資料庫
- **更新頻率**：每週 Cron Job 自動同步
- **工具**：APScheduler 或 Celery Beat

### 本地資料表結構

```python
class FoodOperator(models.Model):
    business_id   = models.CharField(max_length=20, db_index=True)  # 統一編號
    name          = models.CharField(max_length=100, db_index=True) # 業者名稱
    category      = models.CharField(max_length=50, blank=True)     # 業別
    address       = models.CharField(max_length=200, blank=True)    # 地址
    registered_at = models.DateField(null=True, blank=True)         # 登錄日期
    updated_at    = models.DateTimeField(auto_now=True)             # 更新時間
```

### CSV 匯入對照

| CSV 欄位 | Model 欄位 |
|---|---|
| 統一編號 | business_id |
| 業者名稱 | name |
| 業別 | category |
| 地址 | address |
| 登錄日期 | registered_at |

## 環境變數

```env
# 產銷履歷 API
TAFT_API_KEY=your_api_key_here
TAFT_API_BASE_URL=https://data.coa.gov.tw/api/v1

# Claude API
ANTHROPIC_API_KEY=your_claude_key_here

# 食品業者資料集下載網址
FDA_DATASET_URL=https://data.gov.tw/dataset/xxxxx
```
