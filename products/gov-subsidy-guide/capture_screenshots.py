# -*- coding: utf-8 -*-
"""정부지원금 가이드용 실제 사이트 화면 캡처. playwright 헤드리스로 저장까지 직접 처리."""
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(r"C:\Users\nalla\Desktop\서비스허브\products\gov-subsidy-guide\screenshots")
OUT.mkdir(parents=True, exist_ok=True)

VIEWPORT = {"width": 1280, "height": 900}


def shot(page, name, full_page=False):
    path = OUT / f"{name}.png"
    page.screenshot(path=str(path), full_page=full_page)
    print("saved:", path)


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport=VIEWPORT, locale="ko-KR")
        page.set_default_timeout(20000)

        # ---------- 기업마당 ----------
        page.goto("https://www.bizinfo.go.kr", wait_until="networkidle")
        time.sleep(1)
        shot(page, "01_bizinfo_home")

        search_box = page.get_by_placeholder("검색어를 입력해주세요.")
        search_box.click()
        search_box.fill("청년창업")
        shot(page, "02_bizinfo_search_typed")

        search_box.press("Enter")
        page.wait_for_load_state("networkidle")
        time.sleep(1)
        shot(page, "03_bizinfo_search_result")

        # 정책정보 > 지원사업 공고 메뉴 (필터 화면)
        page.goto("https://www.bizinfo.go.kr/sii/siia/selectSIIA200View.do", wait_until="networkidle")
        time.sleep(1)
        shot(page, "04_bizinfo_pblanc_list")

        # ---------- 소상공인24 ----------
        try:
            page.goto("https://www.sbiz24.kr", wait_until="networkidle", timeout=20000)
            time.sleep(1)
            shot(page, "05_sbiz24_home")
        except Exception as e:
            print("sbiz24 실패:", e)

        # ---------- 중소벤처24 ----------
        try:
            page.goto("https://www.smes.go.kr", wait_until="networkidle", timeout=20000)
            time.sleep(1)
            shot(page, "06_smes_home")
        except Exception as e:
            print("smes 실패:", e)

        # ---------- 소진공 ----------
        try:
            page.goto("https://www.semas.or.kr", wait_until="networkidle", timeout=20000)
            time.sleep(1)
            shot(page, "07_semas_home")
        except Exception as e:
            print("semas 실패:", e)

        # ---------- 정부24 보조금24 ----------
        try:
            page.goto("https://www.gov.kr/portal/main/nologin", wait_until="networkidle", timeout=20000)
            time.sleep(1)
            shot(page, "08_gov24_home")
        except Exception as e:
            print("gov24 실패:", e)

        # ---------- 지자체 예시: 수원시 ----------
        try:
            page.goto("https://www.suwon.go.kr", wait_until="networkidle", timeout=20000)
            time.sleep(1)
            shot(page, "09_local_gov_example")
        except Exception as e:
            print("지자체 실패:", e)

        browser.close()


if __name__ == "__main__":
    run()
