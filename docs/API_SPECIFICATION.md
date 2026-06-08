# API 規格

## 1. Django REST API

### 1.1 首頁

```
GET /
```

**查詢參數**

| 參數 | 型態 | 必填 | 說明 |
|---|---|---|---|
| `q` | string | 否 | 初始查詢值，自動觸發搜尋 |

**回應**: HTML (text/html) — 瀏覽器直接渲染。

**Context 包含**
- `products`: 產品卡片列表 (每個含 TraceCode, ProductName, FarmerName, FarmLocation, QR Code Data URI)
- `initial_query`: 使用者帶入的查詢值

---

### 1.2 搜尋 (HTMX Partial)

```
GET /search/
```

**查詢參數**

| 參數 | 型態 | 必填 | 說明 |
|---|---|---|---|
| `q` | string | 是 | 追溯碼、作物名稱或業者名稱 |

**成功回應** (200): HTML partial — `templates/partials/result.html`

**Context**
- `result.answer`: Agent 分析文字 (自然語言，含資料來源標註)
- `result.raw_taft`: 產銷履歷原始資料 (dict 或 None)
- `result.raw_fda`: 食品業者資料 (list)
- `result.raw_inspection`: 農藥殘留檢驗 (list)
- `result.raw_organic`: 有機驗證 (list)
- `result.raw_cas`: CAS 驗證 (list)
- `result.raw_pesticide`: 農藥資訊 (list)

**錯誤回應**

| 情境 | HTTP | 回應內容 |
|---|---|---|
| 空查詢 | 200 | `<p>請輸入查詢內容</p>` |
| 外部 API 失敗 | 200 | `'<div class="error">查詢失敗：無法連線至外部服務，請稍後再試</div>'` |
| 其他錯誤 | 200 | `'<div class="error">查詢發生錯誤，請稍後再試</div>'` |

---

### 1.3 健康檢查

```
GET /health/
```

**回應** (200 JSON):
```json
{
  "status": "ok",
  "version": "1.0.0",
  "timestamp": "2026-06-09T12:00:00",
  "database": "connected"
}
```

| 欄位 | 型態 | 說明 |
|---|---|---|
| `status` | string | `"ok"` 或 `"degraded"` |
| `version` | string | 應用版本 |
| `timestamp` | string (ISO 8601) | 伺服器當前時間 |
| `database` | string | `"connected"` 或 `"disconnected"` |

**downgrade 狀態**: DB 無法連線時 `status` 為 `"degraded"`, `database` 為 `"disconnected"`。

---

### 1.4 Django Admin

```
GET /admin/
```

標準 Django Admin 介面，註冊 `FoodOperator` 模型。需管理員權限。

**FoodOperatorAdmin 設定**
- `list_display`: business_id, name, category, address, registered_at, updated_at
- `search_fields`: business_id, name, address
- `list_filter`: category, registered_at
- `ordering`: -updated_at

---

## 2. 外部 API (本系統消費)

### 2.1 產銷履歷 API (TAFT)

**端點**
```
GET https://data.moa.gov.tw/Service/OpenData/Resume/ResumeData_Plus.aspx
```

**查詢參數**

| 參數 | 範例 | 說明 |
|---|---|---|
| `IsTransData` | `1` | 固定填 1 |
| `UnitId` | `063` | 資料集 ID，固定 |
| `Tracecode` | `1234567890` | 追蹤碼 (精確查詢) |
| `ProductName` | `番茄` | 產品名稱 (模糊查詢) |

**回應**: JSON array of objects

**主要欄位**: Tracecode, Producer, OrgID, ProductName, Place, FarmerName, PackDate, CertificationName, ValidDate, StoreInfo

**重試策略**: 最多 3 次，指數退避 1s→2s→4s，僅重試 RequestException

---

### 2.2 農業部開放資料 (MOA)

| 查詢 | 端點 (GET) | UnitId |
|---|---|---|
| 農藥殘留檢驗 | `/DataFileService.aspx` | `271` |
| 有機驗證 | `/DataFileService.aspx` | `270` |
| CAS 驗證 | `/TransService.aspx` | `qNRePfOf8YMS` |
| 農藥資訊 | `/FromM/PesticideData.aspx` | 無 |

**基礎 URL**: `https://data.moa.gov.tw/Service/OpenData`

**重試策略**: 最多 3 次，指數退避 1s→2s→4s，僅重試 RequestException

---

### 2.3 Gemini API

```
POST https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent
```

**模型**: `gemini-2.5-flash` (可透過 `GEMINI_MODEL` 環境變數覆寫)

**設定**
- `system_instruction`: 限縮 prompt (只整理資料，不推斷)
- `max_output_tokens`: 1024

---

## 3. 內部服務層 API

### 3.1 TAFT Service

```python
query_by_trace_code(trace_code: str) -> dict | None
query_by_product_name(product_name: str) -> list[dict]
```

### 3.2 MOA Service

```python
query_inspection_result(crop_name: str) -> list[dict]     # 農藥殘留
query_organic_cert(producer_name: str) -> list[dict]      # 有機驗證
query_cas_product(product_name: str) -> list[dict]        # CAS 驗證
query_pesticide_info(pesticide_name: str) -> list[dict]   # 農藥資訊
```

**行為**: 所有 MOA 函數先 fetch 完整資料集再於本地端過濾，回傳最多 20 筆。

### 3.3 FDA Service

```python
query_operator(keyword: str) -> list[dict]  # name__icontains | business_id__icontains
```

### 3.4 Agent Service

```python
run_food_agent(query: str) -> dict
# 回傳: { answer, raw_taft, raw_fda, raw_inspection, raw_organic, raw_cas, raw_pesticide }
```

### 3.5 QR Service

```python
generate_qr_data_url(data: str, box_size=6, border=2) -> str | None
generate_product_qr(product: dict, base_url: str) -> dict
```
