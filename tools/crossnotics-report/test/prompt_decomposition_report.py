"""
build_system_prompt() 회귀 테스트 + BEFORE/AFTER 리포트.

이 파일의 EXPECTED_* 표는 build_report.py의 _RULE_META를 그대로 베낀 게 아니라, 실제
엔진 코드(saju.js/run.js/catalog.js)를 직접 읽고 손으로 도출한 "정답 집합"이다 — 즉
build_report.py 코드가 스스로를 검증하는 게 아니라, 이 파일이 독립적으로 도출한 기대값과
실제 산출물을 대조한다(사용자 지시: "규칙 보존 → 정확한 조건부 분리" 검증은 코드 내부
일관성이 아니라 사람이 검증한 기준과의 대조여야 함).

검증 항목(사용자가 요구한 8가지):
  1. 필요한 규칙이 실제로 포함됐는가(MISSING이 비어있는가)
  2. 불필요한 규칙이 실제로 빠졌는가(EXTRA가 비어있는가)
  3. 공통 규칙(ALWAYS_INCLUDED)이 모든 티어에서 유지되는가
  4. 규칙 5/5-A/5-B가 바이트 단위로 원문과 동일한가(절대 손대지 않았다는 증거)
  5. 조립 순서가 원문 순서와 같은가
  6. 스키마 관련 규칙(0번, 형식 규칙)이 항상 포함되는가
  7. 필드 조건부 규칙이 실제 computed.json 필드 유무에 맞게 적용됐는가
  8. 토큰 수를 실측하는가(tiktoken, 근사치임을 명시)

실행: python test/prompt_decomposition_report.py
"""
import json
import sys
from pathlib import Path

import tiktoken

HERE = Path(__file__).resolve().parent
REPORT_DIR = HERE.parent
ENGINE_DIR = REPORT_DIR.parent / "crossnotics-engine"

sys.path.insert(0, str(REPORT_DIR))
import build_report as br  # noqa: E402

enc = tiktoken.get_encoding("cl100k_base")


def toklen(text):
    return len(enc.encode(text))


ALWAYS_INCLUDED = {
    "preamble", "r00", "r01", "r02", "r03", "r04", "r04a", "r05", "r05a", "r05b", "r5c",
    "r06", "r07", "r08_intro", "r08_common_tail", "r09_main", "r11",
}

RULE10_FAMILY = {
    "r10_main", "r10a", "r10b", "r10c", "r10f", "r10f1", "r10g", "r10h", "r10i", "r10j", "r10k",
}

ALL_RULE_IDS = set(br._PROMPT_RULE_ORDER)


def expected_for(tier, computed):
    """엔진 코드 확인 결과를 근거로 손으로 도출한 기대 포함 집합(코드와 독립적)."""
    inc = set(ALWAYS_INCLUDED)
    has_astrology = "astrology" in computed
    has_gunghap_or_synastry = computed.get("gunghap") is not None or computed.get("astrology_synastry") is not None
    has_behavior = computed.get("behavior") is not None
    has_questions = tier != "mini"

    tier_block = {
        "mini": "r08_mini", "light": "r08_light", "single": "r08_single",
        "dual": "r08_dual", "master": "r08_master", "premium": "r08_premium",
    }[tier]
    inc.add(tier_block)
    # single 이상은 상위 티어 프롬프트가 하위 티어 블록을 "위와 동일"로 참조하므로 누적 포함.
    if tier in ("dual", "master", "premium"):
        inc.add("r08_single")
    if tier in ("master", "premium"):
        inc.add("r08_dual")
    if tier == "premium":
        inc.add("r08_master")

    if tier in ("single", "dual", "master", "premium") and has_gunghap_or_synastry:
        inc.add("r08_gunghap_auto")
    if tier in ("dual", "master", "premium"):
        inc.add("r08_new5_auto")
        # 2026-08-30 추가 — r12_schema_link(스키마 태그 명시 규칙)는 r08_new5_auto와
        # 정확히 같은 조건(dual 이상)에서만 의미가 있음 — 그 5개 시스템 자체가 없는
        # mini/light/single에서는 불필요.
        inc.add("r12_schema_link")

    if tier == "premium":
        inc.add("r09a_lts")
    if tier == "premium" and has_behavior:
        inc.add("r09a1_behavior")
    if tier in ("dual", "master", "premium"):
        inc.add("r09b_action_plan")
    if tier in ("single", "dual", "master", "premium"):
        inc.add("r09c_opp_risk")

    if has_questions:
        inc |= RULE10_FAMILY
        if tier in ("dual", "master", "premium") and has_astrology:
            inc.add("r10d")
            inc.add("r10e")

    return inc


