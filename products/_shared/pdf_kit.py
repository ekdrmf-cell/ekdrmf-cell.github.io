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
- ✕(U+2715)ㆍ✗(U+2717) 같은 곱셈기호형 X도 Pretendard에 글리프가 없어 깨진다
  (2026-08-09 발견, comparison_card에서 확인) — "X"자 그대로 쓸 것.

2026-08-09 디자인 리뉴얼(문서적ㆍ단조롭다는 피드백 반영):
- 보조 강조색 ACCENT2(테라코타) 추가 — 보라 하나로만 통일됐던 단조로움을 깨는 용도.
- 표지ㆍ파트 배너ㆍ챕터 헤더에 "고스트 넘버"(큰 반투명/연한 색 숫자) 장식 추가.
- 표지는 평면 단색 박스 대신 캔버스에 풀블리드로 겹친 원 그라디언트풍 배경을 그림.
- 박스류(tip/warn/next/summary/callout/site_box)에 모서리 둥글림(ROUNDEDCORNERS) 적용.
- 신규 컴포넌트: stat_hero(큰 숫자 하나 강조), stat_row(작은 숫자 여러 개 가로 나열),
  pull_quote(큰 인용부호 강조 인용구), comparison_card(Before/After 빨강ㆍ초록 대비 카드).
  **Before/After 실전예시를 쓸 때는 이제 simple_table 대신 comparison_card를 우선 사용할 것.**
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
ACCENT_SOFT = colors.HexColor("#d9cdf7")
TEXT_DARK = colors.HexColor("#1f2333")
TEXT_DIM = colors.HexColor("#4d5268")
BORDER = colors.HexColor("#d9d5f0")

# 2026-08-09 디자인 리뉴얼: 보라 하나로만 통일돼 있던 게 "문서적ㆍ단조롭다"는
# 피드백을 받아, 대비를 주는 보조 강조색(테라코타)과 고스트 넘버ㆍBefore/After
# 카드ㆍ스탯 히어로용 팔레트를 추가함. tip/warn/next/summary는 기존 의미 유지.
# (같은 날 2차 피드백: 배경 틴트가 너무 파스텔해서 밋밋해 보임 → 전체적으로
# 명도를 낮추고 채도를 높여 더 짙고 선명하게 재조정함.)
ACCENT2 = colors.HexColor("#d9501f")
ACCENT2_DEEP = colors.HexColor("#a53c17")
ACCENT2_SOFT = colors.HexColor("#f8cdb3")
GHOST_ON_ACCENT = colors.HexColor("#8574e2")   # 보라 배경 위 고스트 넘버(파트 배너)
GHOST_ON_WHITE = colors.HexColor("#d7c9f5")    # 흰 배경 위 고스트 넘버(챕터 헤더)

