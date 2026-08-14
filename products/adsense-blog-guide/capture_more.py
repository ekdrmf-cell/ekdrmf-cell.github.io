# -*- coding: utf-8 -*-
"""네이버 애드포스트 URL 재시도."""
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(r"C:\Users\nalla\Desktop\서비스허브\products\adsense-blog-guide\screenshots")
VIEWPORT = {"width": 1280, "height": 900}


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport=VIEWPORT, locale="ko-KR")
        page.set_default_timeout(25000)
        for url in ["https://adpost.naver.com", "https://adpost.naver.com/main.nhn"]:
            try:
                page.goto(url, wait_until="load", timeout=20000)
                time.sleep(1.5)
                page.screenshot(path=str(OUT / "08_naver_adpost.png"))
                print("saved with", url)
                break
            except Exception as e:
                print(url, "실패:", e)
        browser.close()


if __name__ == "__main__":
    run()
