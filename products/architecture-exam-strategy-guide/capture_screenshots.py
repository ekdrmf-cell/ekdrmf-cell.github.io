# -*- coding: utf-8 -*-
"""건축기사 실기 합격 전략 가이드용 실제 사이트 화면 캡처."""
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(r"C:\Users\nalla\Desktop\수익화허브\products\architecture-exam-strategy-guide\screenshots")
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

        go(page, "https://www.q-net.or.kr/crf005.do?id=crf00503&gSite=Q&gId=&jmCd=1630&jmInfoDivCcd=B0&gbnn=gbnSubtab2", "01_qnet_exam_info")
        go(page, "https://www.q-net.or.kr/cst006.do?id=cst00602&gSite=Q&gId=&artlSeq=5237527&brdId=Q006&code=1204", "02_qnet_past_exam_archive")
        go(page, "https://www.q-net.or.kr/", "03_qnet_home")
        go(page, "https://www.q-net.or.kr/rcv002.do?id=rcv002_baseInfo&gSite=Q&gId=", "04_qnet_application_notice")

        browser.close()


if __name__ == "__main__":
    run()
