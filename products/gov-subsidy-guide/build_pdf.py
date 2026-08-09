# -*- coding: utf-8 -*-
"""정부지원금 찾기 가이드 PDF 빌드 스크립트 (2026-07-31 개정판 — 분량 확충 + 실제 화면 캡처 포함)"""

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

# ---------- 색(전부 흰 배경 위 텍스트 대비 6:1 이상 확인된 값만 사용) ----------
ACCENT = colors.HexColor("#5a3fd6")
ACCENT_SOFT = colors.HexColor("#efeafc")
TEXT_DARK = colors.HexColor("#1f2333")
TEXT_DIM = colors.HexColor("#4d5268")   # 기존보다 살짝 진하게(대비 여유 확보)
BORDER = colors.HexColor("#d9d5f0")
PART_BG = colors.HexColor("#f5f3fc")

OUT = str(BASE_DIR / "정부지원금_찾기_가이드.pdf")

doc = SimpleDocTemplate(
    OUT, pagesize=A4,
    topMargin=24 * mm, bottomMargin=24 * mm,
    leftMargin=22 * mm, rightMargin=22 * mm,
    title="소상공인ㆍ1인사업자를 위한 정부지원금 찾기 가이드",
    author="수익화허브",
)

# ---------- 스타일: 기존보다 전반적으로 크게(가독성 확보) ----------
styles = {
    "title": ParagraphStyle("title", fontName=FONT, fontSize=27, leading=36,
                             textColor=TEXT_DARK, alignment=TA_CENTER, spaceAfter=10),
    "subtitle": ParagraphStyle("subtitle", fontName=FONT, fontSize=13.5, leading=20,
                                textColor=TEXT_DIM, alignment=TA_CENTER, spaceAfter=4),
    "cover_meta": ParagraphStyle("cover_meta", fontName=FONT, fontSize=11, leading=17,
                                  textColor=TEXT_DIM, alignment=TA_CENTER),
    "part_label": ParagraphStyle("part_label", fontName=FONT, fontSize=14, leading=20,
                                  textColor=ACCENT, alignment=TA_CENTER, spaceAfter=8),
    "part_title": ParagraphStyle("part_title", fontName=FONT, fontSize=24, leading=32,
                                  textColor=TEXT_DARK, alignment=TA_CENTER, spaceAfter=14),
    "part_desc": ParagraphStyle("part_desc", fontName=FONT, fontSize=11.5, leading=19,
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
    "list": ParagraphStyle("list", fontName=FONT, fontSize=11.5, leading=18,
                            textColor=TEXT_DARK, spaceAfter=5),
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
story.append(Spacer(1, 48 * mm))
story.append(Paragraph("소상공인ㆍ1인사업자를 위한", styles["subtitle"]))
story.append(Paragraph("정부지원금 찾기 가이드", styles["title"]))
story.append(Spacer(1, 6))
story.append(HRFlowable(width="26%", thickness=1.4, color=ACCENT, hAlign="CENTER", spaceBefore=8, spaceAfter=16))
story.append(Paragraph("흩어진 지원사업 정보를 어디서, 어떻게 찾아야 하는지<br/>실제 화면과 함께 정리한 실전 내비게이션 가이드", styles["cover_meta"]))
story.append(Spacer(1, 70 * mm))
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
    # 이전에는 이 함수가 강제로 PageBreak를 넣어서 새 파트를 항상 새 페이지에서
    # 시작시켰는데, 그 결과 직전 페이지가 다 안 채워진 채로 남는 경우가 계속
    # 생겼다(페이지 하단에 빈 공간). 페이지를 무조건 다 채우라는 지시에 따라
    # 강제 페이지 나누기를 없애고, 배너가 자연스러운 흐름 속에 이어지도록 한다.
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
        prefix = f"{i}. " if numbered else "☐  "
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


# ============================================================
# 목차
# ============================================================
h1("목차")
toc_line("이 가이드는 누구를 위한 것인가", "toc")
story.append(Spacer(1, 8))
toc_line("1부. 5분 컷 — 가장 빨리 찾는 법", "toc_part")
toc_line("1장. 딱 한 사이트만 볼 시간이라면 — 기업마당", "toc")
toc_line("2장. 5분 컷 체크리스트", "toc")
story.append(Spacer(1, 8))
toc_line("2부. 사이트별 상세 사용법", "toc_part")
toc_line("3장. 소상공인24 ㆍ 4장. 중소벤처24 ㆍ 5장. 소진공", "toc")
toc_line("6장. 정부24 보조금24 ㆍ 7장. 지자체 홈페이지 ㆍ 8장. 민간 통합검색", "toc")
toc_line("9장. 지역별로 살펴보기(대도시 카테고리 예시)", "toc")
story.append(Spacer(1, 8))
toc_line("3부. 헷갈리는 용어 사전", "toc_part")
toc_line("4부. 내 상황별 체크리스트", "toc_part")
toc_line("5부. 실전 사례로 따라 해보기 (A~F씨 6가지 사례)", "toc_part")
toc_line("5-2부. 지원사업 유형 완전정리", "toc_part")
toc_line("5-3부. 사업계획서 작성 실전 가이드", "toc_part")
toc_line("6부. 사이트별 검색 키워드 모음", "toc_part")
toc_line("7부. 신청 전 체크리스트", "toc_part")
toc_line("8부. 자주 묻는 질문(FAQ)", "toc_part")
toc_line("9부. 연간 지원사업 캘린더(월별 상세 포함)", "toc_part")
toc_line("9-2부. 선정 이후 — 협약부터 정산까지", "toc_part")
toc_line("9-3부. 실제 공고문 읽는 법 — 항목별 해설", "toc_part")
toc_line("10부. 자주 하는 오해 10가지", "toc_part")
toc_line("11부. 담당자에게 전화할 때 — 실전 통화 스크립트", "toc_part")
toc_line("12부. 인쇄해서 쓰는 워크시트", "toc_part")
story.append(Spacer(1, 8))
toc_line("마무리 ㆍ 부록1. 신청 서류 준비 가이드", "toc")
toc_line("부록2. 사이트 주소 모음 ㆍ 부록3. 문의 연락처", "toc")
toc_line("부록4. 체크리스트 총모음 ㆍ 부록5. 표현 사전 ㆍ 부록6. 대표 사업 계열표", "toc")
toc_line("부록7. 기관 소개 ㆍ 부록8. 찾아보기(색인) ㆍ 부록9. 약칭 풀이", "toc")
toc_line("부록10. 문제 상황 대처법 ㆍ 부록11. 한 장 요약 카드 ㆍ 부록12. 부별 핵심 요약", "toc")

# ============================================================
# 서문
# ============================================================
h1("이 가이드는 누구를 위한 것인가")
body("이 가이드는 정부지원사업 정보를 찾고 있는 <b>소상공인, 1인사업자, 예비창업자</b>를 위한 것입니다. 예비창업 단계부터 창업 3년 이상 재도약을 준비하는 사업자, 폐업 후 재도전을 고민하는 분까지 모두 해당됩니다.")
quote("&ldquo;제도가 어려운 게 아니라, 정보가 여기저기 흩어져 있고 용어가 낯설어서 못 찾는다.&rdquo;")
body("정부지원사업은 중앙부처, 지자체, 공공기관을 다 합치면 수천 개가 있고, 사이트도 제각각입니다. 어떤 건 기업마당에, 어떤 건 소상공인24에, 어떤 건 지자체 홈페이지에만 올라옵니다. 사업하는 사람 입장에서는 &ldquo;내가 받을 수 있는 게 뭔지&rdquo; 알아내는 것 자체가 일이 됩니다.")
body("이 가이드는 두 부분으로 나눴습니다. <b>1부</b>는 지금 당장 5분 안에 써먹을 수 있는 핵심만 담았습니다. 바쁘면 1부만 읽어도 충분합니다. <b>2부부터</b>는 사이트별 상세 사용법, 용어 사전, 실전 사례, 체크리스트 등 필요할 때 찾아보는 참고자료입니다.")

callout_box("이 가이드가 아닌 것", [
    "지원금 신청을 대신 해드리는 대행 서비스가 아닙니다. 정보를 정리해서 드릴 뿐이고, 실제 신청은 반드시 본인이 직접 해야 합니다. (관련 법상 수수료를 받는 대리 신청은 문제가 될 수 있습니다.)",
    "이 가이드에 실린 화면과 공고 사례는 모두 집필 시점(2026년 7월)에 실제로 접속해서 캡처한 것이며, 최신 금액ㆍ마감일ㆍ자격 조건은 반드시 해당 공식 사이트에서 본인이 직접 확인해야 합니다.",
])

# ============================================================
# 1부
# ============================================================
part_page("PART 1", "5분 컷 — 가장 빨리 찾는 법", "바쁜 분들을 위한 핵심 요약입니다.<br/>이 1부만 그대로 따라 해도 오늘 당장 검색을 시작할 수 있습니다.")

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
body("위쪽에 분야별 버튼(금융ㆍ기술ㆍ인력ㆍ수출ㆍ내수ㆍ창업ㆍ경영ㆍ기타)이 있고, 그 아래에 지역별 버튼(서울ㆍ부산ㆍ대구ㆍ인천 등)이 있습니다. 자신의 업종 분야와 사업장 지역을 각각 클릭하면 그 조건에 맞는 공고만 걸러져서 보입니다. 목록 위쪽의 &ldquo;전체 / 중앙부처 / 지자체&rdquo; 탭으로 발행 주체를 나눠 볼 수도 있고, &ldquo;마감일순&rdquo; 정렬로 바꾸면 곧 마감되는 공고부터 볼 수 있습니다.")
screenshot("14_bizinfo_region_filtered.png", "&ldquo;서울&rdquo; 지역 필터를 누른 실제 결과 — 1,538건 중 서울 지역 46건만 걸러졌다")
body("이렇게 지역 버튼 하나만 눌러도 전체 목록이 순식간에 내 상황에 맞는 크기로 줄어듭니다. 분야 버튼까지 함께 누르면 훨씬 더 좁혀집니다.")
quote("딱 이 세 단계(검색 → 결과 확인 → 필터로 좁히기)만 알아도, 기업마당에서 내게 맞는 공고를 찾는 데는 충분합니다.")
callout_box("기업마당, 자주 하는 실수", [
    "검색어 하나로만 끝낸다 — 같은 사업도 공고마다 표현이 조금씩 다릅니다(예: “청년창업”, “청년 창업자”, “만39세이하”). 키워드를 2~3개 바꿔가며 검색하세요.",
    "지역 필터를 안 쓴다 — 필터 없이 보면 전국 공고가 뒤섞여서 내 지역 것만 골라내기 어렵습니다. 사업장 소재지 버튼을 꼭 눌러보세요.",
    "마감임박 공고만 본다 — 상시모집(마감일 없이 예산 소진 시까지) 공고도 많습니다. “신청기간”란에 “모집 마감시”라고 써 있으면 상시모집이라는 뜻입니다.",
])

h1("분야별 공고 분포 한눈에 보기")
body("1장에서 살펴본 필터 화면(04번 스크린샷)에 실제로 표시됐던 분야별 건수를 그래프로 옮겨봤습니다. &ldquo;경영&rdquo;과 &ldquo;기술&rdquo; 분야가 특히 많다는 걸 한눈에 볼 수 있습니다 — 업종이 애매하면 이 두 분야부터 살펴보는 것도 방법입니다.")

def flow_diagram(steps):
    cells = []
    for i, step in enumerate(steps):
        cells.append(Paragraph(f"<b>{step}</b>", ParagraphStyle(f"flow{i}_{'-'.join(steps)[:4]}", fontName=FONT, fontSize=9.5, leading=13, textColor=colors.white, alignment=TA_CENTER)))
    row = [cells]
    widths = [32 * mm] * len(steps)
    t = Table(row, colWidths=widths, rowHeights=[16 * mm])
    style = [
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]
    shades = [ACCENT, colors.HexColor("#7457e0"), colors.HexColor("#8d6fea"), colors.HexColor("#a687f2"), colors.HexColor("#bfa0f7")]
    for i in range(len(steps)):
        style.append(("BACKGROUND", (i, 0), (i, 0), shades[i % len(shades)]))
    t.setStyle(TableStyle(style))
    story.append(t)


def bar_row(label, value, max_value, color, unit="건"):
    bar_width_mm = max(2, (value / max_value) * 90)
    bar = Table([[""]], colWidths=[bar_width_mm * mm], rowHeights=[6 * mm])
    bar.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), color)]))
    row = Table([[Paragraph(label, styles["table_cell"]), bar, Paragraph(f"{value}{unit}", styles["table_cell"])]],
                colWidths=[26 * mm, 100 * mm, 18 * mm])
    row.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    story.append(row)
    story.append(Spacer(1, 3))

field_data = [
    ("경영", 411, colors.HexColor("#5a3fd6")),
    ("기술", 317, colors.HexColor("#7457e0")),
    ("수출", 243, colors.HexColor("#8d6fea")),
    ("금융", 202, colors.HexColor("#a687f2")),
    ("인력", 150, colors.HexColor("#bfa0f7")),
    ("내수", 123, colors.HexColor("#d3bffa")),
    ("창업", 76, colors.HexColor("#e3d6fb")),
    ("기타", 16, colors.HexColor("#efe8fd")),
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
body("이 답을 조합한 키워드를 기업마당 검색창에 넣고, 필터로 지역을 좁히면 끝입니다. 여기까지가 이 가이드의 핵심입니다. 2부부터는 기업마당 외의 다른 사이트, 용어 설명, 더 자세한 사례와 체크리스트를 다룹니다 — 필요할 때 참고자료로 활용하세요.")

# ============================================================
# 2부
# ============================================================
part_page("PART 2", "사이트별 상세 사용법", "기업마당만으로 부족할 때, 또는 정책자금(융자)처럼<br/>특정 목적에 특화된 정보가 필요할 때 참고하세요.")

h1("3장. 소상공인24 (sbiz24.kr)")
body("소상공인 전문 지원 정보 사이트입니다. 기업마당이 &ldquo;모든 중소기업&rdquo;을 아우른다면, 소상공인24는 <b>소상공인 자격에 딱 맞는 지원</b>(정책자금, 컨설팅, 교육, 각종 바우처)에 특화돼 있습니다.")
screenshot("05_sbiz24_home.png", "소상공인24 첫 화면 — 소상공인24(사업신청)와 경영안정 바우처 배너")
body("첫 화면에 &ldquo;소상공인24(소공인ㆍ소상공인ㆍ전통시장ㆍ예비창업자 등 기타 지원사업 정보 조회 및 신청)&rdquo;와 &ldquo;소상공인 경영안정 바우처&rdquo; 두 개의 큰 배너가 있습니다. 실제로 이 사이트를 열었을 때 구체적인 지원 조건이 배너에 바로 노출되는 경우가 많습니다 — <b>이런 배너는 시기마다 완전히 바뀌므로, 방문할 때마다 새로 확인하는 습관을 들이세요.</b>")
body("<b>사용법</b>: 첫 화면의 &ldquo;소상공인24&rdquo; 배너를 클릭하면 자격 여부 확인 → 지원사업 목록 → 온라인 신청까지 한 사이트 안에서 진행됩니다. 회원가입(간편인증 또는 공동인증서)이 필요한 경우가 대부분이니, 신청까지 하려면 미리 공동인증서나 간편인증(카카오ㆍ네이버 등)을 준비해두면 편합니다.")
callout_box("소상공인24, 자주 하는 실수", [
    "배너만 보고 끝낸다 — 첫 화면 배너는 그때그때 눈에 띄는 사업 한두 개만 보여줍니다. 반드시 &ldquo;전체 지원사업 목록&rdquo;까지 들어가서 확인하세요.",
    "간편인증 없이 방문한다 — 신청 단계에서 인증이 막혀 처음부터 다시 해야 하는 경우가 많습니다. 미리 준비하고 시작하세요.",
])

h1("4장. 중소벤처24 (smes.go.kr)")
body("중소기업ㆍ스타트업 대상 지원사업, K-스타트업 관련 정보가 모여 있습니다. 스타트업이나 기술 기반 창업이라면 기업마당과 함께 반드시 확인해야 합니다.")
screenshot("06_smes_home.png", "중소벤처24 첫 화면 — 오늘의 사업공고와 서비스 개편 안내가 함께 표시된다")
body("2026년 기준 이 사이트는 &ldquo;중소벤처24 서비스 일원화&rdquo;라는 이름으로 개편이 진행 중이었습니다. <b>정부 사이트는 이렇게 주기적으로 개편ㆍ이전을 하니, 예전에 봤던 메뉴 위치가 안 보인다고 당황하지 말고 첫 화면의 공지사항이나 팝업부터 확인하세요.</b>")
body("<b>사용법</b>: 첫 화면 왼쪽의 &ldquo;오늘의 사업공고&rdquo;에서 전체 공고 수, 이번주 신규, 인기공고, 마감임박 공고 건수를 바로 볼 수 있습니다. 회원가입 후 기업 정보를 등록해두면 &ldquo;스마트 맞춤 추천&rdquo;이 내 업종ㆍ규모에 맞는 사업을 자동으로 걸러줍니다.")
callout_box("중소벤처24, 자주 하는 실수", [
    "예전 즐겨찾기 주소로 접속한다 — 개편 전 페이지는 그대로 남아있어도 정보가 최신이 아닐 수 있습니다. 매번 메인 화면부터 새로 들어가는 습관을 들이세요.",
    "기업정보 등록을 건너뛴다 — 맞춤 추천 기능은 기업정보를 등록해야 작동합니다. 등록 안 하면 전체 목록을 일일이 훑어야 해서 훨씬 오래 걸립니다.",
])

h1("5장. 소상공인시장진흥공단(소진공) — semas.or.kr")
body("소상공인 <b>정책자금(융자)</b>을 직접 운영하는 기관입니다. &ldquo;지원금&rdquo;이 아니라 &ldquo;빌려주는 돈(융자)&rdquo;이 필요하다면 반드시 확인해야 하는 사이트입니다.")
screenshot("07_semas_home.png", "소진공 첫 화면 — 정책자금ㆍ교육ㆍ소상공인24ㆍ상권정보 4대 메뉴")
body("첫 화면이 네 개의 큰 메뉴로 나뉩니다. <b>소상공인 정책자금(융자)</b>은 운영자금ㆍ시설자금을 낮은 금리로 빌려주는, 소상공인이 가장 많이 찾는 메뉴입니다. <b>지식배움터(교육)</b>는 창업ㆍ경영 관련 무료 교육 프로그램이고, <b>소상공인365(상권정보)</b>는 업종별ㆍ지역별 상권 분석 데이터를 무료로 제공해 창업 전 입지를 알아볼 때 유용합니다.")
body("오른쪽에는 전국 소상공인지원센터(새출발지원센터) 지도가 있어서, 직접 방문 상담을 원하면 여기서 가까운 센터를 찾을 수 있습니다. 전화 상담은 중소기업통합콜센터 1357, 소진공 콜센터 1533-0100입니다.")
body("<b>사용법</b>: &ldquo;소상공인 정책자금&rdquo; 메뉴로 들어가면 융자 종류별 지원 한도ㆍ금리ㆍ신청 자격이 표에 정리돼 있습니다. 정책자금은 예산이 소진되면 연중에도 마감되는 경우가 많아서, <b>연초(1~2월)에 확인하는 게 가장 유리합니다.</b>")
screenshot("12_semas_policy_fund.png", "소진공 정책자금 메뉴 — 융자 종류별 한도ㆍ금리ㆍ신청 자격이 표로 정리돼 있다")

h1("6장. 정부24 — 보조금24")
body("개인ㆍ사업자가 받을 수 있는 각종 보조금을 한 번에 조회할 수 있는 서비스입니다. 정부24(2026년 기준 &ldquo;정부24 AI&rdquo;로 개편) 사이트 안에서 검색창에 &ldquo;보조금24&rdquo;를 입력하면 진입할 수 있습니다.")
body("가장 큰 특징은 <b>본인 정보를 입력하면 대상이 될 수 있는 보조금을 먼저 추천해주는 방식</b>이라는 점입니다. 기업마당ㆍ소상공인24처럼 &ldquo;내가 키워드를 넣어서 찾는&rdquo; 방식과 반대로, 여기서는 나이ㆍ거주지ㆍ사업 형태 같은 조건을 입력하면 시스템이 역으로 &ldquo;받을 수 있을 것 같은 보조금 목록&rdquo;을 보여줍니다. 사업자 대상 보조금 외에 개인 대상 복지 보조금도 함께 나오니, 검색 결과에서 &ldquo;사업자ㆍ기업&rdquo; 관련 항목만 골라 보면 됩니다.")
callout_box("참고", [
    "정부24는 보안이 엄격한 사이트라 접속 환경(브라우저 보안 프로그램 등)에 따라 첫 접속이 원활하지 않을 수 있습니다. 접속이 안 되면 새로고침하거나 다른 브라우저로 재시도해보세요.",
    "로그인은 공동인증서, 간편인증(카카오ㆍ네이버ㆍPASS 등) 모두 지원합니다.",
])
callout_box("정부24, 자주 하는 실수", [
    "검색 결과에 사업자용이 아닌 개인 복지 서비스가 섞여 나오는데 이를 걸러내지 않고 훑어본다 — 결과 목록의 카테고리 필터(민원서비스/보조금 등)를 활용해 사업자 관련 항목만 좁혀보세요.",
    "한 번 조회하고 다시는 안 본다 — 보조금24 추천 목록은 내 조건이나 정책이 바뀌면 달라집니다. 분기에 한 번 정도 재조회하는 걸 추천합니다.",
])

h1("7장. 지자체(시ㆍ군ㆍ구) 홈페이지 — 중앙 사이트에 없는 걸 찾는 법")
body("같은 업종이어도 <b>사는 지역에 따라 별도로 받을 수 있는 지원사업</b>이 따로 있습니다. 이런 지역 한정 지원사업은 기업마당 같은 중앙 사이트에 안 올라오는 경우가 많아서, 거주 지역 시청ㆍ구청 홈페이지를 따로 봐야 합니다.")
body("예시로 수원시 홈페이지를 살펴보겠습니다.")
screenshot("09_local_gov_example.png", "지자체 홈페이지 예시(수원시) — 종합민원ㆍ정보공개/개방ㆍ분야별정보 메뉴 구조")
body("지자체 홈페이지는 사이트마다 디자인이 다르지만, 찾아야 할 메뉴 이름은 대체로 비슷합니다.")
callout_box("찾아야 할 메뉴", [
    "\u201c고시공고\u201d — 법적 효력이 있는 공식 공고문 게시판. 지원사업 모집공고도 대부분 여기에 함께 올라옵니다.",
    "\u201c분야별정보\u201d 또는 \u201c정보공개/개방\u201d — 경제ㆍ기업지원 카테고리 안에 지원사업 메뉴가 따로 있는 경우가 많습니다.",
    "상단 검색창에 \u201c소상공인 지원\u201d이나 \u201c창업 지원\u201d을 직접 검색하는 것도 빠른 방법입니다.",
])
body("<b>사용법 요령</b>: &ldquo;OO시 소상공인 지원사업&rdquo;, &ldquo;OO구 청년창업 지원&rdquo;처럼 <b>지역명을 반드시 포함해서 검색엔진(네이버ㆍ구글)에 먼저 검색</b>해보는 것도 좋은 방법입니다. 지자체는 자체 예산으로 운영하는 사업이 많아 경쟁률이 상대적으로 낮은 경우가 있어, 중앙 사업 못지않게 챙겨볼 가치가 있습니다.")
callout_box("지자체 홈페이지, 자주 하는 실수", [
    "사업장 소재지가 아니라 거주지 기준으로만 찾는다 — 지자체 지원사업은 &ldquo;사업장 소재지&rdquo; 기준인 경우가 많습니다. 거주지와 사업장이 다르면 두 지역 사이트를 모두 확인하세요.",
    "구ㆍ군 단위를 빼먹는다 — 광역시ㆍ도 사이트만 보고 만족하는 경우가 많은데, 실제로는 기초자치단체(구청ㆍ군청) 단위에서 별도로 운영하는 사업이 더 많을 수 있습니다.",
])

h1("8장. (참고) 민간 통합검색 사이트")
body("기업마당ㆍ소상공인24 등 여러 공공 사이트의 공고를 매일 모아서 보여주는 민간 서비스도 있습니다. 공식 사이트를 일일이 도는 게 번거롭다면 참고용으로 함께 쓰면 좋습니다. 다만 <b>최종 신청과 정확한 조건 확인은 항상 공식 사이트에서</b> 해야 합니다 — 민간 사이트의 정보는 업데이트가 늦거나 요약 과정에서 조건이 빠질 수 있습니다.")

h1("9장. 지역별로 살펴보기 — 대도시는 어떤 카테고리를 운영하나")
body("지자체마다 사업명과 조건은 계속 바뀌지만, 대도시들이 공통으로 운영하는 지원사업 &ldquo;카테고리&rdquo;는 어느 정도 정해져 있습니다. 아래는 대표적인 대도시들이 자체 예산으로 자주 운영하는 지원 분야 예시입니다. <b>구체적인 사업명ㆍ금액ㆍ자격은 반드시 각 지자체 홈페이지에서 확인하세요.</b>")

body("참고로 1장에서 살펴본 기업마당 필터 화면(04번 스크린샷)에는 지역별 공고 건수도 함께 표시돼 있었습니다. 그래프로 옮겨보면 아래와 같습니다.")
region_data = [
    ("전남광주", 120, colors.HexColor("#5a3fd6")),
    ("경북", 135, colors.HexColor("#7457e0")),
    ("경기", 149, colors.HexColor("#8d6fea")),
    ("경남", 83, colors.HexColor("#a687f2")),
    ("강원", 71, colors.HexColor("#bfa0f7")),
    ("부산", 63, colors.HexColor("#d3bffa")),
    ("인천", 59, colors.HexColor("#d3bffa")),
    ("충북", 59, colors.HexColor("#e3d6fb")),
    ("전북", 52, colors.HexColor("#e3d6fb")),
    ("충남", 51, colors.HexColor("#e3d6fb")),
    ("대구", 48, colors.HexColor("#efe8fd")),
    ("울산", 48, colors.HexColor("#efe8fd")),
    ("서울", 46, colors.HexColor("#efe8fd")),
    ("제주", 33, colors.HexColor("#f5f0fe")),
    ("세종", 12, colors.HexColor("#f5f0fe")),
]
for label, value, color in region_data:
    bar_row(label, value, 149, color)
story.append(Spacer(1, 6))
body("<i>(2026년 7월 기업마당 실측 기준. &ldquo;서울&rdquo;이 상대적으로 적어 보이는 건 서울은 자체 구청 사업이 훨씬 많기 때문입니다 — 중앙 사이트에는 광역 단위 공고만 집계됩니다.)</i>")

region_table = [
    [Paragraph("지역", styles["table_head"]), Paragraph("자주 운영하는 카테고리 예시", styles["table_head"])],
    [Paragraph("서울", styles["table_cell"]), Paragraph("청년창업 전용 지원관 운영, 골목상권 활성화, 1인 소상공인 특화 바우처", styles["table_cell"])],
    [Paragraph("부산", styles["table_cell"]), Paragraph("해양ㆍ수산 연계 창업 지원, 소상공인 임대료 지원, 청년 일자리 연계형 창업", styles["table_cell"])],
    [Paragraph("대구", styles["table_cell"]), Paragraph("전통산업(섬유 등) 연계 지원, 소상공인 디지털 전환, 지역혁신클러스터 연계", styles["table_cell"])],
    [Paragraph("인천", styles["table_cell"]), Paragraph("항만ㆍ물류 연계 지원, 소상공인 경영안정자금 이차보전, 청년 창업 임대료 지원", styles["table_cell"])],
    [Paragraph("광주", styles["table_cell"]), Paragraph("문화콘텐츠 연계 창업, 소상공인 판로지원, 골목형 상점가 활성화", styles["table_cell"])],
]
region_tbl = Table(region_table, colWidths=[26 * mm, 140 * mm])
region_tbl.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#faf9ff")]),
    ("GRID", (0, 0), (-1, -1), 0.6, BORDER),
    ("TOPPADDING", (0, 0), (-1, -1), 7),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ("LEFTPADDING", (0, 0), (-1, -1), 9),
    ("RIGHTPADDING", (0, 0), (-1, -1), 9),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
]))
story.append(region_tbl)
story.append(Spacer(1, 10))
body("이 표는 &ldquo;이 지역엔 이런 종류의 지원이 있을 수 있다&rdquo;는 방향을 잡기 위한 것입니다. 실제로는 같은 광역시 안에서도 구청마다 별도 사업을 운영하는 경우가 많으니, 7장에서 설명한 방법대로 거주ㆍ사업장 소재지의 구청 홈페이지까지 반드시 확인하세요.")

