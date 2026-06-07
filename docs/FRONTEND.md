# 前端模板

## Template 結構

```
templates/
├── base.html              # 共用佈局
├── index.html             # 查詢頁面
└── partials/
    └── result.html        # 查詢結果片段（HTMX 局部更新用）
```

---

## base.html — 共用佈局

```html
<!DOCTYPE html>
<html lang="zh-Hant">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>食安查詢 Agent</title>
  <script src="https://unpkg.com/htmx.org@1.9.12"></script>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: system-ui, sans-serif; background: #f5f5f5; color: #333; }
    .container { max-width: 720px; margin: 48px auto; padding: 0 16px; }
    h1 { font-size: 1.5rem; margin-bottom: 24px; }
  </style>
</head>
<body>
  <div class="container">
    {% block content %}{% endblock %}
  </div>
</body>
</html>
```

---

## index.html — 查詢頁面

```html
{% extends "base.html" %}
{% block content %}

<h1>🥬 食安查詢 Agent</h1>

<form>
  <input
    type="text"
    name="q"
    placeholder="輸入追溯碼、作物名稱或業者名稱"
    autofocus
    hx-get="/search/"
    hx-trigger="input changed delay:500ms, search"
    hx-target="#result"
    hx-indicator="#spinner"
    style="width:100%; padding:12px; font-size:1rem; border:1px solid #ccc; border-radius:8px;"
  >
</form>

<div id="spinner" style="display:none; margin-top:12px; color:#888;">
  查詢中...
</div>

<div id="result" style="margin-top:24px;"></div>
{% endblock %}
```

### HTMX 行為說明

| 屬性 | 值 | 說明 |
|---|---|---|
| `hx-get` | `/search/` | 輸入時向此端點發送 GET 請求 |
| `hx-trigger` | `input changed delay:500ms, search` | 輸入停止 500ms 後觸發，或按 Enter 立即觸發 |
| `hx-target` | `#result` | 回應內容注入到 result div |
| `hx-indicator` | `#spinner` | 請求進行中顯示 spinner |

---

## partials/result.html — 查詢結果片段

```html
{% if result.answer %}

<div style="background:#fff; border-radius:12px; padding:24px; box-shadow:0 1px 4px rgba(0,0,0,0.1);">

  <h2 style="font-size:1rem; color:#555; margin-bottom:12px;">🤖 Agent 分析</h2>
  <p style="line-height:1.7;">{{ result.answer }}</p>

  <hr style="margin:20px 0; border:none; border-top:1px solid #eee;">
  <h3 style="font-size:0.85rem; color:#999; margin-bottom:8px;">📄 原始資料來源</h3>

  {% if result.raw_taft %}
  <details style="margin-bottom:8px;">
    <summary style="cursor:pointer; font-size:0.85rem; color:#4a90d9;">產銷履歷資料</summary>
    <pre style="margin-top:8px; font-size:0.78rem; background:#f9f9f9; padding:12px; border-radius:6px; overflow-x:auto;">{{ result.raw_taft }}</pre>
  </details>
  {% endif %}

  {% if result.raw_fda %}
  <details>
    <summary style="cursor:pointer; font-size:0.85rem; color:#4a90d9;">食品業者登錄資料</summary>
    <pre style="margin-top:8px; font-size:0.78rem; background:#f9f9f9; padding:12px; border-radius:6px; overflow-x:auto;">{{ result.raw_fda }}</pre>
  </details>
  {% endif %}

</div>

{% else %}

<div style="background:#fff3cd; border-radius:8px; padding:16px; color:#856404;">
  ⚠️ 查無相關資料，請確認輸入的追溯碼或名稱是否正確。
</div>

{% endif %}
```

### 狀態說明

| 情境 | 顯示 |
|---|---|
| 查詢有結果 | Agent 分析區塊 + 可展開的原始資料來源 |
| 查無資料 | 黃色警告訊息 |
| 載入中 | Spinner 文字（由 hx-indicator 控制） |
