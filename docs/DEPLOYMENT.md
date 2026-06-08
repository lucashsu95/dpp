---
---
# Railway 部署

## 專案根目錄結構（新增檔案）

```
project/
├── railway.toml
├── Procfile
├── requirements.txt
├── runtime.txt
└── ...
```

---

## railway.toml

```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "gunicorn config.wsgi:application --bind 0.0.0.0:$PORT"
restartPolicyType = "on-failure"
restartPolicyMaxRetries = 3
```

> `config` 是你的 Django 專案名稱（有 `wsgi.py` 的那個資料夾），請依實際名稱修改。

---

## Procfile

```
web: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
release: python manage.py migrate
```

> `release` 指令會在每次部署時自動執行 migration，不需要手動進去跑。

---

## runtime.txt

```
python-3.11.9
```

---

## requirements.txt

```
django>=4.2
google-genai
requests
python-dotenv
gunicorn
whitenoise
psycopg2-binary
dj-database-url
```

> `psycopg2-binary` 是 Railway PostgreSQL 必要的 adapter。
> `whitenoise` 讓 Django 能直接 serve 靜態檔案，不需要額外設定 Nginx。
> `dj-database-url` 用於從 `DATABASE_URL` 環境變數解析資料庫連線。

---

## settings.py 調整

```python
import os
from pathlib import Path

# 靜態檔案（whitenoise）
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # 加在 SecurityMiddleware 下面
    ...
]

STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# 資料庫（Railway 會自動注入 DATABASE_URL）
import dj_database_url
DATABASES = {
    "default": dj_database_url.config(
        default=os.getenv("DATABASE_URL"),
        conn_max_age=600,
    )
}

# 安全設定
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
DEBUG = os.getenv("DEBUG", "False") == "True"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(",")
```

---

## 環境變數設定

在 Railway Dashboard 設定：

| 變數 | 說明 |
|---|---|
| `DJANGO_SECRET_KEY` | Django 密鑰（必填） |
| `TAFT_UNIT_ID` | 產銷履歷單位代碼 (`063`) |
| `GEMINI_API_KEY` | Gemini API 金鑰 |
| `FDA_DATASET_URL` | 食品業者資料集下載網址 |
| `ALLOWED_HOSTS` | 例如 `your-app.railway.app` |
| `DEBUG` | `False` |

> `DATABASE_URL` 會由 Railway PostgreSQL 服務自動注入。

---

## 部署流程

```bash
# 1. 安裝 Railway CLI
npm install -g @railway/cli

# 2. 登入
railway login

# 3. 初始化專案（第一次）
railway init

# 4. 在 Railway Dashboard 開一個 PostgreSQL 服務
#    → 它會自動把 DATABASE_URL 注入到你的環境變數

# 5. 在 Railway Dashboard 設定環境變數（見上表）

# 6. 部署
railway up

# 7. 匯入食品業者資料（第一次手動執行）
railway run python manage.py sync_fda_data
```
