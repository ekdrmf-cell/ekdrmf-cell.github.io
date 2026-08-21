"""크로스노틱스 페이지 실제 화면 캡처 — 블로그 글용(6-2 규칙: 7장 고정).
로컬 서버(http://localhost:8768)가 떠있는 상태에서 실행."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent / "screenshots_crossnotics"
OUT.mkdir(exist_ok=True)
BASE = "http://localhost:8768/crossnotics/index.html"


def go(page, name, wait=1.2, clip=None):
    try:
        page.screenshot(path=str(OUT / f"{name}.png"), clip=clip)
        print(name, "완료")
    except Exception as e:
        print(name, "실패:", e)


with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    page.goto(BASE, wait_until="load")
    time.sleep(1)

    # 01: 히어로(제목+설명)
    go(page, "01_hero", clip={"x": 0, "y": 0, "width": 1280, "height": 500})

    # 02: 철학 박스
    el = page.query_selector(".cn-philosophy")
    if el:
        go(page, "02_philosophy", clip=el.bounding_box())

    # 03: 가격 카드 3개 전체 — 가격은 가림(6-3 원칙: 홍보 콘텐츠에 가격 노출 금지,
    # 판매 페이지 자체는 예외지만 이건 그 화면을 "홍보 이미지"로 재사용하는 거라 적용됨)
    page.evaluate("document.querySelectorAll('.cn-tier-price').forEach(el => el.style.visibility = 'hidden')")
    el = page.query_selector(".cn-tiers")
    if el:
        go(page, "03_tiers", clip=el.bounding_box())

    # 04~06: 각 티어 카드 클릭했을 때 폼이 바뀌는 모습(질문개수/출생지 필드)
    # renderTiers()가 매 클릭마다 카드 DOM을 통째로 새로 그리므로, 이전에 잡아둔 핸들이
    # stale해진다 — 매 반복마다 인덱스로 다시 조회해야 함(실제로 여기서 에러 나서 확인함).
    labels = ["04_tier_single_form", "05_tier_dual_form", "06_tier_master_form"]
    for i, label in enumerate(labels):
        cards = page.query_selector_all(".cn-tier-card")
        cards[i].click()
        time.sleep(0.3)
        el = page.query_selector("#cn-form")
        if el:
            go(page, label, clip=el.bounding_box())

    # 07: 전체 페이지 풀샷(축소)
    go(page, "07_full_page")

    browser.close()

print("전체 캡처 완료:", len(list(OUT.glob("*.png"))), "장")