FIXTURES = {
    "mini": ENGINE_DIR / "test/out-mini.json",
    "light": ENGINE_DIR / "test/out-light.json",
    "single": ENGINE_DIR / "test/out-single.json",
    "dual": ENGINE_DIR / "test/out-dual.json",
    "master": ENGINE_DIR / "test/out-master.json",
    "premium": ENGINE_DIR / "test/out-behavior.json",
}

# gunghap/astrology_synastry 필드가 실제로 있는 픽스처 — 위 FIXTURES는 전부 그 필드가 없는
# 경우라서, r08_gunghap_auto가 "필드 있으면 포함" 방향으로도 실제로 토글되는지는 이 두
# 픽스처로 따로 검증해야 한다(그렇지 않으면 이 규칙이 사실상 죽은 코드로 항상 제외되는
# 채로 통과할 위험이 있음).
GUNGHAP_FIXTURES = {
    "single_with_gunghap": (ENGINE_DIR / "test/out-gunghap.json", "single"),
    "master_with_synastry": (ENGINE_DIR / "test/out-synastry.json", "master"),
}


def load(tier):
    return json.loads(FIXTURES[tier].read_text(encoding="utf-8"))


def check_rule5_untouched():
    """규칙 5/5-A/5-B가 절대 손대지 않은 원문 그대로인지 — 세 조각을 이어붙인 텍스트가
    SYSTEM_PROMPT 원문 안에 정확히 그 순서ㆍ그 문자 그대로 연속으로 존재해야 한다."""
    combined = br._PROMPT_BLOCKS["r05"] + "\n" + br._PROMPT_BLOCKS["r05a"] + "\n" + br._PROMPT_BLOCKS["r05b"]
    ok = combined in br.SYSTEM_PROMPT
    for rid in ("r05", "r05a", "r05b"):
        for tier in FIXTURES:
            computed = load(tier)
            assert br._RULE_META[rid]["tier_condition"](tier, computed) is True, (
                f"{rid}는 어떤 티어에서도 항상 포함이어야 하는데 tier={tier}에서 조건이 False"
            )
    return ok


def check_order_preserved():
    """_PROMPT_RULE_ORDER가 SYSTEM_PROMPT 안에서 실제로 등장하는 순서와 같은지 확인."""
    positions = []
    cursor = 0
    for rid in br._PROMPT_RULE_ORDER:
        block = br._PROMPT_BLOCKS[rid]
        idx = br.SYSTEM_PROMPT.find(block, cursor)
        if idx == -1:
            return False, rid
        positions.append(idx)
        cursor = idx + len(block)
    return positions == sorted(positions), None


