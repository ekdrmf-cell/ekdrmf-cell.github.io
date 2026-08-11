"""건축기사 실기 합격 전략 가이드(5편) — 릴스용 9:16 손글씨 카드뉴스 + 슬라이드쇼 영상."""
from pathlib import Path

from build_architecture_cards import SLIDES
from handwritten_card_kit import render_deck
from make_slideshow_video import build_slideshow

HERE = Path(__file__).resolve().parent
OUT_DIR = HERE / "cards_architecture_reels"
VIDEO_PATH = HERE / "reels_architecture.mp4"

DURATIONS = [2.0, 2.6, 2.8, 3.2, 2.8]  # SLIDES와 개수 일치

if __name__ == "__main__":
    render_deck(SLIDES, OUT_DIR, size=(1080, 1920))
    build_slideshow(OUT_DIR, VIDEO_PATH, DURATIONS)
    print(VIDEO_PATH)
