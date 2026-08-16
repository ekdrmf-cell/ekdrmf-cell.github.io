"""손글씨 편지 카드뉴스 — 제휴마케팅 실전 가이드.

가이드 안의 실제 정보(카테고리별 수수료 최대 3배 차이ㆍ24시간 쿠키 정책ㆍ
자기클릭 100% 정지)를 카드 안에 직접 넣어서 사이트 광고처럼 느껴지지 않게 구성.
"""
from pathlib import Path

from handwritten_card_kit import render_deck

OUT_DIR = Path(__file__).resolve().parent / "cards_affiliate"

SLIDES = [
    ["블로그에 링크만", "붙이면 돈 번다길래", "자세히 찾아봤는데"],
    ["[[쿠팡파트너스]]는", "카테고리마다", "수수료가 최대", "3배 차이래"],
    ["내 링크 클릭하고", "24시간 안에", "딴 거 사도", "수수료가 붙는대"],
    ["근데 [[자기 클릭]]으로", "내가 직접 사면", "그 자리에서", "계정 정지래"],
    ["수수료율ㆍ정지사유ㆍ", "세금까지 정리했어", "[[프로필 링크]]에서", "확인해봐"],
]

if __name__ == "__main__":
    for p in render_deck(SLIDES, OUT_DIR):
        print(p)
