# -*- coding: utf-8 -*-
"""쿠팡 셀러 창업 가이드용 실제 사이트 화면 캡처."""
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(r"C:\Users\nalla\Desktop\서비스허브\products\coupang-seller-guide\screenshots")
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

        go(page, "https://marketplace.coupang.com/", "01_coupang_marketplace_home")
        go(page, "https://marketplace.coupang.com/rocket-growth", "02_coupang_rocketgrowth")
        go(page, "https://wing.coupang.com/", "03_coupang_wing_login")
        go(page, "https://marketplace.coupang.com/information-center", "04_coupang_info_center")
        go(page, "https://www.customs.go.kr/kcs/ad/tax/BuyTaxCalculation.do", "05_customs_tax_calc")
        go(page, "https://www.ftc.go.kr/", "06_ftc_home")
        go(page, "https://www.hometax.go.kr/", "07_hometax_home")
        go(page, "https://easylaw.go.kr/CSP/CnpClsMain.laf?popMenu=ov&csmSeq=1504&ccfNo=3&cciNo=1&cnpClsNo=2", "08_easylaw_customs")

        browser.close()


if __name__ == "__main__":
    run()
