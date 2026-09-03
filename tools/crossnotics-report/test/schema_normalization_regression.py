"""
normalize_to_schema()/main() raw 백업ㆍCRITICAL 분류 회귀 테스트 — 2026-08-31, STEP9 사고 대응.

실제 API를 전혀 호출하지 않는다 — call_llm()을 가짜 응답으로 monkeypatch해서 main()의
전체 흐름(진짜 raw 저장 → 정규화 → CRITICAL/MINOR 분류 → incident 보존)을 검증한다.
OFFLINE_TEST_MODE도 방어적으로 켜둔다(혹시 monkeypatch가 안 걸려도 실제 호출은 막힘).
"""
import json
import os
import sys
import types
from pathlib import Path

os.environ["CROSSNOTICS_OFFLINE_TEST_MODE"] = "1"
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-test-not-real")

HERE = Path(__file__).resolve().parent
REPORT_DIR = HERE.parent
ENGINE_DIR = REPORT_DIR.parent / "crossnotics-engine"

sys.path.insert(0, str(REPORT_DIR))
import build_report as br  # noqa: E402


def check_severity_classification():
    """normalize_to_schema() 단위 테스트 — CRITICAL vs MINOR 분류가 올바른지."""
    results = []

    # 1) 최상위 구조 필드(system_sections)가 문자열로 옴 → CRITICAL, 값은 []로.
    fake_report = {
        "intro": "ok", "system_sections": "이것은 배열이 아니라 그냥 문자열입니다",
        "question_answers": None, "long_term_strategy": None, "closing": "ok",
    }
    corrections = []
    normalized = br.normalize_to_schema(fake_report, br.REPORT_SCHEMA["input_schema"], "report", corrections)
    sys_sections_corrections = [c for c in corrections if c["path"] == "report.system_sections"]
    ok1 = (
        len(sys_sections_corrections) == 1
        and sys_sections_corrections[0]["severity"] == "CRITICAL"
        and normalized["system_sections"] == []
    )
    results.append(("최상위 system_sections 문자열 → CRITICAL + []", ok1))

    # 2) 최상위 구조 필드(cross_analysis)가 숫자로 옴 → CRITICAL.
    fake_report2 = {
        "intro": "ok", "system_sections": [], "cross_analysis": 12345,
        "question_answers": None, "long_term_strategy": None, "closing": "ok",
    }
    corrections2 = []
    br.normalize_to_schema(fake_report2, br.REPORT_SCHEMA["input_schema"], "report", corrections2)
    ca_corrections = [c for c in corrections2 if c["path"] == "report.cross_analysis"]
    ok2 = len(ca_corrections) == 1 and ca_corrections[0]["severity"] == "CRITICAL"
    results.append(("최상위 cross_analysis 숫자 → CRITICAL", ok2))

    # 3) 최상위 필드가 아예 빠짐(intro 누락) → 이건 required-missing 경로, 여전히
    #    최상위(report.intro)라 CRITICAL 분류 대상은 아니지만(문자열 타입 기본값 "" 채움),
    #    CRITICAL_TOP_LEVEL_FIELDS에 "intro"는 없으므로 MINOR여야 정상.
    fake_report3 = {
        "system_sections": [], "question_answers": None, "long_term_strategy": None, "closing": "ok",
    }
    corrections3 = []
    br.normalize_to_schema(fake_report3, br.REPORT_SCHEMA["input_schema"], "report", corrections3)
    intro_corrections = [c for c in corrections3 if c["path"] == "report.intro"]
    ok3 = len(intro_corrections) == 1 and intro_corrections[0]["severity"] == "MINOR"
    results.append(("최상위지만 목록 밖(intro) 누락 → MINOR", ok3))

    # 4) 중첩된 하위 필드(system_sections[0].heading 없음)는 MINOR.
    fake_report4 = {
        "intro": "ok",
        "system_sections": [{"system": "saju", "body": "본문"}],  # heading 없음(required)
        "question_answers": None, "long_term_strategy": None, "closing": "ok",
    }
    corrections4 = []
    br.normalize_to_schema(fake_report4, br.REPORT_SCHEMA["input_schema"], "report", corrections4)
    nested = [c for c in corrections4 if "system_sections[0]" in c["path"]]
    ok4 = len(nested) >= 1 and all(c["severity"] == "MINOR" for c in nested)
    results.append(("중첩 하위 필드(system_sections[0].heading) 누락 → MINOR", ok4))

    # 5) 이중 인코딩 JSON 문자열 복구 — 성공 시 MINOR(진짜 손실이 아니라 복구니까).
    real_sections = [{"system": "saju", "heading": "h", "body": "b"}]
    fake_report5 = {
        "intro": "ok", "system_sections": json.dumps(real_sections, ensure_ascii=False),
        "question_answers": None, "long_term_strategy": None, "closing": "ok",
    }
    corrections5 = []
    normalized5 = br.normalize_to_schema(fake_report5, br.REPORT_SCHEMA["input_schema"], "report", corrections5)
    double_enc = [c for c in corrections5 if c["path"] == "report.system_sections"]
    ok5 = (
        len(double_enc) == 1 and double_enc[0]["severity"] == "MINOR"
        and normalized5["system_sections"] == real_sections
    )
    results.append(("이중 인코딩 복구 성공 → MINOR(손실 아님)", ok5))

    return results


class _FakeUsage:
    def __init__(self, input_tokens=100, output_tokens=50):
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens


