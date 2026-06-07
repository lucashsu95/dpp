# 資料來源

## 1. 產銷履歷（農業部）— 有官方 API

- **平台**：政府資料開放平台 [data.gov.tw](https://data.gov.tw)
- **資料集名稱**：產銷履歷農產品詳細資料
- **格式**：JSON（建議）
- **串接方式**：帶參數查詢（追溯碼、產品名稱）

### API 端點

```
# JSON（建議）
GET https://data.moa.gov.tw/Service/OpenData/Resume/ResumeData_Plus.aspx?IsTransData=1&UnitId=063

# CSV
GET https://data.moa.gov.tw/Service/OpenData/Resume/ResumeData_Plus.aspx?FOTT=CSV&IsTransData=1&UnitId=063
```

> 無需 API Key，直接打即可。資料集來源頁面：https://data.gov.tw/dataset/7556

### 查詢參數

> 進階搜尋參考：https://data.moa.gov.tw/open_detail.aspx?id=063

| 參數 | 範例 | 說明 |
|---|---|---|
| `IsTransData` | `1` | 固定填 1 |
| `UnitId` | `063` | 產銷履歷資料集 ID，固定填 063 |
| `Tracecode` | `1234567890` | 追蹤碼（精確查詢） |
| `ProductName` | `番茄` | 產品名稱（模糊查詢） |
| `FarmerName` | `王小明` | 生產者名稱 |
| `$top` | `10` | 限制回傳筆數 |

### 主要欄位（粗體為資料標準欄位）

| 欄位 | 說明 |
|---|---|
| **Tracecode** | 追蹤碼 |
| **Producer** | 農業經營業者 |
| **OrgID** | 組織代碼 |
| **ProductName** | 產品名稱 |
| **Place** | 產地 |
| **FarmerName** | 生產者名稱 |
| **PackDate** | 包裝日期 |
| **CertificationName** | 驗證機構 |
| **ValidDate** | 驗證有效日期 |
| **StoreInfo** | 通路商資訊 |
| OperationDetail | 詳細栽種流程 |
| OperationDate | 作業日期 |
| OperationType | 作業種類 |
| Operation | 作業內容 |
| OperationMemo | 備註說明 |
| ResumeDetail | 詳細履歷資料 |
| ResumeTitle | 顯示標題 |
| ProcessDetail | 詳細加工流程 |
| ProcessDate | 加工作業日期 |
| ProcessItem | 作業項目 |
| ProcessArea | 作業場所 |
| ProcessMemo | 加工備註 |
| CertificateDetail | 其他驗證資訊 |
| LandSecNO | 農產品產地地段地號 |
| ParentTraceCode | 原料追溯碼網址 |
| Log_UpdateTime | 資料更新時間 |
| TraceCodelist | 一籤一碼追溯碼 |

### 查詢方式

```python
# 用追溯碼查（單筆）
query_by_trace_code(trace_code: str) -> dict | None

# 用產品名稱查（多筆）
query_by_product_name(product_name: str) -> list[dict]
```

---

## 2. 食品業者登錄平台（食藥署）— 無即時 API

- **方案**：定期下載官方 CSV 資料集，匯入本地資料庫
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

---

## 3. 農業部開放資料平台（data.moa.gov.tw）— 多資料集 API

- **基礎 URL**：`https://data.moa.gov.tw/Service/OpenData`
- **格式**：JSON
- **認證**：無需 API Key（公開存取）

### 優先串接端點

| 端點 | 用途 |
|---|---|
| `/SalesResumeAgriproductsResultsType/` | 農糧產品農藥殘留檢驗結果 |
| `/TWOrganicAgricultureVerificationInformationType/` | 有機驗證資訊 |
| `/CASProductInquiryType/` | CAS 優良農產品查詢 |
| `/PesticideDataQueryType/` | 農藥毒性資料庫 |

### Agent 查詢流程

```
Step 1  追溯碼 / 產品名稱 → 產銷履歷（data.gov.tw）
Step 2  ProductName      → 農藥殘留檢驗結果
Step 3  農藥名稱          → 農藥毒性分級（若 Step 2 有殘留紀錄）
Step 4  FarmerName       → 有機驗證 / CAS 查詢
Step 5  業者名稱          → 食品業者登錄（本地 DB）
Step 6  整合以上 → Gemini API 產出風險摘要
```

---

## 環境變數

```env
# 產銷履歷（data.moa.gov.tw，無需 API Key）
TAFT_API_BASE_URL=https://data.moa.gov.tw/Service/OpenData/Resume/ResumeData_Plus.aspx
TAFT_UNIT_ID=063

# Gemini API
GEMINI_API_KEY=your_gemini_key_here

# 食品業者資料集下載網址（食藥署 CSV）
FDA_DATASET_URL=https://data.gov.tw/dataset/xxxxx
```

---

## 資料可信度說明

| 資料來源 | 即時性 | 可信度 | 備註 |
|---|---|---|---|
| 產銷履歷 API | 即時 | 高（官方認證） | 需有追溯碼或產品名稱 |
| 食品業者登錄 | 每週同步 | 高（官方登錄） | 查業者合法性用 |
| 農藥殘留檢驗 | 批次更新 | 高（官方檢驗） | 抽查性質，非全面覆蓋 |
| 有機 / CAS 驗證 | 批次更新 | 高（官方認證） | 可交叉比對標章真偽 |
| 農藥毒性資料庫 | 靜態為主 | 高（法規依據） | 用於解釋殘留農藥風險 |