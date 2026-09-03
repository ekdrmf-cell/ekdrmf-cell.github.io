"""
#3 신규5개 시스템 개별화 회귀 테스트 — 2026-08-31, 2026-09-01(D-2 출력 위치 변경) 갱신.

목적: seongmyeonghak/pungsu/taekil이 이제 tojeong/yukhyo와 대칭적으로 각각 독립된
지시 단위(굵게 강조된 자기만의 문장)로 존재하는지 확인한다. 2026-09-01부터 5개
전부 출력 위치가 system_sections 태그에서 new_reference_systems.X 필드로 바뀌었으므로
검증 문자열도 그에 맞춰 갱신됐다. 실제 API 호출 없음.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPORT_DIR = HERE.parent
sys.path.insert(0, str(REPORT_DIR))
import build_report as br  # noqa: E402


def main():
    any_fail = False
    block = br._PROMPT_BLOCKS["r08_new5_auto"]

    print("=" * 100)
    print("1. 5개 시스템이 전부 r08_new5_auto 안에 new_reference_systems.X 필드로 존재하는지")
    print("=" * 100)
    for system in ("tojeong", "yukhyo", "seongmyeonghak", "pungsu", "taekil"):
        ok = f"new_reference_systems.{system}" in block
        status = "PASS" if ok else "FAIL"
        if not ok:
            any_fail = True
        print(f"  new_reference_systems.{system} 언급: [{status}]")

    print()
    print("=" * 100)
    print("2. seongmyeonghak/pungsu/taekil이 각각 독립된 굵게강조 단위로 개별화됐는지")
    print("   ('**new_reference_systems.X**' 형태로 각자 분리)")
    print("=" * 100)
    for system in ("seongmyeonghak", "pungsu", "taekil"):
        ok = f"**new_reference_systems.{system}**" in block
        status = "PASS" if ok else "FAIL"
        if not ok:
            any_fail = True
        print(f"  **new_reference_systems.{system}** 독립 단위로 존재: [{status}]")

    print()
    print("=" * 100)
    print("3. tojeong/yukhyo 기존 문구(내용) 변경 없이 그대로 유지되는지")
    print("=" * 100)
    checks = [
        ("tojeong 필드 매핑 문구 유지", "gwae의 세 조각을 엮어 올해 총운 섹션 하나" in block),
        ("yukhyo 필드 매핑 문구 유지", "bon_gwae/ji_gwae를 엮어 즉석 괘 섹션 하나" in block),
        ("yukhyo 톤 지시 유지", '"지금 이 순간 뽑아본" 톤 유지' in block),
        ("seongmyeonghak 필드 매핑 유지(요약 없음)", "letters/pairs/flow_summary를 엮은 이름 섹션" in block),
        ("pungsu 필드 매핑 유지(요약 없음)", "recommendations를 엮은 공간 배치 섹션" in block),
        ("taekil 필드 매핑 유지(요약 없음)", "good_days/avoid_days를 엮은 택일 섹션" in block),
        ("methodology_note 지시 유지", "methodology_note 취지를" in block),
        ("목표분량 정상 문구 유지", '"목표 분량"이 늘어나는 것도' in block),
        ("부록처럼 따로 놀면 안 됨 지시 유지(#2 규칙8 확장분)", "부록처럼 따로 놀면 안 됩니다" in block),
        ("억지 연결 금지 지시 유지(#2 규칙8 확장분)", "억지로 끼워 맞추지 마세요" in block),
    ]
    for label, ok in checks:
        status = "PASS" if ok else "FAIL"
        if not ok:
            any_fail = True
        print(f"  {label}: [{status}]")

    print()
    print("=" * 100)
    print("4. 티어 게이팅(DUAL/MASTER/PREMIUM) 문구가 그대로 유지되는지")
    print("=" * 100)
    gating_checks = [
        ("DUAL 이상 게이팅 유지", "DUAL 이상은 new_reference_systems.tojeong" in block),
        ("MASTER 이상 게이팅 유지", "MASTER" in block and "이상은 그에 더해 new_reference_systems.yukhyo" in block),
        ("PREMIUM 게이팅 유지", "PREMIUM은 그에 더해" in block),
    ]
    for label, ok in gating_checks:
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
