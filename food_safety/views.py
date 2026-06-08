import datetime
import logging
import os
import requests
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.db import connections
from django.db.utils import OperationalError
from .services.agent_service import run_food_agent
from .services.taft_service import query_by_trace_code
from .services.qr_service import generate_product_qr

logger = logging.getLogger(__name__)


def index(request):
    initial_query = request.GET.get("q", "")

    trace_codes_env = os.getenv("MOCK_TRACE_CODES", "")
    trace_codes = [c.strip() for c in trace_codes_env.split(",") if c.strip()] or [
        "TW00123456789", "TW00123456790", "TW00123456791"
    ]
    products = []
    base_url = request.build_absolute_uri("/")

    for code in trace_codes:
        product = query_by_trace_code(code)
        if product:
            product = generate_product_qr(product, base_url)
            products.append(product)

    return render(request, "index.html", {
        "products": products,
        "initial_query": initial_query,
    })


def search(request):
    query = request.GET.get("q", "").strip()
    if not query:
        return HttpResponse("<p>請輸入查詢內容</p>")

    try:
        result = run_food_agent(query)
    except requests.RequestException as e:
        logger.error("External API request failed: %s", e)
        return HttpResponse(
            '<div class="error">查詢失敗：無法連線至外部服務，請稍後再試</div>'
        )
    except Exception as e:
        logger.exception("Unexpected error during food agent query: %s", e)
        return HttpResponse(
            '<div class="error">查詢發生錯誤，請稍後再試</div>'
        )

    return render(request, "partials/result.html", {"result": result})


def health(request):
    db_ok = True
    try:
        connections["default"].cursor().execute("SELECT 1")
    except OperationalError:
        db_ok = False

    return JsonResponse({
        "status": "ok" if db_ok else "degraded",
        "version": "1.0.0",
        "timestamp": datetime.datetime.now().isoformat(),
        "database": "connected" if db_ok else "disconnected",
    })