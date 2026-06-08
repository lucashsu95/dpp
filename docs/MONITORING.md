# 監控指標

## 1. 健康檢查端點

**端點**: `GET /health/`

**回應範例**:
```json
{
  "status": "ok",
  "version": "1.0.0",
  "timestamp": "2026-06-09T12:00:00",
  "database": "connected"
}
```

**監控項目**:

| 指標 | 閾值 | 說明 |
|---|---|---|
| `status` | `"ok"` | 應用整體健康 |
| `database` | `"connected"` | PostgreSQL 連線狀態 |

**建議**: 外部監控工具 (如 UptimeRobot, Railway 內建健康檢查) 每 1-5 分鐘輪詢此端點。

---

## 2. 應用指標 (建議實作)

以下指標尚未實作，建議逐步加入：

### 2.1 HTTP 請求

| 指標 | 說明 | 建議工具 |
|---|---|---|
| 請求數/min | 整體流量 | Django Prometheus |
| 延遲 P50/P95/P99 | 回應速度 | Django Prometheus |
| 錯誤率 (5xx) | 伺服器錯誤 | Django Prometheus |
| 端點分布 | 各 route 使用率 | Django Prometheus |

### 2.2 資料庫

| 指標 | 說明 | 建議工具 |
|---|---|---|
| 連線數 | DB 連線池使用率 | pg_stat_activity |
| 慢查詢 (>100ms) | SQL 效能 | Django Debug Toolbar |
| FoodOperator 筆數 | 資料量趨勢 | 自訂 management command |
| 同步狀態 | 最後 sync_fda 時間 | 寫入 sync_log 表 |

### 2.3 外部 API

| 指標 | 說明 | 建議工具 |
|---|---|---|
| TAFT API 延遲 | 產銷履歷查詢時間 | 自訂 middleware |
| TAFT API 錯誤率 | 失敗次數 | 自訂 middleware |
| MOA API 延遲 | 農業部查詢時間 | 自訂 middleware |
| MOA API 錯誤率 | 失敗次數 | 自訂 middleware |
| Gemini API 延遲 | AI 回覆時間 | 自訂 middleware |
| Gemini API token 用量 | 花費估算 | 自訂 metric |

### 2.4 排程器

| 指標 | 說明 | 建議工具 |
|---|---|---|
| sync_fda 執行成功/失敗 | 每週同步健康 | django-apscheduler 內建 |
| 同步筆數 | 新增/更新量 | Command stdout 收集 |
| 最後成功時間 | 同步新鮮度 | 寫入 DB 或外部監控 |

---

## 3. 日誌

### 設定 (settings.py)

```python
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "food_safety": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
```

### 日誌事件

| 事件 | 層級 | Logger | 觸發點 |
|---|---|---|---|
| 外部 API 請求失敗 | ERROR | `food_safety` | view error handler |
| 非預期查詢錯誤 | ERROR | `food_safety` | view 例外捕獲 |
| Agent 查詢執行 | INFO | `food_safety` | search view |
| API unavailable | ERROR | `food_safety` | requests.RequestException |
| 同步成功/失敗 | INFO/ERROR | `food_safety` | sync_fda_data command |

### 建議: 集中式日誌

- **Railway**: 內建 log 檢視
- **外部**: 可接入 Papertrail, Loggly, Datadog Logs 等
- **格式**: 結構化 JSON (可自訂 formatter)

---

## 4. 警報建議

| 事件 | 嚴重性 | 通知方式 | 說明 |
|---|---|---|---|
| health check 失敗 | Critical | Email/Slack | 應用無法回應 |
| DB 離線 | Critical | Email/Slack | 資料庫無法連線 |
| 外部 API 錯誤率 > 10% | Warning | Slack | TAFT/MOA/Gemini 異常 |
| sync_fda 連續失敗 2 次 | Warning | Slack | 食品業者資料過期 |
| Gemini API 配額不足 | Warning | Email | 超出 API 用量限制 |

---

## 5. 前端用戶體驗監控

| 指標 | 說明 |
|---|---|
| HTMX 請求成功率 | 前端 AJAX 請求是否成功 |
| Spinner 顯示時間 | 用戶等待時間 |
| 搜索結果空率 | 查無資料的比例 (可能反映資料覆蓋問題) |
| 錯誤顯示次數 | 用戶看到錯誤訊息的頻率 |

---

## 6. 目前已實作的監控

| 項目 | 狀態 | 說明 |
|---|---|---|
| `GET /health/` 端點 | ✅ 已實作 | DB 連線 + 版本 + 時間戳 |
| Console 日誌 | ✅ 已實作 | INFO+ 層級，結構化格式 |
| View 層錯誤處理 | ✅ 已實作 | 捕獲 API/非預期錯誤，記錄 ERROR 日誌 |
| 排程器 job 持久化 | ✅ 已實作 | django-apscheduler DjangoJobStore |
| Prometheus metrics | ❌ 未實作 | 需整合 django-prometheus |
| APM (應用效能監控) | ❌ 未實作 | 如需可接入 Datadog/Sentry |
| 外部 API 延遲追蹤 | ❌ 未實作 | 需 middleware 或 decorator |
| 用戶體驗監控 | ❌ 未實作 | 可透過 Google Analytics / Plausible |
