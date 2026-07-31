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
    title="소상공인·1인사업자를 위한 정부지원금 찾기 가이드",
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
    "body": ParagraphStyle("body", fontName=FONT, fontSize=11.5, leading=19,
                            textColor=TEXT_DARK, spaceAfter=10, alignment=TA_LEFT),
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
story.append(Paragraph("소상공인·1인사업자를 위한", styles["subtitle"]))
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
    story.append(PageBreak())
    story.append(Spacer(1, 70 * mm))
    story.append(Paragraph(label, styles["part_label"]))
    story.append(Paragraph(title, styles["part_title"]))
    story.append(HRFlowable(width="20%", thickness=1.2, color=ACCENT, hAlign="CENTER", spaceBefore=4, spaceAfter=16))
    story.append(Paragraph(desc, styles["part_desc"]))
    story.append(PageBreak())


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
toc_line("이 가이드를 왜 만들었나", "toc")
story.append(Spacer(1, 8))
toc_line("1부. 5분 컷 — 가장 빨리 찾는 법", "toc_part")
toc_line("1장. 딱 한 사이트만 볼 시간이라면 — 기업마당", "toc")
toc_line("2장. 5분 컷 체크리스트", "toc")
story.append(Spacer(1, 8))
toc_line("2부. 사이트별 상세 사용법", "toc_part")
toc_line("3장. 소상공인24 · 4장. 중소벤처24 · 5장. 소진공", "toc")
toc_line("6장. 정부24 보조금24 · 7장. 지자체 홈페이지 · 8장. 민간 통합검색", "toc")
story.append(Spacer(1, 8))
toc_line("3부. 헷갈리는 용어 사전", "toc_part")
toc_line("4부. 내 상황별 체크리스트", "toc_part")
toc_line("5부. 실전 사례로 따라 해보기 (A·B·C·D씨 4가지 사례)", "toc_part")
toc_line("5-2부. 지원사업 유형 완전정리", "toc_part")
toc_line("5-3부. 사업계획서 작성 실전 가이드", "toc_part")
toc_line("6부. 사이트별 검색 키워드 모음", "toc_part")
toc_line("7부. 신청 전 체크리스트", "toc_part")
toc_line("8부. 자주 묻는 질문(FAQ)", "toc_part")
toc_line("9부. 연간 지원사업 캘린더", "toc_part")
story.append(Spacer(1, 8))
toc_line("마무리 · 부록1. 신청 서류 준비 가이드", "toc")
toc_line("부록2. 사이트 주소 모음 · 부록3. 문의 연락처 모음", "toc")
story.append(PageBreak())

# ============================================================
# 서문
# ============================================================
h1("이 가이드를 왜 만들었나")
body("크몽, 스레드, 블라인드에서 소상공인·1인사업자들의 글을 직접 찾아봤습니다. 반복해서 나온 말이 있었습니다.")
quote("&ldquo;제도가 어려운 게 아니라, 정보가 여기저기 흩어져 있고 용어가 낯설어서 못 찾는다.&rdquo;")
body("실제로 정부지원사업은 중앙부처, 지자체, 공공기관을 다 합치면 수천 개가 있고, 사이트도 제각각입니다. 어떤 건 기업마당에, 어떤 건 소상공인24에, 어떤 건 지자체 홈페이지에만 올라옵니다. 사업하는 사람 입장에서는 &ldquo;내가 받을 수 있는 게 뭔지&rdquo; 알아내는 것 자체가 일이 됩니다.")
body("이 가이드는 두 부분으로 나눴습니다. <b>1부</b>는 지금 당장 5분 안에 써먹을 수 있는 핵심만 담았습니다. 바쁘면 1부만 읽어도 충분합니다. <b>2부부터</b>는 사이트별 상세 사용법, 용어 사전, 실전 사례, 체크리스트 등 필요할 때 찾아보는 참고자료입니다.")

callout_box("이 가이드가 아닌 것", [
    "지원금 신청을 대신 해드리는 대행 서비스가 아닙니다. 정보를 정리해서 드릴 뿐이고, 실제 신청은 반드시 본인이 직접 해야 합니다. (관련 법상 수수료를 받는 대리 신청은 문제가 될 수 있습니다.)",
    "이 가이드에 실린 화면과 공고 사례는 모두 집필 시점(2026년 7월)에 실제로 접속해서 캡처한 것이며, 최신 금액·마감일·자격 조건은 반드시 해당 공식 사이트에서 본인이 직접 확인해야 합니다.",
])
story.append(PageBreak())

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
body("화면 위쪽에 전체 건수가 나오고, 그 아래에 지원사업공고·행사정보·정책뉴스처럼 종류별로 나뉘어 있습니다. 우리가 볼 건 대부분 <b>&ldquo;지원사업공고&rdquo;</b> 쪽입니다. 실제로 이 검색에서 이런 공고들이 나왔습니다.")
callout_box("실제 검색 결과 예시(2026년 7월 기준)", [
    "[경북] 2026년 청년창업제품 온라인 기획전 판로지원 참가기업 모집 공고",
    "[충북] 2026년 중소기업육성자금 융자(이차보전) 지원계획 변경 공고",
    "[경기] 성남시 2026년 청년창업 아이디에이션 4.0 참가자 모집 공고",
])
body("이렇게 지역별·사업별로 실제 진행 중인 공고가 리스트로 뜹니다. 제목을 클릭하면 신청 대상, 지원 내용, 신청 기간, 담당 부서 연락처까지 상세 페이지에서 확인할 수 있습니다.")
story.append(PageBreak())

