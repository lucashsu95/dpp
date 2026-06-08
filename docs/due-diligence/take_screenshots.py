"""
Take screenshots of the DPP Food Safety app for investor demo materials.
"""
import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
sys.path.insert(0, "/home/user/dpp")

from playwright.sync_api import sync_playwright
import django

django.setup()

BASE_URL = "http://localhost:8765"
OUTPUT_DIR = "/home/user/dpp/docs/due-diligence/screenshots"


def take_screenshots():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            locale="zh-TW",
        )
        page = context.new_page()

        # 1. Home page with product cards
        print("📸 1/12: Home page...")
        page.goto(BASE_URL)
        page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(OUTPUT_DIR, "01-home-page.png"), full_page=True)

        # 2. Search with trace code — happy path
        print("📸 2/12: Search with trace code...")
        page.goto(f"{BASE_URL}/search/?q=TW00123456789")
        page.wait_for_timeout(2000)
        page.screenshot(path=os.path.join(OUTPUT_DIR, "02-search-trace-code.png"), full_page=True)

        # 3. Search with crop name
        print("📸 3/12: Search with crop name...")
        page.goto(f"{BASE_URL}/search/?q=青江菜")
        page.wait_for_timeout(2000)
        page.screenshot(path=os.path.join(OUTPUT_DIR, "03-search-crop-name.png"), full_page=True)

        # 4. Search with operator name
        print("📸 4/12: Search with operator name...")
        # First ensure there's some data
        page.goto(f"{BASE_URL}")

        # 5. Health check endpoint
        print("📸 5/12: Health check...")
        resp = page.goto(f"{BASE_URL}/health/")
        content = page.content()
        page.screenshot(path=os.path.join(OUTPUT_DIR, "05-health-check.png"), full_page=True)
        print(f"    Health response: {resp}")

        # 6. Mobile viewport
        print("📸 6/12: Mobile view...")
        mobile_context = browser.new_context(
            viewport={"width": 390, "height": 844},
            locale="zh-TW",
        )
        mobile_page = mobile_context.new_page()
        mobile_page.goto(BASE_URL)
        mobile_page.wait_for_timeout(1500)
        mobile_page.screenshot(path=os.path.join(OUTPUT_DIR, "06-mobile-home.png"), full_page=True)
        mobile_context.close()

        # 7. Admin login page
        print("📸 7/12: Admin login...")
        page.goto(f"{BASE_URL}/admin/")
        page.wait_for_timeout(1000)
        page.screenshot(path=os.path.join(OUTPUT_DIR, "07-admin-login.png"), full_page=True)

        # 8. Search result with raw data expanded (simulate via query param)
        print("📸 8/12: Expanded result details...")
        page.goto(f"{BASE_URL}/search/?q=TW00123456789")
        page.wait_for_timeout(2000)
        page.screenshot(path=os.path.join(OUTPUT_DIR, "08-search-result-expanded.png"), full_page=True)

        # 9. Error state (empty query)
        print("📸 9/12: Empty query error...")
        page.goto(f"{BASE_URL}/search/?q=")
        page.wait_for_timeout(1000)
        page.screenshot(path=os.path.join(OUTPUT_DIR, "09-empty-query-error.png"), full_page=True)

        # 10. No results found
        print("📸 10/12: No results...")
        page.goto(f"{BASE_URL}/search/?q=不存在的產品名稱")
        page.wait_for_timeout(2000)
        page.screenshot(path=os.path.join(OUTPUT_DIR, "10-no-results.png"), full_page=True)

        # 11. Skeleton loading
        print("📸 11/12: Skeleton loading...")
        page.goto(BASE_URL)
        page.wait_for_timeout(500)
        page.screenshot(path=os.path.join(OUTPUT_DIR, "11-skeleton-loading.png"), full_page=True)

        # 12. product cards section
        print("📸 12/12: Product cards...")
        page.goto(BASE_URL)
        page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(OUTPUT_DIR, "12-product-cards.png"), full_page=True)

        browser.close()
        print(f"\n✅ All screenshots saved to {OUTPUT_DIR}")


if __name__ == "__main__":
    take_screenshots()
