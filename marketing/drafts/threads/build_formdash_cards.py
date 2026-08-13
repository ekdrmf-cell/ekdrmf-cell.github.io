"""손글씨 편지 카드뉴스 — 구글폼 응답 자동집계·조건부 알림 대시보드(서비스).

가이드 안의 실제 기능(위험 키워드 감지 즉시 알림)을 카드 안에 직접
넣어서 사이트 광고처럼 느껴지지 않게 구성.
"""
from pathlib import Path

from handwritten_card_kit import render_deck

OUT_DIR = Path(__file__).resolve().parent / "cards_formdash"

SLIDES = [
    ["구글폼 응답", "쌓일 때마다", "스크롤하면서", "확인하시나요"],
    ["그러다 저점수ㆍ", "[[환불 같은 불만]]", "응답을", "놓친 적 있어서"],
    ["문항별로", "자동 집계되고"],
    ["[[위험 신호]] 있으면", "바로 이메일로", "알려주는 시트", "만들었어요"],
    ["설치는 5분", "[[프로필 링크]]에서", "확인해주세요"],
]

if __name__ == "__main__":
    for p in render_deck(SLIDES, OUT_DIR):
        print(p)
