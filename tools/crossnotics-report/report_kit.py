# -*- coding: utf-8 -*-
"""
크로스노틱스 리포트 PDF 빌더 — products/_shared/pdf_kit.py(전자책 13종에서 검증된 브랜드
PDF 빌더)를 그대로 가져다 쓴다. pdf_kit.py 자체는 건드리지 않고(다른 상품에 영향 안 주려고),
여기서 "LLM 합성 결과(report.json) + computed.json → PDF" 매핑 로직만 담당한다.

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

SHARED_DIR = Path(__file__).resolve().parent.parent.parent / "products" / "_shared"
sys.path.insert(0, str(SHARED_DIR))
from pdf_kit import PDFKit  # noqa: E402

SYSTEM_LABEL = {"saju": "사주", "astrology": "서양 점성술", "tarot": "타로"}

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


def _render_section(k, ch, sec, computed):
    """system_sections 항목 하나 — key_insight(pull_quote)ㆍ원본 계산값ㆍtakeaways(summary_box)까지
    전부 반영해서 한 섹션을 여러 시각 요소로 풍부하게 채운다."""
    k.chapter_header(ch, sec["heading"], eyebrow=SYSTEM_LABEL.get(sec["system"], sec["system"].upper()))
    if sec.get("key_insight"):
        k.pull_quote(sec["key_insight"])
    k.body(sec["body"])

    # 실제 계산값을 숫자ㆍ막대로도 보여줌(LLM 문장 + 원본 데이터 병기 = 신뢰도 확보)
    if sec["system"] == "saju" and computed.get("saju"):
        _oheng_bars(k, computed["saju"])
    elif sec["system"] == "astrology" and computed.get("astrology"):
        _element_bars(k, computed["astrology"])
    elif sec["system"] == "tarot" and computed.get("tarot"):
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
            present_items = [
                f"{label}: 있음({', '.join(shensha[key]['found_in'])} 기둥)"
                for key, label in [("taohua", "도화살"), ("yeokma", "역마살"), ("hwagae", "화개살"), ("hongyeom", "홍염살")]
                if shensha.get(key, {}).get("present")
            ]
            if present_items:
                k.h2("신살")
                k.callout_box("이 손님 사주에 있는 신살", present_items)
        k.spacer(10)

    # ---- 체계별 섹션(key_insight/takeaways까지 전부 반영) ----
    ch = 1
    for sec in report["system_sections"]:
        _render_section(k, ch, sec, computed)
        ch += 1

    if report.get("cross_analysis"):
        k.chapter_header(ch, report["cross_analysis"]["heading"], eyebrow="CROSS-ANALYSIS")
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
            k.tip_box([opp["body"]], header=f"{i}. {opp['title']}")
        ch += 1

    if report.get("risks"):
        k.chapter_header(ch, "예측 리스크 & 대비책", eyebrow="RISK FORECAST")
        for i, risk in enumerate(report["risks"], 1):
            k.warn_box([risk["body"]], header=f"{i}. {risk['title']}")
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

    k.warn_box([report["disclaimer"]], header="안내")

    k.build(footer_tagline="천지인운명관 — 사주ㆍ점성술ㆍ타로 독립 계산 후 교차 검증하는 통합 진단 서비스")
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
