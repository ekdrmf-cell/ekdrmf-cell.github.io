# -*- coding: utf-8 -*-
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(r"C:\Users\nalla\Desktop\서비스허브\products\gov-subsidy-guide\screenshots")
VIEWPORT = {"width": 1280, "height": 900}


def shot(page, name):
    path = OUT / f"{name}.png"
    page.screenshot(path=str(path))
    print("saved:", path)


def goto_by_text(page, base_url, text, name):
    page.goto(base_url, wait_until="networkidle", timeout=20000)
    time.sleep(1)
    href = page.evaluate(
        """(t) => {
            const links = Array.from(document.querySelectorAll('a'));
            const found = links.find(a => a.textContent && a.textContent.includes(t) && a.href);
            return found ? found.href : null;
        }""",
        text,
    )
    print("found href:", href)
    if href:
        page.goto(href, wait_until="networkidle", timeout=20000)
        time.sleep(1.2)
    shot(page, name)


with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport=VIEWPORT, locale="ko-KR")
    page.set_default_timeout(20000)

    try:
        goto_by_text(page, "https://www.sbiz24.kr", "소상공인24", "11_sbiz24_list")
    except Exception as e:
        print("sbiz24 실패:", e)

    try:
        goto_by_text(page, "https://www.semas.or.kr", "정책자금", "12_semas_policy_fund")
    except Exception as e:
        print("semas 실패:", e)

    try:
        goto_by_text(page, "https://www.suwon.go.kr", "고시공고", "13_local_gov_notice")
    except Exception as e:
        print("suwon 실패:", e)

    browser.close()
