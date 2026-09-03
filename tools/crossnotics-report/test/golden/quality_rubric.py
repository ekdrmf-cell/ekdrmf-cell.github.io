"""API 탈피 가능성 조사 프로젝트 — 품질 루브릭 + Golden Dataset 채점기.

목적: "Claude API가 실제로 하는 해석 작업"을 대체할 후보(로컬 모델 등)를 평가할 때,
production이 이미 쓰고 있는 검증 함수를 **그대로 재사용**해서 채점한다(새 기준을
따로 만들지 않는다 — 그래야 "같은 기준으로 비교했다"고 말할 수 있다).

**중요 — Golden Dataset은 원본 그대로가 아니다.** 실제 발송된 리포트(최광호
premium)를 그대로 "정답"으로 쓰면 안 된다는 걸 이 조사 도중 실제로 확인함:
원본(raw)을 이 채점기로 돌려보니 12개 중 4개가 FAIL이었다(신규 5섹션 누락ㆍ용어
뜻풀이 누락ㆍ강조 부족ㆍ타로 개수 오류 — 전부 이미 알려진 진짜 버그). 그래서 Golden은
"원본 → build_report.py의 실제 검증/교정 파이프라인(apply_term_glosses_by_group,
ensure_required_new_engine_sections, ensure_emphasis, ensure_tarot_suit_tally,
sanitize_report)을 통과시킨 뒤 → 이 채점기로 재확인해서 남은 결함까지 라벨 붙인" 버전만
쓴다(scratchpad/golden_choi_premium_VERIFIED.json, 10/12 — 남은 2개는 코드로 안전하게
못 고치는 진짜 콘텐츠 이슈라고 명시적으로 라벨링됨). "검증 통과 = Golden"이지
"Claude가 썼다 = Golden"이 아니다.

세 계층으로 나눈다(A/B 구분 — 사용자 요구 그대로):

A. OBJECTIVE(코드, 비용 0) — build_report.py + report_kit.py의 실제 check_* 함수를
   그대로 호출. 환각ㆍ용어ㆍ숫자(타로)ㆍ개수(Q&A)ㆍ섹션 누락ㆍ중복ㆍplaceholderㆍ
   PDF 내용 보존ㆍ페이지 구조까지 포함. **알려진 한계 — 정직하게 밝힘**: "본문의
   특정 값이 computed.json 실제 값과 정말 일치하는가"(예: 일간을 다른 글자로
   바꿔치기)는 지금 순수 코드로는 완전히 못 잡는다 — 이건 verify_groundedness(LLM,
   B 계층)가 담당한다. JSON schema 위반은 normalize_to_schema()가 이미 자동
   보정하므로 "보정이 몇 건 필요했는가" 자체를 신호로 기록한다(0건이 이상적).

B. JUDGE(LLM 채점, 비용 발생) — 두 가지:
   B-1. verify_naturalness/verify_groundedness — build_report.py 기존 함수 그대로
        재사용(문장 자연스러움 9개 기준 + 근거 일치).
   B-2. judge_semantic_quality() — 이번에 신설. 사용자가 지정한 개인화ㆍQ&A 실답변
        여부ㆍ앞뒤 맥락ㆍ해석 깊이ㆍ상투적 문구ㆍ"나를 분석했다" 체감도를 1~5점
        구조화 점수로 강제 출력(도구 호출)받아 **정량 비교**가 가능하게 한다 — 텍스트
        "OK/문제 있음"이 아니라 숫자라 후보 모델끼리 직접 비교할 수 있다.

이 파일 자체는 어떤 리포트 내용도 새로 생성하지 않는다 — 이미 있는 report.json(골든
데이터든 후보 모델의 출력이든)을 채점만 한다.

사용법:
    cd tools/crossnotics-report
    python test/golden/quality_rubric.py --score <report.json> <computed.json>          # OBJECTIVE만(비용 0)
    python test/golden/quality_rubric.py --score <report.json> <computed.json> --judge  # OBJECTIVE + LLM 채점(비용 발생, 승인 필요)
"""
import contextlib
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPORT_DIR = HERE.parent.parent
sys.path.insert(0, str(REPORT_DIR))

