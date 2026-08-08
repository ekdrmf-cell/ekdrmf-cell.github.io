# -*- coding: utf-8 -*-
"""메타 광고 최적화 가이드용 실제 사이트 화면 캡처."""
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(r"C:\Users\nalla\Desktop\수익화허브\products\meta-ads-guide\screenshots")
OUT.mkdir(parents=True, exist_ok=True)
VIEWPORT = {"width": 1280, "height": 900}


def shot(page, name):
    path = OUT / f"{name}.png"
    page.screenshot(path=str(path))
    print("saved:", path)


def go(page, url, name, wait="load", timeout=25000, extra_sleep=1.5):
    try:
        page.goto(url, wait_until=wait, timeout=timeout)
        time.sleep(extra_sleep)
        shot(page, name)
    except Exception as e:
        print(f"{name} 실패:", e)


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport=VIEWPORT, locale="ko-KR")
        page.set_default_timeout(25000)

        go(page, "https://www.facebook.com/business/ads", "01_meta_business_ads_home")
        go(page, "https://www.facebook.com/business/help", "02_meta_business_help_center")
        go(page, "https://about.fb.com/ko/news/2025/01/introducing-ads-in-threads/", "03_meta_threads_ads_announcement")
        go(page, "https://www.facebook.com/business/help/461900317906740", "04_meta_vat_kr_info")
        go(page, "https://www.hometax.go.kr/", "05_hometax_home")
        go(page, "https://transparency.fb.com/ko-kr/", "06_meta_transparency_center")

        browser.close()


if __name__ == "__main__":
    run()
