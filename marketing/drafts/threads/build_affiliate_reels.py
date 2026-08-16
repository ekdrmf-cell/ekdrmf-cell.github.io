"""제휴마케팅 실전 가이드 — 릴스용 9:16 손글씨 카드뉴스 + 슬라이드쇼 영상."""
from pathlib import Path

from build_affiliate_cards import SLIDES
from handwritten_card_kit import render_deck
from make_slideshow_video import build_slideshow

HERE = Path(__file__).resolve().parent
OUT_DIR = HERE / "cards_affiliate_reels"
VIDEO_PATH = HERE / "reels_affiliate.mp4"

DURATIONS = [2.2, 2.8, 2.8, 2.8, 2.8]  # SLIDES와 개수 일치

if __name__ == "__main__":
    render_deck(SLIDES, OUT_DIR, size=(1080, 1920))
    build_slideshow(OUT_DIR, VIDEO_PATH, DURATIONS)
    print(VIDEO_PATH)
