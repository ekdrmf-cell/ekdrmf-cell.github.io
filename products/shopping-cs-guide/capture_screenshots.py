# -*- coding: utf-8 -*-
"""쇼핑몰 CS 고객응대 가이드용 실제 사이트 화면 캡처."""
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(r"C:\Users\nalla\Desktop\수익화허브\products\shopping-cs-guide\screenshots")
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

        go(page, "https://www.law.go.kr/lsInfoP.do?lsId=009318&ancYnChk=0", "01_law_go_kr_ecommerce_act")
        go(page, "https://easylaw.go.kr/CSP/CnpClsMain.laf?popMenu=ov&csmSeq=835&ccfNo=4&cciNo=1&cnpClsNo=2", "02_easylaw_refund")
        go(page, "https://www.kca.go.kr/home/main.do", "03_kca_home")
        go(page, "https://www.kca.go.kr/odr/pg/ma/pgProcssInfo2.do", "04_kca_damage_relief")
        go(page, "https://www.ccn.go.kr/index.ccn", "05_ccn_1372")
        go(page, "https://www.consumer.go.kr/consumer/subIndex/51.do", "06_consumer24")
        go(page, "https://www.ftc.go.kr/www/contents.do?key=153", "07_ftc_ecommerce")
        go(page, "https://sell.smartstore.naver.com/", "08_smartstore_seller_center")
        go(page, "https://marketplace.coupang.com/", "09_coupang_marketplace")
        go(page, "https://www.law.go.kr/%EB%B2%95%EB%A0%B9/%EC%82%B0%EC%97%85%EC%95%88%EC%A0%84%EB%B3%B4%EA%B1%B4%EB%B2%95/%EC%A0%9C41%EC%A1%B0", "10_law_go_kr_emotional_labor")

        browser.close()


if __name__ == "__main__":
    run()
