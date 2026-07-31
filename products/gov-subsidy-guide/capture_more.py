# -*- coding: utf-8 -*-
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(r"C:\Users\nalla\Desktop\수익화허브\products\gov-subsidy-guide\screenshots")
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
        page.set_default_timeout(25000)

        # 기업마당 공고 상세 페이지 (검색 결과 첫 항목 클릭)
        try:
            page.goto("https://www.bizinfo.go.kr/sii/siia/selectSIIA200View.do", wait_until="networkidle")
            time.sleep(1)
            first_link = page.locator("table tbody tr td a").first
            first_link.click()
            page.wait_for_load_state("networkidle")
            time.sleep(1)
            shot(page, "10_bizinfo_detail")
        except Exception as e:
            print("bizinfo detail 실패:", e)

        # 소상공인24 지원사업 목록
        try:
            page.goto("https://www.sbiz24.kr", wait_until="networkidle", timeout=20000)
            time.sleep(1)
            # 사업 목록/신청 관련 링크 클릭 시도
            candidates = page.locator("a", has_text="소상공인24")
            if candidates.count() > 0:
                candidates.first.click()
                page.wait_for_load_state("networkidle")
                time.sleep(1)
            shot(page, "11_sbiz24_list")
        except Exception as e:
            print("sbiz24 list 실패:", e)

        # 소진공 정책자금 메뉴
        try:
            page.goto("https://www.semas.or.kr", wait_until="networkidle", timeout=20000)
            time.sleep(1)
            candidates = page.locator("a", has_text="정책자금")
            if candidates.count() > 0:
                candidates.first.click()
                page.wait_for_load_state("networkidle")
                time.sleep(1)
            shot(page, "12_semas_policy_fund")
        except Exception as e:
            print("semas policy fund 실패:", e)

        # 수원시 고시공고 게시판
        try:
            page.goto("https://www.suwon.go.kr", wait_until="networkidle", timeout=20000)
            time.sleep(1)
            candidates = page.locator("a", has_text="고시공고")
            if candidates.count() > 0:
                candidates.first.click()
                page.wait_for_load_state("networkidle")
                time.sleep(1)
            shot(page, "13_local_gov_notice")
        except Exception as e:
            print("고시공고 실패:", e)

        browser.close()


if __name__ == "__main__":
    run()
