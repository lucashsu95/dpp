import os
from django.apps import AppConfig


class FoodSafetyConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "food_safety"
    verbose_name = "食品安全"

    def ready(self):
        if os.environ.get("START_SCHEDULER", "False").lower() != "true":
            return
        if os.environ.get("RUN_MAIN") != "true":
            return
        from food_safety.scheduler import start_scheduler

        start_scheduler()