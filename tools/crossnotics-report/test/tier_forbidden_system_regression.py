"""
#16 — Tier Forbidden-System Enforcement 회귀 테스트, 2026-09-01.

실제 API 검증(dual)에서 발생한 사고를 재현한다: dual(10만원) 고객에게 LLM이 master
전용(15만원) new_reference_systems.yukhyo를 자발적으로 생성했다. 컴파일된 dual 프롬프트에
이미 "MASTER 이상만"이라는 tier gating 문구가 있었음에도 LLM이 무시했으므로, 프롬프트가
아니라 결정론적 코드가 최종 방어선이어야 한다(enforce_tier_system_boundaries, build_report.py).

Test 1~7은 사용자가 지정한 케이스를 그대로 구현한다. 마지막에 실제 dual API 응답
(이번 세션에서 이미 확보된 real capture)을 재생해 새 함수가 그 실제 사고를 정확히
잡아내는지도 확인한다. 실제 API 호출 없음(call_llm을 monkeypatch, 또는 저장된
report.json을 직접 재사용).
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


def _nrs_entry(text="본문 내용 " * 5):
    return {"heading": "h", "body": text, "key_insight": "ki", "takeaways": ["t1"]}


def _section(system, body="본문 " * 20):
    return {"system": system, "heading": f"{system} 섹션", "body": body,
            "key_insight": "", "takeaways": []}


class _FakeUsage:
    def __init__(self, input_tokens=100, output_tokens=50):
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens


def _core_sections(tier):
    """이 tier가 요구하는 saju/astrology/tarot core 섹션(#4 하드블록 통과용)을 채운다."""
    sections = [_section("saju") for _ in range(4)]
    if tier in ("dual", "master", "premium"):
        sections += [_section("astrology") for _ in range(4)]
    if tier in ("master", "premium"):
        sections += [_section("tarot") for _ in range(3)]
    return sections


def _fake_report(tier, new_reference_systems=None, extra_sections=None):
    return {
        "intro": "테스트 intro", "toc_preview": None,
        "system_sections": (_core_sections(tier) if tier != "mini" else [_section("saju")]) + (extra_sections or []),
        "new_reference_systems": new_reference_systems,
        "cross_analysis": {"heading": "h", "body": "b"} if tier not in ("mini",) else None,
        "opportunities": [{"title": "t", "body": "b"}] * 3 if tier not in ("mini", "light") else None,
        "risks": [{"title": "t", "body": "b"}] * 3 if tier not in ("mini", "light") else None,
        "action_plan": {"heading": "h", "steps": [{"label": "l", "desc": "d"}]} if tier in ("dual", "master", "premium") else None,
        "question_answers": None if tier == "mini" else [
            {"question": "q1", "answerability": "direct", "unanswerable_reason": None, "body": "b"},
        ],
        "long_term_strategy": {
            "decade_roadmap": {"heading": "h", "body": "b"}, "lifetime_design": {"heading": "h", "body": "b"},
            "second_act": {"heading": "h", "body": "b"}, "behavior_dna": None,
        } if tier == "premium" else None,
        "closing": "테스트 closing",
    }


def _run_main_with_fake_report(fake_report, computed_path, out_path):
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
    except br.ForbiddenTierSystemError as e:
        error = e
    finally:
        sys.argv = old_argv
        br.call_llm = original_call_llm
        br.verify_groundedness = original_verify_g
        br.verify_naturalness = original_verify_n

    return error, call_counts


FIXTURES = {
    "mini": "out-mini.json", "light": "out-light.json", "single": "out-single.json",
    "dual": "out-dual.json", "master": "out-master.json", "premium": "out-behavior.json",
}


def test1_dual_plus_yukhyo(tmp_dir):
    """Test 1 — dual + yukhyo(금지) → FAIL/HARD BLOCK, report.json 미생성."""
    computed_path = ENGINE_DIR / "test" / FIXTURES["dual"]
    out_path = tmp_dir / "t1_report.json"
    raw_path = out_path.with_suffix(".raw.json")
    fake = _fake_report("dual", new_reference_systems={
        "tojeong": _nrs_entry(), "yukhyo": _nrs_entry(),
    })
    error, counts = _run_main_with_fake_report(fake, computed_path, out_path)
    return [
        ("ForbiddenTierSystemError 발생", error is not None),
        ("에러 메시지에 'yukhyo' 포함", error is not None and "yukhyo" in str(error)),
        ("report.json 미생성", not out_path.exists()),
        ("raw.json 보존됨", raw_path.exists()),
        ("verify_groundedness 미호출(비용 낭비 방지)", counts["verify_groundedness"] == 0),
        ("verify_naturalness 미호출(비용 낭비 방지)", counts["verify_naturalness"] == 0),
    ]


def test2_dual_normal(tmp_dir):
    """Test 2 — dual 정상(tojeong만) → PASS."""
    computed_path = ENGINE_DIR / "test" / FIXTURES["dual"]
    out_path = tmp_dir / "t2_report.json"
    fake = _fake_report("dual", new_reference_systems={"tojeong": _nrs_entry()})
    error, counts = _run_main_with_fake_report(fake, computed_path, out_path)
    return [
        ("예외 없음", error is None),
        ("report.json 정상 저장됨", out_path.exists()),
        ("verify_groundedness 정상 호출(1회)", counts["verify_groundedness"] == 1),
    ]


def test3_master_normal(tmp_dir):
    """Test 3 — master 정상(tojeong+yukhyo) → PASS."""
    computed_path = ENGINE_DIR / "test" / FIXTURES["master"]
    out_path = tmp_dir / "t3_report.json"
    fake = _fake_report("master", new_reference_systems={
        "tojeong": _nrs_entry(), "yukhyo": _nrs_entry(),
    })
    error, counts = _run_main_with_fake_report(fake, computed_path, out_path)
    return [
        ("예외 없음", error is None),
        ("report.json 정상 저장됨", out_path.exists()),
    ]


def test4_master_forbidden(tmp_dir):
    """Test 4 — master에 premium 전용(pungsu) 생성 → FAIL/HARD BLOCK."""
    computed_path = ENGINE_DIR / "test" / FIXTURES["master"]
    out_path = tmp_dir / "t4_report.json"
    raw_path = out_path.with_suffix(".raw.json")
    fake = _fake_report("master", new_reference_systems={
        "tojeong": _nrs_entry(), "yukhyo": _nrs_entry(), "pungsu": _nrs_entry(),
    })
    error, counts = _run_main_with_fake_report(fake, computed_path, out_path)
    return [
        ("ForbiddenTierSystemError 발생", error is not None),
        ("에러 메시지에 'pungsu' 포함", error is not None and "pungsu" in str(error)),
        ("report.json 미생성", not out_path.exists()),
        ("raw.json 보존됨", raw_path.exists()),
    ]


def test5_lower_tiers_clean(tmp_dir):
    """Test 5 — mini/light/single은 신규5개 전혀 없이도 정상 통과."""
    results = []
    for tier in ("mini", "light", "single"):
        computed_path = ENGINE_DIR / "test" / FIXTURES[tier]
        out_path = tmp_dir / f"t5_{tier}_report.json"
        fake = _fake_report(tier, new_reference_systems=None)
        error, counts = _run_main_with_fake_report(fake, computed_path, out_path)
        results.append((f"{tier}: 예외 없음(신규5개 전혀 없어도 정상)", error is None))
        results.append((f"{tier}: report.json 정상 저장됨", out_path.exists()))
    return results


def test6_multiple_forbidden(tmp_dir):
    """Test 6 — 하나의 응답에 forbidden 3개 동시 존재 → 전부 수집돼 기록되는지."""
    computed_path = ENGINE_DIR / "test" / FIXTURES["dual"]
    out_path = tmp_dir / "t6_report.json"
    fake = _fake_report("dual", new_reference_systems={
        "tojeong": _nrs_entry(), "yukhyo": _nrs_entry(),
        "seongmyeonghak": _nrs_entry(), "pungsu": _nrs_entry(),
    })
    error, counts = _run_main_with_fake_report(fake, computed_path, out_path)
    msg = str(error) if error else ""
    return [
        ("ForbiddenTierSystemError 발생", error is not None),
        ("3개 위반 전부 메시지에 포함(yukhyo)", "yukhyo" in msg),
        ("3개 위반 전부 메시지에 포함(seongmyeonghak)", "seongmyeonghak" in msg),
        ("3개 위반 전부 메시지에 포함(pungsu)", "pungsu" in msg),
        ("허용된 tojeong은 위반 목록에 없음", not msg.split("[")[1].split("]")[0].__contains__("'tojeong'") if "[" in msg else False),
    ]


def test7_null_and_empty(tmp_dir):
    """Test 7 — forbidden이 null / {} 인 경우 위반으로 오판하지 않는지."""
    results = []
    computed_path = ENGINE_DIR / "test" / FIXTURES["dual"]

    out_path_null = tmp_dir / "t7_null_report.json"
    fake_null = _fake_report("dual", new_reference_systems={
        "tojeong": _nrs_entry(), "yukhyo": None,
    })
    error, _ = _run_main_with_fake_report(fake_null, computed_path, out_path_null)
    results.append(("yukhyo=null이면 위반 아님(예외 없음)", error is None))
    results.append(("yukhyo=null이면 report.json 정상 저장됨", out_path_null.exists()))

    out_path_empty = tmp_dir / "t7_empty_report.json"
    fake_empty = _fake_report("dual", new_reference_systems={
        "tojeong": _nrs_entry(), "yukhyo": {},
    })
    error2, _ = _run_main_with_fake_report(fake_empty, computed_path, out_path_empty)
    results.append(("yukhyo={}이면 위반 아님(예외 없음)", error2 is None))
    results.append(("yukhyo={}이면 report.json 정상 저장됨", out_path_empty.exists()))
    return results


def check_real_dual_capture_would_have_been_caught():
    """실제 API 검증(#16)에서 저장된 dual 실제 응답(yukhyo 포함)을 새 함수에 직접
    통과시켜, 그 실제 사고가 이 함수로 정확히 잡히는지 확인한다(가장 강력한 증거 —
    가상 mock이 아니라 실제로 있었던 LLM 응답 그대로)."""
    real_path = Path(
        r"C:/Users/ekdrm/AppData/Local/Temp/claude/C--Users-ekdrm-OneDrive-Desktop-------/"
        r"fabfbbaf-de67-4056-a226-be2ac0d8b3c5/scratchpad/step_tier_dual_report.json"
    )
    if not real_path.exists():
        return [("실제 dual 캡처 파일 없음(스킵)", True)]
    report = json.loads(real_path.read_text(encoding="utf-8"))
    computed = {"tier": "dual"}
    try:
        br.enforce_tier_system_boundaries(report, computed)
        return [("실제 dual 응답(yukhyo 포함)을 새 함수가 잡아냄", False)]
    except br.ForbiddenTierSystemError as e:
        return [
            ("실제 dual 응답(yukhyo 포함)을 새 함수가 정확히 잡아냄", True),
            ("에러 메시지에 yukhyo 포함", "yukhyo" in str(e)),
        ]


def main():
    any_fail = False
    cases = [
        ("Test 1 — dual + yukhyo(금지)", test1_dual_plus_yukhyo),
        ("Test 2 — dual 정상", test2_dual_normal),
        ("Test 3 — master 정상", test3_master_normal),
        ("Test 4 — master + pungsu(금지)", test4_master_forbidden),
        ("Test 5 — mini/light/single 정상", test5_lower_tiers_clean),
        ("Test 6 — 동시 다발 forbidden(3개)", test6_multiple_forbidden),
        ("Test 7 — null/empty는 위반 아님", test7_null_and_empty),
    ]
    for title, fn in cases:
        print("=" * 100)
        print(title)
        print("=" * 100)
        with tempfile.TemporaryDirectory() as td:
            for label, ok in fn(Path(td)):
                status = "PASS" if ok else "FAIL"
                if not ok:
                    any_fail = True
                print(f"  {label}: [{status}]")
        print()

    print("=" * 100)
    print("실제 캡처 재생 — dual 실제 API 사고 재현 확인")
    print("=" * 100)
    for label, ok in check_real_dual_capture_would_have_been_caught():
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
