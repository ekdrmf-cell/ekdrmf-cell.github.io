"""
api_usage.py 회귀 테스트 — API 비용 절감 3단계(계측 구조).

이 파일은 실제 네트워크를 전혀 호출하지 않는다 — MOCK TEST 섹션은 가짜 usage 객체로만
api_usage.py의 기록/집계 로직을 검증하고, ACTUAL API DATA 섹션은 과거 실제 주문의
저장된 meta.json(webapp/pipeline.py가 실제 API 응답에서 파싱해 저장한 값)만 읽는다 —
새로운 API 호출은 0건. OFFLINE_TEST_MODE도 방어적으로 켜둔다(이 파일 자체는
call_llm/verify_* 등을 부르지 않지만, 혹시 나중에 이 파일이 확장되어 그런 함수를
불러도 안전하도록).

MOCK TEST와 ACTUAL API DATA는 절대 섞이지 않는다 — 모든 usage record는
build_usage_record(source=...)로 만들어지고, source 필드가 항상 "MOCK_TEST" 또는
"ACTUAL_API_DATA"로 표시된다.
"""
import json
import os
import sys
from pathlib import Path

os.environ["CROSSNOTICS_OFFLINE_TEST_MODE"] = "1"

HERE = Path(__file__).resolve().parent
REPORT_DIR = HERE.parent
sys.path.insert(0, str(REPORT_DIR))

import api_usage  # noqa: E402


class _MockUsage:
    """Anthropic SDK의 usage 객체를 흉내낸 가짜 객체 — 실제 API 응답이 아님을 이름으로도
    명시. cache_* 필드를 아예 갖지 않는 usage도 시뮬레이션(getattr 기본값 경로 검증)."""
    def __init__(self, input_tokens, output_tokens, cache_creation=None, cache_read=None):
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        if cache_creation is not None:
            self.cache_creation_input_tokens = cache_creation
        if cache_read is not None:
            self.cache_read_input_tokens = cache_read


def run_mock_tests():
    print("=" * 100)
    print("[MOCK TEST] 1. extract_usage_fields — cache 필드 없는 usage 객체(이 프로젝트의")
    print("            실제 상황과 동일 — 캐싱 안 씀)")
    print("=" * 100)
    mock = _MockUsage(input_tokens=1234, output_tokens=567)
    fields = api_usage.extract_usage_fields(mock)
    ok = (fields["input_tokens"] == 1234 and fields["output_tokens"] == 567
          and fields["cache_creation_input_tokens"] == 0 and fields["cache_read_input_tokens"] == 0)
    print(f"  결과: {fields} [{'PASS' if ok else 'FAIL'}]")
    assert ok, "cache 필드 없을 때 0 기본값 처리 실패"

    print()
    print("=" * 100)
    print("[MOCK TEST] 2. extract_usage_fields — cache 필드가 실제로 채워진 경우(캐싱을 켰다면")
    print("            어떻게 잡히는지 시뮬레이션, 실제로는 이 프로젝트에 없는 상황)")
    print("=" * 100)
    mock2 = _MockUsage(input_tokens=1000, output_tokens=200, cache_creation=300, cache_read=150)
    fields2 = api_usage.extract_usage_fields(mock2)
    ok2 = (fields2["cache_creation_input_tokens"] == 300 and fields2["cache_read_input_tokens"] == 150)
    print(f"  결과: {fields2} [{'PASS' if ok2 else 'FAIL'}]")
    assert ok2

    print()
    print("=" * 100)
    print("[MOCK TEST] 3. build_usage_record — source 필드 강제(MOCK_TEST/ACTUAL_API_DATA")
    print("            외 값은 거부해야 함)")
    print("=" * 100)
    record = api_usage.build_usage_record(
        call_purpose="generation", model="claude-sonnet-5", usage=mock,
        tier="premium", order_id="MOCK-ORDER-001", thinking_disabled=True, source="MOCK_TEST",
    )
    print(f"  record: {record}")
    assert record["source"] == "MOCK_TEST"
    try:
        api_usage.build_usage_record(
            call_purpose="generation", model="claude-sonnet-5", usage=mock, source="정체불명",
        )
        raise AssertionError("잘못된 source 값이 거부되지 않음")
    except ValueError:
        print("  잘못된 source 값('정체불명') 거부 확인: PASS")
    try:
        api_usage.build_usage_record(
            call_purpose="없는목적", model="claude-sonnet-5", usage=mock, source="MOCK_TEST",
        )
        raise AssertionError("알 수 없는 call_purpose가 거부되지 않음")
    except ValueError:
        print("  알 수 없는 call_purpose 거부 확인: PASS")

    print()
    print("=" * 100)
    print("[MOCK TEST] 4. log_usage_record — 임시 로그 파일에 실제로 append되는지")
    print("=" * 100)
    tmp_log = Path(REPORT_DIR / "logs" / "_mock_test_usage_log.jsonl")
    if tmp_log.exists():
        tmp_log.unlink()
    api_usage.log_usage_record(record, log_path=tmp_log)
    api_usage.log_usage_record(record, log_path=tmp_log)
    lines = tmp_log.read_text(encoding="utf-8").splitlines()
    ok4 = len(lines) == 2 and json.loads(lines[0])["source"] == "MOCK_TEST"
    print(f"  기록된 줄 수: {len(lines)} [{'PASS' if ok4 else 'FAIL'}]")
    tmp_log.unlink()
    assert ok4

    print()
    print("=" * 100)
    print("[MOCK TEST] 5. compute_cost_for_record — 가격 있는 모델(OK) vs 가격 null인 모델")
    print("            (UNKNOWN, 추정 금지 확인) vs usage 자체가 없는 record(UNKNOWN)")
    print("=" * 100)
    pricing = api_usage.load_pricing_config()
    sonnet_record = {"model": "claude-sonnet-5", "input_tokens": 1_000_000, "output_tokens": 1_000_000}
    cost = api_usage.compute_cost_for_record(sonnet_record, pricing)
    print(f"  sonnet-5(가격 있음): {cost}")
    assert cost["status"] == "OK" and abs(cost["usd"] - 18.0) < 1e-9  # 3 + 15 = 18 USD

    haiku_record = {"model": "claude-haiku-4-5-20251001", "input_tokens": 1000, "output_tokens": 500}
    cost_haiku = api_usage.compute_cost_for_record(haiku_record, pricing)
    print(f"  haiku-4.5(가격 null): {cost_haiku}")
    assert cost_haiku["status"] == "UNKNOWN", "가격 미확인 모델인데 숫자를 만들어냄 — 금지된 동작"

    no_usage_record = {"model": "claude-sonnet-5", "input_tokens": None, "output_tokens": None}
    cost_no_usage = api_usage.compute_cost_for_record(no_usage_record, pricing)
    print(f"  usage 기록 없음: {cost_no_usage}")
    assert cost_no_usage["status"] == "UNKNOWN"

    print()
    print("=" * 100)
    print("[MOCK TEST] 6. aggregate_costs — UNKNOWN 레코드가 합계에서 조용히 사라지지 않는지")
    print("=" * 100)
    mixed_records = [
        {"model": "claude-sonnet-5", "input_tokens": 100000, "output_tokens": 50000,
         "call_purpose": "generation", "tier": "mini"},
        {"model": "claude-haiku-4-5-20251001", "input_tokens": 5000, "output_tokens": 500,
         "call_purpose": "verify_groundedness", "tier": "mini"},
    ]
    agg = api_usage.aggregate_costs(mixed_records, pricing)
    print(f"  집계 결과: {agg}")
    ok6 = agg["known_record_count"] == 1 and agg["unknown_record_count"] == 1
    assert ok6, "known/unknown 레코드 개수가 예상과 다름"
    print(f"  known=1, unknown=1 확인 [{'PASS' if ok6 else 'FAIL'}]")

    print()
    print("MOCK TEST 전체 PASS")


