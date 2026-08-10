"""손글씨 편지 카드뉴스 — 전자책 만들어 팔기 실전 가이드(2편)."""
from pathlib import Path

from handwritten_card_kit import render_deck

OUT_DIR = Path(__file__).resolve().parent / "cards_ebook2"

SLIDES = [
    ["있잖아,", "나 전자책 다 쓰고 나서", "진짜 웃긴 일 있었어"],
    ["어디다 팔아야 할지", "하나도 모르겠는 거야 ㅋㅋ", "크몽? 탈잉? 부크크?", "이름만 봐도 [[머리 아팠어]]"],
    ["근데 하나씩 뜯어보니까", "성격이 [[다 다르더라고]]", "사업자등록 필요한 데도 있고", "안 필요한 데도 있고"],
    ["어디는 등록만 하면 되고", "어디는 진짜 “책”처럼", "[[ISBN]]까지 나오고", "그런 차이가 있더라"],
    ["나처럼 헤매지 말라고", "정리해놨어", "[[프로필 링크]] 보고 와 :)"],
]

if __name__ == "__main__":
    for p in render_deck(SLIDES, OUT_DIR):
        print(p)