h2("지역별로 조금 더 자세히")
body("<b>서울</b>: 자치구가 25개로 많아, 광역시 단위 사업 외에 구청별 특화 사업이 특히 다양합니다. 구청 홈페이지의 &ldquo;경제/일자리&rdquo; 메뉴를 꼭 함께 확인하세요.")
body("<b>부산</b>: 해양수산 관련 산업 기반이 커서, 관련 업종이라면 부산광역시 산하 기관(부산경제진흥원 등)의 특화 지원사업을 별도로 확인할 가치가 있습니다.")
body("<b>대구ㆍ경북</b>: 섬유ㆍ전자 등 전통 제조업 기반 지원이 상대적으로 많습니다. 지역혁신클러스터 관련 공고(1부 예시 참고)가 자주 올라옵니다.")
body("<b>인천</b>: 공항ㆍ항만 인접 특성상 물류ㆍ무역 관련 지원사업이 꾸준히 나옵니다.")
body("<b>광주ㆍ전남</b>: 문화콘텐츠, 농식품 연계 창업 지원이 상대적으로 활발한 편입니다.")
body("<b>대전</b>: 대덕연구단지 영향으로 기술창업ㆍR&amp;D 연계 지원사업 비중이 높은 지역입니다.")
body("<b>울산</b>: 중화학공업 기반 특성상 제조업ㆍ산업단지 입주기업 대상 지원사업이 자주 보입니다.")

# ============================================================
# 3부 — 용어 사전
# ============================================================
part_page("PART 3", "헷갈리는 용어 사전", "\u201c용어가 낯설어서 못 찾는다\u201d는 말이<br/>이 가이드를 만든 가장 큰 이유였습니다.")

h1("공고문에 자주 나오는 용어")

def term(name, desc):
    story.append(Paragraph(f"<b>{name}</b>", ParagraphStyle("term", fontName=FONT, fontSize=12.3, leading=18, textColor=ACCENT, spaceBefore=10, spaceAfter=3)))
    body(desc)

term("소상공인 vs 중소기업", "소상공인은 중소기업 중에서도 규모가 더 작은 사업자를 말합니다. 업종별로 기준이 다른데, 대체로 상시근로자 수 5명 미만(제조업ㆍ건설업ㆍ운수업 등은 10명 미만)이면서 매출액 기준을 충족해야 합니다. 지원사업 공고에서 &ldquo;소상공인만 신청 가능&rdquo;이라고 돼 있으면, 이 기준부터 확인해야 합니다.")
term("정책자금(융자) vs 지원금(보조금)", "정책자금은 <b>빌리는 돈</b>입니다. 낮은 금리로 빌려주는 것이지 갚지 않아도 되는 돈이 아닙니다. 반면 지원금ㆍ보조금은 조건을 충족하면 <b>갚지 않아도 되는 돈</b>입니다. 공고문에서 이 둘을 헷갈리면 자금 계획에 큰 차질이 생기니 반드시 구분해서 읽어야 합니다. 예를 들어 공고문 제목이 &ldquo;OO 정책자금 융자 지원&rdquo;이면 갚아야 하는 돈이고, &ldquo;OO 지원금 지급&rdquo;ㆍ&ldquo;OO 사업 보조금 교부&rdquo;라고 돼 있으면 갚지 않아도 되는 돈인 경우가 많습니다. 제목만으로 헷갈리면 본문 &ldquo;지원 내용&rdquo;란에서 &ldquo;융자&rdquo;인지 &ldquo;지급/교부&rdquo;인지 그 단어를 직접 확인하세요.")
term("예비창업패키지 / 초기창업패키지", "중소벤처기업부(창업진흥원)가 운영하는 대표 창업 지원사업 계열입니다. &ldquo;예비창업패키지&rdquo;는 아직 사업자등록을 하지 않은 예비창업자, &ldquo;초기창업패키지&rdquo;는 창업 3년 이내 기업이 대상입니다. 사업화 자금과 함께 멘토링ㆍ교육을 지원합니다.")
term("희망리턴패키지", "폐업(예정) 소상공인의 사업정리 컨설팅과 재취업ㆍ재창업을 지원하는 사업입니다. 폐업 과정에서 드는 철거비ㆍ원상복구비 일부를 지원하기도 합니다.")
term("사업계획서", "지원사업에 신청할 때 제출하는 핵심 서류로, 사업 개요ㆍ목표ㆍ실행 계획ㆍ예산 사용 계획 등을 담습니다. 심사에서 가장 중요하게 보는 서류이므로, 공고문에 첨부된 양식과 배점표를 반드시 먼저 확인해야 합니다.")
term("중복 지원 제한", "같은 목적의 지원사업을 동시에 여러 개 받을 수 없도록 제한하는 규정입니다. 공고문의 &ldquo;지원 제외 대상&rdquo;란에 명시돼 있는 경우가 많으니 꼭 확인하세요. 예를 들어 &ldquo;최근 3년 이내 동일 목적의 정부지원사업 수혜자는 신청 제외&rdquo;처럼 적혀 있으면, 비슷한 지원을 이미 받은 적이 있는지부터 스스로 점검해봐야 합니다.")
term("상시근로자 수", "사업장에 고용된 근로자 수를 말하며, 대표자 본인과 일용직은 대부분 제외하고 계산합니다. 소상공인ㆍ중소기업 기준을 판단하는 핵심 지표라 정확히 알아둬야 합니다.")
term("공고문 / 모집공고", "지원사업의 신청 자격, 지원 내용, 신청 기간, 제출 서류, 심사 기준을 공식적으로 안내하는 문서입니다. 다른 어떤 요약 정보보다 원본 공고문을 직접 읽는 게 가장 정확합니다.")
term("개인사업자 vs 법인사업자", "개인사업자는 대표 개인이 사업의 모든 책임을 지는 형태, 법인사업자는 회사(법인)가 별도 법적 인격을 가지는 형태입니다. 대부분의 소상공인 지원사업은 개인사업자도 신청 가능하지만, 일부 R&amp;Dㆍ투자 연계형 사업은 법인만 대상으로 하는 경우가 있어 공고문에서 반드시 확인해야 합니다.")
term("과세사업자 / 면세사업자", "부가가치세를 신고ㆍ납부해야 하는 일반 사업자는 과세사업자, 일부 업종(농산물 등 기초생활 관련)은 면세사업자로 분류됩니다. 지원사업 신청 시 요구하는 매출 증빙 서류 종류가 이 구분에 따라 달라질 수 있습니다.")
term("특례보증 / 신용보증재단", "담보가 부족한 소상공인이 보증서를 발급받아 대출을 받을 수 있도록 돕는 제도입니다. 지역별 신용보증재단이나 신용보증기금을 통해 이용할 수 있으며, 정책자금과 함께 활용되는 경우가 많습니다.")
term("정책자금 대환", "기존에 받은 정책자금 대출을 새로운 정책자금으로 갈아타는 것을 말합니다. 금리 조건이 바뀌었거나 상환 부담을 줄이고 싶을 때 소진공에 대환 가능 여부를 문의할 수 있습니다.")
term("매출액 증빙서류", "부가가치세 신고서, 손익계산서, 세금계산서 발행 내역 등 실제 매출 규모를 증명하는 서류입니다. 소상공인ㆍ중소기업 여부를 가리는 핵심 증빙이라 신청 전에 미리 발급해두면 좋습니다.")
term("원천징수영수증", "직원을 고용한 사업장이 급여에서 세금을 미리 떼고 남은 금액을 지급했다는 증빙 서류입니다. 상시근로자 수를 증빙할 때 4대보험 가입내역과 함께 요구되는 경우가 있습니다.")
term("고용보험 미가입 사업장", "직원이 없거나 아직 고용보험에 가입하지 않은 사업장을 말합니다. 일부 고용 관련 지원사업은 신청 전에 먼저 고용보험 가입을 완료해야 하는 경우가 있어 순서에 유의해야 합니다.")
term("백년가게 / 백년소공인", "업력이 오래되고 지역에서 인정받은 소상공인ㆍ소공인에게 중소벤처기업부가 부여하는 인증입니다. 인증을 받으면 홍보ㆍ컨설팅ㆍ정책자금 우대 등의 혜택을 받을 수 있습니다.")
term("데모데이", "창업 지원사업 참가 기업들이 투자자ㆍ심사위원 앞에서 사업 성과를 발표하는 행사입니다. 사업화 지원 프로그램의 마지막 단계로 진행되는 경우가 많고, 우수 기업에는 추가 지원이 이어지기도 합니다.")
term("공동인증서 / 간편인증", "정부 사이트 로그인ㆍ신청에 필요한 본인 인증 수단입니다. 공동인증서(옛 공인인증서)는 은행이나 정부24에서 발급받고, 간편인증은 카카오ㆍ네이버ㆍPASS 등 스마트폰 앱으로 인증하는 방식입니다. 신청 직전에 급하게 준비하면 시간이 부족할 수 있으니 미리 만들어두는 게 좋습니다.")
term("사업자등록증명원", "사업자등록 사실을 증명하는 공식 서류로, 대부분의 지원사업 신청에 기본으로 요구됩니다. 정부24에서 무료로 즉시 발급받을 수 있습니다.")
term("고유식별번호(사업자등록번호)", "사업자를 식별하는 10자리 번호입니다. 온라인 신청 시스템에 회원가입할 때 대부분 이 번호로 본인의 사업체를 조회하므로, 정확히 기억해두는 게 좋습니다.")
term("선정평가 / 발표평가", "서류 심사를 통과한 신청자를 대상으로 진행하는 다음 단계 심사입니다. 사업계획을 직접 발표하고 질의응답을 받는 방식이 많으며, 이 단계에서 최종 선정 여부가 갈리는 경우가 많아 발표 자료와 예상 질문 준비가 중요합니다.")
term("협약(협약체결)", "지원사업에 최종 선정된 이후, 지원 조건ㆍ의무사항ㆍ자금 집행 방법 등을 기관과 공식 계약하는 절차입니다. 협약서에 명시된 의무사항(정산보고, 사용처 제한 등)을 지키지 않으면 지원금 환수 대상이 될 수 있어 반드시 꼼꼼히 읽어야 합니다. 예를 들어 협약서에 &ldquo;지원금은 협약일로부터 6개월 이내 집행해야 한다&rdquo;처럼 구체적인 기한이 조항으로 들어가는 경우가 많으니, 서명 전에 날짜부터 계산해보는 게 좋습니다.")
term("정산보고", "지원받은 자금을 실제로 어떻게 사용했는지 증빙자료(영수증, 계약서 등)와 함께 기관에 보고하는 절차입니다. 사업 종료 후 정산보고를 소홀히 하면 다음 지원사업 신청 시 불이익을 받을 수 있으므로, 지원금을 쓸 때부터 증빙자료를 미리 챙겨두는 습관이 중요합니다.")
term("추가경정예산(추경)", "연초에 편성한 예산으로 부족하거나 새로운 정책 수요가 생겼을 때, 연중에 추가로 편성하는 예산입니다. 추경이 통과되면 그 시기에 새로운 지원사업 공고가 갑자기 늘어나는 경우가 많아, 하반기에도 꾸준히 사이트를 확인할 이유가 됩니다.")
term("공공조달 / 나라장터", "정부ㆍ공공기관이 물품ㆍ용역을 구매하는 공식 절차와 그 창구(나라장터, g2b.go.kr)를 말합니다. 여성기업ㆍ장애인기업 등은 공공조달 입찰에서 가점이나 우선구매 혜택을 받는 경우가 있어, 관련 확인서를 미리 갖춰두면 유리합니다.")
term("우대가점", "특정 조건(청년, 여성, 비수도권, 사회적기업 등)에 해당하면 심사 점수에 추가로 더해주는 점수입니다. 본인에게 해당하는 우대가점 항목이 있다면 사업계획서에 반드시 명시해야 놓치지 않습니다. 예를 들어 공고문에 &ldquo;청년(만 39세 이하) 대표 가점 부여&rdquo;, &ldquo;비수도권 사업장 가점 부여&rdquo;처럼 적혀 있으면, 해당 조건을 사업계획서 일반현황이나 별도 확인란에 반드시 기재해야 점수에 반영됩니다.")
term("컨소시엄", "여러 기업ㆍ기관이 하나의 사업을 함께 수행하기 위해 맺는 협력 체계입니다. 일부 대형 지원사업은 단독 신청보다 컨소시엄 구성 시 가점을 주기도 합니다.")
term("매칭펀드(자기부담금)", "지원금 전액을 정부가 주는 게 아니라, 신청자가 일정 비율(예: 자기부담 30%)을 직접 부담하고 나머지를 지원받는 방식입니다. 공고문에서 &ldquo;정부지원 70% + 자기부담 30%&rdquo;처럼 표기됩니다. 자기부담금을 준비할 수 있는지 미리 확인해야 합니다.")
term("지식재산권(IP) 연계지원", "특허ㆍ상표ㆍ디자인 등록 비용을 지원하거나, 등록된 지식재산권을 활용한 사업화를 지원하는 사업입니다. 특허청, 한국발명진흥회 등에서 운영합니다.")
term("사회적기업 / 예비사회적기업", "이윤 추구와 함께 사회적 가치(취약계층 고용, 환경 등)를 목적으로 하는 기업 인증 제도입니다. 인증을 받으면 전용 지원사업과 공공조달 우대를 받을 수 있습니다.")
term("매출액 산정 기준", "소상공인ㆍ중소기업 여부를 가리는 매출액은 보통 직전 사업연도 부가가치세 신고 기준으로 산정합니다. 창업 초기라 직전 연도 매출이 없다면 공고문의 별도 산정 방식을 확인해야 합니다.")
term("업종코드", "국세청이 사업자등록 시 부여하는 업종 분류 번호입니다. 지원사업 자격이 특정 업종코드로 한정된 경우가 많아, 본인의 정확한 업종코드를 사업자등록증에서 미리 확인해두면 좋습니다.")
term("재기지원", "폐업을 경험한 사업자가 다시 창업하거나 취업할 수 있도록 돕는 지원 계열입니다. 희망리턴패키지와 함께 &ldquo;재도전&rdquo; 관련 사업에서 자주 쓰이는 용어입니다.")
term("사업자단위과세", "여러 사업장을 운영하는 사업자가 세금 신고를 사업장별이 아니라 본점 하나로 통합해서 하는 제도입니다. 지원사업 신청 시 사업장별 매출ㆍ인원 구분이 필요한 경우 이 제도 적용 여부에 따라 서류 준비 방식이 달라질 수 있습니다.")
term("휴업 / 폐업", "휴업은 사업을 일시적으로 중단하되 사업자등록은 유지하는 상태, 폐업은 사업자등록 자체를 말소하는 것입니다. 지원사업 자격 판단에서 이 둘은 다르게 취급되는 경우가 많아 정확히 구분해야 합니다.")
term("사업자등록 정정신고", "상호명, 사업장 주소, 업종 등이 바뀌었을 때 국세청(홈택스)에 변경 사실을 신고하는 절차입니다. 정정 전 정보로 서류를 제출하면 불일치로 반려될 수 있어 신청 전 최신 상태인지 확인이 필요합니다.")

# ============================================================
# 4부 — 체크리스트
# ============================================================
part_page("PART 4", "내 상황별 체크리스트", "1부의 5분 컷 체크리스트를 더 자세히 풀어놓은 버전입니다.")

body("세 가지 축을 순서대로 따라가는 흐름을 그림으로 보면 아래와 같습니다.")
flow_diagram(["① 사업 단계 확인", "② 필요 목적 확인", "③ 나의 특성 확인", "④ 키워드 조합", "⑤ 검색ㆍ필터"])
story.append(Spacer(1, 10))