import build_report as br  # noqa: E402 — 재구현 아님, production 검증 함수 재사용


# ============================================================
# 1) OBJECTIVE — 비용 0. build_report.py의 실제 check_* 함수를 그대로 호출한다.
# ============================================================
OBJECTIVE_CHECKS = [
    ("환각(지어낸 사실) 없음", lambda r, c: br.check_hallucination(r, br.collect_known_terms(c), br.collect_valid_years(c))),
    ("티어별 필수 섹션 존재", br.check_required_tier_sections),
    ("Q&A 개수ㆍ순서 일치", br.check_qa_count_and_order),
    ("placeholder/디버그 문구 없음", lambda r, c: br.check_leftover_placeholders(r)),
    ("어스펙트/하우스 근거 일치", br.check_aspect_consistency),
    ("확정적 표현(건강ㆍ임신ㆍ로또 등) 없음", lambda r, c: br.check_overclaim_topics(r)),
    ("Q&A 회피형 종료 없음", lambda r, c: br.check_qa_avoidance_ending(r)),
    ("Q&A ↔ 본문 문장 복사 없음", lambda r, c: br.check_qa_duplicates_sections(r)),
    ("unanswerable_reason 컴퓨터 말투 없음", lambda r, c: br.check_unanswerable_reason_tone(r)),
    ("용어 뜻풀이 누락 없음", lambda r, c: br.check_term_glosses(r)),
    ("강조 표시(**) 개수 기준 충족", lambda r, c: br.check_emphasis_markers(r)),
    ("타로 계열 개수 정확", br.check_tarot_suit_tally),
]


def score_objective(report, computed, pdf_path=None):
    """OBJECTIVE 계층 전체를 실행하고 (통과수, 전체, 상세리스트)를 반환한다.
    pdf_path를 주면 report_kit.py의 실제 PDF 검증 함수(재구현 아님)도 같이 돈다 —
    사용자가 지정한 "PDF 내용 보존"ㆍ"페이지 구조"를 포함시키기 위함."""
    results = []
    for name, fn in OBJECTIVE_CHECKS:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            try:
                fn(report, computed)
                out = buf.getvalue()
            except Exception as e:  # noqa: BLE001 — 채점기 자체가 후보 모델의 이상한 출력 때문에 죽으면 안 됨
                out = f"⚠ 채점 중 예외: {e}"
        ok = "⚠" not in out
        results.append((name, ok, out.strip()))

    if pdf_path is not None:
        sys.path.insert(0, str(REPORT_DIR))
        import report_kit as rk  # noqa: E402 — 재구현 아님, production PDF 검증 함수 재사용
        name_ = (computed.get("customer") or {}).get("name") or "고객"
        for check_name, fn, fn_args in [
            ("PDF 내용 보존(고객이름ㆍ섹션ㆍQ&A)", rk.check_pdf_text_roundtrip, (pdf_path, report, computed, name_)),
            ("PDF 페이지 구조(빈페이지ㆍ페이지수)", rk.check_pdf_structural_integrity, (pdf_path, computed.get("tier"))),
        ]:
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                try:
                    fn(*fn_args)
                    out = buf.getvalue()
                except Exception as e:  # noqa: BLE001
                    out = f"⚠ 채점 중 예외: {e}"
            ok = "⚠" not in out
            results.append((check_name, ok, out.strip()))

    passed = sum(1 for _, ok, _ in results if ok)
    return passed, len(results), results


# ============================================================
# 2) JUDGE — LLM 채점(비용 발생, 호출마다 GROUNDEDNESS_MODEL 1회). 재구현 아님 —
#    build_report.py의 verify_naturalness/verify_groundedness를 그대로 부른다.
#    두 함수는 원래 print()만 하고 값을 반환하지 않으므로, 여기서 표준출력을 캡처해
#    "OK"인지 아닌지로 판정한다(호출부만 감쌌을 뿐 판정 로직 자체는 그대로).
# ============================================================
def score_judge(report, computed):
    results = []
    for name, fn, args in [
        ("표현 자연스러움(verify_naturalness, 9개 기준)", br.verify_naturalness, (report,)),
        ("근거 일치(verify_groundedness)", br.verify_groundedness, (report, computed)),
    ]:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            fn(*args)
        out = buf.getvalue()
        ok = "✓" in out or out.strip().upper().startswith("OK")
        results.append((name, ok, out.strip()))
    passed = sum(1 for _, ok, _ in results if ok)
    return passed, len(results), results