h2("3단계 — 결과가 너무 많으면 필터로 좁히기")
body("검색어 없이 메뉴에서 &ldquo;정책정보 &gt; 지원사업 공고&rdquo;로 들어가면, 아래처럼 <b>분야별·지역별로 걸러볼 수 있는 필터 화면</b>이 나옵니다. 이 화면이 사실 기업마당에서 가장 중요한 화면입니다.")
screenshot("04_bizinfo_pblanc_list.png", "지원사업 공고 필터 화면 — 분야(창업·금융·기술 등)와 지역을 버튼으로 선택")
body("위쪽에 분야별 버튼(금융·기술·인력·수출·내수·창업·경영·기타)이 있고, 그 아래에 지역별 버튼(서울·부산·대구·인천 등)이 있습니다. 자신의 업종 분야와 사업장 지역을 각각 클릭하면 그 조건에 맞는 공고만 걸러져서 보입니다. 목록 위쪽의 &ldquo;전체 / 중앙부처 / 지자체&rdquo; 탭으로 발행 주체를 나눠 볼 수도 있고, &ldquo;마감일순&rdquo; 정렬로 바꾸면 곧 마감되는 공고부터 볼 수 있습니다.")
quote("딱 이 세 단계(검색 → 결과 확인 → 필터로 좁히기)만 알아도, 기업마당에서 내게 맞는 공고를 찾는 데는 충분합니다.")

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
    "운영자금(인건비·임차료) → \u201c정책자금\u201d 또는 \u201c경영안정자금\u201d",
    "온라인 판로·마케팅 → \u201c온라인 판로지원\u201d, \u201c스마트스토어 지원\u201d",
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
body("첫 화면에 &ldquo;소상공인24(소공인·소상공인·전통시장·예비창업자 등 기타 지원사업 정보 조회 및 신청)&rdquo;와 &ldquo;소상공인 경영안정 바우처&rdquo; 두 개의 큰 배너가 있습니다. 실제로 이 사이트를 열었을 때 구체적인 지원 조건이 배너에 바로 노출되는 경우가 많습니다 — <b>이런 배너는 시기마다 완전히 바뀌므로, 방문할 때마다 새로 확인하는 습관을 들이세요.</b>")
body("<b>사용법</b>: 첫 화면의 &ldquo;소상공인24&rdquo; 배너를 클릭하면 자격 여부 확인 → 지원사업 목록 → 온라인 신청까지 한 사이트 안에서 진행됩니다. 회원가입(간편인증 또는 공동인증서)이 필요한 경우가 대부분이니, 신청까지 하려면 미리 공동인증서나 간편인증(카카오·네이버 등)을 준비해두면 편합니다.")
story.append(PageBreak())

h1("4장. 중소벤처24 (smes.go.kr)")
body("중소기업·스타트업 대상 지원사업, K-스타트업 관련 정보가 모여 있습니다. 스타트업이나 기술 기반 창업이라면 기업마당과 함께 반드시 확인해야 합니다.")
screenshot("06_smes_home.png", "중소벤처24 첫 화면 — 오늘의 사업공고와 서비스 개편 안내가 함께 표시된다")
body("2026년 기준 이 사이트는 &ldquo;중소벤처24 서비스 일원화&rdquo;라는 이름으로 개편이 진행 중이었습니다. <b>정부 사이트는 이렇게 주기적으로 개편·이전을 하니, 예전에 봤던 메뉴 위치가 안 보인다고 당황하지 말고 첫 화면의 공지사항이나 팝업부터 확인하세요.</b>")
body("<b>사용법</b>: 첫 화면 왼쪽의 &ldquo;오늘의 사업공고&rdquo;에서 전체 공고 수, 이번주 신규, 인기공고, 마감임박 공고 건수를 바로 볼 수 있습니다. 회원가입 후 기업 정보를 등록해두면 &ldquo;스마트 맞춤 추천&rdquo;이 내 업종·규모에 맞는 사업을 자동으로 걸러줍니다.")

h1("5장. 소상공인시장진흥공단(소진공) — semas.or.kr")
body("소상공인 <b>정책자금(융자)</b>을 직접 운영하는 기관입니다. &ldquo;지원금&rdquo;이 아니라 &ldquo;빌려주는 돈(융자)&rdquo;이 필요하다면 반드시 확인해야 하는 사이트입니다.")
screenshot("07_semas_home.png", "소진공 첫 화면 — 정책자금·교육·소상공인24·상권정보 4대 메뉴")
body("첫 화면이 네 개의 큰 메뉴로 나뉩니다. <b>소상공인 정책자금(융자)</b>은 운영자금·시설자금을 낮은 금리로 빌려주는, 소상공인이 가장 많이 찾는 메뉴입니다. <b>지식배움터(교육)</b>는 창업·경영 관련 무료 교육 프로그램이고, <b>소상공인365(상권정보)</b>는 업종별·지역별 상권 분석 데이터를 무료로 제공해 창업 전 입지를 알아볼 때 유용합니다.")
body("오른쪽에는 전국 소상공인지원센터(새출발지원센터) 지도가 있어서, 직접 방문 상담을 원하면 여기서 가까운 센터를 찾을 수 있습니다. 전화 상담은 중소기업통합콜센터 1357, 소진공 콜센터 1533-0100입니다.")
body("<b>사용법</b>: &ldquo;소상공인 정책자금&rdquo; 메뉴로 들어가면 융자 종류별 지원 한도·금리·신청 자격이 표에 정리돼 있습니다. 정책자금은 예산이 소진되면 연중에도 마감되는 경우가 많아서, <b>연초(1~2월)에 확인하는 게 가장 유리합니다.</b>")
story.append(PageBreak())

