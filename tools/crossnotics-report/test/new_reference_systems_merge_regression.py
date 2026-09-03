"""
#3(D-2) new_reference_systems -> system_sections 병합 회귀 테스트 — 2026-09-01.

목적: _merge_new_reference_systems_into_sections()가 사용자 승인 설계안(D-2)의
①new_reference_systems 확인 ②기존 system_sections 확인 ③둘 중 하나라도 유효 콘텐츠가
있으면 존재로 판단 ④둘 다 없으면 fallback 순서를 정확히 구현하는지 검증한다.

CASE 1~5는 병합 함수를 직접 호출하는 단위 테스트(빠름), 마지막은 main() 전체 흐름으로
fallback과의 상호작용까지 확인하는 end-to-end 테스트. 실제 API 호출 없음.
"""
import contextlib
import io
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


def _nrs_entry(text):
    return {"heading": "h", "body": text, "key_insight": "ki", "takeaways": ["t1"]}


def _section(system, body="본문 " * 20):
    return {"system": system, "heading": f"{system} 섹션", "body": body,
            "key_insight": "", "takeaways": []}


def case1_all_five_present():
    report = {
        "new_reference_systems": {
            "tojeong": _nrs_entry("토정비결 본문 " * 5),
            "yukhyo": _nrs_entry("육효 본문 " * 5),
            "seongmyeonghak": _nrs_entry("성명학 본문 " * 5),
            "pungsu": _nrs_entry("풍수 본문 " * 5),
            "taekil": _nrs_entry("택일 본문 " * 5),
        },
        "system_sections": [],
    }
    br._merge_new_reference_systems_into_sections(report)
    tags = [s["system"] for s in report["system_sections"]]
    results = [
        ("5개 전부 system_sections에 정확히 1개씩 생성됨", sorted(tags) == sorted(br._NEW5_SYSTEM_KEYS)),
        ("각 항목 body가 new_reference_systems 값 그대로 반영됨",
         all(s["body"] == report["new_reference_systems"][s["system"]]["body"] for s in report["system_sections"])),
    ]
    return results


def case2_partial_present():
    report = {
        "new_reference_systems": {
            "tojeong": _nrs_entry("토정비결 본문 " * 5),
            "yukhyo": _nrs_entry("육효 본문 " * 5),
            # seongmyeonghak/pungsu/taekil 없음
        },
        "system_sections": [],
    }
    br._merge_new_reference_systems_into_sections(report)
    tags = {s["system"] for s in report["system_sections"]}
    return [("존재하는 tojeong/yukhyo만 병합됨(나머지 3개는 없음)", tags == {"tojeong", "yukhyo"})]


def case3_none_present():
    report = {"new_reference_systems": {}, "system_sections": [_section("saju")]}
    before = list(report["system_sections"])
    br._merge_new_reference_systems_into_sections(report)
    return [("0개 존재 시 아무것도 병합되지 않음(system_sections 변화 없음)",
              report["system_sections"] == before)]


def case4_duplicate_prevention():
    original_body = "기존 system_sections 경로로 직접 생성된 토정비결 본문입니다 " * 3
    new_body = "새 new_reference_systems 경로로 생성된 토정비결 본문입니다 " * 3
    report = {
        "new_reference_systems": {"tojeong": _nrs_entry(new_body)},
        "system_sections": [_section("tojeong", body=original_body)],
    }
    br._merge_new_reference_systems_into_sections(report)
    tojeong_entries = [s for s in report["system_sections"] if s["system"] == "tojeong"]
    results = [
        ("동일 system이 new_reference_systems와 system_sections에 동시 존재해도 중복 생성 안 됨(정확히 1개)",
         len(tojeong_entries) == 1),
        ("기존 system_sections 경로의 콘텐츠가 우선(덮어쓰기 안 됨)",
         len(tojeong_entries) == 1 and tojeong_entries[0]["body"] == original_body),
    ]
    return results


def case5_legacy_path_only():
    report = {"system_sections": [_section("tojeong")]}  # new_reference_systems 키 자체가 없음
    before = list(report["system_sections"])
    br._merge_new_reference_systems_into_sections(report)
    return [("new_reference_systems가 아예 없어도(레거시 경로만) 정상 인식, 변경/오류 없음",
              report["system_sections"] == before)]


class _FakeUsage:
    def __init__(self, input_tokens=100, output_tokens=50):
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens


