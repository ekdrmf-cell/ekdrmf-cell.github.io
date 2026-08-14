# -*- coding: utf-8 -*-
"""제휴마케팅 실전 가이드용 실제 사이트 화면 캡처."""
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(r"C:\Users\nalla\Desktop\서비스허브\products\affiliate-marketing-guide\screenshots")
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

        go(page, "https://partners.coupang.com/", "01_coupang_partners_home")
        go(page, "https://www.tenping.kr/", "02_tenping_home")
        go(page, "https://adpick.co.kr/", "03_adpick_home")
        go(page, "https://portals.aliexpress.com/affiportals/web/portal.htm", "04_aliexpress_affiliate")
        go(page, "https://blog.aladin.co.kr/ttb/", "05_aladin_ttb")
        go(page, "https://www.ftc.go.kr/", "06_ftc_home")
        go(page, "https://www.hometax.go.kr/", "07_hometax_home")
        go(page, "https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?mi=2227&cntntsId=7667", "08_nts_tax_rate")

        browser.close()


if __name__ == "__main__":
    run()
