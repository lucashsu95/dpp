# 食安 DPP 查詢 Agent

結合數位產品護照（DPP）概念與 AI Agent，打造台灣食品安全透明查詢系統。
第一階段以公開政府資料為基礎，讓消費者或業者能用自然語言查詢農產品產銷履歷與食品業者登錄狀態。

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
整合資料丟給 Gemini API
    ↓
HTMX 更新前端顯示結果
```

## 前置需求

- Python 3.11+
- pip

## 快速啟動

### 1. 啟動虛擬環境

本專案使用 venv（已建立於 `venv/`），啟動方式：

```bash
source venv/bin/activate
```

確認 Python 路徑正確：

```bash
which python
# 應顯示 /home/user/dpp/venv/bin/python
```

### 2. 安裝依賴

```bash
pip install -r requirements.txt
```

### 3. 設定環境變數

```bash
cp .env.example .env
```

編輯 `.env`，填入 API 金鑰（開發階段可維持 `USE_MOCK_API=True`，不需真實金鑰）。

### 4. 資料庫遷移

```bash
python manage.py migrate
```

### 5. 啟動開發伺服器

```bash
python manage.py runserver
```

開啟瀏覽器前往 <http://localhost:8000>

## 使用方式

在搜尋框輸入追溯碼或作物名稱：

- **追溯碼**：輸入 `TW00123456789`（mock 模式下有預設資料）
- **作物名稱**：輸入 `小白菜`
- **業者名稱**：輸入 `開心農場`

開發階段預設使用 mock 資料，不需串接真實 API。

### Mock 模式（USE_MOCK_API=True）

預設開啟。Agent 會用 `_mock_agent()` 回傳模擬回答，不消耗 API 額度。

### 正式模式（USE_MOCK_API=False）

需在 `.env` 設定：

- `GEMINI_API_KEY` — Gemini API 金鑰
- `TAFT_API_KEY` — 產銷履歷 API 金鑰
- `USE_MOCK_API=False`

## 專案結構

```
dpp/
├── config/                  # Django 專案設定
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── food_safety/             # 主要 App
│   ├── models.py            # FoodOperator
│   ├── views.py             # index() + search()
│   ├── services/
│   │   ├── taft_service.py  # 產銷履歷 API
│   │   ├── fda_service.py   # 食品業者查詢
│   │   └── agent_service.py # AI Agent（Gemini）
│   └── management/commands/
│       └── sync_fda_data.py # CSV 匯入
├── templates/
│   ├── base.html
│   ├── index.html
│   └── partials/result.html
├── requirements.txt
├── railway.toml
├── Procfile
├── runtime.txt
└── .env.example
```

## 部署

支援 Railway 一鍵部署。詳見 [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)。

## 文件索引

| 文件 | 說明 |
|---|---|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 系統架構、資料流、模組職責 |
| [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md) | 產銷履歷 API、食品業者 CSV、環境變數 |
| [docs/SERVICES.md](docs/SERVICES.md) | Service 層程式碼 |
| [docs/FRONTEND.md](docs/FRONTEND.md) | HTMX 模板與前端行為 |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Railway 部署設定 |
| [docs/ROADMAP.md](docs/ROADMAP.md) | 開發里程碑、未來階段、已知風險 |
