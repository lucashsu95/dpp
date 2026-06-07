"""
QR Code 產生服務

提供 QR Code 圖片的 Base64 Data URI 產生，
以及包裝成產品查詢 QR 的功能。
"""

import base64
from io import BytesIO


def generate_qr_data_url(data: str, box_size: int = 6, border: int = 2) -> str | None:
    """
    將 data 編碼為 QR Code，回傳 Base64 Data URI 字串。

    參數
    ----
    data : str
        要編碼的內容（追溯碼、網址等）
    box_size : int
        每個 QR 模組的像素大小（預設 6）
    border : int
        QR 碼邊框格數（預設 2）

    回傳
    ----
    str | None
        data:image/png;base64,... 格式的字串；
        若 qrcode 或 PIL 不可用則回傳 None。
    """
    try:
        import qrcode
    except ImportError:
        return None

    try:
        qr = qrcode.QRCode(box_size=box_size, border=border)
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image()
    except Exception:
        return None

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    b64 = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def generate_product_qr(product: dict, base_url: str) -> dict:
    """
    接受產品 dict 與 base_url，回傳追加 QR 資訊的產品 dict。

    回傳的 dict 會額外包含：
    - qr_data_url : QR Code 的 Base64 Data URI
    - query_url   : 完整的查詢頁面網址

    若 QR 產生失敗，qr_data_url 為 None。
    """
    trace_code = product.get("TraceCode", "")
    query_url = f"{base_url}/?q={trace_code}"

    result = dict(product)
    result["qr_data_url"] = generate_qr_data_url(query_url)
    result["query_url"] = query_url
    return result
