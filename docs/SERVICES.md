# Service 層程式碼

## 專案結構

```
food_safety/
├── services/
│   ├── __init__.py
│   ├── taft_service.py        # 產銷履歷 API
│   ├── fda_service.py         # 食品業者查詢
│   └── agent_service.py       # Gemini Agent 整合
├── management/
│   └── commands/
│       └── sync_fda_data.py   # 手動 / 排程匯入
├── models.py
└── views.py
```

---

## taft_service.py — 產銷履歷 API

```python
import os
import requests
from django.conf import settings

TAFT_API_KEY = os.getenv("TAFT_API_KEY")
TAFT_API_BASE_URL = os.getenv("TAFT_API_BASE_URL")

def query_by_trace_code(trace_code: str) -> dict | None:
    """
    用追溯碼查產銷履歷
    回傳原始 API 資料，查無資料回傳 None
    """
    url = f"{TAFT_API_BASE_URL}/TraceabilityData"
    params = {
        "$filter": f"TraceCode eq '{trace_code}'",
        "ApiKey": TAFT_API_KEY,
        "$format": "json",
    }
    try:
        res = requests.get(url, params=params, timeout=10)
        res.raise_for_status()
        data = res.json().get("value", [])
        return data[0] if data else None
    except requests.RequestException as e:
        print(f"[TAFT API Error] {e}")
        return None

def query_by_crop_name(crop_name: str) -> list[dict]:
    """
    用作物名稱查，可能回傳多筆
    """
    url = f"{TAFT_API_BASE_URL}/TraceabilityData"
    params = {
        "$filter": f"contains(CropName, '{crop_name}')",
        "ApiKey": TAFT_API_KEY,
        "$format": "json",
        "$top": 10,
    }
    try:
        res = requests.get(url, params=params, timeout=10)
        res.raise_for_status()
        return res.json().get("value", [])
    except requests.RequestException as e:
        print(f"[TAFT API Error] {e}")
        return []
```

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

## agent_service.py — Gemini Agent 整合

```python
import os
from google import genai
from .taft_service import query_by_trace_code, query_by_crop_name
from .fda_service import query_operator

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

SYSTEM_PROMPT = """
你是一個食品安全查詢助理。
請只根據提供的資料回答，若資料不足請明確說「查無資料」。
不得自行推斷或補充未在資料中出現的資訊。
回答請簡潔，並標註資料來源（產銷履歷 / 食品業者登錄）。
"""

def run_food_agent(query: str) -> dict:
    """
    整合兩個資料來源，交給 Gemini 整理回答
    回傳 { "answer": str, "raw_taft": ..., "raw_fda": ... }
    """
    taft_result = query_by_trace_code(query) or query_by_crop_name(query)
    fda_result  = query_operator(query)

    context = f"""
【產銷履歷資料】
{taft_result if taft_result else '查無產銷履歷資料'}

【食品業者登錄資料】
{fda_result if fda_result else '查無食品業者登錄資料'}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"{SYSTEM_PROMPT}\n\n查詢：{query}\n\n{context}",
    )

    return {
        "answer":   response.text,
        "raw_taft": taft_result,
        "raw_fda":  fda_result,
    }
```

---

## views.py — HTMX 查詢端點

```python
from django.http import HttpResponse
from django.shortcuts import render
from .services.agent_service import run_food_agent

def index(request):
    return render(request, "index.html")

def search(request):
    query = request.GET.get("q", "").strip()
    if not query:
        return HttpResponse("<p>請輸入查詢內容</p>")

    result = run_food_agent(query)
    return render(request, "partials/result.html", {"result": result})
```

---

## urls.py

```python
from django.urls import path
from . import views

urlpatterns = [
    path("",        views.index,  name="index"),
    path("search/", views.search, name="search"),
]
```
