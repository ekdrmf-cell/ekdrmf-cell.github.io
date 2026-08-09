# -*- coding: utf-8 -*-
"""전자책 만들어 팔기 실전 가이드 PDF 빌드 스크립트.

gov-subsidy-guide/build_pdf.py의 검증된 패턴을 그대로 재사용한다:
- 강제 PageBreak 금지(표지 뒤 1번만 예외) — 콘텐츠 흐름만으로 자연스럽게 페이지가 나뉘게 함
- 가운뎃점은 "·"(U+00B7, HYGothic-Medium 미지원) 대신 "ㆍ"(U+318D) 사용
- 빈칸 워크시트ㆍ자가진단 체크리스트 금지 — 전부 이미 채워진 정보로만 구성
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
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from PIL import Image as PILImage

FONT = "HYGothic-Medium"
pdfmetrics.registerFont(UnicodeCIDFont(FONT))

BASE_DIR = Path(r"C:\Users\nalla\Desktop\수익화허브\products\ebook-writing-guide")
SHOT_DIR = BASE_DIR / "screenshots"

ACCENT = colors.HexColor("#5a3fd6")
ACCENT_SOFT = colors.HexColor("#efeafc")
TEXT_DARK = colors.HexColor("#1f2333")
TEXT_DIM = colors.HexColor("#4d5268")
BORDER = colors.HexColor("#d9d5f0")

OUT = str(BASE_DIR / "전자책_만들어_팔기_가이드.pdf")

doc = SimpleDocTemplate(
    OUT, pagesize=A4,
    topMargin=24 * mm, bottomMargin=24 * mm,
    leftMargin=22 * mm, rightMargin=22 * mm,
    title="전자책 만들어 팔기 실전 가이드",
    author="수익화허브",
)

styles = {
    "title": ParagraphStyle("title", fontName=FONT, fontSize=27, leading=36,
                             textColor=TEXT_DARK, alignment=TA_CENTER, spaceAfter=10),
    "subtitle": ParagraphStyle("subtitle", fontName=FONT, fontSize=13.5, leading=20,
                                textColor=TEXT_DIM, alignment=TA_CENTER, spaceAfter=4),
    "cover_meta": ParagraphStyle("cover_meta", fontName=FONT, fontSize=11, leading=17,
                                  textColor=TEXT_DIM, alignment=TA_CENTER),
    "part_desc_std": ParagraphStyle("part_desc_std", fontName=FONT, fontSize=11.5, leading=19,
                                     textColor=TEXT_DIM, alignment=TA_CENTER),
    "h1": ParagraphStyle("h1", fontName=FONT, fontSize=19, leading=26,
                          textColor=ACCENT, spaceBefore=8, spaceAfter=12),
    "h2": ParagraphStyle("h2", fontName=FONT, fontSize=14.5, leading=21,
                          textColor=TEXT_DARK, spaceBefore=16, spaceAfter=8),
    "body": ParagraphStyle("body", fontName=FONT, fontSize=12.2, leading=21,
                            textColor=TEXT_DARK, spaceAfter=12, alignment=TA_LEFT),
    "quote": ParagraphStyle("quote", fontName=FONT, fontSize=12.5, leading=20,
                             textColor=ACCENT, alignment=TA_LEFT, spaceBefore=6, spaceAfter=10,
                             leftIndent=10, backColor=ACCENT_SOFT, borderPadding=12),
    "small": ParagraphStyle("small", fontName=FONT, fontSize=9.5, leading=15,
                             textColor=TEXT_DIM, spaceAfter=4),
    "caption": ParagraphStyle("caption", fontName=FONT, fontSize=9.5, leading=14,
                               textColor=TEXT_DIM, alignment=TA_CENTER, spaceBefore=4, spaceAfter=14),
    "toc": ParagraphStyle("toc", fontName=FONT, fontSize=12.5, leading=24,
                           textColor=TEXT_DARK, alignment=TA_LEFT),
    "toc_part": ParagraphStyle("toc_part", fontName=FONT, fontSize=13.5, leading=26,
                                textColor=ACCENT, alignment=TA_LEFT),
    "table_cell": ParagraphStyle("table_cell", fontName=FONT, fontSize=10.5, leading=15,
                                  textColor=TEXT_DARK),
    "table_head": ParagraphStyle("table_head", fontName=FONT, fontSize=10.5, leading=15,
                                  textColor=colors.white),
}

story = []

# ---------- 표지 ----------
story.append(Spacer(1, 46 * mm))
story.append(Paragraph("부업으로 시작하는 디지털 콘텐츠 판매", styles["subtitle"]))
story.append(Paragraph("전자책 만들어 팔기", styles["title"]))
story.append(Spacer(1, 6))
story.append(HRFlowable(width="26%", thickness=1.4, color=ACCENT, hAlign="CENTER", spaceBefore=8, spaceAfter=16))
story.append(Paragraph("주제 정하기부터 집필ㆍ디자인ㆍ플랫폼 등록ㆍ마케팅까지<br/>처음 시작하는 사람을 위한 실전 안내서", styles["cover_meta"]))
story.append(Spacer(1, 68 * mm))
story.append(Paragraph("데이터로 검증된 빈틈만 골라 만듭니다", styles["cover_meta"]))
story.append(PageBreak())


# ---------- 헬퍼 ----------
def h1(text):
    story.append(Paragraph(text, styles["h1"]))
    story.append(HRFlowable(width="100%", thickness=0.7, color=BORDER, spaceAfter=12))


def h2(text):
    story.append(Paragraph(text, styles["h2"]))


def body(text):
    story.append(Paragraph(text, styles["body"]))


def quote(text):
    story.append(Paragraph(text, styles["quote"]))


def part_page(label, title, desc):
    label_style = ParagraphStyle("banner_label", fontName=FONT, fontSize=10, leading=14,
                                  textColor=colors.HexColor("#e3daf9"), spaceAfter=3)
    title_style = ParagraphStyle("banner_title", fontName=FONT, fontSize=19, leading=25,
                                  textColor=colors.white, spaceAfter=(4 if desc else 0))
    desc_style = ParagraphStyle("banner_desc", fontName=FONT, fontSize=10, leading=15,
                                 textColor=colors.HexColor("#e3daf9"))
    cell = [Paragraph(label, label_style), Paragraph(title, title_style)]
    if desc:
        cell.append(Paragraph(desc, desc_style))
    banner = Table([[cell]], colWidths=[166 * mm])
    banner.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), ACCENT),
        ("TOPPADDING", (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ("LEFTPADDING", (0, 0), (-1, -1), 16),
        ("RIGHTPADDING", (0, 0), (-1, -1), 16),
    ]))
    story.append(banner)
    story.append(Spacer(1, 16))


def callout_box(title_text, items, numbered=False):
    rows = []
    header = Paragraph(f"<b>{title_text}</b>", ParagraphStyle(
        "boxhead", fontName=FONT, fontSize=11.5, leading=16, textColor=colors.white))
    rows.append([header])
    for i, item in enumerate(items, 1):
        prefix = f"{i}. " if numbered else "ㆍ  "
        rows.append([Paragraph(prefix + item, ParagraphStyle(
            "boxitem", fontName=FONT, fontSize=10.8, leading=17, textColor=TEXT_DARK))])
    t = Table(rows, colWidths=[166 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("BACKGROUND", (0, 1), (-1, -1), ACCENT_SOFT),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 13),
        ("RIGHTPADDING", (0, 0), (-1, -1), 13),
        ("TOPPADDING", (0, 1), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
        ("BOX", (0, 0), (-1, -1), 0.8, BORDER),
        ("LINEBELOW", (0, 0), (-1, 0), 0.8, BORDER),
    ]))
    story.append(t)
    story.append(Spacer(1, 14))


def site_box(name, url, desc, highlight=False):
    rows = [[Paragraph(f"<b>{name}</b>  <font color='#4d5268' size=9>{url}</font>", ParagraphStyle(
        "sitehead", fontName=FONT, fontSize=11.5, leading=16, textColor=ACCENT if highlight else TEXT_DARK)),],
        [Paragraph(desc, styles["body"])]]
    t = Table(rows, colWidths=[166 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#faf9ff") if not highlight else ACCENT_SOFT),
        ("BOX", (0, 0), (-1, -1), 0.8, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 13),
        ("RIGHTPADDING", (0, 0), (-1, -1), 13),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t)
    story.append(Spacer(1, 9))


def screenshot(filename, caption_text):
    path = SHOT_DIR / filename
    if not path.exists():
        body(f"<i>[화면 캡처 누락: {filename}]</i>")
        return
    with PILImage.open(path) as im:
        w, h = im.size
    max_w = 156 * mm
    ratio = h / w
    img = Image(str(path), width=max_w, height=max_w * ratio)
    box = Table([[img], [Paragraph(caption_text, styles["caption"])]], colWidths=[max_w])
    box.setStyle(TableStyle([
        ("BOX", (0, 0), (0, 0), 0.8, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(KeepTogether(box))
    story.append(Spacer(1, 6))


def toc_line(text, style="toc"):
    story.append(Paragraph(text, styles[style]))


def flow_diagram(steps):
    cells = []
    for i, step in enumerate(steps):
        cells.append(Paragraph(f"<b>{step}</b>", ParagraphStyle(
            f"flow{i}_{'-'.join(steps)[:4]}", fontName=FONT, fontSize=9.5, leading=13,
            textColor=colors.white, alignment=TA_CENTER)))
    row = [cells]
    widths = [166 / len(steps) * mm] * len(steps)
    t = Table(row, colWidths=widths, rowHeights=[16 * mm])
    style = [
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]
    shades = [ACCENT, colors.HexColor("#7457e0"), colors.HexColor("#8d6fea"),
              colors.HexColor("#a687f2"), colors.HexColor("#bfa0f7"), colors.HexColor("#d3bffa")]
    for i in range(len(steps)):
        style.append(("BACKGROUND", (i, 0), (i, 0), shades[i % len(shades)]))
    t.setStyle(TableStyle(style))
    story.append(t)
    story.append(Spacer(1, 10))


def bar_row(label, value, max_value, color, unit="", label_w=42):
    bar_width_mm = max(2, (value / max_value) * (150 - label_w - 24))
    bar = Table([[""]], colWidths=[bar_width_mm * mm], rowHeights=[6 * mm])
    bar.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), color)]))
    row = Table([[Paragraph(label, styles["table_cell"]), bar,
                  Paragraph(f"{value}{unit}", styles["table_cell"])]],
                colWidths=[label_w * mm, (150 - label_w - 24) * mm, 24 * mm])
    row.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    story.append(row)
    story.append(Spacer(1, 3))


def simple_table(header, rows, col_widths):
    data = [[Paragraph(str(c), styles["table_head"]) for c in header]]
    for r in rows:
        data.append([Paragraph(str(c), styles["table_cell"]) for c in r])
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#faf9ff")]),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(t)
    story.append(Spacer(1, 12))


# ============================================================
# 목차
# ============================================================
h1("목차")
toc_line("이 가이드는 누구를 위한 것인가", "toc")
story.append(Spacer(1, 8))
toc_line("1부. 5분 컷 — 오늘 바로 시작하는 법", "toc_part")
toc_line("1장. 전체 그림 한눈에 보기 ㆍ 2장. 5분 컷 체크리스트", "toc")
story.append(Spacer(1, 8))
toc_line("2부. 주제 정하기 — 팔리는 주제를 찾는 3가지 방법", "toc_part")
toc_line("3장. 플랫폼 베스트셀러로 수요 확인하기 ㆍ 4장. 검색량으로 확인하기", "toc")
toc_line("5장. 써도 되는 주제, 절대 안 되는 주제", "toc")
story.append(Spacer(1, 8))
toc_line("3부. 목차와 분량 설계", "toc_part")
toc_line("6장. 목차 짜는 법 ㆍ 7장. 분량은 결과이지 목표가 아니다", "toc")
story.append(Spacer(1, 8))
toc_line("4부. 집필 실전", "toc_part")
toc_line("8장. 자료조사 원칙 ㆍ 9장. 보조 도구로 AI 활용하기 ㆍ 10장. 쉬운 문장으로 쓰기", "toc")
story.append(Spacer(1, 8))
toc_line("5부. 디자인과 조판", "toc_part")
toc_line("11장. 표지 디자인 원칙 ㆍ 12장. 미리캔버스로 표지 만들기", "toc")
toc_line("13장. 무료 상업용 폰트 구하기 ㆍ 14장. 가독성 원칙과 PDF 내보내기", "toc")
story.append(Spacer(1, 8))
toc_line("6부. 이미지ㆍ스크린샷 안전하게 구하기", "toc_part")
story.append(Spacer(1, 8))
toc_line("7부. 플랫폼별 판매 방법과 수수료", "toc_part")
toc_line("16장. 크몽 ㆍ 17장. 탈잉 ㆍ 18장. 부크크(POD) ㆍ 19장. 유페이퍼", "toc")
toc_line("20장. 스마트스토어 ㆍ 21장. 플랫폼 비교표 총정리", "toc")
story.append(Spacer(1, 8))
toc_line("8부. 가격 책정 전략", "toc_part")
toc_line("9부. 마케팅과 후기 모으기", "toc_part")
toc_line("23장. 무료 체험판 만들기 ㆍ 24장. SNS 카드뉴스 ㆍ 25장. 후기 요청법", "toc")
story.append(Spacer(1, 8))
toc_line("10부. 세금 기초 상식", "toc_part")
toc_line("11부. 실전 사례 여섯 가지 유형", "toc_part")
toc_line("12부. 자주 하는 실수 열 가지", "toc_part")
toc_line("13부. 자주 묻는 질문(FAQ)", "toc_part")
toc_line("14부. 롱런 전략 — 시리즈화와 확장", "toc_part")
toc_line("15부. 처음부터 끝까지 — 하나의 가상 사례로 전체 과정 따라가기", "toc_part")
story.append(Spacer(1, 8))
toc_line("용어 사전", "toc_part")
toc_line("부록1. 플랫폼 수수료 총정리표 ㆍ 부록2. 좋은 제목 짓는 공식과 예시 20개", "toc")
toc_line("부록3. 표지ㆍ상세페이지 문구 모음 ㆍ 부록4. 참고 사이트 주소 모음", "toc")
toc_line("부록5. 찾아보기(색인) ㆍ 부록6. 실측 검증된 5대 카테고리와 세부 주제 50가지", "toc")
toc_line("부록7. 플랫폼별 등록 단계 비교 ㆍ 부록8. 출시 후 처음 석 달 확인할 숫자", "toc")
toc_line("부록9. 보너스 자료로 체감 가치 높이기", "toc")
toc_line("부록10. 자주 쓰는 축약어 풀이 ㆍ 부록11. 핵심 수치 한 장 요약", "toc")
toc_line("부록12. 이 가이드에서 언급한 법령 모음 ㆍ 부록13. 활용 순서 요약", "toc")
toc_line("부록14. 저자 소개 문구 쓰는 법 ㆍ 부록15. 자주 헷갈리는 표현 비교", "toc")

# ============================================================
# 서문
# ============================================================
h1("이 가이드는 누구를 위한 것인가")
body("이 가이드는 <b>자신이 알고 있는 것을 정리해서 전자책(PDF)으로 팔아보고 싶은 사람</b>을 위한 것입니다. 특정 분야의 자격증을 준비하며 얻은 요약노트가 있는 사람, 업무 툴 사용법을 잘 아는 사람, 특정 취미나 부업 노하우를 글로 정리할 수 있는 사람이라면 누구나 대상이 됩니다. 글쓰기를 직업으로 해본 적이 없어도 괜찮습니다.")
quote("&ldquo;뭘 써야 할지 모르겠다&rdquo;, &ldquo;다 만들어도 어디서 팔아야 할지 모르겠다&rdquo; — 이 두 가지 막막함을 순서대로 풀어드립니다.")
body("전자책 부업은 진입장벽이 낮아 보이지만, 실제로 해보면 <b>&ldquo;무엇을 쓸지&rdquo;, &ldquo;어떻게 보기 좋게 만들지&rdquo;, &ldquo;어디에 올려야 팔리는지&rdquo;</b> 세 가지 지점에서 대부분 막힙니다. 이 가이드는 이 세 가지를 순서대로, 실제 화면과 함께 정리했습니다.")
body("<b>1부</b>는 지금 당장 5분 안에 전체 그림을 파악할 수 있는 핵심 요약입니다. 바쁘면 1부만 읽고 시작해도 됩니다. <b>2부부터</b>는 주제 선정, 집필, 디자인, 플랫폼별 등록 방법, 마케팅, 세금까지 단계별로 필요할 때 펼쳐보는 참고자료입니다.")

callout_box("이 가이드가 아닌 것", [
    "&ldquo;하루 만에 월 천만원 번다&rdquo;는 식의 수익 보장이 아닙니다. 전자책 부업은 준비한 만큼, 그리고 주제가 시장 수요와 맞아떨어지는 만큼 결과가 갈리는 일입니다. 이 가이드는 그 확률을 최대한 높이는 방법을 정리한 것입니다.",
    "세무ㆍ법률 자문이 아닙니다. 세금ㆍ자격 관련 내용은 일반적인 절차를 설명하는 수준이며, 구체적인 판단은 국세청ㆍ세무사ㆍ해당 분야 주무기관에 확인해야 합니다.",
    "이 가이드에 실린 화면과 수수료ㆍ가격 정보는 모두 집필 시점(2026년 7월)에 실제로 접속ㆍ조사해서 정리한 것이며, 각 플랫폼의 정책은 수시로 바뀌므로 실제 등록 전에 반드시 해당 사이트에서 최신 내용을 다시 확인해야 합니다.",
])

# ============================================================
# 1부
# ============================================================
part_page("PART 1", "5분 컷 — 오늘 바로 시작하는 법", "바쁜 분들을 위한 핵심 요약입니다.<br/>이 1부만 읽어도 오늘 당장 주제를 정하고 목차를 짤 수 있습니다.")

h1("1장. 전체 그림 한눈에 보기")
body("전자책 한 권을 만들어서 파는 과정은 크게 다섯 단계로 나뉩니다. 순서를 건너뛰면 나중에 되돌아가는 일이 생기므로, 이 순서를 지키는 게 시간을 가장 아끼는 방법입니다.")
flow_diagram(["주제 정하기", "목차 설계", "집필", "디자인/조판", "플랫폼 등록ㆍ마케팅"])
body("각 단계에 걸리는 시간은 사람마다 다르지만, 이미 잘 아는 분야를 정리하는 경우를 기준으로 대략적인 감을 잡으면 다음과 같습니다.")
simple_table(
    ["단계", "보통 걸리는 시간", "핵심"],
    [
        ["주제 정하기", "1일~1주", "수요가 있는지 먼저 확인(2부)"],
        ["목차 설계", "1~2일", "5분컷+참고자료 2단 구조(3부)"],
        ["집필", "1~4주", "이미 아는 내용부터, 분량은 결과(4부)"],
        ["디자인/조판", "2~5일", "무료 도구로 충분(5ㆍ6부)"],
        ["등록ㆍ마케팅", "1일~계속", "플랫폼 선택과 후기 모으기(7~9부)"],
    ],
    [40 * mm, 46 * mm, 80 * mm],
)
body("전체적으로 보면 <b>&ldquo;써서 파는 데&rdquo;까지 짧으면 2주, 보통은 한 달 안팎</b>이 걸립니다. 완벽하게 준비된 다음에 시작하려고 하면 영영 시작하지 못하니, 이 가이드를 따라가면서 각 단계를 하나씩 끝내는 걸 목표로 삼으세요.")

h2("분량은 어느 부분에 더 써야 할까")
body("처음 목차를 짤 때 &ldquo;어느 부분에 힘을 더 줘야 할지&rdquo; 감이 안 잡힌다면, 아래 배분을 참고하세요. 실습형(스크린샷과 절차가 많은 주제)과 요약형(개념ㆍ암기 정보가 많은 주제) 중 자신의 주제에 가까운 쪽을 보면 됩니다.")
simple_table(
    ["구성 요소", "실습형 주제 권장 비중", "요약형 주제 권장 비중"],
    [
        ["핵심 요약(1부 역할)", "10%", "15%"],
        ["단계별 설명+스크린샷", "40%", "10%"],
        ["용어ㆍ개념 정리", "10%", "35%"],
        ["사례ㆍ응용", "20%", "20%"],
        ["FAQㆍ부록", "20%", "20%"],
    ],
    [52 * mm, 52 * mm, 52 * mm],
)
body("예를 들어 &ldquo;업무 툴 사용법&rdquo;처럼 실습형 주제라면 단계별 설명에 분량을 더 투자하고, &ldquo;자격증 요약노트&rdquo;처럼 요약형 주제라면 용어ㆍ개념 정리에 더 투자하는 식입니다.")

h1("2장. 5분 컷 체크리스트")
body("아래 다섯 가지 질문에 스스로 답해보면, 지금 당장 무엇부터 해야 할지 감이 잡힙니다.")
h2("Q1. 남들보다 조금이라도 더 잘 아는 게 있나요?")
callout_box("주제 후보가 될 수 있는 것들", [
    "취득한 자격증 준비 과정에서 만든 요약노트나 오답노트",
    "업무에서 매일 쓰는 툴(엑셀, 스프레드시트, 특정 소프트웨어) 사용법",
    "특정 플랫폼(쇼핑몰, SNS, 블로그)을 운영하며 익힌 절차와 요령",
    "특정 취미ㆍ분야를 오래 하면서 알게 된 정보 정리(장비 고르는 법, 용어 정리 등)",
])
h2("Q2. 그 주제로 이미 팔리고 있는 전자책이 있나요?")
body("있다면 오히려 좋은 신호입니다. 이미 사는 사람이 있다는 뜻이기 때문입니다(2부에서 실제로 확인하는 방법을 다룹니다). 없다면 수요 자체가 없을 가능성이 크므로 다른 주제를 고려하는 게 안전합니다.")
h2("Q3. 내가 직접 확인ㆍ정리할 수 있는 &lsquo;공개된 정보&rsquo;인가요?")
body("자격시험 기출문제, 공식 사이트 사용법, 플랫폼 정책처럼 <b>누구나 접근할 수 있는 정보를 체계적으로 정리하는 것</b>이 가장 안전하고 표준화하기 쉽습니다. 반대로 &ldquo;나만 아는 특별한 비법&rdquo;이나 검증 불가능한 개인 수익 실적을 앞세우는 주제는 피하세요(5장에서 자세히 다룹니다).")
h2("Q4. 어느 플랫폼에 올릴지 정했나요?")
body("주제에 따라 유리한 플랫폼이 다릅니다. 빠르게 감만 잡으려면 &ldquo;재능마켓형(크몽ㆍ탈잉)&rdquo;과 &ldquo;서점 유통형(부크크ㆍ유페이퍼)&rdquo; 중 어느 쪽이 내 주제와 어울리는지만 미리 생각해두세요. 자세한 비교는 7부에 있습니다.")
h2("Q5. 첫 버전은 완벽하지 않아도 된다는 걸 받아들였나요?")
body("첫 버전을 내놓고 나서 후기와 질문을 받아 계속 보완하는 쪽이, 완벽한 버전을 만들겠다고 미루는 쪽보다 훨씬 빨리 결과로 이어집니다. 여기까지 답했다면 2부로 넘어가서 실제로 주제를 검증해볼 차례입니다.")

# ============================================================
# 2부
# ============================================================
part_page("PART 2", "주제 정하기 — 팔리는 주제를 찾는 3가지 방법", "&ldquo;내가 쓰고 싶은 것&rdquo;이 아니라 &ldquo;사람들이 필요로 하는 것&rdquo;을<br/>먼저 확인하는 방법을 다룹니다.")

h1("3장. 플랫폼 베스트셀러로 수요 확인하기")
body("가장 확실한 수요 검증 방법은 <b>이미 그 주제로 팔리고 있는 상품이 있는지, 얼마나 많이 팔렸는지</b>를 직접 확인하는 것입니다. 크몽 같은 재능마켓은 각 서비스에 리뷰 수가 표시되므로, 리뷰 수를 &ldquo;누적 판매량의 대략적인 지표&rdquo;로 참고할 수 있습니다.")
screenshot("01_kmong_home.png", "크몽 첫 화면 — 업종별 카테고리 목록에 &ldquo;전자책&rdquo;이 별도 항목으로 있다")
body("첫 화면 아래쪽 업종별 카테고리에 <b>&ldquo;전자책&rdquo;</b>이 따로 있습니다. 여기를 눌러도 되고, 검색창에 관심 있는 키워드(예: &ldquo;OO자격증&rdquo;, &ldquo;엑셀&rdquo;, &ldquo;블로그&rdquo;)를 직접 입력해도 됩니다.")
screenshot("02_kmong_search_ebook.png", "&ldquo;전자책&rdquo;으로 검색한 화면 — 카테고리가 &ldquo;라이프 전자책&rdquo;, &ldquo;부업ㆍ수익화 전자책&rdquo;, &ldquo;취업ㆍ시험ㆍ자격증 전자책&rdquo;으로 세분화되어 있고, 정렬을 &ldquo;인기순&rdquo;ㆍ&ldquo;추천순&rdquo;ㆍ&ldquo;신규등록순&rdquo;으로 바꿔볼 수 있다")
body("검색 결과 화면 위쪽의 <b>추천 카테고리 태그</b>를 보면 크몽이 전자책을 어떤 큰 갈래로 나누는지 알 수 있습니다. 정렬 기준을 &ldquo;인기순&rdquo;으로 바꾸고, 관심 있는 주제와 가까운 상품들의 <b>리뷰 수와 가격</b>을 눈여겨보세요. 리뷰가 수백~수천 개인 상품이 있다면 그 주제군은 이미 검증된 수요가 있다는 뜻이고, 검색해도 거의 안 나온다면 수요 자체가 작거나 아직 개척되지 않은 영역이라는 뜻입니다.")
h2("실제로 확인해보면 좋은 대분류")
body("2026년 7월 기준으로 크몽 전자책 카테고리를 여러 세부 분야로 나눠 리뷰 수 상위 상품들을 살펴보면, 아래와 같은 계열이 특히 두터운 수요층을 갖고 있었습니다(특정 상품 하나가 아니라 계열 전체의 경향입니다).")
bar_row("자격증 요약형", 3246, 3246, colors.HexColor("#5a3fd6"), unit="리뷰", label_w=46)
bar_row("제작법 안내형", 1619, 3246, colors.HexColor("#7457e0"), unit="리뷰", label_w=46)
bar_row("블로그 수익화형", 1436, 3246, colors.HexColor("#8d6fea"), unit="리뷰", label_w=46)
bar_row("SNS 마케팅형", 619, 3246, colors.HexColor("#a687f2"), unit="리뷰", label_w=46)
bar_row("기술자격 요약형", 593, 3246, colors.HexColor("#bfa0f7"), unit="리뷰", label_w=46)
story.append(Spacer(1, 4))
body("<i>(각 계열의 대표 상품 리뷰 수, 2026년 7월 크몽 실측 기준 ㆍ 시점에 따라 순위와 수치는 계속 바뀝니다.)</i>")
body("이 그래프에서 볼 수 있듯, <b>&ldquo;자격증 시험 준비 요약노트&rdquo;와 &ldquo;돈 버는 방법을 정리해서 알려주는 제작법 안내형&rdquo;</b> 계열이 특히 두텁습니다. 자신의 경험이 이 두 계열 중 하나와 가깝다면 시작하기 유리한 편입니다.")
callout_box("크몽에서 주제 조사할 때 체크할 것", [
    "리뷰 수뿐 아니라 <b>리뷰 본문</b>도 몇 개 읽어보세요. &ldquo;이런 내용이 더 있었으면 좋겠다&rdquo;는 불만이 있다면, 그게 바로 내가 채울 수 있는 빈틈입니다.",
    "가격대도 함께 기록해두세요. 같은 계열 안에서도 1만원대부터 10만원대까지 다양하게 팔리고 있다면, 내용의 깊이에 따라 가격을 어떻게 다르게 매길 수 있는지 감이 잡힙니다.",
    "판매자가 한 명뿐인 &ldquo;독점 시장&rdquo;보다, 여러 판매자가 각자 다른 각도로 같은 주제를 파는 &ldquo;경쟁 시장&rdquo;이 오히려 안전합니다. 이미 여러 명이 팔고 있다는 건 그만큼 사는 사람이 꾸준하다는 뜻입니다.",
])

h1("3-2장. 경쟁 상품 비교표 만들기")
body("후보 주제를 하나로 좁혔다면, 그 주제로 이미 팔리고 있는 상품 3~5개를 골라 아래처럼 표로 정리해보세요. 이렇게 눈에 보이게 정리하면 &ldquo;내가 뭘 더 채워야 하는지&rdquo;가 명확해집니다. 아래는 가상의 예시입니다(실제 특정 판매자의 자료가 아닙니다).")
simple_table(
    ["상품", "가격", "리뷰수", "구성", "빈틈"],
    [
        ["예시 A", "39,000원", "412", "요약노트만", "실제 화면 없음"],
        ["예시 B", "59,000원", "88", "요약+문제풀이", "최신 개정 미반영"],
        ["예시 C", "29,000원", "205", "PDF 20p", "용어 설명 부족"],
    ],
    [26 * mm, 26 * mm, 22 * mm, 40 * mm, 52 * mm],
)
body("이 표를 만들어보면, 이 가상의 예시에서는 &ldquo;최신 정보 반영&rdquo;과 &ldquo;용어 설명을 충분히 곁들인 실제 화면 캡처&rdquo;라는 두 가지 빈틈이 동시에 보입니다. 내 상품을 기획할 때 이 두 가지를 확실히 채우면 그것만으로 차별점이 됩니다. 표의 항목(가격ㆍ리뷰수ㆍ구성ㆍ빈틈)은 그대로 가져다 써도 되고, 자신의 주제에 맞게 항목을 바꿔도 됩니다.")

h1("4장. 검색량으로 확인하기 — 네이버 데이터랩")
body("리뷰 수는 &ldquo;이미 팔리고 있는 상품&rdquo; 기준의 지표이고, 검색량은 &ldquo;사람들이 실제로 궁금해하는 정도&rdquo;를 보여주는 또 다른 지표입니다. 두 가지를 함께 보면 더 정확합니다.")
screenshot("09_datalab_trend.png", "네이버 데이터랩 검색어트렌드 화면 — 주제어를 입력하면 기간별 검색량 추이를 무료로 그래프로 보여준다")
body("<b>사용법</b>: 주제어 칸에 내가 다루려는 키워드(예: &ldquo;OO자격증&rdquo;, &ldquo;스마트스토어 시작하는법&rdquo;)와 관련어를 콤마로 구분해서 입력하고, 기간을 1년 정도로 설정한 뒤 조회하면 시간에 따라 검색량이 늘고 있는지 줄고 있는지 꺾은선 그래프로 보여줍니다.")
callout_box("데이터랩 결과 해석하는 법", [
    "그래프가 <b>꾸준히 우상향</b>한다면 지금 막 관심이 커지는 주제라는 뜻입니다 — 다만 아직 이 정보를 다루는 전자책이 적을 수 있으니 2부 3장의 크몽 검색과 함께 확인하세요.",
    "그래프에 <b>특정 시기마다 뾰족하게 튀는 구간</b>(계절성)이 있다면, 그 시기 직전에 맞춰 출시하는 게 유리합니다(예: 시험 관련 주제는 시험 접수 시작 시기 직전).",
    "그래프가 <b>평평하게 낮은 수준</b>이라면, 검색으로 유입될 여지가 적다는 뜻이므로 크몽 같은 재능마켓 내부 검색에 더 의존해야 할 수 있습니다.",
])

h1("4-2장. 커뮤니티에서 질문 모으기")
body("리뷰 수와 검색량이 &ldquo;이미 있는 수요&rdquo;를 보여준다면, 커뮤니티는 <b>아직 상품으로 안 만들어진 수요</b>를 찾는 곳입니다. 네이버 지식iN, 관련 주제의 오픈채팅ㆍ카페, 디시인사이드ㆍ블라인드 같은 커뮤니티에서 내 주제와 관련된 질문 게시글을 검색해보세요.")
callout_box("커뮤니티 조사 방법", [
    "네이버 지식iN에서 주제 키워드로 검색하면, 같은 질문이 반복해서 올라오는 걸 볼 수 있습니다. 반복되는 질문은 아직 명쾌하게 정리된 답이 없다는 뜻입니다.",
    "관련 오픈채팅방ㆍ카페의 &ldquo;질문&rdquo; 게시판을 최근 순으로 훑어보며, 사람들이 어떤 단어로 곤란함을 표현하는지 그대로 메모해두세요 — 이 표현이 나중에 상세페이지 문구(부록3)로 그대로 쓰입니다.",
    "질문에 달린 답변들이 서로 다르거나 부정확하다면, 그 자체가 &ldquo;정확하게 정리된 정보&rdquo;에 대한 수요가 있다는 신호입니다.",
])
body("이렇게 모은 질문들은 그대로 FAQ 챕터(13부)의 뼈대가 되기도 하고, 목차(3부)를 짤 때 &ldquo;독자가 실제로 궁금해하는 순서&rdquo;를 반영하는 데도 큰 도움이 됩니다.")

h1("5장. 써도 되는 주제, 절대 안 되는 주제")
body("전자책 주제를 두 가지로 나눠보면 무엇을 피해야 할지 훨씬 명확해집니다.")
callout_box("정보 구조화형 (권장)", [
    "공개된 정보ㆍ공식 절차ㆍ누구나 검증할 수 있는 지식을 <b>정리ㆍ요약ㆍ해설</b>하는 형태입니다.",
    "예: 자격시험 기출 요약, 공공 사이트ㆍ플랫폼 사용법, 업무 툴 활용법, 절차 안내, 용어 사전.",
    "글쓴이가 없어도 원래 존재하던 정보이므로, 정확하게만 정리하면 신뢰도와 법적 안전성이 모두 확보됩니다.",
])
callout_box("개인 실증형 — 신중하게 접근 (주의)", [
    "특정 개인의 검증 불가능한 실적(&ldquo;나는 이렇게 해서 월 OOO만원 벌었다&rdquo;)을 앞세우는 형태입니다.",
    "실제로 겪은 일이라도, 독자 입장에서는 사실 확인이 불가능하므로 과장된 주장이 섞이기 쉽고 신뢰를 잃기도 쉽습니다.",
    "이런 유형으로 쓰고 싶다면, 실제 데이터(스크린샷, 계산 근거)를 최대한 투명하게 함께 공개해서 검증 가능하게 만드세요.",
])
body("아래 분야는 <b>정보를 정리하는 것과 &ldquo;그 일을 대신 해주겠다&rdquo;는 것 사이의 경계</b>가 특히 중요한 분야입니다. 관련 법에서 특정 자격을 가진 사람만 할 수 있도록 정한 업무(대리ㆍ대행ㆍ자문 등)가 있기 때문입니다.")
callout_box("주제로 다룰 때 특히 조심해야 할 분야", [
    "세무ㆍ회계 — 세무사법상 세무 대리ㆍ자문은 세무사만 할 수 있습니다. &ldquo;일반적인 절차 설명&rdquo;까지는 괜찮지만, &ldquo;당신의 상황에서는 이렇게 신고하세요&rdquo;처럼 개별 자문으로 읽히는 표현은 피해야 합니다.",
    "법률 — 변호사법상 법률 상담ㆍ대리는 변호사만 할 수 있습니다. 판례ㆍ법 조항을 소개하는 것과 &ldquo;당신의 사건은 이렇게 진행하세요&rdquo;라고 조언하는 것은 다릅니다.",
    "의료ㆍ건강 — 의료법상 진단ㆍ처방ㆍ치료법 안내는 의료인만 할 수 있습니다. 건강 정보를 다루더라도 &ldquo;참고용&rdquo;임을 분명히 하고 진단ㆍ처방으로 읽히지 않게 써야 합니다.",
    "정부지원금ㆍ보조금 신청 대행 — 정보를 정리해서 알려주는 것은 괜찮지만, 수수료를 받고 신청 서류를 대신 작성ㆍ제출해주는 것은 보조금 관련 법과 충돌할 수 있습니다.",
    "투자ㆍ재테크 — 특정 종목ㆍ코인을 추천하며 수익을 보장하는 표현은 자본시장법상 유사투자자문업 규제와 맞닿아 있습니다. 일반적인 개념 설명과 &ldquo;투자 조언&rdquo;은 다릅니다.",
    "부동산 중개 — 공인중개사법상 중개 행위(특정 매물을 소개하고 계약을 알선하는 것)는 공인중개사만 할 수 있습니다. 부동산 세금ㆍ계약 절차를 &ldquo;일반적으로&rdquo; 설명하는 것과 &ldquo;이 매물을 이렇게 거래하라&rdquo;고 알선하는 것은 다릅니다.",
    "보험 — 보험업법상 보험 상품 모집ㆍ권유는 등록된 설계사ㆍ대리점만 할 수 있습니다. 보험 용어ㆍ제도를 설명하는 것과 특정 상품 가입을 권유하는 것은 구분해야 합니다.",
])
quote("한 문장으로 정리하면: <b>&ldquo;정보를 정리해서 보여주는 것&rdquo;은 안전하고, &ldquo;그 사람을 대신해서 판단ㆍ신청ㆍ진단해주는 것&rdquo;은 위험합니다.</b> 애매하면 &ldquo;이 내용은 정보 제공용이며, 실제 결정은 전문가와 상담하세요&rdquo;라는 문구를 넣는 습관을 들이세요.")

h1("5-3장. 애매할 때 판단하는 순서")
body("주제가 5장의 목록에 딱 들어맞지 않고 애매하게 느껴진다면, 아래 순서로 스스로 질문해보세요.")
flow_diagram(["공개된 정보인가?", "누구나 확인 가능한가?", "대신 결정해주는가?", "전문가 자격이 필요한가?"])
body("앞의 두 질문에 &ldquo;그렇다&rdquo;로 답하고, 뒤의 두 질문에 &ldquo;아니다&rdquo;로 답할 수 있다면 안전한 정보 구조화형입니다. 반대로 뒤쪽 질문 중 하나라도 &ldquo;그렇다&rdquo;에 가깝다면, 그 부분만 &ldquo;일반적인 절차 설명&rdquo; 수준으로 톤을 낮추거나, 아예 다른 주제로 방향을 바꾸는 게 안전합니다.")

# ============================================================
# 3부
# ============================================================
part_page("PART 3", "목차와 분량 설계", "쓰기 전에 뼈대부터 잡아야 나중에 헤매지 않습니다.")

h1("6장. 목차 짜는 법 — &ldquo;5분컷 + 참고자료&rdquo; 2단 구조")
body("이 가이드 자체가 쓰고 있는 구조이기도 합니다. 독자는 크게 두 부류로 나뉩니다. <b>지금 당장 급한 사람</b>과 <b>차근차근 다 알고 싶은 사람</b>입니다. 이 둘을 동시에 만족시키는 방법이 2단 구조입니다.")
callout_box("2단 구조 짜는 순서", [
    "1단계: 이 책 전체를 다 읽지 않고 &ldquo;딱 한 페이지만 본다면&rdquo; 무엇을 알려줘야 하는지 적어봅니다. 이게 1부(5분컷)가 됩니다.",
    "2단계: 나머지 세부 내용을 주제별로 묶어 2부부터 순서대로 배치합니다. 각 부는 사전처럼 &ldquo;필요할 때 펼쳐보는&rdquo; 구조로 만듭니다.",
    "3단계: 부와 부 사이에 자연스러운 순서(시간순, 난이도순, 자주 찾는 순)를 만들어서 처음부터 끝까지 읽어도 이야기가 이어지게 합니다.",
    "4단계: 마지막에 용어 사전과 부록(비교표, 체크리스트형이 아닌 정리표, 참고 링크)을 붙여 나중에 다시 찾아볼 수 있게 합니다.",
])
body("목차를 다 짜고 나면 각 장의 제목만 쭉 읽어봤을 때 &ldquo;이 순서대로 읽으면 처음부터 끝까지 할 수 있겠다&rdquo;는 느낌이 들어야 합니다. 그렇지 않다면 순서를 다시 조정하세요.")

h1("7장. 분량은 결과이지 목표가 아니다")
body("&ldquo;몇 페이지를 채워야 한다&rdquo;를 먼저 정해놓고 쓰면, 빈칸 워크시트나 의미 없는 여백으로 억지로 채우게 됩니다. 이렇게 만들어진 전자책은 구매자가 훑어보기만 해도 바로 티가 납니다.")
quote("페이지 수를 목표로 삼지 말고, <b>&ldquo;진짜 필요한 정보를 얼마나 깊이 있게 담았는가&rdquo;</b>를 목표로 삼으세요. 분량은 그 결과로 자연스럽게 따라옵니다.")
callout_box("분량이 자연스럽게 늘어나는 진짜 정보들", [
    "용어 사전 — 그 분야를 처음 접하는 사람이 헷갈릴 만한 단어를 최대한 많이 모아 설명",
    "비교표 — 여러 선택지(플랫폼, 방법, 도구)를 항목별로 나란히 비교",
    "실제 사례 — 여러 유형의 가상 사례를 만들어 상황별로 어떻게 적용되는지 보여주기",
    "스크린샷과 함께하는 단계별 설명 — &ldquo;말로 설명&rdquo;보다 훨씬 많은 분량과 신뢰를 동시에 얻는 방법",
    "자주 묻는 질문(FAQ) — 예상 독자가 실제로 궁금해할 질문을 최대한 모아 답하기",
])
body("반대로 <b>빈칸으로 된 워크시트, 예ㆍ아니오로만 답하는 자가진단표</b>는 페이지 수는 늘려주지만 &ldquo;정보를 제공&rdquo;하는 게 아니라 독자가 스스로 채워야 하는 미완성 콘텐츠로 보이기 쉽습니다. 이런 형식은 피하고, 위 목록처럼 <b>이미 채워진 지식</b>으로 분량을 쌓아가세요.")

# ============================================================
# 4부
# ============================================================
part_page("PART 4", "집필 실전", "자료조사부터 문장 쓰는 법까지, 처음 쓰는 사람이 막히는 지점을 다룹니다.")

h1("8장. 자료조사 원칙 — 1차 자료 우선")
body("전자책의 신뢰도는 &ldquo;얼마나 정확한 출처를 근거로 썼는가&rdquo;에서 크게 갈립니다. 자료를 찾을 때는 아래 순서를 지키세요.")
callout_box("자료 우선순위", [
    "1순위: 공식 기관ㆍ공식 사이트의 원문(정부기관, 시험 주관처, 플랫폼 공식 고객센터ㆍ도움말 페이지)",
    "2순위: 실제로 그 사이트ㆍ도구를 직접 써보고 얻은 경험(스크린샷으로 남기면서 진행)",
    "3순위: 신뢰할 수 있는 2차 해설(전문 블로그, 커뮤니티 노하우 글) — 단, 반드시 1순위 자료로 다시 한번 사실 확인",
])
body("특히 <b>가격ㆍ수수료ㆍ정책처럼 자주 바뀌는 정보</b>는 반드시 &ldquo;집필 시점 기준&rdquo;이라는 문구와 함께 표기하고, 조사한 날짜를 남겨두세요. 이렇게 해두면 나중에 정책이 바뀌어도 &ldquo;거짓 정보&rdquo;가 아니라 &ldquo;그 시점 기준 정보&rdquo;로 남아 신뢰를 지킬 수 있습니다.")

h1("8-2장. 출처 표기법과 인용 범위")
body("공개된 자료(공식 사이트, 통계, 기출문제, 법 조항)를 정리해서 쓰는 게 이 가이드가 권장하는 방식이지만, 그렇다고 남의 글을 그대로 옮겨 쓸 수는 없습니다. 저작권법은 <b>&ldquo;공표된 저작물을 정당한 범위 안에서 인용&rdquo;</b>하는 것은 허용하되, 그 정당한 범위를 넘어서면 침해가 된다고 봅니다.")
callout_box("실무적으로 지키면 안전한 선", [
    "다른 사람의 글을 그대로 옮길 때는 <b>따옴표와 출처</b>를 반드시 함께 표기하고, 옮긴 분량이 내 글 전체에서 아주 작은 비중이어야 합니다.",
    "통계ㆍ수치는 원 출처(기관명, 발표 시점)를 함께 적으세요. 예: &ldquo;(OO기관, 2026년 O월 발표 기준)&rdquo;.",
    "가장 안전한 방법은 <b>남의 표현을 그대로 옮기지 않고, 내가 이해한 내용을 내 문장으로 다시 쓰는 것</b>입니다. 사실관계는 같아도 표현이 다르면 저작권 문제에서 훨씬 자유롭습니다.",
    "법 조항ㆍ판례ㆍ공공기관 공고문처럼 저작권이 없거나 자유이용이 허용된 자료(대부분의 정부 공문서)는 비교적 자유롭게 인용할 수 있지만, 최신 버전인지는 매번 확인해야 합니다.",
])

h1("9장. 보조 도구로 AI 활용하기")
body("챗GPTㆍ클로드 같은 AI 대화형 도구는 <b>초안을 빠르게 뽑아보거나, 이미 쓴 글을 다듬거나, 목차 아이디어를 넓히는 보조 도구</b>로 유용합니다. 다만 아래 원칙을 지켜야 결과물의 질이 떨어지지 않습니다.")
callout_box("AI를 보조로 쓸 때 지켜야 할 것", [
    "AI가 만들어준 사실 정보(숫자, 절차, 날짜, 수수료 등)는 <b>반드시 1차 자료로 직접 재확인</b>하세요. AI는 그럴듯하지만 틀린 정보를 자신 있게 말할 때가 있습니다.",
    "AI가 쓴 문장을 그대로 붙여넣지 말고, 자신의 경험과 예시를 섞어 다시 쓰세요. 그래야 다른 사람의 전자책과 구분되는 &ldquo;자기 목소리&rdquo;가 생깁니다.",
    "AI에게 &ldquo;이 주제로 목차를 짜줘&rdquo;처럼 구조를 넓히는 질문은 유용하지만, &ldquo;이 주제로 전자책을 통째로 써줘&rdquo;처럼 완성본을 그대로 받으면 얕고 일반적인 내용이 되기 쉽습니다. 뼈대는 AI로 빠르게, 살은 직접 채우는 방식이 효율적입니다.",
        "다른 사람이 쓴 글이나 저작권이 있는 자료를 AI에게 그대로 베껴 쓰게 하지 마세요. 표절 문제는 AI를 썼든 안 썼든 똑같이 저자 책임입니다.",
])

h1("9-2장. 자료조사에 쓸 수 있는 질문 예시")
body("AI 도구에게 무엇을 물어야 할지 막막하다면, 아래 형식을 그대로 응용해보세요. 핵심은 <b>&ldquo;완성된 글&rdquo;이 아니라 &ldquo;확인해야 할 목록&rdquo;을 뽑아달라고 요청하는 것</b>입니다.")
callout_box("질문(프롬프트) 예시", [
    "&ldquo;[주제]를 처음 접하는 사람이 헷갈려 할 만한 용어 20개를 목록으로 뽑아줘. 각 용어는 내가 직접 정확한 뜻을 찾아 채울 것이므로 용어 이름만 필요해.&rdquo;",
    "&ldquo;[주제]에 대한 목차 초안을 3가지 다른 구조로 제안해줘. 각 구조의 장단점도 한 줄씩 알려줘.&rdquo;",
    "&ldquo;아래 내 문장을 더 쉬운 말로 다듬어줘. 단, 사실 정보는 바꾸지 말고 표현만 다듬어줘: [내 문장]&rdquo;",
    "&ldquo;[주제]를 처음 시작하는 사람이 실수하기 쉬운 부분이 뭐가 있을지 후보를 알려줘. 내가 실제 사례로 검증해서 쓸게.&rdquo;",
])
body("공통점은 <b>AI에게 최종 사실 판단을 맡기지 않고, &ldquo;후보를 넓히는 역할&rdquo;만 맡긴다</b>는 것입니다. 목록이 나오면 그중 실제로 맞는 것만 골라 1차 자료로 재확인(8장)한 뒤 쓰세요.")

h2("표절 여부 스스로 점검하기")
body("완성 후에는 자신의 글이 다른 자료를 너무 가깝게 따라가지 않았는지 스스로 점검하는 습관도 필요합니다. 온라인 표절 검사 서비스(예: 카피킬러 등)에 핵심 문단을 돌려보거나, 8-2장에서 참고한 원문과 내 문장을 나란히 놓고 직접 비교해보는 것만으로도 대부분의 위험은 걸러낼 수 있습니다.")

h1("10장. 쉬운 문장으로 쓰기")
body("전자책을 사는 사람은 대부분 그 분야를 <b>이제 막 알아가려는 초보자</b>입니다. 전문 용어를 아는 사람에게 파는 게 아니라, 모르는 사람이 알게 만들어주는 게 상품의 가치입니다.")
callout_box("문장을 쉽게 쓰는 방법", [
    "전문 용어가 처음 나올 때는 반드시 괄호나 다음 문장에서 바로 풀어서 설명하기",
    "한 문장에 하나의 정보만 담기 — 접속사로 두세 가지를 이어 붙이면 읽다가 놓치기 쉽습니다",
    "&ldquo;~할 수 있습니다&rdquo;, &ldquo;~하면 됩니다&rdquo;처럼 행동으로 끝나는 문장으로 마무리하기",
    "숫자ㆍ절차는 글 속에 녹이지 말고 목록이나 표로 따로 빼서 한눈에 보이게 하기",
    "다 쓴 뒤에는 그 분야를 전혀 모르는 지인에게 한두 페이지를 읽혀보고, 막히는 부분을 표시해달라고 부탁하기",
])

h1("10-1-2장. 챕터 도입부 쓰는 공식")
body("매번 새 챕터를 어떻게 시작할지 막막하다면, 아래 세 문장 공식을 그대로 써보세요. 이 가이드의 대부분의 장도 이 순서를 따르고 있습니다.")
callout_box("챕터 도입부 3문장 공식", [
    "1문장: 이 챕터가 다루는 대상과 상황을 짚기(&ldquo;OO 상황이라면&rdquo;, &ldquo;OO을 준비하는 분이라면&rdquo;)",
    "2문장: 이 챕터를 읽으면 무엇을 할 수 있게 되는지 미리 알려주기",
    "3문장(선택): 관련된 다른 챕터나 배경 정보를 짧게 연결하기",
])
body("이 공식대로 시작하면 독자가 &ldquo;이 챕터가 지금 나한테 필요한가&rdquo;를 첫 문장만 보고 바로 판단할 수 있습니다. 필요 없다고 판단되면 다음 챕터로 건너뛸 수 있게 해주는 것도 좋은 구성입니다 — 참고자료형 전자책은 처음부터 끝까지 순서대로 읽히기보다 필요한 부분만 찾아 읽히는 경우가 더 많기 때문입니다.")

h1("10-2장. 문장 다듬기 — 실제 전후 비교")
body("같은 내용이라도 문장을 어떻게 쓰느냐에 따라 읽는 속도가 크게 달라집니다. 아래는 같은 내용을 두 가지 방식으로 써본 예시입니다.")
callout_box("수정 전 (어려운 문장)", [
    "본 서비스의 정산은 판매금액 구간별 차등 수수료율이 적용되며 부가가치세 및 결제망 이용료가 합산 공제된 금액이 최종 지급되므로 사전에 이를 감안한 가격 설정이 요구됨.",
])
callout_box("수정 후 (쉬운 문장)", [
    "정산받을 때는 수수료ㆍ부가세ㆍ결제 수수료가 먼저 빠집니다. 그래서 가격을 정할 때 &ldquo;이 정도는 떼일 것&rdquo;을 미리 생각해두는 게 좋습니다.",
])
body("수정 후 문장은 한 문장에 하나의 정보만 담았고(&ldquo;무엇이 빠지는지&rdquo;, &ldquo;그래서 어떻게 해야 하는지&rdquo;), 한자어 대신 쉬운 말(&ldquo;합산 공제&rdquo; → &ldquo;빠집니다&rdquo;)로 바꿨습니다. 자신이 쓴 문장이 어렵게 느껴진다면, <b>&ldquo;이걸 친구에게 말로 설명한다면 어떻게 말할까&rdquo;</b>를 그대로 옮겨 적어보는 게 가장 쉬운 교정 방법입니다.")

h1("8-3장. 자료 정리 도구")
body("집필 기간이 길어질수록 &ldquo;어디서 봤는지 기억나는데 링크를 잃어버렸다&rdquo;는 일이 자주 생깁니다. 아래처럼 처음부터 자료를 한곳에 모아두는 습관을 들이면 나중에 출처(8-2장)를 표기할 때도 훨씬 수월합니다.")
callout_box("자료 정리 방법", [
    "노션ㆍ구글 문서 등에 챕터별 폴더(또는 페이지)를 만들어, 참고한 링크ㆍ캡처ㆍ메모를 그때그때 붙여넣기",
    "스크린샷 파일명에 번호와 출처를 함께 적어두기(예: &ldquo;05_크몽_검색결과_20260731&rdquo;) — 이 가이드도 같은 방식으로 스크린샷을 관리했습니다",
    "숫자ㆍ통계는 발견한 즉시 &ldquo;출처+확인한 날짜&rdquo;까지 함께 메모해두기 — 나중에 다시 찾으려면 배로 오래 걸립니다",
])
body("이렇게 자료를 미리 정리해두면 목차(3부)를 다시 손볼 때도, 나중에 개정판(14부)을 준비할 때도 처음부터 다시 찾아다닐 필요 없이 정리된 폴더만 다시 열어보면 됩니다. 특히 여러 챕터를 오가며 쓰는 참고자료형 전자책은 집필 기간이 길어지기 쉬우므로, 이 습관 하나가 전체 작업 시간을 크게 줄여줍니다.")

# ============================================================
# 5부
# ============================================================
part_page("PART 5", "디자인과 조판", "무료 도구만으로도 충분히 보기 좋은 결과물을 만들 수 있습니다.")

h1("11장. 표지 디자인 원칙")
body("전자책은 표지 이미지 하나로 클릭 여부가 갈립니다. 화려하게 꾸미는 것보다 <b>&ldquo;무엇에 대한 책인지 3초 안에 알 수 있는가&rdquo;</b>가 훨씬 중요합니다.")
callout_box("표지에 꼭 있어야 할 것", [
    "제목 — 검색 키워드가 그대로 들어간 제목(예: &ldquo;OO자격증 실기 요약노트&rdquo;)",
    "부제 — 이 책이 다루는 범위나 특징을 한 줄로(예: &ldquo;최신 개정 기준, 합격자 노트 형식&rdquo;)",
    "핵심 숫자 — &ldquo;80페이지&rdquo;, &ldquo;실제 화면 10장 수록&rdquo;처럼 분량ㆍ구성을 짐작하게 하는 숫자",
    "과한 장식 자제 — 배경 이미지가 제목 글자를 가리지 않도록, 대비가 확실한 배경색 위에 큰 글씨로",
])

h1("11-2장. 많이 쓰이는 표지 레이아웃 3가지")
body("표지 디자인이 막막하다면, 아래 세 가지 배치 중 하나를 뼈대로 삼아보세요. 세부 색상ㆍ폰트만 바꿔도 충분히 완성도 있는 표지가 나옵니다.")


def layout_mockup(name, rows_spec):
    cells = []
    heights = []
    for label, h, color in rows_spec:
        cells.append([Paragraph(label, ParagraphStyle(
            f"layout_{label}", fontName=FONT, fontSize=9, leading=12,
            textColor=colors.white, alignment=TA_CENTER))])
        heights.append(h * mm)
    t = Table(cells, colWidths=[50 * mm], rowHeights=heights)
    style = [("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (0, 0), (-1, -1), "CENTER"),
             ("BOX", (0, 0), (-1, -1), 0.8, BORDER)]
    for i, (_, _, color) in enumerate(rows_spec):
        style.append(("BACKGROUND", (0, i), (0, i), color))
    t.setStyle(TableStyle(style))
    return t


mockup_row = Table([[
    layout_mockup("A", [("부제", 12, colors.HexColor("#8d6fea")), ("제목", 28, ACCENT), ("핵심 숫자", 16, colors.HexColor("#a687f2"))]),
    layout_mockup("B", [("제목", 24, ACCENT), ("이미지/아이콘 영역", 20, colors.HexColor("#bfa0f7")), ("부제", 12, colors.HexColor("#8d6fea"))]),
    layout_mockup("C", [("제목+부제", 20, ACCENT), ("이미지 전체 배경", 36, colors.HexColor("#a687f2"))]),
]], colWidths=[55 * mm, 55 * mm, 55 * mm])
mockup_row.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER")]))
story.append(mockup_row)
story.append(Spacer(1, 6))
callout_box("레이아웃별 특징", [
    "A. 텍스트 중심형 — 부제ㆍ제목ㆍ핵심 숫자를 세로로 쌓는 구조. 이미지 소재가 마땅치 않을 때 가장 안전합니다.",
    "B. 상단 제목+중단 이미지형 — 제목 아래 관련 아이콘이나 일러스트를 넣어 주제를 시각적으로 보여줍니다.",
    "C. 이미지 배경형 — 스톡 이미지나 도형을 배경 전체에 깔고 그 위에 제목을 얹는 구조. 대비가 확실한 이미지를 고르는 게 중요합니다.",
])

h1("12장. 미리캔버스로 표지 만들기")
body("미리캔버스는 회원가입만 하면 무료로 쓸 수 있는 국내 디자인 도구입니다. 폰트ㆍ이미지ㆍ일러스트 등 제공되는 소재를 두 가지 이상 조합해서 만든 디자인은 상업적으로도 자유롭게 쓸 수 있습니다.")
screenshot("07_miricanvas_home.png", "미리캔버스 첫 화면 — &ldquo;템플릿 보러가기&rdquo;에서 표지ㆍ카드뉴스용 템플릿을 바로 골라 편집할 수 있다")
callout_box("표지 만드는 순서", [
    "첫 화면에서 &ldquo;템플릿 보러가기&rdquo;를 누르고 검색창에 &ldquo;전자책 표지&rdquo; 또는 &ldquo;북커버&rdquo;를 입력합니다.",
    "마음에 드는 템플릿을 고른 뒤 제목ㆍ부제 텍스트만 내 책 내용으로 바꿉니다. 폰트와 배치는 처음엔 템플릿 그대로 써도 충분합니다.",
    "완성되면 오른쪽 위 다운로드 버튼에서 <b>PNG 또는 JPG, 고해상도</b>로 내려받습니다.",
    "같은 방식으로 SNS 홍보용 카드뉴스도 같은 템플릿 톤으로 여러 장 만들어두면 나중에 마케팅(9부)에 바로 쓸 수 있습니다.",
])
body("해외 서비스인 <b>캔바(Canva)</b>도 비슷한 기능을 무료로 제공합니다. 두 도구 모두 사용법이 비슷하니, 먼저 접속해보고 더 편한 쪽을 쓰면 됩니다.")

h1("12-2장. 초보자를 위한 폰트 조합 추천")
body("폰트를 고를 때 가장 많이 하는 실수는 <b>서로 다른 폰트를 3개 이상 섞어 쓰는 것</b>입니다. 아래 조합 중 하나만 골라 표지부터 본문까지 통일해서 쓰면 실패할 확률이 거의 없습니다.")
simple_table(
    ["조합", "제목용", "본문용", "느낌"],
    [
        ["깔끔형", "굵은 고딕", "얇은 고딕", "신뢰감, 정보 전달형에 적합"],
        ["친근형", "둥근 고딕", "둥근 고딕(얇게)", "부드럽고 편안한 느낌"],
        ["신뢰형", "명조(세리프)", "얇은 고딕", "전문적ㆍ출판물 느낌"],
    ],
    [24 * mm, 38 * mm, 40 * mm, 64 * mm],
)
body("눈누(13장)에서 &ldquo;고딕&rdquo;, &ldquo;둥근&rdquo;, &ldquo;명조&rdquo;로 검색하면 위 조합에 맞는 무료 폰트를 쉽게 찾을 수 있습니다. 제목과 본문에 <b>굵기만 다르고 같은 폰트 가족</b>을 쓰면 가장 안전하게 통일감을 줄 수 있습니다.")

h1("13장. 무료 상업용 폰트 구하기 — 눈누")
body("표지나 본문에 회사ㆍ개인이 만든 폰트를 허락 없이 쓰면 저작권 문제가 생길 수 있습니다. <b>눈누(noonnu.cc)</b>는 상업적으로 자유롭게 써도 되는 무료 한글 폰트만 모아놓은 사이트입니다. 정부ㆍ지자체ㆍ기업이 배포한 무료 폰트부터 개인 디자이너가 만든 폰트까지 한곳에 모아 정리해두고 있어, 폰트 이름을 몰라도 &ldquo;고딕&rdquo;ㆍ&ldquo;손글씨&rdquo;ㆍ&ldquo;명조&rdquo; 같은 느낌으로 검색해 찾을 수 있습니다.")
body("표지에 쓸 폰트와 본문에 쓸 폰트를 눈누에서 각각 다운로드하면, 12-2장에서 정리한 조합 원칙을 그대로 적용할 수 있습니다.")
screenshot("08_noonnu_home.png", "눈누 첫 화면 — 상단 메뉴에서 &ldquo;추천 폰트&rdquo;ㆍ&ldquo;무료 폰트&rdquo;를 바로 골라볼 수 있다")
callout_box("눈누 사용법과 주의할 점", [
    "상단 메뉴의 &ldquo;무료 폰트&rdquo;에서 마음에 드는 폰트를 고르고, 상세 페이지에서 <b>허용 범위(상업적 이용, 인쇄, 굿즈 제작 등)</b>를 한 번 더 확인한 뒤 내려받으세요.",
    "화면 중간에 유료 폰트를 모아 파는 &ldquo;눈누마켓&rdquo; 배너도 함께 뜨는데, 이건 무료 폰트가 아니니 구분해서 봐야 합니다.",
    "폰트를 내려받아 컴퓨터에 설치한 뒤, 미리캔버스ㆍ한글ㆍ워드 등에서 바로 선택해서 쓸 수 있습니다.",
])

h1("13-2장. 폰트 라이선스 문서 읽는 법")
body("눈누에 올라와 있어도 폰트마다 허용 범위가 조금씩 다를 수 있습니다. 폰트 상세 페이지의 라이선스 요약 아이콘(보통 &ldquo;인쇄물&rdquo;, &ldquo;웹사이트&rdquo;, &ldquo;포장지&rdquo;, &ldquo;임베딩&rdquo; 등으로 표시)을 아래 기준으로 확인하세요.")
callout_box("전자책 제작 시 확인할 항목", [
    "&ldquo;인쇄물&rdquo; 허용 여부 — 전자책(PDF)은 인쇄물에 준하는 사용으로 보는 경우가 많으므로 이 항목이 허용돼야 합니다.",
    "&ldquo;임베딩(폰트 내장)&rdquo; 허용 여부 — PDF에 폰트를 그대로 심는 방식이라면 이 항목도 확인이 필요합니다.",
    "&ldquo;출처 표기 필수&rdquo; 여부 — 일부 무료 폰트는 사용 시 저작자 표기를 요구하기도 하니, 요구한다면 판권 페이지 등에 표기하세요.",
])

h1("14장. 가독성 원칙과 PDF 내보내기")
body("전자책은 결국 화면으로 읽는 문서입니다. 종이책보다 가독성 기준을 더 신경 써야 합니다.")
callout_box("가독성 체크리스트", [
    "본문 글자 크기는 화면 기준으로 종이책보다 조금 크게(11~12pt 이상 권장)",
    "글자색과 배경색의 대비를 확실하게 — 연한 회색 글씨에 흰 배경처럼 흐릿한 조합은 피하기",
    "한 문단은 5~6줄을 넘기지 않게 끊고, 문단 사이 여백을 충분히 주기",
    "표지ㆍ목차ㆍ본문 전체에서 같은 색상 팔레트(2~3가지 색)와 같은 폰트 조합을 일관되게 사용하기",
])
h1("14-1-2장. 표지 시안 여러 개 만들어 비교하기")
body("표지 하나만 만들고 확신이 안 선다면, 11-2장의 레이아웃 3가지 중 두세 가지로 각각 시안을 만들어 지인들에게 어느 쪽이 더 끌리는지 물어보세요. 이게 바로 용어 사전의 <b>A/B 테스트</b>를 가장 간단하게 적용하는 방법입니다. 플랫폼 등록 후에도 판매가 저조하면 표지만 바꿔서 며칠간 반응을 비교해볼 수 있습니다.")

body("워드ㆍ한글ㆍ구글 문서로 작성했다면 <b>&ldquo;PDF로 내보내기&rdquo; 또는 &ldquo;PDF로 저장&rdquo;</b> 기능으로 바로 변환할 수 있습니다. 더 정교한 디자인을 원한다면 미리캔버스ㆍ캔바에서 각 페이지를 디자인한 뒤 한꺼번에 PDF로 내보내는 방법도 있습니다. 어느 방법이든, 완성 후에는 <b>다른 컴퓨터ㆍ스마트폰에서 실제로 열어보고</b> 글자가 깨지지 않는지, 이미지가 잘 보이는지 반드시 확인하세요.")

h1("14-2장. 실패 없는 색상 조합 3가지")
body("색을 고를 때는 <b>포인트색 1가지 + 짙은 글자색 1가지 + 옅은 배경색 1가지</b>, 딱 세 가지만 정해두고 처음부터 끝까지 그 세 가지만 쓰는 게 원칙입니다. 아래 세 조합은 대비가 충분히 확보돼 가독성 문제가 생기지 않습니다.")


def swatch_row(name, accent_hex, text_hex, bg_hex, desc):
    accent_cell = Table([[""]], colWidths=[14 * mm], rowHeights=[10 * mm])
    accent_cell.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(accent_hex))]))
    text_cell = Table([[""]], colWidths=[14 * mm], rowHeights=[10 * mm])
    text_cell.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(text_hex))]))
    bg_cell = Table([[""]], colWidths=[14 * mm], rowHeights=[10 * mm])
    bg_cell.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(bg_hex)), ("BOX", (0, 0), (-1, -1), 0.5, BORDER)]))
    row = Table([[Paragraph(f"<b>{name}</b>", styles["table_cell"]), accent_cell, text_cell, bg_cell,
                  Paragraph(desc, styles["table_cell"])]],
                colWidths=[26 * mm, 18 * mm, 18 * mm, 18 * mm, 86 * mm])
    row.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (1, 0), (3, 0), "CENTER")]))
    story.append(row)
    story.append(Spacer(1, 5))


body("<font size=9 color='#4d5268'>왼쪽부터 순서대로 포인트색ㆍ글자색ㆍ배경색입니다.</font>")
swatch_row("차분한 보라", "#5a3fd6", "#1f2333", "#efeafc", "정보 전달형, 신뢰감 있는 느낌(이 가이드가 쓰는 조합)")
swatch_row("따뜻한 오렌지", "#e0692f", "#2b2018", "#fdf1e7", "실용ㆍ노하우형, 친근하고 편안한 느낌")
swatch_row("차분한 그린", "#2f8f5b", "#1c2b23", "#eaf6ef", "자기계발ㆍ건강 계열, 안정적인 느낌")
story.append(Spacer(1, 6))
body("주제와 분위기가 맞는 조합 하나를 고른 뒤, 표지ㆍ목차ㆍ본문 강조 문구까지 전부 같은 세 가지 색만 쓰세요. 색이 여러 개로 늘어날수록 전문적으로 보이기보다 산만해 보입니다.")

# ============================================================
# 6부
# ============================================================
part_page("PART 6", "이미지ㆍ스크린샷 안전하게 구하기", "저작권 문제 없이 쓸 수 있는 이미지를 구하는 방법입니다.")

h1("15장. 저작권 안전한 이미지 구하는 법")
callout_box("우선순위대로 추천", [
    "1순위: 직접 캡처 — 설명하려는 사이트ㆍ앱 화면을 본인이 직접 캡처. 가장 신뢰도 높고 저작권 문제가 없습니다(다만 캡처한 화면 속 타인의 개인정보ㆍ사진은 가려야 합니다).",
    "2순위: 무료 스톡 사이트 — Unsplash, Pixabay처럼 상업적 이용을 명시적으로 허용하는 사이트의 사진ㆍ일러스트. 다운로드 전 반드시 라이선스 조건을 확인하세요.",
    "3순위: 디자인 도구 제공 소재 — 미리캔버스ㆍ캔바 안에서 제공되는 이미지ㆍ아이콘(도구 안에서 다른 요소와 조합해서 쓰는 경우 상업적 이용 가능).",
])
site_box("Unsplash", "unsplash.com", "고화질 사진 중심의 무료 스톡 사이트. 대부분 별도 출처 표기 없이도 상업적 이용이 허용되지만, 사진마다 라이선스 문구를 한 번씩 확인하는 습관이 안전합니다.")
site_box("Pixabay", "pixabay.com", "사진ㆍ일러스트ㆍ벡터 이미지를 폭넓게 제공하는 무료 스톡 사이트. 검색 결과에 상업용 유료 소재도 함께 섞여 나오니 무료 여부를 항목별로 확인해야 합니다.")
site_box("Flaticon", "flaticon.com", "표지ㆍ카드뉴스에 쓸 작은 아이콘을 무료로 구할 수 있는 사이트. 무료 이용 시 출처 표기를 요구하는 아이콘이 많으니 다운로드 전 조건을 확인하세요.")
callout_box("절대 하면 안 되는 것", [
    "포털 이미지 검색 결과를 그대로 가져다 쓰기 — 대부분 저작권이 있는 이미지입니다.",
    "다른 판매자의 전자책ㆍ상세페이지 이미지를 그대로 캡처해서 쓰기 — 명백한 저작권 침해입니다.",
    "실존 인물의 사진(연예인, 인플루언서 등)을 허락 없이 표지ㆍ본문에 쓰기 — 초상권 문제가 됩니다.",
])

h1("15-2장. 스크린샷 편집 요령")
body("화면을 그냥 캡처만 해서 넣으면 독자가 어디를 봐야 할지 헷갈릴 수 있습니다. 아래처럼 간단하게 손보면 훨씬 이해하기 쉬워집니다.")
callout_box("스크린샷을 보기 좋게 만드는 법", [
    "화살표ㆍ네모 테두리로 지금 설명하는 부분을 표시하기 — 미리캔버스에 캡처 이미지를 불러와 도형을 얹으면 쉽습니다.",
    "캡처 화면에 이름ㆍ전화번호ㆍ주문번호 등 개인정보가 보인다면 반드시 모자이크 처리하기.",
    "캡처 하나에 너무 많은 내용을 담지 말고, 설명하는 단계마다 캡처를 나눠서 넣기(이 가이드도 단계별로 캡처를 나눠 배치했습니다).",
    "캡처 아래에는 항상 &ldquo;무엇을 보여주는 화면인지&rdquo; 한 줄 설명(캡션)을 붙이기 — 이미지만 덩그러니 있으면 설득력이 떨어집니다.",
])

h1("15-3장. 저작권을 침해하면 실제로 어떤 일이 생기나")
body("&ldquo;그냥 이미지 하나인데 괜찮겠지&rdquo;라고 넘기기 쉽지만, 저작권자가 문제를 제기하면 실제로 아래와 같은 절차로 이어질 수 있습니다.")
callout_box("저작권 침해 시 발생할 수 있는 일", [
    "저작권자 또는 대리인으로부터 사용 중지ㆍ삭제 요청을 받을 수 있습니다.",
    "플랫폼(크몽ㆍ탈잉 등)에 신고가 들어가면 해당 상품이 판매 중지되거나 계정에 불이익이 갈 수 있습니다.",
    "손해배상 청구로 이어지는 경우, 이미지 한 장이라도 법적 분쟁 비용이 이미지 사용으로 아낀 시간보다 훨씬 클 수 있습니다.",
])
body("이런 위험을 피하는 가장 확실한 방법은 결국 15장에서 다룬 우선순위(직접 캡처 → 무료 스톡 → 도구 제공 소재)를 지키는 것입니다. 아주 사소해 보이는 이미지 한 장이라도 출처를 확신할 수 없다면 쓰지 않는 게 안전합니다.")

h1("15-4장. 출처 표기가 필요할 때 쓰는 문구")
body("무료 스톡 이미지 중에는 출처 표기를 요구하지 않는 것도 많지만, 요구하는 경우도 있습니다. 아래 형식을 그대로 응용하면 됩니다.")
callout_box("출처 표기 예시", [
    "&ldquo;사진: Unsplash, [작가명]&rdquo;",
    "&ldquo;이 자료의 캡처 화면은 [사이트명] 공식 홈페이지(2026년 7월 기준)에서 직접 촬영했습니다.&rdquo;",
    "&ldquo;본문에 사용된 폰트는 [폰트명](눈누, 상업적 이용 가능)입니다.&rdquo;",
])
body("전자책 맨 뒤쪽에 &ldquo;이미지ㆍ폰트 출처&rdquo; 페이지를 한 쪽 따로 만들어 모아두면, 개별 페이지마다 표기하지 않아도 되는 경우가 많습니다(단, 라이선스가 개별 표기를 요구한다면 그대로 따라야 합니다).")

# ============================================================
# 7부
# ============================================================
part_page("PART 7", "플랫폼별 판매 방법과 수수료", "완성한 전자책을 실제로 어디에, 어떻게 올릴지 다룹니다.<br/>플랫폼마다 수수료 구조와 필요 조건이 다릅니다.")

h1("16장. 크몽 — 재능마켓형, 등록이 가장 쉽다")
body("크몽은 전자책을 &ldquo;서비스&rdquo; 형태로 등록해서 파는 재능마켓입니다. 사업자등록 없이도 개인 자격으로 바로 시작할 수 있어, 첫 판매 경험을 쌓기에 가장 진입장벽이 낮습니다.")
callout_box("크몽 등록 순서", [
    "회원가입 후 &ldquo;전문가 등록&rdquo; 메뉴에서 판매자 전환",
    "&ldquo;서비스 등록&rdquo;에서 카테고리를 &ldquo;전자책&rdquo;으로 선택하고 제목ㆍ소개ㆍ가격ㆍ썸네일(표지 이미지)ㆍPDF 파일 업로드",
    "심사(주로 형식적 검토) 통과 후 바로 검색ㆍ노출 시작",
])
body("<b>수수료 구조</b>: 판매자가 실제로 받는 정산 수수료는 판매 금액 구간에 따라 달라집니다. 단건 판매금액 70만원 이하 구간은 16.4%, 200만원 이하 구간은 9.4%, 200만원 초과 구간은 4.4%의 서비스 이용료가 적용되고, 여기에 결제망 이용료 3.3%와 부가세 10%가 더해집니다. 일반적인 가격대(10만원 이하)에서는 <b>총수수료가 대략 20% 안팎</b>이라고 보면 됩니다(구매자에게는 별도로 결제금액의 4.5% 수수료가 붙습니다).")
site_box("크몽", "kmong.com", "국내 최대 재능마켓. 전자책 카테고리가 &ldquo;라이프&rdquo;ㆍ&ldquo;부업ㆍ수익화&rdquo;ㆍ&ldquo;취업ㆍ시험ㆍ자격증&rdquo;으로 세분화. 사업자등록 불필요, 진입장벽 가장 낮음.", highlight=True)

h1("16-2장. 크몽 상세페이지 잘 쓰는 법")
body("등록 화면에서 가장 많은 공간을 차지하는 게 상세페이지(서비스 소개) 입니다. 아래 순서를 따르면 처음 써도 무난한 결과가 나옵니다.")
callout_box("상세페이지 구조 4단계", [
    "1. 문제 제기 — &ldquo;OO 때문에 시간을 낭비하고 계신가요?&rdquo;처럼 독자의 상황을 먼저 짚어줍니다.",
    "2. 차별점 — 3장에서 찾은 &ldquo;빈틈&rdquo;을 여기서 구체적으로 제시합니다(&ldquo;실제 화면 O장 수록&rdquo;, &ldquo;최신 개정 반영&rdquo; 등).",
    "3. 목차 공개 — 이 가이드의 목차처럼, 구매 전에 무엇이 들어있는지 그대로 보여줍니다. 숨기는 것보다 다 보여주는 쪽이 전환율이 높습니다.",
    "4. 신뢰 요소 — 후기(있다면), 무료 체험판 안내(23장), &ldquo;이 가이드가 아닌 것&rdquo; 같은 정직한 한계 고지를 마지막에 배치합니다.",
])
body("썸네일(표지 이미지)은 목록 화면에서 작게 보이므로, 제목 글자가 표지 안에서도 뭉개지지 않고 읽히는지 축소해서 미리 확인하세요.")

h1("17장. 탈잉 — 클래스와 전자책을 함께 파는 재능마켓")
body("탈잉은 원래 오프라인ㆍ온라인 클래스 중개로 시작한 플랫폼이지만, 전자책ㆍ녹화 영상 형태의 콘텐츠도 함께 등록해 팔 수 있습니다.")
screenshot("05_taling_home.png", "탈잉 첫 화면 — 클래스 카테고리 사이에 전자책 형태의 콘텐츠도 섞여 노출된다")
body("<b>수수료 구조</b>: 전자책ㆍ녹화 영상 클래스의 중개 위탁수수료는 20%이며, 여기에 부가가치세 10%와 소득세 3.3%가 원천징수된 뒤 입금됩니다. 예를 들어 70만원어치가 팔렸다면 최종 수령액은 약 53만원 수준(약 76%)입니다. 크몽과 비슷한 재능마켓형이므로, 두 곳에 동시에 등록해서 노출을 넓히는 것도 방법입니다.")
site_box("탈잉", "taling.me", "클래스 중심 재능마켓, 전자책도 함께 등록 가능. 위탁수수료 20%+세금 원천징수.")
body("이 외에 <b>숨고</b>(전문가를 &ldquo;고수&rdquo;라고 부르는 재능마켓)도 있지만, 숨고는 견적 요청ㆍ매칭 중심 구조라 전자책처럼 미리 만들어둔 파일을 등록해서 파는 방식과는 결이 다릅니다. 전자책은 크몽ㆍ탈잉처럼 &ldquo;상품을 진열해두고 검색으로 찾아오게 하는&rdquo; 구조의 플랫폼에 더 적합합니다.")

h1("16-3장. 검색에 걸리는 제목ㆍ태그 고르는 법")
body("크몽은 정확한 노출 알고리즘을 공개하지 않지만, 3장에서 실제로 확인했듯 검색 결과 화면에 <b>추천 카테고리 태그</b>(&ldquo;전자책&gt;라이프 전자책&rdquo;, &ldquo;부업ㆍ수익화 전자책&rdquo; 등)가 노출되는 걸 볼 수 있었습니다. 이걸 참고해 제목과 태그를 정하면 최소한 &ldquo;검색이 아예 안 되는&rdquo; 상황은 피할 수 있습니다.")
callout_box("제목ㆍ태그 정할 때 참고할 것", [
    "제목에는 반드시 사람들이 실제로 검색할 단어(자격증명, 툴 이름, 플랫폼 이름 등)를 그대로 넣기 — 감성적인 표현만으로는 검색에 걸리지 않습니다.",
    "카테고리는 최대한 세부 카테고리까지 선택하기 — 대분류만 선택하면 그 안의 수많은 경쟁 상품 사이에 묻히기 쉽습니다.",
    "등록 후에도 반응이 없다면 제목ㆍ태그를 조금씩 바꿔가며 며칠 간격으로 다시 검색해보고, 노출이 어떻게 달라지는지 스스로 관찰하는 게 가장 확실한 방법입니다.",
])

h1("21-2장. 상세페이지 나쁜 예 vs 좋은 예")
body("16-2장에서 다룬 구조를 실제 문장으로 비교해보면 차이가 더 명확합니다.")
simple_table(
    ["항목", "나쁜 예", "좋은 예"],
    [
        ["제목", "인생을 바꾸는 전자책", "OO자격증 실기 압축 요약노트(2026년 개정)"],
        ["도입부", "안녕하세요, 전문가입니다.", "OO 시험 준비, 어디서부터 봐야 할지 막막하셨나요?"],
        ["구성 소개", "알찬 내용 가득 담았습니다.", "총 3부 구성ㆍ실제 화면 8장ㆍ최근 3개년 기출 반영"],
        ["신뢰 요소", "(없음)", "이 가이드가 아닌 것 문단으로 과장 없이 범위 명시"],
    ],
    [24 * mm, 68 * mm, 74 * mm],
)
body("나쁜 예의 공통점은 <b>추상적이고 검증할 수 없는 표현</b>이라는 것입니다. 좋은 예는 전부 &ldquo;무엇이, 얼마나&rdquo;를 구체적인 숫자와 함께 보여줍니다. 자신의 상세페이지를 쓸 때도 추상적인 형용사(알찬, 최고의, 완벽한) 대신 구체적인 숫자와 사실로 바꿔보세요.")

h1("18장. 부크크 — 자가출판(POD), 진짜 &ldquo;책&rdquo;으로 만들고 싶다면")
body("부크크는 종이책과 전자책을 동시에 만들 수 있는 국내 자가출판(Self-Publishing, POD) 플랫폼입니다. 원고를 등록하면 ISBN(국제표준도서번호) 발급부터 온ㆍ오프라인 서점 유통까지 한 번에 진행할 수 있어, &ldquo;정식으로 출간된 책&rdquo;이라는 느낌을 주고 싶을 때 적합합니다.")
screenshot("03_bookk_home.png", "부크크 첫 화면 — 2026년 7월 기준 종이책 58,033종, 전자책 23,100종, 저자 42,400명이 이미 등록돼 있다")
body("첫 화면에서 실제로 확인할 수 있듯, 이미 <b>전자책만 2만 3천 종 이상</b>이 등록돼 있을 만큼 활발한 플랫폼입니다. 등록ㆍISBN 발급 등 기본 서비스는 <b>무료</b>이고, 판매가 이뤄질 때 정해진 인세율로 정산받는 구조입니다.")
callout_box("부크크 인세 구조(흑백 도서 기준)", [
    "정가 기준: 250페이지 기준 흑백 도서 정가 13,400원, 컬러 도서 정가 16,000원(페이지 수에 따라 달라짐)",
    "직접 판매(부크크 사이트 내) 시 인세 35%(흑백) / 15%(컬러)",
    "외부 유통(예스24ㆍ알라딘ㆍ11번가ㆍ북센ㆍ교보문고 등) 판매 시 인세 15%(흑백) / 10%(컬러) — 외부 서점의 판매 수수료가 추가로 빠지기 때문입니다",
    "외부 유통 신청 자체는 무료이며, 신청 여부를 직접 선택할 수 있습니다",
])
body("전자책 정보 구조화형 콘텐츠(예: 자격증 요약노트)를 <b>정식 ISBN이 있는 책</b>으로 만들어 신뢰도를 높이고 싶다면 부크크가 적합합니다. 다만 인세율이 재능마켓(크몽ㆍ탈잉)보다 낮으므로, 가격을 좀 더 높게 책정하거나 재능마켓과 병행하는 전략이 유리합니다.")
site_box("부크크", "bookk.co.kr", "국내 대표 자가출판 POD 플랫폼. 등록ㆍISBN 무료, 서점 유통 연계. 종이책+전자책 동시 제작 가능.", highlight=True)

h1("18-2장. 종이책(POD)도 함께 만들어야 할까")
body("POD(Print On Demand)는 <b>주문이 들어온 만큼만 그때그때 인쇄</b>하는 방식이라, 미리 대량으로 찍어 재고를 떠안을 필요가 없습니다. 전자책만으로도 충분하지만, 아래 경우라면 종이책을 함께 고려할 만합니다.")
callout_box("종이책을 함께 만들면 좋은 경우", [
    "손으로 밑줄 치며 공부하는 수요가 큰 주제(자격증 요약노트, 암기용 노트)",
    "선물ㆍ소장 목적이 있는 주제(자기계발, 에세이형 정보서)",
    "이미 전자책으로 반응을 확인했고, 정식 ISBN으로 신뢰도를 한 단계 더 높이고 싶을 때",
])
body("정가를 얼마로 잡을지 감이 안 잡힌다면, 18장에서 본 <b>250페이지 흑백 기준 13,400원</b>을 기준점으로 삼아 내 원고 분량에 비례해서 조정하면 됩니다. 예를 들어 원고가 150페이지 안팎이라면 정가를 그보다 낮은 9,000~10,000원대로, 300페이지를 넘는다면 15,000원 이상으로 잡는 식입니다. 정가가 곧 인세 계산의 기준이 되므로, 너무 낮게 잡으면 직접 판매 인세(35%)를 적용해도 실제 수령액이 작아진다는 점을 함께 고려하세요.")

h1("19장. 유페이퍼 — 전자책 유통 전문 플랫폼")
body("유페이퍼는 전자책 유통에 특화된 플랫폼으로, 원고를 등록하면 유페이퍼 자체 판매는 물론 교보문고ㆍ예스24ㆍ알라딘 등 제휴 서점에도 함께 유통해줍니다.")
screenshot("04_upaper_home.png", "유페이퍼 첫 화면 — 새로 등록된 전자책이 매일 올라오는 유통형 플랫폼")
callout_box("유페이퍼 수수료와 ISBN", [
    "유페이퍼 자체 판매: 수수료 30%, 저자 수령 70%",
    "제휴 서점(교보문고ㆍ예스24ㆍ알라딘 등) 판매: 수수료 40%, 저자 수령 60% — 제휴 서점 자체 수수료가 포함된 구조입니다",
    "ISBN 발급 대행: 비용 1,000원, 발급까지 약 7일 소요",
])
body("부크크와 마찬가지로 <b>정식 서점 유통</b>을 원할 때 좋은 선택지입니다. 부크크는 종이책 제작(POD)에 강점이 있고, 유페이퍼는 전자책 유통 자체에 좀 더 집중돼 있다는 차이가 있으니, 종이책 제작 계획이 없다면 유페이퍼만으로도 충분합니다.")
site_box("유페이퍼", "upaper.kr", "전자책 유통 전문 플랫폼. 교보문고ㆍ예스24ㆍ알라딘 제휴 유통, ISBN 발급 대행(1,000원).")

h1("19-2장. ISBN이 있으면 실제로 뭐가 달라지나")
body("재능마켓(크몽ㆍ탈잉)에 올리는 파일에는 ISBN이 없어도 되지만, 부크크ㆍ유페이퍼를 거쳐 ISBN을 발급받으면 아래와 같은 실질적인 차이가 생깁니다.")
callout_box("ISBN이 주는 실질적 혜택", [
    "국립중앙도서관에 납본되어 공식적으로 &ldquo;출간된 도서&rdquo; 목록에 등재됩니다.",
    "교보문고ㆍ예스24ㆍ알라딘 등 대형 서점 검색에서 정식 도서로 노출될 수 있습니다.",
    "이력서ㆍ포트폴리오ㆍSNS 소개글에 &ldquo;저서&rdquo;로 표기할 수 있는 근거가 생깁니다.",
    "추후 강의ㆍ자문 등 관련 활동을 할 때 &ldquo;출간 작가&rdquo;라는 신뢰 요소로 활용할 수 있습니다.",
])
body("다만 ISBN이 있다고 검색 상위에 자동으로 노출되는 것은 아니며, 결국 9부의 마케팅을 병행해야 실제 판매로 이어집니다. ISBN은 <b>신뢰도를 더하는 장치</b>이지 마케팅을 대신해주는 장치는 아니라는 점을 기억하세요.")

h1("20장. 스마트스토어 — 직접 판매, 사업자등록이 필요하다")
body("네이버 스마트스토어에서도 PDF 전자책을 &ldquo;디지털 상품&rdquo;으로 직접 등록해서 팔 수 있습니다. 다만 이 방법은 <b>사업자등록이 필수</b>이므로, 이미 사업자등록을 마쳤거나 이 부업을 본격적으로 키울 계획이 있는 경우에 적합합니다.")
screenshot("06_smartstore_seller.png", "스마트스토어센터 가입 화면 — 판매를 시작하려면 로그인 후 사업자 정보 등록 절차를 거쳐야 한다")
callout_box("스마트스토어 등록 시 참고할 것", [
    "카테고리는 보통 [도서 &gt; 전자책] 또는 [디지털콘텐츠 관련 카테고리] 중에서 상품 성격에 맞게 선택합니다.",
    "실물 배송이 없으므로 배송 방식을 &ldquo;배송없음&rdquo; 또는 파일을 이메일로 보내는 방식으로 설정합니다.",
    "네이버 통합검색ㆍ쇼핑 유입을 그대로 활용할 수 있다는 게 가장 큰 장점이지만, 재능마켓과 달리 첫 노출까지 스스로 마케팅(9부)을 해야 하는 경우가 많습니다.",
])
body("스마트스토어는 결제 수수료(네이버페이 주문관리수수료)만 부담하면 되고 중개 플랫폼처럼 20~30%씩 떼가지 않아 <b>정산 비율이 가장 유리</b>합니다. 다만 사업자등록ㆍ직접 마케팅이라는 진입장벽이 있으므로, 크몽ㆍ탈잉으로 먼저 반응을 확인한 뒤 규모를 키울 때 추가하는 순서를 추천합니다.")
site_box("스마트스토어", "sell.smartstore.naver.com", "네이버 직접 판매 채널. 사업자등록 필수, 중개수수료 없이 결제수수료만 부담해 정산 비율이 가장 유리.")
callout_box("스마트스토어를 시작하기 전 추가로 필요한 것", [
    "사업자등록증 — 관할 세무서 또는 홈택스에서 발급",
    "통신판매업 신고 — 온라인으로 직접 상품을 파는 경우 관할 구청(정부24에서도 온라인 신청 가능)에 별도로 신고해야 합니다. 사업자등록과는 별개의 절차입니다.",
    "구매안전서비스 이용 확인증 — 통신판매업 신고 시 함께 필요하며, 스마트스토어에 가입하면 스토어 URL로 자동 발급받을 수 있습니다.",
])

h1("20-2장. 그 외에 고려할 수 있는 채널")
body("위 5곳이 가장 대표적이지만, 콘텐츠 성격에 따라 아래 채널도 고려할 만합니다.")
site_box("인프런", "inflearn.com", "IT ㆍ 업무 스킬 계열이라면 전자책보다 &ldquo;강의&rdquo; 형태 수요가 더 큰 경우가 많습니다. PDF 자료를 강의와 묶어 판매하는 방식도 가능합니다.")
site_box("블로그ㆍSNS 자체 채널 + 결제 링크", "-", "이미 구독자ㆍ이웃이 있는 블로그나 SNS가 있다면, 스마트스토어 상품 링크나 계좌 안내로 직접 연결해 중개수수료 자체를 없앨 수 있습니다. 단, 통신판매업 신고 등 요건은 스마트스토어와 동일하게 적용됩니다.")
body("처음 시작하는 단계에서는 앞서 다룬 5개 채널만으로 충분합니다. 이 채널들은 이미 구독자나 팬층을 가진 다음 단계에서 고려해도 늦지 않습니다.")

h1("20-3장. 여러 채널에 동시 등록할 때 파일 관리")
body("2곳 이상에 등록하기로 했다면(21-3장), 개정판(14부)이 나올 때마다 <b>모든 채널의 파일을 빠짐없이 교체</b>해야 합니다. 채널별로 파일 버전이 달라지면 후기에서 &ldquo;어느 게 최신판이냐&rdquo;는 혼란이 생길 수 있습니다.")
callout_box("파일 버전 관리 요령", [
    "파일명에 버전과 날짜를 표기(예: &ldquo;OO가이드_v2_202608.pdf&rdquo;)해 어느 채널에 어떤 버전이 올라가 있는지 스스로 파악할 수 있게 하기",
    "개정할 때마다 변경 이력을 한 페이지로 정리해 파일 맨 앞이나 뒤에 붙여두기 — 재구매자에게도, 스스로에게도 유용합니다",
    "등록해둔 채널 목록과 최종 업데이트 날짜를 별도로 기록해두고, 개정할 때마다 하나씩 체크하며 교체하기",
])

h1("21장. 플랫폼 비교표 총정리")
simple_table(
    ["플랫폼", "수수료(대략)", "사업자등록", "강점"],
    [
        ["크몽", "약 20%", "불필요", "등록이 가장 쉽고 빠름"],
        ["탈잉", "20%+세금 원천징수", "불필요", "클래스 수요층과 겹쳐 노출"],
        ["부크크", "직접 인세 35%/15%*", "불필요", "정식 ISBNㆍ종이책 병행 가능"],
        ["유페이퍼", "저자 수령 70%/60%*", "불필요", "교보ㆍ예스24ㆍ알라딘 유통"],
        ["스마트스토어", "결제수수료만", "필요", "정산 비율 가장 유리"],
    ],
    [34 * mm, 42 * mm, 28 * mm, 62 * mm],
)
body("<i>* 부크크ㆍ유페이퍼는 수수료를 떼는 구조가 아니라 인세율로 지급하는 구조라서, 앞의 세 곳(크몽ㆍ탈잉ㆍ스마트스토어)과 숫자를 단순 비교하기는 어렵습니다. &ldquo;저자가 최종적으로 받는 비율&rdquo; 기준으로 나란히 적었습니다.</i>")
body("정답은 하나가 아닙니다. <b>처음 시작한다면 크몽(진입장벽 낮음) 하나로 반응을 먼저 확인</b>하고, 반응이 좋으면 탈잉을 추가해 노출을 넓히고, 정식 출간 느낌을 원하면 부크크ㆍ유페이퍼를, 사업자등록이 있고 마케팅 채널을 직접 키울 자신이 있다면 스마트스토어까지 넓히는 순서를 권장합니다.")

h1("21-3장. 내 상황별 추천 조합")
callout_box("상황에 맞는 조합", [
    "자격증ㆍ시험 요약형이라 신뢰도가 중요하다 → 크몽(빠른 검증) + 부크크(정식 ISBN)",
    "업무 툴 실습형이라 지속적인 질문 대응이 필요하다 → 크몽 + 탈잉(비슷한 실무형 이용자층)",
    "이미 사업자등록이 있고 블로그ㆍSNS 채널을 키우고 있다 → 스마트스토어(수수료 최소화) + 자체 채널",
    "정식 &ldquo;저자&rdquo; 타이틀이 필요하다(강의ㆍ자문 활동과 연계) → 부크크ㆍ유페이퍼 우선, 재능마켓은 보조 채널로",
    "아직 뭐가 맞을지 모르겠다 → 크몽 하나로 시작해 반응을 보고 위 조합 중 하나로 확장",
])

# ============================================================
# 8부
# ============================================================
part_page("PART 8", "가격 책정 전략", "너무 싸게 팔면 남는 게 없고, 너무 비싸게 팔면 안 팔립니다.")

h1("22장. 가격은 어떻게 정할까")
body("3장에서 살펴본 크몽 검색 결과에서도 확인했듯, 같은 &ldquo;전자책&rdquo; 카테고리 안에서도 가격은 수만원대부터 수십만원대까지 다양합니다. 가격은 페이지 수가 아니라 <b>&ldquo;이 정보를 얻기 위해 다른 방법을 쓴다면 얼마나 들었을까&rdquo;</b>를 기준으로 생각하는 게 합리적입니다.")
callout_box("가격 책정에 참고할 기준", [
    "정보를 스스로 찾아 정리하는 데 걸리는 시간(예: 자격증 기출 정리에 10시간이 걸린다면, 그 시간을 아껴주는 값)",
    "비슷한 계열의 다른 판매자 가격대(3장 크몽 조사 결과 참고)",
    "무료로 얻을 수 있는 정보와 얼마나 차별화되는지(단순 요약이 아니라 실제 사례ㆍ스크린샷ㆍ해설이 더해졌는지)",
])
h2("저가 진입 전략")
body("처음 판매하는 상품이라 후기가 하나도 없다면, 초반에는 시장 평균보다 낮은 가격으로 시작해 <b>후기를 빠르게 쌓는 것</b>이 유리합니다. 후기가 어느 정도 쌓이면(보통 10~20개 이상) 점진적으로 가격을 올리는 방식이 자연스럽습니다.")
h2("프리미엄 전략")
body("이미 그 분야에서 활동 이력(강의, 자격, SNS 팔로워 등)이 있다면 처음부터 시장 평균보다 높은 가격으로 포지셔닝하고, 그만큼 구성을 훨씬 두껍게(사례, 1:1 질문 응답권 등 부가 혜택 포함) 만드는 전략도 가능합니다.")
h2("얼리버드 할인")
body("출시 직후 1~2주간 한시적으로 할인가를 걸어두면, &ldquo;지금 사야 싸다&rdquo;는 동기를 만들어 초기 판매 속도를 높일 수 있습니다. 할인 종료 후 정가로 복귀한다는 문구를 상세페이지에 명확히 적어두세요.")

h1("22-2장. 실제 가격대는 얼마나 넓을까")
body("3장에서 크몽을 검색했을 때 실제로 화면에 함께 노출됐던 가격들을 그대로 옮겨보면, 같은 &ldquo;전자책&rdquo; 카테고리 안에서도 가격 폭이 매우 넓다는 걸 알 수 있습니다.")
bar_row("고관여 투자정보형", 6828000, 6828000, colors.HexColor("#5a3fd6"), unit="원", label_w=52)
bar_row("고관여 재테크형", 1800000, 6828000, colors.HexColor("#7457e0"), unit="원", label_w=52)
bar_row("전문자격 요약형", 79000, 6828000, colors.HexColor("#8d6fea"), unit="원", label_w=52)
bar_row("일반 정보형", 49000, 6828000, colors.HexColor("#a687f2"), unit="원", label_w=52)
bar_row("가벼운 안내형", 24000, 6828000, colors.HexColor("#bfa0f7"), unit="원", label_w=52)
story.append(Spacer(1, 4))
body("<i>(2026년 7월 크몽 &ldquo;전자책&rdquo; 검색 결과 화면에 함께 노출된 실제 가격 예시 ㆍ 특정 판매자를 지목한 것이 아니라 가격 폭을 보여주기 위한 인용입니다.)</i>")
body("가격이 수백만원대까지 올라가는 상품은 대부분 <b>투자ㆍ재테크처럼 &ldquo;잘못되면 큰돈이 걸린&rdquo; 고관여 분야</b>였고, 반대로 낮은 가격대는 <b>가볍게 훑어볼 수 있는 범용 정보</b>였습니다. 처음 시작한다면 이 중간대인 2~6만원대에서 시작해, 후기와 반응을 보며 위아래로 조정하는 게 현실적입니다.")

h1("22-3장. 가격 끝자리 정하는 법")
body("같은 가치라도 가격 표기 방식에 따라 체감이 달라집니다. 정답은 없지만, 아래 두 방식의 차이를 알고 의도적으로 고르는 것과 아무 생각 없이 정하는 것은 다릅니다.")
callout_box("끝자리 표기 비교", [
    "&ldquo;19,000원&rdquo;처럼 <b>9로 끝나는 가격</b> — &ldquo;2만원보다 싸다&rdquo;는 인상을 줘서 저가 진입 전략(8부)과 잘 어울립니다.",
    "&ldquo;20,000원&rdquo;처럼 <b>깔끔한 정수</b> — 정산ㆍ회계 처리가 단순하고, 전문적ㆍ신뢰감 있는 인상을 줘서 프리미엄 전략과 잘 어울립니다.",
])
body("어느 쪽을 고르든 한 번 정한 뒤에는 상세페이지ㆍ표지ㆍ썸네일에 표기된 가격을 전부 통일하세요. 페이지마다 다른 표기가 섞여 있으면 신뢰도가 떨어져 보입니다.")

# ============================================================
# 9부
# ============================================================
part_page("PART 9", "마케팅과 후기 모으기", "잘 만든 것과 잘 팔리는 것은 다른 문제입니다.")

h1("23장. 무료 체험판(샘플 PDF) 만들기")
body("전체 내용 중 <b>목차와 1~2개 챕터 정도(전체 분량의 10~15% 수준)</b>를 별도 PDF로 만들어 무료로 공개하면, 구매를 망설이는 사람의 결정을 도울 수 있습니다. 크몽ㆍ탈잉 상세페이지에는 대부분 미리보기 이미지나 샘플 파일을 첨부하는 기능이 있으니 활용하세요.")

h1("23-2장. 체험판을 만들 때 주의할 점")
callout_box("체험판 구성 요령", [
    "목차 전체는 공개하되, 본문은 &ldquo;가장 매력적인 챕터 1~2개&rdquo;만 완전한 형태로 공개하기 — 서론만 자르면 오히려 부실해 보입니다.",
    "체험판 마지막 페이지에 &ldquo;전체 버전에는 이런 내용이 더 있습니다&rdquo;를 목록으로 보여주며 자연스럽게 구매로 연결하기",
    "체험판이라는 사실과 전체 분량 대비 몇 %인지 첫 페이지에 명시해, 전체 내용으로 오인되지 않게 하기",
])

h1("24장. SNS 카드뉴스로 알리기")
body("12장에서 만든 표지 디자인과 같은 톤으로, 책 내용 중 <b>&ldquo;바로 써먹을 수 있는 핵심 정보&rdquo; 한두 가지를 요약한 카드뉴스</b>(이미지 여러 장)를 만들어 인스타그램ㆍ스레드 등에 올리는 방법입니다.")
callout_box("카드뉴스 구성 예시(5~7장 기준)", [
    "1장: 문제 제기(&ldquo;OO 때문에 고민이신가요?&rdquo;)",
    "2~5장: 핵심 정보 1~2가지를 미리 공개(책 전체가 아니라 &ldquo;맛보기&rdquo; 수준)",
    "6장: &ldquo;더 자세한 내용은 전자책에 담았습니다&rdquo;로 자연스럽게 연결",
    "7장: 판매 링크 또는 프로필 링크 안내",
])
body("카드뉴스에는 <b>책의 실제 내용을 요약해서 보여주되, 전체를 다 공개하지 않는 균형</b>이 중요합니다. 정보가 너무 부족하면 관심을 못 끌고, 너무 다 보여주면 살 이유가 없어집니다.")

h2("프로필 최적화하기")
body("카드뉴스를 올릴 계정의 프로필도 함께 정리해두세요. 프로필 소개 문구에 &ldquo;무엇을 파는 사람인지&rdquo;가 한 줄로 보이고, 프로필 링크가 구매 페이지(또는 여러 링크를 모아주는 링크인바이오 도구)로 바로 연결돼야 카드뉴스를 보고 관심 생긴 사람이 다음 행동으로 자연스럽게 이어집니다.")

h1("24-2장. 블로그로 검색 유입 만들기")
body("네이버 블로그ㆍ티스토리에 <b>내 전자책 주제와 관련된 정보성 글</b>을 올려두면, 검색을 통해 자연스럽게 관심 있는 사람들이 찾아옵니다. 광고처럼 보이면 클릭하지 않으니, 글 자체가 진짜 도움이 되는 정보여야 합니다.")
callout_box("검색 유입 글쓰기 요령", [
    "제목에 사람들이 실제로 검색할 법한 문장을 그대로 넣기(4장의 데이터랩에서 확인한 검색어 활용)",
    "글 앞부분에서 바로 핵심 정보 한두 가지를 무료로 공개하기 — 끝까지 안 읽으면 손해라는 느낌을 주지 않기",
    "글 마지막에 &ldquo;더 자세한 내용을 정리한 전자책&rdquo;이라고 자연스럽게 한 번만 언급하고 링크 연결하기",
    "한 번 쓰고 끝내지 않고, 관련 키워드로 여러 편을 이어서 발행해 검색 노출 범위를 넓히기",
])

h1("24-3장. 첫 서포터즈 모으기")
body("완전히 처음부터 낯선 사람에게 판매하기보다, <b>등록 전 지인ㆍ같은 관심사 커뮤니티 회원 3~5명</b>에게 완성본을 미리 보여주고 솔직한 의견을 받는 &ldquo;첫 서포터즈&rdquo; 단계를 거치면 훨씬 안전하게 출시할 수 있습니다.")
callout_box("서포터즈에게 요청할 것", [
    "오탈자ㆍ이해 안 되는 부분 표시해주기(10장의 &ldquo;지인 테스트&rdquo;와 연결)",
    "실제로 있었으면 하는 다른 정보가 있는지 물어보기",
    "괜찮다고 느꼈다면, 출시 후 가장 먼저 솔직한 후기를 남겨달라고 미리 부탁해두기",
])
body("이렇게 모은 첫 후기 2~3개는 상세페이지 화면비율상 가장 눈에 잘 띄는 초반 노출 구간을 채워주기 때문에, 완전히 후기 0개 상태로 시작하는 것보다 초기 전환율에 실질적인 도움이 됩니다.")

h1("25장. 후기 요청 타이밍과 방법")
body("후기는 판매량 다음으로 중요한 신뢰 지표입니다. 구매자가 실제로 다 읽어볼 시간(보통 구매 후 3~7일)이 지난 뒤에 정중하게 후기를 요청하는 메시지를 보내면 응답률이 높습니다.")
callout_box("후기 요청 시 주의할 점", [
    "허위 후기ㆍ대가성 후기(현금 등 직접 보상)는 표시광고법상 문제가 될 수 있습니다. &ldquo;솔직한 후기 부탁드립니다&rdquo; 정도의 요청은 괜찮지만, 좋은 평가를 조건으로 대가를 주는 건 피해야 합니다.",
    "부정적인 후기를 받았다면 감정적으로 대응하지 말고, 어떤 점이 부족했는지 구체적으로 물어 다음 개정판에 반영하세요. 이 과정 자체가 다른 잠재 구매자에게 신뢰를 줍니다.",
])

h1("25-2장. 출시 첫 달 실행 타임라인 예시")
body("무엇부터 해야 할지 막막하다면, 아래는 앞서 다룬 내용을 그대로 적용한 4주 실행 예시입니다. 자신의 상황에 맞게 순서나 기간을 조정해서 쓰면 됩니다.")
simple_table(
    ["시기", "할 일"],
    [
        ["1주차", "2부 방법으로 주제 확정, 3부로 목차 설계, 크몽ㆍ탈잉 판매자 가입"],
        ["2주차", "4부 원칙으로 집필 시작(핵심 챕터부터), 5부로 표지 시안 제작"],
        ["3주차", "집필 마무리, 6부 기준으로 이미지 정리, PDF 조판 및 오탈자 검토"],
        ["4주차", "크몽ㆍ탈잉 동시 등록, 무료 체험판 배포, SNS 카드뉴스 첫 게시"],
        ["5주차 이후", "지인ㆍ초기 구매자에게 후기 요청, 반응 보고 가격ㆍ상세페이지 수정"],
    ],
    [30 * mm, 136 * mm],
)

# ============================================================
# 10부
# ============================================================
part_page("PART 10", "세금 기초 상식", "이 부는 세무 자문이 아니라 &ldquo;처음 파는 사람이 알아야 할 최소한의 흐름&rdquo;입니다.<br/>구체적인 판단은 반드시 세무사ㆍ국세청에 확인하세요.")

h1("26장. 전자책을 팔면 세금은 어떻게 될까")
body("전자책 판매로 얻은 소득은 기본적으로 <b>사업소득 또는 기타소득</b>으로 신고 대상이 됩니다. 어느 쪽으로 분류되는지, 사업자등록이 필요한지는 판매 방식과 규모에 따라 달라지므로 국세청 홈택스(hometax.go.kr) 또는 세무사를 통해 본인의 상황을 확인하는 게 정확합니다.")
callout_box("플랫폼별로 알아두면 좋은 것", [
    "탈잉처럼 <b>정산 시 소득세 3.3%를 미리 원천징수</b>하는 플랫폼은 매년 5월 종합소득세 신고 때 이미 낸 세금을 정산(환급 또는 추가 납부)받는 구조입니다.",
    "크몽ㆍ부크크ㆍ유페이퍼처럼 원천징수 없이 정산해주는 곳은, 1년 동안의 수익을 스스로 합산해서 다음 해 5월에 종합소득세로 신고해야 합니다.",
    "스마트스토어처럼 사업자등록이 필요한 채널은 부가가치세 신고(통상 연 2회)도 함께 해야 합니다.",
    "여러 플랫폼에서 동시에 판매한다면, 각 플랫폼의 정산 내역(엑셀 다운로드 등)을 미리 모아두면 연말 신고가 훨씬 수월합니다.",
])
simple_table(
    ["과세표준 구간", "세율"],
    [
        ["1,400만원 이하", "6%"],
        ["1,400만원 초과 ~ 5,000만원 이하", "15%"],
        ["5,000만원 초과 ~ 8,800만원 이하", "24%"],
        ["8,800만원 초과 ~ 1억 5,000만원 이하", "35%"],
        ["1억 5,000만원 초과 ~ 10억원 이하", "38~45%(구간별 차등)"],
    ],
    [90 * mm, 76 * mm],
)
body("<i>(2026년 기준 종합소득세 세율 구간, 국세청 공시 기준 ㆍ 과세표준은 총소득에서 경비ㆍ소득공제를 뺀 금액이므로, 실제 판매 금액과는 다릅니다.)</i> 전자책 부업 초기 단계라면 대부분 6~15% 구간에 해당하는 경우가 많지만, 본업 소득과 합산되면 구간이 달라질 수 있으니 정확한 세율은 신고 시점에 다시 확인하세요.")
body("감이 잘 안 잡힌다면 아래처럼 첫 구간(6%)만으로 단순 계산해보세요. 실제로는 다른 소득과 합산되거나 각종 공제가 더해져 최종 금액이 달라지므로, 어디까지나 &ldquo;대략적인 규모&rdquo;를 가늠하는 용도로만 참고하세요.")
callout_box("단순 계산 예시(첫 구간 기준)", [
    "전자책 판매로 번 돈에서 경비(디자인 툴 결제, 광고비 등)를 뺀 과세표준이 300만원이라고 가정하면, 표의 첫 구간(1,400만원 이하ㆍ6%)에 해당하므로 300만원 &times; 6% = 18만원 수준으로 어림잡아 볼 수 있습니다.",
    "과세표준이 1,000만원이라면 같은 첫 구간 안에 있으므로 1,000만원 &times; 6% = 60만원 수준입니다.",
    "과세표준이 1,400만원을 넘어가면 초과분부터 다음 구간(15%) 세율이 적용되는 <b>누진 구조</b>이므로, 이 지점부터는 단순 곱셈으로 어림잡기보다 홈택스의 예상 세액 계산 서비스를 이용하는 게 정확합니다.",
])
body("처음 시작하는 단계에서는 <b>&ldquo;수익이 나면 반드시 신고 대상이 된다&rdquo;는 사실만 기억</b>하고, 실제 신고 시점(다음 해 5월)에 국세청 홈택스의 안내를 따라가거나 세무사에게 정산 내역을 전달해 도움을 받는 것을 권장합니다. 국세청 홈택스는 종합소득세 신고 기간에 맞춰 신고 안내와 예상 세액 계산 서비스를 제공합니다.")

h1("26-2장. 사업소득과 기타소득, 무엇이 다를까")
body("전자책 판매가 <b>계속ㆍ반복적으로</b> 이뤄지면 사업소득으로, 아주 가끔 한두 번 있는 일시적인 수입이면 기타소득으로 분류되는 게 일반적인 기준입니다. 사업자등록 여부와 무관하게 실제로 반복해서 판매하고 있다면 사업소득으로 보는 게 원칙에 가까우므로, 판매가 꾸준히 이어진다면 사업자등록을 검토하는 게 안전합니다.")
callout_box("함께 알아두면 좋은 개념", [
    "경비 처리 — 디자인 도구 유료 결제, 광고비, 통신비 등 전자책을 만들고 파는 데 실제로 쓴 비용은 소득에서 빼고(경비 처리) 신고할 수 있어, 세금 부담을 줄여줍니다. 지출 증빙(영수증, 결제 내역)을 평소에 모아두는 습관이 중요합니다.",
    "현금영수증 발급 의무 — 사업자등록을 한 통신판매업자는 건당 일정 금액 이상 현금 거래 시 현금영수증을 의무적으로 발급해야 하는 경우가 있습니다. 스마트스토어처럼 직접 결제를 받는 채널을 쓴다면 이 부분도 확인이 필요합니다.",
    "간이과세자ㆍ일반과세자 — 사업자등록 시 연 매출 규모에 따라 부가가치세 부담이 다른 유형으로 등록됩니다. 처음 시작 단계에서는 대부분 간이과세자로 등록해 세금 부담을 낮출 수 있습니다.",
])

h1("26-3장. 사업자등록, 언제부터 해야 할까")
body("&ldquo;얼마나 팔려야 사업자등록을 해야 하나요?&rdquo;라는 질문을 자주 받습니다. 명확한 매출 기준선이 법으로 못박혀 있다기보다, <b>계속ㆍ반복적으로 판매하는 사업 활동으로 볼 수 있는 시점</b>부터 등록 의무가 생긴다고 보는 게 정확합니다.")
callout_box("현실적인 판단 기준", [
    "한두 번의 우연한 판매 → 기타소득으로 신고하는 것으로 충분한 경우가 많습니다.",
    "꾸준히, 정기적으로 판매가 이어지는 상태 → 사업자등록을 검토해야 하는 시점입니다.",
    "스마트스토어처럼 사업자등록이 필수인 채널을 쓰기로 했다면 → 판매 시작 전에 미리 등록해야 합니다.",
    "정확한 시점 판단이 어렵다면, 세무서 문의 또는 홈택스 상담 서비스를 통해 본인의 상황을 확인하는 것이 가장 정확합니다.",
])

# ============================================================
# 11부
# ============================================================
part_page("PART 11", "실전 사례 여덟 가지 유형", "아래 사례는 이해를 돕기 위해 만든 가상의 예시이며, 실제 인물이 아닙니다.")

h1("27장. 유형별 가상 사례")
body("여덟 가지 사례는 이 가이드에서 다룬 방법(2부 주제 검증, 7부 플랫폼 선택, 8부 가격, 9부 마케팅)이 실제로 어떻게 조합되는지 보여주기 위한 것입니다. 자신의 상황과 가장 비슷한 사례를 찾아, 그 사례가 무엇을 했고 무엇을 놓쳤는지 참고해보세요.")
h2("사례 A. 자격증 준비생 — 정보 구조화형")
body("특정 자격시험을 준비하며 만든 오답노트를 정리해 &ldquo;시험 3주 전 압축 요약노트&rdquo;로 만든 경우입니다. 기출문제(공개 자료)를 기반으로 했기 때문에 저작권 문제가 없고, 같은 시험을 준비하는 사람들 사이에서 꾸준히 검색되는 주제라 장기적으로 판매가 이어지는 편입니다. 시험 접수 시작 직전처럼 수요가 몰리는 시점에 맞춰 출시하면, 이후 매 회차 접수 시기마다 검색량이 반복해서 오르는 계절성을 노릴 수 있습니다.")
h2("사례 B. 업무 툴 활용러 — 실습형")
body("회사에서 매일 쓰는 스프레드시트 자동화 기능을 정리해 전자책으로 만든 경우입니다. 스크린샷과 함께 &ldquo;따라 하면 되는&rdquo; 형태로 구성해 실용성이 높고, 실제로 써보고 궁금한 점을 묻는 후기가 달리기 쉬운 유형입니다. 이런 후기 질문들을 모아 &ldquo;자주 묻는 질문&rdquo; 챕터로 추가하면, 그 챕터 자체가 다음 구매자에게 &ldquo;질문에 성실히 답해주는 책&rdquo;이라는 신뢰 신호가 됩니다.")
h2("사례 C. 저가 경쟁 실패 사례")
body("이미 포화 상태인 주제(범용적인 &ldquo;SNS 운영 꿀팁&rdquo; 등)를 차별점 없이 요약만 해서 최저가로 등록했다가, 비슷한 상품이 너무 많아 노출조차 되지 않은 경우입니다. 이 사례에서 얻는 교훈은 <b>가격보다 &ldquo;남과 다른 각도&rdquo;가 먼저</b>라는 것입니다. 3-2장의 비교표 방법으로 경쟁 상품과 다른 각도(예: 특정 업종 전용으로 좁히기)를 먼저 찾은 뒤 가격을 정하는 순서가 안전합니다.")
h2("사례 D. 플랫폼 다각화 사례")
body("크몽에서 먼저 반응을 확인한 뒤, 같은 콘텐츠를 부크크에서 정식 ISBN 책으로도 등록해 &ldquo;정식 출간 도서&rdquo;라는 신뢰도를 더한 경우입니다. 두 채널의 가격을 다르게 책정(부크크 쪽을 소폭 높게)해 채널 간 카니발라이제이션(자기잠식)을 줄였습니다. 크몽 구매자는 &ldquo;바로 받아보는 PDF&rdquo;라는 즉시성을, 부크크 구매자는 &ldquo;정식 ISBN이 있는 책&rdquo;이라는 신뢰도를 각각 다른 이유로 선택하는 경향이 있어, 같은 콘텐츠라도 채널별로 소구점을 다르게 잡는 것이 유리합니다.")
h2("사례 E. 개정판 전략 사례")
body("첫 출시 후 들어온 질문과 후기를 모아 3개월 뒤 개정판을 내면서 &ldquo;개정 2판, 최신 정보 반영&rdquo;이라는 문구로 재홍보한 경우입니다. 기존 구매자에게는 무료 업데이트를 제공해 신뢰를 쌓고, 신규 구매자에게는 &ldquo;계속 관리되는 책&rdquo;이라는 인상을 줬습니다. 개정 소식을 기존 구매자에게 안내하는 것만으로도 자발적인 후기 갱신을 유도할 수 있어, 별도 마케팅 비용 없이 후기 수를 늘리는 방법으로도 활용됩니다.")
h2("사례 F. 법적 리스크를 피해간 사례")
body("처음에는 &ldquo;세금 신고 대신 해드립니다&rdquo;처럼 대행성 문구로 기획했다가, 5장에서 다룬 세무사법 이슈를 뒤늦게 확인하고 &ldquo;신고 절차를 이해하기 쉽게 정리한 안내서&rdquo;로 컨셉을 바꿔 출시한 경우입니다. 기획 초기에 법적 경계를 먼저 확인하는 습관의 중요성을 보여줍니다.")
h2("사례 G. 무료 배포 후 유료 전환 사례")
body("처음에는 짧은 요약본을 블로그에 무료로 공개해 반응과 질문을 모은 뒤, 질문에 대한 답과 더 깊은 사례를 더해 유료 전자책으로 확장한 경우입니다. 무료 버전에서 이미 신뢰를 쌓았기 때문에, 유료 전환 후에도 기존 독자 중 상당수가 구매로 이어졌습니다.")
h2("사례 H. 협업으로 분량을 채운 사례")
body("혼자서는 다루기 어려운 실전 사례 부분을, 같은 분야에서 활동하는 지인 두 명에게 사례 코너 집필을 부탁해 채운 경우입니다. 공동 집필 사실과 각자의 역할을 표지ㆍ서문에 정직하게 밝혀 신뢰를 지켰습니다. 공동 집필자의 이름과 기여 부분을 명확히 표기한 것은 용어 사전의 &ldquo;저작인격권(성명표시권)&rdquo;을 지키기 위한 것이기도 했습니다.")
h2("여덟 사례 한눈에 보기")
simple_table(
    ["사례", "핵심 전략", "주로 얻는 교훈"],
    [
        ["A. 자격증 요약형", "공개 기출 기반 정보 구조화", "계절성에 맞춘 출시 타이밍"],
        ["B. 업무 툴 실습형", "스크린샷+따라하기 구성", "후기 질문을 개정판에 반영"],
        ["C. 저가 경쟁 실패", "차별점 없이 최저가 경쟁", "가격보다 차별화가 먼저"],
        ["D. 플랫폼 다각화", "크몽+부크크 동시 운영", "채널마다 다른 구매 이유"],
        ["E. 개정판 전략", "기존 구매자 무료 업데이트", "신뢰가 후기로 이어짐"],
        ["F. 법적 리스크 회피", "컨셉을 정보제공형으로 전환", "기획 초기 법적 검토"],
        ["G. 무료→유료 전환", "블로그 무료 공개 후 확장", "무료 버전이 신뢰를 만듦"],
        ["H. 협업 사례", "역할 분담+정직한 표기", "혼자 다 하지 않아도 됨"],
    ],
    [30 * mm, 68 * mm, 68 * mm],
)
callout_box("여섯ㆍ일곱ㆍ여덟 사례에서 공통적으로 얻는 교훈", [
    "먼저 작게 시도해서 반응을 확인한 뒤 확장하는 쪽이, 처음부터 완벽하게 만들려는 쪽보다 실패 확률이 낮습니다.",
    "혼자 다 하려고 하지 않아도 됩니다. 부족한 부분은 협업ㆍ외주로 채우되, 그 사실을 독자에게 정직하게 밝히세요.",
    "법적 경계(2부 5장)는 기획 단계에서 먼저 확인하는 습관이 나중에 컨셉을 통째로 바꾸는 수고를 막아줍니다.",
])

# ============================================================
# 12부
# ============================================================
part_page("PART 12", "자주 하는 실수 열 가지", "먼저 만들어본 사람들이 공통적으로 겪는 함정입니다.")

h1("28장. 실수 열 가지와 해결법")
body("아래 열 가지는 이 가이드 전체에서 다룬 내용 중, 실제로 가장 자주 놓치는 지점만 뽑아 다시 정리한 것입니다. 각 항목 아래에 왜 이게 문제가 되는지 조금 더 풀어서 설명합니다.")
h2("1. 제목에 검색 키워드를 안 넣는다")
body("감성적인 제목(&ldquo;인생을 바꾸는 노트&rdquo;)은 이미 내 상품을 알고 있는 사람에게는 매력적일 수 있지만, 검색으로 처음 찾아오는 사람에게는 아예 노출되지 않습니다. &ldquo;OO자격증 요약노트&rdquo;처럼 검색될 단어를 제목 앞부분에 그대로 쓰는 게 훨씬 유리합니다(16-3장).")
h2("2. 표지에 글자를 너무 작게 넣는다")
body("목록 화면에서는 표지가 엄지손톱만 한 크기로 줄어들어 보입니다. 편집 화면에서 크게 잘 보이던 글자도 실제 목록에서는 안 보일 수 있으니, 완성 후 표지 이미지를 축소해서 직접 확인하는 습관이 필요합니다(11ㆍ11-2장).")
h2("3. 완벽해질 때까지 출시를 미룬다")
body("첫 버전은 80점이면 충분합니다. 후기와 질문을 받으며 개정하는 쪽이, 완벽한 버전을 혼자 만들겠다고 미루는 쪽보다 훨씬 빠르게 실제 결과로 이어집니다(7장, 사례 E).")
h2("4. 한 플랫폼에만 의존한다")
body("플랫폼마다 이용자층과 노출 방식이 다릅니다. 한 곳에서 반응이 없다고 주제 자체가 안 팔리는 건 아닐 수 있으니, 최소 2곳 이상에 등록해 노출을 분산하세요(7부).")
h2("5. 가격을 한 번 정하고 절대 안 바꾼다")
body("초기 가격은 어디까지나 추정치입니다. 부록8의 지표를 보며 전환율이 낮다면 가격을, 노출은 되는데 구매가 안 된다면 상세페이지를 조정하는 식으로 계속 실험하는 게 정상입니다(8부).")
h2("6. 저작권 확인 없이 이미지를 쓴다")
body("&ldquo;이미지 하나쯤이야&rdquo;라는 생각이 가장 위험합니다. 15-3장에서 다뤘듯 저작권 문제는 실제로 판매 중지ㆍ손해배상까지 이어질 수 있으니, 6부의 우선순위(직접 캡처 → 무료 스톡 → 도구 제공 소재)를 항상 지키세요.")
h2("7. 출처 표기를 생략한다")
body("통계ㆍ법 조항ㆍ수수료처럼 확인 가능한 정보는 출처와 조사 시점을 함께 적어야 신뢰를 얻고, 나중에 정보가 바뀌어도 &ldquo;거짓 정보&rdquo;가 아니라 &ldquo;그 시점 기준 정보&rdquo;로 남습니다(8장).")
h2("8. 후기 요청을 아예 안 한다")
body("구매자는 먼저 나서서 후기를 남기지 않는 경우가 대부분입니다. 24-3장의 서포터즈, 25장의 후기 요청 타이밍을 활용해 정중하게 요청하는 것만으로 후기 수가 크게 달라집니다.")
h2("9. 마케팅을 등록 당일 한 번만 한다")
body("카드뉴스ㆍ블로그 글 같은 홍보는 한 번 올린다고 끝나지 않습니다. 25-2장의 타임라인처럼 최소 몇 주에 걸쳐 반복해야 효과가 쌓입니다.")
h2("10. 법적 경계를 마지막에 확인한다")
body("사례 F처럼, 기획을 다 끝낸 뒤에야 법적 문제를 발견하면 컨셉을 통째로 바꿔야 할 수도 있습니다. 5장의 체크리스트는 반드시 기획 단계에서 가장 먼저 확인하세요.")

# ============================================================
# 13부
# ============================================================
part_page("PART 13", "자주 묻는 질문(FAQ)", "")

h1("29장. FAQ")
h2("Q. 사업자등록이 꼭 있어야 하나요?")
body("크몽ㆍ탈잉ㆍ부크크ㆍ유페이퍼는 개인 자격으로도 등록ㆍ판매할 수 있습니다. 스마트스토어에서 직접 판매하려면 사업자등록이 필요합니다. 다만 어느 채널이든 수익이 계속 발생하면 세금 신고 의무는 생기므로 10부를 참고하세요.")
h2("Q. 표지나 디자인을 못 해도 되나요?")
body("12ㆍ13장에서 다룬 미리캔버스ㆍ눈누 같은 무료 도구만으로도 충분히 시작할 수 있습니다. 디자인 실력보다 &ldquo;제목에서 무슨 내용인지 바로 알 수 있는가&rdquo;가 훨씬 중요합니다.")
h2("Q. 분량이 적으면 안 팔리나요?")
body("절대적인 페이지 수보다 &ldquo;이 가격에 이 정보를 받는 게 합리적인가&rdquo;가 더 중요합니다. 다만 3부에서 다뤘듯, 억지로 채운 분량은 오히려 신뢰를 깎습니다. 진짜 정보로 채운 자연스러운 분량을 목표로 하세요.")
h2("Q. 이미 비슷한 책이 많은데 시작해도 될까요?")
body("3장에서 설명했듯, 경쟁자가 있다는 건 오히려 수요가 검증됐다는 신호입니다. 기존 상품의 리뷰를 읽고 &ldquo;아직 안 채워진 부분&rdquo;을 찾아 그 지점을 더 깊게 다루면 차별화할 수 있습니다.")
h2("Q. 한 번 만들면 계속 팔리나요?")
body("사례 E처럼 정기적으로 개정하고, 9부의 마케팅을 꾸준히 반복해야 판매가 이어집니다. 만들어서 올려두기만 하고 손을 놓으면 시간이 지날수록 노출 순위에서 밀리는 경우가 많습니다.")
h2("Q. 여러 권을 동시에 준비해도 되나요?")
body("처음에는 한 권을 완성해서 전체 과정(2부~9부)을 한 번 경험해보는 것을 권장합니다. 첫 권에서 얻은 노하우(어떤 플랫폼이 잘 맞는지, 어떤 마케팅이 효과 있었는지)를 다음 권에 그대로 적용하면 두 번째부터는 훨씬 빨라집니다.")
h2("Q. AI로 쓴 티가 나면 안 팔리나요?")
body("독자는 &ldquo;AI로 썼는지 사람이 썼는지&rdquo;보다 &ldquo;내용이 정확하고 도움이 되는지&rdquo;를 훨씬 중요하게 봅니다. 9장에서 다뤘듯 AI는 어디까지나 보조 도구로 쓰고, 실제 경험ㆍ사례ㆍ직접 확인한 최신 정보를 충분히 섞으면 내용의 질 자체로 승부할 수 있습니다.")
h2("Q. 무료로 배포하는 것과 유료로 파는 것, 뭐가 더 나을까요?")
body("사례 G처럼 짧은 무료 버전으로 반응을 먼저 확인하고, 반응이 좋으면 더 깊은 유료 버전으로 확장하는 순서가 안전합니다. 처음부터 전부 무료로 풀면 유료 전환이 오히려 어려워질 수 있습니다.")
h2("Q. 개정판을 낼 때 기존 구매자에게도 알려야 하나요?")
body("사례 E처럼 기존 구매자에게 무료로 업데이트를 제공하는 것이 신뢰를 지키는 방법입니다. 플랫폼별로 파일 재업로드 방식이 다르니, 각 플랫폼의 판매자 센터에서 업데이트 공지ㆍ재전송 기능을 확인하세요.")
h2("Q. 사진이나 스크린샷이 하나도 없어도 되나요?")
body("텍스트만으로 구성된 전자책도 가능하지만, 6부에서 다룬 대로 화면이나 절차를 설명하는 주제라면 스크린샷이 있는 쪽이 훨씬 신뢰를 얻기 쉽습니다. 개념 설명형 주제(용어 정리, 이론 해설)라면 표ㆍ도식으로 대체할 수 있습니다.")
h2("Q. 판매가 전혀 안 되면 어떻게 해야 하나요?")
body("12부의 자주 하는 실수 목록을 다시 점검하고, 특히 제목에 검색 키워드가 들어있는지, 최소 2곳 이상에 등록했는지, 상세페이지에 목차를 공개했는지부터 확인하세요. 그래도 반응이 없다면 2부로 돌아가 주제 자체의 수요를 다시 검증해보는 것도 방법입니다.")
h2("Q. 표지 시안을 여러 개 만들 시간이 없어요.")
body("14-1-2장처럼 정교한 A/B 테스트를 못 하더라도, 최소한 가족ㆍ친구 한두 명에게 완성된 표지를 보여주고 &ldquo;이 표지만 보고 어떤 내용인지 알겠는지&rdquo; 물어보는 것만으로도 큰 실수는 걸러낼 수 있습니다.")
h2("Q. 경쟁 상품보다 내용이 부족한 것 같아 불안해요.")
body("3-2장의 비교표를 다시 만들어, 경쟁 상품에 없는 부분이 내 책에 하나라도 있는지 확인해보세요. 모든 면에서 이길 필요는 없습니다. 한 가지 확실한 차별점만 있어도 그 지점을 원하는 독자에게는 최선의 선택이 됩니다.")
h2("Q. 여러 플랫폼에 등록했는데 개정판 관리가 너무 번거로워요.")
body("20-3장의 파일 버전 관리 요령을 먼저 적용해보세요. 채널이 3곳을 넘어가면 관리가 부담스러워지는 게 자연스러우니, 반응이 가장 좋은 1~2곳에 집중하고 나머지는 정리하는 것도 방법입니다.")

# ============================================================
# 14부
# ============================================================
part_page("PART 14", "롱런 전략 — 시리즈화와 확장", "한 권을 다 팔고 나면 다음은 무엇을 해야 할까요.")

h1("30장. 시리즈화 — 한 권을 여러 권으로 나누기")
body("반응이 좋았던 전자책은 <b>주제를 더 잘게 쪼개서 시리즈로 확장</b>할 수 있습니다. 예를 들어 &ldquo;OO자격증 요약노트&rdquo; 한 권이 잘 팔렸다면, 과목별ㆍ난이도별로 나눠 &ldquo;심화편&rdquo;, &ldquo;최종 모의고사편&rdquo;처럼 이어지는 시리즈를 만들 수 있습니다.")
callout_box("시리즈화가 유리한 이유", [
    "이미 1권을 산 독자는 2권을 살 때 고민을 훨씬 덜 합니다 — 새로운 신뢰를 처음부터 쌓을 필요가 없습니다.",
    "시리즈 전체를 묶어 &ldquo;세트 할인&rdquo;으로 판매하면 객단가(한 번에 결제하는 금액)를 자연스럽게 높일 수 있습니다.",
    "검색 노출 측면에서도 같은 저자의 상품이 여러 개 걸리면 신뢰도가 함께 올라갑니다.",
])

h1("31장. 번들ㆍ묶음 판매와 구독형으로의 확장")
body("전자책 여러 권이 쌓이면, 개별 판매 외에 <b>묶음(번들) 판매</b>나 <b>월 구독형 자료실</b>로 확장하는 것도 가능합니다. 예를 들어 매달 새로운 요약 자료를 추가해주는 형태로 운영하면, 한 번 팔고 끝나는 구조에서 벗어나 꾸준한 수입 구조로 이어질 수 있습니다.")
callout_box("확장을 고려할 때 체크할 것", [
    "구독형으로 운영하려면 &ldquo;매달 새로 줄 것&rdquo;이 실제로 있어야 합니다 — 콘텐츠 없이 형식만 구독으로 바꾸면 해지만 늘어납니다.",
    "번들 판매는 개별 구매보다 확실히 저렴하게 느껴지는 가격 차이를 둬야 실제로 묶어서 사는 유인이 생깁니다.",
    "플랫폼에 따라 구독형 판매를 지원하지 않는 곳도 있으므로(7부), 구독형을 계획한다면 등록 전에 해당 플랫폼의 지원 여부를 먼저 확인하세요.",
])
body("처음부터 이 단계를 목표로 할 필요는 없습니다. 1권을 완성해서 팔아보고(1~13부), 반응이 쌓이면 그때 이 장으로 돌아와 다음 단계를 고민해도 늦지 않습니다.")

h2("번들 가격 계산 예시")
body("시리즈 3권이 각각 19,000원이라면 개별 구매 합계는 57,000원입니다. 번들 할인을 20%로 잡으면 번들 가격은 45,600원이 되어, 독자 입장에서는 &ldquo;11,400원을 아꼈다&rdquo;는 명확한 이득이 생기고, 판매자 입장에서는 3권을 따로따로 마케팅하는 것보다 <b>객단가(부록 용어 참고)를 한 번에 높이는 효과</b>를 얻습니다.")

h1("31-2장. 강의ㆍ워크숍으로 연결하기")
body("전자책이 어느 정도 반응을 얻었다면, 같은 내용을 <b>실시간 강의나 워크숍</b>으로 확장하는 것도 자연스러운 다음 단계입니다. 전자책 구매자 중 &ldquo;직접 물어보고 싶다&rdquo;는 수요가 있다면 이미 검증된 신호입니다.")
callout_box("확장 방법 예시", [
    "탈잉ㆍ인프런처럼 이미 강의 등록 기능이 있는 플랫폼에 같은 주제로 강의를 추가로 개설하기",
    "전자책 구매자 대상으로 소규모 질의응답 세션(온라인 화상)을 별도 유료로 열기",
    "전자책 내용을 발표 자료로 재구성해 오프라인 소모임ㆍ스터디에서 활용하기",
])
body("이렇게 확장하면 <b>같은 지식을 여러 형태(글ㆍ영상ㆍ실시간)로 판매</b>하게 되어, 한 사람의 시간과 지식을 여러 채널에서 반복해서 수익으로 연결할 수 있습니다.")

h2("이 가이드 자체도 하나의 예시입니다")
body("지금 읽고 계신 이 가이드도 2부(주제 검증) → 3부(목차 설계) → 4~6부(집필ㆍ디자인) → 7~9부(등록ㆍ가격ㆍ마케팅)의 순서를 그대로 따라 만들어졌습니다. 15부의 가상 사례처럼, 실제로 이 순서를 하나씩 밟아가면 누구나 자신의 지식을 전자책 한 권으로 완성할 수 있습니다.")

# ============================================================
# 15부
# ============================================================
part_page("PART 15", "처음부터 끝까지 — 하나의 가상 사례로 전체 과정 따라가기", "지금까지 배운 내용을 하나의 예시에 그대로 적용해봅니다.<br/>가상의 예시이며 실제 상품이 아닙니다.")

h1("32장. 주제 확정하기")
body("&ldquo;회사에서 엑셀은 쓰는데 함수는 잘 모른다&rdquo;는 사람을 대상으로 한 전자책을 기획한다고 가정해보겠습니다. 2부의 방법을 그대로 적용하면 다음과 같은 확인 과정을 거치게 됩니다.")
callout_box("2부 방법 적용 결과(가상)", [
    "3장(크몽 검색) — &ldquo;엑셀 함수&rdquo;, &ldquo;엑셀 실무&rdquo;로 검색하면 이미 여러 상품이 꾸준한 리뷰를 쌓고 있는 것을 확인(경쟁 시장 = 안전 신호)",
    "4장(데이터랩) — &ldquo;엑셀 vlookup&rdquo;, &ldquo;엑셀 피벗테이블&rdquo; 검색량이 연중 꾸준한 것을 확인(계절성 없이 안정적)",
    "4-2장(커뮤니티) — 지식iN에 &ldquo;vlookup 안 될 때&rdquo;, &ldquo;피벗테이블 오류&rdquo; 질문이 반복적으로 올라오는 것을 확인",
    "5장(법적 검토) — 엑셀 사용법은 순수한 정보 구조화형(Type A)이라 법적 리스크 없음",
])
body("이 네 가지를 종합하면 &ldquo;이미 검증된 수요가 있고, 커뮤니티에는 아직 명쾌하게 안 풀린 질문이 있다&rdquo;는 결론에 도달합니다. 여기서 <b>&ldquo;자주 막히는 오류 해결&rdquo;을 중심 컨셉</b>으로 잡기로 확정합니다.")

h1("33장. 목차 초안 짜기")
body("6장의 &ldquo;5분컷+참고자료&rdquo; 구조를 적용하면 아래처럼 목차 초안이 나옵니다.")
simple_table(
    ["부", "내용"],
    [
        ["1부", "5분 컷 — 자주 막히는 오류 TOP 5와 원인"],
        ["2부", "함수별 상세 — VLOOKUP, IF, SUMIF, 피벗테이블 등"],
        ["3부", "실무 상황별 적용 — 매출표, 근태표, 재고표 만들기"],
        ["4부", "오류 메시지 사전 — #N/A, #REF! 등 원인과 해결법"],
        ["5부", "FAQㆍ용어 사전ㆍ단축키 모음"],
    ],
    [24 * mm, 142 * mm],
)
body("7장에서 강조했듯, 이 단계에서 페이지 수를 미리 정하지 않습니다. 각 부를 실제로 채워보면서 2부(함수 개수만큼)와 4부(오류 메시지 개수만큼)가 자연스럽게 가장 두꺼워질 것으로 예상할 수 있습니다.")

h1("34장. 표지ㆍ상세페이지 문구 완성본 예시")
body("11ㆍ16-2ㆍ부록3에서 다룬 원칙을 그대로 적용하면 아래와 같은 결과물이 나옵니다.")
callout_box("표지 문구", [
    "제목: &ldquo;엑셀 함수, 이제 오류 없이 씁니다&rdquo;",
    "부제: &ldquo;VLOOKUPㆍ피벗테이블 자주 막히는 지점만 모았습니다&rdquo;",
    "핵심 숫자: &ldquo;오류 메시지 12종 해결법 수록&rdquo;",
])
callout_box("상세페이지 도입부(21-2장 좋은 예 형식 적용)", [
    "&ldquo;VLOOKUP은 아는데 막상 쓰면 #N/A만 뜨시나요?&rdquo;",
    "&ldquo;이 가이드는 엑셀 함수를 &lsquo;배우는&rsquo; 책이 아니라, 실무에서 &lsquo;막히는 지점&rsquo;만 골라 해결하는 책입니다.&rdquo;",
    "&ldquo;총 4부 구성ㆍ실제 오류 화면 12장 수록ㆍ현직 실무자 사례 3가지 포함&rdquo;",
])
h2("여러 공식이 하나로 수렴하는지 확인하기")
body("가격 끝자리(22-3장)는 저가 진입 전략에 맞춰 19,000원처럼 9로 끝나는 표기를 선택하고, 제목 공식(부록2)의 [대상]+[핵심 키워드]+[형태/차별점]에 대입하면 <b>[회사원]+[엑셀 함수]+[오류 해결 중심]</b>이 되어, 실제 제목 &ldquo;엑셀 함수, 이제 오류 없이 씁니다&rdquo;와 정확히 맞아떨어지는 것을 확인할 수 있습니다. 이렇게 앞서 배운 여러 공식이 서로 어긋나지 않고 하나의 결과로 수렴하는지 확인하는 것이 이 worked example의 목적입니다.")

h1("35장. 가격과 등록 계획")
body("8부의 저가 진입 전략과 7부의 플랫폼 비교를 적용하면, 이 예시는 다음과 같은 계획으로 이어질 수 있습니다.")
callout_box("적용 계획(가상)", [
    "가격: 첫 출시 19,000원(저가 진입) → 후기 20개 이상 쌓이면 24,000원으로 조정",
    "플랫폼: 크몽(1순위, 진입장벽 낮음)에 먼저 등록 후 2주 뒤 탈잉 추가",
    "마케팅: 오류 메시지 12종 중 3종을 요약한 무료 체험판 PDF를 상세페이지에 첨부",
    "세금: 개인 자격으로 시작하되, 월 수익이 꾸준히 발생하면 10부 기준으로 사업자등록 검토",
])
body("이렇게 2부부터 10부까지의 방법을 하나의 흐름으로 이어보면, 각 부가 따로 노는 게 아니라 <b>&ldquo;주제 확정 → 목차 → 문구 → 등록ㆍ가격&rdquo;으로 이어지는 하나의 절차</b>라는 걸 알 수 있습니다. 실제로 자신의 주제로 이 과정을 따라 해보는 것이 이 가이드를 가장 잘 활용하는 방법입니다.")
h2("이 예시를 자신의 주제로 바꿔 적용하는 법")
body("지금까지 본 엑셀 예시의 각 단계에서 &ldquo;엑셀&rdquo; 대신 자신의 주제를 넣고, &ldquo;VLOOKUP 오류&rdquo; 대신 자신의 분야에서 사람들이 자주 막히는 지점을 넣어보세요. 32장의 네 가지 확인(크몽ㆍ데이터랩ㆍ커뮤니티ㆍ법적 검토)부터 순서대로 직접 해보는 것이 이 워크스루를 가장 잘 활용하는 방법입니다. 표나 목록에 있는 문장을 그대로 베끼지 말고, 자신이 실제로 조사한 숫자와 표현으로 바꿔 채워야 진짜 자신의 전자책 기획이 됩니다.")

h1("36장. 실제 본문 발췌 예시")
body("33장 목차의 &ldquo;4부. 오류 메시지 사전&rdquo; 중 한 챕터를 실제로 완성된 본문처럼 써보면 아래와 같은 모습이 됩니다. 10-1-2장의 도입부 공식, 10-2장의 쉬운 문장 원칙, 8장의 자료조사 원칙이 실제로 어떻게 녹아드는지 확인해보세요.")
quote("<b>VLOOKUP에서 #N/A가 뜰 때 확인할 5가지</b>")
body("VLOOKUP 함수를 분명히 맞게 입력한 것 같은데 #N/A가 뜬다면, 아래 다섯 가지를 순서대로 확인해보세요. 대부분 이 안에서 원인이 발견됩니다.")
callout_box("확인 순서", [
    "1. 찾는 값과 찾는 표의 값 사이에 <b>보이지 않는 공백</b>이 섞여 있지 않은지 — 특히 다른 시스템에서 복사해온 데이터에 자주 생깁니다.",
    "2. 숫자가 <b>텍스트 형식</b>으로 저장돼 있지 않은지 — 셀 왼쪽 정렬로 보이면 텍스트일 가능성이 큽니다.",
    "3. 찾는 범위의 <b>첫 번째 열</b>에 찾는 값이 있는지 — VLOOKUP은 항상 범위의 첫 열에서만 값을 찾습니다.",
    "4. 마지막 옵션을 <b>FALSE(정확히 일치)</b>로 지정했는지 — 생략하면 근사값을 찾아 엉뚱한 결과가 나올 수 있습니다.",
    "5. 참조 범위를 <b>절대참조($)</b>로 고정했는지 — 아래로 수식을 복사하면서 범위가 밀려났을 수 있습니다.",
])
body("이 다섯 가지를 순서대로 확인해도 해결되지 않는다면, 셀 서식을 &ldquo;일반&rdquo;으로 바꾼 뒤 값을 한 번 더 입력해보는 것도 방법입니다. 엑셀이 자동으로 서식을 추측하면서 눈에 안 보이는 차이를 만들어내는 경우가 실무에서 생각보다 흔합니다.")
simple_table(
    ["오류 메시지", "가장 흔한 원인"],
    [
        ["#N/A", "찾는 값이 범위 첫 열에 없거나 공백ㆍ서식 불일치"],
        ["#REF!", "참조하던 셀이 삭제되거나 이동됨"],
        ["#VALUE!", "숫자가 필요한 자리에 텍스트가 섞여 있음"],
        ["#DIV/0!", "0 또는 빈 셀로 나누기를 시도함"],
        ["#NAME?", "함수 이름 오타 또는 지원하지 않는 함수 사용"],
    ],
    [30 * mm, 136 * mm],
)
body("이 짧은 예시 하나에서도 <b>&ldquo;무엇이 문제인지&rdquo;가 아니라 &ldquo;어떤 순서로 확인해야 하는지&rdquo;</b>를 알려주는 방식을 썼습니다. 정보를 나열하기보다 &ldquo;독자가 지금 이 문제를 겪고 있다면 뭘 먼저 해야 하는지&rdquo; 순서를 잡아주는 게 정보 구조화형 콘텐츠의 핵심 가치입니다.")

h1("37장. 두 번째 예시 — 자격증 요약형은 어떻게 다를까")
body("실습형(엑셀)과는 결이 다른 <b>자격증 요약형</b> 주제도 같이 살펴보겠습니다. 국가공인 사무 자격증인 컴퓨터활용능력을 예로 들어보면, 32~35장과 같은 순서를 적용했을 때 강조점이 어떻게 달라지는지 비교할 수 있습니다.")
simple_table(
    ["구분", "실습형(엑셀 예시)", "요약형(자격증 예시)"],
    [
        ["2부에서 확인할 것", "커뮤니티 오류 질문 빈도", "최근 3개년 기출 출제 비중"],
        ["3부 목차 뼈대", "오류 메시지별 해결법", "과목별ㆍ배점별 핵심 요약"],
        ["4부 집필에서 강조", "단계별 스크린샷", "암기 포인트와 오답 패턴"],
        ["가장 두꺼워질 부분", "오류 메시지 사전", "과목별 핵심 요약과 기출 해설"],
    ],
    [40 * mm, 63 * mm, 63 * mm],
)
body("같은 방법론(2부 수요 검증 → 3부 목차 설계 → 4부 집필 원칙)을 쓰더라도, <b>실습형은 &ldquo;막히는 순간&rdquo;을 중심으로, 요약형은 &ldquo;외워야 할 핵심&rdquo;을 중심으로</b> 콘텐츠 무게중심이 달라집니다. 자신의 주제가 어느 쪽에 가까운지 먼저 판단하면, 시간을 어디에 더 써야 할지 훨씬 명확해집니다.")
h2("자격증 요약형 표지ㆍ문구 예시")
callout_box("적용 예시(가상)", [
    "제목: &ldquo;컴퓨터활용능력 필기, 이 요약만 보고 가세요&rdquo;",
    "부제: &ldquo;최근 3개년 기출 출제 비중 반영ㆍ과목별 핵심만 압축&rdquo;",
    "가격 전략: 시험 접수 시작 시기 직전 얼리버드 할인으로 출시(8부 얼리버드 전략 적용)",
])

# ============================================================
# 용어 사전
# ============================================================
h1("용어 사전")
glossary = [
    ("POD (Print On Demand)", "주문이 들어올 때마다 한 부씩 인쇄하는 방식. 부크크처럼 재고 없이 종이책을 만들 수 있게 해주는 자가출판 방식."),
    ("ISBN", "국제표준도서번호. 정식으로 유통되는 책에 부여되는 고유 번호로, 부크크ㆍ유페이퍼에서 발급 대행을 받을 수 있음."),
    ("자가출판(Self-Publishing)", "출판사를 거치지 않고 저자가 직접 책을 만들어 유통하는 방식."),
    ("재능마켓", "크몽ㆍ탈잉처럼 개인의 지식ㆍ서비스ㆍ콘텐츠를 사고파는 온라인 중개 플랫폼."),
    ("정산 수수료", "플랫폼이 판매 대금 중개 대가로 가져가는 비율. 플랫폼마다 계산 방식이 다름(7부 참고)."),
    ("원천징수", "소득을 지급하는 쪽이 세금을 미리 떼고 나머지만 지급하는 방식. 탈잉의 소득세 3.3%가 대표적 예."),
    ("인세", "책이 팔릴 때마다 저자가 정가의 일정 비율로 받는 금액. 부크크ㆍ유페이퍼가 이 방식."),
    ("종합소득세", "한 해 동안 벌어들인 여러 소득을 합산해 다음 해 5월에 신고ㆍ납부하는 세금."),
    ("부가가치세", "재화ㆍ서비스 거래에 부과되는 세금. 사업자등록이 있는 경우 통상 연 2회 신고."),
    ("얼리버드", "정식 판매 전ㆍ초반에 한시적으로 제공하는 할인 판매 방식."),
    ("카니발라이제이션(자기잠식)", "같은 상품을 여러 채널에서 팔 때, 한 채널의 판매가 다른 채널의 판매를 갉아먹는 현상."),
    ("유사투자자문업", "특정 종목ㆍ코인의 매매를 불특정 다수에게 조언하며 대가를 받는 행위. 자본시장법상 별도 신고ㆍ등록이 필요한 영역."),
    ("표시광고법", "허위ㆍ과장 광고, 대가성 후기 등을 규제하는 법. 후기 요청 시 참고해야 함(9부)."),
    ("Type A / Type B (이 가이드에서의 구분)", "정보를 구조화해서 정리하는 주제(Type A, 권장)와 검증 불가능한 개인 실적을 앞세우는 주제(Type B, 신중 접근)를 구분하기 위해 이 가이드에서 사용한 표현(5장 참고)."),
    ("간이과세자", "연 매출 규모가 일정 기준 이하인 사업자에게 적용되는 부가가치세 과세 유형. 일반과세자보다 세금 부담이 낮은 경우가 많음."),
    ("통신판매업 신고", "온라인으로 상품ㆍ서비스를 직접 판매할 때 사업자등록과 별도로 관할 구청에 해야 하는 신고 절차."),
    ("전환율", "상세페이지ㆍ카드뉴스를 본 사람 중 실제로 구매까지 이어진 사람의 비율."),
    ("리드마그넷", "잠재 구매자의 관심을 끌기 위해 먼저 무료로 제공하는 콘텐츠(이 가이드의 &ldquo;무료 체험판&rdquo;이 해당)."),
    ("경비 처리", "사업을 위해 실제로 지출한 비용을 소득에서 제외하고 세금을 계산하는 것."),
    ("공표된 저작물의 인용", "저작권법상 이미 공개된 저작물을 정당한 범위 안에서 출처를 밝히고 인용하는 것을 허용하는 개념(8-2장 참고)."),
    ("노출수(임프레션)", "내 상품 페이지가 검색ㆍ목록 화면에 보여진 횟수. 조회수와 비슷하지만 실제 클릭 여부와는 무관한 지표."),
    ("클릭률(CTR)", "노출된 횟수 대비 실제로 클릭해서 들어온 비율. 썸네일ㆍ제목의 매력도를 가늠하는 지표."),
    ("퍼널", "관심을 가진 사람이 실제 구매까지 이어지는 단계별 흐름(노출 → 클릭 → 상세페이지 열람 → 구매). 어느 단계에서 이탈이 큰지 파악하면 무엇을 고쳐야 할지 알 수 있음."),
    ("리텐션", "한 번 구매한 고객이 다시 찾아오거나 다음 상품을 구매하는 비율. 시리즈화(14부)와 밀접한 개념."),
    ("타겟 페르소나", "내 상품을 살 것으로 예상되는 대표 독자상을 구체적으로 그려본 것(예: &ldquo;이직을 준비하는 30대 직장인&rdquo;). 문장 톤과 표지 디자인을 정할 때 기준이 됨."),
    ("랜딩카피", "상세페이지에서 방문자의 시선을 처음 붙잡는 도입부 문구(16-2장의 &ldquo;문제 제기&rdquo; 문장이 대표적 예)."),
    ("콘텐츠 캘린더", "언제 어떤 홍보 콘텐츠(카드뉴스, 블로그 글 등)를 올릴지 미리 계획한 일정표. 9부의 마케팅을 꾸준히 반복하기 위한 관리 도구."),
    ("A/B 테스트", "표지ㆍ제목ㆍ가격 등 한 가지 요소만 다르게 만든 두 버전을 동시에 운영해 어느 쪽 반응이 더 좋은지 비교하는 방법."),
    ("사업자등록번호", "사업자로 등록하면 부여받는 고유 번호. 세금계산서 발행, 스마트스토어 등 일부 채널 이용에 필요."),
    ("객단가", "한 번의 결제에서 발생하는 평균 구매 금액. 번들ㆍ묶음 판매(14부)로 높일 수 있는 지표."),
    ("썸네일", "목록ㆍ검색 결과 화면에 작게 표시되는 표지 축소 이미지. 11-2장의 레이아웃이 작게 줄어도 읽히는지가 중요한 이유."),
    ("정산 주기", "플랫폼이 판매 대금을 실제로 입금해주는 주기(週ㆍ月 단위). 플랫폼마다 다르므로 판매자 센터에서 확인이 필요."),
    ("환불 정책", "구매자가 환불을 요청할 수 있는 조건과 기간. 디지털 파일 특성상 다운로드 후 환불 제한을 두는 플랫폼이 많으니 등록 전 각 플랫폼 정책을 확인해야 함."),
    ("저작인격권", "저작물에 대해 저작자가 갖는 인격적 권리(공표권ㆍ성명표시권 등). 공동 집필(사례 H) 시 역할과 이름 표기를 명확히 해야 하는 이유."),
]
for term, desc in glossary:
    h2(term)
    body(desc)

# ============================================================
# 부록1
# ============================================================
h1("부록1. 플랫폼 수수료 총정리표")
simple_table(
    ["플랫폼", "저자 최종 수령 비율(대략)", "필요 조건"],
    [
        ["크몽", "약 80%(수수료 약 20%)", "회원가입, 사업자등록 불필요"],
        ["탈잉", "약 76%(수수료 20%+세금)", "회원가입, 사업자등록 불필요"],
        ["부크크(직접판매)", "35%(흑백) / 15%(컬러)", "회원가입, 사업자등록 불필요"],
        ["부크크(외부유통)", "15%(흑백) / 10%(컬러)", "외부유통 별도 신청(무료)"],
        ["유페이퍼(자체판매)", "70%", "회원가입, 사업자등록 불필요"],
        ["유페이퍼(제휴서점)", "60%", "제휴 서점 유통 신청"],
        ["스마트스토어", "결제수수료 제외 대부분", "사업자등록 필수"],
    ],
    [40 * mm, 62 * mm, 62 * mm],
)
body("<i>위 수치는 2026년 7월 각 플랫폼 공식 고객센터ㆍ도움말 페이지 기준으로 조사한 것이며, 정책은 수시로 바뀌므로 실제 등록 전 각 플랫폼에서 최신 수수료를 다시 확인해야 합니다.</i>")
body("표를 다시 보면, 재능마켓(크몽ㆍ탈잉)은 <b>플랫폼이 결제ㆍ정산을 전부 처리해주는 대신 수수료가 높은 구조</b>이고, 서점 유통형(부크크ㆍ유페이퍼)은 <b>인세율은 낮아 보여도 정가를 직접 정할 수 있어 실제 수령액을 조정할 여지가 크다</b>는 차이가 있습니다. 스마트스토어는 <b>수수료 자체는 가장 낮지만 사업자등록ㆍ마케팅을 스스로 다 해야 하는 비용</b>이 숨어 있다고 보면 됩니다. 결국 &ldquo;수수료가 낮은 곳&rdquo;이 무조건 유리한 게 아니라, <b>내가 직접 할 수 있는 일과 플랫폼에 맡기고 싶은 일의 균형</b>을 따져 고르는 것이 21-3장의 상황별 추천 조합이 말하는 핵심입니다.")

# ============================================================
# 부록2
# ============================================================
h1("부록2. 좋은 제목 짓는 공식과 예시 20개")
body("좋은 제목은 <b>[대상] + [핵심 키워드] + [형태/차별점]</b> 공식을 따르면 대부분 해결됩니다.")
callout_box("공식에 맞춘 제목 예시", [
    "OO자격증 실기 압축 요약노트(최신 개정 기준)",
    "엑셀 몰라도 되는 자동화 스프레드시트 만들기",
    "스마트스토어 첫 상품 등록부터 첫 주문까지",
    "블로그 애드센스 승인 받는 법(2026년 최신 정책 반영)",
    "인스타그램 팔로워 없이 시작하는 카드뉴스 마케팅",
    "OO기사 필기 14개년 기출 핵심 정리",
    "챗GPTㆍ클로드로 업무 시간 절반 줄이는 프롬프트 모음",
    "쿠팡 구매대행 첫 발주부터 정산까지",
    "전자책 만들어 팔기(주제 정하기부터 등록까지)",
    "1인 사업자를 위한 홈택스 신고 절차 한눈에 보기",
    "유튜브 쇼츠 알고리즘 이해하고 조회수 늘리는 법",
    "제휴마케팅 첫 수익까지 걸리는 진짜 과정",
    "상세페이지 카피, 이 순서대로만 쓰면 된다",
    "고객 응대 스크립트 모음(쇼핑몰 CS 실전편)",
    "구글 스프레드시트로 매출 대시보드 만들기",
    "산업안전기사 빈출 문제 90선 정리",
    "메타 광고, 예산 10만원으로 시작하는 법",
    "정부지원사업 공고문 읽는 법(초보자 편)",
    "미리캔버스로 표지ㆍ카드뉴스 30분 만에 만들기",
    "전자책 두 번째 권부터는 훨씬 빨라지는 이유",
])
h2("이런 제목은 피하세요")
callout_box("검색에 안 걸리는 제목의 공통점", [
    "&ldquo;인생 역전 노하우&rdquo; — 무엇에 대한 책인지 전혀 알 수 없음(대상ㆍ키워드 없음)",
    "&ldquo;진짜 이것만 알면 됩니다&rdquo; — 검색될 단어가 하나도 없음",
    "&ldquo;OO 마스터 클래스&rdquo; — &ldquo;마스터&rdquo;라는 단어는 검색량이 거의 없는 추상적 표현",
    "본문 내용과 무관하게 자극적인 숫자만 강조한 제목 — 클릭은 유도해도 후기ㆍ신뢰에서 손해를 봄",
])
body("위 예시들의 공통점은 <b>&ldquo;그래서 뭘 알려주는 책인데?&rdquo;라는 질문에 제목만으로 답할 수 없다</b>는 것입니다. 부록2의 공식([대상]+[핵심 키워드]+[형태/차별점])으로 돌아가 다시 점검해보세요.")

# ============================================================
# 부록3
# ============================================================
h1("부록3. 표지ㆍ상세페이지 문구 모음")
body("아래는 실제로 자주 쓰이는 표현을 상황별로 정리한 것입니다. 자신의 콘텐츠에 맞게 숫자와 단어만 바꿔서 바로 활용할 수 있습니다.")
callout_box("표지용 부제 표현", [
    "&ldquo;최신 개정 기준&rdquo; — 정책ㆍ시험ㆍ정보가 자주 바뀌는 주제일 때",
    "&ldquo;실제 화면 OO장 수록&rdquo; — 스크린샷이 많이 포함된 실습형 콘텐츠일 때",
    "&ldquo;OO시간을 아껴주는 요약&rdquo; — 정보 탐색 시간을 줄여주는 게 핵심 가치일 때",
    "&ldquo;처음 시작하는 사람을 위한&rdquo; — 초보자를 대상으로 쉽게 풀어 썼을 때",
])
callout_box("상세페이지 도입부 표현", [
    "&ldquo;이런 고민 있으신가요?&rdquo;로 시작해 독자의 상황을 먼저 짚어주기",
    "&ldquo;이 책은 OO을 위한 것입니다&rdquo;로 대상을 명확히 좁혀서 제시하기",
    "&ldquo;이 책이 아닌 것&rdquo; 문단을 넣어 과장 없이 정직하게 범위를 밝히기(이 가이드 서문 참고)",
    "목차를 상세페이지에 그대로 공개해 구매 전 &ldquo;무엇이 들어있는지&rdquo; 확인시켜주기",
])
callout_box("SNS 홍보 문구 예시", [
    "&ldquo;OO 때문에 며칠을 헤맸다면, 이 글 저장해두세요.&rdquo;",
    "&ldquo;OO 준비하는 분들 반응이 좋아서 전자책으로 더 자세히 정리했습니다.&rdquo;",
    "&ldquo;무료로 목차부터 먼저 보여드릴게요(체험판 링크는 프로필에).&rdquo;",
])

# ============================================================
# 부록4
# ============================================================
h1("부록4. 참고 사이트 주소 모음")
simple_table(
    ["구분", "이름", "주소"],
    [
        ["재능마켓", "크몽", "kmong.com"],
        ["재능마켓", "탈잉", "taling.me"],
        ["자가출판(POD)", "부크크", "bookk.co.kr"],
        ["전자책 유통", "유페이퍼", "upaper.kr"],
        ["직접 판매", "스마트스토어센터", "sell.smartstore.naver.com"],
        ["디자인 도구", "미리캔버스", "miricanvas.com"],
        ["디자인 도구", "캔바(Canva)", "canva.com"],
        ["무료 폰트", "눈누", "noonnu.cc"],
        ["검색량 조회", "네이버 데이터랩", "datalab.naver.com"],
        ["세금 신고", "국세청 홈택스", "hometax.go.kr"],
    ],
    [30 * mm, 40 * mm, 94 * mm],
)

# ============================================================
# 부록5 — 색인
# ============================================================
h1("부록5. 찾아보기(색인)")
index_data = [
    [Paragraph("주제", styles["table_head"]), Paragraph("어디서 다루나", styles["table_head"])],
    [Paragraph("주제 정하기ㆍ수요 검증", styles["table_cell"]), Paragraph("2부(3~5장)", styles["table_cell"])],
    [Paragraph("목차 설계", styles["table_cell"]), Paragraph("3부(6장)", styles["table_cell"])],
    [Paragraph("AI 도구 활용", styles["table_cell"]), Paragraph("4부(9장)", styles["table_cell"])],
    [Paragraph("표지 디자인ㆍ미리캔버스", styles["table_cell"]), Paragraph("5부(11~12장)", styles["table_cell"])],
    [Paragraph("무료 폰트", styles["table_cell"]), Paragraph("5부(13장)", styles["table_cell"])],
    [Paragraph("이미지 저작권", styles["table_cell"]), Paragraph("6부(15장)", styles["table_cell"])],
    [Paragraph("크몽ㆍ탈잉 등록법", styles["table_cell"]), Paragraph("7부(16~17장)", styles["table_cell"])],
    [Paragraph("부크크ㆍ유페이퍼(ISBN)", styles["table_cell"]), Paragraph("7부(18~19장)", styles["table_cell"])],
    [Paragraph("스마트스토어", styles["table_cell"]), Paragraph("7부(20장)", styles["table_cell"])],
    [Paragraph("가격 책정", styles["table_cell"]), Paragraph("8부(22장)", styles["table_cell"])],
    [Paragraph("SNS 마케팅ㆍ후기", styles["table_cell"]), Paragraph("9부(23~25장)", styles["table_cell"])],
    [Paragraph("세금ㆍ홈택스", styles["table_cell"]), Paragraph("10부(26장)", styles["table_cell"])],
    [Paragraph("법적 리스크(세무ㆍ법률ㆍ의료 등)", styles["table_cell"]), Paragraph("2부(5장), 11부 사례F", styles["table_cell"])],
]
index_tbl = Table(index_data, colWidths=[90 * mm, 76 * mm])
index_tbl.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#faf9ff")]),
    ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
    ("TOPPADDING", (0, 0), (-1, -1), 6),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
]))
story.append(index_tbl)

# ============================================================
# 부록6
# ============================================================
h1("부록6. 실측 검증된 5대 카테고리와 세부 주제")
body("2부에서 2026년 7월 크몽 실측 조사로 확인한 5대 카테고리(자격증 요약형ㆍ전자책 제작법형ㆍ블로그 수익화형ㆍSNS 마케팅형ㆍ기술자격 요약형)를 기준으로, 각 카테고리 안에서 실제로 검색ㆍ판매되는 세부 주제만 추려 정리했습니다. 막연한 브레인스토밍이 아니라, 이미 리뷰수로 수요가 확인된 카테고리 안에서 아직 덜 채워진 틈을 찾는 용도입니다.")
idea_groups = [
    ("자격증ㆍ시험 계열 (2026.07 실측 3,246리뷰 1위 카테고리)", [
        "필기시험 과목별 핵심 요약노트", "실기시험 준비 체크포인트 정리", "최근 3개년 기출 경향 분석",
        "합격자 공통 학습 순서 정리", "시험 접수부터 발표까지 절차 안내", "자주 틀리는 개념 오답노트",
        "과목별 용어 사전", "실무 배치 후 자주 쓰는 지식 정리", "재응시자를 위한 취약점 보완 가이드", "관련 자격증 로드맵 비교",
    ]),
    ("전자책 제작법 계열 (2026.07 실측 1,619리뷰 2위 카테고리 — 이 책이 속한 유형)", [
        "특정 분야 노하우를 전자책으로 옮기는 절차 안내", "무료 도구로 표지ㆍ내지 디자인하는 법", "플랫폼별 등록 절차 비교",
        "가격 책정 실측 사례 정리", "저작권 안전하게 지키는 법", "후기 모으는 절차 정리",
        "세금 신고 흐름 정리", "개정판 운영 노하우", "여러 플랫폼 동시 운영 노하우", "전자책 마케팅 채널별 비교",
    ]),
    ("블로그 수익화 계열 (2026.07 실측 1,436리뷰 3위 카테고리)", [
        "애드센스ㆍ카카오애드핏 신청 절차", "블로그 SEO 기초", "포스팅 구조 잡는 법",
        "키워드 리서치 도구 활용법", "광고 배치 최적화", "수익 리포트 읽는 법",
        "정책 위반 피하는 법", "카테고리 확장 전략", "트래픽 늘리는 법", "장기 운영 노하우",
    ]),
    ("SNS 마케팅 계열 (2026.07 실측 619리뷰 4위 카테고리)", [
        "카드뉴스 기획 순서", "짧은 영상 스크립트 쓰는 법", "해시태그 전략",
        "팔로워 없이 시작하는 계정 운영법", "댓글ㆍDM 소통 노하우", "협찬ㆍ제휴 제안서 쓰는 법",
        "브랜드 톤앤매너 잡는 법", "콘텐츠 소재 찾는 습관", "광고 vs 오가닉 노출 차이 이해하기", "인사이트 지표 읽는 법",
    ]),
    ("기술자격 요약 계열 (2026.07 실측 593리뷰 5위 카테고리)", [
        "실기 기출 유형별 정리", "필답형 문제 풀이 노하우", "현장 실습 체크포인트",
        "공구ㆍ장비 사용법 정리", "안전 수칙 요약", "자격증 취득 후 취업 분야 정리",
        "관련 산업 최신 동향 요약", "실무 매뉴얼 정리", "재교육ㆍ보수교육 절차 안내", "선배 합격자 학습 로드맵",
    ]),
]
for group_name, items in idea_groups:
    h2(group_name)
    mid = len(items) // 2
    idea_tbl = Table(
        [[Paragraph("ㆍ " + a, styles["table_cell"]), Paragraph("ㆍ " + b, styles["table_cell"])]
         for a, b in zip(items[:mid], items[mid:])],
        colWidths=[83 * mm, 83 * mm],
    )
    idea_tbl.setStyle(TableStyle([
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(idea_tbl)
    story.append(Spacer(1, 8))
body("이 5개 카테고리 밖의 주제(육아, 외국어, 취미 등)도 물론 정보 구조화형으로 만들 수 있지만, 이 책이 실제로 실측 검증한 범위는 위 5개입니다. 다른 카테고리로 확장하고 싶다면 2부의 방법(크몽 검색ㆍ리뷰수 비교)을 그대로 적용해 본인이 직접 수요를 먼저 확인하세요 — 검증 없이 시작하는 게 가장 흔한 실패 원인입니다(12부 실수 목록 참고).")
body("목록을 훑어보다가 두세 개가 동시에 눈에 들어온다면, 3장의 방법으로 각각의 수요를 확인해본 뒤 <b>가장 검증된 수요와 자신의 경험이 겹치는 지점</b>을 최종 주제로 고르면 됩니다. 여러 개를 동시에 준비하기보다, FAQ의 &ldquo;여러 권을 동시에 준비해도 되나요&rdquo; 답변처럼 하나를 먼저 완성하는 쪽을 권합니다.")

# ============================================================
# 부록7
# ============================================================
h1("부록7. 플랫폼별 등록 단계 상세 비교")
simple_table(
    ["플랫폼", "1단계", "2단계", "3단계", "4단계"],
    [
        ["크몽", "회원가입", "전문가 등록", "서비스 등록(카테고리ㆍ가격ㆍ파일)", "심사 후 노출 시작"],
        ["탈잉", "회원가입", "튜터 등록", "클래스/전자책 등록", "승인 후 노출 시작"],
        ["부크크", "회원가입", "원고 업로드", "정가ㆍ유통 방식 선택", "ISBN 발급ㆍ유통 시작"],
        ["유페이퍼", "판매자 전환", "원고 등록", "ISBN 대행 신청(선택)", "자체+제휴 서점 유통"],
        ["스마트스토어", "사업자등록", "통신판매업 신고", "스토어 개설ㆍ상품 등록", "결제 연동 후 판매 시작"],
    ],
    [30 * mm, 30 * mm, 30 * mm, 40 * mm, 36 * mm],
)
body("표에서 보듯 크몽ㆍ탈잉은 4단계 안에 바로 판매를 시작할 수 있는 반면, 부크크ㆍ유페이퍼는 ISBN 발급이라는 절차가 하나 더 끼어 있고, 스마트스토어는 사업자등록ㆍ통신판매업 신고라는 행정 절차가 앞에 붙습니다. <b>처음 시작한다면 단계가 가장 적은 크몽부터</b>가 합리적인 이유가 여기에도 있습니다.")

# ============================================================
# 부록8
# ============================================================
h1("부록8. 출시 후 처음 석 달, 어떤 숫자를 봐야 할까")
body("전자책을 등록한 뒤에는 아래 네 가지 숫자를 꾸준히 기록해두면, 무엇을 고쳐야 할지 감정이 아니라 데이터로 판단할 수 있습니다.")
simple_table(
    ["지표", "확인 위치", "이 숫자가 낮다면"],
    [
        ["노출ㆍ조회수", "각 플랫폼 판매자 통계 화면", "제목ㆍ태그를 다시 점검(16-3장)"],
        ["전환율(조회 대비 구매)", "구매수 ÷ 조회수", "상세페이지 문구를 다시 점검(16-2ㆍ21-2장)"],
        ["후기 수ㆍ평점", "상품 페이지", "후기 요청 타이밍을 앞당기기(25장)"],
        ["재구매ㆍ시리즈 구매", "판매자 정산 내역", "시리즈화ㆍ번들 판매 고려(14부)"],
    ],
    [40 * mm, 46 * mm, 80 * mm],
)
body("네 가지 지표를 한 번에 다 잘 만들려고 하지 말고, 가장 낮은 지표 하나부터 순서대로 개선해나가는 게 효율적입니다. 예를 들어 조회수는 충분한데 구매로 안 이어진다면 상세페이지 문제일 가능성이 크고, 조회수 자체가 적다면 제목ㆍ태그ㆍ등록 채널의 문제일 가능성이 큽니다.")

# ============================================================
# 부록9
# ============================================================
h1("부록9. 보너스 자료로 체감 가치 높이기")
body("본문 외에 작은 보너스 자료를 함께 제공하면, 같은 가격이라도 &ldquo;더 받았다&rdquo;는 인상을 줄 수 있습니다. 다만 12부의 원칙대로, 이 역시 빈 양식이 아니라 <b>이미 완성된 실사용 자료</b>여야 합니다.")
callout_box("보너스 자료로 적합한 것", [
    "엑셀ㆍ스프레드시트 계산기 파일 — 본문에서 설명한 계산을 자동으로 해주는 실제 작동하는 파일",
    "요약 카드(1장짜리 PDF) — 본문 핵심을 한 장으로 압축한, 인쇄해서 책상에 붙여둘 수 있는 완성된 요약표",
    "용어 사전 별도 파일 — 본문의 용어 사전을 검색하기 쉬운 별도 PDF로 분리 제공",
    "개정 알림 — 이후 개정판을 무료로 제공하겠다는 약속(사례 E와 연결)",
])
body("반대로 &ldquo;나만의 목표 설정표&rdquo;처럼 독자가 빈칸을 채워야 완성되는 자료는 3부ㆍ7장에서 다룬 이유로 보너스 자료로도 권장하지 않습니다. 보너스도 본문과 마찬가지로 <b>이미 채워진 정보</b>여야 진짜 가치로 인정받습니다.")

# ============================================================
# 부록10
# ============================================================
h1("부록10. 자주 쓰는 축약어 풀이")
simple_table(
    ["축약어", "원어", "뜻"],
    [
        ["PDF", "Portable Document Format", "어느 기기에서 열어도 모양이 유지되는 문서 파일 형식"],
        ["ISBN", "International Standard Book Number", "국제표준도서번호(18ㆍ19장 참고)"],
        ["POD", "Print On Demand", "주문형 인쇄(18-2장 참고)"],
        ["SEO", "Search Engine Optimization", "검색엔진에 잘 노출되도록 콘텐츠를 최적화하는 것(24-2장)"],
        ["CTR", "Click Through Rate", "클릭률(용어 사전 참고)"],
        ["FAQ", "Frequently Asked Questions", "자주 묻는 질문(13부)"],
        ["VAT", "Value Added Tax", "부가가치세(10부)"],
    ],
    [24 * mm, 66 * mm, 76 * mm],
)

# ============================================================
# 부록11
# ============================================================
h1("부록11. 핵심 수치 한 장 요약")
body("이 가이드 전체에서 다룬 숫자 중, 실제 등록 전에 다시 확인하면 좋은 것들만 모았습니다. 모두 2026년 7월 조사 기준입니다.")
simple_table(
    ["항목", "수치"],
    [
        ["크몽 총수수료(대략)", "약 20%(구간별 16.4~4.4%+결제망3.3%+부가세10%)"],
        ["탈잉 위탁수수료", "20%+부가세10%+소득세3.3% 원천징수"],
        ["부크크 직접판매 인세", "35%(흑백)/15%(컬러)"],
        ["부크크 외부유통 인세", "15%(흑백)/10%(컬러)"],
        ["유페이퍼 자체판매 수령", "70%(수수료 30%)"],
        ["유페이퍼 제휴서점 수령", "60%(수수료 40%)"],
        ["유페이퍼 ISBN 대행 비용", "1,000원(약 7일 소요)"],
        ["부크크 종이책 정가 기준", "250p 흑백 13,400원 / 컬러 16,000원"],
    ],
    [80 * mm, 86 * mm],
)

# ============================================================
# 부록12
# ============================================================
h1("부록12. 이 가이드에서 언급한 법령 모음")
body("5장ㆍ8-2장ㆍ9장ㆍ25장ㆍ26부에서 언급한 법령을 한곳에 모았습니다. 실제 적용 여부는 반드시 변호사ㆍ세무사 등 전문가와 확인하세요.")
simple_table(
    ["법령", "관련 내용"],
    [
        ["세무사법", "세무 대리ㆍ자문은 세무사만 가능(5장)"],
        ["변호사법", "법률 상담ㆍ대리는 변호사만 가능(5장)"],
        ["의료법", "진단ㆍ처방ㆍ치료법 안내는 의료인만 가능(5장)"],
        ["공인중개사법", "부동산 중개 행위는 공인중개사만 가능(5장)"],
        ["보험업법", "보험 상품 모집ㆍ권유는 등록된 설계사만 가능(5장)"],
        ["자본시장법", "유사투자자문업은 별도 등록 필요(5장)"],
        ["저작권법", "공표된 저작물의 인용 범위(8-2장)"],
        ["표시광고법", "허위ㆍ과장 광고, 대가성 후기 규제(25장)"],
    ],
    [40 * mm, 126 * mm],
)

# ============================================================
# 부록13
# ============================================================
h1("부록13. 이 가이드 활용 순서 요약")
body("전체를 처음부터 끝까지 읽지 않아도 됩니다. 아래 순서대로 필요한 부만 찾아 읽으면 됩니다.")
flow_diagram(["1부 5분컷", "2부 주제검증", "3ㆍ4부 집필", "5ㆍ6부 디자인"])
flow_diagram(["7부 등록", "8부 가격", "9부 마케팅", "10~15부 심화"])
body("막히는 지점이 생기면 부록5(색인)에서 관련 챕터를 바로 찾아 돌아가 다시 읽으면 됩니다.")

# ============================================================
# 부록14
# ============================================================
h1("부록14. 저자 소개 문구 쓰는 법")
body("상세페이지 신뢰 요소(16-2장)에서 저자 소개는 생각보다 중요한 역할을 합니다. 화려한 이력이 없어도 아래 구조로 쓰면 충분합니다.")
callout_box("저자 소개 3문장 구조", [
    "1문장: 이 주제와 나의 접점(&ldquo;OO을 준비하며 직접 정리한 자료입니다&rdquo;, &ldquo;OO 업무를 N년째 하고 있습니다&rdquo;)",
    "2문장: 이 자료를 만들게 된 이유(&ldquo;정보가 너무 흩어져 있어서 직접 정리했습니다&rdquo;)",
    "3문장(선택): 앞으로의 계획(&ldquo;후기를 반영해 계속 개정할 예정입니다&rdquo; — 사례 E와 연결)",
])
body("자격ㆍ경력을 과장할 필요는 없습니다. 오히려 &ldquo;전문가가 아니라 직접 겪어본 사람&rdquo;이라는 솔직한 포지셔닝이 정보 구조화형 콘텐츠에서는 더 신뢰를 얻는 경우가 많습니다.")
h2("환불 문의에 대응하는 법")
body("가끔 &ldquo;생각했던 내용과 달라서 환불하고 싶다&rdquo;는 문의가 올 수 있습니다. 디지털 파일은 이미 다운로드된 이상 무조건 환불해줘야 하는 것은 아니지만, 플랫폼별 정책(용어 사전의 &ldquo;환불 정책&rdquo; 참고)을 먼저 확인하고, 애매한 경우 정중하게 응대하는 쪽이 후기ㆍ평판 관리에 유리합니다. 애초에 16-2장의 상세페이지에 목차를 미리 공개해두면 &ldquo;생각과 다르다&rdquo;는 문의 자체를 크게 줄일 수 있습니다.")

# ============================================================
# 부록15
# ============================================================
h1("부록15. 자주 헷갈리는 표현 비교")
callout_box("수수료 vs 인세", [
    "수수료 — 크몽ㆍ탈잉처럼 정가에서 플랫폼이 떼어가는 비율(7부).",
    "인세 — 부크크ㆍ유페이퍼처럼 정가 대비 저자가 받는 비율로 표현하는 방식(18ㆍ19장). 결국 저자가 받는 몫을 계산하는 두 가지 다른 표현 방식입니다.",
])
callout_box("사업소득 vs 기타소득", [
    "사업소득 — 계속ㆍ반복적으로 이뤄지는 판매 활동에서 나오는 소득(26-2장).",
    "기타소득 — 일시적ㆍ우발적으로 발생한 소득. 전자책 판매가 처음 한두 번에 그친다면 여기 해당할 수 있습니다.",
])
callout_box("POD vs 일반 인쇄", [
    "POD(주문형 인쇄) — 주문이 들어올 때마다 한 부씩 인쇄, 재고 부담 없음(18-2장).",
    "일반(대량) 인쇄 — 미리 수백~수천 부를 찍어두는 방식. 개인 저자에게는 재고ㆍ초기 비용 부담이 커 이 가이드에서는 다루지 않습니다.",
])

story.append(Spacer(1, 20))
h1("마지막으로 전하고 싶은 말")
closing_box = [
    [Paragraph(
        "전자책 한 권을 완성하는 일은 처음이 가장 오래 걸립니다. 어떤 주제를 골라야 할지, "
        "어떤 플랫폼에 올려야 할지, 가격은 어떻게 정해야 할지 전부 낯설기 때문입니다. 하지만 "
        "이 가이드에서 다룬 순서 — 주제 검증, 목차 설계, 집필, 디자인, 등록, 마케팅 — 를 "
        "한 번이라도 끝까지 경험하고 나면, 두 번째 권부터는 훨씬 수월해집니다.<br/><br/>"
        "완벽한 주제가 떠오를 때까지 기다리지 마세요. 2부의 체크리스트로 오늘 당장 후보 주제 "
        "한두 가지를 크몽에서 검색해보는 것부터 시작하시길 바랍니다.",
        ParagraphStyle("closing", fontName=FONT, fontSize=11.5, leading=19, textColor=TEXT_DARK)
    )],
]
closing_tbl = Table(closing_box, colWidths=[166 * mm])
closing_tbl.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, -1), ACCENT_SOFT),
    ("BOX", (0, 0), (-1, -1), 0.8, BORDER),
    ("LEFTPADDING", (0, 0), (-1, -1), 16),
    ("RIGHTPADDING", (0, 0), (-1, -1), 16),
    ("TOPPADDING", (0, 0), (-1, -1), 16),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 16),
]))
story.append(closing_tbl)

story.append(Spacer(1, 24))
story.append(HRFlowable(width="100%", thickness=0.7, color=BORDER, spaceAfter=10))
story.append(Paragraph("데이터로 검증된 빈틈만 골라 만듭니다", styles["small"]))


def add_page_number(canvas, doc_):
    canvas.saveState()
    canvas.setFont(FONT, 9)
    canvas.setFillColor(TEXT_DIM)
    canvas.drawCentredString(A4[0] / 2, 13 * mm, str(doc_.page))
    canvas.restoreState()


doc.build(story, onFirstPage=lambda c, d: None, onLaterPages=add_page_number)
print("done:", OUT)