h1("축 1 — 사업 단계")
callout_box("해당하는 항목을 확인하세요", [
    "예비창업자 (아직 사업자등록 전)",
    "창업 1년 이내",
    "창업 3년 이내",
    "창업 3년 이상 / 재도약 준비",
    "폐업 후 재도전 준비",
])
body("예비창업자ㆍ초기창업이라면 &ldquo;예비창업패키지&rdquo;, &ldquo;초기창업패키지&rdquo; 계열 사업을, 3년 이상이라면 &ldquo;성장기반자금&rdquo;, &ldquo;재도약&rdquo; 계열 사업을 우선 검색하세요. 폐업을 준비 중이라면 &ldquo;희망리턴패키지&rdquo;부터 확인하는 게 순서입니다 — 폐업 이후에는 지원 대상에서 제외되는 사업이 많아, 폐업 전에 미리 알아보는 게 유리합니다.")

h1("축 2 — 필요한 목적")
callout_box("무엇이 필요한지 확인하세요", [
    "운영자금(인건비ㆍ임차료 등)이 필요하다 → 정책자금(융자) 계열, 소진공",
    "시설ㆍ장비 구입이 필요하다 → 시설자금, 스마트상점/스마트공장 계열",
    "온라인 진출ㆍ마케팅이 필요하다 → 온라인 판로지원, 디지털 전환 계열",
    "폐업/재창업을 준비 중이다 → 희망리턴패키지, 재도전 계열",
    "컨설팅ㆍ교육이 필요하다 → 소상공인 컨설팅, 아카데미 계열(소진공 지식배움터)",
    "갚지 않아도 되는 지원이 필요하다 → \u201c보조금\u201d, \u201c지원금\u201d 키워드로 좁혀서 검색(융자와 혼동 주의)",
])

h1("축 3 — 업종/대상 특성")
callout_box("해당 사항을 확인하세요", [
    "청년(만 39세 이하) 대표 → 청년창업 전용 사업 다수",
    "여성 대표 → 여성기업 전용 사업",
    "특정 지역(비수도권 등) → 지역 균형 관련 가산점/전용 사업",
    "기술ㆍ제조 기반 → 중소벤처24, 창업진흥원 계열",
    "장애인 대표 또는 장애인 고용 사업장 → 장애인기업종합지원센터 관련 사업",
    "경력단절 후 창업(경력단절여성 등) → 여성새로일하기센터 연계 사업",
])
body("이 세 가지 축에서 본인에게 해당하는 항목을 체크한 뒤, 2부의 사이트에서 그 키워드로 검색하면 훨씬 빠르게 찾을 수 있습니다.")

# ============================================================
# 5부 — 실전 사례
# ============================================================
part_page("PART 5", "실전 사례로 따라 해보기", "체크리스트만으로는 감이 안 잡힐 수 있어,<br/>두 가지 가상의 사례로 실제 검색 과정을 그대로 보여드립니다.")

body("<i>아래 인물은 이해를 돕기 위한 가상의 예시이며, 등장하는 지원사업명은 실제 존재하는 사업 계열의 이름을 예시로 사용한 것입니다. 실제 신청 가능 여부와 조건은 반드시 해당 시점의 공식 공고로 확인해야 합니다.</i>")

h1("사례 1 — 카페를 막 시작한 27세 A씨")
body("A씨는 3개월 전 사업자등록을 하고 동네 카페를 연 27세 대표입니다. 인테리어 비용으로 자금이 빠듯해서 운영자금이 필요합니다.")
callout_box("A씨의 3단계 판단", [
    "축 1(사업 단계): 창업 1년 이내 → \u201c초기창업패키지\u201d 후보",
    "축 2(목적): 운영자금 필요 → 정책자금(융자) 계열",
    "축 3(특성): 만 39세 이하 → \u201c청년\u201d 키워드 추가",
], numbered=True)
body("→ 기업마당에서 &ldquo;청년 소상공인 정책자금&rdquo;으로 검색합니다. 동시에 소진공(semas.or.kr)에서 &ldquo;소상공인 정책자금&rdquo; 메뉴로 들어가 청년 특화 융자 상품이 있는지 확인합니다. 거주 지역 구청 홈페이지에서도 &ldquo;청년 창업 지원&rdquo;을 검색해 지역 전용 이차보전(이자 일부를 지자체가 대신 부담) 사업이 있는지 함께 확인합니다.")

h1("사례 2 — 20년째 식당을 운영 중인 55세 B씨")
body("B씨는 상권이 침체돼 폐업을 고민 중이지만, 온라인 배달ㆍ포장 판매로 전환해 재도전해볼지 고민하고 있습니다.")
callout_box("B씨의 3단계 판단", [
    "축 1(사업 단계): 창업 3년 이상 → \u201c재도약\u201d 계열도 후보지만, 폐업까지 고려 중이므로 \u201c희망리턴패키지\u201d도 함께 확인",
    "축 2(목적): 온라인 진출 → \u201c온라인 판로지원\u201d, \u201c스마트스토어 지원\u201d",
    "축 3(특성): 해당 없음 (일반 소상공인 기준으로 검색)",
], numbered=True)
body("→ 완전히 다른 두 갈래를 동시에 알아보는 상황이므로, 기업마당에서 &ldquo;온라인 판로지원&rdquo;과 &ldquo;희망리턴패키지&rdquo;를 각각 검색해 두 선택지의 조건을 먼저 비교합니다. 소진공 지식배움터에서 온라인 판매 관련 무료 교육이 있는지도 함께 확인하면, 신청 전에 실제 감당할 수 있는 방향인지 가늠하는 데 도움이 됩니다.")

h1("사례 3 — 소규모 제조업을 하는 42세 C씨")
body("C씨는 반찬가게에 납품하는 소규모 식품가공업체를 운영 중입니다. 노후 장비를 교체하고 위생 설비를 개선하고 싶은데, 목돈이 부담스럽습니다.")
callout_box("C씨의 3단계 판단", [
    "축 1(사업 단계): 창업 3년 이상 → “성장기반자금” 계열",
    "축 2(목적): 시설ㆍ장비 구입 → 시설자금, 스마트공장 계열",
    "축 3(특성): 제조 기반 → 중소벤처24 우선 확인",
], numbered=True)
body("→ 기업마당에서 &ldquo;시설자금&rdquo;, &ldquo;스마트공장&rdquo;으로 각각 검색하고, 중소벤처24에서 제조업 특화 지원사업이 있는지 함께 확인합니다. 소진공 정책자금 중에도 시설자금 전용 상품이 있으니 금리ㆍ한도를 비교해봅니다. 위생 설비는 지자체 식품안전 관련 부서에서 별도 보조사업을 운영하는 경우가 있어, 거주 지역 시청 &ldquo;식품안전&rdquo; 또는 &ldquo;위생&rdquo; 관련 부서 페이지도 함께 검색해보는 게 좋습니다.")

h1("사례 4 — 프리랜서에서 1인사업자로 전환한 34세 D씨")
body("D씨는 3년간 프리랜서로 디자인 일을 하다가 최근 사업자등록을 했습니다. 아직 사업 기반이 약해 안정적인 수입원을 늘리고, 자기 브랜드로 된 온라인 판매도 시작하고 싶습니다.")
callout_box("D씨의 3단계 판단", [
    "축 1(사업 단계): 창업 1년 이내(사업자등록 기준) → “초기창업패키지” 후보",
    "축 2(목적): 온라인 진출 + 컨설팅 → 온라인 판로지원 + 소진공 지식배움터",
    "축 3(특성): 해당 사항에 따라 여성기업ㆍ청년창업 키워드 추가 검토",
], numbered=True)
body("→ 프리랜서 경력은 사업자등록 이전 활동이라 &ldquo;창업 1년 이내&rdquo; 기준 판단이 헷갈릴 수 있습니다. 이런 경우 공고문의 &ldquo;창업일 기준&rdquo; 정의를 꼭 확인해야 합니다(사업자등록일 기준인지, 실제 사업 개시일 기준인지 사업마다 다릅니다). 애매하면 담당 부서에 전화로 먼저 확인하는 게 가장 확실합니다.")

h1("사례 5 — 편의점을 인수한 45세 E씨")
body("E씨는 최근 프랜차이즈 편의점을 인수해 가맹점주가 됐습니다. 본사 지원 외에 정부지원사업도 따로 받을 수 있는지 궁금합니다.")
callout_box("E씨의 3단계 판단", [
    "축 1(사업 단계): 인수 시점 기준 창업 1년 이내로 취급되는 경우가 많음 → 초기창업패키지 계열 문의",
    "축 2(목적): 초기 인수 비용 부담 → 정책자금(융자) 계열",
    "축 3(특성): 프랜차이즈 특성상 지원 제외 대상인 경우가 있어 반드시 사전 확인 필요",
], numbered=True)
body("→ 프랜차이즈 가맹점은 일부 지원사업에서 &ldquo;가맹본부 종속성이 강한 업종&rdquo;으로 분류돼 지원 대상에서 제외되는 경우가 있습니다. 신청 전에 공고문의 &ldquo;지원 제외 업종&rdquo;란을 반드시 확인하고, 애매하면 담당 부서에 프랜차이즈 가맹점도 해당되는지 직접 전화로 물어보는 게 가장 확실합니다. 소진공 정책자금은 프랜차이즈 가맹점도 신청 가능한 상품이 있으니 함께 확인하세요.")

h1("사례 6 — 스마트스토어를 운영하는 29세 F씨")
body("F씨는 오프라인 매장 없이 스마트스토어로만 사업자등록을 하고 온라인 판매를 하고 있습니다. 광고비 부담이 커서 지원사업을 찾고 있습니다.")
callout_box("F씨의 3단계 판단", [
    "축 1(사업 단계): 창업 시점에 따라 예비/초기창업패키지 해당 여부 확인",
    "축 2(목적): 온라인 마케팅ㆍ광고 부담 → 온라인 판로지원, 디지털 전환 계열",
    "축 3(특성): 사업장 없는 온라인 사업자는 신청 자격에서 &ldquo;사업장 소재지&rdquo; 기준이 다르게 적용될 수 있음",
], numbered=True)
body("→ 매장이 없는 온라인 전용 사업자는 사업자등록증에 기재된 주소(주로 자택이나 사업자 대표 주소)가 곧 &ldquo;사업장 소재지&rdquo;가 됩니다. 지역 지원사업에 신청할 때 이 주소 기준으로 자격이 판단되니, 등록 주소가 실제 거주지와 다르면 먼저 정리해두는 게 좋습니다. 기업마당에서 &ldquo;온라인 판로지원&rdquo;, &ldquo;디지털 전환&rdquo; 키워드로 검색하고, 광고비 자체를 지원하는 사업은 드물고 대부분 &ldquo;입점ㆍ제작 지원&rdquo; 형태라는 점도 참고하세요.")

h1("여섯 사례 한눈에 비교")
body("A~F씨의 상황을 표로 모아봤습니다. 본인과 가장 비슷한 사례를 빠르게 찾아보세요.")
case_summary = [
    [Paragraph("인물", styles["table_head"]), Paragraph("상황", styles["table_head"]), Paragraph("핵심 키워드", styles["table_head"])],
    [Paragraph("A씨(27세)", styles["table_cell"]), Paragraph("카페 창업 3개월차, 운영자금 필요", styles["table_cell"]), Paragraph("청년 소상공인 정책자금", styles["table_cell"])],
    [Paragraph("B씨(55세)", styles["table_cell"]), Paragraph("식당 20년, 폐업 vs 온라인 전환 고민", styles["table_cell"]), Paragraph("온라인 판로지원 / 희망리턴패키지", styles["table_cell"])],
    [Paragraph("C씨(42세)", styles["table_cell"]), Paragraph("식품가공업, 장비ㆍ설비 교체 필요", styles["table_cell"]), Paragraph("시설자금 / 스마트공장", styles["table_cell"])],
    [Paragraph("D씨(34세)", styles["table_cell"]), Paragraph("프리랜서→1인사업자 전환, 온라인 판매", styles["table_cell"]), Paragraph("초기창업패키지 / 온라인 판로지원", styles["table_cell"])],
    [Paragraph("E씨(45세)", styles["table_cell"]), Paragraph("프랜차이즈 편의점 인수, 초기비용", styles["table_cell"]), Paragraph("정책자금(제외업종 확인 필수)", styles["table_cell"])],
    [Paragraph("F씨(29세)", styles["table_cell"]), Paragraph("스마트스토어 전업, 광고비 부담", styles["table_cell"]), Paragraph("온라인 판로지원 / 디지털 전환", styles["table_cell"])],
]
case_tbl = Table(case_summary, colWidths=[26 * mm, 78 * mm, 62 * mm])
case_tbl.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#faf9ff")]),
    ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
    ("TOPPADDING", (0, 0), (-1, -1), 6),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
]))
story.append(case_tbl)

# ============================================================
# 5-2부 — 지원사업 유형 완전정리
# ============================================================
part_page("PART 5-2", "지원사업 유형 완전정리", "&ldquo;이게 무슨 사업 계열인지 모르겠다&rdquo; 싶을 때<br/>펼쳐 보는 분야별 사전입니다.")

h1("자금 지원 계열")
h2("정책자금(융자)")
body("정부ㆍ지자체ㆍ공공기관이 낮은 금리로 사업자금을 빌려주는 제도입니다. 대표적으로 소진공의 &ldquo;일반경영안정자금&rdquo;, &ldquo;특별경영안정자금&rdquo;이 있고, 시기에 따라 재해ㆍ물가 등 특수 상황 대응용 특별자금이 한시적으로 열리기도 합니다. 심사에서 신용도와 상환능력을 함께 봅니다.")

h2("정책자금 vs 은행 대출 vs 투자, 뭐가 다른가")
body("자금이 필요할 때 선택지가 정책자금만 있는 건 아닙니다. 아래 비교로 내 상황에 맞는 자금 조달 방법을 가늠해보세요.")
fund_compare = [
    [Paragraph("구분", styles["table_head"]), Paragraph("특징", styles["table_head"]), Paragraph("이런 경우 유리", styles["table_head"])],
    [Paragraph("정책자금(융자)", styles["table_cell"]), Paragraph("낮은 금리, 심사 있음, 갚아야 함", styles["table_cell"]), Paragraph("신용도가 있고 안정적 상환이 가능할 때", styles["table_cell"])],
    [Paragraph("일반 은행 대출", styles["table_cell"]), Paragraph("금리 상대적으로 높음, 심사 빠른 편", styles["table_cell"]), Paragraph("정책자금 한도를 초과하거나 급할 때", styles["table_cell"])],
    [Paragraph("보조금ㆍ지원금", styles["table_cell"]), Paragraph("갚지 않아도 됨, 용도 제한 있음", styles["table_cell"]), Paragraph("특정 목적(시설ㆍ판로 등)에 정확히 해당할 때", styles["table_cell"])],
    [Paragraph("엔젤투자ㆍ크라우드펀딩", styles["table_cell"]), Paragraph("갚지 않지만 지분을 내줌, 조달 난이도 높음", styles["table_cell"]), Paragraph("고성장 아이템으로 큰 규모 자금이 필요할 때", styles["table_cell"])],
]
fund_tbl = Table(fund_compare, colWidths=[36 * mm, 68 * mm, 62 * mm])
fund_tbl.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#faf9ff")]),
    ("GRID", (0, 0), (-1, -1), 0.6, BORDER),
    ("TOPPADDING", (0, 0), (-1, -1), 7),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
]))
story.append(fund_tbl)
story.append(Spacer(1, 10))
body("소상공인ㆍ1인사업자 대부분은 정책자금과 보조금ㆍ지원금 조합만으로도 충분한 경우가 많습니다. 투자 유치는 고성장을 목표로 하는 경우에만 고려하면 됩니다.")
h2("보조금ㆍ지원금")
body("조건을 충족하면 갚지 않아도 되는 자금입니다. 특정 목적(고용창출, 시설개선, 판로개척 등)에 쓰도록 용도가 정해져 있는 경우가 많고, 사후에 사용 내역을 증빙해야 하는 경우가 대부분입니다.")
body("<b>검색 팁</b>: 공고문 제목에 &ldquo;보조금&rdquo;, &ldquo;지원금&rdquo;이라는 단어가 직접 들어간 경우가 많아 이 단어들만으로 검색해도 후보가 꽤 걸러집니다. 단, &ldquo;지원금&rdquo;이라는 이름이 붙었어도 실제로는 융자인 경우가 섞여 있으니 3부 용어사전의 구분법대로 지원내용을 꼭 확인하세요.")
h2("바우처")
body("현금이 아니라 특정 서비스나 물품을 이용할 수 있는 이용권 형태의 지원입니다. 예를 들어 &ldquo;소상공인 경영안정 바우처&rdquo;처럼 정해진 가맹점에서만 사용할 수 있거나, 특정 용도(마케팅, 컨설팅 등)로만 쓸 수 있도록 제한된 경우가 많습니다.")
body("<b>주의</b>: 바우처는 대부분 유효기간이 정해져 있고, 기간 안에 다 쓰지 않으면 소멸됩니다. 발급받은 즉시 사용 계획을 세워두는 게 좋습니다.")

h1("역량 강화 계열")
h2("컨설팅ㆍ멘토링")
body("사업계획 수립, 재무 관리, 마케팅 전략 등을 전문가가 무료 또는 저비용으로 도와주는 프로그램입니다. 소진공 지식배움터, 창업진흥원 계열 사업에 부속된 경우가 많습니다.")
body("단발성 상담보다 여러 회차로 진행되는 멘토링 프로그램이 실질적인 도움이 되는 경우가 많습니다. 신청 시 &ldquo;몇 회차로 진행되는지&rdquo;, &ldquo;담당 멘토가 실제 해당 업종 경험이 있는지&rdquo;를 확인해보세요.")
h2("교육 프로그램")
body("온라인ㆍ오프라인 강의 형태로 제공되며, 창업 기초부터 세무ㆍ회계, 온라인 마케팅까지 주제가 다양합니다. 수료 시 이수증을 발급해 다른 지원사업 신청 시 가점으로 활용할 수 있는 경우도 있습니다.")
body("바쁜 자영업자라면 온라인(비대면) 과정을 우선 찾아보세요. 소진공 지식배움터는 상시 개설되는 온라인 강의가 많아 시간 제약 없이 들을 수 있습니다.")

h1("판로ㆍ시설 계열")
h2("판로지원")
body("온라인몰 입점 지원, 박람회ㆍ전시회 참가비 지원, 라이브커머스 제작 지원 등 매출을 늘리기 위한 지원입니다. &ldquo;온라인 판로지원&rdquo;, &ldquo;스마트스토어 지원&rdquo;이 대표적입니다.")
body("온라인 판매 채널마다 지원 성격이 조금씩 다릅니다. 자사몰(스마트스토어 등)은 입점ㆍ제작ㆍ상세페이지 지원이 많고, 오픈마켓 대형 플랫폼은 광고비ㆍ수수료 일부 지원 형태가 많으며, 라이브커머스는 방송 장비ㆍ제작 지원 형태가 많습니다. 본인이 주력하는 채널에 맞는 지원사업을 기업마당에서 &ldquo;라이브커머스&rdquo;, &ldquo;온라인 판로&rdquo; 등으로 나눠 검색해보세요.")
h2("스마트상점 / 스마트공장")
body("키오스크, 스마트오더, 서빙로봇 등 소상공인 매장의 디지털 전환을 돕는 &ldquo;스마트상점&rdquo;과, 제조업체의 생산 설비를 자동화ㆍ데이터화하는 &ldquo;스마트공장&rdquo; 지원사업이 있습니다. 도입 비용의 일부를 지원하는 방식이 일반적입니다.")
body("스마트상점은 매장 규모가 작은 소상공인도 부담 없이 신청할 수 있도록 설계된 경우가 많아, 카페ㆍ식당ㆍ소매점을 운영한다면 특히 눈여겨볼 만한 계열입니다. 스마트공장은 반대로 어느 정도 생산 라인을 갖춘 제조업체를 전제로 하는 경우가 많아, 사례3(C씨)처럼 설비 교체를 고민하는 소규모 제조업체는 시설자금과 함께 두 가지를 모두 검토해보는 게 좋습니다.")

h1("바우처 사용 시 흔히 하는 실수")
callout_box("바우처 활용 체크", [
    "가맹점 목록을 확인하지 않고 원하는 곳에서 쓰려다 거절당하는 경우 — 지정 가맹점 목록을 미리 확인하세요.",
    "유효기간을 넘겨 소멸시키는 경우 — 발급 즉시 캘린더(12부 워크시트)에 사용 기한을 적어두세요.",
    "바우처 금액을 초과하는 지출을 자비로 부담해야 하는 걸 모르고 계약하는 경우 — 견적 단계에서 바우처 한도를 미리 알려주세요.",
])

h1("창업 단계별 계열")
h2("예비창업패키지 → 초기창업패키지 → 창업도약패키지")
body("창업진흥원이 운영하는 대표 계열로, 사업 연차에 따라 세 단계로 나뉩니다. 예비창업패키지(사업자등록 전), 초기창업패키지(3년 이내), 창업도약패키지(3~7년) 순으로 지원 규모와 요구되는 사업 성숙도가 커집니다. 본인의 창업 연차에 맞는 단계를 정확히 확인하고 신청해야 합니다.")
h2("재도전 / 재도약 계열")
body("한 차례 폐업을 경험했거나, 사업 정체기를 겪고 있는 사업자를 위한 계열입니다. &ldquo;재도전 특별자금&rdquo;, &ldquo;재도약 지원사업&rdquo; 등의 이름으로 운영됩니다.")

h1("수출ㆍ인증 계열")
h2("수출지원")
body("해외 진출을 준비하거나 이미 진행 중인 기업을 위한 지원입니다. 해외 전시회 참가비, 통번역ㆍ인증비, 물류비 일부를 지원하는 사업이 많고, 코트라(KOTRA)ㆍ중소벤처24를 통해 확인할 수 있습니다. 기업마당 필터의 &ldquo;수출&rdquo; 분야를 클릭하면 관련 공고만 모아볼 수 있습니다.")
h2("품목별 인증 지원")
body("식품안전인증(HACCP), 품질경영시스템(ISO) 등 업종별로 요구되는 인증 취득 비용을 지원하는 사업입니다. 기업마당 상단 메뉴의 &ldquo;품목별 법정의무 인증제도&rdquo;에서 본인 업종에 어떤 인증이 필요한지부터 확인할 수 있습니다.")

