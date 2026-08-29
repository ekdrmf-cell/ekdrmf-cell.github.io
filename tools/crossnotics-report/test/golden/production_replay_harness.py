"""PRODUCTION PIPELINE REPLAY / GOLDEN TEST HARNESS.

목적 — Claude_Code_Memory_to_Validator_Enforcement_Protocol.txt의 요구사항을 그대로
구현한다: "MEMORY를 읽었다/기억하겠다"가 아니라, 실제 production 코드 경로를 그대로
재생(replay)해서 과거에 실제로 터졌던 오류들이 다시 발생하면 자동으로 FAIL하는
회귀 하네스.

**절대 원칙 — 별도의 "비슷한 구현"을 만들지 않는다.**
아래에서 부르는 `pipeline.run_full_pipeline()`은 이 프로젝트가 실제 고객 주문을
처리할 때(webapp/app.py) 호출하는 바로 그 함수다. 이 하네스는 그 함수를 import해서
그대로 호출할 뿐, 엔진ㆍLLM 호출ㆍSYSTEM_PROMPTㆍparserㆍvalidatorㆍPDF renderer
중 어느 것도 재구현하지 않는다.

    Production               이 하네스
    ────────────             ────────────
    webapp/app.py       →    이 파일이 직접 import
        │
        ▼
    pipeline.run_full_pipeline()   (동일 함수, 동일 코드)
        │
        ├─ node run.js                    (실제 엔진, subprocess)
        ├─ python build_report.py         (실제 LLM 호출 + 실제 SYSTEM_PROMPT
        │                                  + 실제 REPORT_SCHEMA + 실제 model/params
        │                                  + 실제 parser(tool_use 파싱) + 실제
        │                                  validator 전부, subprocess)
        └─ python report_kit.py           (실제 PDF renderer + 실제 PDF validator,
                                            subprocess)

**주의 — 실행하면 실제 비용이 발생한다.** `run()`을 호출하는 순간 build_report.py의
call_llm()이 실제 Anthropic API를 호출한다. 사용자의 명시적 승인 없이 이 스크립트의
run()/`if __name__ == "__main__"` 경로를 실행하지 말 것(ask_before_spending_api_money
메모리). CLI로 직접 실행할 때도 실수로 비용이 나가는 걸 막기 위해 별도 플래그를
요구한다.

GOLDEN CASE 설계 — 실제로 이 세션에서 재현ㆍ발견됐던 결함 7가지를, "새 가짜 고객"이
아니라 **실제로 그 결함이 났던 진짜 손님(최광호, premium)의 실제 intake.json**
하나로 전부 검사한다. premium 티어라 7개 관심사(용어ㆍQ&Aㆍhouseㆍrulerㆍ타로 개수ㆍ
신규 섹션ㆍPDF 텍스트ㆍ페이지 수) 전부를 커버하므로, 굳이 케이스마다 별도 API 호출을
만들지 않는다 — 실제 파이프라인 실행 1회 + 그 결과물에 대한 7갈래 검사로 비용을
아낀다(같은 이유로 프롬프트 규칙 5-A번 "% 지어내지 않기"와 같은 원칙: 근거 없이
돈을 늘리지 않는다).

사용법(실제 실행 전 반드시 사용자 승인 받을 것):
    cd tools/crossnotics-report
    python test/golden/production_replay_harness.py --yes-i-know-this-costs-money

과거 산출물만으로 이 하네스의 검사 로직 자체를 점검하려면(비용 0, 이미 존재하는
report.json/computed.json/pdf만 재사용):
    python test/golden/production_replay_harness.py --dry-run-existing <order_id>
"""
import io
import contextlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPORT_DIR = HERE.parent.parent
sys.path.insert(0, str(REPORT_DIR / "webapp"))
sys.path.insert(0, str(REPORT_DIR))

import pipeline  # noqa: E402 — webapp/pipeline.py, 실제 production 오케스트레이터(재구현 아님)
import build_report as br  # noqa: E402 — 실제 production 검증 함수 재사용(재구현 아님)
from pypdf import PdfReader  # noqa: E402


def _load_json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


# ============================================================
# 케이스별 검사 함수 — 전부 (report, computed, pdf_path, result) -> [(이름, 통과여부, 상세)]
# 판정 로직 자체도 가능한 한 build_report.py의 실제 check_* 함수를 그대로 호출해서
# 재사용한다(별도 판정 기준을 새로 만들지 않는다).
# ============================================================

