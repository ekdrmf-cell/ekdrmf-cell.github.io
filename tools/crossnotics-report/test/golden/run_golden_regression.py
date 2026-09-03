"""골든 질문 회귀 테스트 — SYSTEM_PROMPT(질문 분류 규칙)를 고칠 때마다 실행할 것.

목적: "질문 하나하나마다 실제 주문처럼 테스트해야 하는가"라는 질문에 대한 답 —
그럴 필요 없다. 대신 다양한 유형(direct/redirected/unanswerable, 명리학
대응표ㆍ신살로 승격되는 유형 포함)을 대표하는 질문 세트를 여기 고정해두고,
프롬프트를 바꿀 때마다 이 세트 전체를 다시 돌려서 기존 판정이 안 깨졌는지
확인한다. 실제 손님 질문마다 매번 이 과정을 반복하는 게 아니라, "판정 로직 자체"가
바뀔 때만 한 번 돌리면 된다.

사용법:
    cd tools/crossnotics-report
    python test/golden/run_golden_regression.py

비용: fixture 2개 × 리포트 전체 생성 1회씩 = MASTER 1건 + SINGLE 1건 분량의
실제 API 호출이 발생한다(약 150~300원 수준, build_report.py 실측치 기준).
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPORT_TOOL_DIR = HERE.parent.parent
sys.path.insert(0, str(REPORT_TOOL_DIR))

import build_report  # noqa: E402  (경로 삽입 이후에 import해야 함)


def run_fixture(fixture_path, expected_map, total_usage):
    computed = json.loads(fixture_path.read_text(encoding="utf-8"))
    print(f"\n{'=' * 60}\n{fixture_path.name} 실행 중 (질문 {len(computed['customer']['questions'])}개)...")

    report, usage = build_report.call_llm(computed)
    total_usage["input"] += usage.input_tokens
    total_usage["output"] += usage.output_tokens

    schema_corrections = []
    report = build_report.normalize_to_schema(
        report, build_report.REPORT_SCHEMA["input_schema"], "report", schema_corrections
    )
    if schema_corrections:
        print(f"⚠ 스키마 보정 {len(schema_corrections)}건 발생 — 이 자체가 회귀 신호일 수 있음:")
        for c in schema_corrections:
            print(f"    - [{c['severity']}] {c['message']}")

    known_terms = build_report.collect_known_terms(computed)
    valid_years = build_report.collect_valid_years(computed)
    build_report.check_hallucination(report, known_terms, valid_years)
    if hasattr(build_report, "verify_groundedness"):
        build_report.verify_groundedness(report, computed)

    qa_list = report.get("question_answers") or []
    got_by_question = {qa.get("question"): qa.get("answerability") for qa in qa_list}

    results = []
    for question, expected in expected_map.items():
        got = got_by_question.get(question, "❌ 응답 없음")
        ok = got == expected
        results.append((question, expected, got, ok))
    return results


def main():
    expected_all = json.loads((HERE / "expected.json").read_text(encoding="utf-8"))
    expected_all.pop("_설명", None)

    total_usage = {"input": 0, "output": 0}
    all_results = []

    for fixture_name, expected_map in expected_all.items():
        fixture_path = HERE / fixture_name
        results = run_fixture(fixture_path, expected_map, total_usage)
        all_results.extend((fixture_name, *r) for r in results)

    print(f"\n{'=' * 60}\n결과 요약\n{'=' * 60}")
    passed = 0
    for fixture_name, question, expected, got, ok in all_results:
        mark = "✓" if ok else "✗ FAIL"
        print(f"{mark}  [{fixture_name}] {question!r} — 기대: {expected} / 실제: {got}")
        if ok:
            passed += 1

    total = len(all_results)
    print(f"\n{passed}/{total} 통과")
    print(f"토큰 사용량: 입력 {total_usage['input']} / 출력 {total_usage['output']}")

    if passed < total:
        print("\n⚠ 실패한 항목이 있음 — SYSTEM_PROMPT 최근 수정이 기존 판정 로직을 깨뜨렸을 수 있음.")
        sys.exit(1)
    else:
        print("\n✓ 전부 통과 — 기존 판정 로직이 이번 수정으로 깨지지 않음.")


if __name__ == "__main__":
    main()