# ============================================================
# B-2) 신설 — 사용자가 지정한 의미/품질 기준을 1~5점 구조화 점수로 강제 출력받는다.
# verify_naturalness(문장 자연스러움만 봄)와 겹치지 않는, "이 손님한테 맞춤인가ㆍ
# 실제로 도움이 되는가" 쪽 기준. 텍스트 "OK/문제있음"이 아니라 숫자라서 후보 모델끼리
# 직접 비교 가능하다 — 이게 사용자가 요구한 "정량적 품질 평가"의 핵심.
#
# 2026-08-30 수정 — 사용자 지적 두 가지 반영:
# 1. "나를 분석했다는 느낌"(feels_personally_analyzed)은 이 상품의 핵심 가치와 직결되므로
#    나머지 5개와 같은 무게의 항목 하나가 아니라 **게이팅(gating) 지표**로 분리한다 —
#    다른 5개가 다 높아도 이 항목이 기준 미달이면 전체 FAIL로 취급한다.
# 2. Golden은 "지금 최고 결과"가 아니라 "정해진 합격선을 통과한 결과"여야 한다 — 그래서
#    점수 자체가 아니라 아래 PASS_THRESHOLDS(이 프로젝트가 이미 스스로 요구해온 품질
#    규칙에서 도출한 합격선)를 기준으로 PASS/FAIL을 가른다. Claude(golden)가 이 채점을
#    받아도 자동으로 만점/합격 처리하지 않는다 — 실제로 이 기준에 못 미치면 Claude
#    결과도 그대로 FAIL로 기록한다(passes_bar 참고).
# ============================================================
_QUALITY_SCORE_SCHEMA = {
    "name": "submit_quality_scores",
    "description": "리포트의 의미/품질을 채점해 제출한다. feels_personally_analyzed는 이 "
                   "상품의 핵심 가치이므로 특히 엄격하게(관대하게 후하지 않게) 채점할 것.",
    "input_schema": {
        "type": "object",
        "properties": {
            "feels_personally_analyzed": {"type": "integer", "minimum": 1, "maximum": 5,
                "description": "[핵심 게이팅 지표] 고객이 읽었을 때 \"나를 분석했다\"고 느낄 정도(1=일반 데이터 나열처럼 느껴짐, 5=나를 오래 아는 사람이 써준 것 같음). 이 상품의 존재 이유와 직결되는 항목이니 다른 항목보다 엄격하게 채점하세요."},
            "personalization": {"type": "integer", "minimum": 1, "maximum": 5,
                "description": "개인화 정도 — 이 손님의 실제 계산값이 아니면 나올 수 없는 문장인가(1=아무 손님에게나 복붙해도 말 되는 문구, 5=이 손님 고유 데이터로만 성립하는 문장)"},
            "qa_actually_answers": {"type": "integer", "minimum": 1, "maximum": 5,
                "description": "Q&A가 질문에 실제로 답했는가(1=회피/동문서답, 5=질문의 핵심 의도에 구체적 결론으로 답함)"},
            "context_consistency": {"type": "integer", "minimum": 1, "maximum": 5,
                "description": "앞뒤 맥락 연결 — 리포트 전체에서 같은 인물상이 모순 없이 이어지는가(1=섹션끼리 따로 놀거나 모순, 5=하나의 일관된 이야기)"},
            "interpretive_depth": {"type": "integer", "minimum": 1, "maximum": 5,
                "description": "해석의 깊이 — 계산값→성향→왜 그런지 이유까지 들어갔는가(1=공식만 읽어줌, 5=이유와 실제 삶의 장면까지 이어짐)"},
            "cliche_free": {"type": "integer", "minimum": 1, "maximum": 5,
                "description": "상투적인 운세 문구를 피했는가(1=\"좋은 일이 생길 것입니다\" 류 뻔한 문구 다수, 5=전혀 없음)"},
            "notes": {"type": "string", "description": "점수 근거를 1~2문장으로, feels_personally_analyzed는 반드시 근거 포함"},
        },
        "required": ["feels_personally_analyzed", "personalization", "qa_actually_answers",
                     "context_consistency", "interpretive_depth", "cliche_free", "notes"],
    },
}