h1("고용 계열")
h2("고용창출 지원금")
body("신규 채용을 하면 인건비 일부를 일정 기간 지원하는 사업입니다. 청년 채용, 고령자 채용, 장애인 채용 등 채용 대상에 따라 지원 조건과 금액이 다릅니다. 고용노동부와 각 지자체 일자리 관련 부서에서 운영합니다.")
h2("일자리 안정자금 / 두루누리 사회보험료 지원")
body("영세 사업장의 인건비ㆍ사회보험료 부담을 낮춰주는 지원입니다. 상시근로자 수와 급여 수준에 따라 지원 대상 여부가 갈리므로, 4대보험 관련 공단(근로복지공단, 국민연금공단 등) 홈페이지에서 조건을 확인해야 합니다.")

h1("R&amp;D 계열")
h2("중소기업 기술개발(R&amp;D) 지원사업")
body("신제품ㆍ신기술 개발에 드는 연구개발비를 지원하는 사업입니다. 기술 기반 창업이나 제조업체에 특화돼 있고, 사업계획서 대신 &ldquo;연구개발계획서&rdquo; 형태의 서류를 요구하는 경우가 많아 준비 방식이 다른 지원사업과 다릅니다. 중소벤처24, 중소기업기술정보진흥원(TIPA) 사이트에서 확인할 수 있습니다.")

h1("환경ㆍ디지털 세부 계열")
h2("친환경ㆍESG 연계 지원")
body("탄소 배출 저감, 친환경 포장재 전환, 폐기물 감축 설비 도입 등을 지원하는 사업입니다. 최근 대기업 납품 조건으로 ESG 인증을 요구하는 경우가 늘면서, 관련 지원사업도 함께 늘어나는 추세입니다.")
body("소상공인ㆍ1인사업자에게는 아직 비중이 크지 않은 영역이지만, 제조ㆍ유통업이라면 거래처가 ESG 관련 서류를 요구하기 시작했는지 미리 점검해두면 좋습니다.")
h2("AIㆍ디지털 도입 지원")
body("스마트상점(6장 참고)보다 더 세분화된 형태로, 챗봇 상담, AI 재고관리, 데이터 기반 마케팅 도구 도입 비용을 지원하는 사업입니다. 도입 후 실제 활용 실적을 보고해야 하는 경우가 많습니다.")
body("이 계열은 신설ㆍ개편이 잦은 편이라, 기업마당에서 &ldquo;AI&rdquo;, &ldquo;디지털 전환&rdquo;으로 주기적으로 재검색해보는 게 좋습니다 — 6장에서 다룬 것처럼 정부 사이트 메뉴 개편도 잦은 영역입니다.")

h1("대상 특화 계열")
h2("여성기업 지원")
body("여성 대표 사업자를 위한 전용 지원사업입니다. 정책자금 우대 금리, 공공조달 입찰 시 가점, 여성기업 전용 판로지원관 입점 등이 대표적입니다. 여성기업종합지원센터에서 &ldquo;여성기업확인서&rdquo;를 발급받아두면 여러 사업에서 공통으로 활용할 수 있습니다.")
h2("장애인기업 지원")
body("장애인 대표 사업자 또는 장애인을 고용한 사업장을 위한 지원입니다. 장애인기업종합지원센터를 통해 창업자금, 판로지원, 보조공학기기 지원 등을 확인할 수 있습니다.")
h2("지역균형 / 비수도권 특화 지원")
body("수도권 외 지역에 사업장을 둔 경우 가산점을 주거나, 지역 전용 예산으로 운영되는 사업들입니다. 같은 사업이라도 지역에 따라 지원 한도나 우대 조건이 달라질 수 있어, 전국 단위 공고를 볼 때도 &ldquo;지역 가산점&rdquo; 항목을 함께 확인하는 게 좋습니다.")

# ============================================================
# 5-3부 — 사업계획서 작성 실전 가이드
# ============================================================
part_page("PART 5-3", "사업계획서 작성 실전 가이드", "사이트에서 공고를 잘 찾아도,<br/>사업계획서가 부실하면 선정되지 않습니다.")

h1("사업계획서의 기본 구조")
body("정부지원사업 사업계획서는 사업마다 세부 양식은 다르지만, 핵심 골격은 대체로 비슷합니다. 아래 다섯 항목이 대표적입니다.")
callout_box("사업계획서 5대 항목", [
    "일반현황 — 대표자ㆍ사업 개요ㆍ업종 등 기본 정보",
    "창업동기 및 문제인식 — 왜 이 사업을 하는지, 어떤 문제를 해결하는지",
    "실현가능성 — 제품ㆍ서비스가 실제로 구현 가능한지, 시장성이 있는지",
    "성장전략 — 지원금을 받은 뒤 어떻게 매출ㆍ고용을 늘릴 것인지",
    "팀 구성 및 역량 — 대표자와 팀원이 이 사업을 해낼 역량이 있는지",
], numbered=True)
flow_diagram(["①일반현황", "②문제인식", "③실현가능성", "④성장전략", "⑤팀역량"])
story.append(Spacer(1, 10))

h1("항목별 작성 요령")

h2("1. 일반현황 — 짧고 명확하게")
body("가장 쉬운 항목이지만 오타ㆍ불일치가 의외로 많이 나옵니다. 사업자등록증의 상호명ㆍ업종코드와 사업계획서에 적은 내용이 정확히 일치하는지 제출 전에 반드시 대조하세요.")

h2("2. 창업동기 및 문제인식 — 숫자와 근거로 말하기")
body("심사위원은 하루에도 수십 건의 사업계획서를 봅니다. &ldquo;시장이 커지고 있다&rdquo;처럼 막연한 문장보다, 구체적인 근거를 드는 쪽이 훨씬 설득력 있습니다.")
callout_box("나쁜 예 vs 좋은 예", [
    "나쁜 예: “요즘 반려동물 시장이 커지고 있어서 관련 사업을 하려 합니다.”",
    "좋은 예: “동네 반려동물 미용실 5곳을 직접 방문 조사한 결과, 3곳이 예약 대기가 2주 이상이었습니다. 수요는 있지만 공급이 부족한 상황을 확인했습니다.”",
], numbered=False)
body("직접 조사한 사례, 인터뷰, 설문 결과처럼 &ldquo;내가 직접 확인한 근거&rdquo;를 넣으면 심사위원에게 신뢰감을 줍니다.")

h2("3. 실현가능성 — 이미 준비된 것을 보여주기")
body("아이디어만 있는 상태보다, 이미 시제품을 만들었거나 테스트 판매를 해본 이력이 있으면 훨씬 유리합니다. 아직 아무것도 없다면, 최소한 &ldquo;어떤 순서로 언제까지 무엇을 만들 것인지&rdquo; 구체적인 일정표(마일스톤)라도 제시하세요.")

h2("4. 성장전략 — 지원금과 연결 짓기")
body("&ldquo;열심히 하겠다&rdquo;가 아니라 &ldquo;지원금 OOO원을 받으면 이런 순서로 써서, 몇 개월 안에 매출/고용이 이만큼 늘어난다&rdquo;처럼 지원금 사용 계획과 성장 목표를 직접 연결해서 설명해야 합니다. 심사위원은 &ldquo;이 돈을 주면 실제로 성과가 날 것인가&rdquo;를 봅니다.")

h2("5. 팀 구성 및 역량 — 부족한 부분을 숨기지 않기")
body("혼자 하는 1인사업이라면 오히려 &ldquo;외주ㆍ협력업체를 어떻게 활용할 것인지&rdquo;를 구체적으로 적는 게 낫습니다. 없는 팀원을 있는 것처럼 부풀리기보다, 부족한 역량을 어떻게 보완할 계획인지 솔직하게 쓰는 편이 신뢰를 얻습니다.")

h1("자주 하는 실수 5가지")
callout_box("작성 전에 점검하세요", [
    "공고문 배점표를 안 보고 쓴다 — 어떤 항목에 점수가 많이 걸려있는지 모르고 균등하게 쓰면, 정작 중요한 항목이 부실해집니다.",
    "경쟁사ㆍ유사 서비스 언급을 피한다 — 오히려 경쟁 현황을 정확히 파악하고 있다는 인상을 줘야 신뢰를 얻습니다. 없는 척하지 마세요.",
    "숫자 없이 형용사로만 쓴다 — “많은”, “빠른”, “저렴한” 대신 구체적 수치를 넣으세요.",
    "양식의 글자수ㆍ페이지 제한을 넘긴다 — 심사 전 서류 요건 미충족으로 자동 탈락하는 경우가 실제로 있습니다.",
    "마감 당일에 처음 작성을 시작한다 — 최소 1주일 전에는 초안을 완성해 다른 사람에게 검토받는 시간을 확보하세요.",
], numbered=False)

h1("업종별 작성 예문 모음")
body("&ldquo;창업동기 및 문제인식&rdquo; 항목을 업종별로 어떻게 풀어 쓰는지 세 가지 예시로 보여드립니다. 그대로 베끼지 말고, 본인 상황에 맞게 숫자와 근거를 바꿔서 참고하세요.")

h2("예문 ① 카페 창업")
quote("&ldquo;반경 500m 내 카페 7곳을 직접 방문해 평균 대기시간과 좌석 회전율을 조사한 결과, 점심시간(12~13시) 좌석 부족으로 발길을 돌리는 손님이 평균 4~6명 확인됐습니다. 좌석 회전율을 높이는 테이크아웃 특화 동선으로 이 수요를 흡수하고자 합니다.&rdquo;")

h2("예문 ② 온라인 쇼핑몰 창업")
quote("&ldquo;동일 카테고리 상위 판매자 10곳의 리뷰 300건을 분석한 결과, &lsquo;사이즈 정보가 부정확하다&rsquo;는 불만이 전체의 34%를 차지했습니다. 정확한 실측 사이즈표와 착용 후기를 기본 제공해 이 불만을 해소하는 방식으로 차별화하겠습니다.&rdquo;")

h2("예문 ③ 제조업(식품가공) 창업")
quote("&ldquo;납품 중인 반찬가게 3곳으로부터 &lsquo;소포장 단위 주문이 어렵다&rsquo;는 요청을 반복해서 받았습니다. 기존 대량 포장 설비로는 대응이 안 돼, 이번 지원사업으로 소포장 전용 설비를 도입해 이 수요에 대응하고자 합니다.&rdquo;")

body("세 예문의 공통점은 <b>&ldquo;내가 직접 확인한 숫자&rdquo;로 시작한다는 것</b>입니다. 방문 조사, 리뷰 분석, 실제 요청 사례처럼 검증 가능한 근거를 앞세우면 심사위원이 훨씬 신뢰합니다.")

h1("발표평가 준비 팁")
callout_box("서류를 통과했다면", [
    "발표 시간(보통 5~10분)을 정확히 지키는 연습을 하세요 — 시간 초과는 감점 요인입니다.",
    "심사위원이 가장 많이 묻는 질문은 &ldquo;그래서 어떻게 돈을 벌 것인가&rdquo;입니다. 수익모델을 한 문장으로 답할 수 있게 준비하세요.",
    "사업계획서에 없는 내용을 발표에서 갑자기 꺼내지 마세요 — 서류와 발표 내용이 다르면 신뢰도가 떨어집니다.",
    "예상 질문과 답변을 미리 종이에 적어보고, 실제로 소리 내어 답하는 연습을 해보세요.",
], numbered=False)

# ============================================================
# 6부 — 키워드 모음
# ============================================================
part_page("PART 6", "사이트별 검색 키워드 모음", "사이트 검색창에 아래 키워드를 그대로 넣어보세요.")

callout_box("바로 써먹는 검색 키워드", [
    "소상공인 정책자금",
    "청년창업 지원사업",
    "예비창업패키지 / 초기창업패키지",
    "재도전 특별자금",
    "희망리턴패키지 (폐업/재창업 준비)",
    "온라인 판로지원 / 스마트스토어 지원",
    "디지털 전환 지원 / 스마트상점",
    "경영안정자금",
    "여성기업 지원사업 (해당 시)",
    "장애인기업 지원사업 (해당 시)",
    "(거주 지역명) 소상공인 지원사업 — 반드시 지역명을 넣어 검색",
    "(거주 지역명) 청년창업 지원 — 지자체 전용 사업 확인용",
])

h1("키워드는 어떻게 조합해서 쓰는가 — 검색 시나리오 3가지")
body("위 키워드를 그냥 하나씩 넣어보는 것도 방법이지만, 상황에 맞게 두세 개를 조합하면 훨씬 빨리 원하는 공고에 닿습니다. 5부의 A~F씨 사례와 같은 방식으로, 실제로 검색창에 뭘 입력하고 어떤 순서로 좁혀가는지 그대로 보여드립니다.")

callout_box("시나리오 ① — 임차료가 부담스러운 소상공인", [
    "기업마당(bizinfo.go.kr) 검색창에 &ldquo;소상공인 경영안정자금&rdquo; 입력",
    "결과에서 &ldquo;지원사업공고&rdquo; 탭만 먼저 확인 (행사정보ㆍ뉴스는 건너뛰기)",
    "결과가 많으면 상단 지역 필터에서 본인 사업장 지역(예: &ldquo;부산&rdquo;)을 클릭해 좁히기",
    "정책자금(융자)이 필요한 상황이라면 소진공(semas.or.kr)에서 같은 키워드로 한 번 더 검색해 금리ㆍ한도를 비교",
], numbered=True)

callout_box("시나리오 ② — 이제 막 사업자등록을 한 예비창업자", [
    "기업마당 검색창에 &ldquo;예비창업패키지&rdquo; 입력",
    "&ldquo;신청기간&rdquo;란이 &ldquo;모집중&rdquo;인 공고만 우선 확인 (마감된 공고는 걸러내기)",
    "자격요건에 &ldquo;예비창업자&rdquo; 또는 &ldquo;사업자등록 전&rdquo;이 명시된 것만 추리기",
    "후보가 좁혀지면 담당 부서 연락처로 전화해 본인이 해당되는지 미리 확인",
], numbered=True)

callout_box("시나리오 ③ — 지방 소도시에서 창업 준비 중인 경우", [
    "중앙 사이트부터 보지 말고, 먼저 기업마당에 &ldquo;(지역명) 소상공인 지원사업&rdquo;처럼 지역명과 키워드를 함께 입력(예: &ldquo;전주 소상공인 지원사업&rdquo;)",
    "검색 결과가 적거나 없으면, 그 지역 시청ㆍ군청 홈페이지의 &ldquo;고시공고&rdquo; 게시판에서 같은 키워드로 다시 검색",
    "네이버ㆍ구글 등 일반 검색엔진에도 같은 지역명+키워드 조합을 넣어 지자체 보도자료ㆍ공지사항이 걸리는지 교차 확인",
], numbered=True)
body("세 시나리오의 공통점은 <b>키워드 하나로 끝내지 않고, 지역ㆍ자격ㆍ신청기간 조건을 단계적으로 덧붙여 좁혀간다</b>는 것입니다. 결과가 안 나온다고 포기하지 말고, 키워드를 살짝 바꾸거나(예: &ldquo;청년창업&rdquo; → &ldquo;청년 창업자&rdquo;) 사이트를 바꿔가며 같은 방식을 반복해보세요.")

# ============================================================
# 7부 — 신청 전 체크리스트
# ============================================================
part_page("PART 7", "신청 전 체크리스트", "떨어지는 이유는 대부분 비슷했습니다.<br/>신청 전에 아래를 꼭 확인하세요.")

callout_box("신청 전 최종 점검", [
    "모집공고를 끝까지 읽었는가 — 지원대상ㆍ제외대상 조건만 봐도 걸러지는 경우가 많습니다.",
    "마감일 직전에 신청하지 않는가 — 마감 임박에는 접속 폭주, 서류 오류로 제출 자체가 안 되는 경우가 있습니다. 최소 2~3일 여유를 두세요.",
    "사업계획서를 성의 있게 썼는가 — 첫 페이지에서 다른 신청자와의 차별점이 보여야 합니다.",
    "증빙서류를 빠짐없이 준비했는가 — 사업자등록증, 신분증, 통장 사본은 기본이고, 임대차계약서ㆍ4대보험 가입내역 등이 추가로 필요한 경우가 많습니다.",
    "자격 요건을 정확히 확인했는가 — 소상공인 기준(업종별 매출액ㆍ상시근로자 수)에 해당하는지 먼저 확인하세요.",
    "중복 지원 제한을 확인했는가 — 이미 받은 지원사업과 중복 불가한 경우가 있습니다.",
    "문의처에 미리 확인했는가 — 애매한 조건은 공고에 나온 담당 부서에 전화로 먼저 물어보는 게 가장 확실합니다.",
    "인증서ㆍ계정을 미리 준비했는가 — 공동인증서나 간편인증이 없으면 마감 직전에 발급받느라 시간을 놓칠 수 있습니다.",
], numbered=True)

# ============================================================
# 8부 — FAQ
# ============================================================
part_page("PART 8", "자주 묻는 질문 (FAQ)", "")

def faq(q, a):
    story.append(Paragraph(f"Q. {q}", ParagraphStyle("faqq", fontName=FONT, fontSize=12.3, leading=18, textColor=ACCENT, spaceBefore=12, spaceAfter=4)))
    body(a)