h1("6장. 정부24 — 보조금24")
body("개인·사업자가 받을 수 있는 각종 보조금을 한 번에 조회할 수 있는 서비스입니다. 정부24(2026년 기준 &ldquo;정부24 AI&rdquo;로 개편) 사이트 안에서 검색창에 &ldquo;보조금24&rdquo;를 입력하면 진입할 수 있습니다.")
body("가장 큰 특징은 <b>본인 정보를 입력하면 대상이 될 수 있는 보조금을 먼저 추천해주는 방식</b>이라는 점입니다. 기업마당·소상공인24처럼 &ldquo;내가 키워드를 넣어서 찾는&rdquo; 방식과 반대로, 여기서는 나이·거주지·사업 형태 같은 조건을 입력하면 시스템이 역으로 &ldquo;받을 수 있을 것 같은 보조금 목록&rdquo;을 보여줍니다. 사업자 대상 보조금 외에 개인 대상 복지 보조금도 함께 나오니, 검색 결과에서 &ldquo;사업자·기업&rdquo; 관련 항목만 골라 보면 됩니다.")
callout_box("참고", [
    "정부24는 보안이 엄격한 사이트라 접속 환경(브라우저 보안 프로그램 등)에 따라 첫 접속이 원활하지 않을 수 있습니다. 접속이 안 되면 새로고침하거나 다른 브라우저로 재시도해보세요.",
    "로그인은 공동인증서, 간편인증(카카오·네이버·PASS 등) 모두 지원합니다.",
])

h1("7장. 지자체(시·군·구) 홈페이지 — 중앙 사이트에 없는 걸 찾는 법")
body("같은 업종이어도 <b>사는 지역에 따라 별도로 받을 수 있는 지원사업</b>이 따로 있습니다. 이런 지역 한정 지원사업은 기업마당 같은 중앙 사이트에 안 올라오는 경우가 많아서, 거주 지역 시청·구청 홈페이지를 따로 봐야 합니다.")
body("예시로 수원시 홈페이지를 살펴보겠습니다.")
screenshot("09_local_gov_example.png", "지자체 홈페이지 예시(수원시) — 종합민원·정보공개/개방·분야별정보 메뉴 구조")
body("지자체 홈페이지는 사이트마다 디자인이 다르지만, 찾아야 할 메뉴 이름은 대체로 비슷합니다.")
callout_box("찾아야 할 메뉴", [
    "\u201c고시공고\u201d — 법적 효력이 있는 공식 공고문 게시판. 지원사업 모집공고도 대부분 여기에 함께 올라옵니다.",
    "\u201c분야별정보\u201d 또는 \u201c정보공개/개방\u201d — 경제·기업지원 카테고리 안에 지원사업 메뉴가 따로 있는 경우가 많습니다.",
    "상단 검색창에 \u201c소상공인 지원\u201d이나 \u201c창업 지원\u201d을 직접 검색하는 것도 빠른 방법입니다.",
])
body("<b>사용법 요령</b>: &ldquo;OO시 소상공인 지원사업&rdquo;, &ldquo;OO구 청년창업 지원&rdquo;처럼 <b>지역명을 반드시 포함해서 검색엔진(네이버·구글)에 먼저 검색</b>해보는 것도 좋은 방법입니다. 지자체는 자체 예산으로 운영하는 사업이 많아 경쟁률이 상대적으로 낮은 경우가 있어, 중앙 사업 못지않게 챙겨볼 가치가 있습니다.")

h1("8장. (참고) 민간 통합검색 사이트")
body("기업마당·소상공인24 등 여러 공공 사이트의 공고를 매일 모아서 보여주는 민간 서비스도 있습니다. 공식 사이트를 일일이 도는 게 번거롭다면 참고용으로 함께 쓰면 좋습니다. 다만 <b>최종 신청과 정확한 조건 확인은 항상 공식 사이트에서</b> 해야 합니다 — 민간 사이트의 정보는 업데이트가 늦거나 요약 과정에서 조건이 빠질 수 있습니다.")

# ============================================================
# 3부 — 용어 사전
# ============================================================
part_page("PART 3", "헷갈리는 용어 사전", "\u201c용어가 낯설어서 못 찾는다\u201d는 말이<br/>이 가이드를 만든 가장 큰 이유였습니다.")

h1("공고문에 자주 나오는 용어")

def term(name, desc):
    story.append(Paragraph(f"<b>{name}</b>", ParagraphStyle("term", fontName=FONT, fontSize=12.3, leading=18, textColor=ACCENT, spaceBefore=10, spaceAfter=3)))
    body(desc)

