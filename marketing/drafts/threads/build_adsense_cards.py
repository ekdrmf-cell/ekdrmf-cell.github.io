"""손글씨 편지 카드뉴스 — 구글 애드센스 블로그 시작 가이드(3편).

가이드 안의 실제 정보(주제별 CPC 차이, 금융ㆍ법률이 가장 높고 연예ㆍ엔터가
가장 낮다는 것)를 카드 안에 직접 넣어서 사이트 광고처럼 느껴지지 않게
구성함 — 1편 재작업 때 확정한 원칙(MARKETING_HANDOFF.md 0-0-1 참고)을 그대로 적용.
"""
from pathlib import Path

from handwritten_card_kit import render_deck

OUT_DIR = Path(__file__).resolve().parent / "cards_adsense"

SLIDES = [
    ["블로그 시작하려는데", "이것부터 알아야 돼"],
    ["나도 처음엔", "그냥 좋아하는 주제로", "쓰면 되는 줄 알았어"],
    ["근데 알고 보니", "주제마다 광고 단가가", "[[수십 배씩]] 차이나더라"],
    ["[[금융]]이랑 [[법률]]이", "제일 높고", "연예ㆍ엔터가", "제일 낮대"],
    ["근데 무조건", "돈 되는 주제로", "가라는 건 아니고", "내가 아는 것부터가 먼저야"],
    ["이런 것들", "정리해놨으니까", "[[프로필 링크]] 보고 와"],
]

if __name__ == "__main__":
    for p in render_deck(SLIDES, OUT_DIR):
        print(p)
