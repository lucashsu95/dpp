# API 規格 — Due Diligence Package

## 1. Django REST API

### 1.1 GET /

**描述**: 首頁，顯示搜尋框與產品卡片 (含 QR Code)

**Query Parameters**:

| 參數 | 型態 | 必填 | 預設 | 說明 |
|---|---|---|---|---|
| `q` | string | 否 | `""` | 初始查詢值，自動觸發搜尋 |

**Response**: HTML 200

**Context**:
- `products`: 產品卡片列表 (含 QR Code Data URI)
- `initial_query`: 查詢參數

---

### 1.2 GET /search/

**描述**: HTMX 搜尋端點，局部更新結果區域

**Query Parameters**:

| 參數 | 型態 | 必填 | 預設 | 說明 |
|---|---|---|---|---|
| `q` | string | 是 | — | 追溯碼 / 作物名稱 / 業者名稱 |

**Response (200)**:

```json
{
  "answer": "🔍 查詢：TW00123456789\n\n✅ **產銷履歷**：有機青江菜，種植者：陳農夫，產地：台中市大肚區，採收日期：2024-03-20，認證：有機農產品\n\n❌ **農藥殘留檢驗**：查無資料\n...",
  "raw_taft": { "TraceCode": "TW00123456789", "ProductName": "有機青江菜", ... },
  "raw_fda": [],
  "raw_inspection": [],
  "raw_organic": [],
  "raw_cas": [],
  "raw_pesticide": []
}
```

**Error Responses**:

| 情境 | Status | Body |
|---|---|---|
| 空查詢 `?q=` | 200 | `<p>請輸入查詢內容</p>` |
| API 不可用 (HTTP/網路錯誤) | 200 | `<div class="error">查詢失敗：無法連線至外部服務，請稍後再試</div>` |
| 非預期錯誤 | 200 | `<div class="error">查詢發生錯誤，請稍後再試</div>` |

---

### 1.3 GET /health/

**描述**: 健康檢查端點

**Response (200)**:

```json
{
  "status": "ok",
  "version": "1.0.0",
  "timestamp": "2026-06-09T12:00:00",
  "database": "connected"
}
```

| 欄位 | 型態 | 值 |
|---|---|---|
| `status` | string | `"ok"` / `"degraded"` |
| `version` | string | 語意化版本 |
| `timestamp` | string | ISO 8601 |
| `database` | string | `"connected"` / `"disconnected"` |

---

### 1.4 GET /admin/

**描述**: Django Admin 介面 (需登入)

**FoodOperatorAdmin**:
- `list_display`: business_id, name, category, address, registered_at, updated_at
- `search_fields`: business_id, name, address
- `list_filter`: category, registered_at

---

## 2. 外部 API 消費規格

### 2.1 產銷履歷 API (TAFT)

| 項目 | 值 |
|---|---|
| 端點 | `GET https://data.moa.gov.tw/Service/OpenData/Resume/ResumeData_Plus.aspx` |
| 認證 | 無需 API Key |
| 參數 | `Tracecode`, `ProductName`, `UnitId=063` |
| 重試 | 3 次, exp backoff 1s→2s→4s |
| 超時 | 10s |

### 2.2 農業部開放資料 (MOA)

| 查詢 | 端點 | UnitId |
|---|---|---|
| 農藥殘留檢驗 | `DataFileService.aspx` | `271` |
| 有機驗證 | `DataFileService.aspx` | `270` |
| CAS 驗證 | `TransService.aspx` | `qNRePfOf8YMS` |
| 農藥資訊 | `PesticideData.aspx` | 無 |

認證: 無需 API Key | 重試: 3 次 exp backoff | 超時: 10s

### 2.3 Gemini API

| 項目 | 值 |
|---|---|
| 模型 | `gemini-2.5-flash` (可透過 `GEMINI_MODEL` 設定) |
| 輸出上限 | 1024 tokens |
| 系統指令 | 限縮 prompt (只整理資料，不推斷) |
| SDK | `google-genai` Python SDK |

### 2.4 食藥署 CSV

| 項目 | 值 |
|---|---|
| 來源 | `data.gov.tw` Open Data |
| 同步方式 | `sync_fda_data` management command |
| 頻率 | 每週 (APScheduler cron: 週日 02:00 UTC) |
| 策略 | `update_or_create` by `business_id` |

---

## 3. 內部 Service API

| 函數 | 回傳 | 說明 |
|---|---|---|
| `taft_service.query_by_trace_code(code)` | `dict \| None` | 追溯碼精確查詢 |
| `taft_service.query_by_product_name(name)` | `list[dict]` | 產品名稱模糊查詢 (上限 20) |
| `moa_service.query_inspection_result(crop)` | `list[dict]` | 農藥殘留檢驗 (上限 20) |
| `moa_service.query_organic_cert(producer)` | `list[dict]` | 有機驗證 (上限 20) |
| `moa_service.query_cas_product(product)` | `list[dict]` | CAS 驗證 (上限 20) |
| `moa_service.query_pesticide_info(pesticide)` | `list[dict]` | 農藥資訊 (上限 20) |
| `fda_service.query_operator(keyword)` | `list[dict]` | 業者名稱/統編模糊查詢 (上限 10) |
| `agent_service.run_food_agent(query)` | `dict` | 7 資料源整合 + Gemini/mock 回答 |
| `qr_service.generate_qr_data_url(data)` | `str \| None` | Base64 QR Code Data URI |
