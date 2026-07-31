# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright

OUT = r"C:\Users\nalla\Desktop\수익화허브\products\gov-subsidy-guide\screenshots\08_gov24_search.png"

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(
        viewport={"width": 1280, "height": 900}, locale="ko-KR",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    )
    page.set_default_timeout(25000)
    try:
        page.goto("https://plus.gov.kr", wait_until="load", timeout=25000)
        page.wait_for_timeout(1500)
        page.screenshot(path=r"C:\Users\nalla\Desktop\수익화허브\products\gov-subsidy-guide\screenshots\_debug_gov24.png")
        print("title:", page.title())
        box = page.get_by_placeholder("안녕하세요. 무엇을 알고 싶으세요?")
        box.click()
        box.fill("보조금24")
        page.keyboard.press("Enter")
        page.wait_for_timeout(2500)
        page.screenshot(path=OUT)
        print("saved gov24 search")
    except Exception as e:
        print("fail:", repr(e))
    browser.close()