faq("여러 지원사업에 동시에 신청해도 되나요?", "가능한 경우가 많지만, 사업마다 &ldquo;중복 지원 제한&rdquo; 조건이 다릅니다. 공고문의 지원 제외 대상란을 반드시 확인하고, 애매하면 담당 부서에 전화로 확인하는 게 가장 확실합니다.")
faq("신청했는데 왜 떨어졌는지 알려주나요?", "사업마다 다릅니다. 탈락 사유를 개별 통보하는 사업도 있고, 통보하지 않는 사업도 있습니다. 통보가 없다면 담당 부서에 직접 문의해 다음 신청에 참고할 점을 물어보는 것도 방법입니다.")
faq("사업자등록을 하기 전에도 신청할 수 있는 지원사업이 있나요?", "있습니다. &ldquo;예비창업패키지&rdquo;처럼 이름에 &ldquo;예비&rdquo;가 붙은 사업들이 대표적입니다. 다만 선정 이후 일정 기간 안에 사업자등록을 완료해야 하는 조건이 붙는 경우가 대부분입니다.")
faq("정책자금(융자)도 신용등급을 보나요?", "사업마다 심사 기준이 다르지만, 대체로 개인신용평점과 사업 타당성을 함께 봅니다. 저신용자 특화 상품도 있으니, 소진공 창구나 콜센터(1533-0100)에 본인 상황을 먼저 상담해보는 걸 추천합니다.")
faq("세무사나 대행업체에 신청을 맡겨도 되나요?", "서류 작성 컨설팅을 받는 것은 문제되지 않지만, 정부지원금ㆍ보조금 신청을 &ldquo;수수료를 받고 대신 신청ㆍ수령&rdquo;하는 행위는 보조금관리법 등에 저촉될 소지가 있습니다. 최종 신청자 명의와 서명은 반드시 본인이어야 하며, 이 원칙은 이 가이드에도 동일하게 적용됩니다 — 저희 역시 신청을 대행하지 않습니다.")
faq("지원금을 받으면 나중에 세금을 더 내나요?", "지원금의 종류에 따라 과세 대상인 경우와 비과세인 경우가 나뉩니다. 정확한 세무 처리는 이 가이드에서 확정적으로 안내드릴 수 없는 영역이라, 세무사 상담을 권장합니다.")
faq("공고문에 자격 요건이 애매하게 적혀 있으면 어떻게 하나요?", "임의로 해석하지 말고 공고문 하단에 적힌 담당 부서ㆍ담당자 연락처로 직접 전화하세요. 신청 전 문의는 감점 요인이 아니라, 오히려 요건에 안 맞는데 신청해서 서류 심사 단계에서 탈락하는 것을 막아줍니다.")
faq("한 번 탈락하면 같은 사업에 다시 신청할 수 없나요?", "대부분의 사업은 회차(분기별, 반기별 등)를 나눠 여러 번 모집합니다. 이번 회차에서 떨어졌다고 해도 다음 회차에 재도전할 수 있는 경우가 많으니, 공고문에서 &ldquo;연간 모집 계획&rdquo;이나 &ldquo;차수&rdquo; 정보를 확인해보세요.")
faq("법인이 아니라 개인사업자인데도 신청할 수 있나요?", "가능한 사업이 대부분입니다. 오히려 소상공인 대상 사업 중에는 법인보다 개인사업자를 주로 겨냥한 것도 많습니다. 다만 일부 기술 기반ㆍR&amp;D 사업은 법인만 대상으로 하는 경우가 있으니 공고문의 &ldquo;신청 자격&rdquo;란에서 사업자 형태 제한을 꼭 확인하세요.")
faq("온라인 신청 중 시스템 오류가 나면 어떻게 하나요?", "화면을 캡처해두고 즉시 담당 부서나 사이트 고객센터에 연락하세요. 마감 시간 직전 오류로 제출하지 못한 경우, 오류 캡처 자료가 있으면 구제받는 사례가 있습니다. 이런 상황을 피하려면 애초에 마감 최소 2~3일 전에 제출을 마치는 게 가장 안전합니다.")
faq("여러 사이트에 각각 회원가입을 다 해야 하나요?", "사이트마다 회원 체계가 분리돼 있어 대부분 개별 가입이 필요합니다. 다만 공동인증서나 간편인증을 미리 만들어두면, 사이트마다 새로 인증 수단을 준비하지 않고 재사용할 수 있어 가입 자체는 빠르게 끝납니다.")
faq("지원사업에 선정된 뒤에도 계속 확인해야 할 게 있나요?", "네. 협약서에 적힌 자금 집행 기한과 정산보고 시점을 캘린더에 미리 표시해두세요. 정산보고를 놓치면 이미 받은 지원금 환수는 물론, 이후 다른 지원사업 신청에도 불이익이 있을 수 있습니다.")
faq("공동사업자(동업)인데 대표자 한 명만 신청하면 되나요?", "대부분 대표 사업자 명의로 신청합니다. 다만 지분 구조나 공동대표 여부에 따라 제출 서류가 추가될 수 있으니, 담당 부서에 공동사업자 특이사항을 미리 알리고 확인하는 게 안전합니다.")
faq("이미 다른 대출(일반 은행 대출)이 있어도 정책자금 신청이 되나요?", "가능한 경우가 많지만, 총 부채 규모나 상환 능력을 함께 심사하는 경우가 있습니다. 소진공 콜센터(1533-0100)에 본인의 대출 현황을 먼저 상담받아보는 걸 추천합니다.")
faq("사업계획서를 손글씨로 써서 스캔해도 되나요?", "대부분의 온라인 신청 시스템은 지정된 양식(한글ㆍ워드 파일)을 요구합니다. 공고문에 첨부된 양식 파일을 그대로 사용하는 게 원칙입니다.")
faq("지원사업 신청 결과 발표는 보통 얼마나 걸리나요?", "사업마다 다르지만, 서류 심사부터 최종 발표까지 보통 3주에서 2개월 정도 걸립니다. 공고문의 &ldquo;향후 일정&rdquo;란에 대략적인 심사 일정이 안내돼 있습니다.")
faq("지원사업에 선정되면 반드시 그 계획대로만 써야 하나요?", "협약서에 명시된 용도 범위 안에서는 어느 정도 조정이 가능한 경우가 많지만, 큰 변경은 사전에 담당 부서 승인을 받아야 합니다. 임의로 다른 용도에 사용하면 환수 사유가 될 수 있습니다.")
faq("여러 지원사업 담당 부서가 서로 다른 답을 주면 어떻게 하나요?", "공고문을 발행한 기관의 답변이 최우선입니다. 정보가 엇갈리면 반드시 해당 공고문 하단에 적힌 담당 부서에 재확인하고, 가능하면 통화 내용을 메모해두세요.")
faq("지원사업 신청에 나이 제한이 있나요?", "청년 전용 사업은 대체로 만 39세 이하로 제한되지만, 일반 소상공인 대상 사업은 대부분 연령 제한이 없습니다. 오히려 중장년ㆍ시니어 전용 재창업 지원사업도 있으니 연령이 걸림돌이라고 지레 포기하지 마세요.")
faq("공동창업(2인 이상 대표)인 경우 신청 방법이 다른가요?", "사업마다 다르지만, 대표자 1인 명의로 신청하되 공동대표 사실을 서류에 명시하는 경우가 일반적입니다. 지분 구조에 따라 추가 서류가 필요할 수 있어 담당 부서 확인이 필요합니다.")
faq("휴업 이력이 있으면 불리한가요?", "휴업 사유와 기간에 따라 다릅니다. 일부 사업은 계속 사업 영위 기간을 기준으로 삼기 때문에 휴업 이력이 불리하게 작용할 수 있으니, 공고문의 &ldquo;계속사업 여부&rdquo; 조건을 확인하고 애매하면 문의하세요.")
faq("여러 사업장(지점)을 운영 중인데 어느 지점 기준으로 신청하나요?", "본점(사업자단위과세) 기준으로 신청하는 경우가 대부분이지만, 지역 한정 지원사업은 실제 지원 대상 지점 주소를 별도로 요구하기도 합니다. 공고문의 &ldquo;사업장&rdquo; 정의를 확인하고 애매하면 문의하세요.")
faq("외국인이 대표인 사업자도 신청할 수 있나요?", "사업마다 다릅니다. 내국인 대표만 가능한 사업도 있고, 외국인등록증ㆍ체류자격에 따라 신청 가능한 사업도 있습니다. 공고문의 &ldquo;신청 자격&rdquo;란에서 국적 관련 조건을 꼭 확인하세요.")
faq("지원사업 신청 이력이 심사에 계속 남아 다음 신청에 불리해지나요?", "일반적으로 탈락 이력 자체가 다음 신청에 불이익을 주지는 않습니다. 다만 중복 지원 제한이나 사후관리 위반 이력은 시스템에 남아 향후 신청에 영향을 줄 수 있으니, 선정된 사업의 의무사항(9-2부 참고)은 꼭 지키세요.")
faq("이 가이드에 나온 사이트들 말고 또 확인할 곳이 있나요?", "업종에 따라 다릅니다. 예를 들어 농업 관련이면 농림축산식품부ㆍ농촌진흥청, 문화콘텐츠라면 한국콘텐츠진흥원처럼 업종별 전담기관이 별도로 있는 경우가 많습니다. 기업마당에서 본인 업종을 검색하면 관련 전담기관이 함께 언급되는 경우가 많으니 참고하세요.")
faq("노란우산공제와 정부지원사업은 같은 건가요?", "다릅니다. 노란우산공제는 소상공인 스스로 매달 납입해 폐업ㆍ퇴직 시 목돈을 받는 공적 공제제도(중소기업중앙회 운영)이고, 이 가이드에서 다룬 지원사업과는 별개입니다. 다만 일부 지원사업 심사에서 가입 여부가 가점 요소가 되는 경우가 있습니다.")
faq("지원사업 관련 사기를 조심해야 한다고 들었는데, 어떻게 구별하나요?", "공식 기관 사이트(정부 도메인은 .go.kr, 공공기관은 .or.kr이 많음)를 벗어난 곳에서 신청비ㆍ수수료를 요구하면 의심해야 합니다. 정부지원사업은 신청 자체에 비용이 들지 않는 것이 원칙입니다. 애매하면 부록3의 콜센터로 먼저 확인하세요.")
faq("이 가이드의 내용을 다른 사람에게 공유해도 되나요?", "개인적으로 참고하시는 건 자유입니다. 다만 이 전자책 파일 자체를 무단으로 재배포ㆍ재판매하는 것은 삼가주세요.")
faq("지원사업을 여러 개 동시에 준비하려면 어떻게 시간을 관리하나요?", "9부의 연간 캘린더를 기준으로 마감일이 겹치지 않는 사업 위주로 우선순위를 정하고, 12부 워크시트4-2(90일 실행 캘린더)에 주차별로 배분해두면 한눈에 파악할 수 있습니다. 서류가 겹치는 사업끼리는 동시에 준비하면 효율적입니다.")
faq("이 가이드에 나온 워크시트를 전부 다 써야 하나요?", "아닙니다. 본인 상황에 필요한 것만 골라 쓰면 됩니다. 처음이라면 워크시트1(상황 정리)과 워크시트5(자가진단)부터 시작하는 걸 추천합니다.")

# ============================================================
# 9부 — 연간 지원사업 캘린더
# ============================================================
part_page("PART 9", "연간 지원사업 캘린더", "정부지원사업은 연중 아무 때나 균일하게 나오지 않습니다.<br/>시기별로 무엇을 확인해야 하는지 정리했습니다.")

h1("월별 확인 포인트")
callout_box("1~2월 — 한 해의 시작, 가장 중요한 시기", [
    "대부분의 연간 정책자금ㆍ지원사업 예산이 새로 편성돼 공고가 집중적으로 쏟아지는 시기입니다.",
    "정책자금(융자)은 예산이 소진되면 연중에도 조기 마감되므로, 이 시기에 가장 먼저 확인해야 합니다.",
    "예비창업패키지ㆍ초기창업패키지 등 연간 대표 사업의 1차 모집이 시작되는 경우가 많습니다.",
], numbered=False)
callout_box("3~6월 — 상반기 집행", [
    "1~2월에 놓친 사업의 2차ㆍ3차 모집이 이어집니다.",
    "지자체 예산 기반 사업들의 공고가 이 시기에 많이 올라옵니다.",
    "교육ㆍ컨설팅 프로그램은 상반기에 기수를 자주 모집합니다.",
], numbered=False)
callout_box("7~9월 — 하반기 대비", [
    "상반기 사업의 성과를 바탕으로 하반기 추가경정예산(추경) 관련 지원사업이 나오기도 합니다.",
    "다음 해 사업을 미리 준비하려면 이 시기부터 필요 서류(사업계획서 초안 등)를 준비해두면 유리합니다.",
], numbered=False)
callout_box("10~12월 — 마감 러시 + 다음 해 예고", [
    "연간 예산 집행 마감 시한이 다가오며 신청 가능한 사업 수가 줄어드는 시기입니다.",
    "일부 기관은 다음 해 지원사업 계획을 미리 예고 발표합니다 — 기업마당 &ldquo;정책뉴스&rdquo;, 각 기관 공지사항을 챙겨보면 1월에 남들보다 빠르게 준비할 수 있습니다.",
], numbered=False)
quote("핵심은 &ldquo;생각날 때 한 번 찾아보는 것&rdquo;이 아니라, 1~2월에 한 번, 이후 분기마다 한 번씩 정기적으로 확인하는 습관입니다.")

h1("월별 상세 캘린더")
body("위 분기별 요약을 달마다 더 세분화했습니다. 매달 무엇을 확인하면 좋을지 짚어보세요.")
month_notes = [
    ("1월", "연간 정책자금 공고가 가장 먼저 열리는 시기. 소진공ㆍ기업마당을 가장 먼저 확인하세요."),
    ("2월", "예비창업패키지ㆍ초기창업패키지 등 대표 창업 사업 1차 모집이 시작되는 경우가 많습니다."),
    ("3월", "지자체 예산 기반 사업 공고가 본격적으로 올라오기 시작합니다."),
    ("4월", "1분기에 놓친 정책자금의 잔여 한도나 2차 모집을 확인하기 좋은 시기입니다."),
    ("5월", "교육ㆍ컨설팅 프로그램의 상반기 기수 모집이 몰리는 시기입니다."),
    ("6월", "상반기 마감 전 막바지 공고들을 놓치지 않았는지 한 번 점검하세요."),
    ("7월", "하반기 사업 준비를 시작하기 좋은 시기 — 필요 서류를 미리 갱신해두세요."),
    ("8월", "추가경정예산(추경) 관련 신규 사업이 발표되는 경우가 있어 정책뉴스를 챙겨보세요."),
    ("9월", "하반기 창업 지원사업의 신규ㆍ추가 모집이 이어집니다."),
    ("10월", "연말로 갈수록 신청 가능한 사업 수가 줄어드니 관심 사업은 서둘러 확인하세요."),
    ("11월", "일부 기관이 다음 해 사업 계획을 미리 예고하기 시작합니다."),
    ("12월", "한 해를 정리하며 올해 놓친 카테고리를 메모해두면 다음 해 1월에 바로 활용할 수 있습니다."),
]
month_rows = [[Paragraph(f"<b>{m}</b>", styles["table_cell"]), Paragraph(n, styles["table_cell"])] for m, n in month_notes]
month_tbl = Table(month_rows, colWidths=[18 * mm, 148 * mm])
month_tbl.setStyle(TableStyle([
    ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
    ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#faf9ff")]),
    ("TOPPADDING", (0, 0), (-1, -1), 6),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
]))
story.append(month_tbl)

# ============================================================
# 9-2부 — 선정 이후 생애주기
# ============================================================
part_page("PART 9-2", "선정 이후 — 협약부터 정산까지", "합격 통보를 받고 나면 끝이 아니라 시작입니다.<br/>이후 과정을 미리 알아두면 당황하지 않습니다.")

h1("선정 이후 5단계")
body("다섯 단계를 순서대로 그림으로 옮기면 아래와 같습니다.")

flow_diagram(["① 선정통보", "② 협약체결", "③ 자금집행", "④ 중간점검", "⑤ 정산보고"])
story.append(Spacer(1, 10))

callout_box("선정 통보부터 정산까지", [
    "① 선정 통보 — 문자ㆍ이메일ㆍ시스템 알림으로 통보됩니다. 통보 후 협약 절차 안내가 함께 오는 경우가 많습니다.",
    "② 협약 체결 — 지원 조건ㆍ의무사항ㆍ자금 집행 계획을 기관과 공식 계약합니다. 이 단계에서 서명하면 법적 효력이 생기므로 조항을 꼼꼼히 읽어야 합니다.",
    "③ 자금 집행 — 협약서에 명시된 용도ㆍ기한 안에서만 자금을 사용해야 합니다. 용도 외 사용은 환수 사유입니다.",
    "④ 중간점검(사업에 따라) — 일부 사업은 집행 중간에 진행 상황을 보고하도록 요구합니다.",
    "⑤ 정산보고 — 사용 내역을 증빙자료와 함께 최종 보고합니다. 이 단계를 소홀히 하면 지원금 환수는 물론, 향후 다른 지원사업 신청에도 불이익이 있을 수 있습니다.",
], numbered=False)

h1("협약서에서 특히 눈여겨봐야 할 조항")
callout_box("체크포인트", [
    "자금 집행 기한 — 협약일로부터 몇 개월 안에 다 써야 하는지",
    "용도 제한 — 어떤 항목에는 쓸 수 없다고 명시돼 있는지",
    "환수 조건 — 어떤 경우에 지원금을 다시 반납해야 하는지",
    "정산보고 시점과 제출 서류 — 언제, 무엇을 제출해야 하는지",
    "사후관리 의무 — 사업 종료 후에도 일정 기간 보고 의무가 있는지",
])
body("협약서는 법적 효력이 있는 문서입니다. 이해가 안 되는 조항이 있으면 서명 전에 반드시 담당 부서에 물어보세요 — 11부의 통화 스크립트를 그대로 활용해도 됩니다.")

h1("환수 사유가 되는 대표 사례")
body("실제로 지원금 환수(다시 반납)로 이어지는 경우는 대부분 아래 세 가지 중 하나입니다.")
callout_box("이런 경우 환수될 수 있습니다", [
    "협약서에 명시된 용도가 아닌 곳에 지원금을 사용한 경우",
    "정산보고 기한을 지키지 않거나, 증빙자료 없이 사용 내역을 제출한 경우",
    "허위 서류로 신청해 선정된 사실이 사후에 확인된 경우",
])
body("반대로 말하면, 이 세 가지만 지키면 환수를 걱정할 일은 거의 없습니다. 협약서를 받으면 이 세 항목부터 확인하는 습관을 들이세요.")

# ============================================================
# 9-3부 — 공고문 읽는 법
# ============================================================
part_page("PART 9-3", "실제 공고문 읽는 법 — 항목별 해설", "공고문은 형식이 거의 정해져 있습니다.<br/>항목별로 어디를 봐야 하는지 짚어드립니다.")

h1("공고문의 표준 구조")
body("정부지원사업 공고문은 기관이 달라도 대체로 같은 항목 순서로 구성됩니다. 아래는 일반적인 공고문의 구조를 항목별로 정리한 것입니다(특정 공고를 그대로 옮긴 것이 아니라, 여러 공고에서 공통으로 나타나는 형식을 정리한 예시입니다).")

def notice_field(field, guide):
    rows = [[Paragraph(f"<b>{field}</b>", ParagraphStyle("nf_field", fontName=FONT, fontSize=10.8, leading=15, textColor=colors.white))],
            [Paragraph(guide, styles["body"])]]
    t = Table(rows, colWidths=[166 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#faf9ff")),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 1), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
        ("BOX", (0, 0), (-1, -1), 0.8, BORDER),
    ]))
    story.append(t)
    story.append(Spacer(1, 8))

notice_field("① 사업목적", "이 사업이 왜 만들어졌는지 설명하는 부분입니다. 여기 적힌 목적과 내 사업이 얼마나 맞닿아 있는지가 사업계획서 &ldquo;문제인식&rdquo; 항목의 출발점이 됩니다.")
notice_field("② 신청자격", "가장 먼저, 가장 꼼꼼히 봐야 하는 항목입니다. 업종ㆍ매출액ㆍ상시근로자 수ㆍ창업 시기 등 자격 조건이 나열됩니다. 하나라도 안 맞으면 아예 신청 자체가 무의미하니 맨 처음 확인하세요.")
notice_field("③ 지원내용", "얼마를, 어떤 형태로(융자/보조금/바우처) 지원하는지 나옵니다. 3부 용어사전의 &ldquo;정책자금 vs 지원금&rdquo; 구분을 여기서 다시 확인하세요.")
notice_field("④ 신청기간", "접수 시작일과 마감일입니다. &ldquo;모집 마감시&rdquo;라고만 적혀 있으면 정해진 마감일 없이 예산 소진 시까지 상시 접수한다는 뜻입니다.")
notice_field("⑤ 제출서류", "필수로 내야 하는 서류 목록입니다. 부록1ㆍ워크시트4의 체크리스트와 대조해가며 준비하세요.")
notice_field("⑥ 선정절차", "서류 심사만 있는지, 발표평가(면접)까지 있는지 나옵니다. 발표평가가 있다면 5-3부 발표평가 준비 팁을 참고하세요.")
notice_field("⑦ 문의처", "담당 부서 전화번호ㆍ이메일입니다. 애매한 조건은 여기로 11부 스크립트를 활용해 문의하세요.")

h1("항목을 다 채운 예시로 보기")
body("아래는 앞서 설명한 7개 항목을 실제 공고문처럼 배치해본 예시입니다(특정 공고를 그대로 옮긴 것이 아니라, 일반적인 형식을 보여주기 위해 구성한 예시입니다).")

sample_notice = [
    [Paragraph("<b>2026년 OO 소상공인 온라인 판로지원 사업 참가기업 모집 공고</b>", ParagraphStyle("snhead", fontName=FONT, fontSize=11.5, leading=17, textColor=colors.white))],
    [Paragraph(
        "① 사업목적: 온라인 판매 역량이 부족한 소상공인의 온라인몰 입점 및 상세페이지 제작을 지원하여 매출 다각화를 도모함<br/><br/>"
        "② 신청자격: 사업자등록 후 6개월 이상 경과한 소상공인(중소기업기본법상 소상공인 기준 충족) ※유흥업종, 금융업 등 제외<br/><br/>"
        "③ 지원내용: 상세페이지 제작비 최대 150만원(자기부담 20%), 온라인몰 입점 컨설팅 3회<br/><br/>"
        "④ 신청기간: 2026.08.01 ~ 2026.08.20(18:00) <b>※마감 엄수, 접수 마감시 자동 종료</b><br/><br/>"
        "⑤ 제출서류: 사업자등록증명원, 참가신청서(별첨 양식), 최근 3개월 매출 증빙자료<br/><br/>"
        "⑥ 선정절차: 서류심사(적격 여부) → 선정위원회 심사 → 결과 개별 통보(9월 첫째 주 예정)<br/><br/>"
        "⑦ 문의처: OO진흥원 판로지원팀 (☎ 02-000-0000, 이메일 생략)",
        styles["body"]
    )],
]
sn_tbl = Table(sample_notice, colWidths=[166 * mm])
sn_tbl.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
    ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#faf9ff")),
    ("BOX", (0, 0), (-1, -1), 0.9, BORDER),
    ("TOPPADDING", (0, 0), (-1, 0), 8),
    ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
    ("LEFTPADDING", (0, 0), (-1, -1), 14),
    ("RIGHTPADDING", (0, 0), (-1, -1), 14),
    ("TOPPADDING", (0, 1), (-1, -1), 10),
    ("BOTTOMPADDING", (0, 1), (-1, -1), 10),
]))
story.append(sn_tbl)
story.append(Spacer(1, 10))
body("이 예시라면 신청 전 체크할 포인트가 이렇게 나옵니다: <b>&ldquo;사업자등록 6개월&rdquo;</b> 조건 충족 여부, <b>&ldquo;자기부담 20%&rdquo;</b>(150만원 지원이면 약 30만원은 본인 부담) 준비 여부, <b>&ldquo;최근 3개월 매출 증빙&rdquo;</b> 서류를 발급하는 데 걸리는 시간, 그리고 마감이 &ldquo;엄수&rdquo;라고 강조된 만큼 여유 있게 제출하는 것입니다.")

h1("두 번째 예시로 비교하기 — 정책자금(융자)형 공고")
body("판로지원처럼 &ldquo;갚지 않는 지원&rdquo;과, 정책자금처럼 &ldquo;갚아야 하는 지원&rdquo;은 공고문 구성 자체가 다릅니다. 아래는 정책자금형 공고의 예시입니다(마찬가지로 특정 공고를 옮긴 것이 아니라 일반적인 형식을 보여주는 예시입니다).")

sample_notice2 = [
    [Paragraph("<b>2026년 OO 소상공인 일반경영안정자금 지원계획 공고</b>", ParagraphStyle("snhead2", fontName=FONT, fontSize=11.5, leading=17, textColor=colors.white))],
    [Paragraph(
        "① 사업목적: 일시적 경영애로를 겪는 소상공인의 경영안정을 위해 융자 형태로 자금을 지원함<br/><br/>"
        "② 신청자격: 사업자등록 후 1년 이상 경과한 소상공인 ※세금 체납 사업자, 휴폐업자 제외<br/><br/>"
        "③ 지원내용: 업체당 최대 7천만원, 연 2%대 고정금리, 5년 상환(2년 거치)<br/><br/>"
        "④ 신청기간: 상시(예산 소진 시 조기 마감) <b>※연초 신청 권장</b><br/><br/>"
        "⑤ 제출서류: 사업자등록증명원, 신용정보조회 동의서, 매출액 증빙서류<br/><br/>"
        "⑥ 선정절차: 서류접수 → 신용도ㆍ상환능력 심사 → 자금 배정 통보<br/><br/>"
        "⑦ 문의처: 소상공인시장진흥공단 콜센터 (☎ 1533-0100)",
        styles["body"]
    )],
]
sn2_tbl = Table(sample_notice2, colWidths=[166 * mm])
sn2_tbl.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
    ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#faf9ff")),
    ("BOX", (0, 0), (-1, -1), 0.9, BORDER),
    ("TOPPADDING", (0, 0), (-1, 0), 8),
    ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
    ("LEFTPADDING", (0, 0), (-1, -1), 14),
    ("RIGHTPADDING", (0, 0), (-1, -1), 14),
    ("TOPPADDING", (0, 1), (-1, -1), 10),
    ("BOTTOMPADDING", (0, 1), (-1, -1), 10),
]))
story.append(sn2_tbl)
story.append(Spacer(1, 10))
callout_box("두 예시의 차이 비교", [
    "지원내용: 첫 번째는 &ldquo;제작비 지원&rdquo;(갚지 않음), 두 번째는 &ldquo;융자&rdquo;(갚아야 함) — 이 차이가 신청 여부를 가르는 가장 큰 기준입니다.",
    "신청기간: 첫 번째는 특정 마감일, 두 번째는 상시(예산 소진 시 마감) — 상시 모집은 서두를수록 유리합니다.",
    "제출서류: 두 번째는 신용정보조회 동의서가 추가로 필요합니다 — 융자형 공고에서 자주 요구되는 서류입니다(부록1 참고).",
])

