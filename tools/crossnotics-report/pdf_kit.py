# -*- coding: utf-8 -*-
"""천지인운명관 전용 PDF 빌드 키트.

2026-08-23 — 서비스허브(전자책 13종)와 공유하던 `products/_shared/pdf_kit.py`에서
완전히 분리된 독립 사본입니다(사용자 지시: "서비스허브와 천지인운명관은 별개의 사이트이니
연결된 모든 것을 끊을 것"). 폰트도 이 폴더 안의 `fonts/`에 따로 복사해뒀습니다 — 이제
서비스허브 쪽 파일이 바뀌어도 이 파일은 전혀 영향받지 않고, 반대로 이 파일을 자유롭게
고쳐도 전자책 13종에는 영향이 없습니다.

분리 시점까지의 디자인 이력(서비스허브 쪽 pdf_kit.py에서 물려받은 것):
- Pretendard TTF 임베딩, 용도별 색 구분 박스(TIP/WARN/NEXT/SUMMARY), 고스트 넘버ㆍ표지
  그라디언트, stat_hero/pull_quote/comparison_card 등 인포그래픽 컴포넌트.
- 2026-08-23 크로스노틱스 전용으로 추가된 것(이제 이 파일에서는 "선택적 파라미터"가 아니라
  기본 동작): chapter_header가 체계별 색(사주=주황ㆍ별자리=보라ㆍ타로=초록)을 받을 수 있음.
- 2026-08-24 — 표지는 사용자가 실제로 제공한 로고 이미지(assets/logo.png)를 그대로 쓰고,
  배경은 crossnotics.css와 같은 팔레트(gold/보라/초록)의 번짐 그라디언트, 본문 테두리는
  금색, 본문 배경엔 로고를 아주 옅게 워터마크로 깔아 사이트와 톤을 맞춤.
"""

import re
from pathlib import Path
from xml.sax.saxutils import escape as _xml_escape
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    HRFlowable, Image, KeepTogether, CondPageBreak
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
# 2026-08-24 추가 — 사용자가 준 디자인 가이드 1번 원칙: "본문은 세리프, 제목은 산세리프
# 두 가지만 써서 위계를 명확히 하라." 가이드가 예시로 든 KoPub바탕체는 "프로그램에
# 내장(임베딩)해서 쓰려면 문화체육관광부ㆍ한국출판인회의의 별도 사전승인이 필요"하다는
# 조건이 있어(공유마당 라이선스 확인, 2026-08-24) 승인 없이 그냥 쓸 수 없었음 — 대신
# 처음부터 소프트웨어 내장을 허용하는 SIL Open Font License인 Noto Serif KR(구글 폰트)로
# 대체함. 변수 폰트(NotoSerifKR[wght].ttf)를 fonttools로 Regular(wght=400) 고정 폭 인스턴스로
# 뽑아 저장한 파일 — ReportLab은 가변 폰트를 안정적으로 지원하지 않아 고정 인스턴스가 필요.
SERIF = "NotoSerifKR"

_FONTS_REGISTERED = False

_BOLD_MARK_RE = re.compile(r"\*\*(.+?)\*\*")
_PAREN_LEADING_SEP_RE = re.compile(r"\(\s*[,ㆍ·]+\s*")
_PAREN_TRAILING_SEP_RE = re.compile(r"[\s,ㆍ·]+\)")
_PAREN_EMPTY_RE = re.compile(r"\(\s*[,ㆍ·]*\s*\)")
_FONT_CMAP_CACHE = None


def _font_cmap():
    """PDF 본문 폰트(Pretendard-Regular)가 실제로 그릴 수 있는 유니코드 집합. 2026-08-24
    추가 — build_report.py가 이미 report.json 저장 전에 같은 검사로 걸러내지만, 이 파일은
    report_kit.py를 통해 독립적으로도 실행될 수 있어(예: 예전에 만들어둔 report.json을
    다시 PDF로 뽑는 경우) 렌더링 직전에도 한 번 더 막아야 "완벽하게" 안전하다(사용자 지시:
    폰트가 못 그리는 글자가 최종 PDF에 나갈 방법 자체를 없앨 것)."""
    global _FONT_CMAP_CACHE
    if _FONT_CMAP_CACHE is None:
        from fontTools.ttLib import TTFont as _TTFont
        _FONT_CMAP_CACHE = set(_TTFont(str(FONT_DIR / "Pretendard-Regular.ttf")).getBestCmap().keys())
    return _FONT_CMAP_CACHE


def _strip_unsupported(text):
    cmap = _font_cmap()
    cleaned = "".join(ch for ch in text if ch.isspace() or ord(ch) < 0x20 or ord(ch) in cmap)
    cleaned = _PAREN_LEADING_SEP_RE.sub("(", cleaned)
    cleaned = _PAREN_TRAILING_SEP_RE.sub(")", cleaned)
    cleaned = _PAREN_EMPTY_RE.sub("", cleaned)
    return re.sub(r" {2,}", " ", cleaned)


