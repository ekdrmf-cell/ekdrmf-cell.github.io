# -*- coding: utf-8 -*-
"""인스타그램 마케팅 가이드용 실제 사이트 화면 캡처."""
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(r"C:\Users\nalla\Desktop\서비스허브\products\instagram-marketing-guide\screenshots")
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

        go(page, "https://www.facebook.com/business", "01_instagram_business_home")
        go(page, "https://help.instagram.com/502981923235522", "02_professional_account_help")
        go(page, "https://creators.instagram.com/create/broadcast-channels?locale=ko_KR", "03_broadcast_channel")
        go(page, "https://help.instagram.com/5861247717337470", "04_collab_post_help")
        go(page, "https://www.facebook.com/business/help/683065845109838", "05_meta_ads_cpc_help")
        go(page, "https://linktr.ee/", "06_linktree_home")
        go(page, "https://www.ftc.go.kr/www/selectBbsNttView.do?key=12&bordCd=3&nttSn=46562", "07_ftc_press_release", wait="domcontentloaded")
        go(page, "https://www.threads.com/", "08_threads_home")
        go(page, "https://transparency.meta.com/ko-kr/policies/ad-standards/", "09_meta_ad_standards")
        go(page, "https://www.facebook.com/business/help/2022466637835789", "10_shopping_help")
        go(page, "https://transparency.meta.com/ko-kr/policies/community-standards/inauthentic-behavior/", "12_inauthentic_behavior_policy")

        browser.close()


if __name__ == "__main__":
    run()
