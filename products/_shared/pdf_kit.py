# -*- coding: utf-8 -*-
"""전자책 PDF 공용 빌드 키트 (전자책 3번부터 사용).

이전 두 권(gov-subsidy-guide, ebook-writing-guide)에서 검증된 원칙을 계승한다:
- 강제 PageBreak 금지(표지 뒤 1번만 예외) — 콘텐츠 흐름만으로 자연스럽게 페이지가 나뉘게 함
- 가운뎃점은 "·" 대신 "ㆍ"(U+318D) 사용 — HYGothic 계열 CID 폰트 가운뎃점 미지원 버그 회피용이었으나,
  Pretendard(TTF)는 진짜 가운뎃점 "·"도 정상 렌더링된다. 다만 통일성을 위해 계속 "ㆍ"를 권장.
- 빈칸 워크시트ㆍ자가진단 금지 원칙은 유지하되, "페이지 채우기용 필러"가 아닌 독립된 실행계획
  챕터 안에서의 체크리스트는 허용(2026-08-01 참고 전자책 비교분석 후 재해석).
- 유료 판매용 전자책은 AI 생성 사진ㆍ워터마크를 넣지 않는다(무료 배포용에는 필요, 2026-08-01 결정).

2026-08-01 참고 전자책(쇼치, 69p) 비교분석 후 신설된 디자인 시스템:
- Pretendard TTF 임베딩(Regular/Medium/SemiBold/Bold/ExtraBold/Black) — 제목에 진짜 굵은
  대비를 줄 수 있음. reportlab CID 표준폰트(HYGothic-Medium)는 굵기가 하나뿐이라 밋밋했음.
- 박스를 용도별로 색 구분: TIP(파랑) / WARN(주의, 주황) / NEXT(다음 챕터 예고, 로즈) /
  SUMMARY(챕터 요약, 남색 배경). 전부 보라 하나로 통일했던 이전 방식보다 스캔하기 쉬움.
- 챕터 끝에는 반드시 summary_box + next_chapter_box를 넣어 "그냥 끊기지 않게" 할 것.
- 이모지는 BMP 범위(★☆⚠▶✓■ 등)만 안전하게 렌더링됨 — 💡🎯 같은 서플리멘터리 플레인
  이모지는 Pretendard에 글리프가 없어 틀린 기호로 깨진다. 절대 쓰지 말 것.
"""

from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    HRFlowable, Image, KeepTogether
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image as PILImage

SHARED_DIR = Path(__file__).resolve().parent
FONT_DIR = SHARED_DIR / "fonts"

REG, MED, SB, BOLD, XB, BLACK = (
    "Pretendard", "Pretendard-Medium", "Pretendard-SemiBold",
    "Pretendard-Bold", "Pretendard-ExtraBold", "Pretendard-Black",
)

_FONTS_REGISTERED = False


def register_fonts():
    global _FONTS_REGISTERED
    if _FONTS_REGISTERED:
        return
    pdfmetrics.registerFont(TTFont(REG, str(FONT_DIR / "Pretendard-Regular.ttf")))
    pdfmetrics.registerFont(TTFont(MED, str(FONT_DIR / "Pretendard-Medium.ttf")))
    pdfmetrics.registerFont(TTFont(SB, str(FONT_DIR / "Pretendard-SemiBold.ttf")))
    pdfmetrics.registerFont(TTFont(BOLD, str(FONT_DIR / "Pretendard-Bold.ttf")))
    pdfmetrics.registerFont(TTFont(XB, str(FONT_DIR / "Pretendard-ExtraBold.ttf")))
    pdfmetrics.registerFont(TTFont(BLACK, str(FONT_DIR / "Pretendard-Black.ttf")))
    _FONTS_REGISTERED = True


# ---------- 색 ----------
ACCENT = colors.HexColor("#5a3fd6")
ACCENT_DEEP = colors.HexColor("#3d2a99")
ACCENT_SOFT = colors.HexColor("#efeafc")
TEXT_DARK = colors.HexColor("#1f2333")
TEXT_DIM = colors.HexColor("#4d5268")
BORDER = colors.HexColor("#d9d5f0")

TIP_BG, TIP_BAR = colors.HexColor("#eaf2ff"), colors.HexColor("#2a63c9")
WARN_BG, WARN_BAR = colors.HexColor("#fff6df"), colors.HexColor("#c2790a")
NEXT_BG, NEXT_BAR = colors.HexColor("#fdeef3"), colors.HexColor("#c23572")
SUMMARY_BG = colors.HexColor("#1f2338")