def _md(text, accent_hex="#5a3fd6", max_bold=2):
    """2026-08-24 추가 — 가독성 개선(사용자 피드백: "3페이지는 그냥 글자로만 가득 차있다,
    중요한 단어에 밑줄이나 색·굵기 변형이 있어야 한다"). LLM이 강조하고 싶은 부분을
    **이렇게** 표시하면(build_report.py SYSTEM_PROMPT에서 이 문법만 쓰도록 지시), 굵게 +
    강조색으로 렌더링한다. ReportLab의 Paragraph는 자체적으로 간단한 XML을 해석하므로,
    LLM이 실수로 <, >, & 같은 문자를 그대로 쓰면(수식·비교 표현 등에서 나올 수 있음) PDF
    빌드가 깨지거나 태그로 오인식될 수 있다 — 그래서 원문을 먼저 XML 이스케이프한 뒤에만
    **마크를 <b><font color=...> 태그로 치환한다(이스케이프 후에도 별표 문자는 그대로
    남으므로 순서가 안전함).

    2026-08-24(2차) — 실사용 리포트에서 한 문단에 강조가 5~8곳씩 붙어 오히려 아무것도
    안 튀는 문제를 실제로 확인함(사용자 지적: "이러면 눈에 안 들어온다"). 프롬프트에서
    "1~3곳만"이라고 지시해도 안 지켜지는 걸 이미 여러 번 확인했으므로(한자 문제와 같은
    패턴), 여기서 문단(chunk)당 강조 개수를 max_bold로 강제 제한한다 — 넘치는 건 그냥
    일반 텍스트로 남긴다(경고만 하고 넘어가지 않고 실제로 결과를 보장함)."""
    safe = _strip_unsupported(text or "")
    escaped = _xml_escape(safe)
    count = 0

    def _sub(m):
        nonlocal count
        count += 1
        if count > max_bold:
            return m.group(1)
        return f'<b><font color="{accent_hex}">{m.group(1)}</font></b>'

    return _BOLD_MARK_RE.sub(_sub, escaped)


_SENTENCE_END_RE = re.compile(r"(?<=[다요])\. ")


def _split_paragraphs(text, max_chunk_chars=420):
    """2026-08-24 추가 — 실사용 리포트에서 한 섹션 본문이 20줄 넘게 줄바꿈 하나 없이
    이어지는 "글자 벽"이 실제로 나온 걸 확인함(사용자 지적). LLM이 문단 사이에 빈 줄
    (\\n\\n)을 넣도록 프롬프트에서도 지시하지만(5-A번), 그것만 믿지 않고(같은 이유로
    한자 문제를 두 번 겪음) 렌더러가 항상 적당한 길이로 문단을 나누도록 보장한다:
    1) 원문에 이미 빈 줄이 있으면 그걸 우선 따르고,
    2) 그렇게 나눈 덩어리가 여전히 max_chunk_chars보다 길면, 그 덩어리의 중간 지점에서
       가장 가까운 문장 끝("~다. "/"~요. ")을 찾아 추가로 쪼갠다.
    문장 경계를 못 찾으면(예: 문장부호가 특이한 경우) 억지로 자르지 않고 그대로 둔다 —
    잘못된 지점에서 자르는 것보다는 긴 문단 하나가 낫다."""
    raw_chunks = [c.strip() for c in re.split(r"\n\s*\n", text or "") if c.strip()]
    result = []
    for chunk in raw_chunks:
        if len(chunk) <= max_chunk_chars:
            result.append(chunk)
            continue
        sentence_ends = [m.end() for m in _SENTENCE_END_RE.finditer(chunk)]
        if not sentence_ends:
            result.append(chunk)
            continue
        mid = len(chunk) / 2
        split_at = min(sentence_ends, key=lambda i: abs(i - mid))
        result.append(chunk[:split_at].strip())
        result.append(chunk[split_at:].strip())
    return result or [text or ""]


def extract_subheadings(text):
    """2026-08-24 추가 — body() 안의 "## 소제목" 줄만 뽑아낸다. mini_toc()가 이 목록으로
    챕터 맨 위에 "이 챕터에서 다루는 것" 칩을 만드는 데 쓴다(사용자 요청: "글만 있기보다
    이해를 돕는 도구를 여러 개 써달라" — 이미 파싱하는 소제목 데이터를 챕터 미리보기로도
    재사용하는 것이라 새 환각 위험은 없음)."""
    heads = []
    for chunk in _split_paragraphs(text):
        stripped = chunk.strip()
        if stripped.startswith("## "):
            first_line = stripped.partition("\n")[0]
            heads.append(first_line[3:].strip())
    return heads


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
    pdfmetrics.registerFont(TTFont(SERIF, str(FONT_DIR / "NotoSerifKR-Regular.ttf")))
    _FONTS_REGISTERED = True


