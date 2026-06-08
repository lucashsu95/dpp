---
---

# Service 層程式碼

## 專案結構

```
food_safety/
├── services/
│   ├── __init__.py
│   ├── taft_service.py        # 產銷履歷 API (data.moa.gov.tw)
│   ├── moa_service.py         # 農業部開放資料 (檢驗/有機/CAS/農藥)
│   ├── fda_service.py         # 食品業者查詢
│   └── agent_service.py       # Gemini Agent 整合
├── management/
│   └── commands/
│       └── sync_fda_data.py   # 手動 / 排程匯入
├── scheduler.py               # APScheduler 排程器 (每週同步)
├── models.py
└── views.py
```

---

## taft_service.py — 產銷履歷 API

```python
import os
import requests
from django.conf import settings

TAFT_API_BASE_URL = os.getenv("TAFT_API_BASE_URL")
TAFT_UNIT_ID = os.getenv("TAFT_UNIT_ID", "063")
USE_MOCK_API = os.getenv("USE_MOCK_API", "False").lower() == "true"


def query_by_trace_code(trace_code: str) -> dict | None:
    """
    用追溯碼查產銷履歷
    回傳原始 API 資料，查無資料回傳 None
    """
    if USE_MOCK_API:
        return _mock_trace_code(trace_code)

    url = TAFT_API_BASE_URL
    params = {
        "Tracecode": trace_code,
        "UnitId": TAFT_UNIT_ID,
    }
    try:
        res = requests.get(url, params=params, timeout=10)
        res.raise_for_status()
        data = res.json()
        return data[0] if data else None
    except requests.RequestException as e:
        print(f"[TAFT API Error] {e}")
        return None


def query_by_product_name(product_name: str) -> list[dict]:
    """
    用產品名稱查，可能回傳多筆
    最多回傳 20 筆
    """
    if USE_MOCK_API:
        return _mock_product_name(product_name)

    url = TAFT_API_BASE_URL
    params = {
        "ProductName": product_name,
        "UnitId": TAFT_UNIT_ID,
    }
    try:
        res = requests.get(url, params=params, timeout=10)
        res.raise_for_status()
        data = res.json()
        return data[:20]
    except requests.RequestException as e:
        print(f"[TAFT API Error] {e}")
        return []
```

主要變更：

- **移除 `TAFT_API_KEY`**：新端點不需要 API Key
- **移除 `$filter` OData 語法**：改用 `Tracecode` / `ProductName` 查詢參數
- **新增 `TAFT_UNIT_ID`**：單位識別碼，預設 `063`
- **`query_by_crop_name` 更名為 `query_by_product_name`**：參數名稱由 `crop_name` 改為 `product_name`
- **支援 Mock 模式**：`USE_MOCK_API=True` 時回傳模擬資料

---

## moa_service.py — 農業部開放資料查詢

```python
import requests

MOA_API_BASE_URL = "https://data.moa.gov.tw/Service/OpenData/DataFileService.aspx"
MOA_API_TRANS_URL = "https://data.moa.gov.tw/Service/OpenData/TransService.aspx"
MOA_PESTICIDE_DATA_URL = "https://data.moa.gov.tw/Service/OpenData/FromM/PesticideData.aspx"
MOA_UNIT_ID_INSPECTION = "271"
MOA_UNIT_ID_ORGANIC = "270"
MOA_UNIT_ID_CAS = "qNRePfOf8YMS"


def query_inspection_result(crop_name: str) -> list[dict]:
    """
    用作物名稱查農藥殘留檢驗結果。
    過濾樣品名稱包含 crop_name 的資料，最多回傳 20 筆。
    """
    params = {"UnitId": MOA_UNIT_ID_INSPECTION}
    try:
        res = requests.get(MOA_API_BASE_URL, params=params, timeout=10)
        res.raise_for_status()
        data = res.json()
    except (requests.RequestException, ValueError):
        return []

    matched = [
        record
        for record in data
        if crop_name.lower() in record.get("樣品名稱", "").lower()
    ]
    return matched[:20]


def query_organic_cert(producer_name: str) -> list[dict]:
    """
    用業者名稱查有機農產品驗證資料。
    過濾農產品經營業者_進口業者包含 producer_name 的資料，最多回傳 20 筆。
    """
    params = {"UnitId": MOA_UNIT_ID_ORGANIC}
    try:
        res = requests.get(MOA_API_BASE_URL, params=params, timeout=10)
        res.raise_for_status()
        data = res.json()
    except (requests.RequestException, ValueError):
        return []

    matched = [
        record
        for record in data
        if producer_name.lower() in record.get("農產品經營業者_進口業者", "").lower()
    ]
    return matched[:20]


def query_cas_product(product_name: str) -> list[dict]:
    """
    用產品名稱查 CAS 驗證資料。
    過濾 Product_Name 包含 product_name 的資料，最多回傳 20 筆。
    """
    params = {"UnitId": MOA_UNIT_ID_CAS}
    try:
        res = requests.get(MOA_API_TRANS_URL, params=params, timeout=10)
        res.raise_for_status()
        data = res.json()
    except (requests.RequestException, ValueError):
        return []

    matched = [
        record
        for record in data
        if product_name.lower() in record.get("Product_Name", "").lower()
    ]
    return matched[:20]


def query_pesticide_info(pesticide_name: str) -> list[dict]:
    """
    用農藥名稱查農藥資訊資料。
    過濾中文名稱包含 pesticide_name 的資料，最多回傳 20 筆。
    """
    try:
        res = requests.get(MOA_PESTICIDE_DATA_URL, timeout=10)
        res.raise_for_status()
        data = res.json()
    except (requests.RequestException, ValueError):
        return []

    matched = [
        record
        for record in data
        if pesticide_name.lower() in record.get("中文名稱", "").lower()
    ]
    return matched[:20]
```

