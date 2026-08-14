# -*- coding: utf-8 -*-
"""인스타 카드뉴스 실제 이미지(PNG) 생성 스크립트.
전자책 PDF와 같은 브랜드 색/폰트(Pretendard)를 써서 톤을 맞춘다.
상품 하나(슬러그)를 바꿔가며 재사용 — SLIDES 리스트만 고치면 다음 상품도 만들 수 있다."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

FONT_DIR = Path(r"C:\Users\nalla\Desktop\서비스허브\products\_shared\fonts")
OUT_DIR = Path(r"C:\Users\nalla\Desktop\홍보\인스타그램")
OUT_DIR.mkdir(parents=True, exist_ok=True)

W, H = 1080, 1350
ACCENT = (90, 63, 214)       # #5a3fd6
ACCENT_SOFT = (239, 234, 252)  # #efeafc
TEXT_DARK = (31, 35, 51)     # #1f2333
TEXT_DIM = (77, 82, 104)     # #4d5268
WHITE = (255, 255, 255)

f_black = str(FONT_DIR / "Pretendard-Black.ttf")
f_bold = str(FONT_DIR / "Pretendard-Bold.ttf")
f_semibold = str(FONT_DIR / "Pretendard-SemiBold.ttf")
f_medium = str(FONT_DIR / "Pretendard-Medium.ttf")


def draw_lines(draw, lines, font_path, size, color, y, x=80, line_gap=1.35, align="left"):
    font = ImageFont.truetype(font_path, size)
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        lw = bbox[2] - bbox[0]
        lx = (W - lw) // 2 if align == "center" else x
        draw.text((lx, y), line, font=font, fill=color)
        y += int(size * line_gap)
    return y


def measure_block(lines, font_path, size, line_gap=1.35):
    return int(len(lines) * size * line_gap)


def badge_centered(draw, text, y, fg=ACCENT, bg=WHITE, size=30):
    font = ImageFont.truetype(f_semibold, size)
    bbox = draw.textbbox((0, 0), text, font=font)
    pad_x, pad_y = 26, 14
    w = (bbox[2] - bbox[0]) + pad_x * 2
    h = (bbox[3] - bbox[1]) + pad_y * 2
    x = (W - w) // 2
    draw.rounded_rectangle([x, y, x + w, y + h], radius=h // 2, fill=bg)
    draw.text((x + pad_x, y + pad_y - bbox[1]), text, font=font, fill=fg)
    return h


def badge_left(draw, text, x, y, fg=ACCENT, bg=WHITE, size=30):
    font = ImageFont.truetype(f_semibold, size)
    bbox = draw.textbbox((0, 0), text, font=font)
    pad_x, pad_y = 26, 14
    w = (bbox[2] - bbox[0]) + pad_x * 2
    h = (bbox[3] - bbox[1]) + pad_y * 2
    draw.rounded_rectangle([x, y, x + w, y + h], radius=h // 2, fill=bg)
    draw.text((x + pad_x, y + pad_y - bbox[1]), text, font=font, fill=fg)
    return h


def cover_slide(kicker, title_lines, sub_lines):
    img = Image.new("RGB", (W, H), ACCENT)
    d = ImageDraw.Draw(img)
    badge_h = 60
    title_h = measure_block(title_lines, f_black, 76, 1.22)
    sub_h = measure_block(sub_lines, f_medium, 34, 1.5)
    total = badge_h + 60 + title_h + 30 + sub_h
    y = (H - total) // 2
    bh = badge_left(d, kicker, 80, y, fg=ACCENT, bg=WHITE)
    y += bh + 60
    y = draw_lines(d, title_lines, f_black, 76, WHITE, y, line_gap=1.22)
    y += 30
    draw_lines(d, sub_lines, f_medium, 34, (227, 218, 249), y, line_gap=1.5)
    return img


def content_slide(number, title_lines, body_lines):
    img = Image.new("RGB", (W, H), WHITE)
    d = ImageDraw.Draw(img)
    num_h = 90
    title_h = measure_block(title_lines, f_black, 58, 1.28)
    body_h = measure_block(body_lines, f_medium, 36, 1.55)
    total = num_h + 60 + title_h + 40 + body_h
    y = (H - total) // 2
    d.rounded_rectangle([80, y, 200, y + num_h], radius=18, fill=ACCENT_SOFT)
    nf = ImageFont.truetype(f_bold, 46)
    nb = d.textbbox((0, 0), number, font=nf)
    d.text((80 + (120 - (nb[2] - nb[0])) // 2, y + (num_h - (nb[3] - nb[1])) // 2 - nb[1]), number, font=nf, fill=ACCENT)
    y += num_h + 60
    y = draw_lines(d, title_lines, f_black, 58, TEXT_DARK, y, line_gap=1.28)
    y += 40
    draw_lines(d, body_lines, f_medium, 36, TEXT_DIM, y, line_gap=1.55)
    d.rectangle([0, H - 14, W, H], fill=ACCENT)
    return img


def cta_slide(price_line, sub_lines, footer):
    img = Image.new("RGB", (W, H), ACCENT)
    d = ImageDraw.Draw(img)
    price_h = measure_block([price_line], f_black, 92, 1.0)
    sub_h = measure_block(sub_lines, f_semibold, 38, 1.5)
    badge_h = 58
    total = price_h + 40 + sub_h + 60 + badge_h
    y = (H - total) // 2
    y = draw_lines(d, [price_line], f_black, 92, WHITE, y, align="center", line_gap=1.0)
    y += 40
    y = draw_lines(d, sub_lines, f_semibold, 38, (227, 218, 249), y, align="center", line_gap=1.5)
    y += 60
    badge_centered(d, footer, y, fg=ACCENT, bg=WHITE)
    return img


# ============================================================
# 상품: 정부지원금 찾기 가이드 — 1주차 로테이션 상품
# 주의(2026-08-10 확정 규칙): 가격ㆍ페이지수는 카드뉴스에 절대 넣지 않는다.
# 마지막 슬라이드는 가격 대신 "지금 확인하기" 같은 행동유도 문구만 쓴다.
# ============================================================
SLIDES = [
    ("01_cover.png", cover_slide(
        "무료 확인",
        ["정부지원금,", "어디서부터", "찾아야 할지", "막막하신가요?"],
        ["소상공인·1인사업자를 위한", "정부지원금 찾기 가이드"])),
    ("02.png", content_slide(
        "1", ["사이트가", "4곳이나 돼요"],
        ["기업마당, 소상공인24,", "중소벤처24, 지자체 사이트", "전부 따로 봐야 해요"])),
    ("03.png", content_slide(
        "2", ["사이트마다", "성격이 달라요"],
        ["통합검색용 / 정책자금용 /", "지역특화용 — 목적에 맞게", "찾아야 시간이 안 아까워요"])),
    ("04.png", content_slide(
        "3", ["순서와 키워드가", "핵심이에요"],
        ["어디부터 봐야 하는지,", "어떤 키워드로 검색해야", "놓치지 않는지가 진짜 노하우"])),
    ("05.png", content_slide(
        "4", ["가이드에", "담은 것"],
        ["사이트별 상세 사용법", "헷갈리는 용어사전", "실전사례 4개", "사업계획서 작성가이드"])),
    ("06_cta.png", cta_slide(
        "지금 확인하기", ["기업마당부터 지자체까지", "한 번에 정리했어요"], "프로필 링크 확인하기")),
]

for filename, img in SLIDES:
    path = OUT_DIR / filename
    img.save(path, "PNG")
    print("saved:", path)
