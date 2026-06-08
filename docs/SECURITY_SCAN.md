# 安全掃描結果

## 1. 自動化安全檢查

> 注意: 本專案尚未整合自動化安全掃描工具 (如 Bandit, OWASP ZAP, Trivy)。
> 以下為手動代碼審查結果與建議工具整合方案。

---

## 2. 手動代碼審查結果

### 2.1 Django 安全設定

| 項目 | 狀態 | 說明 |
|---|---|---|
| `SECRET_KEY` 環境變數 | ✅ 通過 | 不寫死程式碼，`os.getenv("DJANGO_SECRET_KEY")` |
| `DEBUG = False` (正式) | ✅ 通過 | `os.getenv("DJANGO_DEBUG", "False").lower() == "true"` |
| `ALLOWED_HOSTS` 限制 | ✅ 通過 | 環境變數設定，非 `*` |
| CSRF 保護啟用 | ✅ 通過 | `CsrfViewMiddleware` 在 MIDDLEWARE 中 |
| X-Frame-Options | ✅ 通過 | `XFrameOptionsMiddleware` 在 MIDDLEWARE 中 |
| SecurityMiddleware | ✅ 通過 | `SecurityMiddleware` 為第一個 middleware |
| HTTPS 強制 | ⚠️ 缺失 | 需 Railway 層或 Django SECURE_SSL_REDIRECT 處理 |
| `SESSION_COOKIE_SECURE` | ⚠️ 缺失 | 預設 False，正式環境應為 True |
| `CSRF_COOKIE_SECURE` | ⚠️ 缺失 | 預設 False，正式環境應為 True |

### 2.2 SQL Injection

| 項目 | 狀態 | 說明 |
|---|---|---|
| ORM 查詢 (參數化) | ✅ 通過 | 所有查詢使用 Django ORM (`icontains`, `filter`)，無 raw SQL |
| sync_fda CSV 匯入 | ✅ 通過 | 使用 `update_or_create` ORM 方法 |
| 無 `extra()` 使用 | ✅ 通過 | 未使用 raw SQL 方法 |
| 無 `raw()` 使用 | ✅ 通過 | 無 `Model.objects.raw()` 呼叫 |

### 2.3 XSS (跨站腳本)

| 項目 | 狀態 | 說明 |
|---|---|---|
| Django 模板自動轉義 | ✅ 通過 | 使用 `{{ var }}` 而非 `{% autoescape off %}`，預設轉義 HTML |
| 用戶輸入顯示 | ✅ 通過 | `{{ initial_query }}` 在 input value 中，Django 會轉義 |
| result 模板 | ⚠️ 審查中 | `{{ result.raw_taft }}` / `{{ result.raw_fda }}` — Depends on Gemini output |
| Gemini API 輸出 | ⚠️ 注意 | Agent answer 可能包含未轉義內容，Django 模板會自動轉義 |

### 2.4 API 金鑰管理

| 項目 | 狀態 | 說明 |
|---|---|---|
| `.env` gitignore | ✅ 通過 | `.env` 在 `.gitignore` 中 |
| API Key 不寫死 | ✅ 通過 | 所有金鑰皆透過環境變數 |
| `.env.example` 不含真金鑰 | ✅ 通過 | 範例值是 `your_gemini_key_here` |
| TAFT/MOA API 無需 Key | ✅ 通過 | 公開 API，不需認證 |

### 2.5 CSRF

| 項目 | 狀態 | 說明 |
|---|---|---|
| GET 查詢 (安全方法) | ✅ 通過 | `search` 端點使用 GET (查詢操作，無副作用) |
| HTMX 請求 | ⚠️ 注意 | 目前 HTMX 使用 `hx-get`。若未來改為 POST，需加入 `{% csrf_token %}` |

### 2.6 依賴安全性

| 項目 | 狀態 | 說明 |
|---|---|---|
| `requirements.txt` pinned 版本 | ⚠️ 缺失 | 部分套件無版本固定 (`django>=4.2`) |
| 已知漏洞掃描 | ❌ 未執行 | 無 `safety check` 或 `pip-audit` 掃描紀錄 |

---

## 3. 建議整合的安全工具

### 3.1 Bandit (Python 安全靜態分析)

```bash
pip install bandit
bandit -r food_safety/ -f json -o security_report.json
```

**檢查範圍**:
- SQL injection
- 命令注入
- 硬編碼密碼
- 不安全 pickle
- XML 外部實體 (XXE)

### 3.2 pip-audit (依賴漏洞)

```bash
pip install pip-audit
pip-audit -r requirements.txt
```

掃描已知 CVE 漏洞。

### 3.3 Safety (依賴漏洞)

```bash
pip install safety
safety check -r requirements.txt
```

### 3.4 Django 安全檢查

```bash
python manage.py check --deploy
```

Django 內建生產環境安全檢查，會報告缺失的生產設定。

### 3.5 OWASP ZAP (DAST)

適合部署後的動態掃描，可設定 CI 中對 staging 環境執行。

---

## 4. 已知安全風險

| 風險 | 影響 | 因應對策 |
|---|---|---|
| 無 HTTPS 強制 | 中間人攻擊 | Railway 層已提供 TLS，應用層也應設定 `SECURE_SSL_REDIRECT` |
| `ALLOWED_HOSTS=*` 開發預設 | Host header 攻擊 | 正式環境務必設為特定 domain |
| Mock 模式可能誤上 production | 回傳模擬資料，不查真實 API | `USE_MOCK_API` 環境變數控制，正式環境設為 False |
| Gemini API Key 洩漏 | 濫用/花費 | 使用 Railway Secret Variable 而非環境變數，定期輪換 |
| 無 rate limiting | API 濫用 | 建議加入 `django-ratelimit` 或 nginx 層限制 |
| 無 CORS 設定 | 不適用 | 目前無跨域需求，若加入 API 端點需設定 CORS |

---

## 5. 安全改進優先級

| 優先級 | 項目 | 預估工時 |
|---|---|---|
| **高** | 執行 `python manage.py check --deploy` 並修正問題 | 1h |
| **高** | 加入 `SESSION_COOKIE_SECURE` 和 `CSRF_COOKIE_SECURE` | 0.5h |
| **高** | 整合 Bandit 到 CI pipeline | 2h |
| **中** | 加入 `pip-audit` 到 CI pipeline | 1h |
| **中** | rate limiting 保護 search 端點 | 2h |
| **低** | OWASP ZAP DAST 定期掃描 | 4h |

---

## 6. 安全聯絡

若發現安全漏洞，請勿公開揭露。請聯絡專案維護者 (見 README)。
