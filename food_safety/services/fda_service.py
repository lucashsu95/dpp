from food_safety.models import FoodOperator


def query_operator(keyword: str) -> list[dict]:
    """
    從本地資料庫查食品業者
    keyword 可以是業者名稱或統一編號
    """
    if not keyword:
        return []

    qs = FoodOperator.objects.filter(name__icontains=keyword) | FoodOperator.objects.filter(
        business_id__icontains=keyword
    )
    return list(qs.values("name", "business_id", "category", "address", "registered_at")[:10])