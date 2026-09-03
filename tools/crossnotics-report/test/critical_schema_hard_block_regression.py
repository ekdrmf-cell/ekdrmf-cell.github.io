"""
#5/#6 — CRITICAL 스키마 오류(system_sections 붕괴) → #4 하드블록 연쇄 회귀 테스트, 2026-09-01.

#5(schema normalization CRITICAL 분류)와 #6(raw 보존)의 A+B+C 수정, 그리고 #4의
enforce_purchased_core_systems_present() 하드블록은 각각 따로는 이미 회귀 테스트로
검증돼 있다(schema_normalization_regression.py는 cross_analysis 같은 "CRITICAL이지만
하드블록은 안 걸리는" 필드로만 검증했고, tarot_hard_block_regression.py는 "system_sections는
스키마상 정상이지만 tarot 태그만 빠진" 시나리오로 하드블록을 검증했다).

아직 실제로 검증된 적 없는 것은 이 둘의 "합성" 시나리오다: LLM이 system_sections
자체를 통째로 망가뜨린 문자열로 반환했을 때 —
  1. normalize_to_schema()가 CRITICAL로 분류하고 []로 대체하는지
  2. raw.json이 정규화 *전* 원본(문자열 그대로)을 담고 보존되는지
  3. SCHEMA_INCIDENT 영구 보존 파일이 생기는지
  4. []가 된 system_sections 때문에 enforce_purchased_core_systems_present()가
     CoreSystemMissingError를 정상적으로 이어받아 발동하는지
  5. report.json이 저장되지 않는지
  6. verify_groundedness/verify_naturalness(유료 검증)가 호출되지 않는지
가 한 번의 main() 흐름 안에서 전부 맞물려 동작하는지 — 이 연쇄가 끊기지 않는지가
이번 테스트의 목적이다. 실제 API 호출 없음(call_llm을 monkeypatch).
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


def _report_with_broken_system_sections():
    """system_sections만 문자열로 통째로 망가뜨리고, 나머지 최상위 필드는 전부
    스키마에 맞는 정상 값으로 채운다 — 이번 테스트가 검증하려는 연쇄(system_sections
    붕괴 → CRITICAL → []  → 하드블록)만 격리해서 관찰하기 위함."""
    return {
        "intro": "테스트 intro", "toc_preview": None,
        "system_sections": "LLM이 배열 대신 통째로 반환한 망가진 문자열입니다",
        "cross_analysis": {"heading": "h", "body": "b"},
        "opportunities": [{"title": "t", "body": "b"}] * 5,
        "risks": [{"title": "t", "body": "b"}] * 4,
        "action_plan": {"heading": "h", "steps": [{"label": "l", "desc": "d"}]},
        "question_answers": [
            {"question": "q1", "answerability": "direct", "unanswerable_reason": None, "body": "b"},
        ],
        "long_term_strategy": {
            "decade_roadmap": {"heading": "h", "body": "b"},
            "lifetime_design": {"heading": "h", "body": "b"},
            "second_act": {"heading": "h", "body": "b"},
            "behavior_dna": None,
        },
        "closing": "테스트 closing",
    }


def check_critical_corruption_hard_block_chain(tmp_dir):
    computed_path = ENGINE_DIR / "test/out-behavior.json"  # premium 픽스처
    out_path = tmp_dir / "critical_hard_block_report.json"
    raw_path = out_path.with_suffix(".raw.json")

    fake_report = _report_with_broken_system_sections()
    call_counts = {"call_llm": 0, "verify_groundedness": 0, "verify_naturalness": 0}

    def fake_call_llm(computed):
        call_counts["call_llm"] += 1
        return dict(fake_report), _FakeUsage()

    def fake_verify_g(report, computed):
        call_counts["verify_groundedness"] += 1

    def fake_verify_n(report, tier=None):
        call_counts["verify_naturalness"] += 1
        # 2026-09-03 — main()이 이제 이 반환값을 실제로 소비한다(run_targeted_
        # rewrite_pass 배선). 예전엔 호출 횟수만 세면 됐지만, 지금은 진짜 verify_
        # naturalness()와 같은 shape(status/issues/detail)을 반환해야 main()이 안 죽는다.
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

    results = []
    results.append(("CoreSystemMissingError가 이어받아 발동함(system_sections CRITICAL→[] 때문)", error is not None))
    results.append(("report.json이 저장되지 않음", not out_path.exists()))
    results.append(("raw.json이 삭제되지 않고 남아있음", raw_path.exists()))
    if raw_path.exists():
        raw_content = json.loads(raw_path.read_text(encoding="utf-8"))
        results.append(("raw.json이 정규화 *전* 원본(망가진 문자열 그대로)을 담고 있음",
                         raw_content.get("system_sections") == fake_report["system_sections"]))
    incident_files = list(tmp_dir.glob(f"{out_path.stem}.SCHEMA_INCIDENT_*.raw.json"))
    results.append(("SCHEMA_INCIDENT 영구 보존 파일이 정확히 1개 생성됨", len(incident_files) == 1))
    if incident_files:
        incident_content = json.loads(incident_files[0].read_text(encoding="utf-8"))
        results.append(("incident 파일도 정규화 전 원본(망가진 문자열)을 담고 있음",
                         incident_content.get("system_sections") == fake_report["system_sections"]))
    results.append(("verify_groundedness 호출 안 됨(유료 검증 비용 낭비 방지)", call_counts["verify_groundedness"] == 0))
    results.append(("verify_naturalness 호출 안 됨(유료 검증 비용 낭비 방지)", call_counts["verify_naturalness"] == 0))
    results.append(("call_llm은 정확히 1회만 호출됨(추가 재호출 없음)", call_counts["call_llm"] == 1))
    return results


def main():
    any_fail = False
    print("=" * 100)
    print("system_sections CRITICAL 붕괴 -> CRITICAL 분류 -> raw/incident 보존 -> #4 하드블록 -> 저장/검증 차단 (연쇄 전체)")
    print("=" * 100)
    with tempfile.TemporaryDirectory() as td:
        for label, ok in check_critical_corruption_hard_block_chain(Path(td)):
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
