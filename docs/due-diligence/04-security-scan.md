# 安全掃描報告 — Due Diligence Package

## 掃描工具執行結果

### Bandit (Static Analysis)

| 項目 | 值 |
|---|---|
| 指令 | `bandit -r food_safety/ -f json` |
| 結果 | JSON → `docs/due-diligence/bandit_report.json` |
| Total Issues | 94 |
| 高 Severity | **0** |
| 中 Severity | **0** |
| 低 Severity | 94 (全部在測試檔案中) |
| 原始碼行數 | 1291 |

> 所有 94 個 low-severity issue 皆為 `B101: assert_used`，全部位於測試檔案中 (`test_*.py`)，屬於預期行為。**生產程式碼無任何安全問題。**

### pip-audit (Dependency Vulnerabilities)

| 項目 | 值 |
|---|---|
| 指令 | `pip-audit -r requirements.txt --desc` |
| 結果 | **No known vulnerabilities found** ✅ |
| 掃描套件數 | 13 (requirements.txt) |

### Django `check --deploy`

| ID | Severity | 說明 | 因應 |
|---|---|---|---|
| `W004` | Warning | `SECURE_HSTS_SECONDS` 未設定 | Railway 層處理 TLS |
| `W008` | Warning | `SECURE_SSL_REDIRECT` 未啟用 | Railway 自動 TLS 終止 |
| `W009` | Warning | SECRET_KEY 少於 50 字元 | 正式環境使用 Railway Secret 隨機金鑰 |
| `W012` | Warning | `SESSION_COOKIE_SECURE` 未啟用 | 待設定 (依賴 Railway TLS) |
| `W016` | Warning | `CSRF_COOKIE_SECURE` 未啟用 | 待設定 (依賴 Railway TLS) |

## 手動代碼審查結果

### SQL Injection

| 項目 | 狀態 | 說明 |
|---|---|---|
| ORM 參數化查詢 | ✅ | 所有查詢使用 Django ORM (`filter`, `icontains`, `update_or_create`) |
| Raw SQL | ✅ 無使用 | 無 `raw()`, `extra()`, `connection.cursor()` 在 views/services |

### XSS (Cross-Site Scripting)

| 項目 | 狀態 | 說明 |
|---|---|---|
| Django 模板自動轉義 | ✅ | `{{ var }}` 語法預設轉義 HTML |
| 用戶輸入顯示 | ✅ | 搜尋 input 中顯示 `initial_query` 經 Django 轉義 |
| Gemini 輸出 | ⚠️ | 依賴 Gemini 回應，但 Django 模板會自動轉義 |

### API 金鑰管理

| 項目 | 狀態 |
|---|---|
| `.env` in `.gitignore` | ✅ |
| API Key 不寫死程式碼 | ✅ (皆透過環境變數) |
| `.env.example` 不含真金鑰 | ✅ |
| TAFT/MOA 公開 API 無需 Key | ✅ |

### CSRF

| 項目 | 狀態 |
|---|---|
| 目前所有端點皆為 GET | ✅ (查詢操作，無副作用) |
| 若未來改為 POST | ⚠️ 需加入 `{% raw %}{% csrf_token %}{% endraw %}` |

## 已知風險登錄

| 風險 | 影響 | 機率 | 對策 |
|---|---|---|---|
| LLM 幻覺 (Hallucination) | 錯誤食安資訊 | 低 | Prompt 嚴格限縮 + 顯示原始資料來源供交叉比對 |
| 上遊資料造假 | 不可靠的產銷履歷 | 中 | Agent 定位為「偵測異常」非「保證真實」 |
| 食藥署無即時 API | FDA 資料延遲 ≤ 7 天 | 中 | 標註資料更新時間 |
| API Key 洩漏 | Gemini 花費超額 | 低 | Railway Secret + 定期輪換 |

## 建議安全改進

| 優先級 | 項目 | 時程 |
|---|---|---|
| **高** | 整合 Bandit 至 CI pipeline | 2h |
| **高** | 設定 `SESSION_COOKIE_SECURE` + `CSRF_COOKIE_SECURE` | 0.5h |
| **中** | Rate limiting on `/search/` endpoint | 2h |
| **中** | 整合 pip-audit 至 CI | 1h |
| **低** | 加入 Content Security Policy header | 1h |
| **低** | OWASP ZAP DAST 定期掃描 | 4h |