def run_actual_data_analysis():
    print()
    print("=" * 100)
    print("[ACTUAL API DATA] 과거 저장된 주문 meta.json 기반 비용 분석(새 API 호출 없음)")
    print("=" * 100)
    orders_dir = REPORT_DIR / "orders"
    pricing = api_usage.load_pricing_config()

    records = []
    for meta_path in sorted(orders_dir.glob("*/meta.json")):
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        cost = meta.get("cost")
        if not cost:
            print(f"  {meta_path.parent.name}: cost 필드 없음 — 건너뜀")
            continue
        record = api_usage.build_usage_record(
            call_purpose="generation",
            model="claude-sonnet-5",  # meta.json에 모델명이 안 남아있어 build_report.py의
                                       # 현재 MODEL 기본값을 근거로 추정 — 아래 REPORT에 명시.
            usage=type("U", (), {
                "input_tokens": cost["input_tokens"], "output_tokens": cost["output_tokens"],
            })(),
            tier=meta.get("tier"), order_id=meta_path.parent.name,
            thinking_disabled=True, source="ACTUAL_API_DATA",
        )
        records.append(record)
        print(f"  {meta_path.parent.name} (tier={meta.get('tier')}): "
              f"input={record['input_tokens']}, output={record['output_tokens']} [ACTUAL_API_DATA]")

    print()
    print("  검증 호출(verify_groundedness/verify_naturalness)/rewrite 호출의 usage는 이번 3단계")
    print("  계측 코드를 추가하기 전 생성된 과거 주문이라 애초에 기록된 적이 없음 — UNKNOWN.")
    print("  (이 3단계 계측 코드가 실제로 배포된 이후에 생성되는 새 주문부터만 확인 가능해짐.)")

    agg = api_usage.aggregate_costs(records, pricing)
    print()
    print("  === 생성 호출만의 비용 집계(claude-sonnet-5 기준, 실제 API 데이터) ===")
    print(f"  {json.dumps(agg, ensure_ascii=False, indent=2)}")
    print()
    print("  === 확인 불가 항목 ===")
    print("  - verify_groundedness 비용: UNKNOWN(과거 주문에 usage 기록 자체가 없음)")
    print("  - verify_naturalness 비용: UNKNOWN(위와 동일)")
    print("  - targeted_rewrite 비용: UNKNOWN(이 기능 자체가 실제 운영에서 아직 호출된 적 없음)")
    print("  - 생성+검증+rewrite 합산 전체 비용: UNKNOWN(구성요소 중 검증/rewrite가 UNKNOWN이므로)")
    print("  - claude-haiku-4-5-20251001 가격: UNKNOWN(api_pricing_config.json에 null로 기록,")
    print("    이 프로젝트 어디에도 문서화된 적 없어 추정하지 않음)")


if __name__ == "__main__":
    run_mock_tests()
    run_actual_data_analysis()