# 합격선 — "지금 나온 것 중 제일 나은 값"이 아니라, 이 프로젝트가 SYSTEM_PROMPT 5번ㆍ
# 5-A번 규칙에서 이미 스스로 요구해온 수준을 숫자로 못박은 것. GATING_CRITERION은
# 이 값 미만이면 나머지 점수와 무관하게 전체 FAIL — 이 상품의 핵심 가치라서.
PASS_THRESHOLDS = {
    "feels_personally_analyzed": 4,  # 게이팅 지표 — 미달 시 전체 FAIL
    "personalization": 4,
    "qa_actually_answers": 4,
    "context_consistency": 3,
    "interpretive_depth": 3,
    "cliche_free": 4,
}
GATING_CRITERION = "feels_personally_analyzed"


def passes_bar(scores):
    """scores(judge_semantic_quality의 반환값)가 PASS_THRESHOLDS를 전부 만족하는지
    판정한다. GATING_CRITERION 미달이면 다른 게 아무리 높아도 무조건 FAIL —
    "Claude가 냈다"는 이유로 자동 합격시키지 않는다."""
    failures = [k for k, min_v in PASS_THRESHOLDS.items() if scores.get(k, 0) < min_v]
    gating_failed = scores.get(GATING_CRITERION, 0) < PASS_THRESHOLDS[GATING_CRITERION]
    return (not failures), failures, gating_failed


def judge_semantic_quality(report, computed, model=None):
    """B-2 채점을 실행하고 구조화된 점수 dict를 반환한다. model을 안 주면
    build_report.GROUNDEDNESS_MODEL(현재 haiku)을 쓴다 — 후보 로컬 모델과 비교할 때도
    항상 같은 model로 채점해야 "같은 잣대"가 된다(채점자를 고정하고 생성자만 바꿔서
    비교하는 게 핵심)."""
    import anthropic
    client = anthropic.Anthropic()
    judge_model = model or br.GROUNDEDNESS_MODEL
    prompt = (
        "아래는 사주ㆍ점성술ㆍ타로 통합 리포트의 계산값과, 그 계산값으로 작성된 리포트 "
        "본문입니다. 문장 표현이 아니라(그건 이미 별도로 평가함) 다음 기준으로만 "
        "1~5점씩 채점하세요 — 반드시 근거를 들어 판단하고, 애매하면 중간값(3)이 아니라 "
        "실제로 본문에서 확인되는 근거를 기준으로 판정하세요. **feels_personally_analyzed는 "
        "이 상품이 파는 것의 핵심이므로, 후하게 주지 말고 정말로 이 손님만의 이야기로 "
        "읽히는지 엄격하게 보세요.**\n\n"
        f"[계산값]\n```json\n{json.dumps(computed, ensure_ascii=False)}\n```\n\n"
        f"[리포트 본문]\n```json\n{json.dumps(report, ensure_ascii=False)}\n```"
    )
    # 2026-09-03 — GROUNDEDNESS_MODEL 기본값이 claude-sonnet-5로 바뀌면서 이 채점자도
    # 자동으로 sonnet-5를 쓰게 됨(judge_model = model or br.GROUNDEDNESS_MODEL). sonnet-5는
    # thinking을 명시 안 하면 기본으로 켜지므로, build_report.py의 다른 실제 API 호출들과
    # 동일하게 명시적으로 꺼서 채점 스키마 출력이 잘리지 않게 한다 — 채점 기준ㆍ프롬프트는
    # 그대로.
    resp = client.messages.create(
        model=judge_model,
        max_tokens=1024,
        thinking={"type": "disabled"},
        tools=[_QUALITY_SCORE_SCHEMA],
        tool_choice={"type": "tool", "name": "submit_quality_scores"},
        messages=[{"role": "user", "content": prompt}],
    )
    for block in resp.content:
        if block.type == "tool_use" and block.name == "submit_quality_scores":
            return block.input
    raise RuntimeError("judge_semantic_quality: 모델이 submit_quality_scores를 호출하지 않음")


