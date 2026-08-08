# -*- coding: utf-8 -*-
"""챗GPT 실무 활용 가이드용 실제 사이트 화면 캡처."""
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(r"C:\Users\nalla\Desktop\수익화허브\products\chatgpt-usage-guide\screenshots")
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

        go(page, "https://openai.com/chatgpt/pricing/", "01_openai_pricing")
        go(page, "https://help.openai.com/en/", "02_openai_help_center")
        go(page, "https://openai.com/index/introducing-gpts/", "03_openai_gpts_intro")
        go(page, "https://openai.com/policies/row-privacy-policy/", "04_openai_privacy_policy")
        go(page, "https://openai.com/chatgpt/overview/", "05_chatgpt_overview")

        browser.close()


if __name__ == "__main__":
    run()
