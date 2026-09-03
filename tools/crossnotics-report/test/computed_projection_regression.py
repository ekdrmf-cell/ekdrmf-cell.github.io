"""
computed_projection.py 회귀 테스트 — API 비용 절감 2단계.

OFFLINE_TEST_MODE를 최상단에서 켠다(이 값은 build_report import보다 먼저 설정돼야
call_llm/verify_groundedness/verify_naturalness/_call_targeted_rewrite_llm이 실제
네트워크 호출 전에 확실히 막힌다) — 이 파일 자체는 어떤 경우에도 실제 API를 호출하지
않는다(사용자 지시: "테스트 실행 전에 각 테스트가 실제 API를 호출하는지 먼저 코드로
확인" — 이 파일은 call_llm 등을 직접 부르지 않으므로 애초에 네트워크 호출 코드 경로가
없고, 그 위에 OFFLINE_TEST_MODE까지 이중 안전장치로 세팅함).

검증 항목(사용자가 요구한 8개 완료 기준 그대로):
  1. computed.json 원본 불변
  2. projection 구현(이미 됨, 여기서는 대조만)
  3. dependency map 코드화 확인
  4. required field 누락 검사(양방향의 절반)
  5. removed field 사용 여부 검사(양방향의 나머지 절반)
  6. fallback 데이터 보존
  7. Q&A 안전성 보존(규칙10-A~10-K가 제거 대상 필드를 참조하지 않는지 재확인)
  8. BEFORE/AFTER token 실측
"""
import json
import os
import sys
from pathlib import Path

os.environ["CROSSNOTICS_OFFLINE_TEST_MODE"] = "1"  # 반드시 build_report import 전에 설정

import tiktoken

HERE = Path(__file__).resolve().parent
REPORT_DIR = HERE.parent
ENGINE_DIR = REPORT_DIR.parent / "crossnotics-engine"

sys.path.insert(0, str(REPORT_DIR))
import build_report as br  # noqa: E402
import computed_projection as cp  # noqa: E402

enc = tiktoken.get_encoding("cl100k_base")


def toklen_json(obj):
    return len(enc.encode(json.dumps(obj, ensure_ascii=False, indent=2)))


FIXTURES = {
    "mini": ENGINE_DIR / "test/out-mini.json",
    "light": ENGINE_DIR / "test/out-light.json",
    "single": ENGINE_DIR / "test/out-single.json",
    "dual": ENGINE_DIR / "test/out-dual.json",
    "master": ENGINE_DIR / "test/out-master.json",
    "premium": ENGINE_DIR / "test/out-behavior.json",
}


def check_offline_mode_actually_blocks():
    assert br.OFFLINE_TEST_MODE is True, "OFFLINE_TEST_MODE가 켜지지 않음 — 안전장치 무효"
    for fn, args in [
        (br.call_llm, ({"tier": "mini"},)),
        (br.verify_groundedness, ({}, {})),
        (br.verify_naturalness, ({},)),
        (br._call_targeted_rewrite_llm, ("x",)),
    ]:
        try:
            fn(*args)
            return False, fn.__name__
        except RuntimeError as e:
            if "OFFLINE_TEST_MODE" not in str(e):
                return False, f"{fn.__name__}(다른 이유로 예외: {e})"
    return True, None


def check_original_unmodified(tier, path):
    """project_computed()가 원본 dict를 절대 mutate하지 않는지 — 디스크에서 다시 읽은
    원본과, project_computed() 호출 이후의 in-memory 원본이 완전히 같아야 한다."""
    before_text = path.read_text(encoding="utf-8")
    computed = json.loads(before_text)
    original_copy_for_compare = json.loads(before_text)  # 별도 파싱본(참조 공유 없음)

    _ = cp.project_computed(computed)

    unchanged = computed == original_copy_for_compare
    file_unchanged = path.read_text(encoding="utf-8") == before_text
    return unchanged, file_unchanged