term("소상공인 vs 중소기업", "소상공인은 중소기업 중에서도 규모가 더 작은 사업자를 말합니다. 업종별로 기준이 다른데, 대체로 상시근로자 수 5명 미만(제조업·건설업·운수업 등은 10명 미만)이면서 매출액 기준을 충족해야 합니다. 지원사업 공고에서 &ldquo;소상공인만 신청 가능&rdquo;이라고 돼 있으면, 이 기준부터 확인해야 합니다.")
term("정책자금(융자) vs 지원금(보조금)", "정책자금은 <b>빌리는 돈</b>입니다. 낮은 금리로 빌려주는 것이지 갚지 않아도 되는 돈이 아닙니다. 반면 지원금·보조금은 조건을 충족하면 <b>갚지 않아도 되는 돈</b>입니다. 공고문에서 이 둘을 헷갈리면 자금 계획에 큰 차질이 생기니 반드시 구분해서 읽어야 합니다.")
term("예비창업패키지 / 초기창업패키지", "중소벤처기업부(창업진흥원)가 운영하는 대표 창업 지원사업 계열입니다. &ldquo;예비창업패키지&rdquo;는 아직 사업자등록을 하지 않은 예비창업자, &ldquo;초기창업패키지&rdquo;는 창업 3년 이내 기업이 대상입니다. 사업화 자금과 함께 멘토링·교육을 지원합니다.")
term("희망리턴패키지", "폐업(예정) 소상공인의 사업정리 컨설팅과 재취업·재창업을 지원하는 사업입니다. 폐업 과정에서 드는 철거비·원상복구비 일부를 지원하기도 합니다.")
term("사업계획서", "지원사업에 신청할 때 제출하는 핵심 서류로, 사업 개요·목표·실행 계획·예산 사용 계획 등을 담습니다. 심사에서 가장 중요하게 보는 서류이므로, 공고문에 첨부된 양식과 배점표를 반드시 먼저 확인해야 합니다.")
term("중복 지원 제한", "같은 목적의 지원사업을 동시에 여러 개 받을 수 없도록 제한하는 규정입니다. 공고문의 &ldquo;지원 제외 대상&rdquo;란에 명시돼 있는 경우가 많으니 꼭 확인하세요.")
term("상시근로자 수", "사업장에 고용된 근로자 수를 말하며, 대표자 본인과 일용직은 대부분 제외하고 계산합니다. 소상공인·중소기업 기준을 판단하는 핵심 지표라 정확히 알아둬야 합니다.")
term("공고문 / 모집공고", "지원사업의 신청 자격, 지원 내용, 신청 기간, 제출 서류, 심사 기준을 공식적으로 안내하는 문서입니다. 다른 어떤 요약 정보보다 원본 공고문을 직접 읽는 게 가장 정확합니다.")
term("공동인증서 / 간편인증", "정부 사이트 로그인·신청에 필요한 본인 인증 수단입니다. 공동인증서(옛 공인인증서)는 은행이나 정부24에서 발급받고, 간편인증은 카카오·네이버·PASS 등 스마트폰 앱으로 인증하는 방식입니다. 신청 직전에 급하게 준비하면 시간이 부족할 수 있으니 미리 만들어두는 게 좋습니다.")
term("사업자등록증명원", "사업자등록 사실을 증명하는 공식 서류로, 대부분의 지원사업 신청에 기본으로 요구됩니다. 정부24에서 무료로 즉시 발급받을 수 있습니다.")
term("고유식별번호(사업자등록번호)", "사업자를 식별하는 10자리 번호입니다. 온라인 신청 시스템에 회원가입할 때 대부분 이 번호로 본인의 사업체를 조회하므로, 정확히 기억해두는 게 좋습니다.")
term("선정평가 / 발표평가", "서류 심사를 통과한 신청자를 대상으로 진행하는 다음 단계 심사입니다. 사업계획을 직접 발표하고 질의응답을 받는 방식이 많으며, 이 단계에서 최종 선정 여부가 갈리는 경우가 많아 발표 자료와 예상 질문 준비가 중요합니다.")
term("협약(협약체결)", "지원사업에 최종 선정된 이후, 지원 조건·의무사항·자금 집행 방법 등을 기관과 공식 계약하는 절차입니다. 협약서에 명시된 의무사항(정산보고, 사용처 제한 등)을 지키지 않으면 지원금 환수 대상이 될 수 있어 반드시 꼼꼼히 읽어야 합니다.")
term("정산보고", "지원받은 자금을 실제로 어떻게 사용했는지 증빙자료(영수증, 계약서 등)와 함께 기관에 보고하는 절차입니다. 사업 종료 후 정산보고를 소홀히 하면 다음 지원사업 신청 시 불이익을 받을 수 있으므로, 지원금을 쓸 때부터 증빙자료를 미리 챙겨두는 습관이 중요합니다.")
term("추가경정예산(추경)", "연초에 편성한 예산으로 부족하거나 새로운 정책 수요가 생겼을 때, 연중에 추가로 편성하는 예산입니다. 추경이 통과되면 그 시기에 새로운 지원사업 공고가 갑자기 늘어나는 경우가 많아, 하반기에도 꾸준히 사이트를 확인할 이유가 됩니다.")
term("공공조달 / 나라장터", "정부·공공기관이 물품·용역을 구매하는 공식 절차와 그 창구(나라장터, g2b.go.kr)를 말합니다. 여성기업·장애인기업 등은 공공조달 입찰에서 가점이나 우선구매 혜택을 받는 경우가 있어, 관련 확인서를 미리 갖춰두면 유리합니다.")

# ============================================================
# 4부 — 체크리스트
# ============================================================
part_page("PART 4", "내 상황별 체크리스트", "1부의 5분 컷 체크리스트를 더 자세히 풀어놓은 버전입니다.")

h1("축 1 — 사업 단계")
callout_box("해당하는 항목을 확인하세요", [
    "예비창업자 (아직 사업자등록 전)",
    "창업 1년 이내",
    "창업 3년 이내",
    "창업 3년 이상 / 재도약 준비",
    "폐업 후 재도전 준비",
])
body("예비창업자·초기창업이라면 &ldquo;예비창업패키지&rdquo;, &ldquo;초기창업패키지&rdquo; 계열 사업을, 3년 이상이라면 &ldquo;성장기반자금&rdquo;, &ldquo;재도약&rdquo; 계열 사업을 우선 검색하세요. 폐업을 준비 중이라면 &ldquo;희망리턴패키지&rdquo;부터 확인하는 게 순서입니다 — 폐업 이후에는 지원 대상에서 제외되는 사업이 많아, 폐업 전에 미리 알아보는 게 유리합니다.")

