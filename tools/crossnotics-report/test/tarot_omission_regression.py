"""
#4 타로 누락 회귀 테스트 — 2026-08-31.

목적: check_required_tier_sections()가 이제 saju/astrology/tarot 개별 존재를 실제로
검사하는지 확인한다. 특히 STEP6에서 실제로 벌어진 정확한 상황(saju+astrology+신규5개
합만으로 개수 기준을 넘겨 tarot 소실이 은폐됨)을 그대로 재현해 잡아내는지 검증한다.

실제 API 호출은 하지 않는다 — 순수 함수 단위 테스트.
"""
import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPORT_DIR = HERE.parent
ENGINE_DIR = REPORT_DIR.parent / "crossnotics-engine"

sys.path.insert(0, str(REPORT_DIR))
import build_report as br  # noqa: E402


def _section(system, n=1):
    return {"system": system, "heading": f"{system} 섹션 {n}", "body": "본문 " * 20}


def run_check(report, computed):
    buf = io.StringIO()
    with redirect_stdout(buf):
        br.check_required_tier_sections(report, computed)
    return buf.getvalue()


def check_step6_reproduction():
    """STEP6 실제 상황 재현 — saju4+astrology4+신규5개=13개(premium 최소치 11 넘음)인데
    tarot이 0개. 수정 전에는 이걸 '통과'로 찍었다(실제 로그로 확인됨) — 수정 후에는
    반드시 tarot 누락을 잡아내야 한다."""
    computed = json.loads((ENGINE_DIR / "test/out-behavior.json").read_text(encoding="utf-8"))
    assert computed.get("tarot"), "이 fixture는 tarot을 포함해야 재현 테스트가 의미 있음"

    sections = (
        [_section("saju", i) for i in range(4)]
        + [_section("astrology", i) for i in range(4)]
        + [_section(s) for s in ("tojeong", "yukhyo", "seongmyeonghak", "pungsu", "taekil")]
        # tarot 섹션 의도적으로 0개 — STEP6 재현
    )
    report = {"system_sections": sections, "question_answers": None,
              "long_term_strategy": {"decade_roadmap": {"body": "x"}, "lifetime_design": {"body": "x"},
                                      "second_act": {"body": "x"}},
              "action_plan": {"steps": []}, "cross_analysis": None}
    output = run_check(report, computed)
    ok = "tarot" in output and "premium" in output and "✓" not in output
    return ok, output


def check_tarot_present_passes():
    """tarot이 실제로 있으면 이 새 검사가 오탐하지 않아야 한다."""
    computed = json.loads((ENGINE_DIR / "test/out-behavior.json").read_text(encoding="utf-8"))
    sections = (
        [_section("saju", i) for i in range(4)]
        + [_section("astrology", i) for i in range(4)]
        + [_section("tarot", i) for i in range(3)]
        + [_section(s) for s in ("tojeong", "yukhyo", "seongmyeonghak", "pungsu", "taekil")]
    )
    report = {"system_sections": sections, "question_answers": None,
              "long_term_strategy": {"decade_roadmap": {"body": "x"}, "lifetime_design": {"body": "x"},
                                      "second_act": {"body": "x"}},
              "action_plan": {"steps": []}, "cross_analysis": None}
    output = run_check(report, computed)
    ok = "tarot" not in output and "✓ 티어별 필수 섹션 검사 통과" in output
    return ok, output


def check_no_tarot_purchased_no_false_positive():
    """tarot을 안 산 티어(single 등, computed에 tarot 자체가 없음)는 이 새 검사가
    당연히 걸리면 안 된다 — computed.get('tarot')이 없으면 검사 자체를 건너뛰어야 함."""
    computed = json.loads((ENGINE_DIR / "test/out-single.json").read_text(encoding="utf-8"))
    assert not computed.get("tarot"), "single 티어 fixture는 tarot이 없어야 함"
    sections = [_section("saju", i) for i in range(4)]
    report = {"system_sections": sections, "question_answers": None,
              "long_term_strategy": None, "action_plan": None, "cross_analysis": None}
    output = run_check(report, computed)
    ok = "tarot" not in output
    return ok, output


def check_saju_astrology_symmetry():
    """같은 논리로 saju/astrology가 빠져도(인위적 시나리오) 잡히는지 — 대칭성 확인."""
    computed = json.loads((ENGINE_DIR / "test/out-behavior.json").read_text(encoding="utf-8"))
    sections = (
        [_section("tarot", i) for i in range(3)]
        + [_section(s) for s in ("tojeong", "yukhyo", "seongmyeonghak", "pungsu", "taekil")]
        + [_section("saju", i) for i in range(3)]  # astrology 없음, saju는 있음
    )
    report = {"system_sections": sections, "question_answers": None,
              "long_term_strategy": {"decade_roadmap": {"body": "x"}, "lifetime_design": {"body": "x"},
                                      "second_act": {"body": "x"}},
              "action_plan": {"steps": []}, "cross_analysis": None}
    output = run_check(report, computed)
    ok = "astrology" in output and "saju" not in output.replace("astrology", "")
    return ok, output


def main():
    checks = [
        ("STEP6 실제 상황 재현(saju+astrology+신규5개로 개수는 채우고 tarot만 0개) → 반드시 잡힘",
         check_step6_reproduction),
        ("tarot 실제로 있으면 오탐 없음", check_tarot_present_passes),
        ("tarot 구매 안 한 티어는 이 검사가 당연히 안 걸림", check_no_tarot_purchased_no_false_positive),
        ("saju/astrology 빠져도 대칭적으로 잡힘(방어적 확장 검증)", check_saju_astrology_symmetry),
    ]
    any_fail = False
    for label, fn in checks:
        ok, output = fn()
        status = "PASS" if ok else "FAIL"
        if not ok:
            any_fail = True
        print(f"{label}: [{status}]")
        if not ok:
            print(f"  실제 출력:\n{output}")

    print()
    if any_fail:
        raise SystemExit("치명적 실패")
    print("전체 PASS")


if __name__ == "__main__":
    main()
