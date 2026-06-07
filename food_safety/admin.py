from django.contrib import admin
from .models import FoodOperator


@admin.register(FoodOperator)
class FoodOperatorAdmin(admin.ModelAdmin):
    list_display = ("business_id", "name", "category", "address", "registered_at", "updated_at")
    search_fields = ("business_id", "name", "address")
    list_filter = ("category", "registered_at")
    ordering = ("-updated_at",)