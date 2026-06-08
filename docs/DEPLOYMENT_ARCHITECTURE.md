# 部署架構

## 整體拓撲

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Railway Cloud                               │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                  Railway Application                         │   │
│  │                                                              │   │
│  │  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐   │   │
│  │  │  Nixpacks     │───▶│  Gunicorn    │───▶│  Django App  │   │   │
│  │  │  Build        │    │  WSGI Server │    │  (config)    │   │   │
│  │  └──────────────┘    └──────────────┘    └──────┬───────┘   │   │
│  │                                                  │           │   │
│  └──────────────────────────────────────────────────┼───────────┘   │
│                                                     │               │
│  ┌──────────────────────────────────────────────────┼───────────┐   │
│  │                    Railway PostgreSQL            │           │   │
│  │                    (DATABASE_URL 自動注入)        ◀──────────┘   │
│  └─────────────────────────────────────────────────┘               │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    外部服務                                    │   │
│  │                                                              │   │
│  │  TAFT API ──── data.moa.gov.tw (HTTP, 無需 Key)              │   │
│  │  MOA API  ──── data.moa.gov.tw (HTTP, 無需 Key)              │   │
│  │  Gemini API ── generativeai.google.com (需 GEMINI_API_KEY)   │   │
│  │  FDA CSV  ──── data.gov.tw (HTTP, 無需 Key)                  │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 部署元件

### 1. Build 系統

| 元件 | 設定值 |
|---|---|
| 建置工具 | Nixpacks (自動偵測 Python/Django) |
| Python 版本 | 3.11.9 (定義於 `runtime.txt`) |
| 相依安裝 | `pip install -r requirements.txt` |

### 2. 應用伺服器

| 元件 | 設定值 |
|---|---|
| WSGI Server | Gunicorn |
| Bind | `0.0.0.0:$PORT` (Railway 自動注入 PORT) |
| Worker 數 | 預設 1 (sync workers) |

### 3. 資料庫

| 元件 | 設定值 |
|---|---|
| 引擎 | PostgreSQL |
| 連線字串 | Railway 自動注入 `DATABASE_URL` |
| 連線池 | `conn_max_age=600` (10 分鐘 keep-alive) |
| Adapter | psycopg2-binary |

### 4. 靜態檔案

| 元件 | 設定值 |
|---|---|
| Serve 方式 | Whitenoise (CompressedManifestStaticFilesStorage) |
| MIDDLEWARE 順序 | SecurityMiddleware → Whitenoise → ... |
| STATIC_ROOT | `BASE_DIR / "staticfiles"` |

### 5. 排程器

| 元件 | 設定值 |
|---|---|
| 工具 | APScheduler + django-apscheduler |
| Job Store | DjangoJobStore (持久化至資料庫) |
| 條件啟動 | `START_SCHEDULER=True` + `RUN_MAIN=true` |
| 工作排程 | 每週日 02:00 UTC → `sync_fda_data` |

---

## 設定檔一覽

### railway.toml

```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "gunicorn config.wsgi:application --bind 0.0.0.0:$PORT"
restartPolicyType = "on-failure"
restartPolicyMaxRetries = 3
```

### Procfile

```
web: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
release: python manage.py migrate
```

### runtime.txt

```
python-3.11.9
```

---

## Release Phase (Migration)

```
git push → Nixpacks build → release command → deploy
                                │
                                ▼
                         python manage.py migrate
                         (自動執行，無需手動介入)
```

- 每次部署自動執行 `python manage.py migrate`
- migration 失敗 → 部署停止，不影響現行版本

---

## 環境變數

| 變數 | 必要 | 開發值 | 正式值 |
|---|---|---|---|
| `DJANGO_SECRET_KEY` | 是 | dev-only | 隨機 50+ 字元 |
| `DJANGO_DEBUG` | 否 | True | False |
| `DJANGO_ALLOWED_HOSTS` | 否 | `localhost,127.0.0.1` | `.railway.app` |
| `USE_MOCK_API` | 否 | True | False |
| `GEMINI_API_KEY` | 正式 | (不填) | Gemini API key |
| `GEMINI_MODEL` | 否 | (不填) | `gemini-2.5-flash` |
| `TAFT_API_BASE_URL` | 否 | (預設值) | 同預設 |
| `TAFT_UNIT_ID` | 否 | `063` | `063` |
| `FDA_DATASET_URL` | 否 | (不填) | data.gov.tw CSV URL |
| `START_SCHEDULER` | 否 | False | True |
| `DATABASE_URL` | 自動 | (不填) | Railway 自動注入 |

---

## 部署流程

```bash
# 1. 安裝 Railway CLI
npm install -g @railway/cli

# 2. 登入
railway login

# 3. 初始化 (首次)
railway init

# 4. 建立 PostgreSQL (Railway Dashboard)
#    自動注入 DATABASE_URL

# 5. 設定環境變數 (Railway Dashboard)

# 6. 部署
railway up

# 7. 首次手動同步食品業者資料
railway run python manage.py sync_fda_data
```

---

## 重啟策略

| 設定 | 值 |
|---|---|
| 類型 | on-failure |
| 最大重試 | 3 次 |

---

## 擴展考量

| 情境 | 建議 |
|---|---|
| 流量成長 | Gunicorn workers: `--workers=2-4` (根據記憶體調整) |
| 排程器高可用 | 使用 Celery Beat + Redis 替代 APScheduler |
| 快取層 | 加入 Redis 緩存 TAFT/MOA API 結果 (TTL 5 分鐘) |
| CDN | 靜態檔移至 Cloudflare R2 或 S3 |
| 多環境 | PR → staging → main → production 部署流 |
