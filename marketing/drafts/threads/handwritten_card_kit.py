"""손글씨 편지 스타일 카드뉴스 공용 부품 — 종이 질감 배경 + 손글씨 폰트 렌더링.

상품이 바뀔 때마다 이 모듈을 import해서 SLIDES(문장 목록)만 새로 쓰면 된다.
텍스트는 항상 실제 폰트로 정확하게 그린다(AI 이미지 생성으로 글자를 직접 그리면
한글이 깨지기 쉬운 문제를 피하기 위함 — 사용자 프로젝트에서 이미 겪은 문제).

강조하고 싶은 단어는 문장 안에서 [[이렇게]] 겹대괄호로 감싸면 보조 잉크 색+
밑줄로 포인트가 들어간다. 카드 안에 강조 표시가 하나도 없으면 마지막 줄의
마지막 단어를 자동으로 강조 처리해서, 매 카드마다 최소 2가지 잉크 색이
나오도록 보장한다(2026-08-11 사용자 요청).

이모지는 그냥 문장 안에 🔥 이렇게 넣으면 된다 — 손글씨 폰트는 이모지
글리프가 없어서, 이모지만 자동으로 감지해서 시스템 컬러 이모지 폰트(윈도우
Segoe UI Emoji)로 따로 그려 붙인다.

종이 질감(색ㆍ줄 유무ㆍ구겨짐 강도)과 잉크 색 조합은 render_deck() 호출마다
무작위로 하나씩 골라서, 상품(덱)이 바뀔 때마다 매번 다른 느낌이 나게 한다.

캔버스 크기는 size=(width, height)로 지정한다 — 캐러셀/스레드용은 기본값
(1080, 1350, 4:5), 릴스용은 (1080, 1920, 9:16)을 쓴다(build_*_reels.py 참고).
"""
import hashlib
import math
import random
import re
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = Path(__file__).resolve().parent
FONT_PATH = HERE / "fonts" / "NanumPenScript-Regular.ttf"
EMOJI_FONT_PATH = Path("C:/Windows/Fonts/seguiemj.ttf")

DEFAULT_SIZE = (1080, 1350)

# 종이 스타일 팔레트 — 덱(상품)마다 하나씩 무작위로 고른다.
PAPER_STYLES = [
    {"name": "cream_notebook", "paper": (252, 249, 241), "line": (231, 223, 200),
     "vignette": (185, 176, 150), "ruled": True, "grid": False},
    {"name": "soft_gray_sketch", "paper": (240, 240, 237), "line": (210, 210, 206),
     "vignette": (170, 170, 168), "ruled": False, "grid": False},
    {"name": "engineer_blue", "paper": (231, 239, 246), "line": (176, 199, 216),
     "vignette": (150, 168, 185), "ruled": True, "grid": False},
    {"name": "kraft_brown", "paper": (224, 203, 172), "line": (188, 158, 118),
     "vignette": (140, 112, 78), "ruled": False, "grid": False},
    {"name": "blush_memo", "paper": (250, 236, 236), "line": (223, 195, 195),
     "vignette": (196, 160, 160), "ruled": True, "grid": False},
    {"name": "mint_index", "paper": (231, 245, 238), "line": (180, 214, 196),
     "vignette": (150, 190, 170), "ruled": False, "grid": True},
]

# 잉크(펜) 색 조합 — 기본색+보조색, 덱마다 하나씩 무작위로 고른다.
INK_PALETTES = [
    ((26, 34, 64), (162, 48, 38)),      # 남색 + 빨강
    ((30, 60, 50), (190, 110, 20)),     # 진초록 + 주황
    ((45, 30, 70), (20, 120, 130)),     # 보라 + 청록
    ((60, 40, 20), (150, 30, 90)),      # 갈색 + 자홍
    ((20, 40, 80), (200, 140, 20)),     # 짙은파랑 + 겨자
    ((50, 50, 50), (170, 40, 100)),     # 차콜 + 진분홍
]

HIGHLIGHT_RE = re.compile(r"\[\[(.*?)\]\]")
EMOJI_RE = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF"
    "\U00002190-\U000021FF\U00002B00-\U00002BFF\U0000FE0F\U0000200D]+"
)


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


