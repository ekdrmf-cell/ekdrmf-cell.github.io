# -*- coding: utf-8 -*-
"""
크로스노틱스(천지인운명관) 리포트 PDF 빌더.

2026-08-23 — 이 폴더의 pdf_kit.py는 서비스허브(전자책 13종)의 products/_shared/pdf_kit.py에서
완전히 분리된 독립 사본이다(사용자 지시: 서비스허브와 천지인운명관 사이의 공유 파일을 전부
분리할 것). 이제 이 파일을 자유롭게 고쳐도 전자책에 영향이 없다 — 여기서는
"LLM 합성 결과(report.json) + computed.json → PDF" 매핑 로직을 담당한다.

사용법: python report_kit.py <computed.json> <report.json> <출력 PDF 경로>
(보통은 build_report.py가 이 모듈의 build_pdf()를 직접 import해서 이어붙여 쓴다.)

버그 기록(2026-08-21, 목업 리포트로 실제 PDF를 뽑아보다 발견): Pretendard 폰트는 한자
글리프가 없어 report.json 본문에 "신금(辛金)"처럼 한자가 섞이면 빈칸으로 깨진다(큐텐재팬
전자책 때 일본어 한자로 겪었던 것과 동일한 부류의 버그, EBOOK_HANDOFF.md 20번 참고).
build_report.py의 SYSTEM_PROMPT에 "한자 절대 쓰지 말 것" 규칙을 명시해 방지함.

2026-08-22 대폭 리뉴얼(사용자 피드백 "허술해 보이면 안 된다ㆍ가격대비 분량이 적다"):
pdf_kit.py에 이미 있던 고급 컴포넌트(bar_row/stat_hero/flow_diagram/icon_steps/
summary_box 등)를 지금까지 거의 안 쓰고 있었음 — 실제로 부족했던 건 "쓸 수 있는 도구"가
아니라 "그 도구를 실제로 쓰는 매핑 로직"이었다. 이번에 다음을 추가:
- 목차 미리보기 페이지(report.json의 toc_preview)
- "종합 지표" 페이지 — LLM이 아니라 computed.json의 실측값(오행 분포ㆍ4원소 분포ㆍ체계
  일치도)만으로 그린다. 지어낼 게 없어 환각 위험이 0인 페이지.
- 섹션마다 key_insight(pull_quote)ㆍtakeaways(summary_box) 반영
- action_plan(icon_steps), long_term_strategy의 대운 8구간 타임라인(flow_diagram)
- 리포트 끝에 모든 key_insight를 모은 "한눈에 보기" 요약(이미 나온 문장을 재사용할 뿐이라
  새 환각 위험 없음)

2026-08-22(2차) 운명도감 실제 리포트(1~4번 도감, 8페이지씩) 벤치마킹 후 반영:
- opportunities(기회)/risks(리스크)를 tip_box(파랑)/warn_box(주황)로 항목마다 색을
  나눠 렌더 — 운명도감처럼 "기회/리스크"를 프로즈에 묻지 않고 색으로 스캔 가능하게 함.
- action_plan에 scripts(실제 대화 대사, pull_quote)ㆍreflection_questions(자문 질문,
  callout_box) 추가 — 운명도감의 "이렇게 말해보세요"/"결정 프레임" 기법을 가져오되,
  운명도감에서 실제로 확인한 안티패턴(근거 없는 코호트 %, 구체적 미래 예언)은
  build_report.py SYSTEM_PROMPT 9-C번에서 명시적으로 금지함.
- 가독성: 이 인스턴스(k)의 본문 폰트만 11.8pt→12.4pt, 줄간격 20→21.5로 소폭 확대
  (pdf_kit.py 공용 설정은 그대로 — 다른 상품에 영향 없음).
"""
import json
import sys
from pathlib import Path

from reportlab.lib import colors

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from pdf_kit import PDFKit, extract_subheadings  # noqa: E402  — 2026-08-23: 서비스허브 공유 파일에서 분리된 이 폴더의 로컬 사본

SYSTEM_LABEL = {"saju": "사주", "astrology": "서양 점성술", "tarot": "타로"}

