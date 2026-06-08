# 系統架構 — Due Diligence Package

## 模組邊界圖 (Mermaid)

```mermaid
graph TB
    subgraph "使用者層"
        USER[消費者 / 業者]
    end

    subgraph "表現層 (templates/)"
        BASE[base.html]
        INDEX[index.html]
        RESULT[partials/result.html]
    end

    subgraph "REST API (food_safety/urls.py)"
        GET_INDEX["GET /"]
        GET_SEARCH["GET /search/"]
        GET_HEALTH["GET /health/"]
    end

    subgraph "服務層 (services/)"
        TAFT[taft_service.py<br/>產銷履歷 API]
        MOA[moa_service.py<br/>4 MOA 開放資料]
        FDA[fda_service.py<br/>本地 DB 查詢]
        AGENT[agent_service.py<br/>7-source orchestrator]
        QR[qr_service.py<br/>QR Code 產生]
    end

    subgraph "資料層"
        DB[(PostgreSQL<br/>FoodOperator)]
        CSV[CSV 食藥署 Open Data]
        SCHEDULER[scheduler.py<br/>APScheduler<br/>每週日 02:00 UTC]
        SYNC[sync_fda_data.py<br/>CSV ETL Command]
    end

    subgraph "外部 API"
        TAFT_API[TAFT API<br/>data.moa.gov.tw]
        MOA_API[MOA API<br/>data.moa.gov.tw]
        GEMINI_API[Gemini API<br/>gemini-2.5-flash]
    end

    USER --> GET_INDEX
    USER --> GET_SEARCH
    GET_INDEX --> INDEX
    GET_SEARCH --> AGENT
    AGENT --> TAFT
    AGENT --> MOA
    AGENT --> FDA
    AGENT --> GEMINI_API
    TAFT --> TAFT_API
    MOA --> MOA_API
    FDA --> DB
    INDEX --> QR
    QR --> DB
    SCHEDULER --> SYNC
    SYNC --> CSV
    SYNC --> DB
    GET_HEALTH --> DB
```

## 資料流圖

```mermaid
sequenceDiagram
    participant U as 使用者
    participant V as views.py
    participant A as agent_service.py
    participant T as taft_service
    participant M as moa_service
    participant F as fda_service
    participant G as Gemini API

    U->>V: GET /search/?q=追溯碼
    V->>A: run_food_agent(query)

    par TAFT 查詢
        A->>T: query_by_trace_code(query)
        T-->>A: dict | None
        alt 查無
            A->>T: query_by_product_name(query)
            T-->>A: list[dict]
        end
    and MOA 4 查詢
        A->>M: query_inspection_result(query)
        A->>M: query_organic_cert(query)
        A->>M: query_cas_product(query)
        A->>M: query_pesticide_info(query)
        M-->>A: list[dict] each
    and FDA 查詢
        A->>F: query_operator(query)
        F-->>A: list[dict]
    end

    alt USE_MOCK or no GEMINI_API_KEY
        A-->>A: _mock_agent()
    else
        A->>G: generate_content(prompt + context)
        G-->>A: answer text
    end

    A-->>V: { answer, raw_taft, raw_fda, ... }
    V-->>U: HTML partial (HTMX)
```

## 部署拓撲

```mermaid
graph LR
    subgraph "Railway Cloud"
        GB[Gunicorn WSGI<br/>workers=1]
        DJ[Django App]
        PG[(PostgreSQL<br/>Railway Managed)]
        NW[Nixpacks Build<br/>Python 3.11.9]
    end

    subgraph "外部服務"
        TA[TAFT API<br/>data.moa.gov.tw]
        MOA_API2[MOA API<br/>data.moa.gov.tw]
        GE[Gemini API<br/>generativeai.google.com]
        FD[食藥署 CSV<br/>data.gov.tw]
    end

    NW --> GB
    GB --> DJ
    DJ --> PG
    DJ --> TA
    DJ --> MOA_API2
    DJ --> GE
    DJ --> FD
```

## 模組依賴關係

| 模組 | 依賴 | 外部依賴 |
|---|---|---|
| `views.py` | agent_service, qr_service | — |
| `agent_service.py` | taft_service, moa_service, fda_service | Gemini API (`google-genai`) |
| `taft_service.py` | — | data.moa.gov.tw, `tenacity` retry |
| `moa_service.py` | — | data.moa.gov.tw, `tenacity` retry |
| `fda_service.py` | models.FoodOperator | PostgreSQL |
| `qr_service.py` | — | `qrcode[pil]` |
| `scheduler.py` | django-apscheduler, DjangoJobStore | PostgreSQL |
| `sync_fda_data.py` | models.FoodOperator | data.gov.tw CSV |

## 關鍵架構決策

1. **Mock 模式優先**: `USE_MOCK_API=True` 開發模式無需 API key，可完全離線開發
2. **錯誤隔離**: 每個外部 API 查詢獨立 try/except，單一來源失敗不影響其他
3. **重試策略**: tenacity 指數退避 (1s→2s→4s)，最多 3 次，僅重試網路/5xx 錯誤
4. **降級策略**: API 失敗回傳 None/[]，view 層顯示用戶友好錯誤
5. **資料新鮮度**: TAFT/MOA 即時查詢，FDA 每週同步 (最長 7 天延遲)
6. **LLM 安全**: Prompt 嚴格限縮為資料整理者，禁止自行推斷；顯示原始資料來源供用戶交叉比對