def check_bidirectional(tier, path):
    computed = json.loads(path.read_text(encoding="utf-8"))
    projection = cp.project_computed(computed)

    actual_removed = cp.diff_removed_paths(computed, projection)
    declared = cp.declared_removed_paths()

    # declared에 있는 경로(예: 'astrology.planets')를 통째로 지우면 그 자손 leaf 경로
    # ('astrology.planets[].degree' 등)도 diff에 함께 나타나는 게 정상 — 그래서 단순
    # 집합 차집합이 아니라 "조상-자손" 관계까지 보는 unauthorized_removed_paths()로 판정.
    unauthorized_removed = cp.unauthorized_removed_paths(actual_removed, declared)
    return {
        "tier": tier,
        "actual_removed": sorted(actual_removed),
        "unauthorized_removed": sorted(unauthorized_removed),
        "ok": len(unauthorized_removed) == 0,
    }


def check_removed_fields_unused_in_full_prompt():
    results = cp.verify_removed_fields_unused_in_prompt(br.SYSTEM_PROMPT, br._PROMPT_BLOCKS)
    bad = [r for r in results if r["found_in_prompt"]]
    return results, bad


def check_removed_fields_absent_from_rule10_blocks():
    """Q&A 안전성 — 규칙10-A~10-K 각 블록 텍스트에 제거 대상 필드의 leaf 이름이 없는지
    개별적으로 재확인(전체 SYSTEM_PROMPT 검사보다 더 좁혀서, "혹시 다른 규칙에서만 안 쓰이고
    Q&A 규칙에서는 쓰인다"는 가능성까지 배제). disambiguation_exclude_blocks가 지정된
    항목(예: 'aspects' — astrology_synastry.aspects 문맥인 r10e 자체)은 그 블록을 검사
    대상에서 뺀다(computed_projection.verify_removed_fields_unused_in_prompt와 동일 원칙)."""
    rule10_ids = ["r10_main", "r10a", "r10b", "r10c", "r10d", "r10e", "r10f", "r10f1",
                  "r10g", "r10h", "r10i", "r10j", "r10k"]
    bad = []
    for entry in cp.REMOVED_FIELD_MANIFEST:
        leaf = entry["path"].split(".")[-1]
        exclude = set(entry.get("disambiguation_exclude_blocks") or [])
        combined = "\n".join(br._PROMPT_BLOCKS[r] for r in rule10_ids if r not in exclude)
        if leaf in combined:
            bad.append(leaf)
    for entry in cp.SUB_ARRAY_FIELD_REMOVALS:
        combined = "\n".join(br._PROMPT_BLOCKS[r] for r in rule10_ids)
        for sub in entry["sub_fields"]:
            if sub in combined:
                bad.append(sub)
    return bad


def check_fallback_preserved():
    all_results = []
    for tier, path in FIXTURES.items():
        computed = json.loads(path.read_text(encoding="utf-8"))
        projection = cp.project_computed(computed)
        results = cp.verify_fallback_fields_preserved(computed, projection)
        all_results.append((tier, results))
    return all_results


