# -*- coding: utf-8 -*-
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(r"C:\Users\nalla\Desktop\수익화허브\products\gov-subsidy-guide\screenshots")
VIEWPORT = {"width": 1280, "height": 900}

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport=VIEWPORT, locale="ko-KR")
    page.set_default_timeout(20000)

    try:
        page.goto("https://www.bizinfo.go.kr/sii/siia/selectSIIA200View.do", wait_until="networkidle")
        time.sleep(1)
        seoul_btn = page.get_by_text("서울(", exact=False).first
        seoul_btn.click()
        time.sleep(1.5)
        page.screenshot(path=str(OUT / "14_bizinfo_region_filtered.png"))
        print("saved 14")
    except Exception as e:
        print("bizinfo region 실패:", e)

    try:
        page.goto("https://www.semas.or.kr", wait_until="networkidle", timeout=20000)
        time.sleep(1)
        href = page.evaluate(
            """() => {
                const links = Array.from(document.querySelectorAll('a'));
                const found = links.find(a => a.textContent && a.textContent.includes('희망리턴') && a.href);
                return found ? found.href : null;
            }"""
        )
        print("href:", href)
        if href:
            page.goto(href, wait_until="networkidle", timeout=20000)
            time.sleep(1)
        page.screenshot(path=str(OUT / "15_semas_hope_return.png"))
        print("saved 15")
    except Exception as e:
        print("semas hope return 실패:", e)

    browser.close()
