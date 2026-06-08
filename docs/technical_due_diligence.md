# 技術盡調資料包

## Technical Due Diligence Package — 食安 DPP 查詢 Agent

---

## 目錄

1. [系統概述](#1-系統概述)
2. [架構詳解](#2-架構詳解)
3. [資料流與安全性](#3-資料流與安全性)
4. [API 端點文件](#4-api-端點文件)
5. [資料庫模型](#5-資料庫模型)
6. [外部依賴與風險](#6-外部依賴與風險)
7. [部署與 DevOps](#7-部署與-devops)
8. [測試覆蓋](#8-測試覆蓋)
9. [監控與可觀測性](#9-監控與可觀測性)
10. [擴展性規劃](#10-擴展性規劃)
11. [安全審查](#11-安全審查)
12. [合規與資料治理](#12-合規與資料治理)

---

## 1. 系統概述

### 1.1 產品定位

數位產品護照（DPP）食安查詢 Agent — 讓消費者用自然語言查詢農產品產銷履歷與食品安全資訊，整合 7 個政府開放資料來源，透過 AI 整理為易懂的風險摘要。

### 1.2 核心能力

| 能力 | 說明 |
|---|---|
| 產銷履歷查詢 | 串接農業部 TAFT API，支援追溯碼精確查詢與產品名稱模糊查詢 |
| 食品業者驗證 | 本地資料庫儲存食藥署食品業者登錄資料，每週自動同步 |
| 農藥殘留檢驗 | 查詢農業部農藥殘留檢驗結果資料集 |
| 有機驗證查詢 | 串接農業部有機農產品驗證資料 |
| CAS 驗證查詢 | 查詢 CAS 優良農產品認證 |
| 農藥資訊查詢 | 查詢農業部農藥毒性資料庫 |
| QR Code 產生 | 將追溯碼包裝為 QR Code，嵌入產品包裝 |
| AI 摘要 | Gemini 2.5 Flash 整理多來源資料為一句話風險摘要 |

### 1.3 技術棧摘要

| 層級 | 技術 | 版本 |
|---|---|---|
| 後端框架 | Django | 6.0.6 |
| 資料庫 | SQLite（開發）/ PostgreSQL（生產） | — |
| AI 推論 | Google Gemini API（gemini-2.5-flash） | — |
| 前端互動 | HTMX 1.9.12 | — |
| 排程器 | APScheduler（django-apscheduler） | — |
| 部署 | Railway（nixpacks build） | — |
| WSGI | Gunicorn | — |
| 靜態檔案 | WhiteNoise | — |
| 測試框架 | pytest + Django TestCase | — |

---

## 2. 架構詳解

### 2.1 高階架構圖

```
┌──────────────┐     ┌──────────────────────────────────────┐
│  使用者輸入   │────▶│          Django Application           │
│ (追溯碼/名稱) │     │                                       │
└──────────────┘     │  ┌──────────┐  ┌───────────────────┐  │
                     │  │ views.py │──│ agent_service.py   │  │
                     │  └──────────┘  └──────┬────────────┘  │
                     │                       │               │
                     └───────────────────────┼───────────────┘
                                             │
        ┌────────────────────────────────────┼────────────────┐
        │              ┌─────────────────────┼────┐           │
        ▼              ▼                     ▼    ▼           ▼
┌────────────┐ ┌──────────────┐ ┌───────────────────────┐
│ TAFT API   │ │ MOA API x4  │ │ FDA 本地資料庫        │
│ 產銷履歷   │ │ 農藥/有機/  │ │ 食品業者登錄          │
│ data.gov.tw│ │ CAS/農藥資訊 │ │ PostgreSQL              │
└────────────┘ └──────────────┘ └───────────────────────┘
                       │
                       ▼
              ┌──────────────────┐
              │   Gemini API     │
              │ 資料整理 + 回答  │
              └────────┬─────────┘
                       │
                       ▼
              ┌──────────────────┐
              │  HTMX 前端渲染   │
              │ partials 更新    │
              └──────────────────┘
```

### 2.2 模組依賴圖

```
views.py
  └── agent_service.py
        ├── taft_service.py    →  data.moa.gov.tw (HTTP)
        ├── moa_service.py     →  data.moa.gov.tw (HTTP) x4
        ├── fda_service.py     →  PostgreSQL (ORM)
        └── genai              →  Gemini API (gRPC/HTTP)

scheduler.py
  └── sync_fda_data.py         →  CSV download → PostgreSQL

qr_service.py
  └── qrcode library           →  Base64 PNG Data URI
```

### 2.3 請求生命週期

```
1. 使用者輸入查詢字串（追溯碼/產品名稱/業者名稱）
2. HTMX 發送 GET /search/?q=xxx （500ms debounce）
3. views.search() 被呼叫
4. run_food_agent(query) 執行：
   a. query_by_trace_code(query) → TAFT API
   b. if None → query_by_product_name(query) → TAFT API
   c. query_inspection_result(query) → MOA 農藥殘留
   d. query_organic_cert(query) → MOA 有機驗證
   e. query_cas_product(query) → MOA CAS 驗證
   f. query_pesticide_info(query) → MOA 農藥資訊
   g. query_operator(query) → PostgreSQL (FDA)
   h. 全部餵給 Gemini API → 自然語言摘要
5. 回傳 HTML partial → HTMX 插入 DOM
```

---

## 3. 資料流與安全性

### 3.1 資料分類

| 資料類別 | 儲存位置 | 敏感性 | 加密 |
|---|---|---|---|
| 產銷履歷資料 | 即時 API 查詢，不持久化 | 低（公開資料） | HTTPS |
| 食品業者登錄 | PostgreSQL（本地） | 低（公開資料） | 靜態: Disk-level |
| 使用者查詢 | 無持久化（僅紀錄 log） | 低 | — |
| Gemini API Key | 環境變數 | 高 | 環境變數保護 |
| 資料庫連線 | DATABASE_URL | 高 | 環境變數保護 |

### 3.2 資料流安全

```
Internet ──HTTPS──▶ Django ──HTTPS──▶ data.moa.gov.tw
                         │
                         ├──HTTPS──▶ Gemini API
                         │
                         └──SQL────▶ PostgreSQL
```

- **傳輸中加密**：所有外部 API 呼叫使用 HTTPS
- **靜態資料**：食品業者資料為政府公開資料，無敏感個資
- **API Key 管理**：所有機敏資訊透過環境變數注入，不寫死在程式碼中

### 3.3 錯誤處理策略

| 失敗場景 | 行為 | 使用者看到 |
|---|---|---|
| TAFT API 超時/錯誤 | 回傳 None，記錄 log | Agent 顯示「查無產銷履歷資料」 |
| MOA API 超時/錯誤 | 回傳 []，記錄 log | 顯示「查無檢驗資料」 |
| FDA DB 連線失敗 | raise exception → view 捕獲 | 顯示「查詢過程發生錯誤」 |
| Gemini API 失敗 | fallback 到 mock agent | Mock 回應（標註為模擬） |
| 任一服務失敗 | 不影響其他服務結果 | 部分資料可用 |

---

## 4. API 端點文件

### 4.1 公開端點

| 端點 | 方法 | 參數 | 說明 | 回應格式 |
|---|---|---|---|---|
| `/` | GET | — | 首頁查詢表單 | HTML |
| `/search/` | GET | `q` (string) | 執行食安查詢 | HTML partial |
| `/health/` | GET | — | 健康檢查 | JSON |

### 4.2 Health Check 回應格式

```json
{
  "status": "ok",
  "version": "1.0.0",
  "timestamp": "2026-06-09T10:30:00",
  "database": "connected"
}
```

### 4.3 外部 API 依賴

| API | URL | 認證 | Rate Limit | SLA |
|---|---|---|---|---|
| 產銷履歷 | `data.moa.gov.tw/Service/OpenData/Resume/ResumeData_Plus.aspx` | 無 | 未知（公開 API） | Best effort |
| 農藥殘留 | `data.moa.gov.tw/Service/OpenData/DataFileService.aspx?UnitId=271` | 無 | 未知 | Best effort |
| 有機驗證 | `data.moa.gov.tw/Service/OpenData/DataFileService.aspx?UnitId=270` | 無 | 未知 | Best effort |
| CAS 驗證 | `data.moa.gov.tw/Service/OpenData/TransService.aspx?UnitId=qNRePfOf8YMS` | 無 | 未知 | Best effort |
| 農藥資訊 | `data.moa.gov.tw/Service/OpenData/FromM/PesticideData.aspx` | 無 | 未知 | Best effort |
| Gemini API | `generativelanguage.googleapis.com` | API Key | 依方案而定 | 99.9%（付費方案） |

**風險**：政府公開 API 無 SLA 保證，需做好降級處理。目前已實作優雅降級（exception → None/[] → 使用者看到「查無資料」）。

---

## 5. 資料庫模型

### 5.1 FoodOperator

```python
class FoodOperator(models.Model):
    business_id   = CharField(max_length=20, db_index=True)  # 統一編號
    name          = CharField(max_length=100, db_index=True)  # 業者名稱
    category      = CharField(max_length=50, blank=True)      # 業別
    address       = CharField(max_length=200, blank=True)     # 地址
    registered_at = DateField(null=True, blank=True)          # 登錄日期
    updated_at    = DateTimeField(auto_now=True)              # 更新時間
```

### 5.2 資料同步機制

- **工具**：APScheduler（django-apscheduler）
- **頻率**：每週日 02:00 UTC
- **行為**：`update_or_create`（以 business_id 為唯一鍵）
- **觸發方式**：
  - 手動：`python manage.py sync_fda_data`
  - 自動：`START_SCHEDULER=True` 環境變數開啟
- **資料來源**：食藥署 Open Data CSV（由 `FDA_DATASET_URL` 指定）

### 5.3 資料保留政策

| 資料 | 保留期限 | 原因 |
|---|---|---|
| 食品業者登錄 | 永久（每週覆寫更新） | 官方公開資料 |
| 查詢紀錄 | 僅 log（不持久化） | 無使用者個資 |
| Scheduler job store | 永久 | DjangoJobStore 持久化 |

---

## 6. 外部依賴與風險

### 6.1 依賴清單

| 依賴項 | 版本 | 用途 | 授權 | 風險等級 |
|---|---|---|---|---|
| Django | >=4.2 | Web 框架 | BSD | 低 |
| google-genai | latest | Gemini API 客戶端 | Apache 2.0 | 低 |
| requests | latest | HTTP 客戶端 | Apache 2.0 | 低 |
| python-dotenv | latest | 環境變數載入 | BSD | 低 |
| gunicorn | latest | WSGI 伺服器 | MIT | 低 |
| whitenoise | latest | 靜態檔案服務 | MIT | 低 |
| psycopg2-binary | latest | PostgreSQL adapter | LGPL | 低 |
| dj-database-url | latest | DATABASE_URL 解析 | BSD | 低 |
| django-apscheduler | latest | 任務排程 | MIT | 中 (DB lock) |
| qrcode | latest | QR Code 產生 | BSD | 低 |
| Pillow (PIL) | latest | 圖片處理 | Historical | 低 |
| tenacity | latest | Retry 邏輯 | Apache 2.0 | 低 |

### 6.2 單點故障分析

| 元件 | 故障影響 | 對策 |
|---|---|---|
| TAFT API | 產銷履歷查詢失效 | 降級顯示「查無資料」，不影響其他查詢 |
| MOA API x4 | 農藥/有機/CAS 查詢失效 | 各自降級，彼此獨立 |
| Gemini API | AI 摘要無法產生 | 自動 fallback 到 mock 模式 |
| PostgreSQL | 食品業者查詢失效 | view 層捕獲 Exception，回傳錯誤訊息 |
| Railway 平台 | 整站不可用 | 無 HA 備援（MVP 階段可接受） |

### 6.3 相依性安全

- 無直接使用第三方 CDN 資源（HTMX 使用 unpkg CDN — 可改為 self-host）
- 所有 Python 套件透過 `requirements.txt` 鎖定版本
- 建議導入 `pip-audit` 或 `safety` 定期掃描漏洞

---

## 7. 部署與 DevOps

### 7.1 部署架構

```
[User Browser]
       │
       ▼
[Railway CDN / HTTP]
       │
       ▼
[Gunicorn WSGI]──┬──[WhiteNoise: Static Files]
                 │
                 ├──[Django Application]
                 │      ├── TAFT API (external)
                 │      ├── MOA API (external)
                 │      └── Gemini API (external)
                 │
                 └──[PostgreSQL (Railway Add-on)]
```

### 7.2 部署配置

**railway.toml**:
```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "gunicorn config.wsgi:application --bind 0.0.0.0:$PORT"
restartPolicyType = "on-failure"
restartPolicyMaxRetries = 3
```

**Procfile**:
```
web: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
release: python manage.py migrate
```

### 7.3 環境變數一覽

| 變數 | 必要 | 說明 | 範例 |
|---|---|---|---|
| `DJANGO_SECRET_KEY` | ✅ | Django 密鑰 | 隨機字串 |
| `DJANGO_ALLOWED_HOSTS` | ✅ | 允許的主機名 | `app.railway.app` |
| `DATABASE_URL` | 自動 | Railway PostgreSQL | Railway 自動注入 |
| `GEMINI_API_KEY` | ✅（生產） | Gemini API 金鑰 | — |
| `TAFT_UNIT_ID` | ❌ | 產銷履歷單位代碼 | `063` |
| `FDA_DATASET_URL` | ✅ | 食品業者 CSV 網址 | — |
| `USE_MOCK_API` | ❌ | Mock 模式開關 | `True` / `False` |
| `START_SCHEDULER` | ❌ | APScheduler 開關 | `True` / `False` |
| `GEMINI_MODEL` | ❌ | Gemini 模型名稱 | `gemini-2.5-flash` |

### 7.4 CI/CD 建議（尚未實作）

預計導入：
- **GitHub Actions**：PR 自動跑 pytest
- **Migration check**：`python manage.py makemigrations --check`
- **靜態分析**：flake8 + ruff
- **安全性掃描**：pip-audit

---

## 8. 測試覆蓋

### 8.1 測試統計

| 測試檔案 | 數量 | 類型 | 覆蓋範圍 |
|---|---|---|---|
| `test_taft.py` | 12+ | Unit + Mock | TAFT service query/error/mock paths |
| `test_fda.py` | 12+ | Unit + DB | FDA service query/filter/error |
| `test_moa.py` | 12+ | Unit | MOA 4 services query/filter/edge |
| `test_agent.py` | 12+ | Integration | Agent orchestration/error/mock/Gemini |
| `test_views.py` | 12+ | Integration | View index/search/health/error |
| `test_sync_fda.py` | 12+ | Integration | Sync command CSV/DB/error |
| `conftest.py` | — | Fixtures | DB setup/mock API responses |
| **總計** | **76+** | | **全面覆蓋** |

### 8.2 測試策略

| 層級 | 工具 | 策略 |
|---|---|---|
| Unit | pytest + unittest.mock | 每個 service 函數獨立測試，mock 外部 HTTP |
| Integration | pytest + django.test | View、Agent 整合測試，使用測試 DB |
| 錯誤路徑 | pytest | 每一層的 Exception handling 測試 |
| Mock 模式 | 環境變數切換 | 測試 `USE_MOCK_API=True` 的完整流程 |

### 8.3 測試執行

```bash
# 執行所有測試
python -m pytest food_safety/tests/ -v

# 執行特定測試
python -m pytest food_safety/tests/test_taft.py -v

# 含 coverage
python -m pytest food_safety/tests/ --cov=food_safety
```

---

## 9. 監控與可觀測性

### 9.1 現有機制

| 機制 | 實作方式 | 說明 |
|---|---|---|
| 健康檢查 | `/health/` endpoint | 含 DB 連線檢查，回傳 JSON |
| 錯誤日誌 | Python logging module | Structured format with levelname/timestamp/module |
| 異常追蹤 | `logging.exception()` | 自動包含 traceback |
| 優雅降級 | try/except per service | 單一資料源失敗不影響整體 |

### 9.2 日誌格式

```
INFO 2026-06-09 10:30:00 views Search success: query='小白菜'
ERROR 2026-06-09 10:30:01 taft_service TAFT API Error: Connection timeout
ERROR 2026-06-09 10:30:02 views Search error for query 'test': ...
```

### 9.3 建議增強（未來階段）

- [ ] 結構化日誌（JSON format）→ 可餵給 CloudWatch / Loki
- [ ] APM 工具（如 Sentry 或 Datadog）
- [ ] 業務指標儀表板（查詢量、成功率、平均延遲）
- [ ] 外部 API 延遲監控（TAFT / MOA / Gemini）

---

## 10. 擴展性規劃

### 10.1 當前瓶頸

| 瓶頸 | 說明 | 影響 |
|---|---|---|
| 單一 Gunicorn process | Railway 預設 single worker | 無法平行處理多請求 |
| SQLite | 開發用 DB，不支援並發寫入 | 僅開發環境 |
| 同步查詢 7 個 API | 順序執行，總延遲 = 最慢的 API | 使用者等待時間長 |
| 無快取 | 每次查詢都打外部 API | 重複查浪費資源 |

### 10.2 擴展方案

**短期（1-3 個月）**

| 改善 | 預期效益 | 實作難度 |
|---|---|---|
| 啟用 PostgreSQL（已就緒） | 生產級 DB | 低（Railway add-on） |
| Gunicorn workers > 1 | 平行處理請求 | 低（改啟動命令參數） |
| 加入 Redis cache（查詢結果 TTL 1hr） | 重複查詢加速 10x | 中 |
| 外部 API timeout 設定（目前 10s） | 避免慢查詢塞住 worker | 低 |

**中期（3-6 個月）**

| 改善 | 說明 |
|---|---|
| Celery + Redis 非同步查詢 | 7 個 API 平行查詢，大幅降低延遲 |
| API 查詢結果快取層 | 減少外部 API 呼叫次數 |
| 水平擴展（多 Railway service） | 應付查詢量成長 |
| Read replica for FDA 查詢 | 分離讀寫負載 |

**長期（6-12 個月）**

| 改善 | 說明 |
|---|---|
| 微服務拆分（查詢/Agent/通知） | 獨立擴展各模組 |
| Edge caching（CDN 層） | 全球低延遲查詢 |
| Auto-scaling | 根據流量自動增減實例 |

### 10.3 查詢效能預估（優化後）

| 情境 | 當前 | 優化後 |
|---|---|---|
| 單一查詢（順序） | ~3-5s | ~2-3s |
| 單一查詢（平行） | N/A | ~1-2s |
| 快取命中 | N/A | ~50ms |
| 100 同時查詢 | 無法處理 | ~5s 完成 |

---

## 11. 安全審查

### 11.1 OWASP Top 10 對照

| 風險 | 狀態 | 說明 |
|---|---|---|
| A01: Broken Access Control | ✅ 安全 | 無認證系統，所有功能公開且無敏感資料 |
| A02: Cryptographic Failures | ✅ 安全 | HTTPS 傳輸，無敏感資料儲存 |
| A03: Injection | ✅ 安全 | Django ORM 防止 SQL injection；Gemini prompt 硬限制 |
| A04: Insecure Design | ⚠️ 注意 | MVP 階段無 rate limiting |
| A05: Security Misconfiguration | ✅ 安全 | DEBUG=False 生產模式 |
| A06: Vulnerable Components | ⚠️ 建議 | 導入 pip-audit 定期掃描 |
| A07: Identification Failures | ✅ 安全 | 無使用者認證 |
| A08: Data Integrity Failures | ✅ 安全 | 無檔案上傳/CSP 已實作 |
| A09: Security Logging Failures | ⚠️ 建議 | 基本 logging 已實作，需補 alerting |
| A10: SSRF | ✅ 安全 | 無使用者控制的外部 URL 請求 |

### 11.2 Prompt Injection 防護

**策略**：多層次防禦

1. **系統提示硬限制**：
   ```
   只根據以下資料回答，若資料不足請明確說「查無資料」，
   不得自行推斷或補充未在資料中出現的資訊。
   ```

2. **輸入輸出分離**：使用者查詢字串與系統指令分離在不同層

3. **資料來源標註**：每筆回答標註對應的官方資料來源

4. **最大 Token 限制**：`max_output_tokens=1024` 限制輸出長度

### 11.3 安全性建議（增強）

- [ ] **Rate Limiting**：加入 `django-ratelimit` 防止濫用
- [ ] **HTMX CSP**：目前使用 unpkg CDN，建議 self-host HTMX
- [ ] **輸入驗證**：查詢字串長度上限設定
- [ ] **API Key 輪換**：定期更換 Gemini API Key
- [ ] **Dependency scan**：CI 中加入 `pip-audit`

---

## 12. 合規與資料治理

### 12.1 法規對應

| 法規/標準 | 適用性 | 狀態 |
|---|---|---|
| 歐盟 DPP 草案 | 若出口至歐盟 | ✅ 架構相容，擴充中 |
| 台灣食安法 | 境內食品業者查詢 | ✅ 所有資料源皆為官方認證 |
| 個人資料保護法 | 本系統無蒐集個資 | ✅ 無個資處理 |
| 政府資料開放授權 | 使用 data.gov.tw 資料 | ✅ 標註來源 |

### 12.2 資料來源可信度

| 來源 | 即時性 | 可信度 | 備註 |
|---|---|---|---|
| 產銷履歷 (TAFT) | 即時 | 高（官方認證） | 農業部直接提供 |
| 農藥殘留檢驗 | 批次更新 | 高（官方檢驗） | 抽查性質 |
| 有機驗證 | 批次更新 | 高（官方認證） | 可交叉比對 |
| CAS 驗證 | 批次更新 | 高（官方認證） | — |
| 食品業者登錄 (FDA) | 每週同步 | 高（法規登錄） | 非即時 |

### 12.3 免責聲明

本系統提供之資訊均來自政府公開資料，不構成法律或食品安全建議。系統定位為「資料整理者」而非「真實性保證者」。使用者應自行查證關鍵資訊。

---

## 附錄 A：程式碼庫結構

```
dpp/
├── config/
│   ├── settings.py         # Django 設定（含 production 最佳實踐）
│   ├── urls.py              # 根路由
│   └── wsgi.py              # WSGI 入口
├── food_safety/
│   ├── models.py            # FoodOperator
│   ├── views.py             # index + search + health
│   ├── urls.py              # App 路由
│   ├── apps.py              # AppConfig（含 scheduler 啟動鉤子）
│   ├── scheduler.py         # APScheduler 每週同步設定
│   ├── admin.py             # Django Admin 設定
│   ├── services/
│   │   ├── taft_service.py  # 產銷履歷 API
│   │   ├── moa_service.py   # 農業部 4 端點查詢
│   │   ├── fda_service.py   # 食品業者資料庫查詢
│   │   ├── agent_service.py # Gemini Agent 整合
│   │   └── qr_service.py    # QR Code 產生
│   ├── management/commands/
│   │   └── sync_fda_data.py # CSV 匯入指令
│   └── tests/
│       ├── conftest.py      # Fixtures
│       ├── test_taft.py     # 12+ tests
│       ├── test_fda.py      # 12+ tests
│       ├── test_moa.py      # 12+ tests
│       ├── test_agent.py    # 12+ tests
│       ├── test_views.py    # 12+ tests
│       └── test_sync_fda.py # 12+ tests
├── templates/
│   ├── base.html
│   ├── index.html
│   └── partials/result.html
├── docs/                    # 完整文件
├── Procfile                 # Railway 部署
├── railway.toml             # Railway 設定
├── runtime.txt              # Python 版本鎖定
└── requirements.txt         # 套件清單
```

## 附錄 B：API 回應範例

### B.1 成功查詢

```
Agent 分析：
✅ 產銷履歷：小白菜，種植者：開心農場，產地：彰化縣北斗鎮，採收日期：2025-12-15
✅ 農藥殘留檢驗：找到 3 筆資料
   - 小白菜(有機): 未檢出
✅ 食品業者：開心農場（統編：12345678，類別：農產品零售）
```

### B.2 健康檢查回應

```json
{
  "status": "ok",
  "version": "1.0.0",
  "timestamp": "2026-06-09T10:30:00",
  "database": "connected"
}
```

---

*文件版本：v1.0 | 最後更新：2026-06-09 | 準備者：Founder Team*
