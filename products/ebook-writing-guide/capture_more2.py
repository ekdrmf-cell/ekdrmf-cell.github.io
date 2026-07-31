# -*- coding: utf-8 -*-
"""탈잉 팝업 닫고 재캡처 + 홈택스 첫 화면 추가 캡처. 캔바는 Cloudflare 봇차단으로 캡처 포기(우회 시도 안 함)."""
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(r"C:\Users\nalla\Desktop\수익화허브\products\ebook-writing-guide\screenshots")
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
            time.sleep(1.5)
            for sel in ["button:has-text('닫기')", "[aria-label='닫기']", ".close", "svg"]:
                try:
                    page.locator(sel).first.click(timeout=1500)
                    break
                except Exception:
                    continue
            time.sleep(1)
            shot(page, "05_taling_home")
        except Exception as e:
            print("taling 실패:", e)

        try:
            page.goto("https://www.hometax.go.kr", wait_until="load", timeout=25000)
            time.sleep(1.5)
            shot(page, "11_hometax_home")
        except Exception as e:
            print("hometax 실패:", e)

        browser.close()


if __name__ == "__main__":
    run()