def check_glossary_no_duplicate(report, computed, pdf_path, result):
    """CASE 001 — glossary 중복. 실제로 재현됐던 "정관 뜻풀이 두 번 반복" 버그와 같은
    부류: system_sections 각 body 안에서 같은 뜻풀이 문구(괄호 안 10자 이상)가 두 번
    이상 등장하면 FAIL."""
    findings = []
    for sec in report.get("system_sections") or []:
        body = sec.get("body") or ""
        seen = set()
        for m in re.finditer(r"[가-힣ㆍ]{2,10}\(([^()]{10,})\)", body):
            gloss = m.group(1)
            if gloss in seen:
                findings.append(f"{sec.get('system')}: 뜻풀이 중복 — {gloss[:30]}")
            seen.add(gloss)
    return [("용어 뜻풀이 중복 없음", not findings, "; ".join(findings))]


def check_qa_not_avoidant(report, computed, pdf_path, result):
    """CASE 002 — Q&A 회피. build_report.check_qa_avoidance_ending과 같은 판정
    기준(회피 표현으로 답변이 끝나는가)을 그대로 재사용."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        br.check_qa_avoidance_ending(report)
    out = buf.getvalue()
    return [("Q&A 회피형 종료 없음", "⚠" not in out, out.strip())]


def check_house_ruler_grounded(report, computed, pdf_path, result):
    """CASE 003 — house ruler 표현. build_report.check_aspect_consistency와 같은
    성격(본문 주장과 computed 실측값 대조) — "N하우스의 주인은 X" 패턴을 실제
    astrology.house_rulers와 대조한다."""
    astro = computed.get("astrology") or {}
    rulers = {r["house"]: r["ruler"] for r in (astro.get("house_rulers") or [])}
    findings = []
    all_text = " ".join(
        (sec.get("body") or "") for sec in (report.get("system_sections") or [])
        if sec.get("system") == "astrology"
    )
    for m in re.finditer(r"(\d+)하우스의 주인은 ([가-힣]+)", all_text):
        house, claimed = int(m.group(1)), m.group(2)
        real = rulers.get(house)
        if real and claimed != real:
            findings.append(f"{house}하우스 주인을 '{claimed}'라고 썼는데 실제는 '{real}'")
    return [("하우스 주인 표현이 실제 계산값과 일치(또는 언급 없음)", not findings, "; ".join(findings))]


def check_tarot_count_accurate(report, computed, pdf_path, result):
    """CASE 004 — 숫자 변조. build_report.check_tarot_suit_tally를 그대로 재사용."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        br.check_tarot_suit_tally(report, computed)
    out = buf.getvalue()
    return [("타로 계열 개수 정확", "⚠" not in out, out.strip())]


