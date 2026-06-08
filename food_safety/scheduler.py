import os
from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from django.core.management import call_command


def run_weekly_sync():
    """Run the sync_fda_data management command."""
    call_command("sync_fda_data")


def start_scheduler():
    """Start the APScheduler with DjangoJobStore for persistence."""
    if os.environ.get("START_SCHEDULER", "False").lower() != "true":
        return

    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), "default")

    scheduler.add_job(
        run_weekly_sync,
        "cron",
        day_of_week="sun",
        hour=2,
        minute=0,
        id="weekly_fda_sync",
        replace_existing=True,
    )

    scheduler.start()