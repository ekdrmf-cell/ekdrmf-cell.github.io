# -*- coding: utf-8 -*-
"""애드센스 블로그 가이드용 실제 사이트 화면 캡처."""
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(r"C:\Users\nalla\Desktop\수익화허브\products\adsense-blog-guide\screenshots")
OUT.mkdir(parents=True, exist_ok=True)
VIEWPORT = {"width": 1280, "height": 900}


def shot(page, name):
    path = OUT / f"{name}.png"
    page.screenshot(path=str(path))
    print("saved:", path)


def go(page, url, name, wait="load", timeout=25000, extra_sleep=1.2):
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

        go(page, "https://www.google.com/adsense/start/", "01_adsense_home")
        go(page, "https://www.tistory.com", "02_tistory_home")
        go(page, "https://wordpress.com/ko/", "03_wordpress_home")
        go(page, "https://www.blogger.com", "04_blogger_home")
        go(page, "https://trends.google.co.kr/trends/", "05_google_trends")
        go(page, "https://adfit.kakao.com", "06_kakao_adfit")
        go(page, "https://search.google.com/search-console/about", "07_search_console_about")
        go(page, "https://section.blog.naver.com/adpost.naver", "08_naver_adpost", wait="domcontentloaded")

        browser.close()


if __name__ == "__main__":
    run()