h1("축 2 — 필요한 목적")
callout_box("무엇이 필요한지 확인하세요", [
    "운영자금(인건비·임차료 등)이 필요하다 → 정책자금(융자) 계열, 소진공",
    "시설·장비 구입이 필요하다 → 시설자금, 스마트상점/스마트공장 계열",
    "온라인 진출·마케팅이 필요하다 → 온라인 판로지원, 디지털 전환 계열",
    "폐업/재창업을 준비 중이다 → 희망리턴패키지, 재도전 계열",
    "컨설팅·교육이 필요하다 → 소상공인 컨설팅, 아카데미 계열(소진공 지식배움터)",
    "갚지 않아도 되는 지원이 필요하다 → \u201c보조금\u201d, \u201c지원금\u201d 키워드로 좁혀서 검색(융자와 혼동 주의)",
])

h1("축 3 — 업종/대상 특성")
callout_box("해당 사항을 확인하세요", [
    "청년(만 39세 이하) 대표 → 청년창업 전용 사업 다수",
    "여성 대표 → 여성기업 전용 사업",
    "특정 지역(비수도권 등) → 지역 균형 관련 가산점/전용 사업",
    "기술·제조 기반 → 중소벤처24, 창업진흥원 계열",
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
body("B씨는 상권이 침체돼 폐업을 고민 중이지만, 온라인 배달·포장 판매로 전환해 재도전해볼지 고민하고 있습니다.")
callout_box("B씨의 3단계 판단", [
    "축 1(사업 단계): 창업 3년 이상 → \u201c재도약\u201d 계열도 후보지만, 폐업까지 고려 중이므로 \u201c희망리턴패키지\u201d도 함께 확인",
    "축 2(목적): 온라인 진출 → \u201c온라인 판로지원\u201d, \u201c스마트스토어 지원\u201d",
    "축 3(특성): 해당 없음 (일반 소상공인 기준으로 검색)",
], numbered=True)
body("→ 완전히 다른 두 갈래를 동시에 알아보는 상황이므로, 기업마당에서 &ldquo;온라인 판로지원&rdquo;과 &ldquo;희망리턴패키지&rdquo;를 각각 검색해 두 선택지의 조건을 먼저 비교합니다. 소진공 지식배움터에서 온라인 판매 관련 무료 교육이 있는지도 함께 확인하면, 신청 전에 실제 감당할 수 있는 방향인지 가늠하는 데 도움이 됩니다.")
story.append(PageBreak())

h1("사례 3 — 소규모 제조업을 하는 42세 C씨")
body("C씨는 반찬가게에 납품하는 소규모 식품가공업체를 운영 중입니다. 노후 장비를 교체하고 위생 설비를 개선하고 싶은데, 목돈이 부담스럽습니다.")
callout_box("C씨의 3단계 판단", [
    "축 1(사업 단계): 창업 3년 이상 → “성장기반자금” 계열",
    "축 2(목적): 시설·장비 구입 → 시설자금, 스마트공장 계열",
    "축 3(특성): 제조 기반 → 중소벤처24 우선 확인",
], numbered=True)
body("→ 기업마당에서 &ldquo;시설자금&rdquo;, &ldquo;스마트공장&rdquo;으로 각각 검색하고, 중소벤처24에서 제조업 특화 지원사업이 있는지 함께 확인합니다. 소진공 정책자금 중에도 시설자금 전용 상품이 있으니 금리·한도를 비교해봅니다. 위생 설비는 지자체 식품안전 관련 부서에서 별도 보조사업을 운영하는 경우가 있어, 거주 지역 시청 &ldquo;식품안전&rdquo; 또는 &ldquo;위생&rdquo; 관련 부서 페이지도 함께 검색해보는 게 좋습니다.")

h1("사례 4 — 프리랜서에서 1인사업자로 전환한 34세 D씨")
body("D씨는 3년간 프리랜서로 디자인 일을 하다가 최근 사업자등록을 했습니다. 아직 사업 기반이 약해 안정적인 수입원을 늘리고, 자기 브랜드로 된 온라인 판매도 시작하고 싶습니다.")
callout_box("D씨의 3단계 판단", [
    "축 1(사업 단계): 창업 1년 이내(사업자등록 기준) → “초기창업패키지” 후보",
    "축 2(목적): 온라인 진출 + 컨설팅 → 온라인 판로지원 + 소진공 지식배움터",
    "축 3(특성): 해당 사항에 따라 여성기업·청년창업 키워드 추가 검토",
], numbered=True)
body("→ 프리랜서 경력은 사업자등록 이전 활동이라 &ldquo;창업 1년 이내&rdquo; 기준 판단이 헷갈릴 수 있습니다. 이런 경우 공고문의 &ldquo;창업일 기준&rdquo; 정의를 꼭 확인해야 합니다(사업자등록일 기준인지, 실제 사업 개시일 기준인지 사업마다 다릅니다). 애매하면 담당 부서에 전화로 먼저 확인하는 게 가장 확실합니다.")

# ============================================================
# 5-2부 — 지원사업 유형 완전정리
# ============================================================
part_page("PART 5-2", "지원사업 유형 완전정리", "&ldquo;이게 무슨 사업 계열인지 모르겠다&rdquo; 싶을 때<br/>펼쳐 보는 분야별 사전입니다.")

h1("자금 지원 계열")
h2("정책자금(융자)")
body("정부·지자체·공공기관이 낮은 금리로 사업자금을 빌려주는 제도입니다. 대표적으로 소진공의 &ldquo;일반경영안정자금&rdquo;, &ldquo;특별경영안정자금&rdquo;이 있고, 시기에 따라 재해·물가 등 특수 상황 대응용 특별자금이 한시적으로 열리기도 합니다. 심사에서 신용도와 상환능력을 함께 봅니다.")
h2("보조금·지원금")
body("조건을 충족하면 갚지 않아도 되는 자금입니다. 특정 목적(고용창출, 시설개선, 판로개척 등)에 쓰도록 용도가 정해져 있는 경우가 많고, 사후에 사용 내역을 증빙해야 하는 경우가 대부분입니다.")
h2("바우처")
body("현금이 아니라 특정 서비스나 물품을 이용할 수 있는 이용권 형태의 지원입니다. 예를 들어 &ldquo;소상공인 경영안정 바우처&rdquo;처럼 정해진 가맹점에서만 사용할 수 있거나, 특정 용도(마케팅, 컨설팅 등)로만 쓸 수 있도록 제한된 경우가 많습니다.")

h1("역량 강화 계열")
h2("컨설팅·멘토링")
body("사업계획 수립, 재무 관리, 마케팅 전략 등을 전문가가 무료 또는 저비용으로 도와주는 프로그램입니다. 소진공 지식배움터, 창업진흥원 계열 사업에 부속된 경우가 많습니다.")
h2("교육 프로그램")
body("온라인·오프라인 강의 형태로 제공되며, 창업 기초부터 세무·회계, 온라인 마케팅까지 주제가 다양합니다. 수료 시 이수증을 발급해 다른 지원사업 신청 시 가점으로 활용할 수 있는 경우도 있습니다.")

h1("판로·시설 계열")
h2("판로지원")
body("온라인몰 입점 지원, 박람회·전시회 참가비 지원, 라이브커머스 제작 지원 등 매출을 늘리기 위한 지원입니다. &ldquo;온라인 판로지원&rdquo;, &ldquo;스마트스토어 지원&rdquo;이 대표적입니다.")
h2("스마트상점 / 스마트공장")
body("키오스크, 스마트오더, 서빙로봇 등 소상공인 매장의 디지털 전환을 돕는 &ldquo;스마트상점&rdquo;과, 제조업체의 생산 설비를 자동화·데이터화하는 &ldquo;스마트공장&rdquo; 지원사업이 있습니다. 도입 비용의 일부를 지원하는 방식이 일반적입니다.")

h1("창업 단계별 계열")
h2("예비창업패키지 → 초기창업패키지 → 창업도약패키지")
body("창업진흥원이 운영하는 대표 계열로, 사업 연차에 따라 세 단계로 나뉩니다. 예비창업패키지(사업자등록 전), 초기창업패키지(3년 이내), 창업도약패키지(3~7년) 순으로 지원 규모와 요구되는 사업 성숙도가 커집니다. 본인의 창업 연차에 맞는 단계를 정확히 확인하고 신청해야 합니다.")
h2("재도전 / 재도약 계열")
body("한 차례 폐업을 경험했거나, 사업 정체기를 겪고 있는 사업자를 위한 계열입니다. &ldquo;재도전 특별자금&rdquo;, &ldquo;재도약 지원사업&rdquo; 등의 이름으로 운영됩니다.")
story.append(PageBreak())

h1("수출·인증 계열")
h2("수출지원")
body("해외 진출을 준비하거나 이미 진행 중인 기업을 위한 지원입니다. 해외 전시회 참가비, 통번역·인증비, 물류비 일부를 지원하는 사업이 많고, 코트라(KOTRA)·중소벤처24를 통해 확인할 수 있습니다. 기업마당 필터의 &ldquo;수출&rdquo; 분야를 클릭하면 관련 공고만 모아볼 수 있습니다.")
h2("품목별 인증 지원")
body("식품안전인증(HACCP), 품질경영시스템(ISO) 등 업종별로 요구되는 인증 취득 비용을 지원하는 사업입니다. 기업마당 상단 메뉴의 &ldquo;품목별 법정의무 인증제도&rdquo;에서 본인 업종에 어떤 인증이 필요한지부터 확인할 수 있습니다.")

h1("고용 계열")
h2("고용창출 지원금")
body("신규 채용을 하면 인건비 일부를 일정 기간 지원하는 사업입니다. 청년 채용, 고령자 채용, 장애인 채용 등 채용 대상에 따라 지원 조건과 금액이 다릅니다. 고용노동부와 각 지자체 일자리 관련 부서에서 운영합니다.")
h2("일자리 안정자금 / 두루누리 사회보험료 지원")
body("영세 사업장의 인건비·사회보험료 부담을 낮춰주는 지원입니다. 상시근로자 수와 급여 수준에 따라 지원 대상 여부가 갈리므로, 4대보험 관련 공단(근로복지공단, 국민연금공단 등) 홈페이지에서 조건을 확인해야 합니다.")

h1("R&D 계열")
h2("중소기업 기술개발(R&D) 지원사업")
body("신제품·신기술 개발에 드는 연구개발비를 지원하는 사업입니다. 기술 기반 창업이나 제조업체에 특화돼 있고, 사업계획서 대신 &ldquo;연구개발계획서&rdquo; 형태의 서류를 요구하는 경우가 많아 준비 방식이 다른 지원사업과 다릅니다. 중소벤처24, 중소기업기술정보진흥원(TIPA) 사이트에서 확인할 수 있습니다.")

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
    "일반현황 — 대표자·사업 개요·업종 등 기본 정보",
    "창업동기 및 문제인식 — 왜 이 사업을 하는지, 어떤 문제를 해결하는지",
    "실현가능성 — 제품·서비스가 실제로 구현 가능한지, 시장성이 있는지",
    "성장전략 — 지원금을 받은 뒤 어떻게 매출·고용을 늘릴 것인지",
    "팀 구성 및 역량 — 대표자와 팀원이 이 사업을 해낼 역량이 있는지",
], numbered=True)

