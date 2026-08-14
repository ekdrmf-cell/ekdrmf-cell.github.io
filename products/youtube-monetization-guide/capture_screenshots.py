# -*- coding: utf-8 -*-
"""유튜브 채널 수익화 가이드용 실제 사이트 화면 캡처."""
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(r"C:\Users\nalla\Desktop\서비스허브\products\youtube-monetization-guide\screenshots")
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

        go(page, "https://www.youtube.com/intl/ko_ALL/creators/partner-program/", "01_ypp_official")
        go(page, "https://support.google.com/youtube/answer/72851?hl=ko", "02_ypp_requirements_help")
        go(page, "https://support.google.com/youtube/answer/72902?hl=ko", "03_partner_income_overview")
        go(page, "https://www.youtube.com/intl/ko_ALL/creators/how-things-work/video-monetization/", "04_monetization_ways")
        go(page, "https://support.google.com/youtube/answer/9288567?hl=ko", "05_community_guidelines")
        go(page, "https://support.google.com/youtube/answer/2814000?hl=ko", "06_copyright_strike_help")
        go(page, "https://support.google.com/youtube/answer/6013276?hl=ko", "07_content_id_help")
        go(page, "https://support.google.com/adsense/answer/10735961?hl=ko", "08_us_tax_faq")
        go(page, "https://support.google.com/youtube/answer/3376882?hl=ko", "09_audio_library_help")
        go(page, "https://support.google.com/youtube/answer/13376398?hl=ko", "10_shopping_affiliate_help")

        browser.close()


if __name__ == "__main__":
    run()
