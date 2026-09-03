"""
report_kit.py _TIER_EXPECTED_PAGES 키 정합성 회귀 테스트 — 2026-09-01.

#16 실제 tier 검증 중 발견: dual 실제 tier 값이 "full"이라는 죽은 키 때문에 페이지 수
안전망(check_pdf_structural_integrity)에서 사실상 무제한 범위(기본값 1~200)로 빠져
있었다. "full"은 SYSTEM_PROMPT 산문의 scope 표현일 뿐 실제 tier 값으로 쓰인 적이
없어 어떤 tier로도 이 키에 도달할 수 없었다(죽은 코드) — 키 이름만 "dual"로 고쳤다.

실제 PDF 렌더링 없이, 딕셔너리 구조 자체를 build_report.py의 6개 실제 tier 값과
대조한다. 실제 API 호출 없음.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPORT_DIR = HERE.parent

sys.path.insert(0, str(REPORT_DIR))
import report_kit as rk  # noqa: E402
import build_report as br  # noqa: E402


def main():
    any_fail = False

    print("=" * 100)
    print("1. 'full'이라는 죽은 키가 더 이상 없는지")
    print("=" * 100)
    ok = "full" not in rk._TIER_EXPECTED_PAGES
    status = "PASS" if ok else "FAIL"
    if not ok:
        any_fail = True
    print(f"  'full' 키 제거됨: [{status}]")

    print()
    print("=" * 100)
    print("2. 실제 tier 6개 전부가 각자 자기 키로 범위를 가지는지(기본값 1~200으로 새지 않는지)")
    print("=" * 100)
    real_tiers = (br._TIER_MINI, br._TIER_LIGHT, br._TIER_SINGLE, br._TIER_DUAL, br._TIER_MASTER, br._TIER_PREMIUM)
    for tier in real_tiers:
        lo, hi = rk._TIER_EXPECTED_PAGES.get(tier, (1, 200))
        has_own_key = tier in rk._TIER_EXPECTED_PAGES
        ok = has_own_key and (lo, hi) != (1, 200)
        status = "PASS" if ok else "FAIL"
        if not ok:
            any_fail = True
        print(f"  {tier:8s}: 전용 키 존재={has_own_key}, 범위=({lo},{hi}) [{status}]")

    print()
    print("=" * 100)
    print("3. dual 범위가 이웃 tier(single/master)와 순서상 일관적인지(lo/hi가 단조 증가)")
    print("=" * 100)
    single_lo, single_hi = rk._TIER_EXPECTED_PAGES["single"]
    dual_lo, dual_hi = rk._TIER_EXPECTED_PAGES["dual"]
    master_lo, master_hi = rk._TIER_EXPECTED_PAGES["master"]
    ok1 = single_lo <= dual_lo <= master_lo
    ok2 = single_hi <= dual_hi <= master_hi
    print(f"  lo 단조 증가(single={single_lo} <= dual={dual_lo} <= master={master_lo}): [{'PASS' if ok1 else 'FAIL'}]")
    print(f"  hi 단조 증가(single={single_hi} <= dual={dual_hi} <= master={master_hi}): [{'PASS' if ok2 else 'FAIL'}]")
    if not (ok1 and ok2):
        any_fail = True

    print()
    print("=" * 100)
    print("4. 실제 API 검증에서 확보된 dual 실측 페이지 수(22페이지)가 새 범위 안에 있는지")
    print("=" * 100)
    ok = dual_lo <= 22 <= dual_hi
    status = "PASS" if ok else "FAIL"
    if not ok:
        any_fail = True
    print(f"  22페이지가 dual 범위({dual_lo}~{dual_hi}) 안에 있음: [{status}]")

    print()
    if any_fail:
        raise SystemExit("치명적 실패")
    print("전체 PASS")


if __name__ == "__main__":
    main()
