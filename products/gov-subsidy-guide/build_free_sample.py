# -*- coding: utf-8 -*-
"""정부지원금 찾기 가이드 — 무료 샘플 PDF (뉴스레터 구독 유도용).
본편 build_pdf.py의 1부(5분 컷) 내용을 그대로 가져와 별도 PDF로 뽑는다.
스타일/헬퍼 함수는 build_pdf.py와 동일 — 두 파일을 수정할 땐 같이 맞출 것."""

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

BASE_DIR = Path(r"C:\Users\nalla\Desktop\수익화허브\products\gov-subsidy-guide")
SHOT_DIR = BASE_DIR / "screenshots"

ACCENT = colors.HexColor("#5a3fd6")
ACCENT_SOFT = colors.HexColor("#efeafc")
TEXT_DARK = colors.HexColor("#1f2333")
TEXT_DIM = colors.HexColor("#4d5268")
BORDER = colors.HexColor("#d9d5f0")

OUT = str(BASE_DIR / "정부지원금_찾기_가이드_무료샘플.pdf")

doc = SimpleDocTemplate(
    OUT, pagesize=A4,
    topMargin=24 * mm, bottomMargin=24 * mm,
    leftMargin=22 * mm, rightMargin=22 * mm,
    title="정부지원금 찾기 가이드 - 무료 샘플",
    author="수익화허브",
)

styles = {
    "title": ParagraphStyle("title", fontName=FONT, fontSize=27, leading=36,
                             textColor=TEXT_DARK, alignment=TA_CENTER, spaceAfter=10),
    "subtitle": ParagraphStyle("subtitle", fontName=FONT, fontSize=13.5, leading=20,
                                textColor=TEXT_DIM, alignment=TA_CENTER, spaceAfter=4),
    "cover_meta": ParagraphStyle("cover_meta", fontName=FONT, fontSize=11, leading=17,
                                  textColor=TEXT_DIM, alignment=TA_CENTER),
    "free_badge": ParagraphStyle("free_badge", fontName=FONT, fontSize=12.5, leading=18,
                                  textColor=colors.white, alignment=TA_CENTER),
    "h1": ParagraphStyle("h1", fontName=FONT, fontSize=19, leading=26,
                          textColor=ACCENT, spaceBefore=8, spaceAfter=12),
    "h2": ParagraphStyle("h2", fontName=FONT, fontSize=14.5, leading=21,
                          textColor=TEXT_DARK, spaceBefore=16, spaceAfter=8),
    "body": ParagraphStyle("body", fontName=FONT, fontSize=12.2, leading=21,
                            textColor=TEXT_DARK, spaceAfter=12, alignment=TA_LEFT),
    "quote": ParagraphStyle("quote", fontName=FONT, fontSize=12.5, leading=20,
                             textColor=ACCENT, alignment=TA_LEFT, spaceBefore=6, spaceAfter=10,
                             leftIndent=10, backColor=ACCENT_SOFT, borderPadding=12),
    "caption": ParagraphStyle("caption", fontName=FONT, fontSize=9.5, leading=14,
                               textColor=TEXT_DIM, alignment=TA_CENTER, spaceBefore=4, spaceAfter=14),
    "cta_title": ParagraphStyle("cta_title", fontName=FONT, fontSize=17, leading=24,
                                 textColor=colors.white, alignment=TA_CENTER, spaceAfter=8),
    "cta_body": ParagraphStyle("cta_body", fontName=FONT, fontSize=11.5, leading=19,
                                textColor=colors.HexColor("#e3daf9"), alignment=TA_CENTER),
}

story = []

# ---------- 표지 ----------
badge = Table([[Paragraph("무료 샘플 · 1부만 담았습니다", styles["free_badge"])]], colWidths=[70 * mm])
badge.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, -1), ACCENT),
    ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
]))
story.append(Spacer(1, 40 * mm))
story.append(badge)
story.append(Spacer(1, 10))
story.append(Paragraph("소상공인ㆍ1인사업자를 위한", styles["subtitle"]))
story.append(Paragraph("정부지원금 찾기 가이드", styles["title"]))
story.append(Spacer(1, 6))
story.append(HRFlowable(width="26%", thickness=1.4, color=ACCENT, hAlign="CENTER", spaceBefore=8, spaceAfter=16))
story.append(Paragraph("1부(5분 컷 핵심 요약)만 무료로 담았습니다.<br/>전체 가이드는 마지막 페이지에서 안내합니다.", styles["cover_meta"]))
story.append(Spacer(1, 60 * mm))
story.append(Paragraph("수익화허브", styles["cover_meta"]))
story.append(PageBreak())


