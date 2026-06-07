import os
import csv
import requests
from django.core.management.base import BaseCommand
from food_safety.models import FoodOperator

FDA_DATASET_URL = os.getenv("FDA_DATASET_URL")


class Command(BaseCommand):
    help = "從食藥署 Open Data 同步食品業者資料"

    def handle(self, *args, **kwargs):
        if not FDA_DATASET_URL:
            self.stderr.write("FDA_DATASET_URL not configured")
            return

        self.stdout.write("開始下載食品業者資料集...")
        try:
            res = requests.get(FDA_DATASET_URL, timeout=30)
            res.encoding = "utf-8-sig"
            lines = res.text.splitlines()
            reader = csv.DictReader(lines)

            created, updated = 0, 0
            for row in reader:
                business_id = row.get("統一編號", "").strip()
                if not business_id:
                    continue

                obj, is_new = FoodOperator.objects.update_or_create(
                    business_id=business_id,
                    defaults={
                        "name": row.get("業者名稱", "").strip(),
                        "category": row.get("業別", "").strip(),
                        "address": row.get("地址", "").strip(),
                        "registered_at": row.get("登錄日期") or None,
                    },
                )
                if is_new:
                    created += 1
                else:
                    updated += 1

            self.stdout.write(self.style.SUCCESS(f"完成：新增 {created} 筆，更新 {updated} 筆"))
        except requests.RequestException as e:
            self.stderr.write(f"下載失敗: {e}")
        except Exception as e:
            self.stderr.write(f"處理失敗: {e}")