h1("읽을 때 반드시 표시해야 할 세 단어")
callout_box("이 단어가 보이면 반드시 표시하고 넘어가세요", [
    "&ldquo;제외&rdquo; — 지원 제외 대상에 내가 해당하지 않는지 확인",
    "&ldquo;필수&rdquo; — 빠지면 안 되는 서류나 조건",
    "&ldquo;단,&rdquo; — 예외 조항이 뒤따르는 경우가 많아 놓치기 쉬운 부분",
])

# ============================================================
# 10부 — 자주 하는 오해 10가지
# ============================================================
part_page("PART 10", "자주 하는 오해 10가지", "잘못 알고 있으면 지레 포기하거나,<br/>반대로 안 되는 걸 시도하다 시간만 버리게 됩니다.")

def myth(wrong, right):
    story.append(Paragraph(f"✕ {wrong}", ParagraphStyle("mythwrong", fontName=FONT, fontSize=11.5, leading=17, textColor=colors.HexColor("#b3432f"), spaceBefore=10, spaceAfter=3)))
    story.append(Paragraph(f"✓ {right}", ParagraphStyle("mythright", fontName=FONT, fontSize=11.5, leading=17, textColor=colors.HexColor("#2f7a4f"), spaceAfter=2)))

myth("오해: 정부지원사업은 대기업이나 큰 회사만 받을 수 있다.", "진실: 오히려 대부분의 지원사업이 소상공인ㆍ중소기업ㆍ1인사업자를 대상으로 설계돼 있습니다. 대기업은 애초에 신청 자격이 안 되는 경우가 많습니다.")
myth("오해: 신용등급이 낮으면 아예 신청할 수 없다.", "진실: 보조금ㆍ지원금(갚지 않는 돈)은 대부분 신용등급을 보지 않습니다. 신용등급은 정책자금(융자, 빌리는 돈)에서만 심사 요소로 작동합니다.")
myth("오해: 한 번 떨어지면 그 사업은 다시 신청 못 한다.", "진실: 대부분 회차를 나눠 여러 번 모집합니다. 이번에 떨어져도 다음 회차에 재도전할 수 있는 경우가 많습니다(8부 FAQ 참고).")
myth("오해: 정부지원사업 신청에는 무조건 비용이 든다.", "진실: 신청 자체는 무료입니다. 다만 일부 서류(소상공인확인서 등) 발급에 시간이 걸리거나, 컨설팅 등 부가서비스는 유료일 수 있습니다.")
myth("오해: 사업자등록을 안 하면 아무 지원도 못 받는다.", "진실: 예비창업패키지처럼 사업자등록 전 예비창업자를 위한 사업도 많습니다. &ldquo;예비&rdquo;가 붙은 사업명을 찾아보세요.")
myth("오해: 지원사업은 전부 청년만 대상으로 한다.", "진실: 청년 전용 사업도 많지만, 연령 제한이 없는 일반 소상공인 대상 사업이 훨씬 많습니다. 4부 체크리스트로 본인에게 맞는 카테고리를 먼저 확인하세요.")
myth("오해: 정부지원금을 받으면 나라에서 계속 간섭한다.", "진실: 협약서에 명시된 용도로 정해진 기간에만 사용 내역을 보고(정산보고)하면 됩니다. 그 외에 경영에 간섭받는 일은 없습니다.")
myth("오해: 온라인 신청은 복잡해서 컴퓨터를 잘 알아야 한다.", "진실: 대부분 순서대로 안내가 나오는 양식 채우기 방식입니다. 막히면 콜센터(부록3)로 전화하면 안내받을 수 있습니다.")
myth("오해: 지자체 지원사업은 그 지역에 오래 산 사람만 받을 수 있다.", "진실: 사업자등록 소재지 기준인 경우가 대부분이라, 최근에 사업장을 연 경우에도 신청 가능한 경우가 많습니다. 거주 기간 요건은 공고문에서 개별 확인하세요.")
myth("오해: 지원사업에 붙으려면 화려한 스펙이 있어야 한다.", "진실: 5-3부에서 다뤘듯, 심사는 스펙보다 &ldquo;문제 인식이 명확한지&rdquo;, &ldquo;실현 가능한 계획인지&rdquo;를 더 중요하게 봅니다. 솔직하고 구체적인 계획서가 화려한 이력서보다 유리한 경우가 많습니다.")
myth("오해: 정부지원사업은 전부 서울ㆍ수도권에 몰려 있다.", "진실: 오히려 지자체 예산 사업(7ㆍ9장 참고)은 비수도권에 더 많은 경우가 있습니다. 지역 균형 관련 가산점 제도도 있어, 비수도권이 불리하기만 한 건 아닙니다.")
myth("오해: 한 번 신청서를 내면 절대 수정할 수 없다.", "진실: 접수 마감 전이라면 대부분 재제출ㆍ수정이 가능합니다. 제출 후에도 마감 전에 오류를 발견했다면 담당 부서에 문의해보세요.")

h1("헷갈리는 비슷한 단어 한눈에 비교")
compare_words = [
    [Paragraph("용어", styles["table_head"]), Paragraph("차이점", styles["table_head"])],
    [Paragraph("소상공인 vs 중소기업 vs 중견기업", styles["table_cell"]), Paragraph("규모 순서로 소상공인 < 중소기업 < 중견기업. 소상공인은 중소기업에 포함되는 더 작은 범주입니다.", styles["table_cell"])],
    [Paragraph("창업 vs 개업", styles["table_cell"]), Paragraph("창업은 새로운 사업을 시작하는 행위 전반, 개업은 그중 매장을 열고 영업을 시작하는 시점을 뜻합니다. 지원사업에서는 대부분 &ldquo;창업&rdquo; 개념(사업자등록 기준)을 씁니다.", styles["table_cell"])],
    [Paragraph("지원금 vs 보조금 vs 장려금", styles["table_cell"]), Paragraph("셋 다 갚지 않는 돈이라는 점은 같고, 사업 성격에 따라 이름만 다르게 쓰입니다(예: 고용 관련은 &ldquo;장려금&rdquo;이 흔함). 명칭보다 공고문의 실제 지원내용을 확인하는 게 정확합니다.", styles["table_cell"])],
    [Paragraph("공고 vs 모집공고 vs 시행공고", styles["table_cell"]), Paragraph("실무적으로 거의 같은 의미로 쓰입니다. 기관마다 부르는 이름이 다를 뿐, 전부 &ldquo;신청을 받는다&rdquo;는 뜻입니다.", styles["table_cell"])],
]
cmp_tbl = Table(compare_words, colWidths=[52 * mm, 114 * mm])
cmp_tbl.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#faf9ff")]),
    ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
    ("TOPPADDING", (0, 0), (-1, -1), 6),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
]))
story.append(cmp_tbl)
story.append(Spacer(1, 10))

h1("신청을 미루게 되는 이유, 그리고 극복하는 법")
body("여기까지 읽고도 막상 신청 버튼 앞에서 망설이는 경우가 많습니다. 흔한 이유와 실질적인 극복법을 정리했습니다.")
callout_box("자주 망설이는 이유와 해결책", [
    "&ldquo;내가 될까?&rdquo; 하는 불안 — 완벽한 조건을 갖춰야 붙는 게 아닙니다. 10부에서 다뤘듯 심사는 스펙보다 문제 인식과 실현 가능성을 봅니다. 일단 워크시트(12부)부터 채워보세요.",
    "서류가 너무 많아 보여서 시작을 못 함 — 부록1ㆍ워크시트4의 체크리스트를 인쇄해 하나씩 지워가며 준비하면 생각보다 오래 걸리지 않습니다.",
    "글쓰기가 막막함 — 백지에서 시작하지 말고 부록5의 표현 사전에서 비슷한 문장을 골라 내 상황으로 바꿔 쓰는 것부터 시작하세요.",
    "&ldquo;나중에 여유 있을 때&rdquo;로 미룸 — 9부 캘린더를 참고해 마감이 있는 사업부터 우선순위를 정하면 미루기가 훨씬 줄어듭니다.",
])
body("가장 중요한 건 완벽한 준비가 아니라 <b>첫 신청을 한 번 해보는 것</b>입니다. 떨어져도 8부 FAQ에서 다뤘듯 대부분 다음 회차가 있고, 그 경험이 다음 신청에 그대로 도움이 됩니다.")

# ============================================================
# 11부 — 담당자에게 전화할 때
# ============================================================
part_page("PART 11", "담당자에게 전화할 때 — 실전 통화 스크립트", "공고문만 읽고 애매하면 반드시 전화로 확인하세요.<br/>뭐라고 물어봐야 할지 그대로 따라 하면 됩니다.")

h1("왜 전화로 먼저 확인해야 하는가")
body("7부 체크리스트에서도 다뤘듯, 애매한 조건으로 무작정 신청했다가 서류 심사에서 탈락하는 것보다 신청 전에 전화로 확인하는 편이 훨씬 낫습니다. 담당 부서 전화번호는 공고문 하단에 반드시 적혀 있습니다.")

h1("상황별 통화 스크립트")
h2("① 자격 요건이 애매할 때")
quote("&ldquo;안녕하세요, [사업명] 공고 보고 연락드렸습니다. 제가 [본인 상황: 예. 사업자등록 6개월 차 개인사업자]인데, 이 사업에 신청 자격이 되는지 확인하고 싶어서요.&rdquo;")
h2("② 중복 지원 여부를 확인할 때")
quote("&ldquo;제가 올해 [다른 사업명] 지원사업을 이미 받았는데, 이번 [사업명]도 같이 신청할 수 있는지 궁금합니다.&rdquo;")
h2("③ 서류 요건을 확인할 때")
quote("&ldquo;공고문에 나온 서류 중에 [서류명]을 아직 준비 못 했는데, 마감일 전에 추가 제출도 가능한가요? 아니면 접수 시점에 전부 있어야 하나요?&rdquo;")
h2("④ 탈락 후 다음 기회를 물어볼 때")
quote("&ldquo;이번 회차에는 아쉽게 안 됐는데, 다음 회차 모집 일정이 정해져 있을까요? 어떤 점을 보완하면 좋을지도 혹시 안내해주실 수 있나요?&rdquo;")

callout_box("통화 전 준비하면 좋은 것", [
    "공고문 제목과 공고 번호(있는 경우) — 담당자가 바로 어떤 사업인지 확인할 수 있습니다.",
    "본인의 사업 현황 한 줄 요약 — 업종, 창업 시기, 상시근로자 수 정도만 있으면 충분합니다.",
    "궁금한 점을 미리 1~2개로 정리 — 통화 중 횡설수설하지 않도록 메모해두고 통화하세요.",
])

h1("전화가 어렵다면 — 이메일 문의 템플릿")
body("담당 부서가 전화 연결이 잘 안 되거나, 통화 내용을 기록으로 남기고 싶다면 이메일로 문의하는 것도 좋은 방법입니다. 공고문에 담당자 이메일이 함께 적혀 있는 경우가 많습니다.")
quote(
    "제목: [사업명] 신청 자격 문의드립니다<br/><br/>"
    "안녕하세요, [사업명] 공고를 보고 문의드립니다.<br/>"
    "저는 [업종]을 운영하는 [창업 시기] 사업자입니다.<br/>"
    "다음 사항이 궁금해 문의드립니다.<br/>"
    "1. [구체적 질문 1]<br/>"
    "2. [구체적 질문 2]<br/><br/>"
    "바쁘시겠지만 답변 부탁드립니다. 감사합니다."
)
body("이메일은 전화와 달리 기록이 남는다는 장점이 있습니다. 애매한 답변을 받았다면 답장을 보관해뒀다가 나중에 참고하세요.")

# ============================================================
# 12부 — 인쇄해서 쓰는 워크시트
# ============================================================
part_page("PART 12", "인쇄해서 쓰는 워크시트", "출력하거나 화면에 그대로 두고<br/>빈칸을 채우면서 정리해보세요.")


def blank_line_rows(n, height=8):
    return [[Paragraph("&nbsp;", styles["table_cell"])] for _ in range(n)]


def worksheet_table(rows, col_widths, row_height=9):
    t = Table(rows, colWidths=col_widths, rowHeights=[row_height * mm] * len(rows))
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.6, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t)


h1("워크시트 1. 나의 상황 정리표")
body("4부 체크리스트를 직접 손으로 채워보세요. 채운 답을 조합하면 그대로 검색 키워드가 됩니다.")
callout_box("① 사업 단계 (해당하는 것에 표시)", [
    "예비창업자 ／ 창업 1년 이내 ／ 창업 3년 이내 ／ 창업 3년 이상 ／ 폐업 후 재도전",
])
callout_box("② 필요한 목적 (해당하는 것에 표시, 복수 가능)", [
    "운영자금 ／ 시설ㆍ장비 ／ 온라인 진출 ／ 폐업ㆍ재창업 ／ 컨설팅ㆍ교육 ／ 갚지 않는 지원금",
])
callout_box("③ 나의 특성 (해당하는 것에 표시)", [
    "청년(만 39세 이하) ／ 여성 대표 ／ 비수도권 ／ 기술ㆍ제조 기반 ／ 장애인 ／ 경력단절 후 창업",
])
body("<b>내가 조합한 검색 키워드:</b>")
worksheet_table(blank_line_rows(2), [166 * mm])
story.append(Spacer(1, 10))

h1("워크시트 3. 사업계획서 초안 작성표")
body("5-3부의 5대 항목을 짧게라도 직접 써보세요. 완성된 문장이 아니어도 됩니다 — 초안이 있는 것과 없는 것의 차이가 큽니다.")
for label in ["① 일반현황(대표자ㆍ업종ㆍ사업 개요)", "② 창업동기 및 문제인식(구체적 근거 포함)", "③ 실현가능성(현재까지 준비된 것)", "④ 성장전략(지원금 사용 계획과 목표)", "⑤ 팀 구성 및 역량(부족한 부분과 보완 계획)"]:
    story.append(Paragraph(f"<b>{label}</b>", ParagraphStyle("wslabel", fontName=FONT, fontSize=11, leading=16, textColor=ACCENT, spaceBefore=10, spaceAfter=4)))
    worksheet_table(blank_line_rows(2), [166 * mm])

h1("워크시트 4. 서류 준비 체크리스트")
body("부록1의 서류 목록을 직접 체크하며 준비 상황을 관리하세요.")
callout_box("준비 상황 체크", [
    "사업자등록증명원",
    "주민등록등본",
    "통장 사본",
    "임대차계약서",
    "4대보험 가입내역",
    "소상공인확인서",
    "신용정보조회 동의서",
    "공동인증서 / 간편인증 준비 여부",
])

h1("워크시트 4-2. 나의 90일 실행 캘린더")
body("찾아보는 것부터 결과 확인까지, 3개월(12주) 단위로 나눠 계획을 세워보세요. 주차별로 할 일을 적고 체크하면서 진행하면 흐지부지되지 않습니다.")

weeks_plan = [
    ("1주차", "4부 워크시트로 내 상황(사업단계/목적/특성) 정리"),
    ("2주차", "기업마당ㆍ2부 사이트에서 1차 검색, 후보 공고 5개 이상 스크랩"),
    ("3주차", "후보 공고별 신청 자격ㆍ마감일 비교, 우선순위 3개로 압축"),
    ("4주차", "부록1 서류 목록 확인 후 발급에 오래 걸리는 서류부터 신청"),
    ("5주차", "애매한 조건 담당 부서에 전화ㆍ이메일로 확인(11부 스크립트 활용)"),
    ("6주차", "워크시트3으로 사업계획서 초안(5개 항목) 작성"),
    ("7주차", "작성한 초안을 주변 사람에게 보여주고 피드백 받기"),
    ("8주차", "피드백 반영해 사업계획서 수정, 자가진단 20문항(워크시트5) 점검"),
    ("9주차", "1순위 공고 최종 제출(마감 2~3일 전 완료 목표)"),
    ("10주차", "2ㆍ3순위 공고 순차 제출"),
    ("11주차", "발표평가 대상이라면 5-3부 팁으로 준비ㆍ리허설"),
    ("12주차", "결과 확인, 탈락 시 사유 문의 후 다음 회차 재도전 계획 수립"),
]
weeks_rows = [[Paragraph(f"<b>{w}</b>", styles["table_cell"]), Paragraph(t, styles["table_cell"]), Paragraph("☐", styles["table_cell"])] for w, t in weeks_plan]
weeks_tbl = Table(weeks_rows, colWidths=[20 * mm, 130 * mm, 16 * mm])
weeks_tbl.setStyle(TableStyle([
    ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
    ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#faf9ff")]),
    ("TOPPADDING", (0, 0), (-1, -1), 6),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
]))
story.append(weeks_tbl)
story.append(Spacer(1, 10))
quote("12주는 권장 속도일 뿐입니다. 더 빠르게 가도 되고, 상황에 맞게 늘려도 됩니다 — 중요한 건 완벽한 일정이 아니라 &ldquo;멈추지 않는 것&rdquo;입니다.")

h1("워크시트 5. 신청 전 자가진단 20문항")
body("신청 버튼을 누르기 전에 아래 20개 문항에 &ldquo;예/아니오&rdquo;로 답해보세요. &ldquo;아니오&rdquo;가 하나라도 있으면 제출 전에 그 항목부터 다시 점검하세요.")
diag_items = [
    "① 이 사업의 신청 자격(소상공인/중소기업 기준)에 내가 해당하는지 확인했다",
    "② 창업 시기(예비/1년/3년 등) 기준에 내가 해당하는지 확인했다",
    "③ 지원 제외 업종에 내 업종이 포함되지 않는지 확인했다",
    "④ 다른 지원사업과 중복 수혜 제한에 걸리지 않는지 확인했다",
    "⑤ 이 지원이 융자(빚)인지 보조금(무상)인지 정확히 구분했다",
    "⑥ 자기부담금(매칭펀드)이 있다면 그 금액을 준비할 수 있다",
    "⑦ 공고문에 첨부된 사업계획서 양식을 내려받아 확인했다",
    "⑧ 배점표(심사 기준)를 확인하고 어디에 힘을 줘야 할지 파악했다",
    "⑨ 필요 서류 목록을 전부 확인하고 준비를 시작했다",
    "⑩ 발급까지 며칠 걸리는 서류(소상공인확인서 등)를 미리 신청했다",
    "⑪ 공동인증서 또는 간편인증 수단을 준비해뒀다",
    "⑫ 사업자등록증의 상호명ㆍ업종코드가 계획서 내용과 일치한다",
    "⑬ 창업동기ㆍ문제인식에 구체적 근거(숫자ㆍ사례)를 넣었다",
    "⑭ 성장전략에 지원금 사용 계획을 구체적으로 연결했다",
    "⑮ 글자수ㆍ페이지 제한 등 양식 요건을 지켰다",
    "⑯ 마감일보다 최소 2~3일 여유를 두고 제출할 계획이다",
    "⑰ 애매한 조건은 담당 부서에 전화로 확인했다(11부 스크립트 참고)",
    "⑱ 선정 이후 정산보고ㆍ협약 의무사항을 미리 읽어봤다",
    "⑲ 제출 직전 오탈자ㆍ서류 누락을 한 번 더 검토했다",
    "⑳ 시스템 오류 대비용으로 제출 화면을 캡처해둘 계획이다",
]
diag_rows = [[Paragraph(item, styles["table_cell"]), Paragraph("예 ／ 아니오", styles["table_cell"])] for item in diag_items]
diag_tbl = Table(diag_rows, colWidths=[136 * mm, 30 * mm])
diag_tbl.setStyle(TableStyle([
    ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
    ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#faf9ff")]),
    ("TOPPADDING", (0, 0), (-1, -1), 5),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
]))
story.append(diag_tbl)

h1("정책자금(융자) 실제 금리ㆍ한도 총정리")
body("2부에서 소진공 정책자금을 &ldquo;융자&rdquo;라고만 짧게 다뤘는데, 실제로 어떤 자금이 있고 금리ㆍ한도가 얼마인지 궁금한 분들을 위해 2026년 기준 실측 수치로 정리했습니다.")
callout_box("2026년 1월 기준 정책자금 금리", [
    "전체 평균 금리는 연 2.96% 수준 — 자금 유형에 따라 2%대~4%대까지 차등 적용됩니다.",
    "비수도권 사업자는 0.2%포인트 우대금리를 추가로 받습니다.",
    "스마트소상공인자금은 연 1~2%대로 가장 낮은 금리 구간에 속합니다.",
])
fund_header = [Paragraph("자금 종류", styles["table_head"]), Paragraph("대출 한도", styles["table_head"]),
               Paragraph("특징", styles["table_head"])]
fund_rows = [fund_header] + [
    [Paragraph("일반ㆍ특별 경영안정자금", styles["table_cell"]), Paragraph("최대 7천만원", styles["table_cell"]), Paragraph("가장 기본적인 운영자금 대출", styles["table_cell"])],
    [Paragraph("재도전 특별자금", styles["table_cell"]), Paragraph("최대 2억원(유형별 상이)", styles["table_cell"]), Paragraph("폐업 후 재창업자 대상", styles["table_cell"])],
    [Paragraph("성장기반자금", styles["table_cell"]), Paragraph("최대 5억원", styles["table_cell"]), Paragraph("일정 매출ㆍ고용 규모 이상 성장 단계 기업", styles["table_cell"])],
    [Paragraph("스마트소상공인자금", styles["table_cell"]), Paragraph("자금별 상이", styles["table_cell"]), Paragraph("금리 연 1~2%대로 가장 낮음", styles["table_cell"])],
]
fund_tbl = Table(fund_rows, colWidths=[50 * mm, 42 * mm, 74 * mm])
fund_tbl.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
    ("GRID", (0, 0), (-1, -1), 0.6, BORDER),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#faf9ff")]),
    ("TOPPADDING", (0, 0), (-1, -1), 6),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
]))
story.append(fund_tbl)
story.append(Spacer(1, 10))
callout_box("신청 경로 주의", [
    "정책자금은 &ldquo;소상공인정책자금 공식 사이트(ols.semas.or.kr)&rdquo; 또는 전국 78곳 소진공 지역센터에서만 신청할 수 있습니다.",
    "사설 대출중개업체가 &ldquo;정책자금 대행&rdquo;을 내세우며 수수료를 요구하면 사기일 가능성이 높으니 주의하세요.",
])

