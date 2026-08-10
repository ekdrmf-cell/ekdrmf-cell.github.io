"""손글씨 편지 스타일 카드뉴스 공용 부품 — 종이 질감 배경 + 손글씨 폰트 렌더링.

상품이 바뀔 때마다 이 모듈을 import해서 SLIDES(문장 목록)만 새로 쓰면 된다.
텍스트는 항상 실제 폰트로 정확하게 그린다(AI 이미지 생성으로 글자를 직접 그리면
한글이 깨지기 쉬운 문제를 피하기 위함 — 사용자 프로젝트에서 이미 겪은 문제).

강조하고 싶은 단어는 문장 안에서 [[이렇게]] 겹대괄호로 감싸면 빨간 펜 색+밑줄로
포인트가 들어간다.
"""
import random
import re
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = Path(__file__).resolve().parent
FONT_PATH = HERE / "fonts" / "NanumPenScript-Regular.ttf"

W, H = 1080, 1350
PAPER_COLOR = (252, 249, 241)
INK_COLOR = (26, 34, 64)
ACCENT_COLOR = (162, 48, 38)
LINE_COLOR = (231, 223, 200)
VIGNETTE_COLOR = (185, 176, 150)

HIGHLIGHT_RE = re.compile(r"\[\[(.*?)\]\]")


def _parse_runs(text: str) -> list:
    runs = []
    pos = 0
    for m in HIGHLIGHT_RE.finditer(text):
        if m.start() > pos:
            runs.append((text[pos:m.start()], False))
        runs.append((m.group(1), True))
        pos = m.end()
    if pos < len(text):
        runs.append((text[pos:], False))
    return runs or [("", False)]


def add_stains(paper: Image.Image, seed: int) -> None:
    rng = random.Random(seed)
    draw = ImageDraw.Draw(paper, "RGBA")

    if rng.random() < 0.8:
        corners = [(130, 130), (W - 160, 140), (150, H - 170), (W - 170, H - 150)]
        cx, cy = rng.choice(corners)
        r = rng.randint(65, 95)
        ring_color = (101, 67, 33)
        for i in range(3):
            offset = rng.randint(-6, 6)
            bbox = [cx - r + offset, cy - r + offset, cx + r + offset, cy + r + offset]
            alpha = 34 if i == 0 else 20
            draw.ellipse(bbox, outline=(*ring_color, alpha), width=rng.randint(3, 6))
        draw.ellipse(
            [cx - r + 16, cy - r + 16, cx + r - 16, cy + r - 16],
            outline=(*ring_color, 12), width=4,
        )

    crumb_band = rng.choice([(H - 230, H - 100), (110, 220)])
    for _ in range(rng.randint(6, 11)):
        px = rng.randint(90, W - 90)
        py = rng.randint(*crumb_band)
        size = rng.randint(3, 9)
        shade = rng.choice([(150, 110, 60), (120, 85, 45), (170, 130, 80)])
        alpha = rng.randint(90, 160)
        h = size * rng.uniform(0.6, 1.0)
        draw.ellipse([px, py, px + size, py + h], fill=(*shade, alpha))


def make_paper(seed: int) -> Image.Image:
    rng = np.random.default_rng(seed)
    base = Image.new("RGB", (W, H), PAPER_COLOR)

    noise = rng.integers(-14, 14, (H, W, 1), dtype=np.int16)
    noise = np.repeat(noise, 3, axis=2)
    arr = np.array(base, dtype=np.int16) + noise
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    paper = Image.fromarray(arr, "RGB").filter(ImageFilter.GaussianBlur(0.6))

    draw = ImageDraw.Draw(paper, "RGBA")
    y = 210
    while y < H - 60:
        draw.line([(70, y), (W - 70, y)], fill=(*LINE_COLOR, 130), width=2)
        y += 78

    add_stains(paper, seed)

    vignette = Image.new("L", (W, H), 90)
    vdraw = ImageDraw.Draw(vignette)
    vdraw.ellipse([-260, -260, W + 260, H + 260], fill=255)
    vignette = vignette.filter(ImageFilter.GaussianBlur(160))
    shade = Image.new("RGB", (W, H), VIGNETTE_COLOR)
    paper = Image.composite(paper, shade, vignette)

    return paper


