"""손글씨 편지 카드뉴스 — 큐텐재팬 셀러 판매전략 가이드.

가이드 안의 실제 정보(입점 진입장벽 없음ㆍ관세면제와 소비세는 별개)를
카드 안에 직접 넣어서 사이트 광고처럼 느껴지지 않게 구성.
"""
from pathlib import Path

from handwritten_card_kit import render_deck

OUT_DIR = Path(__file__).resolve().parent / "cards_qoo10"

SLIDES = [
    ["일본 역직구", "자료 찾아보다가", "알았는데"],
    ["[[라쿠텐ㆍ아마존재팬]]", "말고", "큐텐재팬부터", "시작하더라고"],
    ["입점심사도 없고", "재고도 미리", "안 넣어도 되는데"],
    ["관세 면제여도", "[[소비세]]는", "따로 나올 수", "있대"],
    ["통관ㆍ세금 정리해놨어", "[[프로필 링크]]에서", "확인해봐"],
]

if __name__ == "__main__":
    for p in render_deck(SLIDES, OUT_DIR):
        print(p)