h1("청년 창업 3대 대표 프로그램 비교")
body("&ldquo;예비창업패키지ㆍ초기창업패키지ㆍ청년창업사관학교&rdquo;는 이름이 비슷해 헷갈리기 쉬운 대표적인 청년 창업 지원 프로그램입니다. 셋 다 상환 의무가 없는 사업화 자금이며, K-Startup 창업지원포털에서 온라인으로 신청합니다.")
youth_header = [Paragraph("프로그램", styles["table_head"]), Paragraph("대상", styles["table_head"]),
                Paragraph("지원 규모", styles["table_head"])]
youth_rows = [youth_header] + [
    [Paragraph("예비창업패키지", styles["table_cell"]), Paragraph("사업자등록 전 예비창업자", styles["table_cell"]), Paragraph("최대 1억원", styles["table_cell"])],
    [Paragraph("초기창업패키지", styles["table_cell"]), Paragraph("업력 3년 이내 기업 대표", styles["table_cell"]), Paragraph("최대 1억원", styles["table_cell"])],
    [Paragraph("청년창업사관학교", styles["table_cell"]), Paragraph("만 39세 이하, 창업 3년 이내", styles["table_cell"]), Paragraph("최대 1억원(총사업비의 70% 이내) + 창업공간ㆍ코칭", styles["table_cell"])],
]
youth_tbl = Table(youth_rows, colWidths=[46 * mm, 60 * mm, 60 * mm])
youth_tbl.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
    ("GRID", (0, 0), (-1, -1), 0.6, BORDER),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#faf9ff")]),
    ("TOPPADDING", (0, 0), (-1, -1), 6),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
]))
story.append(youth_tbl)
story.append(Spacer(1, 10))
body("청년창업사관학교는 매년 <b>글로벌형ㆍ지역특화형ㆍ투자형</b> 세 갈래로 나눠 총 850명 안팎을 선발하며, <b>공고(1월) → 신청ㆍ접수(1~2월) → 평가ㆍ발표(2~3월) → 프로그램 진행(3월~)</b> 순서로 진행됩니다. 예비창업패키지ㆍ초기창업패키지보다 창업 공간ㆍ코칭ㆍ기술지원까지 포함된 밀착형 프로그램이라는 점이 가장 큰 차이입니다.")
callout_box("정책자금ㆍ청년 프로그램 핵심 요약", [
    "정책자금은 자금 유형별로 금리 2~4%대, 한도 7천만원~5억원까지 천차만별 — 본인 상황에 맞는 유형부터 확인",
    "예비ㆍ초기창업패키지는 사업화 자금 중심, 청년창업사관학교는 공간ㆍ코칭까지 포함된 밀착형",
])

h1("폐업을 고민 중이라면 — 희망리턴패키지 실측 정리")
body("이 가이드의 독자 중에는 새로 시작하려는 분뿐 아니라 <b>폐업을 고민 중이거나 이미 폐업한 뒤 재도전을 준비하는 분</b>도 있습니다. &ldquo;희망리턴패키지&rdquo;는 이런 분들을 위한 대표적인 정부지원사업입니다.")
callout_box("지원 내용과 금액", [
    "점포 철거비 — 전용면적 3.3㎡당 13만원 이내, 업체당 최대 600만원",
    "사업정리 컨설팅ㆍ법률자문ㆍ채무조정도 함께 신청 가능한 4가지 항목",
    "자가 건물이 아니라 임대차 계약으로 운영 중인 사업장이 대상(자가 건물은 철거비 제외)",
])
body("신청은 공식 홈페이지(<b>www.sbiz.or.kr</b>)에서 상시 접수하며, 2026년부터 공공 마이데이터 서비스가 연동되어 제출 서류가 예전보다 대폭 간소화됐습니다.")
h2("정리가 끝난 뒤에는 &lsquo;재도전성공패키지&rsquo;")
body("폐업 정리를 마치고 다시 도전할 준비가 됐다면, 중소벤처기업부의 <b>재도전성공패키지</b>가 정확히 이 시점을 위한 사업입니다. 폐업 이력이 있는 예비재창업자 또는 <b>7년 이내 재창업기업</b>을 대상으로, 사업화 자금(최대 1억원, 평균 6,700만원)에 더해 심리치유ㆍ실패원인분석ㆍ맞춤형 멘토링ㆍ투자연계까지 패키지로 지원합니다.")
callout_box("재도전성공패키지 핵심 정보", [
    "대상 — 폐업 이력 보유 예비재창업자, 또는 7년 이내 재창업기업",
    "지원 규모 — 사업화자금 최대 1억원(평균 6,700만원) + 심리치유ㆍ실패원인분석ㆍ멘토링",
    "신청 경로 — K-Startup 창업지원포털(k-startup.go.kr), 일반 모집은 보통 2~3월 접수",
])
body("즉 <b>희망리턴패키지(정리) → 재도전성공패키지(재창업)</b>로 이어지는 흐름이 폐업 이후 재도전을 준비하는 가장 현실적인 순서입니다.")

# ============================================================
# 마무리 + 부록
# ============================================================
h1("마무리 — 이 가이드를 어떻게 쓰면 좋을까")
callout_box("4단계로 활용하세요", [
    "1부의 5분 컷 체크리스트로 내 상황을 먼저 정리하고, 기업마당에서 바로 검색해보세요.",
    "결과가 부족하면 2부에서 목적에 맞는 사이트(정책자금은 소진공, 지역 사업은 지자체 홈페이지 등)를 추가로 확인하세요.",
    "공고문 용어가 헷갈리면 3부 용어 사전을 참고하세요.",
    "마음에 드는 공고를 찾으면 7부 체크리스트로 신청 전 준비를 점검하세요.",
], numbered=True)
body("정부지원사업 정보는 계속 바뀝니다. 이 가이드는 &ldquo;어디서, 어떻게 찾는지&rdquo;의 틀을 알려드리는 것이고, 최신 금액ㆍ마감일ㆍ자격 조건은 항상 해당 공식 사이트에서 본인이 직접 최종 확인해야 합니다.")
body("검색 한 번으로 끝나는 일이 아닙니다. 이 가이드에서 다룬 순서 — 상황 정리(4부) → 검색(1ㆍ2부) → 서류 준비(부록1) → 계획서 작성(5-3부) → 신청(7부) → 협약ㆍ정산(9-2부) — 를 한 사이클로 여러 번 반복하다 보면, 처음엔 낯설던 과정이 점점 손에 익을 것입니다.")

h1("부록 1. 신청 서류 준비 가이드")
body("지원사업마다 요구 서류는 다르지만, 아래 서류들은 대부분의 신청에 공통으로 필요합니다. 미리 발급받아 폴더 하나에 모아두면 마감 임박 시 훨씬 여유가 생깁니다.")

doc_table_data = [
    [Paragraph("서류명", styles["table_head"]), Paragraph("발급처", styles["table_head"]), Paragraph("비고", styles["table_head"])],
    [Paragraph("사업자등록증명원", styles["table_cell"]), Paragraph("정부24 (온라인 무료)", styles["table_cell"]), Paragraph("즉시 발급 가능", styles["table_cell"])],
    [Paragraph("주민등록등본", styles["table_cell"]), Paragraph("정부24 (온라인 무료)", styles["table_cell"]), Paragraph("즉시 발급 가능", styles["table_cell"])],
    [Paragraph("통장 사본", styles["table_cell"]), Paragraph("은행 앱 캡처 또는 인터넷뱅킹", styles["table_cell"]), Paragraph("사업용 계좌 권장", styles["table_cell"])],
    [Paragraph("임대차계약서", styles["table_cell"]), Paragraph("본인 보관분", styles["table_cell"]), Paragraph("사업장 주소 일치 확인", styles["table_cell"])],
    [Paragraph("4대보험 가입내역", styles["table_cell"]), Paragraph("4대사회보험 정보연계센터", styles["table_cell"]), Paragraph("상시근로자 수 증빙용", styles["table_cell"])],
    [Paragraph("소상공인확인서", styles["table_cell"]), Paragraph("소상공인24", styles["table_cell"]), Paragraph("발급까지 수일 소요 가능", styles["table_cell"])],
    [Paragraph("신용정보조회 동의서", styles["table_cell"]), Paragraph("각 사업 신청 시스템 내 서식", styles["table_cell"]), Paragraph("정책자금(융자) 신청 시 필수", styles["table_cell"])],
]
dtbl = Table(doc_table_data, colWidths=[46 * mm, 62 * mm, 58 * mm])
dtbl.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#faf9ff")]),
    ("GRID", (0, 0), (-1, -1), 0.6, BORDER),
    ("TOPPADDING", (0, 0), (-1, -1), 7),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ("LEFTPADDING", (0, 0), (-1, -1), 9),
    ("RIGHTPADDING", (0, 0), (-1, -1), 9),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
]))
story.append(dtbl)
story.append(Spacer(1, 10))
quote("소상공인확인서ㆍ신용정보조회 동의서처럼 발급에 며칠씩 걸리는 서류가 있습니다. 마음에 드는 공고를 발견했다면, 서류부터 먼저 신청해두고 사업계획서를 쓰는 순서를 추천합니다.")

h1("서류별 발급 소요 기간 한눈에 보기")
docs_time = [
    ("사업자등록증명원", 0.5, colors.HexColor("#5a3fd6")),
    ("주민등록등본", 0.5, colors.HexColor("#5a3fd6")),
    ("통장 사본", 0.5, colors.HexColor("#5a3fd6")),
    ("임대차계약서", 1, colors.HexColor("#8d6fea")),
    ("4대보험 가입내역", 1, colors.HexColor("#8d6fea")),
    ("신용정보조회 동의서", 1, colors.HexColor("#8d6fea")),
    ("소상공인확인서", 4, colors.HexColor("#bfa0f7")),
]
for label, days, color in docs_time:
    bar_row(label, days, 4, color, unit="일")
story.append(Spacer(1, 4))
body("<i>(막대 길이는 &ldquo;즉시 발급&rdquo;을 0.5, &ldquo;최대 며칠 소요&rdquo;를 4로 상대 비교한 것입니다. 실제 소요일은 신청 시기ㆍ기관 사정에 따라 달라질 수 있습니다.)</i>")

h2("헷갈리기 쉬운 서류 자세히 보기")
body("<b>소상공인확인서</b>: 소상공인24에서 신청하면 국세청ㆍ중소벤처기업부 자료를 조회해 자동으로 소상공인 해당 여부를 판정해줍니다. 자동 판정이 안 되는 경우 서류를 직접 제출해야 할 수 있어, 발급까지 수일이 걸릴 수 있습니다.")
body("<b>신용정보조회 동의서</b>: 정책자금(융자) 신청 시 본인의 신용도를 조회하는 데 동의하는 서류입니다. 대부분 온라인 신청 시스템 안에서 전자 서명으로 바로 처리되지만, 일부 사업은 별도 양식을 요구하기도 합니다.")
body("<b>임대차계약서</b>: 사업장 주소와 계약서상 주소가 정확히 일치해야 합니다. 확정일자를 받아둔 계약서라면 그 사본도 함께 준비해두면 좋습니다.")


h1("부록 2. 사이트 주소 모음")

table_data = [
    [Paragraph("사이트", styles["table_head"]), Paragraph("주소", styles["table_head"]), Paragraph("핵심 용도", styles["table_head"])],
    [Paragraph("기업마당", styles["table_cell"]), Paragraph("bizinfo.go.kr", styles["table_cell"]), Paragraph("가장 먼저 볼 통합 공고 사이트", styles["table_cell"])],
    [Paragraph("소상공인24", styles["table_cell"]), Paragraph("sbiz24.kr", styles["table_cell"]), Paragraph("소상공인 전용 지원ㆍ바우처 신청", styles["table_cell"])],
    [Paragraph("중소벤처24", styles["table_cell"]), Paragraph("smes.go.kr", styles["table_cell"]), Paragraph("중소기업ㆍ스타트업 맞춤 추천", styles["table_cell"])],
    [Paragraph("소상공인시장진흥공단", styles["table_cell"]), Paragraph("semas.or.kr", styles["table_cell"]), Paragraph("정책자금(융자), 교육, 상권정보", styles["table_cell"])],
    [Paragraph("정부24", styles["table_cell"]), Paragraph("gov.kr / plus.gov.kr", styles["table_cell"]), Paragraph("보조금24 — 개인 맞춤 보조금 조회", styles["table_cell"])],
    [Paragraph("거주 지역 시ㆍ군ㆍ구청", styles["table_cell"]), Paragraph("(지역마다 다름)", styles["table_cell"]), Paragraph("지자체 전용 지원사업, 고시공고", styles["table_cell"])],
]
tbl = Table(table_data, colWidths=[42 * mm, 46 * mm, 78 * mm])
tbl.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
    ("BACKGROUND", (0, 1), (-1, -1), colors.white),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#faf9ff")]),
    ("GRID", (0, 0), (-1, -1), 0.6, BORDER),
    ("TOPPADDING", (0, 0), (-1, -1), 7),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ("LEFTPADDING", (0, 0), (-1, -1), 9),
    ("RIGHTPADDING", (0, 0), (-1, -1), 9),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
]))
story.append(tbl)

story.append(Spacer(1, 16))
h1("부록 3. 문의 연락처 모음")
contact_data = [
    [Paragraph("기관", styles["table_head"]), Paragraph("전화", styles["table_head"]), Paragraph("용도", styles["table_head"])],
    [Paragraph("중소기업통합콜센터", styles["table_cell"]), Paragraph("1357", styles["table_cell"]), Paragraph("중소기업ㆍ소상공인 지원사업 전반 문의", styles["table_cell"])],
    [Paragraph("소진공 콜센터", styles["table_cell"]), Paragraph("1533-0100", styles["table_cell"]), Paragraph("정책자금(융자), 소상공인24 문의", styles["table_cell"])],
    [Paragraph("정부24 콜센터", styles["table_cell"]), Paragraph("110", styles["table_cell"]), Paragraph("정부24ㆍ보조금24 이용 문의", styles["table_cell"])],
    [Paragraph("국번 없이 지자체 대표번호", styles["table_cell"]), Paragraph("지역마다 상이", styles["table_cell"]), Paragraph("지자체 전용 지원사업 문의", styles["table_cell"])],
]
ctbl = Table(contact_data, colWidths=[52 * mm, 38 * mm, 76 * mm])
ctbl.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#faf9ff")]),
    ("GRID", (0, 0), (-1, -1), 0.6, BORDER),
    ("TOPPADDING", (0, 0), (-1, -1), 7),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ("LEFTPADDING", (0, 0), (-1, -1), 9),
    ("RIGHTPADDING", (0, 0), (-1, -1), 9),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
]))
story.append(ctbl)

h1("부록 4. 체크리스트 총모음")
body("책 전체에 흩어진 체크리스트를 한곳에 모았습니다. 신청 직전에 이 페이지만 다시 훑어봐도 충분합니다.")

callout_box("찾기 전 — 내 상황 확인 (4부)", [
    "사업 단계(예비/1년/3년/재도약/재도전)를 확인했다",
    "필요한 목적(운영자금/시설/온라인/재창업/컨설팅)을 확인했다",
    "나의 특성(청년/여성/비수도권/기술기반/장애인/경력단절)을 확인했다",
])
callout_box("신청 전 — 최종 점검 (7부)", [
    "모집공고를 끝까지 읽었다",
    "마감일보다 2~3일 여유를 뒀다",
    "사업계획서를 성의 있게 썼다",
    "증빙서류를 빠짐없이 준비했다",
    "자격 요건과 중복 지원 제한을 확인했다",
    "애매한 조건은 담당 부서에 문의했다",
    "인증서ㆍ계정을 미리 준비했다",
])
callout_box("선정 이후 — 잊지 말아야 할 것", [
    "협약서의 자금 집행 기한을 캘린더에 표시했다",
    "정산보고 시점과 필요 증빙자료를 확인했다",
    "지원금 용도 제한 범위를 정확히 이해했다",
])

h1("부록 5. 사업계획서 표현 사전")
body("무슨 말로 시작해야 할지 막막할 때 참고하는 표현 모음입니다. 그대로 쓰기보다, 본인 상황에 맞는 숫자와 사실로 바꿔서 활용하세요.")

def phrase(category, examples):
    story.append(Paragraph(f"<b>{category}</b>", ParagraphStyle("phrasecat", fontName=FONT, fontSize=11.5, leading=17, textColor=ACCENT, spaceBefore=10, spaceAfter=3)))
    for ex in examples:
        story.append(Paragraph(f"ㆍ {ex}", styles["list"]))

phrase("문제 상황을 설명할 때", [
    "&ldquo;[대상] OO명을 대상으로 [방법]한 결과, [비율/숫자]가 [문제]를 겪고 있음을 확인했습니다.&rdquo;",
    "&ldquo;기존 [경쟁 서비스/제품]은 [한계]라는 공통된 아쉬움이 있었습니다.&rdquo;",
])
phrase("차별점을 설명할 때", [
    "&ldquo;기존 방식과 달리, 저희는 [구체적 방법]으로 이 문제를 해결합니다.&rdquo;",
    "&ldquo;[직접 조사/경험]을 통해 확인한 니즈를 반영해 [차별 요소]를 갖췄습니다.&rdquo;",
])
phrase("실현 가능성을 설명할 때", [
    "&ldquo;현재까지 [완료한 것: 시제품/테스트 판매/예약 문의 등]을 통해 실현 가능성을 확인했습니다.&rdquo;",
    "&ldquo;[기간] 안에 [단계별 계획]을 순차적으로 진행할 예정입니다.&rdquo;",
])
phrase("성장 전략을 설명할 때", [
    "&ldquo;지원금 [금액]을 [항목]에 사용해, [기간] 내 [구체적 목표: 매출/고객 수/고용]를 달성하겠습니다.&rdquo;",
    "&ldquo;1단계로 [목표], 2단계로 [목표]를 순차적으로 달성할 계획입니다.&rdquo;",
])
phrase("팀 역량을 설명할 때", [
    "&ldquo;[본인 경력/경험]을 바탕으로 [역할]을 직접 수행하며, 부족한 [분야]는 [외주/협력업체]로 보완합니다.&rdquo;",
    "&ldquo;[관련 경험 기간]의 실무 경험을 통해 [강점]을 갖췄습니다.&rdquo;",
])

h1("부록 6. 카테고리별 대표 사업 계열 한눈에")
body("5-2부에서 다룬 유형들을 검색용으로 빠르게 찾아볼 수 있도록 표 하나로 정리했습니다. 정확한 사업명과 조건은 시기마다 바뀌므로 반드시 공식 사이트에서 최종 확인하세요.")

master_table = [
    [Paragraph("카테고리", styles["table_head"]), Paragraph("검색 키워드 예시", styles["table_head"]), Paragraph("주로 확인할 사이트", styles["table_head"])],
    [Paragraph("창업 초기 자금", styles["table_cell"]), Paragraph("예비창업패키지, 초기창업패키지", styles["table_cell"]), Paragraph("기업마당, 중소벤처24", styles["table_cell"])],
    [Paragraph("성장기 자금", styles["table_cell"]), Paragraph("창업도약패키지, 성장기반자금", styles["table_cell"]), Paragraph("기업마당, 중소벤처24", styles["table_cell"])],
    [Paragraph("운영자금(융자)", styles["table_cell"]), Paragraph("소상공인 정책자금, 경영안정자금", styles["table_cell"]), Paragraph("소진공", styles["table_cell"])],
    [Paragraph("재도전/재도약", styles["table_cell"]), Paragraph("희망리턴패키지, 재도전 특별자금", styles["table_cell"]), Paragraph("소진공, 기업마당", styles["table_cell"])],
    [Paragraph("온라인 판로", styles["table_cell"]), Paragraph("온라인 판로지원, 스마트스토어 지원", styles["table_cell"]), Paragraph("기업마당", styles["table_cell"])],
    [Paragraph("디지털 전환", styles["table_cell"]), Paragraph("스마트상점, 스마트공장, AI 도입지원", styles["table_cell"]), Paragraph("기업마당, 중소벤처24", styles["table_cell"])],
    [Paragraph("수출", styles["table_cell"]), Paragraph("해외전시회 지원, 수출바우처", styles["table_cell"]), Paragraph("기업마당(수출 분야 필터)", styles["table_cell"])],
    [Paragraph("인증 취득", styles["table_cell"]), Paragraph("HACCP, ISO 인증 지원", styles["table_cell"]), Paragraph("기업마당(품목별 인증제도)", styles["table_cell"])],
    [Paragraph("고용", styles["table_cell"]), Paragraph("고용창출장려금, 두루누리 사회보험료", styles["table_cell"]), Paragraph("고용노동부, 근로복지공단", styles["table_cell"])],
    [Paragraph("R&amp;D", styles["table_cell"]), Paragraph("중소기업 기술개발 지원사업", styles["table_cell"]), Paragraph("중소벤처24, TIPA", styles["table_cell"])],
    [Paragraph("여성기업", styles["table_cell"]), Paragraph("여성기업 확인, 여성기업 전용자금", styles["table_cell"]), Paragraph("여성기업종합지원센터", styles["table_cell"])],
    [Paragraph("장애인기업", styles["table_cell"]), Paragraph("장애인기업 창업자금", styles["table_cell"]), Paragraph("장애인기업종합지원센터", styles["table_cell"])],
    [Paragraph("교육ㆍ컨설팅", styles["table_cell"]), Paragraph("소상공인 아카데미, 경영컨설팅", styles["table_cell"]), Paragraph("소진공 지식배움터", styles["table_cell"])],
    [Paragraph("보조금(개인 맞춤)", styles["table_cell"]), Paragraph("보조금24 맞춤 조회", styles["table_cell"]), Paragraph("정부24", styles["table_cell"])],
    [Paragraph("특화 소상공인 인증", styles["table_cell"]), Paragraph("백년가게, 백년소공인", styles["table_cell"]), Paragraph("소진공", styles["table_cell"])],
    [Paragraph("창업 경진대회", styles["table_cell"]), Paragraph("창업경진대회, 데모데이", styles["table_cell"]), Paragraph("기업마당, 중소벤처24", styles["table_cell"])],
    [Paragraph("지식재산권", styles["table_cell"]), Paragraph("특허 출원 지원, IP 사업화", styles["table_cell"]), Paragraph("특허청, 발명진흥회", styles["table_cell"])],
    [Paragraph("경영개선 컨설팅", styles["table_cell"]), Paragraph("소상공인 경영개선컨설팅", styles["table_cell"]), Paragraph("소진공 지식배움터", styles["table_cell"])],
    [Paragraph("공공조달 진입", styles["table_cell"]), Paragraph("나라장터 등록 지원", styles["table_cell"]), Paragraph("조달청, 여성기업종합지원센터", styles["table_cell"])],
]
master_tbl = Table(master_table, colWidths=[36 * mm, 76 * mm, 54 * mm])
master_tbl.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#faf9ff")]),
    ("GRID", (0, 0), (-1, -1), 0.6, BORDER),
    ("TOPPADDING", (0, 0), (-1, -1), 6),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
]))
story.append(master_tbl)