TIP_BG, TIP_BAR = colors.HexColor("#c3daf9"), colors.HexColor("#1f4fa8")
WARN_BG, WARN_BAR = colors.HexColor("#fbdf9c"), colors.HexColor("#a35f05")
NEXT_BG, NEXT_BAR = colors.HexColor("#f6c7d8"), colors.HexColor("#a12760")
SUMMARY_BG = colors.HexColor("#1f2338")
CMP_BAD_BG, CMP_BAD_BAR = colors.HexColor("#f6c9c2"), colors.HexColor("#a8321f")
CMP_GOOD_BG, CMP_GOOD_BAR = colors.HexColor("#bce6d1"), colors.HexColor("#1c6e3f")

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
            # ---- 2026-08-09 디자인 리뉴얼 추가분 ----
            "chnum_badge": ParagraphStyle("chnum_badge", fontName=BLACK, fontSize=14.5, leading=17,
                                           textColor=colors.white, alignment=TA_CENTER),
            "chnum_ghost": ParagraphStyle("chnum_ghost", fontName=BLACK, fontSize=46, leading=46,
                                           textColor=GHOST_ON_WHITE, alignment=TA_CENTER),
            "part_ghost": ParagraphStyle("part_ghost", fontName=BLACK, fontSize=40, leading=40,
                                          textColor=GHOST_ON_ACCENT, alignment=TA_CENTER),
            "stat_num": ParagraphStyle("stat_num", fontName=BLACK, fontSize=38, leading=42,
                                        textColor=ACCENT2, alignment=TA_CENTER),
            "stat_label": ParagraphStyle("stat_label", fontName=BOLD, fontSize=11.5, leading=15,
                                          textColor=TEXT_DARK, alignment=TA_CENTER, spaceBefore=2),
            "stat_sub": ParagraphStyle("stat_sub", fontName=REG, fontSize=9, leading=13,
                                        textColor=TEXT_DIM, alignment=TA_CENTER),
            "pull_mark": ParagraphStyle("pull_mark", fontName=BLACK, fontSize=32, leading=26,
                                         textColor=ACCENT2, spaceAfter=2),
            "pull_text": ParagraphStyle("pull_text", fontName=MED, fontSize=12.8, leading=19.5,
                                         textColor=ACCENT_DEEP, alignment=TA_LEFT),
            "pull_attr": ParagraphStyle("pull_attr", fontName=BOLD, fontSize=9.3, leading=13,
                                         textColor=TEXT_DIM, spaceBefore=6),
            "cmp_head_bad": ParagraphStyle("cmp_head_bad", fontName=BOLD, fontSize=10, leading=14,
                                            textColor=CMP_BAD_BAR),
            "cmp_head_good": ParagraphStyle("cmp_head_good", fontName=BOLD, fontSize=10, leading=14,
                                             textColor=CMP_GOOD_BAR),
        }

    # ---------- 표지 ----------
    def cover(self, kicker, title_html, subtitle, tagline=None):
        """표지 배경(그라디언트풍 도형)은 build()의 onFirstPage에서 캔버스에 풀블리드로
        그리므로, 여기 테이블은 배경색 없이 텍스트만 얹는다(2026-08-09 리뉴얼)."""
        accent_line = Table([[""]], colWidths=[26 * mm], rowHeights=[2.6 * mm],
                             style=TableStyle([("BACKGROUND", (0, 0), (-1, -1), ACCENT2)]))
        cell = [accent_line, Spacer(1, 10),
                Paragraph(kicker, self.styles["cover_kicker"]), Spacer(1, 12),
                Paragraph(title_html, self.styles["cover_title"]), Spacer(1, 10),
                Paragraph(subtitle, self.styles["cover_sub"])]
        if tagline:
            cell += [Spacer(1, 178), Paragraph(tagline, self.styles["cover_sub"])]
        else:
            cell += [Spacer(1, 198)]
        box = Table([[cell]], colWidths=[166 * mm], rowHeights=[233 * mm])
        box.setStyle(TableStyle([
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
        """2026-08-09 리뉴얼: 파트 번호를 오른쪽에 큰 고스트 넘버로 얹고 모서리를 둥글려
        평범한 색 배너에서 벗어나게 함."""
        num_str = "".join(ch for ch in label if ch.isdigit())
        cell = [Paragraph(label, self.styles["part_label"]), Paragraph(title, self.styles["part_title"])]
        if desc:
            cell.append(Paragraph(desc, self.styles["part_desc"]))
        ghost = Paragraph(num_str, self.styles["part_ghost"]) if num_str else Paragraph("", self.styles["part_ghost"])
        banner = Table([[cell, ghost]], colWidths=[136 * mm, 30 * mm])
        banner.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), ACCENT),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (1, 0), (1, 0), "RIGHT"),
            ("TOPPADDING", (0, 0), (-1, -1), 14), ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
            ("LEFTPADDING", (0, 0), (-1, -1), 16), ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ("ROUNDEDCORNERS", [10, 10, 10, 10]),
        ]))
        self.story.append(banner)
        self.story.append(Spacer(1, 14))

    def chapter_header(self, num, title, eyebrow="CHAPTER"):
        """2026-08-09 리뉴얼: 얇은 색바 대신 컬러 배지 + 큰 고스트 넘버 + 짧은 강조선으로
        구성해 매뉴얼 느낌의 반복 패턴에서 벗어나게 함."""
        badge = Table([[Paragraph(f"{num:02d}", self.styles["chnum_badge"])]],
                      colWidths=[15 * mm], rowHeights=[15 * mm])
        badge.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), ACCENT),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ROUNDEDCORNERS", [5, 5, 5, 5]),
        ]))
        head = [Paragraph(eyebrow, self.styles["eyebrow"]), Paragraph(title, self.styles["chapter_title"])]
        ghost = Paragraph(f"{num:02d}", self.styles["chnum_ghost"])
        t = Table([[badge, head, ghost]], colWidths=[19 * mm, 120 * mm, 27 * mm])
        t.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (2, 0), (2, 0), "RIGHT"),
            ("LEFTPADDING", (1, 0), (1, 0), 10),
        ]))
        self.story.append(t)
        self.story.append(HRFlowable(width="22%", thickness=2.2, color=ACCENT2, spaceBefore=8, spaceAfter=12, hAlign="LEFT"))

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
            ("ROUNDEDCORNERS", [7, 7, 7, 7]),
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
            ("ROUNDEDCORNERS", [8, 8, 8, 8]),
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
            ("ROUNDEDCORNERS", [7, 7, 7, 7]),
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
            ("ROUNDEDCORNERS", [9, 9, 9, 9]),
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
            ("ROUNDEDCORNERS", [7, 7, 7, 7]),
        ]))
        self.story.append(t)
        self.story.append(Spacer(1, 9))

    # ---------- 2026-08-09 리뉴얼 추가 컴포넌트 ----------
    def stat_hero(self, number, label, sublabel=None):
        """큰 숫자 하나로 데이터를 강조하는 인포그래픽형 카드. 법정기한ㆍ리뷰수ㆍ
        피해구제 건수처럼 "이 숫자 하나가 핵심"인 실측 데이터에 쓸 것."""
        cell = [Paragraph(number, self.styles["stat_num"]), Paragraph(label, self.styles["stat_label"])]
        if sublabel:
            cell.append(Paragraph(sublabel, self.styles["stat_sub"]))
        t = Table([[cell]], colWidths=[164 * mm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), ACCENT2_SOFT),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 16), ("BOTTOMPADDING", (0, 0), (-1, -1), 16),
            ("ROUNDEDCORNERS", [12, 12, 12, 12]),
        ]))
        self.story.append(t)
        self.story.append(Spacer(1, 12))

    def stat_row(self, stats):
        """stats: [(number, label), ...] 2~4개. 작은 숫자 여러 개를 가로로 나열할 때."""
        n = len(stats)
        w = 164 / n
        cells = []
        for number, label in stats:
            cells.append([Paragraph(number, ParagraphStyle(
                "sr_num", fontName=BLACK, fontSize=24, leading=27, textColor=ACCENT2, alignment=TA_CENTER)),
                Paragraph(label, self.styles["stat_sub"])])
        row = Table([cells], colWidths=[w * mm] * n)
        row.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#ece3f9")),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 12), ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ("LINEAFTER", (0, 0), (-2, -1), 0.6, BORDER),
            ("ROUNDEDCORNERS", [10, 10, 10, 10]),
        ]))
        self.story.append(row)
        self.story.append(Spacer(1, 12))

    def pull_quote(self, text, attribution=None):
        """굵은 인용부호를 곁들인 강조 인용구. 법 조문 원문ㆍ실제 응대 대사ㆍ핵심 한 문장을
        본문 사이에서 잡지 기사처럼 도드라지게 보여줄 때 쓸 것(기존 quote()보다 강한 강조)."""
        cell = [Paragraph("“", self.styles["pull_mark"]), Paragraph(text, self.styles["pull_text"])]
        if attribution:
            cell.append(Paragraph(attribution, self.styles["pull_attr"]))
        t = Table([[cell]], colWidths=[164 * mm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), ACCENT_SOFT),
            ("LEFTPADDING", (0, 0), (-1, -1), 20), ("RIGHTPADDING", (0, 0), (-1, -1), 18),
            ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 16),
            ("ROUNDEDCORNERS", [12, 12, 12, 12]),
        ]))
        self.story.append(t)
        self.story.append(Spacer(1, 12))

    def comparison_card(self, bad_label, bad_text, good_label, good_text):
        """Before/After(나쁜 예ㆍ좋은 예) 실전 대비 카드. 지금까지 simple_table이나 평문으로
        처리하던 Before/After 실전예시를 빨강/초록 카드로 시각화해 한눈에 대비되게 함."""
        def _panel(label, text, bg, bar, mark):
            rows = [[Paragraph(f"{mark}  {label}", ParagraphStyle(
                "cmph", fontName=BOLD, fontSize=10, leading=14, textColor=bar))],
                [Paragraph(text, self.styles["box_body"])]]
            t = Table(rows, colWidths=[79 * mm])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), bg),
                ("LINEBEFORE", (0, 0), (0, -1), 3, bar),
                ("LEFTPADDING", (0, 0), (-1, -1), 11), ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("ROUNDEDCORNERS", [7, 7, 7, 7]),
            ]))
            return t
        bad = _panel(bad_label, bad_text, CMP_BAD_BG, CMP_BAD_BAR, "X")
        good = _panel(good_label, good_text, CMP_GOOD_BG, CMP_GOOD_BAR, "✓")
        outer = Table([[bad, good]], colWidths=[81 * mm, 83 * mm])
        outer.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (1, 0), (1, 0), 4)]))
        self.story.append(outer)
        self.story.append(Spacer(1, 12))

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

        def draw_cover_art(canvas):
            """표지 전체를 풀블리드로 채우는 배경(2026-08-09 리뉴얼). 평면 단색 박스 대신
            겹쳐진 반투명 원으로 깊이감을 주고, 하단에 보조색 강조선을 둔다."""
            w, h = A4
            canvas.saveState()
            canvas.setFillColor(colors.HexColor("#15132a"))
            canvas.rect(0, 0, w, h, stroke=0, fill=1)
            layers = [
                (w * 0.95, h * 0.97, 128, ACCENT_DEEP, 0.78),
                (w * 0.86, h * 0.86, 92, ACCENT, 0.58),
                (w * 0.06, h * 0.05, 96, ACCENT2, 0.68),
                (w * 0.18, h * 0.14, 46, ACCENT2, 0.4),
            ]
            for cx, cy, r, col, alpha in layers:
                canvas.setFillColor(col)
                try:
                    canvas.setFillAlpha(alpha)
                except AttributeError:
                    pass
                canvas.circle(cx, cy, r, stroke=0, fill=1)
            try:
                canvas.setFillAlpha(1)
            except AttributeError:
                pass
            canvas.setFillColor(ACCENT2)
            canvas.rect(0, 26, w, 3.2, stroke=0, fill=1)
            canvas.restoreState()

        def on_cover(canvas, doc_):
            draw_cover_art(canvas)
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