四個查詢函數：

| 函數 | 用途 | 端點 |
|---|---|---|
| `query_inspection_result` | 農藥殘留檢驗 | `DataFileService.aspx?UnitId=271` |
| `query_organic_cert` | 有機農產品驗證 | `DataFileService.aspx?UnitId=270` |
| `query_cas_product` | CAS 驗證產品 | `TransService.aspx?UnitId=qNRePfOf8YMS` |
| `query_pesticide_info` | 農藥資訊 | `PesticideData.aspx` |

所有函數皆先 fetch 完整資料集再於本地端過濾，回傳最多 20 筆。

---

## fda_service.py — 食品業者本地查詢

```python
from food_safety.models import FoodOperator

def query_operator(keyword: str) -> list[dict]:
    """
    從本地資料庫查食品業者
    keyword 可以是業者名稱或統一編號
    """
    qs = FoodOperator.objects.filter(
        name__icontains=keyword
    ) | FoodOperator.objects.filter(
        business_id__icontains=keyword
    )
    return list(qs.values("name", "business_id", "category", "address", "registered_at")[:10])
```

---

## models.py — 食品業者資料表

```python
from django.db import models

class FoodOperator(models.Model):
    business_id   = models.CharField(max_length=20, db_index=True)
    name          = models.CharField(max_length=100, db_index=True)
    category      = models.CharField(max_length=50, blank=True)
    address       = models.CharField(max_length=200, blank=True)
    registered_at = models.DateField(null=True, blank=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "食品業者"
```

---

## sync_fda_data.py — CSV 匯入指令

```python
import os, csv, requests
from django.core.management.base import BaseCommand
from food_safety.models import FoodOperator

FDA_DATASET_URL = os.getenv("FDA_DATASET_URL")

class Command(BaseCommand):
    help = "從食藥署 Open Data 同步食品業者資料"

    def handle(self, *args, **kwargs):
        self.stdout.write("開始下載食品業者資料集...")
        res = requests.get(FDA_DATASET_URL, timeout=30)
        res.encoding = "utf-8-sig"
        lines = res.text.splitlines()
        reader = csv.DictReader(lines)

        created, updated = 0, 0
        for row in reader:
            obj, is_new = FoodOperator.objects.update_or_create(
                business_id=row.get("統一編號", "").strip(),
                defaults={
                    "name":          row.get("業者名稱", "").strip(),
                    "category":      row.get("業別", "").strip(),
                    "address":       row.get("地址", "").strip(),
                    "registered_at": row.get("登錄日期") or None,
                }
            )
            if is_new:
                created += 1
            else:
                updated += 1

        self.stdout.write(f"完成：新增 {created} 筆，更新 {updated} 筆")
```

---

## scheduler.py — APScheduler 排程器

```python
import os
from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from django.core.management import call_command


def run_weekly_sync():
    """Run the sync_fda_data management command."""
    call_command("sync_fda_data")


def start_scheduler():
    """Start the APScheduler with DjangoJobStore for persistence."""
    if os.environ.get("START_SCHEDULER", "False").lower() != "true":
        return

    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), "default")

    scheduler.add_job(
        run_weekly_sync,
        "cron",
        day_of_week="sun",
        hour=2,
        minute=0,
        id="weekly_fda_sync",
        replace_existing=True,
    )

    scheduler.start()
```