def check_main_flow_raw_backup_and_incident(tmp_dir):
    """main() 전체 흐름 — call_llm()만 가짜로 바꾸고 나머지는 실제 코드 그대로 실행."""
    computed_path = ENGINE_DIR / "test/out-mini.json"
    out_path = tmp_dir / "schema_test_report.json"
    raw_path = out_path.with_suffix(".raw.json")

    # 실제 call_llm()이 반환했을 법한 "고장난" 응답 — cross_analysis가 문자열.
    # 2026-08-31 수정 — 원래 system_sections를 고장냈었는데, #4(타로 누락 재발방지)의
    # enforce_purchased_core_systems_present()가 도입되면서 system_sections가 비면(mini도
    # saju는 있어야 하므로) CoreSystemMissingError가 먼저 발생해 이 테스트 본연의 목적
    # (CRITICAL 분류ㆍraw 보존)을 검증하기 전에 끊겨버림 — 그래서 system_sections는
    # #4 검사를 통과하는 최소 유효값(mini 규칙대로 saju 1개)으로 두고, 대신
    # cross_analysis를 고장내 같은 시나리오(최상위 구조 필드 타입 오류)를 재현한다.
    fake_report = {
        "intro": "테스트 intro",
        "system_sections": [{"system": "saju", "heading": "h", "body": "본문 " * 20,
                              "key_insight": "", "takeaways": []}],
        "toc_preview": None, "cross_analysis": "고장난 문자열 응답 시뮬레이션",
        "opportunities": None, "risks": None,
        "action_plan": None, "question_answers": None, "long_term_strategy": None,
        "closing": "테스트 closing",
    }

    original_call_llm = br.call_llm
    original_verify_g = br.verify_groundedness
    original_verify_n = br.verify_naturalness

    def fake_call_llm(computed):
        return dict(fake_report), _FakeUsage()

    # verify_groundedness/verify_naturalness도 실제 API를 부르므로 이 테스트에서는
    # 아무것도 안 하는 스텁으로 바꾼다(이 테스트의 목적은 raw 백업/CRITICAL 분류 검증이지
    # 검증 호출 자체가 아님 — 실제 API 호출 0건 유지).
    def fake_verify_g(report, computed):
        pass

    def fake_verify_n(report, tier=None):
        # 2026-09-03 — main()이 이제 이 반환값을 실제로 소비한다(run_targeted_
        # rewrite_pass 배선). 진짜 verify_naturalness()와 같은 shape을 반환해야 함.
        return {"status": "PASS", "issues": [], "detail": "mock — 이 회귀 테스트는 issue 없음"}

    br.call_llm = fake_call_llm
    br.verify_groundedness = fake_verify_g
    br.verify_naturalness = fake_verify_n

    old_argv = sys.argv
    sys.argv = ["build_report.py", str(computed_path), str(out_path)]
    try:
        br.main()
    finally:
        sys.argv = old_argv
        br.call_llm = original_call_llm
        br.verify_groundedness = original_verify_g
        br.verify_naturalness = original_verify_n

    results = []

    # A. 최종 report.json은 정규화된 안전한 기본값이어야 함 — cross_analysis 타입은
    # REPORT_SCHEMA에 ["object","null"]로 선언돼 있어 "object"가 먼저 매치되므로
    # 기본값은 {}(빈 객체)다(None이 아님 — _SCHEMA_SAFE_DEFAULT가 타입 선언 순서대로
    # 첫 매치를 고름, build_report.py normalize_to_schema 확인).
    final_report = json.loads(out_path.read_text(encoding="utf-8"))
    results.append(("최종 report.json의 cross_analysis가 안전한 기본값({})으로 정규화됨",
                     final_report.get("cross_analysis") == {}))

    # B. 진짜 raw 백업(schema_corrections 있었으므로 삭제 안 되고 남아있어야 함)이
    #    정규화 *전* 값(문자열 그대로)을 담고 있어야 함 — A(진짜 raw)와 정규화 결과가
    #    서로 분리돼 있다는 직접 증거.
    raw_exists = raw_path.exists()
    raw_content = json.loads(raw_path.read_text(encoding="utf-8")) if raw_exists else None
    ok_raw = raw_exists and raw_content.get("cross_analysis") == fake_report["cross_analysis"]
    results.append(("raw.json이 삭제되지 않고 원본 문자열을 그대로 담고 있음", ok_raw))

    # C. incident 파일(스키마 보정 발생 시 영구 보존)이 out_path와 같은 폴더에
    #    "SCHEMA_INCIDENT"를 포함한 이름으로 생겨야 함.
    incident_files = list(tmp_dir.glob(f"{out_path.stem}.SCHEMA_INCIDENT_*.raw.json"))
    ok_incident = len(incident_files) == 1
    results.append(("SCHEMA_INCIDENT 영구 보존 파일이 정확히 1개 생성됨", ok_incident))
    if ok_incident:
        incident_content = json.loads(incident_files[0].read_text(encoding="utf-8"))
        results.append(("incident 파일도 정규화 전 원본 문자열을 담고 있음",
                         incident_content.get("cross_analysis") == fake_report["cross_analysis"]))

    return results


def main():
    print("=" * 100)
    print("1. normalize_to_schema() CRITICAL/MINOR 분류 단위 테스트")
    print("=" * 100)
    any_fail = False
    for label, ok in check_severity_classification():
        status = "PASS" if ok else "FAIL"
        if not ok:
            any_fail = True
        print(f"  {label}: [{status}]")

    print()
    print("=" * 100)
    print("2. main() 전체 흐름 — 진짜 raw 백업 / CRITICAL 분류 / incident 보존")
    print("=" * 100)
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        tmp_dir = Path(td)
        for label, ok in check_main_flow_raw_backup_and_incident(tmp_dir):
            status = "PASS" if ok else "FAIL"
            if not ok:
                any_fail = True
            print(f"  {label}: [{status}]")

    print()
    if any_fail:
        raise SystemExit("치명적 실패 — 위 항목 중 하나 이상 FAIL")
    print("전체 PASS")


if __name__ == "__main__":
    main()
