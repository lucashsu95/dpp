# 食安 DPP 查詢 Agent

結合**數位產品護照（DPP）**概念與 **AI Agent**，打造台灣食品安全透明查詢系統。
第一階段以公開政府資料為基礎，讓消費者或業者能用自然語言查詢農產品產銷履歷與食品業者登錄狀態。

---

## 系統架構

```
使用者輸入（追溯碼 or 作物名稱）
    ↓
Django View 接收
    ↓
打產銷履歷 API（data.gov.tw）
    ↓
查本地資料庫（食品業者 CSV 匯入）
    ↓
整合資料丟給 Claude API
    ↓
HTMX 更新前端顯示結果
```

## 技術棧

| 層級 | 技術 |
|---|---|
| 後端框架 | Django |
| 資料庫 | PostgreSQL |
| 非同步排程 | Celery Beat / APScheduler |
| 前端互動 | HTMX |
| AI 推論 | Claude API（claude-sonnet） |
| 爬蟲備援 | requests + BeautifulSoup |

## Prompt 設計原則

```
只根據以下資料回答，若資料不足請明確說「查無資料」，
不得自行推斷或補充未在資料中出現的資訊。
```

> 核心原則：Agent 是資料整理者，不是知識生成者。

---

## 快速啟動

```bash
pip install django anthropic requests python-dotenv gunicorn whitenoise
cp .env.example .env
python manage.py makemigrations
python manage.py migrate
python manage.py sync_fda_data
python manage.py runserver
```

---

## 文件索引

| 文件 | 說明 |
|---|---|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 系統架構、資料流、模組職責 |
| [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md) | 產銷履歷 API、食品業者 CSV、環境變數 |
| [docs/SERVICES.md](docs/SERVICES.md) | Service 層程式碼（taft/fda/agent + models + views） |
| [docs/FRONTEND.md](docs/FRONTEND.md) | HTMX 模板與前端行為 |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Railway 部署、環境設定 |
| [docs/ROADMAP.md](docs/ROADMAP.md) | 開發里程碑、未來階段、已知風險 |
