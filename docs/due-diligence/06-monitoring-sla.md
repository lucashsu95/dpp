# 監控指標與 SLA — Due Diligence Package

## SLA 目標

| 指標 | 目標 | 測量方法 | 警報閾值 |
|---|---|---|---|
| 正常運行時間 | **99.5%** | Railway 平台狀態 | < 99.5% monthly |
| API P95 回應延遲 | **< 2s** | Prometheus / middleware | > 2s for 5min |
| 搜尋成功率 | **> 99%** | `/health/` + 錯誤計數 | > 1% 錯誤率 |
| 外部 API 可用性 | **> 99%** | TAFT/MOA/Gemini 健康 | > 5% 失敗率 |
| 資料同步新鮮度 | **≤ 7 天** | sync_fda 最後成功時間 | > 7 天未同步 |

## 目前已實作監控

### 健康檢查端點

```json
GET /health/
→ { "status": "ok", "version": "1.0.0", "timestamp": "...", "database": "connected" }
```

此端點可被外部監控工具 (UptimeRobot, Railway 內建) 定期輪詢。

### 日誌

```python
# 格式: {levelname} {asctime} {module} {message}
# 日誌事件:
#   ERROR - 外部 API 請求失敗 / 非預期錯誤
#   INFO  - Agent 查詢執行 / DB 同步成功
```

所有日誌輸出至 console (Railway 自動擷取)。

## 建議實作監控

### HTTP Metrics (Prometheus + django-prometheus)

| Metric | Type | Labels |
|---|---|---|
| `django_http_requests_total` | Counter | method, endpoint, status |
| `django_http_requests_latency_seconds` | Histogram | method, endpoint |
| `django_http_requests_body_bytes` | Histogram | method, endpoint |

### 外部 API Metrics

| Metric | Type | Labels |
|---|---|---|
| `taft_api_latency_seconds` | Histogram | endpoint |
| `taft_api_errors_total` | Counter | endpoint, error_type |
| `moa_api_latency_seconds` | Histogram | query_type |
| `gemini_api_latency_seconds` | Histogram | — |
| `gemini_api_token_usage` | Gauge | — |

### 資料庫 Metrics

| Metric | Type | 說明 |
|---|---|---|
| `db_connection_pool_size` | Gauge | 連線數 |
| `db_slow_queries_total` | Counter | 慢查詢 (>100ms) |
| `food_operator_total` | Gauge | FoodOperator 筆數 |
| `last_sync_timestamp` | Gauge | 最後 FDA 同步時間 |

### 排程器 Metrics

| Metric | Type | 說明 |
|---|---|---|
| `sync_success_total` | Counter | 同步成功次數 |
| `sync_failure_total` | Counter | 同步失敗次數 |
| `sync_records_created` | Counter | 新增筆數 |
| `sync_records_updated` | Counter | 更新筆數 |

## 儀表板建議

### Railway 內建監控

- CPU / Memory 使用率
- 請求數 / 頻寬
- 部署歷史
- Service logs

### 建議: Grafana Dashboard

```text
第一行:
  - Uptime (99.5% target)
  - API P95 Latency (< 2s target)
  - Error Rate (< 1% target)

第二行:
  - TAFT API Latency P50/P95/P99
  - MOA API Latency P50/P95/P99
  - Gemini API Latency P50/P95/P99

第三行:
  - DB Connection Count
  - FoodOperator Record Count
  - 7-day Sync Status
```

## 警報規則建議

| 事件 | Severity | 通知 | 閾值 |
|---|---|---|---|
| Service Down | 🔴 Critical | PagerDuty / Slack | `/health/` 連續 3 次失敗 |
| DB Disconnected | 🔴 Critical | Slack | `/health/` database=disconnected |
| High Error Rate | 🟡 Warning | Slack | Error rate > 5% in 5min |
| High Latency | 🟡 Warning | Slack | P95 > 3s in 5min |
| Sync Stale | 🟡 Warning | Slack | > 8 days since last sync |