def _split_emoji(text: str) -> list:
    """(chunk, is_emoji) 튜플 리스트로 쪼갠다."""
    parts = []
    pos = 0
    for m in EMOJI_RE.finditer(text):
        if m.start() > pos:
            parts.append((text[pos:m.start()], False))
        parts.append((m.group(0), True))
        pos = m.end()
    if pos < len(text):
        parts.append((text[pos:], False))
    return parts or [("", False)]


def add_stains(paper: Image.Image, seed: int, size: tuple, style: dict) -> None:
    w, h = size
    rng = random.Random(seed)
    draw = ImageDraw.Draw(paper, "RGBA")
    ring_color = tuple(max(0, c - 40) for c in style["line"])

    if rng.random() < 0.7:
        corners = [(130, 130), (w - 160, 140), (150, h - 170), (w - 170, h - 150)]
        cx, cy = rng.choice(corners)
        r = rng.randint(65, 95)
        for i in range(3):
            offset = rng.randint(-6, 6)
            bbox = [cx - r + offset, cy - r + offset, cx + r + offset, cy + r + offset]
            alpha = 34 if i == 0 else 20
            draw.ellipse(bbox, outline=(*ring_color, alpha), width=rng.randint(3, 6))
        draw.ellipse(
            [cx - r + 16, cy - r + 16, cx + r - 16, cy + r - 16],
            outline=(*ring_color, 12), width=4,
        )

    crumb_band = rng.choice([(h - 230, h - 100), (110, 220)])
    for _ in range(rng.randint(5, 10)):
        px = rng.randint(90, w - 90)
        py = rng.randint(*crumb_band)
        csize = rng.randint(3, 9)
        shade = rng.choice([ring_color, tuple(max(0, c - 20) for c in ring_color)])
        alpha = rng.randint(80, 150)
        ch = csize * rng.uniform(0.6, 1.0)
        draw.ellipse([px, py, px + csize, py + ch], fill=(*shade, alpha))


def add_crumple(paper: Image.Image, seed: int, size: tuple, intensity: float) -> Image.Image:
    """구겨진 종이 느낌 — 저해상도 노이즈를 부드럽게 확대해서 명암 얼룩을 만들고,
    거기에 접힌 자국(밝은 선+어두운 선 짝) 몇 개를 더한다. intensity(0~1)가
    클수록 더 많이 구겨진 것처럼 보인다."""
    w, h = size
    rng = np.random.default_rng(seed + 999)
    small = rng.uniform(-1, 1, (10, 8)).astype(np.float32)
    small_img = Image.fromarray(((small + 1) * 127.5).astype(np.uint8), "L").resize(
        (w, h), Image.BICUBIC
    )
    norm = (np.array(small_img, dtype=np.float32) - 127.5) / 127.5  # -1..1
    shade = norm * (26 * intensity)

    arr = np.array(paper, dtype=np.float32)
    arr += shade[:, :, None]
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    paper = Image.fromarray(arr, "RGB")

    py_rng = random.Random(seed + 555)
    draw = ImageDraw.Draw(paper, "RGBA")
    crease_count = int(2 + intensity * 4)
    for _ in range(crease_count):
        x0, y0 = py_rng.randint(0, w), py_rng.randint(0, h)
        angle = py_rng.uniform(0, 3.14159)
        length = py_rng.randint(int(h * 0.3), int(h * 0.8))
        x1 = x0 + length * math.cos(angle)
        y1 = y0 + length * math.sin(angle)
        pts = [(x0 + py_rng.randint(-3, 3), y0 + py_rng.randint(-3, 3)) for _ in range(1)]
        pts += [(x0 + (x1 - x0) * t / 6 + py_rng.randint(-8, 8), y0 + (y1 - y0) * t / 6 + py_rng.randint(-8, 8))
                for t in range(1, 7)]
        dark_alpha = int(18 + intensity * 22)
        light_alpha = int(14 + intensity * 18)
        draw.line(pts, fill=(0, 0, 0, dark_alpha), width=3, joint="curve")
        pts_light = [(px + 2, py - 2) for px, py in pts]
        draw.line(pts_light, fill=(255, 255, 255, light_alpha), width=2, joint="curve")

    return paper


