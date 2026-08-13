# -*- coding: utf-8 -*-
"""큐텐재팬(Qoo10 Japan) 셀러 판매전략 가이드용 실제 사이트 화면 캡처."""
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(r"C:\Users\nalla\Desktop\서비스허브\products\qoo10-japan-seller-guide\screenshots")
OUT.mkdir(parents=True, exist_ok=True)
VIEWPORT = {"width": 1280, "height": 900}


def shot(page, name):
    path = OUT / f"{name}.png"
    page.screenshot(path=str(path))
    print("saved:", path)


def go(page, url, name, wait="load", timeout=25000, extra_sleep=1.8):
    try:
        page.goto(url, wait_until=wait, timeout=timeout)
        time.sleep(extra_sleep)
        shot(page, name)
    except Exception as e:
        print(f"{name} 실패:", e)


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport=VIEWPORT, locale="ja-JP")
        page.set_default_timeout(25000)

        go(page, "https://www.qoo10.jp/", "01_qoo10jp_home")
        go(page, "https://qsm.qoo10.jp/gmkt.inc.gsm.web/login.aspx", "02_qsm_login")
        go(page, "https://www.qoo10.com/gmkt.inc/cs/guideDefault.aspx", "03_become_seller_guide")
        go(page, "https://www.gov.kr/mw/AA020InfoCappView.do?CappBizCD=11300000006", "04_gov24_tongsinpanmaeeop")
        go(page, "https://nts.go.kr/nts/cm/cntnts/cntntsView.do?mi=40574&cntntsId=239004", "05_nts_haewoejikgu_daehaeng")
        go(page, "https://www.customs.go.kr/kcs/ad/tax/ItemTaxCalculation.do", "06_kcustoms_tax_calc")
        go(page, "https://helpcosmetic.or.kr/pc/material/material01.php", "07_cosmetic_global_regulation")
        go(page, "https://www.mfds.go.kr/", "08_mfds_home")

        browser.close()


if __name__ == "__main__":
    run()
