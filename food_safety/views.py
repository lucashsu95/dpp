import os
from django.http import HttpResponse
from django.shortcuts import render
from .services.agent_service import run_food_agent
from .services.taft_service import _mock_trace_code
from .services.qr_service import generate_product_qr


def index(request):
    initial_query = request.GET.get("q", "")

    trace_codes_env = os.getenv("MOCK_TRACE_CODES", "")
    trace_codes = [c.strip() for c in trace_codes_env.split(",") if c.strip()] or [
        "TW00123456789", "TW00123456790", "TW00123456791"
    ]
    products = []
    base_url = request.build_absolute_uri("/")

    for code in trace_codes:
        product = _mock_trace_code(code)
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

    result = run_food_agent(query)
    return render(request, "partials/result.html", {"result": result})