h1("부록 7. 자주 나오는 기관 소개")
body("공고문에 자주 등장하는 소관부처ㆍ수행기관이 정확히 어떤 곳인지 모르면 낯설게 느껴질 수 있습니다. 짧게 정리했습니다.")

def org(name, desc):
    story.append(Paragraph(f"<b>{name}</b>", ParagraphStyle("orgname", fontName=FONT, fontSize=11.5, leading=17, textColor=ACCENT, spaceBefore=9, spaceAfter=3)))
    body(desc)

org("중소벤처기업부", "중소기업ㆍ소상공인ㆍ벤처기업 정책을 총괄하는 중앙부처입니다. 기업마당, 중소벤처24 등 여러 사이트의 상위 주무부처입니다.")
org("창업진흥원", "중소벤처기업부 산하 기관으로, 예비창업패키지ㆍ초기창업패키지 등 창업 단계별 지원사업을 직접 운영합니다.")
org("소상공인시장진흥공단(소진공)", "소상공인 정책자금(융자), 교육, 상권정보 등을 전담하는 공공기관입니다. 5장에서 자세히 다뤘습니다.")
org("중소기업기술정보진흥원(TIPA)", "중소기업의 기술개발(R&amp;D) 지원사업을 전담하는 기관입니다.")
org("고용노동부", "고용창출장려금, 일자리 안정자금 등 고용 관련 지원사업을 운영합니다.")
org("특허청", "특허ㆍ상표ㆍ디자인 등 지식재산권 관련 지원사업과 등록 절차를 관장합니다.")
org("조달청", "정부ㆍ공공기관의 물품ㆍ용역 구매(공공조달)를 담당하며, 나라장터를 운영합니다.")
org("코트라(KOTRA)", "해외 진출ㆍ수출 지원을 전담하는 공공기관으로, 해외 전시회 참가 지원 등을 운영합니다.")
org("여성기업종합지원센터", "여성기업확인서 발급과 여성기업 전용 지원사업을 담당합니다.")
org("장애인기업종합지원센터", "장애인기업 확인과 관련 지원사업을 담당합니다.")
org("여성새로일하기센터", "경력단절여성의 취업ㆍ창업을 지원하는 여성가족부 산하 기관입니다. 경력단절 후 창업을 준비 중이라면 4부 축3 체크리스트와 함께 확인해보세요.")
org("근로복지공단", "4대보험 중 산재보험ㆍ고용보험 관련 업무를 담당하며, 일자리 안정자금 등 고용 관련 지원사업의 실무 창구 역할을 합니다.")
org("신용보증재단(지역별)", "담보력이 부족한 소상공인에게 보증서를 발급해 대출을 받을 수 있도록 돕는 지역별 공공기관입니다. 정책자금 신청 시 함께 언급되는 경우가 많습니다.")
org("한국콘텐츠진흥원", "문화콘텐츠(영상, 게임, 캐릭터 등) 분야 사업자를 위한 지원사업을 전담하는 기관입니다.")
org("농림축산식품부 / 농촌진흥청", "농업ㆍ식품 관련 창업과 지원사업을 담당합니다. 농산물 가공, 6차산업화(생산+가공+체험 융합) 관련 지원사업이 대표적입니다.")
org("해양수산부", "수산업ㆍ해운ㆍ항만 관련 창업과 지원사업을 담당합니다. 부산 등 해양 인접 지역 사업자라면 참고할 만합니다(9장 지역별 살펴보기 참고).")
org("중소기업중앙회", "중소기업ㆍ소상공인 단체를 대표하는 기관으로, 공제사업(노란우산공제 등)과 각종 정책 건의 창구 역할을 합니다.")
org("신용보증기금", "중견ㆍ중소기업을 위한 신용보증을 전담하는 기관으로, 지역 신용보증재단과 역할이 유사하지만 대상 규모가 조금 더 큰 기업까지 포괄합니다.")

h1("기관 관계도로 한눈에 보기")
body("여러 기관이 등장해 헷갈릴 수 있어, 소상공인 입장에서 가장 자주 접하는 순서대로 관계를 정리했습니다.")
flow_diagram(["중소벤처기업부", "산하 실행기관", "지역 창구", "나(신청자)"])
story.append(Spacer(1, 6))
body("<b>중소벤처기업부</b>가 정책을 정하면, <b>창업진흥원ㆍ소진공ㆍTIPA</b> 같은 산하 실행기관이 실제 사업을 운영하고, <b>지역 신용보증재단ㆍ지자체</b> 등 지역 창구가 현장 접점 역할을 하며, 최종적으로 <b>신청자</b>가 이 창구들을 통해 지원을 받는 구조입니다. 어느 기관에 연락해야 할지 헷갈리면 이 순서를 떠올려보세요 — 정책 방향이 궁금하면 부처, 실제 신청 방법이 궁금하면 실행기관, 현장 상담이 필요하면 지역 창구입니다.")

# ============================================================
# 부록 8 — 찾아보기(색인)
# ============================================================
h1("부록 8. 찾아보기(색인)")
body("본문에 나온 주요 용어와 사업명이 어느 부에 나오는지 빠르게 찾아보는 색인입니다.")

index_entries = [
    ("간편인증", "2부 3장, 3부 용어사전"),
    ("공고문 읽는 법", "9-3부"),
    ("공동인증서", "2부 3장, 3부 용어사전"),
    ("공공조달", "3부 용어사전, 부록6"),
    ("기업마당", "1부 1장, 2부"),
    ("나라장터", "3부 용어사전"),
    ("매칭펀드(자기부담금)", "3부 용어사전"),
    ("보조금24", "2부 6장"),
    ("사업계획서 작성법", "5-3부"),
    ("사업계획서 표현 사전", "부록5"),
    ("소상공인24", "2부 3장"),
    ("소진공(정책자금)", "2부 5장"),
    ("실전 사례(A~F씨)", "5부"),
    ("업종별 예문", "5-3부"),
    ("연간 캘린더", "9부"),
    ("오해와 진실", "10부"),
    ("용어 사전", "3부"),
    ("월별 상세 캘린더", "9부"),
    ("자가진단 20문항", "12부 워크시트5"),
    ("정책자금 vs 은행대출 비교", "5-2부"),
    ("정산보고", "3부 용어사전, 9-2부"),
    ("중소벤처24", "2부 4장"),
    ("지역별 살펴보기", "2부 9장"),
    ("지원사업 유형 완전정리", "5-2부"),
    ("체크리스트 총모음", "부록4"),
    ("통화 스크립트", "11부"),
    ("협약", "3부 용어사전, 9-2부"),
    ("희망리턴패키지", "3부 용어사전, 5부 사례2"),
    ("90일 실행 캘린더", "12부 워크시트4-2"),
]
index_entries += [
    ("90일 실행 캘린더", "12부 워크시트4-2"),
    ("문제 상황 대처법", "부록10"),
    ("한 장 요약 카드", "부록11"),
    ("분야ㆍ지역별 그래프", "1부ㆍ2부 9장"),
    ("협약 이후 흐름도", "9-2부"),
]
idx_rows = [[Paragraph(term, styles["table_cell"]), Paragraph(loc, styles["table_cell"])] for term, loc in index_entries]
idx_tbl = Table(idx_rows, colWidths=[70 * mm, 96 * mm])
idx_tbl.setStyle(TableStyle([
    ("GRID", (0, 0), (-1, -1), 0.4, BORDER),
    ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#faf9ff")]),
    ("TOPPADDING", (0, 0), (-1, -1), 5),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ("LEFTPADDING", (0, 0), (-1, -1), 8),
]))
story.append(idx_tbl)

h1("부록 9. 자주 쓰는 약칭 풀이")
abbr_data = [
    [Paragraph("약칭", styles["table_head"]), Paragraph("풀이", styles["table_head"])],
    [Paragraph("TIPA", styles["table_cell"]), Paragraph("중소기업기술정보진흥원 — 중소기업 R&amp;D 지원 전담기관", styles["table_cell"])],
    [Paragraph("KOTRA(코트라)", styles["table_cell"]), Paragraph("대한무역투자진흥공사 — 해외 진출ㆍ수출 지원기관", styles["table_cell"])],
    [Paragraph("HACCP(해썹)", styles["table_cell"]), Paragraph("식품안전관리인증기준 — 식품 제조ㆍ가공업 안전 인증", styles["table_cell"])],
    [Paragraph("ISO", styles["table_cell"]), Paragraph("국제표준화기구 인증 — 품질ㆍ환경경영시스템 등 국제 인증", styles["table_cell"])],
    [Paragraph("ESG", styles["table_cell"]), Paragraph("환경(Environment)ㆍ사회(Social)ㆍ지배구조(Governance) — 기업의 비재무적 가치 지표", styles["table_cell"])],
    [Paragraph("R&amp;D", styles["table_cell"]), Paragraph("Research and Development, 연구개발", styles["table_cell"])],
    [Paragraph("IP", styles["table_cell"]), Paragraph("Intellectual Property, 지식재산권(특허ㆍ상표ㆍ디자인 등)", styles["table_cell"])],
    [Paragraph("소진공", styles["table_cell"]), Paragraph("소상공인시장진흥공단의 줄임말", styles["table_cell"])],
    [Paragraph("PG", styles["table_cell"]), Paragraph("Payment Gateway, 전자결제대행사 — 온라인 판매 시 결제를 대신 처리해주는 서비스", styles["table_cell"])],
    [Paragraph("스마트스토어", styles["table_cell"]), Paragraph("네이버가 운영하는 개인ㆍ소상공인 대상 온라인 판매 플랫폼", styles["table_cell"])],
    [Paragraph("HACCPㆍISO 등 인증", styles["table_cell"]), Paragraph("업종별 법정ㆍ국제 인증 — 6장ㆍ5-2부 참고", styles["table_cell"])],
    [Paragraph("4대보험", styles["table_cell"]), Paragraph("국민연금ㆍ건강보험ㆍ고용보험ㆍ산재보험 — 상시근로자 증빙의 기준", styles["table_cell"])],
]
abbr_tbl = Table(abbr_data, colWidths=[36 * mm, 130 * mm])
abbr_tbl.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#faf9ff")]),
    ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
    ("TOPPADDING", (0, 0), (-1, -1), 6),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
]))
story.append(abbr_tbl)

h1("부록 10. 자주 발생하는 문제 상황과 대처법")
body("신청 과정에서 실제로 자주 생기는 문제 상황과 대처 방법을 모았습니다.")

def trouble(situation, action):
    story.append(Paragraph(f"<b>상황: {situation}</b>", ParagraphStyle("trbl_s", fontName=FONT, fontSize=11.3, leading=17, textColor=ACCENT, spaceBefore=9, spaceAfter=3)))
    body(f"<b>대처</b>: {action}")

trouble("서류 발급이 마감일에 임박해서야 완료됐다", "일단 준비된 서류만으로 접수하고, 부족한 서류는 담당 부서에 전화해 추가 제출이 가능한지 확인하세요(11부 스크립트 참고). 상당수 사업이 일부 서류의 사후 제출을 허용합니다.")
trouble("온라인 신청 사이트에 로그인이 안 된다", "공동인증서 유효기간, 브라우저 호환성(일부 사이트는 특정 브라우저에서만 원활)을 먼저 확인하세요. 그래도 안 되면 사이트 고객센터나 담당 부서에 전화로 상황을 알리고 대안을 물어보세요.")
trouble("작성한 사업계획서 파일이 양식과 다르다는 오류가 뜬다", "공고문에 첨부된 최신 양식을 다시 내려받아 옮겨 붙이세요. 양식이 중간에 개정되는 경우가 있어, 예전에 저장해둔 양식을 쓰다가 오류가 나는 경우가 흔합니다.")
trouble("선정됐는데 협약 체결 기한을 놓칠 것 같다", "기한 내 서명이 어려우면 반드시 사전에 담당 부서에 연락해 연기 가능 여부를 물어보세요. 연락 없이 기한을 넘기면 선정이 취소될 수 있습니다.")
trouble("정산보고 증빙자료를 일부 분실했다", "결제 수단(카드사, 계좌이체 내역)을 통해 재발급받을 수 있는 경우가 많습니다. 담당 부서에 상황을 먼저 알리고 대체 증빙 방법을 문의하세요.")
trouble("사업자등록 정보(주소ㆍ업종)를 최근에 바꿨는데 서류마다 정보가 다르게 나온다", "국세청 홈택스에서 사업자등록 정정 신고를 먼저 마치고, 정정 완료된 증명원을 다시 발급받으세요. 지원사업 신청 서류는 항상 최신 등록 정보와 일치해야 합니다.")
trouble("공고문에 담당자 연락처가 없거나 연결이 안 된다", "공고문을 게시한 사이트(기업마당 등)의 대표 콜센터(부록3)로 연락해 해당 사업 담당 부서를 안내받으세요.")

h1("가이드 활용 자가 점검")
body("이 가이드를 어디까지 활용했는지 스스로 점검해보세요.")
callout_box("체크해보세요", [
    "1부 5분 컷 체크리스트로 내 상황을 정리해봤다",
    "기업마당에서 실제로 한 번 이상 검색해봤다",
    "관심 있는 공고를 최소 1개 이상 찾았다",
    "필요 서류 중 하나 이상 발급을 시작했다",
    "사업계획서 초안을 워크시트에 적어봤다",
    "담당 부서에 문의 전화나 이메일을 해본 적이 있다",
])
body("절반 이상 체크했다면 이미 &ldquo;찾아만 보고 마는&rdquo; 단계를 지나 실제 행동으로 옮기고 있는 것입니다. 나머지 항목도 12부 워크시트를 활용해 하나씩 채워보세요.")

h1("실제 탈락 이유 TOP 5 — 심사위원 입장에서 본 함정")
body("10부에서 &ldquo;자주 하는 오해&rdquo;를 다뤘다면, 여기서는 실제로 서류ㆍ발표 평가에서 가장 자주 나오는 <b>탈락 원인 5가지</b>를 심사위원 시점에서 정리했습니다.")
callout_box("1위. 공고와 &ldquo;단계&rdquo;가 안 맞는다", [
    "탈락의 원인은 대부분 실력 부족이 아니라 &ldquo;이 기업은 아직 이 사업을 받을 단계가 아니다&rdquo;, &ldquo;사업 취지와 방향이 안 맞는다&rdquo;는 단계ㆍ목적 불일치입니다.",
    "지원 전 4부 체크리스트로 내 창업 단계(예비/1년/3년 등)를 먼저 명확히 하고, 그 단계에 맞는 사업만 추려서 지원하세요.",
])
callout_box("2위. 설명 없는 표ㆍ차트만 붙여넣는다", [
    "평가위원은 하루에 수십 개 계획서를 보기 때문에, 숫자나 그래프만 있고 &ldquo;왜 이 숫자인지&rdquo; 설명이 없으면 감점 대상입니다.",
    "표를 넣었다면 반드시 그 아래에 &ldquo;이 표가 의미하는 것&rdquo;을 한두 문장으로 설명하세요.",
])
callout_box("3위. &ldquo;할 수 있다&rdquo;만 있고 &ldquo;해봤다&rdquo;가 없다", [
    "심사위원은 아이디어 자체보다 시장조사ㆍ프로토타입ㆍ고객 반응처럼 <b>이미 해본 흔적</b>을 봅니다.",
    "작은 규모라도 실제로 시도해본 것(설문조사 결과, 시제품 사진, SNS 반응 등)이 있다면 반드시 넣으세요.",
])
callout_box("4위. 근거 없는 재무 숫자", [
    "&ldquo;3년 안에 매출 10억&rdquo;처럼 과장되거나 근거 없는 숫자는 즉시 감점 요인입니다.",
    "숫자를 쓸 때는 반드시 &ldquo;어떤 계산으로 나온 숫자인지&rdquo; 함께 적어야 신뢰를 얻습니다.",
])
callout_box("5위. 첨부서류ㆍ서명 누락", [
    "빠진 첨부파일, 서명 누락, 증빙자료 불충분처럼 사소해 보이는 서류 미비도 실제 탈락 사유의 큰 비중을 차지합니다.",
    "제출 직전 7부 체크리스트로 한 번 더 확인하는 습관이 가장 확실한 예방책입니다.",
])
callout_box("탈락 이유 TOP5 핵심 요약", [
    "가장 흔한 탈락 원인은 실력 부족이 아니라 &ldquo;단계ㆍ취지 불일치&rdquo;",
    "표는 설명과 함께, 재무 숫자는 근거와 함께, 서류는 제출 직전 한 번 더 확인",
])

# ============================================================
# 부록 11 — 요약 카드
# ============================================================
h1("부록 11. 한 장 요약 카드")
body("이 가이드 전체를 세 문장으로 압축하면 이렇습니다. 다 잊어도 이 세 가지만 기억하면 됩니다.")
callout_box("기억할 세 가지", [
    "1. 바쁘면 기업마당(bizinfo.go.kr) 검색창에 내 상황 키워드만 넣어도 절반은 해결됩니다(1부).",
    "2. 정책자금(융자)과 지원금(무상)을 헷갈리지 마세요 — 공고문의 지원내용을 항상 확인하세요(3부).",
    "3. 애매하면 무조건 담당 부서에 전화ㆍ이메일로 먼저 확인하세요 — 이게 탈락을 막는 가장 확실한 방법입니다(11부).",
])
body("이 세 가지를 기준으로, 필요할 때마다 이 책의 각 부를 사전처럼 펼쳐보시면 됩니다.")

h1("부록 12. 부별 핵심 요약")
summary_data = [
    [Paragraph("부", styles["table_head"]), Paragraph("한 줄 요약", styles["table_head"])],
    [Paragraph("1부", styles["table_cell"]), Paragraph("기업마당 검색 3단계 + 5분 컷 체크리스트", styles["table_cell"])],
    [Paragraph("2부", styles["table_cell"]), Paragraph("소상공인24ㆍ중소벤처24ㆍ소진공ㆍ정부24ㆍ지자체 상세 사용법", styles["table_cell"])],
    [Paragraph("3부", styles["table_cell"]), Paragraph("헷갈리는 용어 25개 이상 정리", styles["table_cell"])],
    [Paragraph("4부", styles["table_cell"]), Paragraph("사업단계ㆍ목적ㆍ특성 3축 체크리스트", styles["table_cell"])],
    [Paragraph("5부", styles["table_cell"]), Paragraph("A~F씨 6가지 실전 검색 사례", styles["table_cell"])],
    [Paragraph("5-2부", styles["table_cell"]), Paragraph("지원사업 유형 전체 분류(자금ㆍ역량ㆍ판로ㆍ창업단계 등)", styles["table_cell"])],
    [Paragraph("5-3부", styles["table_cell"]), Paragraph("사업계획서 작성법 + 업종별 예문", styles["table_cell"])],
    [Paragraph("6~8부", styles["table_cell"]), Paragraph("검색 키워드 모음, 신청 전 체크리스트, FAQ", styles["table_cell"])],
    [Paragraph("9부ㆍ9-2ㆍ9-3", styles["table_cell"]), Paragraph("연간 캘린더, 선정 이후 절차, 공고문 읽는 법", styles["table_cell"])],
    [Paragraph("10~11부", styles["table_cell"]), Paragraph("오해와 진실, 통화ㆍ이메일 스크립트", styles["table_cell"])],
    [Paragraph("12부", styles["table_cell"]), Paragraph("인쇄용 워크시트 5종 + 정책자금ㆍ탈락원인 실측 정리", styles["table_cell"])],
    [Paragraph("부록", styles["table_cell"]), Paragraph("서류가이드ㆍ체크리스트ㆍ표현사전ㆍ기관소개ㆍ색인 등 12종", styles["table_cell"])],
]
summary_tbl = Table(summary_data, colWidths=[30 * mm, 136 * mm])
summary_tbl.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#faf9ff")]),
    ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
    ("TOPPADDING", (0, 0), (-1, -1), 6),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
]))
story.append(summary_tbl)

story.append(Spacer(1, 20))
h1("마지막으로 전하고 싶은 말")
closing_box = [
    [Paragraph(
        "정부지원사업을 찾는 일은 처음이 가장 어렵습니다. 어떤 사이트를 봐야 할지, 어떤 "
        "용어가 무슨 뜻인지, 내가 자격이 되는지조차 알기 어렵기 때문입니다. 하지만 이 가이드에서 "
        "다룬 순서 — 상황 정리, 검색, 서류 준비, 계획서 작성, 신청, 정산 — 를 한 번이라도 "
        "끝까지 경험하고 나면, 두 번째부터는 훨씬 수월해집니다.<br/><br/>"
        "완벽하게 준비될 때까지 기다리지 마세요. 4부 워크시트로 오늘 당장 내 상황부터 "
        "정리해보고, 1부로 돌아가 기업마당 검색창에 키워드를 입력하는 것부터 시작하시길 "
        "바랍니다.",
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


WATERMARK_TEXT = "수익화허브 · 무단 전재·재배포 금지"


def draw_watermark(canvas, dark_bg=False):
    """구매 후 재배포를 막기 위한 저작권 표시용 옅은 대각선 반복 워터마크."""
    canvas.saveState()
    canvas.setFont(FONT, 12.5)
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
            canvas.drawCentredString(ix * step_x, iy * step_y, WATERMARK_TEXT)
    canvas.restoreState()


def add_page_number(canvas, doc_):
    draw_watermark(canvas, dark_bg=False)
    canvas.saveState()
    canvas.setFont(FONT, 9)
    canvas.setFillColor(TEXT_DIM)
    canvas.drawCentredString(A4[0] / 2, 13 * mm, str(doc_.page))
    canvas.restoreState()


doc.build(story, onFirstPage=lambda c, d: draw_watermark(c, dark_bg=True), onLaterPages=add_page_number)
print("done:", OUT)