def check_no_missing_sections(report, computed, pdf_path, result):
    """CASE 005 — 정보 누락. build_report.check_required_tier_sections를 그대로
    재사용(신규 5개 시스템 섹션 등 티어별 필수 항목)."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        br.check_required_tier_sections(report, computed)
    out = buf.getvalue()
    return [("필수 섹션 누락 없음", "⚠" not in out, out.strip())]


def check_pdf_text_matches(report, computed, pdf_path, result):
    """CASE 006 — PDF 텍스트 변형. report_kit.check_pdf_text_roundtrip과 같은 목적을
    이 하네스 자체의 독립 코드로 다시 대조(같은 pypdf 라이브러리 사용, 판정 로직은
    이중 확인 차원에서 따로 씀)."""
    reader = PdfReader(str(pdf_path))
    full_text = "".join((p.extract_text() or "") for p in reader.pages)
    name = (computed.get("customer") or {}).get("name") or ""
    findings = []
    if name and name not in full_text:
        findings.append(f"고객 이름 '{name}'이 PDF 텍스트에서 안 보임")
    return [("PDF 텍스트에 핵심 정보 존재", not findings, "; ".join(findings))]


def check_page_count_reasonable(report, computed, pdf_path, result):
    """CASE 007 — 페이지 문제. run_full_pipeline()이 이미 계산한 page_status(카탈로그
    목표치의 60% 미만이면 REVIEW)를 그대로 인용 — 재계산하지 않는다."""
    return [(
        f"페이지 수 정상 범위({result.get('page_count')}p, 목표 {result.get('expected_pages')}p)",
        result.get("page_status") != "REVIEW",
        str(result.get("page_status")),
    )]


GOLDEN_CASES = [
    ("CASE 001 — glossary 중복", check_glossary_no_duplicate),
    ("CASE 002 — Q&A 회피", check_qa_not_avoidant),
    ("CASE 003 — house ruler 표현", check_house_ruler_grounded),
    ("CASE 004 — 숫자 변조(타로 계열 개수)", check_tarot_count_accurate),
    ("CASE 005 — 정보 누락(필수 섹션)", check_no_missing_sections),
    ("CASE 006 — PDF 텍스트 변형", check_pdf_text_matches),
    ("CASE 007 — 페이지 문제", check_page_count_reasonable),
]

# 실제로 이 7가지 결함이 재현ㆍ발견됐던 진짜 손님의 진짜 주문(가짜 고객 아님).
GOLDEN_FIXTURE = REPORT_DIR / "orders" / "20260829-010717_최광호" / "intake.json"


def _evaluate(report, computed, pdf_path, result):
    all_results = []
    for case_name, check_fn in GOLDEN_CASES:
        for name, ok, detail in check_fn(report, computed, pdf_path, result):
            all_results.append((case_name, name, ok, detail))

    print(f"\n{'=' * 60}")
    passed = 0
    for case_name, name, ok, detail in all_results:
        mark = "✓ PASS" if ok else "✗ FAIL"
        print(f"{mark}  [{case_name}] {name}")
        if not ok and detail:
            print(f"       {detail}")
        if ok:
            passed += 1
    total = len(all_results)
    print(f"\n{passed}/{total} 통과")
    return passed, total, all_results


def run(order_id="GOLDEN-001-choi-premium"):
    """실제 pipeline.run_full_pipeline()을 그대로 호출한다 — 별도 구현 없음.
    **이 호출 시점에 진짜 Anthropic API 비용이 발생한다.**"""
    intake = _load_json(GOLDEN_FIXTURE)
    print(f"=== 실제 production pipeline 실행: {order_id} (실제 API 호출 발생) ===")
    result = pipeline.run_full_pipeline(intake, order_id)

    order_dir = pipeline.ORDERS_DIR / order_id
    report = _load_json(order_dir / "report.json")
    computed = _load_json(order_dir / "computed.json")
    pdf_path = order_dir / "report.pdf"

    passed, total, all_results = _evaluate(report, computed, pdf_path, result)
    print(f"실제 비용: {result.get('cost')}")
    print(f"build_report.py 경고: {result.get('warnings')}")

    out = {
        "order_id": order_id, "passed": passed, "total": total,
        "cost": result.get("cost"), "warnings": result.get("warnings"),
        "cases": [{"case": c, "check": n, "ok": ok, "detail": d} for c, n, ok, d in all_results],
    }
    (HERE / "golden_results_latest.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return passed, total


def dry_run_existing(order_id):
    """비용 0 — 이미 존재하는 과거 산출물(report.json/computed.json/pdf)만 다시 읽어
    검사 로직 자체를 점검한다. 실제 API 호출 없음. 하네스 코드를 고친 뒤 "검사
    함수들이 제대로 동작하는가"만 무료로 확인하고 싶을 때 쓴다."""
    order_dir = pipeline.ORDERS_DIR / order_id
    report = _load_json(order_dir / "report.json")
    computed = _load_json(order_dir / "computed.json")
    pdf_path = order_dir / "report.pdf"
    fake_result = {"page_count": len(PdfReader(str(pdf_path)).pages), "expected_pages": None, "page_status": "UNKNOWN"}
    print(f"=== 기존 산출물로 검사 로직만 점검(비용 0): {order_id} ===")
    return _evaluate(report, computed, pdf_path, fake_result)


if __name__ == "__main__":
    if "--dry-run-existing" in sys.argv:
        idx = sys.argv.index("--dry-run-existing")
        order_id = sys.argv[idx + 1]
        dry_run_existing(order_id)
    elif "--yes-i-know-this-costs-money" in sys.argv:
        run()
    else:
        print("이 스크립트는 실제 Anthropic API 호출을 발생시켜 비용이 청구됩니다.")
        print("실행하려면: python production_replay_harness.py --yes-i-know-this-costs-money")
        print("비용 없이 검사 로직만 점검하려면: python production_replay_harness.py --dry-run-existing <order_id>")
        sys.exit(1)
