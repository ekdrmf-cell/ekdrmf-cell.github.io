# -*- coding: utf-8 -*-
"""정부지원금 찾기 가이드 PDF 빌드 스크립트"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    HRFlowable, KeepTogether, ListFlowable, ListItem
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

FONT = "HYGothic-Medium"
pdfmetrics.registerFont(UnicodeCIDFont(FONT))

ACCENT = colors.HexColor("#5a3fd6")
ACCENT_SOFT = colors.HexColor("#efeafc")
TEXT_DARK = colors.HexColor("#1f2333")
TEXT_DIM = colors.HexColor("#5b6178")
BORDER = colors.HexColor("#d9d5f0")

OUT = r"C:\Users\nalla\Desktop\수익화허브\products\gov-subsidy-guide\정부지원금_찾기_가이드.pdf"

doc = SimpleDocTemplate(
    OUT, pagesize=A4,
    topMargin=22 * mm, bottomMargin=22 * mm,
    leftMargin=20 * mm, rightMargin=20 * mm,
    title="소상공인·1인사업자를 위한 정부지원금 찾기 가이드",
    author="수익화허브",
)

styles = {
    "title": ParagraphStyle("title", fontName=FONT, fontSize=25, leading=34,
                             textColor=TEXT_DARK, alignment=TA_CENTER, spaceAfter=10),
    "subtitle": ParagraphStyle("subtitle", fontName=FONT, fontSize=12.5, leading=19,
                                textColor=TEXT_DIM, alignment=TA_CENTER, spaceAfter=4),
    "cover_meta": ParagraphStyle("cover_meta", fontName=FONT, fontSize=10, leading=15,
                                  textColor=TEXT_DIM, alignment=TA_CENTER),
    "h1": ParagraphStyle("h1", fontName=FONT, fontSize=18, leading=24,
                          textColor=ACCENT, spaceBefore=6, spaceAfter=10),
    "h2": ParagraphStyle("h2", fontName=FONT, fontSize=13.5, leading=19,
                          textColor=TEXT_DARK, spaceBefore=14, spaceAfter=6),
    "body": ParagraphStyle("body", fontName=FONT, fontSize=10.3, leading=17,
                            textColor=TEXT_DARK, spaceAfter=8, alignment=TA_LEFT),
    "quote": ParagraphStyle("quote", fontName=FONT, fontSize=11.5, leading=18,
                             textColor=ACCENT, alignment=TA_LEFT, spaceBefore=6, spaceAfter=6,
                             leftIndent=10, borderColor=ACCENT, borderWidth=0,
                             backColor=ACCENT_SOFT, borderPadding=10),
    "small": ParagraphStyle("small", fontName=FONT, fontSize=8.7, leading=13.5,
                             textColor=TEXT_DIM, spaceAfter=4),
    "list": ParagraphStyle("list", fontName=FONT, fontSize=10.3, leading=16.5,
                            textColor=TEXT_DARK, spaceAfter=4),
    "toc": ParagraphStyle("toc", fontName=FONT, fontSize=11.5, leading=22,
                           textColor=TEXT_DARK, alignment=TA_LEFT),
}

story = []

# ---------- 표지 ----------
story.append(Spacer(1, 55 * mm))
story.append(Paragraph("소상공인·1인사업자를 위한", styles["subtitle"]))
story.append(Paragraph("정부지원금 찾기 가이드", styles["title"]))
story.append(Spacer(1, 6))
story.append(HRFlowable(width="30%", thickness=1.4, color=ACCENT, hAlign="CENTER", spaceBefore=8, spaceAfter=14))
story.append(Paragraph("흩어진 지원사업 정보를 어디서, 어떻게 찾아야 하는지 정리한<br/>실전 내비게이션 가이드", styles["cover_meta"]))
story.append(Spacer(1, 60 * mm))
story.append(Paragraph("수익화허브", styles["cover_meta"]))
story.append(PageBreak())


def h1(text):
    story.append(Paragraph(text, styles["h1"]))
    story.append(HRFlowable(width="100%", thickness=0.7, color=BORDER, spaceAfter=10))


def h2(text):
    story.append(Paragraph(text, styles["h2"]))


def body(text):
    story.append(Paragraph(text, styles["body"]))


def quote(text):
    story.append(Paragraph(text, styles["quote"]))


def callout_box(title_text, items, numbered=False):
    rows = []
    header = Paragraph(f"<b>{title_text}</b>", ParagraphStyle(
        "boxhead", fontName=FONT, fontSize=11, leading=15, textColor=colors.white))
    rows.append([header])
    for i, item in enumerate(items, 1):
        prefix = f"{i}. " if numbered else "☐  "
        rows.append([Paragraph(prefix + item, ParagraphStyle(
            "boxitem", fontName=FONT, fontSize=10, leading=15.5, textColor=TEXT_DARK))])
    t = Table(rows, colWidths=[160 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("BACKGROUND", (0, 1), (-1, -1), ACCENT_SOFT),
        ("TOPPADDING", (0, 0), (-1, 0), 7),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 1), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
        ("BOX", (0, 0), (-1, -1), 0.8, BORDER),
        ("LINEBELOW", (0, 0), (-1, 0), 0.8, BORDER),
    ]))
    story.append(t)
    story.append(Spacer(1, 12))


def site_box(name, url, desc, highlight=False):
    rows = [[Paragraph(f"<b>{name}</b>  <font color='#5b6178' size=8.5>{url}</font>", ParagraphStyle(
        "sitehead", fontName=FONT, fontSize=11, leading=15, textColor=ACCENT if highlight else TEXT_DARK)),],
        [Paragraph(desc, styles["body"])]]
    t = Table(rows, colWidths=[160 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#faf9ff") if not highlight else ACCENT_SOFT),
        ("BOX", (0, 0), (-1, -1), 0.8, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    story.append(Spacer(1, 8))


# ---------- 이 가이드를 왜 만들었나 ----------
h1("이 가이드를 왜 만들었나")
body("크몽, 스레드, 블라인드에서 소상공인·1인사업자들의 글을 직접 찾아봤습니다. 반복해서 나온 말이 있었습니다.")
quote("&ldquo;제도가 어려운 게 아니라, 정보가 여기저기 흩어져 있고 용어가 낯설어서 못 찾는다.&rdquo;")
body("실제로 정부지원사업은 중앙부처, 지자체, 공공기관을 다 합치면 수천 개가 있고, 사이트도 제각각입니다. 어떤 건 기업마당에, 어떤 건 소상공인24에, 어떤 건 지자체 홈페이지에만 올라옵니다. 사업하는 사람 입장에서는 &ldquo;내가 받을 수 있는 게 뭔지&rdquo; 알아내는 것 자체가 일이 됩니다.")
body("이 가이드는 그 흩어진 정보를 한곳에 정리해서, &ldquo;어디를 봐야 하는지&rdquo; &ldquo;내 상황에 맞는 걸 어떻게 찾는지&rdquo;를 빠르게 알 수 있도록 만들었습니다.")

callout_box("이 가이드가 아닌 것", [
    "지원금 신청을 대신 해드리는 대행 서비스가 아닙니다. 정보를 정리해서 드릴 뿐이고, 실제 신청은 반드시 본인이 직접 해야 합니다. (관련 법상 수수료를 받는 대리 신청은 문제가 될 수 있습니다.)",
    "구체적인 지원금액·마감일은 시기마다 바뀌기 때문에, 이 책은 &ldquo;정확한 금액표&rdquo;가 아니라 &ldquo;어디서 어떻게 찾는지&rdquo;에 집중합니다. 최신 금액과 마감일은 반드시 공식 사이트에서 본인이 직접 확인해야 합니다.",
])

story.append(PageBreak())

# ---------- 1장 ----------
h1("1장. 핵심 사이트 지도 — 어디를 봐야 하나")
body("정부지원사업 정보가 모여 있는 대표 사이트들입니다. 처음 찾아본다면 이 순서로 보는 걸 추천합니다.")

site_box("① 기업마당", "bizinfo.go.kr",
         "중소벤처기업부가 운영하는 사이트로, 중앙부처와 지자체의 지원사업 공고가 가장 폭넓게 모여 있습니다. &ldquo;정책정보 &gt; 지원사업 공고&rdquo; 메뉴에서 업종·지역·사업 목적으로 검색할 수 있습니다. <b>가장 먼저 확인할 사이트.</b>",
         highlight=True)
site_box("② 소상공인24", "sbiz24.kr",
         "소상공인 전문 지원 정보 사이트입니다. 소상공인 자격 여부, 정책자금, 컨설팅, 교육 등 소상공인에 특화된 지원을 확인할 수 있습니다.")
site_box("③ 중소벤처24", "smes.go.kr",
         "중소기업·스타트업 대상 지원사업, K-스타트업 관련 정보가 모여 있습니다. 스타트업이나 기술 기반 창업이라면 여기를 함께 확인하세요.")
site_box("④ 소상공인시장진흥공단(소진공)", "semas.or.kr",
         "소상공인 정책자금(융자)을 직접 운영하는 기관입니다. 정책자금이 필요하다면 반드시 확인해야 하는 사이트입니다.")
site_box("⑤ 정부24 — 보조금24", "gov.kr",
         "개인·사업자가 받을 수 있는 각종 보조금을 한 번에 조회할 수 있는 서비스입니다. 본인 정보를 입력하면 대상이 될 수 있는 보조금을 추천해주는 기능도 있습니다.")
site_box("⑥ 지자체(시·군·구) 홈페이지", "",
         "같은 업종이어도 사는 지역에 따라 별도로 받을 수 있는 지원사업이 따로 있습니다. 거주 지역 시청/구청 홈페이지의 &ldquo;고시공고&rdquo; 또는 &ldquo;지원사업&rdquo; 메뉴를 꼭 함께 확인하세요. 중앙 사이트에는 안 올라오는 경우가 많습니다.")
site_box("⑦ (참고) 민간 통합검색 사이트", "",
         "여러 공공 사이트의 공고를 매일 모아서 보여주는 민간 서비스도 있습니다. 공식 사이트를 일일이 도는 게 번거롭다면 참고용으로 함께 쓰면 좋습니다. 다만 최종 신청과 정확한 조건 확인은 항상 공식 사이트에서 해야 합니다.")

story.append(PageBreak())

# ---------- 2장 ----------
h1("2장. 내 상황별 체크리스트")
body("지원사업은 &ldquo;업종&rdquo;, &ldquo;사업 단계&rdquo;, &ldquo;필요한 목적&rdquo; 세 가지 축으로 나눠보면 훨씬 빠르게 좁혀집니다.")

h2("축 1 — 사업 단계")
callout_box("해당하는 항목을 확인하세요", [
    "예비창업자 (아직 사업자등록 전)",
    "창업 1년 이내",
    "창업 3년 이내",
    "창업 3년 이상 / 재도약 준비",
    "폐업 후 재도전 준비",
])
body("→ 예비창업자·초기창업이라면 &ldquo;예비창업패키지&rdquo;, &ldquo;초기창업패키지&rdquo; 계열 사업을, 3년 이상이라면 &ldquo;성장기반자금&rdquo;, &ldquo;재도약&rdquo; 계열 사업을 우선 검색하세요.")

h2("축 2 — 필요한 목적")
callout_box("무엇이 필요한지 확인하세요", [
    "운영자금(인건비·임차료 등)이 필요하다 → 정책자금(융자) 계열",
    "시설·장비 구입이 필요하다 → 시설자금, 스마트상점/스마트공장 계열",
    "온라인 진출·마케팅이 필요하다 → 온라인 판로지원, 디지털 전환 계열",
    "폐업/재창업을 준비 중이다 → 희망리턴패키지, 재도전 계열",
    "컨설팅·교육이 필요하다 → 소상공인 컨설팅, 아카데미 계열",
])

h2("축 3 — 업종/대상 특성")
callout_box("해당 사항을 확인하세요", [
    "청년(만 39세 이하) 대표 → 청년창업 전용 사업 다수",
    "여성 대표 → 여성기업 전용 사업",
    "특정 지역(비수도권 등) → 지역 균형 관련 가산점/전용 사업",
    "기술·제조 기반 → 중소벤처24, 창업진흥원 계열",
])
body("이 세 가지 축에서 본인에게 해당하는 항목을 체크한 뒤, 1장의 사이트에서 그 키워드로 검색하면 훨씬 빠르게 찾을 수 있습니다.")

story.append(PageBreak())

# ---------- 3장 ----------
h1("3장. 사이트별 검색 키워드 모음")
body("사이트 검색창에 아래 키워드를 그대로 넣어보세요.")
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
    "(거주 지역명) 소상공인 지원사업 — 반드시 지역명을 넣어 검색",
])

# ---------- 4장 ----------
h1("4장. 신청 전 체크리스트 — 떨어지는 이유부터 피하기")
body("여러 사례를 찾아보니, 지원사업에서 떨어지는 이유는 대부분 비슷했습니다. 신청 전에 아래를 꼭 확인하세요.")
callout_box("신청 전 최종 점검", [
    "모집공고를 끝까지 읽었는가 — 지원대상·제외대상 조건만 봐도 걸러지는 경우가 많습니다.",
    "마감일 직전에 신청하지 않는가 — 마감 임박에는 접속 폭주, 서류 오류로 제출 자체가 안 되는 경우가 있습니다. 최소 2~3일 여유를 두세요.",
    "사업계획서를 성의 있게 썼는가 — 첫 페이지에서 다른 신청자와의 차별점이 보여야 합니다.",
    "증빙서류를 빠짐없이 준비했는가 — 사업자등록증, 신분증, 통장 사본은 기본이고, 임대차계약서·4대보험 가입내역 등이 추가로 필요한 경우가 많습니다.",
    "자격 요건을 정확히 확인했는가 — 소상공인 기준(업종별 매출액·상시근로자 수)에 해당하는지 먼저 확인하세요.",
    "중복 지원 제한을 확인했는가 — 이미 받은 지원사업과 중복 불가한 경우가 있습니다.",
    "문의처에 미리 확인했는가 — 애매한 조건은 공고에 나온 담당 부서에 전화로 먼저 물어보는 게 가장 확실합니다.",
], numbered=True)

story.append(PageBreak())

# ---------- 마무리 ----------
h1("마무리 — 이 가이드를 어떻게 쓰면 좋을까")
callout_box("3단계로 활용하세요", [
    "2장 체크리스트로 내 상황을 먼저 정리하세요.",
    "1장 사이트 지도에서 해당하는 사이트 2~3곳을 골라 3장의 키워드로 검색하세요.",
    "마음에 드는 공고를 찾으면 4장 체크리스트로 신청 전 준비를 점검하세요.",
], numbered=True)
body("정부지원사업 정보는 계속 바뀝니다. 이 가이드는 &ldquo;어디서, 어떻게 찾는지&rdquo;의 틀을 알려드리는 것이고, 최신 금액·마감일·자격 조건은 항상 해당 공식 사이트에서 본인이 직접 최종 확인해야 합니다.")
story.append(Spacer(1, 20))
story.append(HRFlowable(width="100%", thickness=0.7, color=BORDER, spaceAfter=10))
story.append(Paragraph("수익화허브 · 데이터로 검증된 빈틈만 골라 만듭니다", styles["small"]))


def add_page_number(canvas, doc_):
    canvas.saveState()
    canvas.setFont(FONT, 8.5)
    canvas.setFillColor(TEXT_DIM)
    canvas.drawCentredString(A4[0] / 2, 12 * mm, str(doc_.page))
    canvas.restoreState()


doc.build(story, onFirstPage=lambda c, d: None, onLaterPages=add_page_number)
print("done:", OUT)
