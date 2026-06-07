from django.db import models


class FoodOperator(models.Model):
    business_id = models.CharField(max_length=20, db_index=True, verbose_name="統一編號")
    name = models.CharField(max_length=100, db_index=True, verbose_name="業者名稱")
    category = models.CharField(max_length=50, blank=True, verbose_name="業別")
    address = models.CharField(max_length=200, blank=True, verbose_name="地址")
    registered_at = models.DateField(null=True, blank=True, verbose_name="登錄日期")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")

    class Meta:
        verbose_name = "食品業者"
        verbose_name_plural = "食品業者"

    def __str__(self):
        return f"{self.name} ({self.business_id})"