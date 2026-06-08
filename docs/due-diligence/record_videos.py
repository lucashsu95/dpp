"""
Record demo videos of the DPP Food Safety app using Playwright.
"""
import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
sys.path.insert(0, "/home/user/dpp")

from playwright.sync_api import sync_playwright
import django
django.setup()

BASE_URL = "http://localhost:8765"
VIDEO_DIR = "/home/user/dpp/docs/due-diligence/videos"
os.makedirs(VIDEO_DIR, exist_ok=True)


def record_happy_path():
    """5-min Happy Path: trace code search → result → QR → source markers"""
    print("🎬 Recording: Happy Path Demo...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            locale="zh-TW",
            record_video_dir=VIDEO_DIR,
            record_video_size={"width": 1280, "height": 800},
        )
        page = context.new_page()

        # 1. Homepage with product cards
        page.goto(BASE_URL)
        page.wait_for_timeout(2000)

        # 2. Search with trace code
        page.goto(f"{BASE_URL}/search/?q=TW00123456789")
        page.wait_for_timeout(3000)

        # 3. Scroll result area
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1000)

        # 4. Search with crop name
        page.goto(f"{BASE_URL}/search/?q=青江菜")
        page.wait_for_timeout(3000)

        # 5. Search with operator name
        page.goto(f"{BASE_URL}/search/?q=開心農場")
        page.wait_for_timeout(2000)

        # 6. Go back to home to show product cards + QR
        page.goto(BASE_URL)
        page.wait_for_timeout(2000)

        context.close()
        browser.close()
        print(f"   ✅ Happy Path recording saved")


def record_anomaly_demo():
    """
    2-min Anomaly Demo: currently no anomaly detection implemented.
    Records current error handling capabilities:
    - Empty query handling (graceful)
    - No results found
    - Health check status
    Note: cert_expired / location_mismatch are planned features for Phase 3.
    """
    print("🎬 Recording: Error Handling Demo...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            locale="zh-TW",
            record_video_dir=VIDEO_DIR,
            record_video_size={"width": 1280, "height": 800},
        )
        page = context.new_page()

        # 1. Empty query error
        page.goto(f"{BASE_URL}/search/?q=")
        page.wait_for_timeout(2000)

        # 2. No results
        page.goto(f"{BASE_URL}/search/?q=不存在的產品")
        page.wait_for_timeout(3000)

        # 3. Health check
        page.goto(f"{BASE_URL}/health/")
        page.wait_for_timeout(2000)

        # 4. Admin login
        page.goto(f"{BASE_URL}/admin/")
        page.wait_for_timeout(2000)

        context.close()
        browser.close()
        print(f"   ✅ Error Handling recording saved")


def record_api_demo():
    """1-min API Demo: health endpoint, search endpoint, admin"""
    print("🎬 Recording: API Demo...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            locale="zh-TW",
            record_video_dir=VIDEO_DIR,
            record_video_size={"width": 1280, "height": 800},
        )
        page = context.new_page()

        # 1. Health check JSON response
        page.goto(f"{BASE_URL}/health/")
        page.wait_for_timeout(2000)

        # 2. Search API in action (via HTMX) - trace code
        page.goto(f"{BASE_URL}/search/?q=TW00123456789")
        page.wait_for_timeout(2000)

        # 3. Search API - crop name with results
        page.goto(f"{BASE_URL}/search/?q=小白菜")
        page.wait_for_timeout(2000)

        # 4. Admin listing FoodOperator records
        page.goto(f"{BASE_URL}/admin/")
        page.wait_for_timeout(1500)

        context.close()
        browser.close()
        print(f"   ✅ API Demo recording saved")


if __name__ == "__main__":
    record_happy_path()
    record_anomaly_demo()
    record_api_demo()
    print(f"\n✅ All recordings saved to {VIDEO_DIR}")