h1("항목별 작성 요령")

h2("1. 일반현황 — 짧고 명확하게")
body("가장 쉬운 항목이지만 오타·불일치가 의외로 많이 나옵니다. 사업자등록증의 상호명·업종코드와 사업계획서에 적은 내용이 정확히 일치하는지 제출 전에 반드시 대조하세요.")

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
body("혼자 하는 1인사업이라면 오히려 &ldquo;외주·협력업체를 어떻게 활용할 것인지&rdquo;를 구체적으로 적는 게 낫습니다. 없는 팀원을 있는 것처럼 부풀리기보다, 부족한 역량을 어떻게 보완할 계획인지 솔직하게 쓰는 편이 신뢰를 얻습니다.")

h1("자주 하는 실수 5가지")
callout_box("작성 전에 점검하세요", [
    "공고문 배점표를 안 보고 쓴다 — 어떤 항목에 점수가 많이 걸려있는지 모르고 균등하게 쓰면, 정작 중요한 항목이 부실해집니다.",
    "경쟁사·유사 서비스 언급을 피한다 — 오히려 경쟁 현황을 정확히 파악하고 있다는 인상을 줘야 신뢰를 얻습니다. 없는 척하지 마세요.",
    "숫자 없이 형용사로만 쓴다 — “많은”, “빠른”, “저렴한” 대신 구체적 수치를 넣으세요.",
    "양식의 글자수·페이지 제한을 넘긴다 — 심사 전 서류 요건 미충족으로 자동 탈락하는 경우가 실제로 있습니다.",
    "마감 당일에 처음 작성을 시작한다 — 최소 1주일 전에는 초안을 완성해 다른 사람에게 검토받는 시간을 확보하세요.",
], numbered=False)

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