def main():
    print("=" * 100)
    print("A. 규칙 5/5-A/5-B 원문 보존 검증")
    print("=" * 100)
    ok = check_rule5_untouched()
    print(f"  규칙5+5-A+5-B 연속 원문 일치: {'PASS' if ok else 'FAIL'}")
    if not ok:
        raise SystemExit("치명적 실패 — 규칙5/5-A/5-B가 원문과 다름, 배포 중단")

    print()
    print("=" * 100)
    print("B. 조립 순서 보존 검증")
    print("=" * 100)
    order_ok, bad_rid = check_order_preserved()
    print(f"  순서 보존: {'PASS' if order_ok else f'FAIL(rule_id={bad_rid})'}")
    if not order_ok:
        raise SystemExit("치명적 실패 — 조립 순서가 원문 등장 순서와 다름")

    print()
    print("=" * 100)
    print("C. 스키마 규칙(0번, 형식) 항상 포함 검증")
    print("=" * 100)
    for tier in FIXTURES:
        computed = load(tier)
        assert br._RULE_META["r00"]["tier_condition"](tier, computed) is True
    print("  r00(JSON 따옴표 형식 규칙) 전 티어 포함: PASS")

    schema_tok = toklen(json.dumps(br.REPORT_SCHEMA, ensure_ascii=False))
    baseline_sys_tok = toklen(br.SYSTEM_PROMPT)

    print()
    print("=" * 100)
    print("D. 티어별 MISSING/EXTRA/BEFORE-AFTER 실측")
    print("=" * 100)
    print(f"  BEFORE(고정 SYSTEM_PROMPT 전체, 모든 티어 공통): {baseline_sys_tok} 토큰")
    print(f"  도구 스키마(REPORT_SCHEMA, 모든 티어 공통, 변경 없음): {schema_tok} 토큰")
    print()

    any_fail = False
    summary_rows = []
    for tier, path in FIXTURES.items():
        computed = load(tier)
        manifest = br.get_prompt_rule_manifest(tier, computed)
        actual_included = {m["rule_id"] for m in manifest if m["included"]}
        expected_included = expected_for(tier, computed)

        missing = expected_included - actual_included  # 필요한데 빠짐 — 반드시 비어있어야 함
        extra = actual_included - expected_included     # 불필요한데 남음 — 반드시 비어있어야 함
        removed = ALL_RULE_IDS - actual_included
        retained = actual_included

        assembled = br.build_system_prompt(tier, computed)
        assembled_tok = toklen(assembled)
        computed_tok = toklen(json.dumps(computed, ensure_ascii=False, indent=2))
        total_input_tok = assembled_tok + schema_tok + computed_tok

        status = "PASS" if (not missing and not extra) else "FAIL"
        if status == "FAIL":
            any_fail = True

        print(f"  --- tier={tier} [{status}] (fixture: {path.name}) ---")
        print(f"    SYSTEM_PROMPT 실측: BEFORE {baseline_sys_tok} -> AFTER {assembled_tok} "
              f"토큰 (절감 {baseline_sys_tok - assembled_tok}, {(1 - assembled_tok/baseline_sys_tok)*100:.1f}%)")
        print(f"    computed.json 실측: {computed_tok} 토큰")
        print(f"    총 입력 추정(SYSTEM_PROMPT+스키마+computed.json): {total_input_tok} 토큰")
        print(f"    RETAINED({len(retained)}개): {sorted(retained)}")
        print(f"    REMOVED({len(removed)}개): {sorted(removed)}")
        print(f"    MISSING(반드시 비어있어야 함, {len(missing)}개): {sorted(missing)}")
        print(f"    EXTRA(반드시 비어있어야 함, {len(extra)}개): {sorted(extra)}")
        print()

        summary_rows.append((tier, assembled_tok, computed_tok, total_input_tok, status))

    print("=" * 100)
    print("E. 요약표")
    print("=" * 100)
    print(f"  {'tier':8s} {'SYS(after)':>11s} {'computed':>10s} {'총입력':>10s} {'검증':>6s}")
    for tier, sys_tok, cm_tok, tot_tok, status in summary_rows:
        print(f"  {tier:8s} {sys_tok:11d} {cm_tok:10d} {tot_tok:10d} {status:>6s}")

    print("=" * 100)
    print("F. r08_gunghap_auto DATA_DEPENDENT 토글 검증(필드가 실제로 있을 때 포함되는가)")
    print("=" * 100)
    for label, (path, tier) in GUNGHAP_FIXTURES.items():
        computed = json.loads(path.read_text(encoding="utf-8"))
        manifest = br.get_prompt_rule_manifest(tier, computed)
        included = {m["rule_id"] for m in manifest if m["included"]}
        has_it = "r08_gunghap_auto" in included
        status = "PASS" if has_it else "FAIL"
        if not has_it:
            any_fail = True
        print(f"  {label} (tier={tier}, fixture={path.name}): r08_gunghap_auto 포함 여부={has_it} [{status}]")

    print()
    print("=" * 100)
    print("G. r12_schema_link — SYSTEM_PROMPT 필드 참조와 REPORT_SCHEMA 자동 대조")
    print("   (2026-09-01 D-2 갱신: system_sections 태그 대신 new_reference_systems.X 필드 참조)")
    print("=" * 100)
    r12_text = br._PROMPT_BLOCKS["r12_schema_link"]
    schema_enum = set(
        br.REPORT_SCHEMA["input_schema"]["properties"]["system_sections"]["items"]["properties"]["system"]["enum"]
    )
    nrs_keys = set(br.REPORT_SCHEMA["input_schema"]["properties"]["new_reference_systems"]["properties"].keys())
    new5_systems = {"tojeong", "yukhyo", "seongmyeonghak", "pungsu", "taekil"}
    g_fail = False
    for name in sorted(new5_systems):
        in_prompt = f"new_reference_systems.{name}" in r12_text
        # 하위호환 경로(system_sections enum)도 여전히 존재해야 하고, 신설 경로
        # (new_reference_systems 객체 key)도 함께 존재해야 함 — 둘 중 하나라도 없으면 FAIL.
        in_schema = name in schema_enum and name in nrs_keys
        status = "PASS" if (in_prompt and in_schema) else "FAIL"
        if status == "FAIL":
            g_fail = True
            any_fail = True
        print(f"  {name:16s} r12 블록에 등장={in_prompt}  REPORT_SCHEMA enum에 존재={in_schema} [{status}]")
    if not new5_systems.issubset(schema_enum):
        print(f"  경고: REPORT_SCHEMA enum에 없는 신규5개 시스템: {new5_systems - schema_enum}")
        g_fail = True
        any_fail = True
    print(f"  종합: {'PASS' if not g_fail else 'FAIL'}")

    print()
    if any_fail:
        raise SystemExit("치명적 실패 — 하나 이상의 검증에서 MISSING/EXTRA/토글 실패 발생, 배포 중단")
    print("전체 PASS — 모든 티어에서 MISSING/EXTRA 없이 필요한 규칙만 정확히 조건부 조립됨")


if __name__ == "__main__":
    main()