def score_report(report, computed, pdf_path=None, include_judge=False, include_semantic=False):
    obj_passed, obj_total, obj_results = score_objective(report, computed, pdf_path=pdf_path)
    print(f"\n=== A. OBJECTIVE(비용 0) — {obj_passed}/{obj_total} ===")
    for name, ok, detail in obj_results:
        mark = "✓" if ok else "✗"
        print(f"{mark} {name}")
        if not ok:
            print(f"    {detail}")

    out = {
        "objective": {"passed": obj_passed, "total": obj_total,
                      "items": [{"name": n, "ok": ok, "detail": d} for n, ok, d in obj_results]},
    }

    if include_judge:
        j_passed, j_total, j_results = score_judge(report, computed)
        print(f"\n=== B-1. JUDGE — 문장/근거(LLM, 비용 발생) — {j_passed}/{j_total} ===")
        for name, ok, detail in j_results:
            mark = "✓" if ok else "✗"
            print(f"{mark} {name}")
            if not ok:
                print(f"    {detail}")
        out["judge"] = {"passed": j_passed, "total": j_total,
                         "items": [{"name": n, "ok": ok, "detail": d} for n, ok, d in j_results]}

    if include_semantic:
        scores = judge_semantic_quality(report, computed)
        ok, failures, gating_failed = passes_bar(scores)
        print(f"\n=== B-2. JUDGE — 의미/품질(LLM, 비용 발생) ===")
        gate_mark = "✓" if scores.get(GATING_CRITERION, 0) >= PASS_THRESHOLDS[GATING_CRITERION] else "✗"
        print(f"  [게이팅] {gate_mark} {GATING_CRITERION}: {scores.get(GATING_CRITERION)} (합격선 {PASS_THRESHOLDS[GATING_CRITERION]}+)")
        for k, v in scores.items():
            if k in (GATING_CRITERION, "notes"):
                continue
            mark = "✓" if v >= PASS_THRESHOLDS.get(k, 0) else "✗"
            print(f"  {mark} {k}: {v} (합격선 {PASS_THRESHOLDS.get(k, '-')}+)")
        print(f"  notes: {scores.get('notes')}")
        print(f"  => 합격선 종합: {'PASS' if ok else 'FAIL'}"
              + (f" (게이팅 지표 미달 — 다른 점수와 무관하게 FAIL)" if gating_failed else "")
              + (f" — 미달 항목: {failures}" if failures and not gating_failed else ""))
        out["semantic_scores"] = scores
        out["semantic_pass"] = {"ok": ok, "failures": failures, "gating_failed": gating_failed}

    return out


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--score" not in sys.argv or len(args) < 2:
        print("사용법: python quality_rubric.py --score <report.json> <computed.json> [<pdf경로>] [--judge] [--semantic]")
        sys.exit(1)
    report = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    computed = json.loads(Path(args[1]).read_text(encoding="utf-8"))
    pdf_path = args[2] if len(args) > 2 else None
    include_judge = "--judge" in sys.argv
    include_semantic = "--semantic" in sys.argv
    if include_judge or include_semantic:
        n_calls = (2 if include_judge else 0) + (1 if include_semantic else 0)
        print(f"⚠ 실제 API 호출 {n_calls}회 발생(GROUNDEDNESS_MODEL 기준, 비용 소액).")
    result = score_report(report, computed, pdf_path=pdf_path, include_judge=include_judge, include_semantic=include_semantic)
    out_path = Path(args[0]).with_suffix(".quality_score.json")
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n저장: {out_path}")