STEP_SHADES = [ACCENT, colors.HexColor("#7457e0"), colors.HexColor("#8d6fea"),
               colors.HexColor("#a687f2"), colors.HexColor("#bfa0f7"), colors.HexColor("#d3bffa")]


class PDFKit:
    def __init__(self, out_path, title, author="수익화허브", shot_dir=None):
        register_fonts()
        self.out_path = str(out_path)
        self.shot_dir = Path(shot_dir) if shot_dir else None
        self.doc = SimpleDocTemplate(
            self.out_path, pagesize=A4,
            topMargin=24 * mm, bottomMargin=24 * mm,
            leftMargin=22 * mm, rightMargin=22 * mm,
            title=title, author=author,
        )
        self.story = []
        self._chapter_counter = 0
        self.styles = {
            "cover_kicker": ParagraphStyle("cover_kicker", fontName=BOLD, fontSize=11.5, leading=16,
                                            textColor=colors.HexColor("#c9bdf7"), alignment=TA_LEFT),
            "cover_title": ParagraphStyle("cover_title", fontName=BLACK, fontSize=30, leading=37,
                                           textColor=colors.white, alignment=TA_LEFT),
            "cover_sub": ParagraphStyle("cover_sub", fontName=SB, fontSize=13, leading=19,
                                         textColor=colors.HexColor("#e3daf9"), alignment=TA_LEFT),
            "part_label": ParagraphStyle("part_label", fontName=BOLD, fontSize=11, leading=15,
                                          textColor=colors.HexColor("#e3daf9"), spaceAfter=3),
            "part_title": ParagraphStyle("part_title", fontName=BLACK, fontSize=20, leading=26,
                                          textColor=colors.white, spaceAfter=4),
            "part_desc": ParagraphStyle("part_desc", fontName=REG, fontSize=10, leading=15,
                                         textColor=colors.HexColor("#e3daf9")),
            "eyebrow": ParagraphStyle("eyebrow", fontName=BOLD, fontSize=10.5, leading=14,
                                       textColor=ACCENT, spaceAfter=3),
            "chapter_title": ParagraphStyle("chapter_title", fontName=BLACK, fontSize=20, leading=26,
                                             textColor=TEXT_DARK),
            "h1": ParagraphStyle("h1", fontName=XB, fontSize=15.5, leading=21,
                                  textColor=ACCENT_DEEP, spaceBefore=10, spaceAfter=10),
            "h2": ParagraphStyle("h2", fontName=BOLD, fontSize=13, leading=19,
                                  textColor=TEXT_DARK, spaceBefore=14, spaceAfter=7),
            "body": ParagraphStyle("body", fontName=REG, fontSize=11.8, leading=20,
                                    textColor=TEXT_DARK, spaceAfter=11, alignment=TA_LEFT),
            "quote": ParagraphStyle("quote", fontName=MED, fontSize=12, leading=19,
                                     textColor=ACCENT_DEEP, alignment=TA_LEFT, spaceBefore=4, spaceAfter=10,
                                     leftIndent=10, backColor=ACCENT_SOFT, borderPadding=12),
            "small": ParagraphStyle("small", fontName=REG, fontSize=9.3, leading=14,
                                     textColor=TEXT_DIM, spaceAfter=4),
            "caption": ParagraphStyle("caption", fontName=REG, fontSize=9.3, leading=13,
                                       textColor=TEXT_DIM, alignment=TA_CENTER, spaceBefore=4, spaceAfter=14),
            "toc": ParagraphStyle("toc", fontName=REG, fontSize=12, leading=23,
                                   textColor=TEXT_DARK, alignment=TA_LEFT),
            "toc_part": ParagraphStyle("toc_part", fontName=BOLD, fontSize=13, leading=25,
                                        textColor=ACCENT, alignment=TA_LEFT),
            "table_cell": ParagraphStyle("table_cell", fontName=REG, fontSize=10, leading=14.5,
                                          textColor=TEXT_DARK),
            "table_head": ParagraphStyle("table_head", fontName=BOLD, fontSize=10, leading=14.5,
                                          textColor=colors.white),
            "box_body": ParagraphStyle("box_body", fontName=REG, fontSize=10.5, leading=16.5,
                                        textColor=TEXT_DARK),
            "step_num": ParagraphStyle("step_num", fontName=BLACK, fontSize=14, leading=17,
                                        textColor=colors.white, alignment=TA_CENTER),
            "step_label": ParagraphStyle("step_label", fontName=BOLD, fontSize=10, leading=13.5,
                                          textColor=TEXT_DARK, alignment=TA_CENTER),
            "step_desc": ParagraphStyle("step_desc", fontName=REG, fontSize=8.5, leading=12,
                                         textColor=TEXT_DIM, alignment=TA_CENTER),
            "summary_head": ParagraphStyle("summary_head", fontName=XB, fontSize=11.5, leading=15,
                                            textColor=colors.white),
            "summary_body": ParagraphStyle("summary_body", fontName=REG, fontSize=10.3, leading=16,
                                            textColor=colors.HexColor("#dcdcf5")),
        }

    # ---------- 표지 ----------
    def cover(self, kicker, title_html, subtitle, tagline=None):
        cell = [Paragraph(kicker, self.styles["cover_kicker"]), Spacer(1, 12),
                Paragraph(title_html, self.styles["cover_title"]), Spacer(1, 10),
                Paragraph(subtitle, self.styles["cover_sub"])]
        if tagline:
            cell += [Spacer(1, 190), Paragraph(tagline, self.styles["cover_sub"])]
        else:
            cell += [Spacer(1, 210)]
        box = Table([[cell]], colWidths=[166 * mm], rowHeights=[233 * mm])
        box.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#15132a")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 20),
            ("RIGHTPADDING", (0, 0), (-1, -1), 16),
            ("TOPPADDING", (0, 0), (-1, -1), 26),
        ]))
        self.story.append(box)
        self.story.append(PageBreak())

    # ---------- 기본 텍스트 ----------
    def h1(self, text):
        self.story.append(Paragraph(text, self.styles["h1"]))
        self.story.append(HRFlowable(width="100%", thickness=0.8, color=BORDER, spaceAfter=10))

    def h2(self, text):
        self.story.append(Paragraph(text, self.styles["h2"]))

    def body(self, text):
        self.story.append(Paragraph(text, self.styles["body"]))

    def quote(self, text):
        self.story.append(Paragraph(text, self.styles["quote"]))

    def spacer(self, h=8):
        self.story.append(Spacer(1, h))

    # ---------- 파트/챕터 헤더 ----------
    def part_page(self, label, title, desc=""):
        cell = [Paragraph(label, self.styles["part_label"]), Paragraph(title, self.styles["part_title"])]
        if desc:
            cell.append(Paragraph(desc, self.styles["part_desc"]))
        banner = Table([[cell]], colWidths=[166 * mm])
        banner.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), ACCENT),
            ("TOPPADDING", (0, 0), (-1, -1), 14), ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
            ("LEFTPADDING", (0, 0), (-1, -1), 16), ("RIGHTPADDING", (0, 0), (-1, -1), 16),
        ]))
        self.story.append(banner)
        self.story.append(Spacer(1, 14))

    def chapter_header(self, num, title, eyebrow="CHAPTER"):
        bar = Table([[""]], colWidths=[3 * mm], rowHeights=[18 * mm],
                    style=TableStyle([("BACKGROUND", (0, 0), (-1, -1), ACCENT)]))
        head = [Paragraph(f"{eyebrow} {num:02d}", self.styles["eyebrow"]),
                Paragraph(title, self.styles["chapter_title"])]
        t = Table([[bar, head]], colWidths=[6 * mm, 160 * mm])
        t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (1, 0), (1, 0), 10)]))
        self.story.append(t)
        self.story.append(Spacer(1, 12))

    # ---------- 색상별 박스 ----------
    def _colored_box(self, header, items, bg, bar, icon):
        rows = [[Paragraph(f"{icon} {header}", ParagraphStyle(
            "bh", fontName=BOLD, fontSize=10.3, leading=14, textColor=bar))]]
        for it in items:
            rows.append([Paragraph("• " + it, self.styles["box_body"])])
        t = Table(rows, colWidths=[164 * mm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), bg),
            ("LINEBEFORE", (0, 0), (0, -1), 3, bar),
            ("LEFTPADDING", (0, 0), (-1, -1), 14), ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]))
        self.story.append(t)
        self.story.append(Spacer(1, 11))

    def tip_box(self, items, header="TIP"):
        self._colored_box(header, items, TIP_BG, TIP_BAR, "✓")

    def warn_box(self, items, header="주의"):
        self._colored_box(header, items, WARN_BG, WARN_BAR, "⚠")

    def callout_box(self, title_text, items, numbered=False):
        """범용 보라색 박스(참고 자료ㆍ목록형 콘텐츠용, 기존 방식 유지)."""
        rows = [[Paragraph(f"<b>{title_text}</b>", ParagraphStyle(
            "boxhead", fontName=BOLD, fontSize=11, leading=15, textColor=colors.white))]]
        for i, item in enumerate(items, 1):
            prefix = f"{i}. " if numbered else "ㆍ  "
            rows.append([Paragraph(prefix + item, self.styles["box_body"])])
        t = Table(rows, colWidths=[166 * mm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
            ("BACKGROUND", (0, 1), (-1, -1), ACCENT_SOFT),
            ("TOPPADDING", (0, 0), (-1, 0), 7), ("BOTTOMPADDING", (0, 0), (-1, 0), 7),
            ("LEFTPADDING", (0, 0), (-1, -1), 13), ("RIGHTPADDING", (0, 0), (-1, -1), 13),
            ("TOPPADDING", (0, 1), (-1, -1), 6), ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
            ("BOX", (0, 0), (-1, -1), 0.8, BORDER), ("LINEBELOW", (0, 0), (-1, 0), 0.8, BORDER),
        ]))
        self.story.append(t)
        self.story.append(Spacer(1, 12))

    def next_chapter_box(self, title, hook):
        rows = [[Paragraph("▶ NEXT CHAPTER", ParagraphStyle(
            "nb", fontName=BOLD, fontSize=9.5, leading=13, textColor=NEXT_BAR))],
            [Paragraph(title, ParagraphStyle("nt", fontName=XB, fontSize=12, leading=16, textColor=TEXT_DARK))],
            [Paragraph(hook, self.styles["box_body"])]]
        t = Table(rows, colWidths=[164 * mm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), NEXT_BG),
            ("LINEBEFORE", (0, 0), (0, -1), 3, NEXT_BAR),
            ("LEFTPADDING", (0, 0), (-1, -1), 14),
            ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        self.story.append(t)
        self.story.append(Spacer(1, 12))

    def summary_box(self, title, items):
        rows = [[Paragraph("■ " + title, self.styles["summary_head"])]]
        for i, it in enumerate(items, 1):
            rows.append([Paragraph(f"{i}. " + it, self.styles["summary_body"])])
        t = Table(rows, colWidths=[164 * mm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), SUMMARY_BG),
            ("LEFTPADDING", (0, 0), (-1, -1), 16), ("RIGHTPADDING", (0, 0), (-1, -1), 16),
            ("TOPPADDING", (0, 0), (-1, -1), 10), ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ]))
        self.story.append(t)
        self.story.append(Spacer(1, 13))

    def site_box(self, name, url, desc, highlight=False):
        rows = [[Paragraph(f"<b>{name}</b>  <font color='#4d5268' size=9>{url}</font>", ParagraphStyle(
            "sitehead", fontName=BOLD, fontSize=11, leading=15, textColor=ACCENT if highlight else TEXT_DARK))],
            [Paragraph(desc, self.styles["body"])]]
        t = Table(rows, colWidths=[166 * mm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#faf9ff") if not highlight else ACCENT_SOFT),
            ("BOX", (0, 0), (-1, -1), 0.8, BORDER),
            ("LEFTPADDING", (0, 0), (-1, -1), 13), ("RIGHTPADDING", (0, 0), (-1, -1), 13),
            ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        self.story.append(t)
        self.story.append(Spacer(1, 9))

    # ---------- 도식 ----------
    def icon_steps(self, steps):
        """steps: [(label, desc), ...] 최대 5~6개 권장"""
        cells = []
        for i, (label, desc) in enumerate(steps):
            circ = Table([[Paragraph(str(i + 1), self.styles["step_num"])]], colWidths=[10 * mm], rowHeights=[10 * mm])
            circ.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), STEP_SHADES[i % len(STEP_SHADES)]),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROUNDEDCORNERS", [20, 20, 20, 20]),
            ]))
            cells.append([circ, Spacer(1, 4), Paragraph(label, self.styles["step_label"]),
                          Paragraph(desc, self.styles["step_desc"])])
        row = Table([cells], colWidths=[164 / len(steps) * mm] * len(steps))
        row.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
        self.story.append(row)
        self.story.append(Spacer(1, 13))

    def flow_diagram(self, steps):
        cells = [Paragraph(f"<b>{s}</b>", ParagraphStyle(
            f"flow{i}", fontName=BOLD, fontSize=9.3, leading=13, textColor=colors.white, alignment=TA_CENTER))
            for i, s in enumerate(steps)]
        t = Table([cells], colWidths=[166 / len(steps) * mm] * len(steps), rowHeights=[16 * mm])
        style = [("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (0, 0), (-1, -1), "CENTER")]
        for i in range(len(steps)):
            style.append(("BACKGROUND", (i, 0), (i, 0), STEP_SHADES[i % len(STEP_SHADES)]))
        t.setStyle(TableStyle(style))
        self.story.append(t)
        self.story.append(Spacer(1, 10))

    def star_table(self, header3, rows):
        """rows: [(label, desc, stars(1-5)), ...]"""
        data = [[Paragraph(h, self.styles["table_head"]) for h in header3]]
        for label, desc, stars in rows:
            star_str = "★" * stars + "☆" * (5 - stars)
            data.append([Paragraph(label, self.styles["table_cell"]), Paragraph(desc, self.styles["table_cell"]),
                         Paragraph(f"<font color='#5a3fd6'>{star_str}</font>", self.styles["table_cell"])])
        t = Table(data, colWidths=[42 * mm, 90 * mm, 32 * mm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#faf9ff")]),
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        self.story.append(t)
        self.story.append(Spacer(1, 12))

    def simple_table(self, header, rows, col_widths):
        data = [[Paragraph(str(c), self.styles["table_head"]) for c in header]]
        for r in rows:
            data.append([Paragraph(str(c), self.styles["table_cell"]) for c in r])
        t = Table(data, colWidths=col_widths)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#faf9ff")]),
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        self.story.append(t)
        self.story.append(Spacer(1, 12))

    def bar_row(self, label, value, max_value, color, unit="", label_w=42):
        bar_width_mm = max(2, (value / max_value) * (150 - label_w - 24))
        bar = Table([[""]], colWidths=[bar_width_mm * mm], rowHeights=[6 * mm])
        bar.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), color)]))
        row = Table([[Paragraph(label, self.styles["table_cell"]), bar,
                      Paragraph(f"{value}{unit}", self.styles["table_cell"])]],
                    colWidths=[label_w * mm, (150 - label_w - 24) * mm, 24 * mm])
        row.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
        self.story.append(row)
        self.story.append(Spacer(1, 3))

    # ---------- 스크린샷 ----------
    def screenshot(self, filename, caption_text):
        path = self.shot_dir / filename
        if not path.exists():
            self.body(f"<i>[화면 캡처 누락: {filename}]</i>")
            return
        with PILImage.open(path) as im:
            w, h = im.size
        max_w = 156 * mm
        ratio = h / w
        img = Image(str(path), width=max_w, height=max_w * ratio)
        box = Table([[img], [Paragraph(caption_text, self.styles["caption"])]], colWidths=[max_w])
        box.setStyle(TableStyle([
            ("BOX", (0, 0), (0, 0), 0.8, BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]))
        self.story.append(KeepTogether(box))
        self.story.append(Spacer(1, 6))

    def toc_line(self, text, style="toc"):
        self.story.append(Paragraph(text, self.styles[style]))

    # ---------- 빌드 ----------
    def build(self, footer_tagline=None, watermark_text="수익화허브 · 무단 전재·재배포 금지"):
        if footer_tagline:
            self.story.append(Spacer(1, 20))
            self.story.append(HRFlowable(width="100%", thickness=0.7, color=BORDER, spaceAfter=10))
            self.story.append(Paragraph(footer_tagline, self.styles["small"]))

        def draw_watermark(canvas, dark_bg=False):
            """구매 후 재배포를 막기 위한 저작권 표시용 옅은 대각선 반복 워터마크.
            눈에 거슬리지 않을 정도로만 보이되, 스크린샷ㆍ캡처로 재유포될 때는
            남아있도록 본문 위에 얹는다(밝은 배경=짙은 회색/어두운 배경=흰색, 알파 매우 낮음)."""
            canvas.saveState()
            canvas.setFont(BOLD, 12.5)
            canvas.setFillColor(colors.white if dark_bg else colors.HexColor("#000000"))
            try:
                canvas.setFillAlpha(0.05 if dark_bg else 0.045)
            except AttributeError:
                pass
            canvas.translate(A4[0] / 2, A4[1] / 2)
            canvas.rotate(33)
            step_x, step_y = 78 * mm, 40 * mm
            for ix in range(-3, 4):
                for iy in range(-5, 6):
                    canvas.drawCentredString(ix * step_x, iy * step_y, watermark_text)
            canvas.restoreState()

        def on_cover(canvas, doc_):
            if watermark_text:
                draw_watermark(canvas, dark_bg=True)

        def add_page_number(canvas, doc_):
            if watermark_text:
                draw_watermark(canvas, dark_bg=False)
            canvas.saveState()
            canvas.setFont(REG, 9)
            canvas.setFillColor(TEXT_DIM)
            canvas.drawCentredString(A4[0] / 2, 13 * mm, str(doc_.page))
            canvas.restoreState()

        self.doc.build(self.story, onFirstPage=on_cover, onLaterPages=add_page_number)
        print("done:", self.out_path)