# ---------- 색 ----------
ACCENT = colors.HexColor("#5a3fd6")
ACCENT_DEEP = colors.HexColor("#3d2a99")
ACCENT_SOFT = colors.HexColor("#d9cdf7")
TEXT_DARK = colors.HexColor("#1f2333")
TEXT_DIM = colors.HexColor("#4d5268")
BORDER = colors.HexColor("#d9d5f0")

ACCENT2 = colors.HexColor("#d9501f")
ACCENT2_DEEP = colors.HexColor("#a53c17")
ACCENT2_SOFT = colors.HexColor("#f8cdb3")

# 2026-08-24 추가 — 사용자 지시: "사이트 색상을 보고 표지도 비슷하게, 그라데이션(번지는
# 느낌)이 고급스러워 보인다." crossnotics.css의 실제 변수값을 그대로 가져옴(--gold,
# --accent, --accent-2 / 프리미엄 버튼 그라디언트 linear-gradient(135deg, gold, #c99a4e,
# accent)) — 사이트와 PDF가 같은 팔레트를 쓰게 함.
GOLD = colors.HexColor("#dcb972")
GOLD_DEEP = colors.HexColor("#c99a4e")
SITE_PURPLE = colors.HexColor("#a68aff")
SITE_TEAL = colors.HexColor("#2fd7a3")
COVER_BASE = colors.HexColor("#100e1c")
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
    def __init__(self, out_path, title, author="천지인운명관", shot_dir=None):
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
            # 2026-08-24 — 사용자 지시: "표지 폰트는 본문의 폰트와 일치시키고 텍스트 전부
            # 황금색으로." 본문(body/box_body)이 쓰는 세리프(SERIF=NotoSerifKR)로 통일하고,
            # 색도 하나(GOLD)로 맞춤 — 크기 차이만으로 킥커/제목/부제 위계를 표현.
            "cover_kicker": ParagraphStyle("cover_kicker", fontName=SERIF, fontSize=11.5, leading=16,
                                            textColor=GOLD, alignment=TA_LEFT),
            "cover_title": ParagraphStyle("cover_title", fontName=SERIF, fontSize=30, leading=37,
                                           textColor=GOLD, alignment=TA_LEFT),
            "cover_sub": ParagraphStyle("cover_sub", fontName=SERIF, fontSize=13, leading=19,
                                         textColor=GOLD, alignment=TA_LEFT),
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
            # 2026-08-24 신설 — 사용자 지적: "가독성이 여전히 떨어진다, h구조를 써보는 게
            # 어떨까." 지금까지는 챕터 제목(chapter_header) 하나 아래에 긴 본문이 소제목
            # 없이 쭉 이어졌음 — 본문 안에서도 소주제가 바뀔 때마다 짚어줄 소제목 스타일을
            # 추가함(body()가 "## 소제목" 마크를 인식해서 이 스타일로 렌더링, 아래 참고).
            "h3": ParagraphStyle("h3", fontName=BOLD, fontSize=12.5, leading=17,
                                  textColor=ACCENT, spaceBefore=14, spaceAfter=4),
            # 2026-08-24 — 디자인 가이드 1번 원칙("본문은 세리프, 제목/포인트는 산세리프
            # 두 가지만") 반영. 본문(body)ㆍ박스 안 설명글(box_body)만 세리프로 바꾸고,
            # 제목ㆍ배지ㆍ강조 인용구는 계속 Pretendard(산세리프)로 남겨 위계를 유지함.
            "body": ParagraphStyle("body", fontName=SERIF, fontSize=11.8, leading=20,
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
            "box_body": ParagraphStyle("box_body", fontName=SERIF, fontSize=10.5, leading=16.5,
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
        self.story.append(Paragraph(_xml_escape(_strip_unsupported(text)), self.styles["h1"]))
        self.story.append(HRFlowable(width="100%", thickness=0.8, color=BORDER, spaceAfter=10))

    def h2(self, text):
        self.story.append(Paragraph(_xml_escape(_strip_unsupported(text)), self.styles["h2"]))

    def body(self, text):
        """2026-08-24 — "## 소제목" 마크로 시작하는 문단은 본문이 아니라 소제목(h3)으로
        렌더링한다(SYSTEM_PROMPT 5-A번에서 LLM에게 이 문법을 쓰도록 지시 — "h구조를
        써달라"는 사용자 요청 반영). LLM이 "## 소제목" 뒤에 빈 줄을 안 두고 바로 본문을
        이어 쓸 가능성에 대비해(지금까지 프롬프트 지시가 100% 지켜진 적이 없었다 —
        한자ㆍ강조 개수와 같은 패턴), 첫 줄만 소제목으로 떼어내고 나머지는 별도 본문
        문단으로 렌더링한다 — 통째로 긴 문단이 전부 굵은 소제목 스타일로 나가는 사고를
        막기 위함."""
        chunks = _split_paragraphs(text)
        for i, chunk in enumerate(chunks):
            stripped = chunk.strip()
            if stripped.startswith("## "):
                first_line, _, rest = stripped.partition("\n")
                self.story.append(Paragraph(_xml_escape(_strip_unsupported(first_line[3:].strip())), self.styles["h3"]))
                rest = rest.strip()
                if rest:
                    self.story.append(Spacer(1, 2))
                    self.story.append(Paragraph(_md(rest), self.styles["body"]))
            else:
                self.story.append(Paragraph(_md(chunk), self.styles["body"]))
            if i < len(chunks) - 1:
                self.story.append(Spacer(1, 8))

    def quote(self, text):
        self.story.append(Paragraph(_md(text), self.styles["quote"]))

    def mini_toc(self, labels, color=None):
        """2026-08-24 신설 — 챕터 맨 위에 "이 챕터에서 다루는 것"을 짧게 미리 보여주는
        칩 목록(사용자 요청: "글만 있기보다 이해를 돕는 도구를 여러 개 써달라"). body()가
        인식하는 "## 소제목"을 그대로 재사용해서 만들므로 새 데이터ㆍ환각 위험이 없다."""
        if not labels:
            return
        col = color or ACCENT
        text = " · ".join(_xml_escape(_strip_unsupported(lb)) for lb in labels)
        cell = [Paragraph("이 챕터에서 다루는 것", ParagraphStyle(
            "toc_label", fontName=BOLD, fontSize=8.5, leading=11, textColor=col)),
            Paragraph(f"<b>{text}</b>", ParagraphStyle(
                "toc_chips", fontName=BOLD, fontSize=10, leading=15, textColor=TEXT_DARK))]
        t = Table([[cell]], colWidths=[164 * mm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f5f3fb")),
            ("LEFTPADDING", (0, 0), (-1, -1), 13), ("RIGHTPADDING", (0, 0), (-1, -1), 13),
            ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("ROUNDEDCORNERS", [8, 8, 8, 8]),
        ]))
        self.story.append(t)
        self.story.append(Spacer(1, 10))

    def spacer(self, h=8):
        self.story.append(Spacer(1, h))

    # ---------- 파트/챕터 헤더 ----------
    def part_page(self, label, title, desc=""):
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

    def chapter_header(self, num, title, eyebrow="CHAPTER", accent=None, accent2=None):
        """accent/accent2를 넘기면 배지ㆍ강조선 색을 바꿀 수 있음 — 천지인운명관은 체계별로
        (사주=주황ㆍ별자리=보라ㆍ타로=초록) 다른 색을 씀(report_kit.py의 SYSTEM_ACCENT 참고)."""
        badge_color = accent or ACCENT
        line_color = accent2 or ACCENT2
        eyebrow_style = self.styles["eyebrow"]
        if accent:
            eyebrow_style = ParagraphStyle("eyebrow_c", parent=eyebrow_style, textColor=badge_color)
        badge = Table([[Paragraph(f"{num:02d}", self.styles["chnum_badge"])]],
                      colWidths=[15 * mm], rowHeights=[15 * mm])
        badge.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), badge_color),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ROUNDEDCORNERS", [5, 5, 5, 5]),
        ]))
        head = [Paragraph(eyebrow, eyebrow_style), Paragraph(_xml_escape(_strip_unsupported(title)), self.styles["chapter_title"])]
        ghost = Paragraph(f"{num:02d}", self.styles["chnum_ghost"])
        t = Table([[badge, head, ghost]], colWidths=[19 * mm, 120 * mm, 27 * mm])
        t.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (2, 0), (2, 0), "RIGHT"),
            ("LEFTPADDING", (1, 0), (1, 0), 10),
        ]))
        self.story.append(t)
        self.story.append(HRFlowable(width="22%", thickness=2.2, color=line_color, spaceBefore=8, spaceAfter=12, hAlign="LEFT"))

    # ---------- 색상별 박스 ----------
    def _colored_box(self, header, items, bg, bar, icon, number=None):
        """2026-08-24 리디자인 — 경쟁사(운명도감) 디자인 벤치마킹(사용자 지시: 내용은
        가져오지 않고 레이아웃만 참고). 예전엔 "1. 제목"처럼 번호가 텍스트로 붙어있었는데,
        번호를 흰 글자의 색칠된 원형 배지로 분리해서 더 고급스럽게 보이도록 함."""
        if number is not None:
            badge = Table([[Paragraph(str(number), ParagraphStyle(
                "badge_num", fontName=XB, fontSize=11, leading=13, textColor=colors.white,
                alignment=TA_CENTER))]], colWidths=[8 * mm], rowHeights=[8 * mm])
            badge.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), bar),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROUNDEDCORNERS", [4, 4, 4, 4]),
            ]))
            head = Table([[badge, Paragraph(header, ParagraphStyle(
                "bh", fontName=BOLD, fontSize=10.8, leading=14, textColor=TEXT_DARK))]],
                colWidths=[10 * mm, 154 * mm])
            head.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]))
            rows = [[head]]
        else:
            rows = [[Paragraph(f"{icon} {header}", ParagraphStyle(
                "bh", fontName=BOLD, fontSize=10.3, leading=14, textColor=bar))]]
        for it in items:
            rows.append([Paragraph("• " + _md(it), self.styles["box_body"])])
        t = Table(rows, colWidths=[164 * mm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), bg),
            ("LINEBEFORE", (0, 0), (0, -1), 3, bar),
            ("LEFTPADDING", (0, 0), (-1, -1), 14), ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ("TOPPADDING", (0, 0), (-1, -1), 9), ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (0, 0), 6),
            ("BOX", (0, 0), (-1, -1), 0.6, bar),
            ("ROUNDEDCORNERS", [9, 9, 9, 9]),
        ]))
        self.story.append(t)
        self.story.append(Spacer(1, 12))

    def tip_box(self, items, header="TIP", number=None):
        self._colored_box(header, items, TIP_BG, TIP_BAR, "✓", number=number)

    def warn_box(self, items, header="주의", number=None):
        self._colored_box(header, items, WARN_BG, WARN_BAR, "⚠", number=number)

    def callout_box(self, title_text, items, numbered=False):
        rows = [[Paragraph(f"<b>{title_text}</b>", ParagraphStyle(
            "boxhead", fontName=BOLD, fontSize=11, leading=15, textColor=colors.white))]]
        for i, item in enumerate(items, 1):
            prefix = f"{i}. " if numbered else "ㆍ  "
            rows.append([Paragraph(prefix + _md(item), self.styles["box_body"])])
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
            rows.append([Paragraph(f"{i}. " + _md(it), self.styles["summary_body"])])
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

    # ---------- 인포그래픽 컴포넌트 ----------
    def stat_hero(self, number, label, sublabel=None):
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

    def four_pillars(self, items):
        """2026-08-24 신설 — 경쟁사(운명도감) 실제 리포트 디자인을 참고해 추가(사용자 지시:
        "내용 말고 디자인을 보라" — 그쪽의 근거 없는 통계·확정적 예언 문구는 가져오지 않고,
        네 기둥을 카드로 시각화하는 레이아웃만 차용함). 지금까지는 사주 네 기둥(년ㆍ월ㆍ일ㆍ
        시주)이 본문 산문 속에서만 언급되고 한눈에 보이는 표가 전혀 없었다 — 리포트를 열자마자
        "이 사람의 사주"를 시각적으로 각인시키는 element가 빠져 있던 것.
        @param items: [{"label": "년주", "text": "갑술", "sub": "목·토", "color": Color}, ...]
        """
        n = len(items)
        w = 164 / n
        cells = []
        for it in items:
            color = it.get("color") or ACCENT
            cell_style = ParagraphStyle("fp_text", fontName=XB, fontSize=22, leading=26,
                                         textColor=color, alignment=TA_CENTER)
            label_style = ParagraphStyle("fp_label", fontName=BOLD, fontSize=9, leading=13,
                                          textColor=TEXT_DIM, alignment=TA_CENTER)
            sub_style = ParagraphStyle("fp_sub", fontName=REG, fontSize=8.5, leading=12,
                                        textColor=TEXT_DIM, alignment=TA_CENTER)
            col = [Paragraph(it["label"], label_style), Spacer(1, 3),
                   Paragraph(it["text"], cell_style)]
            if it.get("sub"):
                col += [Spacer(1, 2), Paragraph(it["sub"], sub_style)]
            cells.append(col)
        row = Table([cells], colWidths=[w * mm] * n)
        row.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#faf9fc")),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 14), ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
            ("BOX", (0, 0), (-1, -1), 0.8, BORDER),
            ("LINEAFTER", (0, 0), (-2, -1), 0.7, BORDER),
            ("ROUNDEDCORNERS", [10, 10, 10, 10]),
        ]))
        self.story.append(row)
        self.story.append(Spacer(1, 12))

    def pull_quote(self, text, attribution=None):
        cell = [Paragraph("“", self.styles["pull_mark"]), Paragraph(_md(text), self.styles["pull_text"])]
        if attribution:
            cell.append(Paragraph(_xml_escape(_strip_unsupported(attribution)), self.styles["pull_attr"]))
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
        """2026-08-24 리디자인 — 예전엔 빈 여백 위에 색칠된 사각형 하나만 떠 있어서 "허접해
        보인다"는 지적을 받음(사용자 피드백). 실제 값 비율이 얼마인지 한눈에 안 보이는 게
        문제였음 — 항상 전체 길이를 채우는 옅은 회색 트랙을 깔고, 그 위에 실제 값만큼만
        진한 색으로 채워서 "게이지"처럼 보이게 바꿈. 둥근 모서리로 완성도를 높임.

        2026-08-24(2차) — "1개(12%)"처럼 개수와 퍼센트를 같이 보여줬는데, 사용자 지적:
        "갯수로 뭘 세는거지? 퍼센트로 충분하지 않나? 쓸데없는 걸 없애는 것도 퀄리티다."
        원본 개수(value/unit)는 막대 길이 계산에는 계속 쓰지만, 화면에는 퍼센트만 보여준다
        (정보가 많다고 고급스러운 게 아니라, 필요 없는 숫자를 빼는 것도 디자인이라는 지적을
        그대로 반영)."""
        track_w = 150 - label_w - 30
        pct = value / max_value if max_value else 0
        fill_w = max(2, pct * track_w)
        empty_w = max(0.01, track_w - fill_w)

        fill_cell = Table([[""]], colWidths=[fill_w * mm], rowHeights=[7 * mm])
        fill_cell.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), color),
            ("ROUNDEDCORNERS", [4, 4, 4, 4]),
        ]))
        empty_cell = Table([[""]], colWidths=[empty_w * mm], rowHeights=[7 * mm])
        empty_cell.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#eef0f5")),
        ]))
        gauge = Table([[fill_cell, empty_cell]], colWidths=[fill_w * mm, empty_w * mm])
        gauge.setStyle(TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))

        value_para = Paragraph(f'<b>{round(pct * 100)}%</b>', self.styles["table_cell"])
        row = Table([[Paragraph(f"<b>{label}</b>", self.styles["table_cell"]), gauge, value_para]],
                    colWidths=[label_w * mm, track_w * mm, 30 * mm])
        row.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
        self.story.append(row)
        self.story.append(Spacer(1, 5))

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

    # ---------- 이미지 그리드 페이지 / 인라인 이미지 (2026-08-29 신설, 공용) ----------
    def image_grid_page(self, items, page_title=None):
        """이미지 여러 개를 그리드로 크게 보여준다(예: 타로 카드 공개).
        items: [{"path": str, "caption": str}, ...]. 특정 상품 전용 로직은 여기 넣지
        않는다 — 호출 쪽(report_kit.py)이 items만 준비해서 넘긴다.

        2026-08-29 두 번 수정된 이력 — 처음엔 시작ㆍ끝 둘 다 PageBreak()로 강제 넘겼더니
        바로 앞 내용(챕터 제목 등)이 반 페이지만 쓰고 나머지가 비는 사고가 났고, 그
        다음엔 "그리드보다 먼저 챕터 제목을 보여준다"는 이 문서 전체의 일관된 순서 자체를
        깨는 땜질을 시도했다가(사용자가 바로 반려) 되돌렸다. **진짜 원칙에 맞는 해법은
        무조건 새 페이지가 아니라, 지금 페이지에 이 그리드가 들어갈 공간이 없을 때만 새
        페이지로 넘기는 것**(reportlab의 CondPageBreak) — 순서는 그대로 유지하면서 빈
        공간만 없앤다."""
        n = len(items)
        cols = 2 if n <= 4 else (3 if n <= 9 else 5)
        col_w = (170 * mm) / cols
        rows_data, row_heights, row, row_max_h = [], [], [], 0
        for i, item in enumerate(items):
            with PILImage.open(item["path"]) as im:
                w, h = im.size
            ratio = h / w
            img_w = col_w - 6 * mm
            img_h = img_w * ratio
            img = Image(item["path"], width=img_w, height=img_h)
            cap = Paragraph(item["caption"], self.styles["caption"])
            cell = Table([[img], [cap]], colWidths=[img_w])
            cell.setStyle(TableStyle([
                ("BOX", (0, 0), (0, 0), 0.8, BORDER),
                ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]))
            row.append(cell)
            row_max_h = max(row_max_h, img_h + 22)  # 캡션(대략 2줄)ㆍ패딩 여유분
            if len(row) == cols or i == n - 1:
                while len(row) < cols:
                    row.append("")
                rows_data.append(row)
                row_heights.append(row_max_h)
                row, row_max_h = [], 0
        grid = Table(rows_data, colWidths=[col_w] * cols)
        grid.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"), ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        total_h = sum(row_heights) + (24 if page_title else 0)
        self.story.append(CondPageBreak(total_h))
        if page_title:
            self.story.append(Paragraph(page_title, self.styles["h1"]))
            self.story.append(Spacer(1, 14))
        self.story.append(grid)
        self.story.append(Spacer(1, 10))

    def inline_image(self, path, caption, max_width_mm=42):
        """본문 문단 사이에 작게 끼워 넣는 이미지 — screenshot()과 같은 모양이지만 크기가
        작고 캡션이 짧다(카드 한 장 같은 보조 이미지용). image_grid_page()로 이미 크게
        보여준 것과 "같은 그림"이라는 걸 바로 알아볼 수 있을 정도의 크기로 설계."""
        with PILImage.open(path) as im:
            w, h = im.size
        ratio = h / w
        img_w = max_width_mm * mm
        img = Image(path, width=img_w, height=img_w * ratio)
        cap = Paragraph(caption, self.styles["caption"])
        box = Table([[img], [cap]], colWidths=[img_w])
        box.setStyle(TableStyle([
            ("BOX", (0, 0), (0, 0), 0.8, BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]))
        self.story.append(Spacer(1, 4))
        self.story.append(KeepTogether(box))
        self.story.append(Spacer(1, 6))

    # ---------- 빌드 ----------
    def build(self, footer_tagline=None, watermark_text="천지인운명관 · 무단 전재·재배포 금지", logo_path=None):
        if footer_tagline:
            self.story.append(Spacer(1, 20))
            self.story.append(HRFlowable(width="100%", thickness=0.7, color=BORDER, spaceAfter=10))
            self.story.append(Paragraph(footer_tagline, self.styles["small"]))

        def draw_watermark(canvas, dark_bg=False):
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
            """2026-08-24 재작성 — 사용자 지적: "코너에 흩어진 색깔 원 장식이 전형적인
            템플릿 느낌을 준다, 서비스허브 같아 보인다." 근거 없이 3원 겹침 마크를
            "브랜드 정체성"이라고 단정했던 것도 사용자가 직접 정정함(실제로 준 자료는
            로고 이미지였음). 그래서 장식용 원들은 전부 빼고, 짙은 남색 배경 + 진짜
            로고 이미지 하나만 남긴다 — 뭘 상징하는지 불분명한 장식보다, 실제 브랜드
            자산 하나가 훨씬 고급스럽고 확실하다는 판단.

            2026-08-24 추가 수정 — 사용자 지시: "사이트 색상을 보고 표지도 비슷하게
            만들자, 그라데이션(번지는 느낌)이 고급스러워 보인다." crossnotics.css가
            배경 전체에 까는 옅은 radial-gradient 번짐(보라·초록·주황)과 프리미엄
            버튼의 gold→accent 그라디언트를 PDF 캔버스 네이티브 셰이딩
            (canvas.radialGradient/linearGradient, PDF axial/radial shading 연산자)
            으로 재현함. extend=False로 그려서 반경 밖은 그대로 배경색이 비치게 해
            CSS의 'transparent' 스톱과 같은 효과를 냄.

            2026-08-24 재조정 — 첫 시도는 SITE_PURPLE/SITE_TEAL/GOLD 원색을 중심점에
            그대로 써서 반원이 진한 색 덩어리로 보였음(PDF 셰이딩은 CSS처럼 중심에서부터
            알파를 낮게 시작하지 못함 — 알파 대신 배경색과 미리 섞은(mix) 색을 씀).
            사이트 CSS도 실제로는 rgba(...,0.10~0.16) 수준의 아주 옅은 색이라 원색이
            아님 — 그 비율(10~26%)만큼 COVER_BASE와 섞어 옅은 '번짐'만 남김."""
            w, h = A4

            def _mix(base, tint, t):
                r = int(base[0] + (tint[0] - base[0]) * t)
                g = int(base[1] + (tint[1] - base[1]) * t)
                b = int(base[2] + (tint[2] - base[2]) * t)
                return colors.Color(r / 255, g / 255, b / 255)

            base_rgb = (0x10, 0x0e, 0x1c)
            purple_bloom = _mix(base_rgb, (0xa6, 0x8a, 0xff), 0.18)
            teal_bloom = _mix(base_rgb, (0x2f, 0xd7, 0xa3), 0.12)
            gold_bloom = _mix(base_rgb, (0xdc, 0xb9, 0x72), 0.26)

            canvas.saveState()
            canvas.setFillColor(COVER_BASE)
            canvas.rect(0, 0, w, h, stroke=0, fill=1)
            canvas.radialGradient(w * 0.08, h * 1.0, 120 * mm, [purple_bloom, COVER_BASE], [0, 1], extend=False)
            canvas.radialGradient(w * 0.98, h * 0.96, 85 * mm, [teal_bloom, COVER_BASE], [0, 1], extend=False)
            canvas.radialGradient(w * 0.5, h * 0.06, 150 * mm, [gold_bloom, COVER_BASE], [0, 1], extend=False)
            canvas.restoreState()
            # 2026-08-24 — 하단 gold→보라 그라디언트 바 삭제(사용자: "저게 뭔지 모르겠다,
            # 없애라" — 설명 없이 화면 아래를 가로지르는 띠라 의미가 안 읽혔음).

        def draw_logo(canvas):
            """logo_path가 주어졌을 때만 호출 — 사용자가 실제로 제공한 로고 이미지
            (짙은 남색+금색 원형 문장, crossnotics/apple-touch-icon.png와 동일 자산)를
            표지 하단에 원형 그대로 그린다. PNG 자체가 원형 바깥이 투명이라 별도
            마스킹 없이 배경과 자연스럽게 어우러짐."""
            w, h = A4
            size = 62 * mm
            x = (w - size) / 2
            y = 42 * mm
            canvas.saveState()
            canvas.drawImage(logo_path, x, y, width=size, height=size, mask="auto")
            canvas.restoreState()

        def draw_page_frame(canvas, dark_bg=False):
            """2026-08-24 신설 — 경쟁사(운명도감) 디자인 벤치마킹(사용자 지시: 내용은
            가져오지 않고 레이아웃만 참고). 페이지마다 여백에 둥근 테두리를 그려 "증서ㆍ
            고급 인쇄물" 같은 느낌을 준다 — 본문 여백(22~24mm)보다 안쪽(9mm)에 그려서
            텍스트와 절대 겹치지 않음.

            2026-08-24 수정 — 사용자 지시: "본문 테두리는 황금색으로." 사이트 CSS의
            --gold-line(rgba(220,185,114,0.35))과 같은 저채도 반투명 금색을 그대로
            씀 — 진하게 칠하면 본문 텍스트보다 시선을 끌어 가독성을 해치므로 알파를
            낮게 유지."""
            canvas.saveState()
            margin = 9 * mm
            w, h = A4
            canvas.setStrokeColor(GOLD)
            try:
                canvas.setStrokeAlpha(0.55 if dark_bg else 0.4)
            except AttributeError:
                pass
            canvas.setLineWidth(1.1)
            canvas.roundRect(margin, margin, w - 2 * margin, h - 2 * margin, 9, stroke=1, fill=0)
            canvas.restoreState()

        def on_cover(canvas, doc_):
            draw_cover_art(canvas)
            if logo_path:
                draw_logo(canvas)
            if watermark_text:
                draw_watermark(canvas, dark_bg=True)
            draw_page_frame(canvas, dark_bg=True)

        def draw_page_wash(canvas):
            """2026-08-24 신설 — 사용자가 준 디자인 가이드("premium_pdf_workflow_guide.pdf")
            2번 원칙: "순백색ㆍ순흑색 조합은 문서의 품격을 떨어뜨린다ㆍ저채도 미색 배경을
            써라." 순백색 배경 대신 아주 옅은 미색(따뜻한 아이보리)으로 전체 깔아, 눈의
            피로를 줄이고 고급 인쇄물 같은 질감을 준다(기존 보라/주황 브랜드 컬러는 그대로
            유지 — 배경 톤만 조정, 브랜드 정체성은 바꾸지 않음)."""
            canvas.saveState()
            canvas.setFillColor(colors.HexColor("#fdfbf5"))
            canvas.rect(0, 0, A4[0], A4[1], stroke=0, fill=1)
            canvas.restoreState()

        def draw_logo_watermark(canvas):
            """2026-08-24 신설 — 사용자 지시: "본문에 우리 로고를 투명하게 해서
            워터마크처럼 중간중간에 넣어, 단 가독성이 떨어지지 않게." 기존 텍스트
            워터마크(draw_watermark)처럼 촘촘한 격자로 깔면 로고는 글자보다 시각적
            밀도가 높아 본문과 겹쳐 읽기 힘들어짐 — 그래서 페이지 3곳에만, 아주 낮은
            불투명도로 크게 배치(문자 그대로 "중간중간에"). 텍스트 워터마크(저작권
            문구)는 그대로 유지하고 로고는 그 위에 얹는 방식."""
            if not logo_path:
                return
            w, h = A4
            size = 100 * mm
            canvas.saveState()
            try:
                canvas.setFillAlpha(0.07)
            except AttributeError:
                pass
            for x, y in (
                (w - size * 0.5, h - size * 0.55),
                (-size * 0.4, h * 0.30),
                (w * 0.55, -size * 0.42),
            ):
                canvas.drawImage(logo_path, x, y, width=size, height=size, mask="auto")
            canvas.restoreState()

        def add_page_number(canvas, doc_):
            draw_page_wash(canvas)
            draw_logo_watermark(canvas)
            if watermark_text:
                draw_watermark(canvas, dark_bg=False)
            draw_page_frame(canvas)
            canvas.saveState()
            canvas.setFont(REG, 9)
            canvas.setFillColor(TEXT_DIM)
            canvas.drawCentredString(A4[0] / 2, 13 * mm, str(doc_.page))
            canvas.restoreState()

        self.doc.build(self.story, onFirstPage=on_cover, onLaterPages=add_page_number)
        print("done:", self.out_path)
