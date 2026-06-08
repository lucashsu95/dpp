# 系統架構

## 系統脈絡圖 (System Context)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        使用者 (消費者 / 業者)                            │
│                 輸入追溯碼、作物名稱、業者名稱                              │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        Django Application                               │
│                                                                         │
│  ┌──────────────┐  ┌───────────────────────────────────────────────┐   │
│  │   views.py   │──│           agent_service.py                     │   │
│  │  (3 routes)  │  │  (7-source orchestrator + Gemini AI)          │   │
│  └──────────────┘  └───────┬───────────┬──────────┬───────────────┘   │
│         │                  │           │          │                    │
│         │                  ▼           ▼          ▼                    │
│         │         ┌────────────┐ ┌──────────┐ ┌──────────┐            │
│         │         │taft_service│ │moa_service│ │fda_service│           │
│         │         │(產銷履歷)   │ │(4 sources)│ │(本地 DB)  │           │
│         │         └────────────┘ └──────────┘ └──────────┘            │
│         │                  │           │          │                    │
│         │         ┌────────────┐ ┌──────────┐ ┌──────────┐            │
│         │         │qr_service  │ │scheduler │ │sync_fda  │            │
│         │         │(QR生成)    │ │(APSched.)│ │(CSV ETL) │            │
│         │         └────────────┘ └──────────┘ └──────────┘            │
└─────────────────────────┬──────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        外部依賴                                          │
│                                                                         │
│  ┌──────────────────┐  ┌────────────────────┐  ┌────────────────────┐  │
│  │ TAFT API          │  │ MOA 開放資料平台    │  │ 食藥署 Open Data   │  │
│  │ 產銷履歷 API      │  │ 農藥/有機/CAS/農藥   │  │ 食品業者 CSV       │  │
│  │ data.moa.gov.tw  │  │ data.moa.gov.tw    │  │ data.gov.tw       │  │
│  └──────────────────┘  └────────────────────┘  └────────────────────┘  │
│                                                                         │
│  ┌──────────────────┐  ┌────────────────────┐                          │
│  │ Gemini API        │  │ PostgreSQL          │                          │
│  │ gemini-2.5-flash  │  │ (Railway managed)   │                          │
│  └──────────────────┘  └────────────────────┘                          │
└─────────────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       前端 (HTMX + Django Templates)                     │
│                                                                         │
│  base.html ── index.html (搜尋 + 產品卡片 + QR) ── partials/result.html │
│      骨架載入動畫    錯誤/空狀態處理      CSS 過渡動畫     響應式網格    │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 資料流 (Data Flow)

### 查詢流程

```
使用者輸入
    │
    ▼
views.search()
    │
    ▼
run_food_agent(query)
    │
    ├── query_by_trace_code(query)     → TAFT API (產銷履歷)
    │    或查無 → query_by_product_name(query)
    │
    ├── query_inspection_result(query) → MOA API (農藥殘留檢驗)
    ├── query_organic_cert(query)      → MOA API (有機驗證)
    ├── query_cas_product(query)       → MOA API (CAS 驗證)
    ├── query_pesticide_info(query)    → MOA API (農藥資訊)
    │
    ├── query_operator(query)          → 本地 PostgreSQL (食品業者)
    │
    ├── USE_MOCK=True? → _mock_agent() (不回真 API)
    │   或 GEMINI_API_KEY 不存在? → _mock_agent()
    │
    └── Gemini API → 自然語言回答 (限縮 prompt: 只整理不推斷)
         │
         ▼
    { answer, raw_taft, raw_fda, raw_inspection,
      raw_organic, raw_cas, raw_pesticide }
```

### 同步流程 (定時)

```
APScheduler (每週日 02:00 UTC)
    │
    ▼
sync_fda_data management command
    │
    ├── GET FDA_DATASET_URL (食藥署 CSV)
    ├── 解析 CSV → update_or_create FoodOperator
    └── 報告新增/更新筆數
```

---

## 模組職責

### 1. 表現層 (views.py)

| 路由 | 方法 | 說明 |
|---|---|---|
| `GET /` | `index()` | 首頁。載入產品卡片 (含 QR Code)、初始查詢參數 |
| `GET /search/` | `search()` | HTMX 局部更新端點，呼叫 agent_service，渲染 result partial |
| `GET /health/` | `health()` | 健康檢查 (DB 連線 + 版本 + 時間戳) |

### 2. 服務層 (services/)

| 模組 | 類型 | 說明 |
|---|---|---|
| `taft_service.py` | REST API | 產銷履歷查詢 (追溯碼/產品名稱)，3 次重試 + exp backoff |
| `moa_service.py` | REST API | 4 個農業部開放資料查詢 (農藥殘留/有機/CAS/農藥資訊) |
| `fda_service.py` | 資料庫查詢 | 食品業者模糊查詢 (名稱/統編)，限 10 筆 |
| `agent_service.py` | Agent 協調 | 7 資料來源整合 + Gemini/mock 回答，mock 模式離線可用 |
| `qr_service.py` | 工具 | 追溯碼 → QR Code (Base64 Data URI) |

### 3. 資料層

| 模組 | 說明 |
|---|---|
| `models.py` | FoodOperator (business_id, name, category, address, registered_at) |
| `sync_fda_data.py` | CSV → DB 的 UpdateOrCreate ETL |
| `scheduler.py` | APScheduler，django-apscheduler + DjangoJobStore 持久化 |

### 4. 系統層

| 模組 | 說明 |
|---|---|
| `apps.py` | `ready()` 鉤子條件式啟動排程器 |
| `config/settings.py` | Railway PostgreSQL、whitenoise 靜態檔、日誌設定 |
| `config/urls.py` | 根路由: admin/ + food_safety/ |

---

## 跨切面關注點

| 關注點 | 實作 |
|---|---|
| 重試策略 | tenacity: 3 次重試, exp backoff (1s→2s→4s), 僅 retry RequestException |
| Mock 模式 | `USE_MOCK_API=True` 時所有外部 API 回傳模擬資料，不消耗額度 |
| 錯誤降級 | 外部 API 失敗回傳 None/[]，view 層捕獲 Exception 回應用戶友好訊息 |
| 日誌 | console handler, structured format, food_safety logger |
| 前端載入 | skeleton loader (CSS animation), 500ms debounce, aria-live |
| 前端動畫 | fadeIn 過渡, 響應式 grid (1→2→3 欄), 產品卡片 hover 效果 |
| 快取 | 無 (TAFT API 即時查詢; FDA 每週同步延遲 ≤ 7 天) |

---

## 注意事項

- Agent Service 是純資料整理者，不做知識推斷 (prompt 嚴格限制)
- TAFT/MOA API 為即時查詢，FDA 為本地定期同步 (最多 7 天延遲)
- 所有外部 API 失敗時優雅降級，不讓 view 炸掉
- 正式環境需設定 `GEMINI_API_KEY`，開發環境 mock 模式無需 API key