def _premium_fake_report_new_path_partial():
    """premium 기준 saju(4)+astrology(4)+tarot(3)는 정상(#4 하드블록 통과용),
    신규5개 중 tojeong/yukhyo만 new_reference_systems로 옴 — seongmyeonghak/pungsu/
    taekil은 어느 경로에도 없어 fallback이 발동해야 하는 상황."""
    sections = (
        [_section("saju") for _ in range(4)]
        + [_section("astrology") for _ in range(4)]
        + [_section("tarot") for _ in range(3)]
    )
    return {
        "intro": "테스트 intro", "toc_preview": None, "system_sections": sections,
        "new_reference_systems": {
            "tojeong": _nrs_entry("new_reference_systems 경로 토정비결 본문 " * 5),
            "yukhyo": _nrs_entry("new_reference_systems 경로 육효 본문 " * 5),
        },
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


def check_fallback_interaction(tmp_dir):
    """instruction #8 — new_reference_systems에 tojeong/yukhyo만 있을 때, fallback은
    나머지 3개(seongmyeonghak/pungsu/taekil)에만 발동하고 이미 채워진 tojeong/yukhyo는
    건드리지 않아야 한다."""
    computed_path = ENGINE_DIR / "test/out-behavior.json"
    out_path = tmp_dir / "nrs_merge_report.json"
    fake_report = _premium_fake_report_new_path_partial()

    def fake_call_llm(computed):
        return dict(fake_report), _FakeUsage()

    def fake_verify_g(report, computed):
        pass

    def fake_verify_n(report, tier=None):
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
    stdout_buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(stdout_buf):
            br.main()
    finally:
        sys.argv = old_argv
        br.call_llm = original_call_llm
        br.verify_groundedness = original_verify_g
        br.verify_naturalness = original_verify_n

    stdout_text = stdout_buf.getvalue()
    final_report = json.loads(out_path.read_text(encoding="utf-8"))
    tags = {s["system"]: s for s in final_report["system_sections"]}

    results = []
    results.append(("예외 없이 정상 완주함(report.json 저장됨)", out_path.exists()))
    results.append(("fallback 로그에 seongmyeonghak/pungsu/taekil만 언급됨(3개 전부)",
                     all(name in stdout_text for name in ("seongmyeonghak", "pungsu", "taekil"))
                     and "✓ 신규 참고 시스템 섹션 자동 보강 완료" in stdout_text))
    results.append(("fallback 로그에 tojeong이 언급되지 않음(이미 존재해 fallback 대상 아님)",
                     "자동 보강 완료(" in stdout_text
                     and "자동 보강 완료(" in stdout_text
                     and stdout_text.split("자동 보강 완료(", 1)[1].split(")")[0].find("tojeong") == -1))
    results.append(("fallback 로그에 yukhyo가 언급되지 않음(이미 존재해 fallback 대상 아님)",
                     stdout_text.split("자동 보강 완료(", 1)[1].split(")")[0].find("yukhyo") == -1
                     if "자동 보강 완료(" in stdout_text else False))
    # 2026-09-01 — ensure_emphasis()가 merge 이후 단계에서 본문에 **강조**를 입힐 수
    # 있으므로(기존 파이프라인의 정상 동작, merge 함수와 무관), 마크다운 강조 기호를
    # 제거한 뒤 내용 자체가 new_reference_systems 값 그대로인지 비교한다.
    results.append(("최종 system_sections에 tojeong 존재, body 내용이 new_reference_systems 값 그대로(강조 기호 제외)",
                     "tojeong" in tags
                     and tags["tojeong"]["body"].replace("*", "") == fake_report["new_reference_systems"]["tojeong"]["body"]))
    results.append(("최종 system_sections에 yukhyo 존재, body 내용이 new_reference_systems 값 그대로(강조 기호 제외)",
                     "yukhyo" in tags
                     and tags["yukhyo"]["body"].replace("*", "") == fake_report["new_reference_systems"]["yukhyo"]["body"]))
    results.append(("seongmyeonghak이 fallback으로 생성되어 존재함", "seongmyeonghak" in tags))
    results.append(("pungsu가 fallback으로 생성되어 존재함", "pungsu" in tags))
    results.append(("taekil이 fallback으로 생성되어 존재함", "taekil" in tags))
    return results


def main():
    any_fail = False
    cases = [
        ("CASE 1 — 5개 전부 존재", case1_all_five_present),
        ("CASE 2 — 일부만 존재", case2_partial_present),
        ("CASE 3 — 0개 존재", case3_none_present),
        ("CASE 4 — 동일 system 중복 존재 시 중복 방지", case4_duplicate_prevention),
        ("CASE 5 — 기존 system_sections에만 존재(레거시 경로)", case5_legacy_path_only),
    ]
    for title, fn in cases:
        print("=" * 100)
        print(title)
        print("=" * 100)
        for label, ok in fn():
            status = "PASS" if ok else "FAIL"
            if not ok:
                any_fail = True
            print(f"  {label}: [{status}]")
        print()

    print("=" * 100)
    print("CASE 6 — main() 전체 흐름: fallback은 없는 3개에만 발동, 있는 2개는 안 건드림")
    print("=" * 100)
    with tempfile.TemporaryDirectory() as td:
        for label, ok in check_fallback_interaction(Path(td)):
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
