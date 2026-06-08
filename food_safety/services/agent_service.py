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