def h1(text):
    story.append(Paragraph(text, styles["h1"]))
    story.append(HRFlowable(width="100%", thickness=0.7, color=BORDER, spaceAfter=12))


def h2(text):
    story.append(Paragraph(text, styles["h2"]))


def body(text):
    story.append(Paragraph(text, styles["body"]))


def quote(text):
    story.append(Paragraph(text, styles["quote"]))


def callout_box(title_text, items, numbered=False):
    rows = []
    header = Paragraph(f"<b>{title_text}</b>", ParagraphStyle(
        "boxhead", fontName=FONT, fontSize=11.5, leading=16, textColor=colors.white))
    rows.append([header])
    for i, item in enumerate(items, 1):
        prefix = f"{i}. " if numbered else "☐  "
        rows.append([Paragraph(prefix + item, ParagraphStyle(
            "boxitem", fontName=FONT, fontSize=10.8, leading=17, textColor=TEXT_DARK))])
    t = Table(rows, colWidths=[166 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("BACKGROUND", (0, 1), (-1, -1), ACCENT_SOFT),
        ("TOPPADDING", (0, 0), (-1, 0), 8), ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 13), ("RIGHTPADDING", (0, 0), (-1, -1), 13),
        ("TOPPADDING", (0, 1), (-1, -1), 6), ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
        ("BOX", (0, 0), (-1, -1), 0.8, BORDER),
        ("LINEBELOW", (0, 0), (-1, 0), 0.8, BORDER),
    ]))
    story.append(t)
    story.append(Spacer(1, 14))


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
        ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(KeepTogether(box))
    story.append(Spacer(1, 6))


def bar_row(label, value, max_value, color, unit="건"):
    bar_width_mm = max(2, (value / max_value) * 90)
    bar = Table([[""]], colWidths=[bar_width_mm * mm], rowHeights=[6 * mm])
    bar.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), color)]))
    row = Table([[Paragraph(label, styles["body"]), bar, Paragraph(f"{value}{unit}", styles["body"])]],
                colWidths=[26 * mm, 100 * mm, 18 * mm])
    row.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    story.append(row)
    story.append(Spacer(1, 3))


# ============================================================
# 짧은 서문 (원본 서문 중 맥락 파악에 필요한 부분만)
# ============================================================
h1("이 가이드는 누구를 위한 것인가")
body("이 가이드는 정부지원사업 정보를 찾고 있는 <b>소상공인, 1인사업자, 예비창업자</b>를 위한 것입니다.")
quote("&ldquo;제도가 어려운 게 아니라, 정보가 여기저기 흩어져 있고 용어가 낯설어서 못 찾는다.&rdquo;")
callout_box("이 가이드가 아닌 것", [
    "지원금 신청을 대신 해드리는 대행 서비스가 아닙니다. 정보를 정리해서 드릴 뿐이고, 실제 신청은 반드시 본인이 직접 해야 합니다.",
    "이 가이드에 실린 화면과 공고 사례는 모두 집필 시점(2026년 7월)에 실제로 접속해서 캡처한 것이며, 최신 금액ㆍ마감일ㆍ자격 조건은 반드시 해당 공식 사이트에서 본인이 직접 확인해야 합니다.",
])

# ============================================================
# 1부 (본편 build_pdf.py의 259~363행과 동일 내용)
# ============================================================
h1("1장. 딱 한 사이트만 볼 시간이라면 — 기업마당")
body("정부지원사업 정보가 모여 있는 사이트는 여러 개지만, 시간이 없다면 <b>기업마당(bizinfo.go.kr) 하나만 먼저 보세요.</b> 중소벤처기업부가 운영하는 사이트로, 중앙부처와 지자체의 지원사업 공고가 가장 폭넓게 모여 있습니다.")
screenshot("01_bizinfo_home.png", "기업마당 첫 화면 — 가운데 검색창에 실시간 신청 가능 건수가 표시된다")
body("접속하면 가운데에 큰 검색창이 보입니다. 검색창 위에는 &ldquo;인기 검색어&rdquo;로 다른 사람들이 많이 찾는 키워드(#지원 #ai #충북 #경북 #수출 등)가 뜹니다.")

h2("1단계 — 검색창에 키워드 입력하기")
body("검색창을 클릭하고 자신에게 맞는 키워드를 입력합니다. 예를 들어 청년 대표라면 &ldquo;청년창업&rdquo;, 소상공인이라면 &ldquo;소상공인 정책자금&rdquo;처럼요.")
screenshot("02_bizinfo_search_typed.png", "검색창에 '청년창업' 입력한 화면")