def main():
    print("=" * 100)
    print("0. OFFLINE_TEST_MODE 실제 차단 확인")
    print("=" * 100)
    ok, bad = check_offline_mode_actually_blocks()
    print(f"  결과: {'PASS' if ok else f'FAIL({bad})'}")
    if not ok:
        raise SystemExit("치명적 실패 — OFFLINE_TEST_MODE가 실제로 네트워크 호출을 막지 못함")

    print()
    print("=" * 100)
    print("1. computed.json 원본 불변 확인(전체 6개 티어 fixture)")
    print("=" * 100)
    any_fail = False
    for tier, path in FIXTURES.items():
        mem_ok, file_ok = check_original_unmodified(tier, path)
        status = "PASS" if (mem_ok and file_ok) else "FAIL"
        if status == "FAIL":
            any_fail = True
        print(f"  {tier:8s}: in-memory 불변={mem_ok}, 파일 불변={file_ok} [{status}]")

    print()
    print("=" * 100)
    print("2. 양방향 검증 A — REMOVED FIELD가 선언된 것과 정확히 같은가(무단 제거 없음)")
    print("=" * 100)
    for tier, path in FIXTURES.items():
        r = check_bidirectional(tier, path)
        status = "PASS" if r["ok"] else "FAIL"
        if not r["ok"]:
            any_fail = True
        print(f"  {tier:8s} [{status}] 실제 제거된 경로 {len(r['actual_removed'])}개, "
              f"미승인 제거 {len(r['unauthorized_removed'])}개: {r['unauthorized_removed']}")

    print()
    print("=" * 100)
    print("3. 양방향 검증 B — REMOVED FIELD가 SYSTEM_PROMPT 전체에서 실제로 미사용인가")
    print("=" * 100)
    results, bad = check_removed_fields_unused_in_full_prompt()
    for r in results:
        print(f"  {r['path']:35s} leaf={r['leaf']:20s} SYSTEM_PROMPT에 등장={r['found_in_prompt']}")
    status = "PASS" if not bad else "FAIL"
    if bad:
        any_fail = True
    print(f"  종합: {status} (미사용 아닌 것으로 드러난 필드 {len(bad)}개: {[b['path'] for b in bad]})")

    print()
    print("=" * 100)
    print("4. Q&A 안전성 — 규칙10-A~10-K가 제거 대상 필드를 참조하지 않는가")
    print("=" * 100)
    bad_q = check_removed_fields_absent_from_rule10_blocks()
    status = "PASS" if not bad_q else "FAIL"
    if bad_q:
        any_fail = True
    print(f"  결과: {status} (규칙10 계열에서 발견된 제거 대상 필드: {bad_q})")

    print()
    print("=" * 100)
    print("5. fallback 데이터 보존 확인(4개 지정 필드 + saju.lunar_conversion_note)")
    print("=" * 100)
    for tier, results in check_fallback_preserved():
        all_ok = all(r["ok"] for r in results)
        status = "PASS" if all_ok else "FAIL"
        if not all_ok:
            any_fail = True
        print(f"  {tier:8s} [{status}]")
        for r in results:
            if r["existed_in_original"]:
                print(f"      {r['path']}: 원본에 존재={r['existed_in_original']}, "
                      f"projection에 존재={r['exists_in_projection']}")

    print()
    print("=" * 100)
    print("6. BEFORE/AFTER token 실측(computed.json 단독, SYSTEM_PROMPT는 1단계에서 별도 실측)")
    print("=" * 100)
    print(f"  {'tier':8s} {'BEFORE':>8s} {'AFTER':>8s} {'절감':>6s} {'절감%':>7s}")
    combined_rows = []
    for tier, path in FIXTURES.items():
        computed = json.loads(path.read_text(encoding="utf-8"))
        projection = cp.project_computed(computed)
        before_tok = toklen_json(computed)
        after_tok = toklen_json(projection)
        saved = before_tok - after_tok
        pct = saved / before_tok * 100
        print(f"  {tier:8s} {before_tok:8d} {after_tok:8d} {saved:6d} {pct:6.1f}%")
        combined_rows.append((tier, before_tok, after_tok))

    print()
    print("  참고 — SYSTEM_PROMPT(1단계)와 computed projection(2단계)을 합산한 총 입력 절감:")
    print(f"  {'tier':8s} {'SYS before':>10s} {'SYS after':>9s} {'CMP before':>10s} {'CMP after':>9s} {'총 before':>9s} {'총 after':>9s} {'총 절감%':>8s}")
    baseline_sys_tok = len(enc.encode(br.SYSTEM_PROMPT))
    for tier, cmp_before, cmp_after in combined_rows:
        computed = json.loads(FIXTURES[tier].read_text(encoding="utf-8"))
        sys_after = len(enc.encode(br.build_system_prompt(tier, computed)))
        total_before = baseline_sys_tok + cmp_before
        total_after = sys_after + cmp_after
        pct = (total_before - total_after) / total_before * 100
        print(f"  {tier:8s} {baseline_sys_tok:10d} {sys_after:9d} {cmp_before:10d} {cmp_after:9d} "
              f"{total_before:9d} {total_after:9d} {pct:7.1f}%")

    print()
    print("  주의: 위 절감률은 \"API 비용 문제 해결\"이 아니라 \"불필요한 데이터를 전달하지 "
          "않는 구조 확보\"의 실측치임(사용자 지시).")

    print()
    if any_fail:
        raise SystemExit("치명적 실패 — 위 항목 중 하나 이상 FAIL, 배포 중단")
    print("전체 PASS")


if __name__ == "__main__":
    main()