# 2026-08-23 추가 — PDF 퀄리티 개선(사용자 요청: "PDF를 더 고급스럽게"). 웹사이트 로고 마크의
# 원 3개 색(index.html <svg class="logo-mark"> 그대로)을 PDF 챕터 배지ㆍ표지 엠블럼에도 써서
# 웹ㆍPDF 브랜드를 통일한다. pdf_kit.py는 그대로 두고(다른 전자책 영향 없음) chapter_header()/
# build()에 새로 생긴 선택적 accent/brand_emblem 파라미터만 여기서 사용.
SYSTEM_ACCENT = {"saju": "#e8562f", "astrology": "#6d4aff", "tarot": "#0a7d5e"}
CROSSNOTICS_EMBLEM = (SYSTEM_ACCENT["saju"], SYSTEM_ACCENT["astrology"], SYSTEM_ACCENT["tarot"])

# 오행ㆍ4원소 막대색 — pdf_kit.py의 ACCENT 계열과 어울리되 항목별로 구분되게 직접 지정.
OHENG_COLOR = {
    "목": colors.HexColor("#2f9e5c"), "화": colors.HexColor("#d9501f"),
    "토": colors.HexColor("#b8860b"), "금": colors.HexColor("#8a8f9c"),
    "수": colors.HexColor("#2f6fd9"),
}
ELEMENT_COLOR = {
    "불": colors.HexColor("#d9501f"), "땅": colors.HexColor("#8a6d3b"),
    "바람": colors.HexColor("#2f9e8c"), "물": colors.HexColor("#2f6fd9"),
}


def _oheng_bars(k, saju):
    order = ["목", "화", "토", "금", "수"]
    counts = saju.get("oheng_count") or {}
    max_v = max(1, sum(counts.get(o, 0) for o in order))
    for o in order:
        k.bar_row(o, counts.get(o, 0), max_v, OHENG_COLOR[o], unit="개")


def _element_bars(k, astrology):
    order = ["불", "땅", "바람", "물"]
    counts = astrology.get("element_count") or {}
    max_v = max(1, sum(counts.get(e, 0) for e in order))
    for e in order:
        k.bar_row(e, counts.get(e, 0), max_v, ELEMENT_COLOR[e], unit="개")


def _render_section(k, ch, sec, computed, show_receipt):
    """system_sections 항목 하나 — key_insight(pull_quote)ㆍ원본 계산값ㆍtakeaways(summary_box)까지
    전부 반영해서 한 섹션을 여러 시각 요소로 풍부하게 채운다.

    2026-08-24 수정 — 사용자가 실제 PDF에서 발견한 버그: SINGLE 이상 티어는 사주 한
    체계를 system_sections 여러 개(예: "네 기둥 총론"/"오행 균형"/"대운 흐름"/"실전
    포인트")로 나눠 쓰는데(build_report.py 8번 규칙), 예전 코드는 그 사주 섹션마다
    매번 똑같은 오행 막대그래프를 다시 그렸다 — "종합 지표" 페이지에서 이미 완전한
    형태로 한 번 보여준 것과 완전히 동일한 차트가 문서 안에 여러 번 반복되고, 심지어
    페이지 경계에서 어색하게 잘리는 경우까지 있었다(FREE 티어 실사용 테스트에서 실제
    확인). 오행/4원소 분포는 "종합 지표"에 이미 있으므로 여기서는 완전히 제거하고,
    타로 "뽑힌 카드" 목록만(다른 곳에 안 나오는 정보라 유지) 그 체계의 **첫 섹션에서
    한 번만** 보여준다(show_receipt=False인 두 번째 이후 섹션에서는 생략)."""
    sys_color = SYSTEM_ACCENT.get(sec["system"])
    k.chapter_header(ch, sec["heading"], eyebrow=SYSTEM_LABEL.get(sec["system"], sec["system"].upper()),
                      accent=sys_color, accent2=sys_color)
    if sec.get("key_insight"):
        k.pull_quote(sec["key_insight"])
    # 2026-08-24 추가 — body() 안의 "## 소제목"을 그대로 재사용해 챕터 맨 위에 미니 목차
    # 칩을 보여준다(사용자 요청: 글만 있지 않고 이해를 돕는 도구를 더 써달라).
    k.mini_toc(extract_subheadings(sec["body"]), color=sys_color)
    k.body(sec["body"])

    if show_receipt and sec["system"] == "tarot" and computed.get("tarot"):
        cards = [f"{d['position']}: {d['card_name']}({d['orientation']})" for d in computed["tarot"]["draws"]]
        k.callout_box("뽑힌 카드", cards)

    if sec.get("takeaways"):
        k.summary_box(f"{sec['heading']} — 핵심 정리", sec["takeaways"])


