# -*- coding: utf-8 -*-
"""1차 캡처에서 timeout난 사이트(탈잉ㆍ캔바) 재시도 — networkidle 대신 load 이벤트로 대기."""
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(r"C:\Users\nalla\Desktop\서비스허브\products\ebook-writing-guide\screenshots")
VIEWPORT = {"width": 1280, "height": 900}


def shot(page, name):
    path = OUT / f"{name}.png"
    page.screenshot(path=str(path))
    print("saved:", path)


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport=VIEWPORT, locale="ko-KR")
        page.set_default_timeout(25000)

        try:
            page.goto("https://taling.me", wait_until="load", timeout=25000)
            time.sleep(2)
            shot(page, "05_taling_home")
        except Exception as e:
            print("taling 실패:", e)

        try:
            page.goto("https://www.canva.com/ko_kr/", wait_until="domcontentloaded", timeout=25000)
            time.sleep(2.5)
            shot(page, "10_canva_home")
        except Exception as e:
            print("canva 실패:", e)

        browser.close()


if __name__ == "__main__":
    run()