h2("2단계 — 검색 버튼(돋보기 아이콘)을 누르면")
body("바로 결과가 뜹니다. 아래는 실제로 &ldquo;청년창업&rdquo;을 검색했을 때 나온 화면입니다.")
screenshot("03_bizinfo_search_result.png", "'청년창업' 검색 결과 — 총 111건, 지원사업공고 18건")
body("화면 위쪽에 전체 건수가 나오고, 그 아래에 지원사업공고ㆍ행사정보ㆍ정책뉴스처럼 종류별로 나뉘어 있습니다. 우리가 볼 건 대부분 <b>&ldquo;지원사업공고&rdquo;</b> 쪽입니다. 실제로 이 검색에서 이런 공고들이 나왔습니다.")
callout_box("실제 검색 결과 예시(2026년 7월 기준)", [
    "[경북] 2026년 청년창업제품 온라인 기획전 판로지원 참가기업 모집 공고",
    "[충북] 2026년 중소기업육성자금 융자(이차보전) 지원계획 변경 공고",
    "[경기] 성남시 2026년 청년창업 아이디에이션 4.0 참가자 모집 공고",
])
body("이렇게 지역별ㆍ사업별로 실제 진행 중인 공고가 리스트로 뜹니다. 제목을 클릭하면 신청 대상, 지원 내용, 신청 기간, 담당 부서 연락처까지 상세 페이지에서 확인할 수 있습니다.")
screenshot("10_bizinfo_detail.png", "공고 제목을 클릭하면 나오는 상세 페이지 — 신청기간ㆍ지원내용ㆍ담당부서까지 한 화면에")

h2("3단계 — 결과가 너무 많으면 필터로 좁히기")
body("검색어 없이 메뉴에서 &ldquo;정책정보 &gt; 지원사업 공고&rdquo;로 들어가면, 아래처럼 <b>분야별ㆍ지역별로 걸러볼 수 있는 필터 화면</b>이 나옵니다. 이 화면이 사실 기업마당에서 가장 중요한 화면입니다.")
screenshot("04_bizinfo_pblanc_list.png", "지원사업 공고 필터 화면 — 분야(창업ㆍ금융ㆍ기술 등)와 지역을 버튼으로 선택")
body("위쪽에 분야별 버튼(금융ㆍ기술ㆍ인력ㆍ수출ㆍ내수ㆍ창업ㆍ경영ㆍ기타)이 있고, 그 아래에 지역별 버튼(서울ㆍ부산ㆍ대구ㆍ인천 등)이 있습니다. 자신의 업종 분야와 사업장 지역을 각각 클릭하면 그 조건에 맞는 공고만 걸러져서 보입니다.")
screenshot("14_bizinfo_region_filtered.png", "&ldquo;서울&rdquo; 지역 필터를 누른 실제 결과 — 1,538건 중 서울 지역 46건만 걸러졌다")
body("이렇게 지역 버튼 하나만 눌러도 전체 목록이 순식간에 내 상황에 맞는 크기로 줄어듭니다. 분야 버튼까지 함께 누르면 훨씬 더 좁혀집니다.")
quote("딱 이 세 단계(검색 → 결과 확인 → 필터로 좁히기)만 알아도, 기업마당에서 내게 맞는 공고를 찾는 데는 충분합니다.")
callout_box("기업마당, 자주 하는 실수", [
    "검색어 하나로만 끝낸다 — 같은 사업도 공고마다 표현이 조금씩 다릅니다. 키워드를 2~3개 바꿔가며 검색하세요.",
    "지역 필터를 안 쓴다 — 필터 없이 보면 전국 공고가 뒤섞여서 내 지역 것만 골라내기 어렵습니다.",
    "마감임박 공고만 본다 — 상시모집(마감일 없이 예산 소진 시까지) 공고도 많습니다.",
])

h1("분야별 공고 분포 한눈에 보기")
body("1장에서 살펴본 필터 화면에 실제로 표시됐던 분야별 건수를 그래프로 옮겨봤습니다.")
field_data = [
    ("경영", 411, colors.HexColor("#5a3fd6")), ("기술", 317, colors.HexColor("#7457e0")),
    ("수출", 243, colors.HexColor("#8d6fea")), ("금융", 202, colors.HexColor("#a687f2")),
    ("인력", 150, colors.HexColor("#bfa0f7")), ("내수", 123, colors.HexColor("#d3bffa")),
    ("창업", 76, colors.HexColor("#e3d6fb")), ("기타", 16, colors.HexColor("#efe8fd")),
]
for label, value, color in field_data:
    bar_row(label, value, 411, color)
