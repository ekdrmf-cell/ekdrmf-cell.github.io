"""손글씨 편지 카드뉴스 — 건축기사 실기 합격 전략 가이드(5편).

가이드 안의 실제 규정(공학용계산기 허용 기종ㆍ직접 초기화 의무)을
카드 안에 직접 넣어서 사이트 광고처럼 느껴지지 않게 구성.
"""
from pathlib import Path

from handwritten_card_kit import render_deck

OUT_DIR = Path(__file__).resolve().parent / "cards_architecture"

SLIDES = [
    ["건축기사 실기", "준비하다가 알았는데"],
    ["계산기 아무거나", "가져가면", "시험장에서 못 써"],
    ["[[카시오ㆍ샤프ㆍ캐논]]", "같은 허용 기종만", "되는데"],
    ["그것도 시험 전에", "본인이 직접", "[[초기화(리셋)]]", "해가야 된대"],
    ["나처럼 몰랐다가", "낭패보지 말라고", "[[프로필 링크]]에", "정리해놨어"],
]

if __name__ == "__main__":
    for p in render_deck(SLIDES, OUT_DIR):
        print(p)
