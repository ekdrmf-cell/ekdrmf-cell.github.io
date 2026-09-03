"""
#4 타로 누락 — 재발 방지(하드 차단) 회귀 테스트, 2026-08-31.

STEP6에서 실제로 벌어진 정확한 상황(saju+astrology+신규5개로 개수는 채우고 tarot만
0개 — 기존 check_required_tier_sections()가 "통과"로 잘못 찍었던 바로 그 시나리오)을
main() 전체 흐름으로 재현해, 이제는:
  1. CoreSystemMissingError가 발생하는지
  2. report.json이 저장되지 않는지
  3. raw.json이 삭제되지 않고 남아있는지(정규화 전 원본 그대로)
  4. verify_groundedness/verify_naturalness가 호출되지 않는지(비용 낭비 방지)
를 한 번에 검증한다. 실제 API는 전혀 호출하지 않는다(call_llm 자체를 monkeypatch).
"""
import json
import os
import sys
import tempfile
from pathlib import Path

os.environ["CROSSNOTICS_OFFLINE_TEST_MODE"] = "1"
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-test-not-real")

HERE = Path(__file__).resolve().parent
REPORT_DIR = HERE.parent
ENGINE_DIR = REPORT_DIR.parent / "crossnotics-engine"

sys.path.insert(0, str(REPORT_DIR))
import build_report as br  # noqa: E402


class _FakeUsage:
    def __init__(self, input_tokens=100, output_tokens=50):
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens


def _section(system, n=1):
    return {"system": system, "heading": f"{system} 섹션 {n}", "body": "본문 " * 20,
            "key_insight": "", "takeaways": []}


def _step6_reproduction_report():
    """STEP6 실제 상황: saju(4)+astrology(4)+신규5개(5)=13개(premium 최소 11 넘김),
    tarot은 0개."""
    sections = (
        [_section("saju", i) for i in range(4)]
        + [_section("astrology", i) for i in range(4)]
        + [_section(s) for s in ("tojeong", "yukhyo", "seongmyeonghak", "pungsu", "taekil")]
    )
    return {
        "intro": "테스트 intro", "toc_preview": None, "system_sections": sections,
        "cross_analysis": {"heading": "h", "body": "b"},
        "opportunities": [{"title": "t", "body": "b"}] * 5,
        "risks": [{"title": "t", "body": "b"}] * 4,
        "action_plan": {"heading": "h", "steps": [{"label": "l", "desc": "d"}]},
        "question_answers": [
            {"question": "q1", "answerability": "direct", "unanswerable_reason": None, "body": "b"},
            {"question": "q2", "answerability": "direct", "unanswerable_reason": None, "body": "b"},
        ],
        "long_term_strategy": {
            "decade_roadmap": {"heading": "h", "body": "b"},
            "lifetime_design": {"heading": "h", "body": "b"},
            "second_act": {"heading": "h", "body": "b"},
            "behavior_dna": None,
        },
        "closing": "테스트 closing",
    }


def _tarot_present_report():
    fake = _step6_reproduction_report()
    fake["system_sections"] = fake["system_sections"] + [_section("tarot", i) for i in range(3)]
    return fake


def _run_main_with_fake_report(fake_report, computed_path, out_path):
    """call_llm/verify_*를 monkeypatch하고 main()을 실행 — verify_* 호출 여부를
    카운터로 추적한다(비용 낭비 방지 검증용)."""
    call_counts = {"call_llm": 0, "verify_groundedness": 0, "verify_naturalness": 0}

    def fake_call_llm(computed):
        call_counts["call_llm"] += 1
        return dict(fake_report), _FakeUsage()

    def fake_verify_g(report, computed):
        call_counts["verify_groundedness"] += 1

    def fake_verify_n(report, tier=None):
        call_counts["verify_naturalness"] += 1
        # 2026-09-03 — main()이 이제 이 반환값을 실제로 소비한다(run_targeted_
        # rewrite_pass 배선). 진짜 verify_naturalness()와 같은 shape을 반환해야 함.
        return {"status": "PASS", "issues": [], "detail": "mock — 이 회귀 테스트는 issue 없음"}

    original_call_llm = br.call_llm
    original_verify_g = br.verify_groundedness
    original_verify_n = br.verify_naturalness
    br.call_llm = fake_call_llm
    br.verify_groundedness = fake_verify_g
    br.verify_naturalness = fake_verify_n

    old_argv = sys.argv
    sys.argv = ["build_report.py", str(computed_path), str(out_path)]
    error = None
    try:
        br.main()
    except br.CoreSystemMissingError as e:
        error = e
    finally:
        sys.argv = old_argv
        br.call_llm = original_call_llm
        br.verify_groundedness = original_verify_g
        br.verify_naturalness = original_verify_n

    return error, call_counts


