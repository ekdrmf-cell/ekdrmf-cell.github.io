# -*- coding: utf-8 -*-
"""1인사업자 부가세 셀프 체크리스트용 실제 사이트 화면 캡처.
hometax.go.kr은 과거 이 프로젝트에서 WAF(봇 차단)로 캡처 실패한 이력이 있음 —
시도는 하되 실패하면 우회 없이 정직하게 텍스트로 대체."""
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(r"C:\Users\nalla\Desktop\수익화허브\products\vat-self-check-guide\screenshots")
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

        go(page, "https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?mi=2273&cntntsId=7694", "01_nts_filing_deadline")
        go(page, "https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7693&mi=2272", "02_nts_vat_basic_info")
        go(page, "https://tasis.nts.go.kr/", "03_tasis_stats_portal")
        go(page, "https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?mi=2461&cntntsId=7787", "04_nts_etax_invoice")
        go(page, "https://www.hometax.go.kr/", "05_hometax_main")  # 과거 이력상 WAF 차단 예상 — 실제로도 흰 화면으로 차단됨
        go(page, "https://law.go.kr/LSW/lsInfoP.do?lsiSeq=90468", "06_law_go_kr_vat_act")
        go(page, "https://www.gov.kr/portal/service/serviceInfo/OA0002", "07_gov24_business_reg")  # 매크로 차단 페이지로 리다이렉트됨(사용 안 함)
        go(page, "https://www.nts.go.kr/", "09_nts_home")
        go(page, "https://www.law.go.kr/lsLawLinkInfo.do?chrClsCd=010202&lsJoLnkSeq=1000574868", "10_law_go_kr_gasan_reduction")
        go(page, "https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?mi=2275&cntntsId=7696", "11_nts_vat_rate_table")

        browser.close()


if __name__ == "__main__":
    run()