使用 `django-apscheduler` 搭配 `DjangoJobStore` 實現排程持久化。每週日 02:00 執行 `sync_fda_data` 指令，由 `START_SCHEDULER` 環境變數控制啟停。

---

## apps.py — AppConfig 啟動鉤子

```python
import os
from django.apps import AppConfig


class FoodSafetyConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "food_safety"
    verbose_name = "食品安全"

    def ready(self):
        if os.environ.get("START_SCHEDULER", "False").lower() != "true":
            return
        if os.environ.get("RUN_MAIN") != "true":
            return
        from food_safety.scheduler import start_scheduler

        start_scheduler()
```

在 Django 啟動時透過 `ready()` 鉤子條件式啟動排程器。僅當 `START_SCHEDULER=True` 且 `RUN_MAIN=true`（避免 dev 模式下重複啟動）時才會初始化。

---

## agent_service.py — Gemini Agent 整合

```python
import os
from google import genai
from google.genai import types
from .taft_service import query_by_trace_code, query_by_product_name
from .fda_service import query_operator
from .moa_service import (
    query_inspection_result,
    query_organic_cert,
    query_cas_product,
    query_pesticide_info,
)

USE_MOCK = os.getenv("USE_MOCK_API", "False").lower() == "true"

SYSTEM_PROMPT = """
你是一個食品安全查詢助理。
請只根據提供的資料回答，若資料不足請明確說「查無資料」。
不得自行推斷或補充未在資料中出現的資訊。
回答請簡潔，並標註資料來源（產銷履歷 / 食品業者登錄 / 農藥檢驗 / 有機驗證 / CAS驗證 / 農藥資訊）。
"""


def _mock_agent(query: str, taft_result, fda_result, inspection_result, organic_result, cas_result, pesticide_result) -> str:
    parts = [f"🔍 查詢：{query}\n"]
    if taft_result:
        if isinstance(taft_result, list):
            taft_result = taft_result[0] if taft_result else None
        if taft_result:
            crop = taft_result.get("ProductName", "未知")
            farmer = taft_result.get("FarmerName", "未知")
            origin = taft_result.get("FarmLocation") or taft_result.get("Origin", "未知")
            date = taft_result.get("HarvestDate") or taft_result.get("PackDate", "未知")
            cert = taft_result.get("Certification", "")
            parts.append(
                f"✅ **產銷履歷**：{crop}，種植者：{farmer}，產地：{origin}"
                f"，採收日期：{date}"
                + (f"，認證：{cert}" if cert else "")
            )
        else:
            parts.append("❌ **產銷履歷**：查無資料")
    else:
        parts.append("❌ **產銷履歷**：查無資料")

    if inspection_result:
        parts.append(f"✅ **農藥殘留檢驗**：找到 {len(inspection_result)} 筆資料")
        for r in inspection_result[:3]:
            parts.append(f"   - {r.get('樣品名稱', '未知')}: {r.get('檢出藥劑ppm', '未檢出')}")
    else:
        parts.append("❌ **農藥殘留檢驗**：查無資料")

    if organic_result:
        parts.append(f"✅ **有機驗證**：找到 {len(organic_result)} 筆資料")
        for r in organic_result[:3]:
            parts.append(f"   - {r.get('農產品經營業者_進口業者', '未知')}: {r.get('標題', '未知')}")
    else:
        parts.append("❌ **有機驗證**：查無資料")

    if cas_result:
        parts.append(f"✅ **CAS驗證**：找到 {len(cas_result)} 筆資料")
        for r in cas_result[:3]:
            parts.append(f"   - {r.get('Product_Name', '未知')}: {r.get('Factory_CName', '未知')}")
    else:
        parts.append("❌ **CAS驗證**：查無資料")

    if pesticide_result:
        parts.append(f"✅ **農藥資訊**：找到 {len(pesticide_result)} 筆資料")
        for r in pesticide_result[:3]:
            parts.append(f"   - {r.get('中文名稱', '未知')}: {r.get('許可證號', '未知')}")
    else:
        parts.append("❌ **農藥資訊**：查無資料")

    if fda_result:
        for op in fda_result[:3]:
            parts.append(
                f"✅ **食品業者**：{op['name']}（統編：{op['business_id']}"
                f"，類別：{op.get('category', '')}）"
            )
    else:
        parts.append("❌ **食品業者**：查無資料")

    parts.append("\n⚠️ *此為模擬回應，正式使用時將由 Gemini API 產出*")
    return "\n".join(parts)


def run_food_agent(query: str) -> dict:
    """
    整合多個資料來源，交給 Gemini 整理回答
    回傳 { "answer": str, "raw_taft": ..., "raw_fda": ..., "raw_inspection": ..., "raw_organic": ..., "raw_cas": ..., "raw_pesticide": ... }
    """
    # TAFT: 追溯碼或產品名稱查詢
    taft_result = query_by_trace_code(query) or query_by_product_name(query)
    
    # MOA: 4個查詢都執行（即使 TAFT 查無資料）
    inspection_result = query_inspection_result(query)[:20]
    organic_result = query_organic_cert(query)[:20]
    cas_result = query_cas_product(query)[:20]
    pesticide_result = query_pesticide_info(query)[:20]
    
    # FDA: 業者查詢
    fda_result = query_operator(query)

    if USE_MOCK or not os.getenv("GEMINI_API_KEY"):
        answer = _mock_agent(query, taft_result, fda_result, inspection_result, organic_result, cas_result, pesticide_result)
    else:
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        context = f"""
【產銷履歷資料】
{taft_result if taft_result else '查無產銷履歷資料'}

【農藥殘留檢驗資料】
{inspection_result if inspection_result else '查無農藥殘留檢驗資料'}

【有機驗證資料】
{organic_result if organic_result else '查無有機驗證資料'}

【CAS驗證資料】
{cas_result if cas_result else '查無CAS驗證資料'}

【農藥資訊資料】
{pesticide_result if pesticide_result else '查無農藥資訊資料'}

【食品業者登錄資料】
{fda_result if fda_result else '查無食品業者登錄資料'}
"""
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            max_output_tokens=1024,
        )
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        response = client.models.generate_content(
            model=model_name,
            contents=f"查詢：{query}\n\n{context}",
            config=config,
        )
        answer = response.text

    return {
        "answer": answer,
        "raw_taft": taft_result,
        "raw_fda": fda_result,
        "raw_inspection": inspection_result,
        "raw_organic": organic_result,
        "raw_cas": cas_result,
        "raw_pesticide": pesticide_result,
    }
```