def make_paper(seed: int, size: tuple = DEFAULT_SIZE, style: dict = None, crumple: float = 0.4) -> Image.Image:
    style = style or PAPER_STYLES[0]
    w, h = size
    rng = np.random.default_rng(seed)
    base = Image.new("RGB", (w, h), style["paper"])

    noise = rng.integers(-14, 14, (h, w, 1), dtype=np.int16)
    noise = np.repeat(noise, 3, axis=2)
    arr = np.array(base, dtype=np.int16) + noise
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    paper = Image.fromarray(arr, "RGB").filter(ImageFilter.GaussianBlur(0.6))

    draw = ImageDraw.Draw(paper, "RGBA")
    if style["ruled"]:
        y = 210
        while y < h - 60:
            draw.line([(70, y), (w - 70, y)], fill=(*style["line"], 130), width=2)
            y += 78
    elif style["grid"]:
        step = 74
        x = 70
        while x < w - 60:
            draw.line([(x, 60), (x, h - 60)], fill=(*style["line"], 70), width=1)
            x += step
        y = 60
        while y < h - 60:
            draw.line([(70, y), (w - 70, y)], fill=(*style["line"], 70), width=1)
            y += step

    add_stains(paper, seed, size, style)

    vignette = Image.new("L", (w, h), 90)
    vdraw = ImageDraw.Draw(vignette)
    vdraw.ellipse([-260, -260, w + 260, h + 260], fill=255)
    vignette = vignette.filter(ImageFilter.GaussianBlur(160))
    shade = Image.new("RGB", (w, h), style["vignette"])
    paper = Image.composite(paper, shade, vignette)

    paper = add_crumple(paper, seed, size, crumple)

    return paper


def _draw_emoji(tmp: Image.Image, emoji_text: str, x: int, y: int, size: int) -> int:
    """이모지를 컬러 폰트로 그려서 tmp에 붙이고, 그린 폭을 반환한다."""
    if not EMOJI_FONT_PATH.exists():
        return 0
    total_w = 0
    for ch in emoji_text:
        try:
            efont = ImageFont.truetype(str(EMOJI_FONT_PATH), size)
            tile = Image.new("RGBA", (size + 20, size + 20), (0, 0, 0, 0))
            tdraw = ImageDraw.Draw(tile)
            tdraw.text((0, 0), ch, font=efont, embedded_color=True)
            bbox = tile.getbbox()
            if not bbox:
                continue
            tile = tile.crop(bbox)
            paste_y = int(y + size * 0.08)
            tmp.paste(tile, (int(x + total_w), paste_y), tile)
            total_w += tile.width + 4
        except Exception:
            continue
    return total_w


def draw_handwritten_line(canvas: Image.Image, text: str, font: ImageFont.FreeTypeFont,
                           x: int, y: int, align_center_x: int = None, canvas_width: int = DEFAULT_SIZE[0],
                           ink_primary: tuple = (26, 34, 64), ink_secondary: tuple = (162, 48, 38)) -> int:
    runs = _parse_runs(text)

    tmp = Image.new("RGBA", (canvas_width, 260), (0, 0, 0, 0))
    tdraw = ImageDraw.Draw(tmp)
    cursor_x = 10
    top = 10
    for run_text, is_hl in runs:
        color = ink_secondary if is_hl else ink_primary
        for chunk, is_emoji in _split_emoji(run_text):
            if not chunk:
                continue
            if is_emoji:
                cursor_x += _draw_emoji(tmp, chunk, cursor_x, top, int(font.size * 0.9))
                continue
            ink = (*color, random.randint(215, 255))
            tdraw.text((cursor_x, top), chunk, font=font, fill=ink)
            seg_w = tdraw.textlength(chunk, font=font)
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


def _measure_line_width(line: str, font: ImageFont.FreeTypeFont, probe: ImageDraw.ImageDraw) -> float:
    """draw_handwritten_line과 동일한 규칙으로 폭을 잰다 — 이모지는 손글씨
    폰트로 재면 폭이 거의 0으로 나와서(글리프가 없음) 실제보다 훨씬 좁게
    추정되는 문제가 있어, 이모지 폰트 기준 폭(font.size*0.9 + 4)을 따로 더한다."""
    total = 0.0
    for run_text, _is_hl in _parse_runs(line):
        for chunk, is_emoji in _split_emoji(run_text):
            if is_emoji:
                total += (font.size * 0.9 + 4) * len(chunk)
            else:
                total += probe.textlength(chunk, font=font)
    return total