def draw_handwritten_line(canvas: Image.Image, text: str, font: ImageFont.FreeTypeFont,
                           x: int, y: int, align_center_x: int = None) -> int:
    runs = _parse_runs(text)

    tmp = Image.new("RGBA", (W, 260), (0, 0, 0, 0))
    tdraw = ImageDraw.Draw(tmp)
    cursor_x = 10
    top = 10
    for run_text, is_hl in runs:
        color = ACCENT_COLOR if is_hl else INK_COLOR
        ink = (*color, random.randint(215, 255))
        tdraw.text((cursor_x, top), run_text, font=font, fill=ink)
        seg_w = tdraw.textlength(run_text, font=font)
        if is_hl and seg_w > 0:
            base_y = top + font.size * 1.02
            step = 7
            pts = [(cursor_x + i * step, base_y + random.randint(-3, 3)) for i in range(int(seg_w // step) + 2)]
            if len(pts) >= 2:
                tdraw.line(pts, fill=(*color, 200), width=4, joint="curve")
        cursor_x += seg_w

    bbox = tmp.getbbox()
    if not bbox:
        return y
    tmp = tmp.crop(bbox)
    angle = random.uniform(-2.2, 2.2)
    tmp = tmp.rotate(angle, expand=True, resample=Image.BICUBIC)

    px = align_center_x - tmp.width // 2 if align_center_x is not None else x
    py = y + random.randint(-4, 4)
    canvas.paste(tmp, (px, py), tmp)
    return py + tmp.height


def _plain(text: str) -> str:
    return HIGHLIGHT_RE.sub(r"\1", text)


def _fit_font_size(lines: list, start_size: int, max_width: int) -> int:
    probe_img = Image.new("RGBA", (10, 10))
    probe = ImageDraw.Draw(probe_img)
    size = start_size
    while size > 40:
        font = ImageFont.truetype(str(FONT_PATH), size)
        widest = max(probe.textlength(_plain(line), font=font) for line in lines)
        if widest <= max_width:
            break
        size -= 4
    return size


def render_slide(idx: int, total: int, lines: list, out_dir: Path, underline: bool = False) -> Path:
    paper = make_paper(seed=100 + idx)

    line_count = len(lines)
    base_size = 132 if line_count <= 3 else 112
    font_size = _fit_font_size(lines, base_size, max_width=W - 160)
    font = ImageFont.truetype(str(FONT_PATH), font_size)
    small_font = ImageFont.truetype(str(FONT_PATH), 50)

    line_height = int(font_size * 1.55)
    block_height = line_height * line_count
    cursor_y = (H - block_height) // 2 - 40

    for line in lines:
        cursor_y = draw_handwritten_line(paper, line, font, x=0, y=cursor_y, align_center_x=W // 2)

    if underline:
        underline_y = cursor_y + 6
        rng_pts = [(W // 2 - 210 + i * 12, underline_y + random.randint(-4, 4)) for i in range(36)]
        draw = ImageDraw.Draw(paper, "RGBA")
        draw.line(rng_pts, fill=(*INK_COLOR, 200), width=5, joint="curve")

    tag = f"{idx + 1}/{total}"
    draw_handwritten_line(paper, tag, small_font, x=W - 130, y=H - 110)

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"card_{idx + 1}.png"
    paper.convert("RGB").save(out_path, quality=95)
    return out_path


def render_deck(slides: list, out_dir: Path, seed: int = 7) -> list:
    random.seed(seed)
    total = len(slides)
    return [
        render_slide(i, total, lines, out_dir, underline=(i == total - 1))
        for i, lines in enumerate(slides)
    ]
