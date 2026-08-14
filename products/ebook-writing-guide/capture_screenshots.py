# -*- coding: utf-8 -*-
"""전자책 만들기 가이드용 실제 사이트 화면 캡처. playwright 헤드리스로 저장까지 직접 처리."""
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(r"C:\Users\nalla\Desktop\서비스허브\products\ebook-writing-guide\screenshots")
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

        # ---------- 크몽 ----------
        try:
            page.goto("https://kmong.com", wait_until="networkidle", timeout=20000)
            time.sleep(1)
            shot(page, "01_kmong_home")
        except Exception as e:
            print("kmong home 실패:", e)

        try:
            page.goto("https://kmong.com/search?keyword=%EC%A0%84%EC%9E%90%EC%B1%85", wait_until="networkidle", timeout=20000)
            time.sleep(1.2)
            shot(page, "02_kmong_search_ebook")
        except Exception as e:
            print("kmong search 실패:", e)

        # ---------- 부크크 ----------
        try:
            page.goto("https://bookk.co.kr", wait_until="networkidle", timeout=20000)
            time.sleep(1)
            shot(page, "03_bookk_home")
        except Exception as e:
            print("bookk 실패:", e)

        # ---------- 유페이퍼 ----------
        try:
            page.goto("https://upaper.kr", wait_until="networkidle", timeout=20000)
            time.sleep(1)
            shot(page, "04_upaper_home")
        except Exception as e:
            print("upaper 실패:", e)

        # ---------- 탈잉 ----------
        try:
            page.goto("https://taling.me", wait_until="networkidle", timeout=20000)
            time.sleep(1)
            shot(page, "05_taling_home")
        except Exception as e:
            print("taling 실패:", e)

        # ---------- 스마트스토어 판매자센터 ----------
        try:
            page.goto("https://sell.smartstore.naver.com", wait_until="networkidle", timeout=20000)
            time.sleep(1)
            shot(page, "06_smartstore_seller")
        except Exception as e:
            print("smartstore 실패:", e)

        # ---------- 미리캔버스 ----------
        try:
            page.goto("https://www.miricanvas.com", wait_until="networkidle", timeout=20000)
            time.sleep(1.2)
            shot(page, "07_miricanvas_home")
        except Exception as e:
            print("miricanvas 실패:", e)

        # ---------- 눈누(무료 폰트) ----------
        try:
            page.goto("https://noonnu.cc", wait_until="networkidle", timeout=20000)
            time.sleep(1)
            shot(page, "08_noonnu_home")
        except Exception as e:
            print("noonnu 실패:", e)

        # ---------- 네이버 데이터랩 검색어트렌드 ----------
        try:
            page.goto("https://datalab.naver.com/keyword/trendSearch.naver", wait_until="networkidle", timeout=20000)
            time.sleep(1)
            shot(page, "09_datalab_trend")
        except Exception as e:
            print("datalab 실패:", e)

        # ---------- Canva(캔바) ----------
        try:
            page.goto("https://www.canva.com/ko_kr/", wait_until="networkidle", timeout=20000)
            time.sleep(1)
            shot(page, "10_canva_home")
        except Exception as e:
            print("canva 실패:", e)

        browser.close()


if __name__ == "__main__":
    run()