def _fit_font_size(lines: list, start_size: int, max_width: int) -> int:
    probe_img = Image.new("RGBA", (10, 10))
    probe = ImageDraw.Draw(probe_img)
    size = start_size
    while size > 40:
        font = ImageFont.truetype(str(FONT_PATH), size)
        widest = max(_measure_line_width(line, font, probe) for line in lines)
        if widest <= max_width:
            break
        size -= 4
    return size


def _ensure_two_colors(lines: list) -> list:
    """카드 안에 [[강조]]가 하나도 없으면, 마지막 줄의 마지막 단어를 자동으로
    강조 처리해서 최소 2가지 잉크 색이 나오게 한다."""
    if any(HIGHLIGHT_RE.search(line) for line in lines):
        return lines
    lines = list(lines)
    last = lines[-1]
    words = last.rsplit(" ", 1)
    if len(words) == 2:
        lines[-1] = f"{words[0]} [[{words[1]}]]"
    else:
        lines[-1] = f"[[{last}]]"
    return lines


def render_slide(idx: int, total: int, lines: list, out_dir: Path, underline: bool = False,
                  size: tuple = DEFAULT_SIZE, style: dict = None, ink_palette: tuple = None,
                  crumple: float = 0.4) -> Path:
    style = style or PAPER_STYLES[0]
    ink_primary, ink_secondary = ink_palette or INK_PALETTES[0]
    lines = _ensure_two_colors(lines)

    w, h = size
    paper = make_paper(seed=100 + idx, size=size, style=style, crumple=crumple)

    line_count = len(lines)
    base_size = 148 if line_count <= 3 else 126
    font_size = _fit_font_size(lines, base_size, max_width=w - 160)
    font = ImageFont.truetype(str(FONT_PATH), font_size)
    small_font = ImageFont.truetype(str(FONT_PATH), 50)

    line_height = int(font_size * 1.55)
    block_height = line_height * line_count
    cursor_y = (h - block_height) // 2 - 40

    for line in lines:
        cursor_y = draw_handwritten_line(
            paper, line, font, x=0, y=cursor_y, align_center_x=w // 2, canvas_width=w,
            ink_primary=ink_primary, ink_secondary=ink_secondary,
        )

    if underline:
        underline_y = cursor_y + 6
        rng_pts = [(w // 2 - 210 + i * 12, underline_y + random.randint(-4, 4)) for i in range(36)]
        draw = ImageDraw.Draw(paper, "RGBA")
        draw.line(rng_pts, fill=(*ink_primary, 200), width=5, joint="curve")

    tag = f"{idx + 1}/{total}"
    draw_handwritten_line(paper, tag, small_font, x=w - 130, y=h - 110, canvas_width=w,
                           ink_primary=ink_primary, ink_secondary=ink_secondary)

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"card_{idx + 1}.png"
    paper.convert("RGB").save(out_path, quality=95)
    return out_path


def _stable_seed(text: str) -> int:
    return int(hashlib.md5(text.encode("utf-8")).hexdigest(), 16) % 1_000_000


def render_deck(slides: list, out_dir: Path, seed: int = 7, size: tuple = DEFAULT_SIZE) -> list:
    random.seed(seed)
    # 종이 스타일ㆍ잉크 팔레트ㆍ구겨짐 정도는 out_dir 이름에서 안정적으로 파생시킨
    # 시드로 고른다 — 상품(폴더)마다 항상 다른 조합이 나오면서도, 같은 상품을
    # 다시 생성하면 매번 같은 결과가 나오게(재현 가능하게) 하기 위함.
    deck_rng = random.Random(_stable_seed(str(out_dir.name)))
    style = deck_rng.choice(PAPER_STYLES)
    ink_palette = deck_rng.choice(INK_PALETTES)
    crumple = deck_rng.uniform(0.15, 0.9)

    total = len(slides)
    return [
        render_slide(i, total, lines, out_dir, underline=(i == total - 1), size=size,
                     style=style, ink_palette=ink_palette, crumple=crumple)
        for i, lines in enumerate(slides)
    ]
