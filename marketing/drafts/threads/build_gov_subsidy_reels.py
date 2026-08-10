"""정부지원금 찾기 가이드 — 릴스용 9:16 손글씨 카드뉴스 + 슬라이드쇼 영상."""
from pathlib import Path

from build_gov_subsidy_cards import SLIDES
from handwritten_card_kit import render_deck
from make_slideshow_video import build_slideshow

HERE = Path(__file__).resolve().parent
OUT_DIR = HERE / "cards_gov_subsidy_reels"
VIDEO_PATH = HERE / "reels_gov_subsidy.mp4"

DURATIONS = [2.2, 2.6, 2.8, 3.4, 2.2, 3.2]  # SLIDES와 개수 일치, 팁·CTA 슬라이드는 더 오래

if __name__ == "__main__":
    render_deck(SLIDES, OUT_DIR, size=(1080, 1920))
    build_slideshow(OUT_DIR, VIDEO_PATH, DURATIONS)
    print(VIDEO_PATH)