story.append(Spacer(1, 6))
body("<i>(2026년 7월 기업마당 실측 기준 — 시기에 따라 분야별 건수는 계속 바뀝니다.)</i>")

h1("2장. 5분 컷 체크리스트")
body("아래 세 가지만 스스로 확인하면 검색 키워드가 바로 나옵니다.")
h2("Q1. 사업을 시작한 지 얼마나 됐나요?")
callout_box("사업 단계", [
    "아직 사업자등록 전(예비창업자) → \u201c예비창업패키지\u201d로 검색",
    "창업 1~3년 이내 → \u201c초기창업패키지\u201d로 검색",
    "창업 3년 이상 → \u201c재도약\u201d, \u201c성장기반자금\u201d으로 검색",
])
h2("Q2. 지금 가장 필요한 게 뭔가요?")
callout_box("필요한 목적", [
    "운영자금(인건비ㆍ임차료) → \u201c정책자금\u201d 또는 \u201c경영안정자금\u201d",
    "온라인 판로ㆍ마케팅 → \u201c온라인 판로지원\u201d, \u201c스마트스토어 지원\u201d",
    "폐업/재창업 준비 → \u201c희망리턴패키지\u201d",
])
h2("Q3. 나에게만 해당하는 조건이 있나요?")
callout_box("업종/대상 특성", [
    "만 39세 이하 대표 → \u201c청년창업\u201d을 키워드 앞에 붙이기",
    "여성 대표 → \u201c여성기업\u201d",
    "비수도권 사업장 → \u201c(거주 지역명) 소상공인 지원사업\u201d",
])
body("이 답을 조합한 키워드를 기업마당 검색창에 넣고, 필터로 지역을 좁히면 끝입니다. 여기까지가 무료 샘플입니다.")

# ============================================================
# CTA 페이지
# ============================================================
story.append(Spacer(1, 20))
cta_rows = [
    [Paragraph("여기까지가 무료 샘플입니다", styles["cta_title"])],
    [Paragraph(
        "전체 가이드에는 소상공인24ㆍ중소벤처24ㆍ소진공ㆍ정부24ㆍ지자체 "
        "사이트별 상세 사용법, 헷갈리는 용어 사전, 실전 사례 6개(A~F씨), 사업계획서 작성 "
        "실전가이드, 연간 지원사업 캘린더, 담당자 통화 스크립트까지 담겨 있습니다.",
        styles["cta_body"])],
    [Paragraph("ekdrmf-cell.github.io/ebooks.html", styles["cta_body"])],
]
cta = Table(cta_rows, colWidths=[166 * mm])
cta.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, -1), ACCENT),
    ("TOPPADDING", (0, 0), (-1, -1), 14), ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
    ("LEFTPADDING", (0, 0), (-1, -1), 18), ("RIGHTPADDING", (0, 0), (-1, -1), 18),
]))
story.append(cta)

# ============================================================
# 워터마크 + 빌드
# ============================================================
WATERMARK_TEXT = "수익화허브 무료 샘플 · ekdrmf-cell.github.io"


def draw_watermark(canvas, dark_bg=False):
    canvas.saveState()
    canvas.setFont(FONT, 12.5)
    canvas.setFillColor(colors.white if dark_bg else colors.HexColor("#000000"))
    try:
        canvas.setFillAlpha(0.06 if dark_bg else 0.05)
    except AttributeError:
        pass
    canvas.translate(A4[0] / 2, A4[1] / 2)
    canvas.rotate(33)
    step_x, step_y = 78 * mm, 40 * mm
    for ix in range(-3, 4):
        for iy in range(-5, 6):
            canvas.drawCentredString(ix * step_x, iy * step_y, WATERMARK_TEXT)
    canvas.restoreState()


def on_cover(canvas, doc_):
    draw_watermark(canvas, dark_bg=True)


def add_page_number(canvas, doc_):
    draw_watermark(canvas, dark_bg=False)
    canvas.saveState()
    canvas.setFont(FONT, 9)
    canvas.setFillColor(TEXT_DIM)
    canvas.drawCentredString(A4[0] / 2, 13 * mm, str(doc_.page))
    canvas.restoreState()


doc.build(story, onFirstPage=on_cover, onLaterPages=add_page_number)
print("done:", OUT)