主要變更：

- **新增 MOA 查詢整合**：`run_food_agent` 現在會同時查詢 7 個資料來源（TAFT + 4 個 MOA + FDA）
- **回傳 7 個 key**：`answer`, `raw_taft`, `raw_fda`, `raw_inspection`, `raw_organic`, `raw_cas`, `raw_pesticide`
- **`query_by_crop_name` 改為 `query_by_product_name`**：對應 TAFT 端的重新命名
- **Mock 模式支援多來源**：`_mock_agent` 會列出所有查詢結果
- **SYSTEM_PROMPT 增加資料來源標籤**：加入農藥檢驗、有機驗證、CAS 驗證、農藥資訊
- **使用 `GenerateContentConfig`**：透過 `types.GenerateContentConfig` 設定 system instruction 與 token 上限

---

## views.py — HTMX 查詢端點

```python
import logging
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from .services.agent_service import run_food_agent
import requests
from datetime import datetime
from django.db import connections

logger = logging.getLogger(__name__)

def index(request):
    return render(request, "index.html")

def search(request):
    query = request.GET.get("q", "").strip()
    if not query:
        return HttpResponse("<p>請輸入查詢內容</p>")
    try:
        result = run_food_agent(query)
        return render(request, "partials/result.html", {"result": result})
    except requests.RequestException:
        logger.error(f"API unavailable for query: {query}")
        return render(request, "partials/result.html", {"result": {"answer": None}, "error": "API 服務暫時無法連線，請稍後再試"})
    except Exception as e:
        logger.error(f"Search error for query '{query}': {e}", exc_info=True)
        return render(request, "partials/result.html", {"result": {"answer": None}, "error": "查詢過程發生錯誤，請稍後再試"})

def health(request):
    db_ok = "disconnected"
    try:
        connections['default'].cursor().execute('SELECT 1')
        db_ok = "connected"
    except Exception:
        db_ok = "disconnected"
    return JsonResponse({
        "status": "ok",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "database": db_ok,
    })
```

---

## urls.py

```python
from django.urls import path
from . import views

urlpatterns = [
    path("",        views.index,  name="index"),
    path("search/", views.search, name="search"),
    path("health/", views.health, name="health"),
]
```