def build_pdf(computed, report, out_path, product_name):
    """
    @param computed: run.js가 만든 computed.json (dict)
    @param report: build_report.py가 LLM으로 만든 report.json (dict)
    @param out_path: 출력 PDF 경로
    @param product_name: 표지에 쓸 상품명(예: "천지인운명관 — 장기 인생 전략 프리미엄")
    """
    k = PDFKit(out_path, title=f"{product_name} — {computed['customer'].get('name', '고객님')}")

    # 2026-08-22 가독성 개선: pdf_kit.py(공용, 전자책 13종이 같이 씀) 자체는 건드리지 않고,
    # 이 report_kit 인스턴스(k)의 스타일 딕셔너리만 국소적으로 조정한다 — 다른 상품에는
    # 전혀 영향 없음. 운명도감 벤치마킹 후 "가격대비 분량ㆍ가독성"을 검토한 결과, 본문
    # 폰트가 살짝 작고(11.8pt) 줄간격도 좁아(leading 20) 20~30페이지 분량을 읽기엔
    # 빽빽하다고 판단해 소폭 키움(가독성ㆍ신뢰감 둘 다 목적 — 너무 커지면 오히려 유치해
    # 보이므로 과하게 키우지 않음).
    k.styles["body"].fontSize = 12.4
    k.styles["body"].leading = 21.5
    k.styles["h2"].spaceBefore = 16

    k.cover(
        kicker="CHUNJIIN PERSONAL REPORT",
        title_html=product_name,
        subtitle=f"{computed['customer'].get('name', '고객님')}님을 위한 개인 맞춤 진단",
        tagline="사주ㆍ점성술ㆍ타로 — 독립 계산 후 교차 검증한 결과만 담았습니다",
    )

    # ---- 목차 미리보기(scope full/premium만 채워짐) ----
    if report.get("toc_preview"):
        k.h1("목차")
        for i, item in enumerate(report["toc_preview"], 1):
            k.toc_line(f"{i:02d}   {item}")
        k.spacer(16)

    k.h1("들어가며")
    k.body(report["intro"])

    # ---- 사주 네 기둥 카드 — 2026-08-24 신설(경쟁사 디자인 벤치마킹, 위 build_pdf 주석
    # 참고). saju가 있으면 리포트 도입부에서 바로 이 손님의 네 기둥을 시각적으로 보여준다.
    # 전부 computed.json 실측값이라 환각 위험 없음. 한자(甲戌 등)는 폰트가 못 그리므로
    # 한글 표기(갑술)만 씀.
    # 2026-08-24(2차) — 사용자 지적: "년주는 뭐고 월주는 뭐야, 기둥이 무슨 뜻인지 애초에
    # 설명했어야 하지 않나." "년주"ㆍ"월주"ㆍ"기둥" 같은 말이 리포트 전체에서 계속 쓰이는데
    # 정작 그 뜻을 한 번도 설명한 적이 없었음(개별 신살 이름은 풀이해주면서 정작 이 리포트의
    # 가장 기본이 되는 틀인 "기둥"은 빠뜨림) — 이 카드가 나오는 바로 이 자리, 리포트에서
    # "기둥"이라는 말이 처음 등장하는 지점에서 한 번 짧게 짚어준다.
    _customer_name = computed["customer"].get("name", "고객")
    _pillars = (computed.get("saju") or {}).get("pillars")
    if _pillars:
        k.body(
            "사주는 태어난 연도ㆍ월ㆍ일ㆍ시, 이 네 시점 각각을 **'기둥'**이라고 부릅니다. "
            "그래서 태어난 해는 **년주**, 달은 **월주**, 날은 **일주**, 시간은 **시주**라고 하고, "
            f"이 네 기둥을 합쳐 흔히 말하는 **'사주팔자'**가 됩니다. 아래는 {_customer_name}님의 네 기둥입니다."
        )
        _pillar_items = []
        for _key, _label in [("year", "년주"), ("month", "월주"), ("day", "일주"), ("hour", "시주")]:
            _p = _pillars.get(_key)
            if not _p:
                continue
            _pillar_items.append({
                "label": _label, "text": _p["ganzhi_ko"],
                "sub": f"{_p['gan_oheng']}·{_p['zhi_oheng']}",
                "color": OHENG_COLOR.get(_p["gan_oheng"]),
            })
        if _pillar_items:
            k.four_pillars(_pillar_items)

    # ---- 종합 지표 — computed.json 실측값만 사용(LLM 개입 없음, 환각 위험 0) ----
    saju = computed.get("saju")
    astrology = computed.get("astrology")
    correlation = computed.get("correlation") or {}
    has_indicators = bool(saju or astrology or correlation.get("mode") == "cross_correlation")
    if has_indicators:
        k.h1("종합 지표")
        if correlation.get("mode") == "cross_correlation" and correlation.get("agreement_score") is not None:
            k.stat_hero(
                f"{int(round(correlation['agreement_score'] * 100))}%",
                "체계 일치도",
                sublabel=f"중심 기운: {correlation.get('dominant_axis', '-')}",
            )
        if saju and saju.get("oheng_count"):
            k.h2("사주 오행 분포")
            _oheng_bars(k, saju)
            if saju.get("dominant_elements"):
                k.body(f"우세 오행: {', '.join(saju['dominant_elements'])}" + (
                    f" · 부족 오행: {', '.join(saju['missing_elements'])}" if saju.get("missing_elements") else ""
                ))
        if astrology and astrology.get("element_count"):
            k.h2("점성술 4원소 분포")
            _element_bars(k, astrology)
        # 2026-08-23 추가 — 궁합 계산 엔진(gunghap.js) 결과 시각화. computed.json.gunghap은
        # LLM이 아니라 gunghap.js가 결정론적으로 계산한 점수이므로(환각 위험 0), 사주 오행
        # 분포와 같은 방식으로 여기서 직접 렌더링한다 — 궁합 질문이 있을 때만 존재하는 필드.
        gunghap = computed.get("gunghap")
        if gunghap:
            rel_label = gunghap.get("relationship_type_label") or "연인ㆍ부부"
            k.h2(f"궁합 점수 — {rel_label}")
            k.stat_hero(
                f"{gunghap['score']}점",
                gunghap.get("score_label", ""),
                sublabel="일간ㆍ일지ㆍ띠ㆍ오행 보완을 종합한 참고 지표(여러 궁합 판단 기준 중 하나)",
            )
            if gunghap.get("highlights"):
                k.callout_box("궁합 근거", gunghap["highlights"])
            if gunghap.get("disclaimer"):
                k.callout_box("참고", [gunghap["disclaimer"]])
        # 2026-08-23 추가 — 신살(shensha.js) 결과도 같은 방식으로 시각화. LLM 개입 없이
        # saju.shensha의 present/found_in만으로 그린다(환각 위험 0).
        shensha = saju.get("shensha") if saju else None
        if shensha:
            # shensha.js가 주는 found_in은 "year"/"month"/"day"/"hour" 영문 키라 그대로 PDF에
            # 노출하면 안 됨(2026-08-23 시각 점검에서 발견) — 한글 기둥 명칭으로 옮겨서 표기.
            # 2026-08-24 수정 — 사용자 피드백("신살이니 화개살이니 뭐니 그게 뭔지 설명이
            # 없다"): shensha[key]["meaning"]에 뜻풀이가 이미 계산되어 있었는데 여기서 안 쓰고
            # "있음" 한 마디만 보여주고 있었다. 용어가 처음 등장하는 바로 이 자리에서 뜻까지
            # 함께 굵게 강조해 보여준다(**마크는 pdf_kit.py의 _md()가 굵게+강조색으로 렌더).
            PILLAR_KO = {"year": "년주", "month": "월주", "day": "일주", "hour": "시주"}
            present_items = [
                f"**{label}**: {', '.join(PILLAR_KO.get(p, p) for p in shensha[key]['found_in'])} 기둥에 있음 — "
                f"{shensha[key].get('meaning', '')}"
                for key, label in [("taohua", "도화살"), ("yeokma", "역마살"), ("hwagae", "화개살"), ("hongyeom", "홍염살")]
                if shensha.get(key, {}).get("present")
            ]
            if present_items:
                k.h2("신살")
                # 2026-08-24 추가 — 사용자 지적: "신살 뜻이 뭔지 나는 아직도 모르겠다"
                # (개별 화개살ㆍ홍염살 뜻은 풀어줬지만, 정작 "신살"이라는 상위 분류 자체를
                # 한 번도 설명한 적이 없었음 — 위 "기둥" 설명 누락과 같은 유형의 실수).
                k.body(
                    "**신살**은 사주에서 유독 눈에 띄는 특징에 붙는 이름입니다. 이름 때문에 "
                    "무섭게 들릴 수 있지만 나쁘다는 뜻이 아니라, 그 사람만의 두드러진 기질이나 "
                    f"매력을 가리키는 표현에 가깝습니다. {_customer_name}님의 사주에서 발견된 "
                    "신살은 다음과 같습니다."
                )
                k.callout_box("이 손님 사주에 있는 신살", present_items)
        k.spacer(10)

    # ---- 체계별 섹션(key_insight/takeaways까지 전부 반영) ----
    ch = 1
    seen_systems = set()
    for sec in report["system_sections"]:
        show_receipt = sec["system"] not in seen_systems
        seen_systems.add(sec["system"])
        _render_section(k, ch, sec, computed, show_receipt)
        ch += 1

    if report.get("cross_analysis"):
        # 2026-08-23 추가 — 세 체계가 겹치는 지점을 다루는 챕터라, 개별 체계 색이 아니라
        # "종합"을 뜻하는 골드 톤(웹사이트 --gold 계열을 인쇄용으로 짙게 조정)을 씀.
        k.chapter_header(ch, report["cross_analysis"]["heading"], eyebrow="CROSS-ANALYSIS",
                          accent="#a67c1e", accent2="#a67c1e")
        corr = computed["correlation"]
        if corr.get("agreement_score") is not None:
            k.pull_quote(
                f"체계 일치도 {int(round(corr['agreement_score'] * 100))}% — "
                f"중심 기운은 '{corr['dominant_axis']}'",
            )
        k.body(report["cross_analysis"]["body"])
        ch += 1

    # ---- 포착할 기회 / 예측 리스크 — 운명도감 벤치마킹(2026-08-22)에서 가져온 구조.
    # 프로즈로 묻어두지 않고 tip_box(파랑ㆍ✓)/warn_box(주황ㆍ⚠)로 항목마다 색을 나눠
    # 한눈에 스캔되게 한다 — "색으로 가독성을 높여달라"는 요청에 대한 핵심 대응. ----
    if report.get("opportunities"):
        k.chapter_header(ch, "포착할 기회", eyebrow="OPPORTUNITIES")
        for i, opp in enumerate(report["opportunities"], 1):
            k.tip_box([opp["body"]], header=opp["title"], number=i)
        ch += 1

    if report.get("risks"):
        k.chapter_header(ch, "예측 리스크 & 대비책", eyebrow="RISK FORECAST")
        for i, risk in enumerate(report["risks"], 1):
            k.warn_box([risk["body"]], header=risk["title"], number=i)
        ch += 1

    if report.get("action_plan") and report["action_plan"].get("steps"):
        k.chapter_header(ch, report["action_plan"].get("heading") or "실전 액션 플랜", eyebrow="ACTION PLAN")
        steps = report["action_plan"]["steps"][:6]
        k.icon_steps([(s["label"], s["desc"]) for s in steps])

        # 대화 스크립트 — 운명도감 벤치마킹에서 확인한 "실제로 이렇게 말해보세요" 기법.
        # pull_quote(대사) + attribution(상황)로 잡지 인용구처럼 보이게 렌더.
        scripts = report["action_plan"].get("scripts") or []
        if scripts:
            k.h2("결정의 순간, 이렇게 말해보세요")
            for s in scripts:
                k.pull_quote(s["line"], attribution=s["situation"])

        # 자문 질문 — 운명도감의 "결정 프레임" 기법. 질문+왜 이 사람에게 중요한지를
        # 한 박스에 모아 스스로 점검할 수 있게 함.
        reflections = report["action_plan"].get("reflection_questions") or []
        if reflections:
            k.callout_box(
                "스스로에게 물어보세요",
                [f"{q['question']} — {q['note']}" for q in reflections],
                numbered=True,
            )
        ch += 1

    if report.get("long_term_strategy"):
        lts = report["long_term_strategy"]
        k.chapter_header(ch, "장기 인생 전략", eyebrow="LONG-TERM STRATEGY")
        dae_yun = (computed.get("saju") or {}).get("dae_yun") or []
        if dae_yun:
            k.h2("대운 8구간 타임라인")
            k.flow_diagram([f"{d['start_age']}세 {d['ganzhi_ko']}" for d in dae_yun])
        if lts.get("decade_roadmap"):
            k.h1(lts["decade_roadmap"]["heading"])
            k.body(lts["decade_roadmap"]["body"])
        if lts.get("lifetime_design"):
            k.h1(lts["lifetime_design"]["heading"])
            k.body(lts["lifetime_design"]["body"])
        if lts.get("second_act"):
            k.h1(lts["second_act"]["heading"])
            k.body(lts["second_act"]["body"])
        ch += 1

    # ---- 질문 답변 — 2026-08-23 재설계: 질문마다 answerability(direct/redirected/
    # unanswerable)를 먼저 판정하게 했다. redirected/unanswerable인데 그 사실을 숨기고
    # 마치 원래 질문에 답한 것처럼 보이면 안 되므로, 그 경우 quote()로 "왜 문자 그대로는
    # 답할 수 없는지"를 본문보다 먼저, 눈에 띄게 보여준 뒤에 본문을 이어붙인다. ----
    if report.get("question_answers"):
        k.chapter_header(ch, "질문에 대한 답변", eyebrow="Q&A")
        for i, qa in enumerate(report["question_answers"], 1):
            k.h2(f"Q{i}. {qa['question']}")
            if qa.get("answerability") in ("redirected", "unanswerable") and qa.get("unanswerable_reason"):
                k.quote(f"※ {qa['unanswerable_reason']}")
            k.body(qa["body"])
        ch += 1

    # ---- 한눈에 보기 — 지금까지 나온 key_insight를 한 곳에 모아 다시 보여준다(새 문장을
    # 짓는 게 아니라 이미 만든 문장을 재사용하는 것뿐이라 환각 위험이 늘지 않음). ----
    all_insights = [sec["key_insight"] for sec in report["system_sections"] if sec.get("key_insight")]
    if len(all_insights) >= 2:
        k.h1("한눈에 보기")
        k.summary_box("이 리포트의 핵심 통찰", all_insights)

    k.h1("마치며")
    k.body(report["closing"])

    # 2026-08-24 제거 — 사용자 명확한 지시: "고객에게 전달될 파일 안에는 절대 상품에 따른
    # 내용 이외의 내용이 포함되지 않도록 해." 법적 안내 문구(정보 제공 목적ㆍ전문가 상담
    # 권고 등)는 PDF 안에 넣지 않고, 사이트 하단(문의ㆍ개인정보처리방침 옆)으로 옮긴다 —
    # report["disclaimer"] 필드 자체를 스키마에서 제거함(build_report.py REPORT_SCHEMA
    # 참고, LLM에게 더 이상 생성을 요청하지 않음).

    # 2026-08-24 수정 — 사용자 지시: "마지막 부분은 천지인운명관까지는 좋은데 내용이
    # 별로야. 고객명, 상품명에 따른 진단입니다. 정도로 해줘." 회사 소개 문구 대신 이
    # 리포트가 누구를 위한 무엇인지만 짧게 밝힘. product_name은 이미 "천지인운명관 FREE —
    # 오늘의 사주 미니 진단"처럼 브랜드명이 앞에 붙어있으므로, 그 뒷부분(상품 설명)만 뽑아
    # "고객명님을 위한 상품설명입니다" 형태로 만든다(브랜드명 중복 방지).
    _tier_desc = product_name.split(" — ", 1)[-1]
    k.build(
        footer_tagline=f"{_customer_name}님을 위한 {_tier_desc}입니다.",
        brand_emblem=CROSSNOTICS_EMBLEM,
        # 2026-08-23 발견 — watermark_text 기본값이 "서비스허브"(상위 우산 브랜드)라 표지에
        # "CHUNJIIN PERSONAL REPORT"라고 써놓고 워터마크는 다른 브랜드명이 반복되는
        # 불일치가 있었음(시각 점검으로 발견). 크로스노틱스는 자체 브랜드명으로 오버라이드.
        watermark_text="천지인운명관 · 무단 전재·재배포 금지",
    )
    return out_path


def main():
    if len(sys.argv) < 4:
        print("사용법: python report_kit.py <computed.json> <report.json> <출력 PDF 경로>")
        sys.exit(1)
    computed = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    report = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    out_path = sys.argv[3]

    from catalog_names import tier_product_name  # 같은 폴더의 작은 헬퍼(아래 참고)
    product_name = tier_product_name(computed.get("tier"))

    build_pdf(computed, report, out_path, product_name)
    print(f"PDF 생성 완료: {out_path}")


if __name__ == "__main__":
    main()
