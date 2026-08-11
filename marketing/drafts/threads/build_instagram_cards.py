"""손글씨 편지 카드뉴스 — 인스타그램 마케팅 핵심노하우(4편).

가이드 안의 실제 실측 데이터(릴스 vs 캐러셀 참여율, 안전영역 규격)를
카드 안에 직접 넣어서 사이트 광고처럼 느껴지지 않게 구성.
"""
from pathlib import Path

from handwritten_card_kit import render_deck

OUT_DIR = Path(__file__).resolve().parent / "cards_instagram"

SLIDES = [
    ["릴스 만드느라", "며칠을 갈아넣었는데"],
    ["캐러셀보다", "진짜 나은 게 맞나", "싶어서 찾아봤어"],
    ["릴스는 [[신규유입]]에", "제일 강하고", "캐러셀은 [[저장유도]]에", "강하다더라"],
    ["근데 화면 [[하단 35%]]는", "캡션이랑 프로필에", "가려지는 영역이래", "거기 텍스트 넣으면 안 보여"],
    ["나처럼 모르고", "만들지 말라고", "[[프로필 링크]] 보고 와"],
]

if __name__ == "__main__":
    for p in render_deck(SLIDES, OUT_DIR):
        print(p)
