# -*- coding: utf-8 -*-
"""1차에서 실패한 사이트들을 각각 독립된 페이지/컨텍스트로 재시도."""
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(r"C:\Users\nalla\Desktop\서비스허브\products\qoo10-japan-seller-guide\screenshots")
OUT.mkdir(parents=True, exist_ok=True)
VIEWPORT = {"width": 1280, "height": 900}

TARGETS = [
    ("https://www.gov.kr/mw/AA020InfoCappView.do?CappBizCD=11300000006", "04_gov24_tongsinpanmaeeop"),
    ("https://nts.go.kr/nts/cm/cntnts/cntntsView.do?mi=40574&cntntsId=239004", "05_nts_haewoejikgu_daehaeng"),
    ("https://www.customs.go.kr/kcs/ad/tax/ItemTaxCalculation.do", "06_kcustoms_tax_calc"),
    ("https://helpcosmetic.or.kr/pc/material/material01.php", "07_cosmetic_global_regulation"),
    ("https://www.mfds.go.kr/", "08_mfds_home"),
]


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for url, name in TARGETS:
            try:
                context = browser.new_context(viewport=VIEWPORT, locale="ko-KR", ignore_https_errors=True)
                page = context.new_page()
                page.set_default_timeout(20000)
                page.goto(url, wait_until="domcontentloaded", timeout=20000)
                time.sleep(2.2)
                path = OUT / f"{name}.png"
                page.screenshot(path=str(path))
                print("saved:", path)
                context.close()
            except Exception as e:
                print(f"{name} 실패:", e)


if __name__ == "__main__":
    run()
