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
"""
import json
import sys
from pathlib import Path

SHARED_DIR = Path(__file__).resolve().parent.parent.parent / "products" / "_shared"
sys.path.insert(0, str(SHARED_DIR))
from pdf_kit import PDFKit  # noqa: E402

SYSTEM_LABEL = {"saju": "사주", "astrology": "서양 점성술", "tarot": "타로"}


def _saju_stats(saju):
    """사주 오행 분포를 stat_row로 보여줄 데이터로 변환."""
    order = ["목", "화", "토", "금", "수"]
    return [(str(saju["oheng_count"].get(k, 0)), k) for k in order]


def _astrology_stats(astrology):
    order = ["불", "땅", "바람", "물"]
    return [(str(astrology["element_count"].get(k, 0)), k) for k in order]


def build_pdf(computed, report, out_path, product_name):
    """
    @param computed: run.js가 만든 computed.json (dict)
    @param report: build_report.py가 LLM으로 만든 report.json (dict)
    @param out_path: 출력 PDF 경로
    @param product_name: 표지에 쓸 상품명(예: "크로스노틱스 마스터 다차원 통합 진단")
    """
    k = PDFKit(out_path, title=f"{product_name} — {computed['customer'].get('name', '고객님')}")

    k.cover(
        kicker="CROSS-NOTICS PERSONAL REPORT",
        title_html=product_name,
        subtitle=f"{computed['customer'].get('name', '고객님')}님을 위한 개인 맞춤 진단",
        tagline="사주ㆍ점성술ㆍ타로 — 독립 계산 후 교차 검증한 결과만 담았습니다",
    )

    k.h1("들어가며")
    k.body(report["intro"])

    ch = 1
    for sec in report["system_sections"]:
        k.chapter_header(ch, sec["heading"], eyebrow=SYSTEM_LABEL.get(sec["system"], sec["system"].upper()))
        k.body(sec["body"])

        # 실제 계산값을 숫자로도 보여줌(LLM 문장 + 원본 데이터 병기 = 신뢰도 확보)
        if sec["system"] == "saju" and computed.get("saju"):
            k.stat_row(_saju_stats(computed["saju"]))
        elif sec["system"] == "astrology" and computed.get("astrology"):
            k.stat_row(_astrology_stats(computed["astrology"]))
        elif sec["system"] == "tarot" and computed.get("tarot"):
            cards = ", ".join(f"{d['position']}: {d['card_name']}({d['orientation']})" for d in computed["tarot"]["draws"])
            k.callout_box("뽑힌 카드", [cards])
        ch += 1

    if report.get("cross_analysis"):
        k.chapter_header(ch, report["cross_analysis"]["heading"], eyebrow="CROSS-ANALYSIS")
        corr = computed["correlation"]
        k.pull_quote(
            f"체계 일치도 {int(corr['agreement_score'] * 100)}% — "
            f"중심 기운은 '{corr['dominant_axis']}'",
        )
        k.body(report["cross_analysis"]["body"])
        ch += 1

    k.h1("마치며")
    k.body(report["closing"])

    k.warn_box([report["disclaimer"]], header="안내")

    k.build(footer_tagline="크로스노틱스 — 사주ㆍ점성술ㆍ타로 독립 계산 후 교차 검증하는 통합 진단 서비스")
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
