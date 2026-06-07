import os
from google import genai
from google.genai import types
from .taft_service import query_by_trace_code, query_by_crop_name
from .fda_service import query_operator

USE_MOCK = os.getenv("USE_MOCK_API", "False").lower() == "true"

SYSTEM_PROMPT = """
你是一個食品安全查詢助理。
請只根據提供的資料回答，若資料不足請明確說「查無資料」。
不得自行推斷或補充未在資料中出現的資訊。
回答請簡潔，並標註資料來源（產銷履歷 / 食品業者登錄）。
"""


def _mock_agent(query: str, taft_result, fda_result) -> str:
    parts = [f"🔍 查詢：{query}\n"]
    if taft_result:
        if isinstance(taft_result, list):
            taft_result = taft_result[0] if taft_result else None
        if taft_result:
            crop = taft_result.get("CropName", "未知")
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
    整合兩個資料來源，交給 Gemini 整理回答
    回傳 { "answer": str, "raw_taft": ..., "raw_fda": ... }
    """
    taft_result = query_by_trace_code(query) or query_by_crop_name(query)
    fda_result = query_operator(query)

    if USE_MOCK or not os.getenv("GEMINI_API_KEY"):
        answer = _mock_agent(query, taft_result, fda_result)
    else:
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        context = f"""
【產銷履歷資料】
{taft_result if taft_result else '查無產銷履歷資料'}

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
    }