def check_step6_reproduction_hard_blocks(tmp_dir):
    computed_path = ENGINE_DIR / "test/out-behavior.json"
    out_path = tmp_dir / "tarot_missing_report.json"
    raw_path = out_path.with_suffix(".raw.json")

    error, call_counts = _run_main_with_fake_report(_step6_reproduction_report(), computed_path, out_path)

    results = []
    results.append(("CoreSystemMissingError 발생", error is not None))
    results.append(("에러 메시지에 'tarot' 포함", error is not None and "tarot" in str(error)))
    results.append(("report.json이 저장되지 않음", not out_path.exists()))
    results.append(("raw.json이 삭제되지 않고 남아있음", raw_path.exists()))
    if raw_path.exists():
        raw_content = json.loads(raw_path.read_text(encoding="utf-8"))
        raw_has_no_tarot = "tarot" not in {s.get("system") for s in raw_content.get("system_sections", [])}
        results.append(("raw.json이 정규화 전 원본(tarot 없는 상태) 그대로", raw_has_no_tarot))
    results.append(("verify_groundedness 호출 안 됨(비용 낭비 방지)", call_counts["verify_groundedness"] == 0))
    results.append(("verify_naturalness 호출 안 됨(비용 낭비 방지)", call_counts["verify_naturalness"] == 0))
    results.append(("call_llm은 정확히 1회만 호출됨(추가 재호출 없음)", call_counts["call_llm"] == 1))
    return results


def check_tarot_present_no_regression(tmp_dir):
    """정상 케이스(회귀 확인) — tarot이 있으면 예외 없이 기존처럼 끝까지 완주해야 함."""
    computed_path = ENGINE_DIR / "test/out-behavior.json"
    out_path = tmp_dir / "tarot_present_report.json"
    raw_path = out_path.with_suffix(".raw.json")

    error, call_counts = _run_main_with_fake_report(_tarot_present_report(), computed_path, out_path)

    results = []
    results.append(("예외 발생 안 함(정상 케이스 회귀 없음)", error is None))
    results.append(("report.json이 정상 저장됨", out_path.exists()))
    results.append(("raw.json은 정상 케이스라 삭제됨", not raw_path.exists()))
    results.append(("verify_groundedness 정상 호출됨(1회)", call_counts["verify_groundedness"] == 1))
    results.append(("verify_naturalness 정상 호출됨(1회)", call_counts["verify_naturalness"] == 1))
    return results


def main():
    any_fail = False

    print("=" * 100)
    print("1. STEP6 정확한 재현 시나리오 — 하드 차단 검증")
    print("=" * 100)
    with tempfile.TemporaryDirectory() as td:
        for label, ok in check_step6_reproduction_hard_blocks(Path(td)):
            status = "PASS" if ok else "FAIL"
            if not ok:
                any_fail = True
            print(f"  {label}: [{status}]")

    print()
    print("=" * 100)
    print("2. tarot 존재 시 정상 케이스 — 회귀 없음 확인")
    print("=" * 100)
    with tempfile.TemporaryDirectory() as td:
        for label, ok in check_tarot_present_no_regression(Path(td)):
            status = "PASS" if ok else "FAIL"
            if not ok:
                any_fail = True
            print(f"  {label}: [{status}]")

    print()
    if any_fail:
        raise SystemExit("치명적 실패")
    print("전체 PASS")


if __name__ == "__main__":
    main()