# ============================================================
# 7부 — 신청 전 체크리스트
# ============================================================
part_page("PART 7", "신청 전 체크리스트", "떨어지는 이유는 대부분 비슷했습니다.<br/>신청 전에 아래를 꼭 확인하세요.")

callout_box("신청 전 최종 점검", [
    "모집공고를 끝까지 읽었는가 — 지원대상·제외대상 조건만 봐도 걸러지는 경우가 많습니다.",
    "마감일 직전에 신청하지 않는가 — 마감 임박에는 접속 폭주, 서류 오류로 제출 자체가 안 되는 경우가 있습니다. 최소 2~3일 여유를 두세요.",
    "사업계획서를 성의 있게 썼는가 — 첫 페이지에서 다른 신청자와의 차별점이 보여야 합니다.",
    "증빙서류를 빠짐없이 준비했는가 — 사업자등록증, 신분증, 통장 사본은 기본이고, 임대차계약서·4대보험 가입내역 등이 추가로 필요한 경우가 많습니다.",
    "자격 요건을 정확히 확인했는가 — 소상공인 기준(업종별 매출액·상시근로자 수)에 해당하는지 먼저 확인하세요.",
    "중복 지원 제한을 확인했는가 — 이미 받은 지원사업과 중복 불가한 경우가 있습니다.",
    "문의처에 미리 확인했는가 — 애매한 조건은 공고에 나온 담당 부서에 전화로 먼저 물어보는 게 가장 확실합니다.",
    "인증서·계정을 미리 준비했는가 — 공동인증서나 간편인증이 없으면 마감 직전에 발급받느라 시간을 놓칠 수 있습니다.",
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
faq("세무사나 대행업체에 신청을 맡겨도 되나요?", "서류 작성 컨설팅을 받는 것은 문제되지 않지만, 정부지원금·보조금 신청을 &ldquo;수수료를 받고 대신 신청·수령&rdquo;하는 행위는 보조금관리법 등에 저촉될 소지가 있습니다. 최종 신청자 명의와 서명은 반드시 본인이어야 하며, 이 원칙은 이 가이드에도 동일하게 적용됩니다 — 저희 역시 신청을 대행하지 않습니다.")
faq("지원금을 받으면 나중에 세금을 더 내나요?", "지원금의 종류에 따라 과세 대상인 경우와 비과세인 경우가 나뉩니다. 정확한 세무 처리는 이 가이드에서 확정적으로 안내드릴 수 없는 영역이라, 세무사 상담을 권장합니다.")
faq("공고문에 자격 요건이 애매하게 적혀 있으면 어떻게 하나요?", "임의로 해석하지 말고 공고문 하단에 적힌 담당 부서·담당자 연락처로 직접 전화하세요. 신청 전 문의는 감점 요인이 아니라, 오히려 요건에 안 맞는데 신청해서 서류 심사 단계에서 탈락하는 것을 막아줍니다.")
faq("한 번 탈락하면 같은 사업에 다시 신청할 수 없나요?", "대부분의 사업은 회차(분기별, 반기별 등)를 나눠 여러 번 모집합니다. 이번 회차에서 떨어졌다고 해도 다음 회차에 재도전할 수 있는 경우가 많으니, 공고문에서 &ldquo;연간 모집 계획&rdquo;이나 &ldquo;차수&rdquo; 정보를 확인해보세요.")
faq("법인이 아니라 개인사업자인데도 신청할 수 있나요?", "가능한 사업이 대부분입니다. 오히려 소상공인 대상 사업 중에는 법인보다 개인사업자를 주로 겨냥한 것도 많습니다. 다만 일부 기술 기반·R&D 사업은 법인만 대상으로 하는 경우가 있으니 공고문의 &ldquo;신청 자격&rdquo;란에서 사업자 형태 제한을 꼭 확인하세요.")
faq("온라인 신청 중 시스템 오류가 나면 어떻게 하나요?", "화면을 캡처해두고 즉시 담당 부서나 사이트 고객센터에 연락하세요. 마감 시간 직전 오류로 제출하지 못한 경우, 오류 캡처 자료가 있으면 구제받는 사례가 있습니다. 이런 상황을 피하려면 애초에 마감 최소 2~3일 전에 제출을 마치는 게 가장 안전합니다.")
faq("여러 사이트에 각각 회원가입을 다 해야 하나요?", "사이트마다 회원 체계가 분리돼 있어 대부분 개별 가입이 필요합니다. 다만 공동인증서나 간편인증을 미리 만들어두면, 사이트마다 새로 인증 수단을 준비하지 않고 재사용할 수 있어 가입 자체는 빠르게 끝납니다.")
faq("지원사업에 선정된 뒤에도 계속 확인해야 할 게 있나요?", "네. 협약서에 적힌 자금 집행 기한과 정산보고 시점을 캘린더에 미리 표시해두세요. 정산보고를 놓치면 이미 받은 지원금 환수는 물론, 이후 다른 지원사업 신청에도 불이익이 있을 수 있습니다.")

story.append(PageBreak())

# ============================================================
# 9부 — 연간 지원사업 캘린더
# ============================================================
part_page("PART 9", "연간 지원사업 캘린더", "정부지원사업은 연중 아무 때나 균일하게 나오지 않습니다.<br/>시기별로 무엇을 확인해야 하는지 정리했습니다.")

h1("월별 확인 포인트")
callout_box("1~2월 — 한 해의 시작, 가장 중요한 시기", [
    "대부분의 연간 정책자금·지원사업 예산이 새로 편성돼 공고가 집중적으로 쏟아지는 시기입니다.",
    "정책자금(융자)은 예산이 소진되면 연중에도 조기 마감되므로, 이 시기에 가장 먼저 확인해야 합니다.",
    "예비창업패키지·초기창업패키지 등 연간 대표 사업의 1차 모집이 시작되는 경우가 많습니다.",
], numbered=False)
callout_box("3~6월 — 상반기 집행", [
    "1~2월에 놓친 사업의 2차·3차 모집이 이어집니다.",
    "지자체 예산 기반 사업들의 공고가 이 시기에 많이 올라옵니다.",
    "교육·컨설팅 프로그램은 상반기에 기수를 자주 모집합니다.",
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
body("정부지원사업 정보는 계속 바뀝니다. 이 가이드는 &ldquo;어디서, 어떻게 찾는지&rdquo;의 틀을 알려드리는 것이고, 최신 금액·마감일·자격 조건은 항상 해당 공식 사이트에서 본인이 직접 최종 확인해야 합니다.")

story.append(PageBreak())
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
quote("소상공인확인서·신용정보조회 동의서처럼 발급에 며칠씩 걸리는 서류가 있습니다. 마음에 드는 공고를 발견했다면, 서류부터 먼저 신청해두고 사업계획서를 쓰는 순서를 추천합니다.")
story.append(PageBreak())

h1("부록 2. 사이트 주소 모음")

table_data = [
    [Paragraph("사이트", styles["table_head"]), Paragraph("주소", styles["table_head"]), Paragraph("핵심 용도", styles["table_head"])],
    [Paragraph("기업마당", styles["table_cell"]), Paragraph("bizinfo.go.kr", styles["table_cell"]), Paragraph("가장 먼저 볼 통합 공고 사이트", styles["table_cell"])],
    [Paragraph("소상공인24", styles["table_cell"]), Paragraph("sbiz24.kr", styles["table_cell"]), Paragraph("소상공인 전용 지원·바우처 신청", styles["table_cell"])],
    [Paragraph("중소벤처24", styles["table_cell"]), Paragraph("smes.go.kr", styles["table_cell"]), Paragraph("중소기업·스타트업 맞춤 추천", styles["table_cell"])],
    [Paragraph("소상공인시장진흥공단", styles["table_cell"]), Paragraph("semas.or.kr", styles["table_cell"]), Paragraph("정책자금(융자), 교육, 상권정보", styles["table_cell"])],
    [Paragraph("정부24", styles["table_cell"]), Paragraph("gov.kr / plus.gov.kr", styles["table_cell"]), Paragraph("보조금24 — 개인 맞춤 보조금 조회", styles["table_cell"])],
    [Paragraph("거주 지역 시·군·구청", styles["table_cell"]), Paragraph("(지역마다 다름)", styles["table_cell"]), Paragraph("지자체 전용 지원사업, 고시공고", styles["table_cell"])],
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
    [Paragraph("중소기업통합콜센터", styles["table_cell"]), Paragraph("1357", styles["table_cell"]), Paragraph("중소기업·소상공인 지원사업 전반 문의", styles["table_cell"])],
    [Paragraph("소진공 콜센터", styles["table_cell"]), Paragraph("1533-0100", styles["table_cell"]), Paragraph("정책자금(융자), 소상공인24 문의", styles["table_cell"])],
    [Paragraph("정부24 콜센터", styles["table_cell"]), Paragraph("110", styles["table_cell"]), Paragraph("정부24·보조금24 이용 문의", styles["table_cell"])],
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
