"""
품질 개선 폐쇄 루프(카테고리9 결정론적 탐지 + naturalness 구조화 + targeted rewrite
검증 파이프라인) 회귀 테스트 — 2026-09-01.

#7~#14 공통원인(A: 근거ㆍ연결 부족=카테고리1/5/6/7, B: 내부 필드명 노출=카테고리9) 대응.
이 세션에서 설계한 폐쇄 루프(생성→감지→path검증→재작성→재검증→채택/롤백)를 실제 API
없이 전부 검증한다. _call_targeted_rewrite_llm/verify_naturalness의 실제 API 경로는
호출하지 않는다(전부 call_fn/rewrite_fn/groundedness_call_fn으로 mock).
"""
import json
import os
import re
import sys
from pathlib import Path

os.environ["CROSSNOTICS_OFFLINE_TEST_MODE"] = "1"
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-test-not-real")

HERE = Path(__file__).resolve().parent
REPORT_DIR = HERE.parent
ENGINE_DIR = REPORT_DIR.parent / "crossnotics-engine"

sys.path.insert(0, str(REPORT_DIR))
import build_report as br  # noqa: E402
import api_usage  # noqa: E402


def _fake_report():
    return {
        "intro": "이 사람은 원칙을 중시하는 성향이 뚜렷합니다.",
        "toc_preview": None,
        "system_sections": [
            {
                "system": "saju", "heading": "네 기둥 총론",
                "body": "정관은 명예와 책임, 편재는 유동적인 돈, 칠살은 부담이자 추진력입니다. 이 세 십신의 조합은 안정과 도전을 동시에 추구하는 성향을 만듭니다.",
                "key_insight": "안정과 도전의 공존", "takeaways": ["안정", "도전"],
            },
            {
                "system": "astrology", "heading": "하우스로 보는 삶의 영역",
                "body": "7하우스는 파트너십을 보는 자리이고, 목성은 확장을 뜻하며, 물고기자리는 감수성을 뜻합니다. 따라서 관계에서는 감정적으로 깊이 몰입하는 편입니다.",
                "key_insight": "", "takeaways": [],
            },
        ],
        "new_reference_systems": {
            "taekil": {
                "heading": "택일", "body": "앞으로 30일 안에서 흐름이 좋은 날은 9월 6일입니다.",
                "key_insight": "", "takeaways": [],
            },
        },
        "cross_analysis": {"heading": "교차분석", "body": "사주와 점성술 모두 오행 균형이 특정 방향으로 몰려 있습니다(oheng_count 기준)."},
        "opportunities": [{"title": "기회1", "body": "새로운 시도에 유리한 시기입니다."}],
        "risks": [{"title": "위험1", "body": "무리한 확장은 피하는 것이 좋습니다."}],
        "action_plan": {"heading": "h", "steps": [{"label": "l", "desc": "d"}]},
        "question_answers": [
            {"question": "올해 이직할까요?", "answerability": "direct", "unanswerable_reason": None,
             "body": "지금은 준비하며 움직이는 쪽을 권합니다."},
        ],
        "long_term_strategy": None,
        "closing": "앞으로도 꾸준히 나아가시길 바랍니다.",
    }


class _FakeUsage:
    def __init__(self, input_tokens=10, output_tokens=5):
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens


class _FakeToolUseBlock:
    def __init__(self, name, input_):
        self.type = "tool_use"
        self.name = name
        self.input = input_


class _FakeResponse:
    def __init__(self, content, usage=None, stop_reason="end_turn"):
        self.content = content
        self.usage = usage or _FakeUsage()
        self.stop_reason = stop_reason


def test1_valid_category5_path():
    report = _fake_report()
    issue = {
        "section_kind": "system_sections", "index": 0, "field": "body",
        "category": 5,
        "quoted_sentence": "정관은 명예와 책임, 편재는 유동적인 돈, 칠살은 부담이자 추진력입니다.",
        "reason": "용어 나열 후 결론",
    }
    path, err = br.resolve_naturalness_issue_path(report, issue)
    return [
        ("정확한 path 생성됨", path == ("system_sections", 0, "body")),
        ("에러 없음", err is None),
    ]


def test2_invalid_section_index():
    report = _fake_report()
    issue = {
        "section_kind": "system_sections", "index": 999, "field": "body",
        "category": 5, "quoted_sentence": "아무거나", "reason": "r",
    }
    path, err = br.resolve_naturalness_issue_path(report, issue)
    issue2 = {
        "section_kind": "not_a_real_section", "index": 0, "field": "body",
        "category": 5, "quoted_sentence": "아무거나", "reason": "r",
    }
    path2, err2 = br.resolve_naturalness_issue_path(report, issue2)
    return [
        ("존재하지 않는 index -> path None", path is None),
        ("존재하지 않는 index -> 에러 사유 있음", bool(err)),
        ("허용 안 된 section_kind -> path None", path2 is None),
    ]


def test3_non_string_field_blocked():
    report = _fake_report()
    # question_answers[0].unanswerable_reason은 None(문자열 아님)
    issue = {
        "section_kind": "question_answers", "index": 0, "field": "unanswerable_reason",
        "category": 1, "quoted_sentence": "아무거나", "reason": "r",
    }
    path, err = br.resolve_naturalness_issue_path(report, issue)
    return [
        ("문자열 아닌 필드 -> path None", path is None),
        ("에러 사유에 타입 언급", "문자열이 아님" in (err or "")),
    ]


def test4_rewrite_wrong_type_rollback():
    report = _fake_report()
    computed = {"tier": "premium"}
    original = report["system_sections"][0]["body"]

    def bad_rewrite_fn(user_message):
        return None, _FakeUsage()  # 문자열이 아닌 값 반환

    issue = {
        "section_kind": "system_sections", "index": 0, "field": "body",
        "category": 5, "quoted_sentence": original[:20], "reason": "r",
    }
    result = br.rewrite_and_validate_issue(report, computed, issue, rewrite_fn=bad_rewrite_fn)
    return [
        ("잘못된 타입 결과 -> accepted False", result["accepted"] is False),
        ("stage가 type_check", result.get("stage") == "type_check"),
        ("report 원본 그대로 유지(rollback)", report["system_sections"][0]["body"] == original),
    ]


def test5_no_retry_on_same_issue():
    report = _fake_report()
    computed = {"tier": "premium"}
    original = report["system_sections"][0]["body"]
    call_count = {"n": 0}

    def counting_rewrite_fn(user_message):
        call_count["n"] += 1
        return "여전히 문제가 있는 재작성 결과입니다. 이 문장도 아직 개선이 더 필요한 상태이고 다른 부분도 손봐야 합니다", _FakeUsage()

    def failing_groundedness(prompt):
        return "문제가 있습니다 — 계산값과 다릅니다"  # 항상 실패 -> rollback

    issue = {
        "section_kind": "system_sections", "index": 0, "field": "body",
        "category": 5, "quoted_sentence": original[:20], "reason": "r",
    }
    result = br.rewrite_and_validate_issue(
        report, computed, issue, rewrite_fn=counting_rewrite_fn, groundedness_call_fn=failing_groundedness,
    )
    return [
        ("rewrite_fn이 정확히 1회만 호출됨(재시도 없음)", call_count["n"] == 1),
        ("groundedness 실패 -> accepted False", result["accepted"] is False),
        ("stage가 groundedness", result.get("stage") == "groundedness"),
        ("report 원본 그대로 유지(rollback)", report["system_sections"][0]["body"] == original),
    ]


def test6_category9_detection():
    computed_path = ENGINE_DIR / "test/out-behavior.json"
    computed = json.loads(computed_path.read_text(encoding="utf-8"))
    internal_keys = br.collect_internal_field_key_names(computed)

    known_leaked = [
        "oheng_count", "correspondence.dominant_oheng_lifestyle", "yearly_fortune",
    ]
    results = []
    for leak in known_leaked:
        text = f"이 사람은 {leak}에 따르면 원칙적인 성향입니다."
        found = br.detect_internal_field_name_leaks(text, internal_keys)
        results.append((f"'{leak}' 탐지됨", leak.split(".")[0] in [f.split(".")[0] for f in found] or leak in found))

    # 오탐 방지: computed.json에 없는 일반 영단어(스네이크케이스 아님)는 안 잡혀야 함
    clean_text = "이 사람은 매우 신중한 성향입니다."
    found_clean = br.detect_internal_field_name_leaks(clean_text, internal_keys)
    results.append(("정상 한국어 문장에서는 아무것도 탐지 안 됨", found_clean == []))

    # report 전체 스캔
    report = _fake_report()
    findings = br.scan_report_for_internal_field_leaks(report, internal_keys)
    results.append(("report 스캔에서 cross_analysis의 oheng_count 발견",
                     any(f["path"] == ("cross_analysis", "body") for f in findings)))
    return results


def test7_no_issues_no_changes():
    report = _fake_report()
    computed = {"tier": "premium"}
    before = json.loads(json.dumps(report, ensure_ascii=False))  # deep copy for compare
    results = br.run_targeted_rewrite_pass(report, computed, issues=[])
    return [
        ("issue 0개 -> 결과 0개", results == []),
        ("report 완전히 그대로", report == before),
    ]


def test8_quoted_sentence_mismatch_discarded():
    report = _fake_report()
    issue = {
        "section_kind": "system_sections", "index": 0, "field": "body",
        "category": 5, "quoted_sentence": "이 문장은 원문에 절대 존재하지 않습니다 완전히 다른 내용",
        "reason": "r",
    }
    path, err = br.resolve_naturalness_issue_path(report, issue)
    return [
        ("불일치하는 quoted_sentence -> path None", path is None),
        ("에러 사유에 위치 특정 실패 언급", "위치 특정" in (err or "")),
    ]


def test9_successful_rewrite_only_changes_target_field():
    report = _fake_report()
    computed = {"tier": "premium"}
    before = json.loads(json.dumps(report, ensure_ascii=False))
    original = report["system_sections"][0]["body"]

    def good_rewrite_fn(user_message):
        return "이 사람은 안정과 도전을 함께 추구합니다. 정관(명예ㆍ책임)과 편재(유동적 재물)와 칠살(부담이자 추진력)이 이런 성향을 만듭니다.", _FakeUsage()

    def good_groundedness(prompt):
        return "OK"

    issue = {
        "section_kind": "system_sections", "index": 0, "field": "body",
        "category": 5, "quoted_sentence": original[:20], "reason": "r",
    }
    result = br.rewrite_and_validate_issue(
        report, computed, issue, rewrite_fn=good_rewrite_fn, groundedness_call_fn=good_groundedness,
    )

    other_fields_unchanged = (
        report["system_sections"][1] == before["system_sections"][1]
        and report["intro"] == before["intro"]
        and report["closing"] == before["closing"]
        and report["cross_analysis"] == before["cross_analysis"]
        and report["new_reference_systems"] == before["new_reference_systems"]
    )
    return [
        ("정상 재작성 -> accepted True", result["accepted"] is True),
        ("대상 필드만 실제로 변경됨", report["system_sections"][0]["body"] != original),
        ("다른 필드는 전부 그대로", other_fields_unchanged),
    ]


def test10_groundedness_failure_rollback():
    report = _fake_report()
    computed = {"tier": "premium"}
    original = report["system_sections"][0]["body"]

    def plausible_but_wrong_rewrite(user_message):
        return "정관은 재물운을 뜻하고 칠살은 명예를 뜻합니다(계산값과 실제로 다른 내용).", _FakeUsage()

    def failing_groundedness(prompt):
        return "문제가 있습니다 — 정관/칠살의 의미가 계산값과 다릅니다"

    issue = {
        "section_kind": "system_sections", "index": 0, "field": "body",
        "category": 6, "quoted_sentence": original[:20], "reason": "r",
    }
    result = br.rewrite_and_validate_issue(
        report, computed, issue, rewrite_fn=plausible_but_wrong_rewrite, groundedness_call_fn=failing_groundedness,
    )
    return [
        ("groundedness 실패 -> accepted False", result["accepted"] is False),
        ("stage가 groundedness", result.get("stage") == "groundedness"),
        ("report 원본으로 롤백됨", report["system_sections"][0]["body"] == original),
    ]


def test11_verify_naturalness_issues_found():
    """정상 완료 + issues 1건 -> status ISSUES_FOUND."""
    report = _fake_report()

    def mock_call_fn(prompt):
        return _FakeResponse([
            _FakeToolUseBlock("submit_naturalness_issues", {
                "issues": [
                    {"section_kind": "system_sections", "index": 0, "field": "body",
                     "category": 5, "quoted_sentence": "정관은 명예와 책임", "reason": "용어 나열"},
                ]
            }),
        ], stop_reason="tool_use")

    result = br.verify_naturalness(report, tier="premium", call_fn=mock_call_fn)
    return [
        ("status가 ISSUES_FOUND", result["status"] == "ISSUES_FOUND"),
        ("issues 1건 반환됨", len(result["issues"]) == 1),
        ("category 필드 보존됨", result["issues"][0].get("category") == 5),
    ]


def test12_verify_naturalness_pass_when_complete_and_empty():
    """정상 완료 + issues 0건 -> status PASS(진짜 완료된 경우에만)."""
    report = _fake_report()

    def mock_call_fn_empty(prompt):
        return _FakeResponse([
            _FakeToolUseBlock("submit_naturalness_issues", {"issues": []}),
        ], stop_reason="tool_use")

    result = br.verify_naturalness(report, tier="premium", call_fn=mock_call_fn_empty)
    return [
        ("status가 PASS", result["status"] == "PASS"),
        ("issues 빈 리스트", result["issues"] == []),
    ]


def test13_verify_naturalness_max_tokens_never_pass():
    """핵심 게이트 — stop_reason==max_tokens면 issues가 비어있어도 절대 PASS가 아님."""
    report = _fake_report()

    def mock_call_fn_truncated(prompt):
        # 실제 파일럿에서 재현된 정확한 상황: tool_use는 있지만 input이 텅 빈 {}
        return _FakeResponse([
            _FakeToolUseBlock("submit_naturalness_issues", {}),
        ], stop_reason="max_tokens", usage=_FakeUsage(output_tokens=4096))

    result = br.verify_naturalness(report, tier="light", call_fn=mock_call_fn_truncated)
    return [
        ("status가 PASS가 아님", result["status"] != "PASS"),
        ("status가 INCOMPLETE", result["status"] == "INCOMPLETE"),
        ("issues는 신뢰할 수 없으므로 빈 리스트로 취급", result["issues"] == []),
    ]


def test14_verify_naturalness_incomplete_tool_input():
    """tool_use는 있으나 input에 issues 키가 아예 없음(스키마 불완전) -> INCOMPLETE."""
    report = _fake_report()

    def mock_call_fn(prompt):
        return _FakeResponse([
            _FakeToolUseBlock("submit_naturalness_issues", {}),  # issues 키 없음
        ], stop_reason="tool_use")  # stop_reason은 정상인데 input만 깨진 극단 케이스

    result = br.verify_naturalness(report, tier="light", call_fn=mock_call_fn)
    return [("status가 INCOMPLETE", result["status"] == "INCOMPLETE")]


def test15_verify_naturalness_no_tool_use_block():
    """도구를 아예 호출하지 않은 응답 -> ERROR."""
    report = _fake_report()

    def mock_call_fn(prompt):
        return _FakeResponse([], stop_reason="end_turn")

    result = br.verify_naturalness(report, tier="light", call_fn=mock_call_fn)
    return [("status가 ERROR", result["status"] == "ERROR")]


def test16_verify_naturalness_issues_not_a_list():
    """issues가 배열이 아닌 경우(스키마 위반) -> ERROR."""
    report = _fake_report()

    def mock_call_fn(prompt):
        return _FakeResponse([
            _FakeToolUseBlock("submit_naturalness_issues", {"issues": "이상한 문자열"}),
        ], stop_reason="tool_use")

    result = br.verify_naturalness(report, tier="light", call_fn=mock_call_fn)
    return [("status가 ERROR", result["status"] == "ERROR")]


# ---- quoted_sentence Markdown 정규화 검증(2026-09-01, 실제 파일럿에서 발견된 사고 대응) ----
# 실제 리포트 본문의 body 하나에 인라인 강조(**)가 걸쳐 있는 상황을 그대로 재현한다.

def _report_with_markdown_body():
    return {
        "intro": "i", "toc_preview": None,
        "system_sections": [
            {"system": "saju", "heading": "h",
             "body": "이 사람은 한번 자리를 잡으면 꾸준히 쌓아 올리는 힘은 강하지만, 그 구조**로 볼 수 있습니다. 당신은 **신중한 사람**입니다.",
             "key_insight": "", "takeaways": []},
        ],
        "new_reference_systems": None, "cross_analysis": None,
        "opportunities": None, "risks": None, "action_plan": None,
        "question_answers": None, "long_term_strategy": None, "closing": "c",
    }


def _issue_for(quoted):
    return {"section_kind": "system_sections", "index": 0, "field": "body",
            "category": 1, "quoted_sentence": quoted, "reason": "r"}


def testA_markdown_free_identical_sentence():
    """Test A — 마크다운 없는 완전 동일 문장 -> PASS."""
    report = _report_with_markdown_body()
    path, err = br.resolve_naturalness_issue_path(report, _issue_for("당신은 **신중한 사람**입니다."))
    # 원문 자체에 **가 있으므로, 인용도 그대로 **를 포함해 인용한 경우 -> 당연히 일치
    return [("원문 그대로(** 포함) 인용 -> path 성공", path is not None), ("에러 없음", err is None)]


def testB_markdown_stripped_by_llm():
    """Test B — LLM이 **를 빼고 인용 -> 이번 수정으로 PASS가 되어야 함(핵심 케이스)."""
    report = _report_with_markdown_body()
    path, err = br.resolve_naturalness_issue_path(report, _issue_for("당신은 신중한 사람입니다."))
    return [("** 없이 인용해도 path 성공", path is not None), ("에러 없음", err is None)]


def testB2_markdown_mid_sentence_stripped():
    """Test B의 실제 파일럿 재현 — 문장 중간에 걸친 **가 빠진 경우."""
    report = _report_with_markdown_body()
    path, err = br.resolve_naturalness_issue_path(
        report, _issue_for("이 사람은 한번 자리를 잡으면 꾸준히 쌓아 올리는 힘은 강하지만, 그 구조로 볼 수 있습니다."),
    )
    return [("문장 중간 ** 누락돼도 path 성공(실제 파일럿 재현)", path is not None), ("에러 없음", err is None)]


def testC_content_changed_still_fails():
    """Test C — 문장 내용 자체가 달라짐(적극적인 사람) -> 여전히 실패해야 함."""
    report = _report_with_markdown_body()
    path, err = br.resolve_naturalness_issue_path(report, _issue_for("당신은 적극적인 사람입니다."))
    return [("내용이 다르면 여전히 path 실패", path is None), ("에러 사유 있음", bool(err))]


def testD_word_inserted_still_fails():
    """Test D — 원문에 없는 단어가 끼어듦(매우) -> 여전히 실패해야 함."""
    report = _report_with_markdown_body()
    path, err = br.resolve_naturalness_issue_path(report, _issue_for("당신은 매우 신중한 사람입니다."))
    return [("단어가 추가되면 여전히 path 실패", path is None), ("에러 사유 있음", bool(err))]


def testE_nonexistent_sentence_still_fails():
    """Test E — 원문에 아예 없는 문장(냉정한 사람) -> 여전히 실패해야 함."""
    report = _report_with_markdown_body()
    path, err = br.resolve_naturalness_issue_path(report, _issue_for("당신은 냉정한 사람입니다."))
    return [("존재하지 않는 문장은 여전히 path 실패", path is None), ("에러 사유 있음", bool(err))]


# ---- field_groundedness call_purpose 등록 + new_value 진단 보강 검증 ----
# (2026-09-01, 실제 Pilot에서 발견된 사고 대응: field_groundedness가 CALL_PURPOSES에
# 없어 정상 API 호출 뒤 로깅 단계에서 죽고, 그 예외가 "검증 실패"로 오인식되어
# 정상 재작성 2건이 콘텐츠와 무관하게 rollback됐었다.)

def testG1_field_groundedness_call_purpose_registered():
    """Test 1 — field_groundedness가 정상 call_purpose로 usage logging되는가."""
    try:
        record = api_usage.build_usage_record(
            call_purpose="field_groundedness", model="claude-haiku-4-5-20251001",
            usage=_FakeUsage(), tier="light", thinking_disabled=None,
        )
        ok = record.get("call_purpose") == "field_groundedness"
        err = None
    except ValueError as e:
        ok = False
        err = str(e)
    return [("field_groundedness로 build_usage_record 예외 없이 성공", ok and err is None)]


def testG2_existing_call_purposes_unaffected():
    """Test 2 — 기존 CALL_PURPOSES(generation/verify_groundedness/verify_naturalness/
    targeted_rewrite)가 여전히 정상 동작하는가(field_groundedness 추가로 안 깨졌는지)."""
    results = []
    for purpose in ("generation", "verify_groundedness", "verify_naturalness", "targeted_rewrite"):
        try:
            api_usage.build_usage_record(
                call_purpose=purpose, model="claude-sonnet-5", usage=_FakeUsage(),
                tier="light", thinking_disabled=None,
            )
            ok = True
        except ValueError:
            ok = False
        results.append((f"기존 call_purpose='{purpose}' 정상 동작", ok))
    # 여전히 알 수 없는 값은 거부돼야 함(허용 목록이 무분별하게 넓어지지 않았는지 확인)
    try:
        api_usage.build_usage_record(
            call_purpose="완전히_없는_값", model="x", usage=_FakeUsage(), tier=None, thinking_disabled=None,
        )
        rejected = False
    except ValueError:
        rejected = True
    results.append(("등록 안 된 call_purpose는 여전히 거부됨", rejected))
    return results


def testG3_groundedness_pass_accepts_rewrite():
    """Test 3 — groundedness mock PASS -> rewrite ACCEPT."""
    report = _fake_report()
    computed = {"tier": "premium"}
    original = report["system_sections"][0]["body"]

    def good_rewrite_fn(user_message):
        return "이 사람은 안정과 도전을 함께 추구합니다. 정관(명예ㆍ책임)과 편재(유동적 재물)와 칠살(부담이자 추진력)이 이런 성향을 만듭니다.", _FakeUsage()

    def good_groundedness(prompt):
        return "OK"

    issue = {"section_kind": "system_sections", "index": 0, "field": "body",
              "category": 5, "quoted_sentence": original[:20], "reason": "r"}
    result = br.rewrite_and_validate_issue(report, computed, issue, rewrite_fn=good_rewrite_fn, groundedness_call_fn=good_groundedness)
    return [("groundedness PASS -> accepted True", result["accepted"] is True)]


def testG4_groundedness_fail_rolls_back():
    """Test 4 — groundedness mock FAIL -> 원본으로 ROLLBACK."""
    report = _fake_report()
    computed = {"tier": "premium"}
    original = report["system_sections"][0]["body"]

    def rewrite_fn(user_message):
        return "재작성된 내용이지만 계산값과 어긋나는 결과입니다 매우 다른 새로운 문장", _FakeUsage()

    def failing_groundedness(prompt):
        return "문제가 있습니다 — 계산값과 다릅니다"

    issue = {"section_kind": "system_sections", "index": 0, "field": "body",
              "category": 5, "quoted_sentence": original[:20], "reason": "r"}
    result = br.rewrite_and_validate_issue(report, computed, issue, rewrite_fn=rewrite_fn, groundedness_call_fn=failing_groundedness)
    return [
        ("groundedness FAIL -> accepted False", result["accepted"] is False),
        ("report는 원본으로 rollback됨", report["system_sections"][0]["body"] == original),
    ]


def testG5_new_value_preserved_on_failure():
    """Test 5 — groundedness FAIL이어도 결과 객체에 실제 new_value가 남아 있는가
    (2026-09-01 보강 — 실패해도 진단용으로 new_value를 확인할 수 있어야 함)."""
    report = _fake_report()
    computed = {"tier": "premium"}
    original = report["system_sections"][0]["body"]
    generated_text = "재작성된 내용이지만 계산값과 어긋나는 결과입니다 매우 다른 새로운 문장"

    def rewrite_fn(user_message):
        return generated_text, _FakeUsage()

    def failing_groundedness(prompt):
        return "문제가 있습니다"

    issue = {"section_kind": "system_sections", "index": 0, "field": "body",
              "category": 5, "quoted_sentence": original[:20], "reason": "r"}
    result = br.rewrite_and_validate_issue(report, computed, issue, rewrite_fn=rewrite_fn, groundedness_call_fn=failing_groundedness)
    return [
        ("실패해도 new_value 키가 존재", "new_value" in result),
        ("new_value가 실제 생성된 텍스트와 일치", result.get("new_value") == generated_text),
        ("report 본문에는 반영되지 않음(rollback)", report["system_sections"][0]["body"] == original),
    ]


def testG6_rollback_target_field_matches_original():
    """Test 6 — rollback 후 report의 대상 field가 원본과 정확히 동일한가."""
    report = _fake_report()
    computed = {"tier": "premium"}
    original = report["system_sections"][0]["body"]

    def rewrite_fn(user_message):
        return "완전히 다른 새 내용입니다 이것도 마찬가지로 새로운 문장입니다", _FakeUsage()

    def failing_groundedness(prompt):
        return "실패"

    issue = {"section_kind": "system_sections", "index": 0, "field": "body",
              "category": 5, "quoted_sentence": original[:20], "reason": "r"}
    br.rewrite_and_validate_issue(report, computed, issue, rewrite_fn=rewrite_fn, groundedness_call_fn=failing_groundedness)
    return [("대상 field가 원본과 byte 단위로 동일", report["system_sections"][0]["body"] == original)]


def testG7_rollback_other_fields_untouched():
    """Test 7 — 대상 field 이외의 모든 field가 rollback 전후로 동일한가."""
    report = _fake_report()
    computed = {"tier": "premium"}
    before = json.loads(json.dumps(report, ensure_ascii=False))
    original = report["system_sections"][0]["body"]

    def rewrite_fn(user_message):
        return "완전히 다른 새 내용입니다 이것도 마찬가지로 새로운 문장입니다", _FakeUsage()

    def failing_groundedness(prompt):
        return "실패"

    issue = {"section_kind": "system_sections", "index": 0, "field": "body",
              "category": 5, "quoted_sentence": original[:20], "reason": "r"}
    br.rewrite_and_validate_issue(report, computed, issue, rewrite_fn=rewrite_fn, groundedness_call_fn=failing_groundedness)
    return [("전체 report가 실행 전과 완전히 동일(대상 필드도 rollback됐으므로)", report == before)]


def testG8_max_one_rewrite_per_field_still_holds():
    """Test 8 — 필드당 rewrite가 여전히 최대 1회인가(new_value 보강 후에도 재시도
    로직이 추가되지 않았는지 확인)."""
    report = _fake_report()
    computed = {"tier": "premium"}
    original = report["system_sections"][0]["body"]
    call_count = {"n": 0}

    def counting_rewrite_fn(user_message):
        call_count["n"] += 1
        return "여전히 문제가 있는 재작성 결과입니다. 이 문장도 아직 개선이 더 필요한 상태이고 다른 부분도 손봐야 합니다", _FakeUsage()

    def failing_groundedness(prompt):
        return "실패"

    issue = {"section_kind": "system_sections", "index": 0, "field": "body",
              "category": 5, "quoted_sentence": original[:20], "reason": "r"}
    br.rewrite_and_validate_issue(report, computed, issue, rewrite_fn=counting_rewrite_fn, groundedness_call_fn=failing_groundedness)
    return [("rewrite_fn이 정확히 1회만 호출됨", call_count["n"] == 1)]


# ---- Format Integrity 검사(2026-09-01, 실제 파일럿 2회차에서 재현된 사고 대응) ----
# groundedness/scope를 전부 통과해도 tool-call 프로토콜 잔재(</new_value></invoke> 등)가
# 그대로 섞여 나온 실제 사고를 계기로 D단계(check_format_integrity)를 폐쇄 루프에 추가.

def _issue_body0(quoted="정관은 명예와 책임"):
    return {"section_kind": "system_sections", "index": 0, "field": "body",
            "category": 5, "quoted_sentence": quoted, "reason": "r"}


def testH1_clean_rewrite_passes_and_accepted():
    """Test H1 — 정상 rewrite -> Format Integrity PASS -> ACCEPT."""
    report = _fake_report()
    computed = {"tier": "premium"}
    original = report["system_sections"][0]["body"]

    def clean_rewrite_fn(user_message):
        return "이 사람은 안정과 도전을 함께 추구합니다. 정관(명예ㆍ책임)과 편재(유동적 재물)와 칠살(부담이자 추진력)이 이런 성향을 만듭니다.", _FakeUsage()

    def ok_groundedness(prompt):
        return "OK"

    result = br.rewrite_and_validate_issue(
        report, computed, _issue_body0(original[:20]), rewrite_fn=clean_rewrite_fn, groundedness_call_fn=ok_groundedness,
    )
    return [("정상 rewrite -> accepted True", result["accepted"] is True)]


def _residue_case(residue_text):
    report = _fake_report()
    computed = {"tier": "premium"}
    original = report["system_sections"][0]["body"]

    def residue_rewrite_fn(user_message):
        return residue_text, _FakeUsage()

    def ok_groundedness(prompt):
        return "OK"

    result = br.rewrite_and_validate_issue(
        report, computed, _issue_body0(original[:20]), rewrite_fn=residue_rewrite_fn, groundedness_call_fn=ok_groundedness,
    )
    return report, original, result


def testH2_invoke_close_tag_rejected():
    """Test H2 — </invoke> 포함 -> FAIL -> ROLLBACK."""
    report, original, result = _residue_case(
        "이 사람은 안정과 도전을 함께 추구하는 성향입니다.</new_value>\n</invoke>\n"
    )
    return [
        ("</invoke> 포함 -> accepted False", result["accepted"] is False),
        ("stage가 format_integrity", result.get("stage") == "format_integrity"),
        ("report는 원본으로 rollback됨", report["system_sections"][0]["body"] == original),
    ]


def testH3_invoke_open_tag_rejected():
    """Test H3 — <invoke> 포함 -> FAIL -> ROLLBACK."""
    report, original, result = _residue_case(
        '<invoke name="submit_field_rewrite">이 사람은 안정과 도전을 함께 추구합니다.'
    )
    return [
        ("<invoke> 포함 -> accepted False", result["accepted"] is False),
        ("stage가 format_integrity", result.get("stage") == "format_integrity"),
        ("report는 원본으로 rollback됨", report["system_sections"][0]["body"] == original),
    ]


def testH4_new_value_tags_rejected():
    """Test H4 — <new_value>/</new_value> 포함 -> FAIL -> ROLLBACK."""
    results = []
    base = "이 사람은 안정과 도전을 함께 추구하는 성향입니다. 정관과 편재와 칠살이 이런 특징을 만듭니다."
    for text in (f"<new_value>{base}", f"{base}</new_value>"):
        report, original, result = _residue_case(text)
        results.append((f"{text[:20]}... -> accepted False", result["accepted"] is False))
        results.append((f"{text[:20]}... -> stage=format_integrity", result.get("stage") == "format_integrity"))
    return results


def testH5_multiple_residues_rejected():
    """Test H5 — 여러 protocol residue 동시 포함 -> FAIL -> ROLLBACK."""
    report, original, result = _residue_case(
        '<invoke name="submit_field_rewrite"><parameter name="new_value">이 사람은 안정과 도전을 함께 추구합니다.</parameter></invoke>'
    )
    return [
        ("복합 잔재 포함 -> accepted False", result["accepted"] is False),
        ("stage가 format_integrity", result.get("stage") == "format_integrity"),
        ("report는 원본으로 rollback됨", report["system_sections"][0]["body"] == original),
    ]


def testH6_normal_markdown_passes():
    """Test H6 — 정상 Markdown **강조** -> PASS(오탐 없음)."""
    report, original, result = _residue_case(
        "이 사람은 **안정과 도전**을 함께 추구하는 성향입니다. 정관과 편재와 칠살이 이런 특징을 만듭니다."
    )
    return [("정상 마크다운 강조는 format_integrity 통과", result.get("stage") != "format_integrity")]


def testH7_korean_particle_attached_passes():
    """Test H7 — 한국어 조사 결합 문장(예: oheng_count에) -> PASS(오탐 없음)."""
    ok = br.check_format_integrity("이 사람의 특징은 oheng_count에 잘 드러납니다.")["passed"]
    return [("한글 조사 결합 문장은 format_integrity 통과", ok)]


def testH8_format_integrity_failure_other_fields_untouched():
    """Test H8 — Format Integrity FAIL이어도 다른 field는 변경되지 않음."""
    report = _fake_report()
    before = json.loads(json.dumps(report, ensure_ascii=False))
    original = report["system_sections"][0]["body"]
    computed = {"tier": "premium"}

    def residue_rewrite_fn(user_message):
        return "이 사람은 안정과 도전을 함께 추구합니다.</invoke>", _FakeUsage()

    def ok_groundedness(prompt):
        return "OK"

    br.rewrite_and_validate_issue(
        report, computed, _issue_body0(original[:20]), rewrite_fn=residue_rewrite_fn, groundedness_call_fn=ok_groundedness,
    )
    return [("전체 report가 실행 전과 완전히 동일", report == before)]


def testH9_new_value_preserved_on_format_integrity_failure():
    """Test H9 — Format Integrity FAIL이어도 new_value가 진단 결과에 보존됨."""
    residue_text = "이 사람은 안정과 도전을 함께 추구하는 성향입니다. 정관과 편재와 칠살이 이런 특징을 만듭니다.</invoke>"
    report, original, result = _residue_case(residue_text)
    return [
        ("new_value가 실제 생성된 텍스트와 일치", result.get("new_value") == residue_text),
        ("matched_pattern이 결과에 기록됨", result.get("matched_pattern") == "</invoke>"),
    ]


def testH10_still_max_one_rewrite_per_field():
    """Test H10 — Format Integrity 추가 후에도 필드당 rewrite는 여전히 최대 1회."""
    report = _fake_report()
    computed = {"tier": "premium"}
    original = report["system_sections"][0]["body"]
    call_count = {"n": 0}

    def residue_rewrite_fn(user_message):
        call_count["n"] += 1
        return "이 사람은 안정과 도전을 함께 추구합니다.</invoke>", _FakeUsage()

    def ok_groundedness(prompt):
        return "OK"

    br.rewrite_and_validate_issue(
        report, computed, _issue_body0(original[:20]), rewrite_fn=residue_rewrite_fn, groundedness_call_fn=ok_groundedness,
    )
    return [("rewrite_fn이 정확히 1회만 호출됨(재시도 없음)", call_count["n"] == 1)]


# ============================================================================
# Test I~T — paragraph-level 폐쇄 루프 근본 원인 제거 검증(2026-09-01).
#
# 기존 _fake_report()의 system_sections[0].body는 "\n\n"이 전혀 없는 단일 문단이라
# (기존 40개 테스트 그룹이 전부 이 fixture에 의존) 문단 격리 자체를 검증할 수 없다 —
# single tier 실제 pilot에서 재현된 사고(대상 문단은 정상인데 같은 field의 다른 문단에
# 있던 기존 오류 때문에 정상 rewrite까지 rollback됨)를 mock으로 재현하려면 반드시
# 멀티문단 fixture가 필요해서 별도로 추가한다.
# ============================================================================


def _fake_multi_paragraph_report():
    report = _fake_report()
    report["system_sections"][0]["body"] = (
        "첫 번째 문단입니다. 정관은 명예와 책임을 뜻하는 기운입니다.\n\n"
        "두 번째 문단입니다. 편재는 유동적인 재물을 뜻하며, 이 사람은 여러 경로로 "
        "돈이 들고 나는 성향이 있습니다.\n\n"
        "세 번째 문단입니다. 칠살은 부담이자 추진력을 뜻하며, 이 사람은 도전정신이 "
        "강한 편입니다."
    )
    return report


def _fake_duplicate_sentence_report():
    report = _fake_report()
    report["system_sections"][0]["body"] = (
        "첫 번째 문단입니다. 정관은 명예와 책임을 뜻하는 기운입니다.\n\n"
        "두 번째 문단에도 똑같이 정관은 명예와 책임을 뜻하는 기운입니다 라고 다시 "
        "적었습니다.\n\n"
        "세 번째 문단입니다. 칠살은 부담이자 추진력을 뜻합니다."
    )
    return report


def _ms_issue(quoted_sentence, category=5):
    return {
        "section_kind": "system_sections", "index": 0, "field": "body",
        "category": category, "quoted_sentence": quoted_sentence, "reason": "r",
    }


def testI_other_paragraph_groundedness_issue_does_not_block_target():
    """Test I — 대상 문단은 정상, 같은 field의 다른 문단에 groundedness 문제가 있다고
    가정해도(prompt에 다른 문단 단서가 섞이면 일부러 FAIL을 반환하는 mock) ACCEPT되어야
    한다 — 다른 문단이 애초에 groundedness 프롬프트에 실리지 않음을 이 mock의 실패
    조건 자체로 증명한다."""
    report = _fake_multi_paragraph_report()
    computed = {"tier": "premium"}
    target_quote = "칠살은 부담이자 추진력을 뜻하며"
    captured_prompts = []

    def rewrite_fn(user_message):
        return ("세 번째 문단을 이렇게 다시 씁니다. 칠살은 부담이자 동시에 추진력이 "
                "되는 기운이라, 도전정신이 남다른 편입니다."), _FakeUsage()

    def groundedness_call_fn(prompt):
        captured_prompts.append(prompt)
        if "편재" in prompt or "두 번째 문단" in prompt:
            return "다른 문단 내용이 섞여 있음 — 격리 실패"
        return "OK"

    result = br.rewrite_and_validate_issue(
        report, computed, _ms_issue(target_quote, category=1),
        rewrite_fn=rewrite_fn, groundedness_call_fn=groundedness_call_fn,
    )
    return [
        ("target paragraph index가 2(세 번째 문단)로 정확히 특정됨", result.get("paragraph_index") == 2),
        ("matched_paragraph_count가 1", result.get("matched_paragraph_count") == 1),
        ("groundedness 프롬프트에 다른 문단(편재) 내용이 섞이지 않음",
         not any("편재" in p for p in captured_prompts)),
        ("다른 문단의 잠재적 문제와 무관하게 ACCEPT됨", result.get("accepted") is True),
    ]


def testJ_target_paragraph_new_error_rolls_back():
    """Test J — target paragraph 자체에 새 groundedness 오류가 생기면 여전히 ROLLBACK."""
    report = _fake_multi_paragraph_report()
    computed = {"tier": "premium"}
    target_quote = "칠살은 부담이자 추진력을 뜻하며"
    original_body = report["system_sections"][0]["body"]

    def rewrite_fn(user_message):
        return "세 번째 문단을 이렇게 잘못 바꿉니다. 칠살은 사실 재물운을 뜻합니다(계산값과 다른 잘못된 내용).", _FakeUsage()

    def groundedness_call_fn(prompt):
        return "문제가 있습니다 — 칠살의 의미가 계산값과 다릅니다"

    result = br.rewrite_and_validate_issue(
        report, computed, _ms_issue(target_quote, category=1),
        rewrite_fn=rewrite_fn, groundedness_call_fn=groundedness_call_fn,
    )
    return [
        ("target paragraph 자체 오류 -> accepted False", result.get("accepted") is False),
        ("stage가 groundedness", result.get("stage") == "groundedness"),
        ("report 전체가 원본과 완전히 동일(rollback)", report["system_sections"][0]["body"] == original_body),
    ]


def testK_non_target_paragraphs_byte_identical_after_accept():
    """Test K — ACCEPT 후 target 외 문단은 byte 단위로 완전히 동일해야 한다."""
    report = _fake_multi_paragraph_report()
    computed = {"tier": "premium"}
    original_paragraphs = report["system_sections"][0]["body"].split("\n\n")
    target_quote = "칠살은 부담이자 추진력을 뜻하며"

    def rewrite_fn(user_message):
        return ("세 번째 문단을 이렇게 확장합니다. 칠살은 부담이자 동시에 추진력이 "
                "되는 기운이라, 힘든 시기일수록 오히려 도전정신이 살아나는 편입니다."), _FakeUsage()

    result = br.rewrite_and_validate_issue(
        report, computed, _ms_issue(target_quote, category=1),
        rewrite_fn=rewrite_fn, groundedness_call_fn=lambda p: "OK",
    )
    new_paragraphs = report["system_sections"][0]["body"].split("\n\n")
    return [
        ("ACCEPT됨", result.get("accepted") is True),
        ("문단 개수 유지", len(new_paragraphs) == len(original_paragraphs)),
        ("0번째 문단 byte 단위로 완전히 동일", new_paragraphs[0] == original_paragraphs[0]),
        ("1번째 문단 byte 단위로 완전히 동일", new_paragraphs[1] == original_paragraphs[1]),
        ("2번째(target) 문단만 실제로 변경됨", new_paragraphs[2] != original_paragraphs[2]),
    ]


def testL_within_paragraph_sentence_reorder_accepted_and_isolated():
    """Test L — target 문단 내부의 정상적인 문장 재배열/확장(기존 성공 사례와 같은
    패턴)은 ACCEPT되고, 다른 문단으로는 절대 splice되지 않는다."""
    report = _fake_multi_paragraph_report()
    computed = {"tier": "premium"}
    original_paragraphs = report["system_sections"][0]["body"].split("\n\n")
    target_quote = "편재는 유동적인 재물을 뜻하며"

    def rewrite_fn(user_message):
        return ("이 사람은 여러 경로로 돈이 들고 나는 성향이 있습니다. 그 바탕에는 "
                "편재, 즉 유동적인 재물을 뜻하는 기운이 자리하고 있습니다."), _FakeUsage()

    result = br.rewrite_and_validate_issue(
        report, computed, _ms_issue(target_quote, category=6),
        rewrite_fn=rewrite_fn, groundedness_call_fn=lambda p: "OK",
    )
    new_paragraphs = report["system_sections"][0]["body"].split("\n\n")
    return [
        ("문단 내 재배열도 ACCEPT됨", result.get("accepted") is True),
        ("다른 문단(0,2번)은 손대지 않음",
         new_paragraphs[0] == original_paragraphs[0] and new_paragraphs[2] == original_paragraphs[2]),
        ("target(1번) 문단만 변경됨", new_paragraphs[1] != original_paragraphs[1]),
    ]


def testM_quoted_sentence_is_phrase_within_paragraph_targets_whole_paragraph():
    """Test M — quoted_sentence가 문단 안의 구(句) 하나만 가리켜도, rewrite 단위는
    sentence가 아니라 그 문단 전체여야 한다(sentence-level로 과도하게 축소 금지)."""
    report = _fake_multi_paragraph_report()
    field_text = report["system_sections"][0]["body"]
    idx, paragraphs, matched, err = br.locate_target_paragraph(field_text, "여러 경로로 돈이 들고 나는 성향")
    return [
        ("문단 index가 1(두 번째 문단)로 특정됨", idx == 1),
        ("매칭 1건", matched == 1),
        ("에러 없음", err is None),
    ]


def testN_markdown_difference_still_matches_paragraph():
    """Test N — quoted_sentence의 마크다운(**) 차이는 기존 _norm_ws_rewrite_match()로
    여전히 정상 매칭되어야 한다(회귀 확인, 로직 변경 없음)."""
    report = _fake_multi_paragraph_report()
    body = report["system_sections"][0]["body"].replace(
        "정관은 명예와 책임을", "**정관은 명예와 책임을**",
    )
    idx, paragraphs, matched, err = br.locate_target_paragraph(body, "정관은 명예와 책임을 뜻하는 기운입니다.")
    return [
        ("마크다운 차이에도 문단 매칭 성공", idx == 0),
        ("매칭 1건", matched == 1),
    ]


def testO_duplicate_sentence_in_two_paragraphs_is_ambiguous():
    """Test O — 동일 문장이 서로 다른 두 문단에 있으면 AMBIGUOUS로 실패해야 한다
    (임의로 첫 번째 문단을 선택하지 않음)."""
    report = _fake_duplicate_sentence_report()
    computed = {"tier": "premium"}
    # 끝에 마침표를 붙이지 않는다 — 두 번째 문단에서는 이 구 뒤에 "라고 다시 적었습니다"가
    # 이어져 마침표가 없으므로, 마침표를 포함하면 우연히 첫 번째 문단에만 매칭돼(부분
    # 문자열 검사) 테스트가 실제로 검증하려는 "2개 문단 매칭"을 재현하지 못한다.
    quote = "정관은 명예와 책임을 뜻하는 기운입니다"
    idx, paragraphs, matched, err = br.locate_target_paragraph(report["system_sections"][0]["body"], quote)
    result = br.rewrite_and_validate_issue(report, computed, _ms_issue(quote, category=1))
    return [
        ("locate_target_paragraph -> index None(추측 금지)", idx is None),
        ("매칭 2건으로 집계됨", matched == 2),
        ("에러 사유에 AMBIGUOUS 명시", "AMBIGUOUS" in (err or "")),
        ("rewrite_and_validate_issue도 accepted False", result.get("accepted") is False),
        ("stage가 paragraph_location", result.get("stage") == "paragraph_location"),
        ("matched_paragraph_count가 2로 결과에 기록됨", result.get("matched_paragraph_count") == 2),
    ]


def testP_rewrite_exceeds_scope_relative_to_paragraph_only():
    """Test P — scope(0.5~2.0)가 field 전체가 아니라 target 문단 하나만 기준으로
    판정되어야 한다."""
    report = _fake_multi_paragraph_report()
    computed = {"tier": "premium"}
    target_quote = "칠살은 부담이자 추진력을 뜻하며"
    original_paragraphs = report["system_sections"][0]["body"].split("\n\n")
    target_len = len(original_paragraphs[2])

    def rewrite_fn(user_message):
        return "칠살 " * target_len, _FakeUsage()  # target 문단 대비 명백히 2배 이상

    result = br.rewrite_and_validate_issue(
        report, computed, _ms_issue(target_quote, category=1),
        rewrite_fn=rewrite_fn, groundedness_call_fn=lambda p: "OK",
    )
    return [
        ("scope 초과 -> accepted False", result.get("accepted") is False),
        ("stage가 scope_check", result.get("stage") == "scope_check"),
        ("reason에 target 문단 기준 글자수가 언급됨", str(target_len) in (result.get("reason") or "")),
    ]


def testQ_new_paragraph_contains_blank_line_rejected():
    """Test Q — rewrite 결과 안에 새 빈 줄("\\n\\n")이 생기면 paragraph 경계 침범으로
    fail-closed 처리해야 한다(자동으로 재분할해 여러 문단에 적용하지 않음)."""
    report = _fake_multi_paragraph_report()
    computed = {"tier": "premium"}
    target_quote = "칠살은 부담이자 추진력을 뜻하며"
    original_body = report["system_sections"][0]["body"]

    def rewrite_fn(user_message):
        return "칠살은 부담이자 추진력을 뜻합니다.\n\n그리고 도전정신도 강합니다.", _FakeUsage()

    result = br.rewrite_and_validate_issue(
        report, computed, _ms_issue(target_quote, category=1),
        rewrite_fn=rewrite_fn, groundedness_call_fn=lambda p: "OK",
    )
    return [
        ("문단 경계 침범 -> accepted False", result.get("accepted") is False),
        ("stage가 paragraph_structure", result.get("stage") == "paragraph_structure"),
        ("report는 원본과 완전히 동일(rollback)", report["system_sections"][0]["body"] == original_body),
    ]


def testR_tool_protocol_residue_in_paragraph_rejected():
    """Test R — 문단 단위로 축소된 뒤에도 tool/XML protocol residue는 여전히 차단돼야
    한다(check_format_integrity 자체는 무수정, 검사 대상만 문단으로 축소됨을 확인)."""
    report = _fake_multi_paragraph_report()
    computed = {"tier": "premium"}
    target_quote = "칠살은 부담이자 추진력을 뜻하며"
    original_body = report["system_sections"][0]["body"]

    def rewrite_fn(user_message):
        return "칠살은 부담이자 추진력을 뜻하는 기운입니다.</invoke>", _FakeUsage()

    result = br.rewrite_and_validate_issue(
        report, computed, _ms_issue(target_quote, category=1),
        rewrite_fn=rewrite_fn, groundedness_call_fn=lambda p: "OK",
    )
    return [
        ("tool residue -> accepted False", result.get("accepted") is False),
        ("stage가 format_integrity", result.get("stage") == "format_integrity"),
        ("matched_pattern이 기록됨", result.get("matched_pattern") == "</invoke>"),
        ("report는 원본과 완전히 동일(rollback)", report["system_sections"][0]["body"] == original_body),
    ]


def testS_groundedness_prompt_contains_only_target_paragraph():
    """Test S — Test I의 핵심 안전성을 더 강한 형태로 재확인: groundedness에 실제로
    전달되는 프롬프트가 target 문단만으로 만든 프롬프트와 byte 단위로 완전히 동일해야
    한다(다른 문단 내용이 조금도 섞이지 않음을 직접 대조로 증명)."""
    report = _fake_multi_paragraph_report()
    computed = {"tier": "premium"}
    target_quote = "칠살은 부담이자 추진력을 뜻하며"
    new_paragraph_text = "칠살은 부담이자 동시에 추진력이 되는 기운이라, 도전정신이 남다른 편입니다."
    captured = {}

    def rewrite_fn(user_message):
        return new_paragraph_text, _FakeUsage()

    def groundedness_call_fn(prompt):
        captured["prompt"] = prompt
        return "OK"

    br.rewrite_and_validate_issue(
        report, computed, _ms_issue(target_quote, category=1),
        rewrite_fn=rewrite_fn, groundedness_call_fn=groundedness_call_fn,
    )
    expected_prompt = br._field_groundedness_prompt(computed, new_paragraph_text)
    return [
        ("groundedness에 전달된 프롬프트가 target 문단 기준 프롬프트와 완전히 동일",
         captured.get("prompt") == expected_prompt),
        ("프롬프트에 다른 문단(편재) 텍스트가 없음", "편재" not in captured.get("prompt", "")),
        ("프롬프트에 다른 문단(정관) 텍스트가 없음", "정관" not in captured.get("prompt", "")),
    ]


def testT_spliced_paragraph_matches_rewrite_output_exactly():
    """Test T — splice 후 report 안의 target 문단이 rewrite API 반환값과 byte 단위로
    완전히 동일한지, 그리고 rewrite_fn이 정확히 1회만 호출됐는지 확인."""
    report = _fake_multi_paragraph_report()
    computed = {"tier": "premium"}
    target_quote = "칠살은 부담이자 추진력을 뜻하며"
    new_paragraph_text = "칠살은 부담이자 동시에 추진력이 되는 기운이라, 도전정신이 남다른 편입니다."
    call_count = {"n": 0}

    def rewrite_fn(user_message):
        call_count["n"] += 1
        return new_paragraph_text, _FakeUsage()

    result = br.rewrite_and_validate_issue(
        report, computed, _ms_issue(target_quote, category=1),
        rewrite_fn=rewrite_fn, groundedness_call_fn=lambda p: "OK",
    )
    spliced_paragraph = report["system_sections"][0]["body"].split("\n\n")[2]
    return [
        ("rewrite_fn이 정확히 1회 호출됨", call_count["n"] == 1),
        ("splice 후 target 문단이 rewrite 결과와 byte 단위로 완전히 동일",
         spliced_paragraph == new_paragraph_text),
        ("result['new_value']도 동일한 값", result.get("new_value") == new_paragraph_text),
    ]


# ============================================================================
# TEST GP1~GP4 — groundedness prompt gan/zhi ROOT CAUSE B 수정 검증(2026-09-01).
#
# STEP 2 실제 pilot에서 확인된 사고: computed에 shi_shen_zhi=["편재","칠살(편관)"]가
# 실제로 있었는데도 groundedness가 scalar shi_shen_gan="정관"만 보고 "편재는 년주에
# 없다"고 오판해 정상 rewrite가 rollback됨. _field_groundedness_prompt()에 gan/zhi
# 관계 설명을 추가한 게 실제로 프롬프트에 들어가는지, 기존 계약(전체 computed 그대로
# 전달ㆍOK/한문장 출력)이 유지되는지, "부분 언급 허용"과 "유일값 단정 차단"이 동시에
# 명시되는지, 그리고 이 변경이 paragraph-level 격리를 깨지 않는지를 API 없이 확인한다.
# ============================================================================


def testGP1_prompt_explains_gan_zhi_meaning():
    """TEST 1 — prompt에 gan/zhi 의미가 실제로(키워드가 아니라 뜻으로) 포함되는지."""
    computed = {"tier": "light"}
    prompt = br._field_groundedness_prompt(computed, "검토 대상 문장입니다.")
    return [
        ("shi_shen_gan이 '천간의 십신 하나'라는 의미로 설명됨",
         "shi_shen_gan은 그 기둥 천간의 십신 하나" in prompt),
        ("shi_shen_zhi가 '지지/지장간의 십신 목록(여러 개 가능)'이라는 의미로 설명됨",
         "shi_shen_zhi는 그 기둥 지지ㆍ지장간에서 나오는 십신 목록으로 여러 개일 수 있습니다" in prompt),
        ("두 필드를 함께 확인하라는 지시가 있음",
         "shi_shen_gan만이 아니라 shi_shen_zhi도 함께 확인하세요" in prompt),
    ]


def testGP2_real_out_light_computed_appears_unfiltered():
    """TEST 2 — 실제 out-light.json의 shi_shen_gan/shi_shen_zhi 값이 가공ㆍ필터링
    없이 그대로 prompt에 들어가는지(기존 "computed 전체 그대로 전달" 계약 유지)."""
    computed_path = ENGINE_DIR / "test/out-light.json"
    computed = json.loads(computed_path.read_text(encoding="utf-8"))
    year = computed["saju"]["pillars"]["year"]
    prompt = br._field_groundedness_prompt(computed, "검토 대상 문장입니다.")
    return [
        ("out-light.json의 customer가 테스트고객4임(fixture 확인)", computed["customer"]["name"] == "테스트고객4"),
        ("년주 shi_shen_gan이 실제로 '정관'임(fixture 확인)", year["shi_shen_gan"] == "정관"),
        ("년주 shi_shen_zhi에 실제로 '편재'가 있음(fixture 확인)", "편재" in year["shi_shen_zhi"]),
        ("prompt 안에 shi_shen_gan 원본 값 '정관'이 그대로 존재", '"shi_shen_gan": "정관"' in prompt),
        ("prompt 안에 shi_shen_zhi 원본 값 '편재'가 그대로 존재",
         '"편재"' in prompt and '"shi_shen_zhi"' in prompt),
        ("computed 전체가 필터 없이 JSON으로 들어감(다른 기둥 month도 포함)",
         '"ganzhi_ko": "병술"' in prompt),
    ]


def testGP3_partial_mention_vs_unique_value_distinction_present():
    """TEST 3 — "list 중 하나만 언급"은 허용하되 "유일값 단정/list 전체 왜곡"은 여전히
    FAIL 대상이라는 두 방향이 프롬프트에 동시에 명시되는지(모델 판정을 mock으로
    재현하지 않음 — 프롬프트 문구 자체만 검증)."""
    computed = {"tier": "light"}
    prompt = br._field_groundedness_prompt(computed, "검토 대상 문장입니다.")
    return [
        ("list 중 하나만 언급하는 것 자체는 근거 없음이 아니라고 명시됨",
         "그 자체로 근거 없음이 아닙니다" in prompt),
        ("유일값 단정/목록 전체 동일시는 여전히 근거 없는 주장이라고 명시됨",
         "유일한 십신" in prompt and "동일시하면" in prompt),
        ("computed에 없는 값ㆍ다른 기둥 값 사용은 여전히 FAIL 대상이라고 명시됨(과도한 완화 아님)",
         "계산값에 없는 값, 다른 기둥의 값을 가져다 쓴 경우도 마찬가지로 근거 없는 주장" in prompt),
        ("기존 출력 계약(OK/한 문장) 문구가 그대로 유지됨",
         "\"OK\"라고만 답하세요" in prompt and "한 문장으로 답하세요" in prompt),
    ]


def testGP4_paragraph_isolation_unaffected_by_prompt_change():
    """TEST 4 — groundedness prompt 수정 이후에도 paragraph-level isolation이 깨지지
    않는지. STEP 2에서 실제로 캡처된 new_paragraph(실제 API 결과, 재호출 없음)를 재사용해
    [검토할 문장] 섹션이 여전히 그 문단 하나와 완전히 일치하는지 직접 대조한다."""
    computed_path = ENGINE_DIR / "test/out-light.json"
    computed = json.loads(computed_path.read_text(encoding="utf-8"))
    # STEP 2 실제 API 결과(재작성된 target paragraph) — 재호출 없이 그대로 재사용
    new_paragraph = (
        "사업이나 부업, 새로운 돈벌이 이야기가 자연스럽게 떠오를 수 있는 구간이라고 볼 "
        "수 있는데, **년주에 편재(여러 경로로 돈이 들고 나는 사업가형 재물운)가 자리하고 "
        "있어 이 시기와 맞물리기 때문입니다.** 다만 편재는 원래 '흘러 다니는 재물'이라 "
        "들어오는 만큼 나가기도 쉬운 성질이라는 걸 함께 기억해 두시면 좋겠습니다."
    )
    prompt = br._field_groundedness_prompt(computed, new_paragraph)
    marker = "[검토할 문장]\n"
    reviewed_text = prompt.split(marker, 1)[1].split("\n\n계산값과 어긋나거나", 1)[0]
    return [
        ("[검토할 문장] 섹션이 target 문단과 byte 단위로 완전히 일치", reviewed_text == new_paragraph),
        ("[검토할 문장]에 다른 문단(월주 관련) 산문이 섞이지 않음",
         "사회생활" not in reviewed_text and "대운" not in reviewed_text),
        ("gan/zhi 설명 블록이 [검토할 문장]보다 앞(계산값 앞)에 위치함(구조 유지)",
         prompt.index("[십신 필드 읽는 법") < prompt.index("[계산값]") < prompt.index(marker)),
    ]


# ============================================================================
# TEST RT1~RT17 — run_targeted_rewrite_pass()/is_naturalness_pass_complete()
# orchestration 강화 검증(2026-09-02, 품질 원칙 강화 지시 대응).
#
# 발견된 실제 결함: (1) category 불일치/상한 초과 시 issue가 반환값에서 조용히
# 사라짐(silent 누락), (2) 처리 중 예외가 발생하면 함수 전체가 죽어 이미 처리된
# 결과와 나머지 issue가 통째로 사라짐, (3) issue와 결과를 연결할 id/echo 필드가
# 없어 동일 path의 issue 2개를 구분할 수 없음, (4) "전체 완료" 판정 로직 자체가
# 코드 어디에도 없음. 전부 mock으로 재현ㆍ수정 검증한다(실제 API 없음).
# ============================================================================


def _extract_target_paragraph(user_message):
    start = user_message.index("[문제로 지적된 내용]\n") + len("[문제로 지적된 내용]\n")
    end = user_message.index("\n\n[같은 필드의 다른 문단")
    context = json.loads(user_message[start:end])
    return context["target_paragraph"]


def _good_rewrite_fn(user_message):
    target = _extract_target_paragraph(user_message)
    return target + " 다시 정리합니다.", _FakeUsage()


def _good_groundedness(prompt):
    return "OK"


def testRT1_zero_issues_complete_true():
    """Test 1 — issue 0개."""
    report = _fake_report()
    computed = {"tier": "premium"}
    detection = {"status": "PASS", "issues": [], "detail": "검증 완료, 이슈 없음"}
    results = br.run_targeted_rewrite_pass(report, computed, detection["issues"])
    complete = br.is_naturalness_pass_complete(detection, results)
    return [
        ("issue 0개 -> results도 0개", results == []),
        ("complete == True", complete is True),
    ]


def testRT2_single_issue_resolved_complete_true():
    """Test 2 — issue 1개 -> resolved."""
    report = _fake_multi_paragraph_report()
    computed = {"tier": "premium"}
    issue = _ms_issue("칠살은 부담이자 추진력을 뜻하며", category=1)
    detection = {"status": "ISSUES_FOUND", "issues": [issue]}
    results = br.run_targeted_rewrite_pass(
        report, computed, detection["issues"], rewrite_fn=_good_rewrite_fn, groundedness_call_fn=_good_groundedness,
    )
    complete = br.is_naturalness_pass_complete(detection, results)
    return [
        ("results 길이 1", len(results) == 1),
        ("accepted True", results[0]["accepted"] is True),
        ("원본 issue의 category가 echo됨", results[0]["category"] == 1),
        ("원본 issue의 quoted_sentence가 echo됨", results[0]["quoted_sentence"] == issue["quoted_sentence"]),
        ("complete == True", complete is True),
    ]


def testRT3_multiple_issues_all_resolved():
    """Test 3 — 여러 issue -> 전부 resolved."""
    report = _fake_multi_paragraph_report()
    computed = {"tier": "premium"}
    issue_a = _ms_issue("정관은 명예와 책임을 뜻하는 기운입니다.", category=1)
    issue_b = _ms_issue("칠살은 부담이자 추진력을 뜻하며", category=6)
    detection = {"status": "ISSUES_FOUND", "issues": [issue_a, issue_b]}
    results = br.run_targeted_rewrite_pass(
        report, computed, detection["issues"], rewrite_fn=_good_rewrite_fn, groundedness_call_fn=_good_groundedness,
    )
    complete = br.is_naturalness_pass_complete(detection, results)
    return [
        ("results 길이 2", len(results) == 2),
        ("둘 다 accepted", all(r["accepted"] is True for r in results)),
        ("서로 다른 paragraph_index", results[0]["paragraph_index"] != results[1]["paragraph_index"]),
        ("complete == True", complete is True),
    ]


def testRT4_partial_resolution_complete_false():
    """Test 4 — 여러 issue 중 일부만 resolved -> complete는 반드시 False."""
    report = _fake_multi_paragraph_report()
    computed = {"tier": "premium"}
    issue_a = _ms_issue("정관은 명예와 책임을 뜻하는 기운입니다.", category=1)
    issue_b = _ms_issue("칠살은 부담이자 추진력을 뜻하며", category=6)
    detection = {"status": "ISSUES_FOUND", "issues": [issue_a, issue_b]}

    call_n = {"n": 0}

    def mixed_groundedness(prompt):
        call_n["n"] += 1
        return "OK" if call_n["n"] == 1 else "문제가 있습니다 — 계산값과 다릅니다"

    results = br.run_targeted_rewrite_pass(
        report, computed, detection["issues"], rewrite_fn=_good_rewrite_fn, groundedness_call_fn=mixed_groundedness,
    )
    complete = br.is_naturalness_pass_complete(detection, results)
    return [
        ("results 길이 2", len(results) == 2),
        ("첫 번째 accepted", results[0]["accepted"] is True),
        ("두 번째 rollback(stage=groundedness)", results[1]["accepted"] is False and results[1]["stage"] == "groundedness"),
        ("일부만 해결됐어도 complete는 반드시 False", complete is False),
    ]


def testRT5_rewrite_type_failure_via_pass():
    """Test 5 — rewrite failure(타입 오류)가 orchestration을 통해서도 정확히 기록됨."""
    report = _fake_multi_paragraph_report()
    computed = {"tier": "premium"}
    issue = _ms_issue("칠살은 부담이자 추진력을 뜻하며", category=1)
    detection = {"status": "ISSUES_FOUND", "issues": [issue]}

    def bad_rewrite_fn(user_message):
        return None, _FakeUsage()

    results = br.run_targeted_rewrite_pass(report, computed, detection["issues"], rewrite_fn=bad_rewrite_fn)
    complete = br.is_naturalness_pass_complete(detection, results)
    return [
        ("stage가 type_check", results[0]["stage"] == "type_check"),
        ("complete False", complete is False),
    ]


def testRT6_groundedness_failure_via_pass():
    """Test 6 — groundedness failure가 orchestration을 통해서도 정확히 기록됨."""
    report = _fake_multi_paragraph_report()
    computed = {"tier": "premium"}
    issue = _ms_issue("칠살은 부담이자 추진력을 뜻하며", category=1)
    detection = {"status": "ISSUES_FOUND", "issues": [issue]}

    def failing_groundedness(prompt):
        return "문제가 있습니다 — 계산값과 다릅니다"

    results = br.run_targeted_rewrite_pass(
        report, computed, detection["issues"], rewrite_fn=_good_rewrite_fn, groundedness_call_fn=failing_groundedness,
    )
    complete = br.is_naturalness_pass_complete(detection, results)
    return [
        ("stage가 groundedness", results[0]["stage"] == "groundedness"),
        ("complete False", complete is False),
    ]


def testRT7_format_failure_via_pass():
    """Test 7 — format failure가 orchestration을 통해서도 정확히 기록됨."""
    report = _fake_multi_paragraph_report()
    computed = {"tier": "premium"}
    issue = _ms_issue("칠살은 부담이자 추진력을 뜻하며", category=1)
    detection = {"status": "ISSUES_FOUND", "issues": [issue]}

    def residue_rewrite_fn(user_message):
        target = _extract_target_paragraph(user_message)
        return target + " 추가 설명입니다.</invoke>", _FakeUsage()

    results = br.run_targeted_rewrite_pass(
        report, computed, detection["issues"], rewrite_fn=residue_rewrite_fn, groundedness_call_fn=_good_groundedness,
    )
    complete = br.is_naturalness_pass_complete(detection, results)
    return [
        ("stage가 format_integrity", results[0]["stage"] == "format_integrity"),
        ("complete False", complete is False),
    ]


def testRT8_rollback_never_mutates_report_via_pass():
    """Test 8 — ROLLBACK은 resolved가 아니며, orchestration을 거쳐도 report가 절대 변경되지 않음."""
    report = _fake_multi_paragraph_report()
    original_body = report["system_sections"][0]["body"]
    computed = {"tier": "premium"}
    issue = _ms_issue("칠살은 부담이자 추진력을 뜻하며", category=1)
    detection = {"status": "ISSUES_FOUND", "issues": [issue]}

    def failing_groundedness(prompt):
        return "문제가 있습니다"

    results = br.run_targeted_rewrite_pass(
        report, computed, detection["issues"], rewrite_fn=_good_rewrite_fn, groundedness_call_fn=failing_groundedness,
    )
    return [
        ("ROLLBACK -> accepted False", results[0]["accepted"] is False),
        ("report가 원본과 완전히 동일(byte 단위)", report["system_sections"][0]["body"] == original_body),
    ]


def testRT9_exception_does_not_kill_batch():
    """Test 9 — 처리 중 예외가 발생해도 배치 전체가 죽지 않고, 그 issue만 실패로 기록됨."""
    report = _fake_multi_paragraph_report()
    original_body = report["system_sections"][0]["body"]
    computed = {"tier": "premium"}
    issue_a = _ms_issue("정관은 명예와 책임을 뜻하는 기운입니다.", category=1)
    issue_b = _ms_issue("칠살은 부담이자 추진력을 뜻하며", category=6)
    detection = {"status": "ISSUES_FOUND", "issues": [issue_a, issue_b]}

    def exploding_rewrite_fn(user_message):
        raise RuntimeError("네트워크 오류 시뮬레이션")

    results = br.run_targeted_rewrite_pass(
        report, computed, detection["issues"], rewrite_fn=exploding_rewrite_fn, groundedness_call_fn=_good_groundedness,
    )
    complete = br.is_naturalness_pass_complete(detection, results)
    return [
        ("results 길이가 issues와 동일(배치 전체가 죽지 않고 둘 다 살아남음)", len(results) == 2),
        ("첫 번째 stage가 exception", results[0]["stage"] == "exception"),
        ("두 번째도 stage가 exception(같은 rewrite_fn)", results[1]["stage"] == "exception"),
        ("complete False", complete is False),
        ("예외가 나도 report는 원본 그대로", report["system_sections"][0]["body"] == original_body),
    ]


def testRT10_detection_incomplete_complete_false():
    """Test 10 — Detection INCOMPLETE는 절대 complete로 승격되지 않음."""
    detection = {"status": "INCOMPLETE", "issues": [], "detail": "stop_reason=max_tokens"}
    complete = br.is_naturalness_pass_complete(detection, [])
    return [("INCOMPLETE -> complete False(issue/결과가 0개여도)", complete is False)]


def testRT11_length_mismatch_detected():
    """Test 11 — issue 누락(results 길이가 issues 길이와 다름) 자체를 감지."""
    detection = {"status": "ISSUES_FOUND", "issues": [{"category": 1}, {"category": 5}]}
    fake_results = [{"accepted": True}]  # 어딘가에서 issue 하나가 누락된 상황을 직접 대입
    complete = br.is_naturalness_pass_complete(detection, fake_results)
    return [("results 길이가 issues보다 적으면 complete False", complete is False)]


def testRT12_duplicate_issue_entries_each_tracked_separately():
    """Test 12 — 동일 issue가 두 번(duplicate) 들어와도 각각 별도로 결과에 남음."""
    report = _fake_multi_paragraph_report()
    computed = {"tier": "premium"}
    quote = "칠살은 부담이자 추진력을 뜻하며"
    issue = _ms_issue(quote, category=1)
    duplicate_issues = [issue, dict(issue)]
    detection = {"status": "ISSUES_FOUND", "issues": duplicate_issues}

    def paraphrase_rewrite_fn(user_message):
        return ("세 번째 문단을 다시 씁니다. 칠살이라는 기운은 부담인 동시에 추진력의 "
                "원천이 되는 자리이며, 이 사람은 도전정신이 남다른 편입니다."), _FakeUsage()

    results = br.run_targeted_rewrite_pass(
        report, computed, detection["issues"], rewrite_fn=paraphrase_rewrite_fn, groundedness_call_fn=_good_groundedness,
    )
    return [
        ("results 길이 2(하나가 삼켜지지 않음)", len(results) == 2),
        ("첫 번째 성공", results[0]["accepted"] is True),
        # 실제 실행 결과 기준으로 확정: resolve_naturalness_issue_path()가 field 전체
        # 텍스트를 대상으로 quoted_sentence 존재를 먼저 확인하므로(paragraph 단위 확인
        # 이전 단계), 첫 rewrite로 field 전체 문구가 바뀌면 여기서 먼저 걸린다 —
        # "path_resolution" 단계에서 실패함(paragraph_location에는 도달하지 않음).
        ("두 번째는 첫 rewrite로 원문이 바뀌어 field 단계에서 위치를 못 찾음(path_resolution 실패)",
         results[1]["accepted"] is False and results[1].get("stage") == "path_resolution"),
        ("두 번째 실패도 quoted_sentence가 echo되어 원본 issue와 연결 가능", results[1]["quoted_sentence"] == quote),
        ("두 번째 실패에 '직전 rewrite 때문에 stale해짐' 표시가 있음(Detection 오류로 오인 방지)",
         results[1].get("stale_due_to_earlier_rewrite_in_this_pass") is True),
    ]


def testRT13_two_distinct_issues_same_paragraph():
    """Test 13 — 동일 paragraph를 가리키는 서로 다른(진짜 다른 문구) 두 issue."""
    report = _fake_multi_paragraph_report()
    computed = {"tier": "premium"}
    issue_a = _ms_issue("칠살은 부담이자 추진력을 뜻하며", category=1)
    issue_b = _ms_issue("이 사람은 도전정신이 강한 편입니다", category=6)
    detection = {"status": "ISSUES_FOUND", "issues": [issue_a, issue_b]}

    def paraphrase_rewrite_fn(user_message):
        return ("세 번째 문단을 다시 씁니다. 칠살이라는 기운은 부담인 동시에 추진력의 "
                "원천이 되는 자리이며, 도전정신이 남다른 편입니다."), _FakeUsage()

    results = br.run_targeted_rewrite_pass(
        report, computed, detection["issues"], rewrite_fn=paraphrase_rewrite_fn, groundedness_call_fn=_good_groundedness,
    )
    return [
        ("첫 번째 issue -> 문단2 재작성 성공", results[0]["accepted"] is True and results[0]["paragraph_index"] == 2),
        # RT12와 동일한 이유(field-level 존재 확인이 paragraph 단위 확인보다 먼저 실행됨)로
        # path_resolution에서 실패한다 — paragraph_location에는 도달하지 않음.
        ("두 번째 issue -> 같은 문단이 이미 바뀌어 field 단계에서 원문을 못 찾음(path_resolution)",
         results[1]["accepted"] is False and results[1]["stage"] == "path_resolution"),
        ("두 번째 실패도 결과에 명시적으로 남음(사라지지 않음)", len(results) == 2),
        ("두 번째 실패에 stale 표시가 있음(진짜 위치 오류가 아니라 순서 때문임을 구분)",
         results[1].get("stale_due_to_earlier_rewrite_in_this_pass") is True),
    ]


def testRT14_earlier_rewrite_does_not_affect_unrelated_paragraph_issue():
    """Test 14 — 앞선 rewrite가 '다른' paragraph의 issue에는 영향을 주지 않음(대조군)."""
    report = _fake_multi_paragraph_report()
    computed = {"tier": "premium"}
    issue_a = _ms_issue("칠살은 부담이자 추진력을 뜻하며", category=1)  # paragraph2
    issue_b = _ms_issue("정관은 명예와 책임을 뜻하는 기운입니다.", category=6)  # paragraph0
    detection = {"status": "ISSUES_FOUND", "issues": [issue_a, issue_b]}
    results = br.run_targeted_rewrite_pass(
        report, computed, detection["issues"], rewrite_fn=_good_rewrite_fn, groundedness_call_fn=_good_groundedness,
    )
    return [
        ("두 issue 모두 성공(서로 다른 문단이라 영향 없음)", all(r["accepted"] is True for r in results)),
        ("서로 다른 paragraph_index", results[0]["paragraph_index"] != results[1]["paragraph_index"]),
    ]


def testRT15_complete_true_only_when_all_resolved():
    """Test 15 — 모든 issue가 resolved일 때만 complete=True."""
    report = _fake_multi_paragraph_report()
    computed = {"tier": "premium"}
    issue_a = _ms_issue("정관은 명예와 책임을 뜻하는 기운입니다.", category=1)
    issue_b = _ms_issue("칠살은 부담이자 추진력을 뜻하며", category=6)
    detection = {"status": "ISSUES_FOUND", "issues": [issue_a, issue_b]}

    results_all_ok = br.run_targeted_rewrite_pass(
        report, computed, detection["issues"], rewrite_fn=_good_rewrite_fn, groundedness_call_fn=_good_groundedness,
    )
    complete_all_ok = br.is_naturalness_pass_complete(detection, results_all_ok)

    report2 = _fake_multi_paragraph_report()
    call_n = {"n": 0}

    def one_fail_groundedness(prompt):
        call_n["n"] += 1
        return "OK" if call_n["n"] == 1 else "문제가 있습니다"

    results_one_fail = br.run_targeted_rewrite_pass(
        report2, computed, detection["issues"], rewrite_fn=_good_rewrite_fn, groundedness_call_fn=one_fail_groundedness,
    )
    complete_one_fail = br.is_naturalness_pass_complete(detection, results_one_fail)

    return [
        ("전부 resolved -> complete True", complete_all_ok is True),
        ("하나라도 미resolved -> complete False", complete_one_fail is False),
    ]


def testRT16_out_of_scope_category_recorded_not_silently_dropped():
    """Test 16 — 이 폐쇄 루프의 자동 대상이 아닌 category(2026-09-03 확장 이후로는
    9뿐 — 2/3/4/8은 이제 대상에 포함됨, testCAT_* 참고)도 결과에서 사라지지 않음."""
    report = _fake_multi_paragraph_report()
    computed = {"tier": "premium"}
    issue_scope = _ms_issue("칠살은 부담이자 추진력을 뜻하며", category=1)
    issue_out = _ms_issue("정관은 명예와 책임을 뜻하는 기운입니다.", category=9)
    detection = {"status": "ISSUES_FOUND", "issues": [issue_scope, issue_out]}
    results = br.run_targeted_rewrite_pass(
        report, computed, detection["issues"], rewrite_fn=_good_rewrite_fn, groundedness_call_fn=_good_groundedness,
    )
    complete = br.is_naturalness_pass_complete(detection, results)
    return [
        ("결과 길이 2(대상 밖 카테고리도 사라지지 않음)", len(results) == 2),
        ("두 번째 stage가 out_of_scope_category", results[1]["stage"] == "out_of_scope_category"),
        ("out_of_scope_category도 accepted=False(자동 해결로 치지 않음)", results[1]["accepted"] is False),
        ("대상 밖 issue가 남아있으면 complete False", complete is False),
    ]


def testRT17_skipped_cap_recorded_not_silently_dropped():
    """Test 17 — max_rewrites_per_report 상한 초과분도 결과에서 사라지지 않음."""
    report = _fake_multi_paragraph_report()
    computed = {"tier": "premium"}
    issue_a = _ms_issue("정관은 명예와 책임을 뜻하는 기운입니다.", category=1)
    issue_b = _ms_issue("칠살은 부담이자 추진력을 뜻하며", category=1)
    detection = {"status": "ISSUES_FOUND", "issues": [issue_a, issue_b]}
    results = br.run_targeted_rewrite_pass(
        report, computed, detection["issues"], rewrite_fn=_good_rewrite_fn, groundedness_call_fn=_good_groundedness,
        max_rewrites_per_report=1,
    )
    complete = br.is_naturalness_pass_complete(detection, results)
    return [
        ("결과 길이 2(상한 초과분도 사라지지 않음)", len(results) == 2),
        ("첫 번째는 실제로 시도되어 성공", results[0]["accepted"] is True),
        ("두 번째는 skipped_cap으로 명시 기록", results[1]["stage"] == "skipped_cap"),
        ("skipped_cap도 accepted=False", results[1]["accepted"] is False),
        ("상한 초과분이 남아있으면 complete False", complete is False),
    ]


def testRT18_stale_flag_not_set_for_genuinely_nonexistent_quote():
    """Test 18 — 애초에 존재한 적 없는 quoted_sentence는 stale 표시가 붙지 않아야 함
    (거짓 양성 방지 — "이전 rewrite 때문"이라는 표시는 실제로 그런 경우에만 붙어야 함)."""
    report = _fake_multi_paragraph_report()
    computed = {"tier": "premium"}
    issue = _ms_issue("이 문장은 원문에 전혀 존재하지 않는 완전히 다른 내용입니다", category=1)
    detection = {"status": "ISSUES_FOUND", "issues": [issue]}
    results = br.run_targeted_rewrite_pass(
        report, computed, detection["issues"], rewrite_fn=_good_rewrite_fn, groundedness_call_fn=_good_groundedness,
    )
    return [
        ("stage가 path_resolution", results[0]["stage"] == "path_resolution"),
        ("stale 표시가 없음(진짜 존재한 적 없는 문구이므로 오탐 아님)",
         not results[0].get("stale_due_to_earlier_rewrite_in_this_pass")),
    ]


def testRT19_key_based_path_new_reference_systems_in_pass():
    """Test 19 — needs_key=True(new_reference_systems)도 다중 issue orchestration에서
    index 기반 path와 동일하게 안전하게 처리되는지(추적/echo/complete 판정 전부)."""
    report = _fake_report()
    computed = {"tier": "premium"}
    issue = {
        "section_kind": "new_reference_systems", "system_or_key": "taekil", "field": "body",
        "category": 1, "quoted_sentence": "앞으로 30일 안에서 흐름이 좋은 날은 9월 6일입니다.",
        "reason": "r",
    }
    detection = {"status": "ISSUES_FOUND", "issues": [issue]}
    results = br.run_targeted_rewrite_pass(
        report, computed, detection["issues"], rewrite_fn=_good_rewrite_fn, groundedness_call_fn=_good_groundedness,
    )
    complete = br.is_naturalness_pass_complete(detection, results)
    return [
        ("key 기반 path도 accepted True", results[0]["accepted"] is True),
        ("system_or_key가 echo됨", results[0]["system_or_key"] == "taekil"),
        ("path가 정확히 ('new_reference_systems','taekil','body')",
         results[0]["path"] == ("new_reference_systems", "taekil", "body")),
        ("complete True", complete is True),
    ]


# ============================================================================
# TEST CAT/MAIN — category 2/3/4/8 자동 해결 확장 + main() 배선 검증(2026-09-03).
#
# STEP2 조사 결론: rewrite/scope/groundedness/format_integrity 전부 category 번호를
# 참조하지 않는 범용 로직이라, target_categories를 1~8 전부로 넓혀도 구조적으로
# 안전함을 코드 추적으로 확인했다. category9만 별도 결정론적 경로
# (scan_report_for_internal_field_leaks)를 계속 쓰므로 이 폐쇄 루프 대상에서 제외.
# 아래 테스트는 synthetic fixture로 "구조적 계약"만 검증한다 — 실제 Naturalness
# Detection이 이 카테고리들을 실제로 이렇게 검출했다는 뜻이 아니다(사용자 지시로
# 명확히 구분).
# ============================================================================


def testCAT_all_non9_categories_flow_through_full_pipeline():
    """category 2/3/4/8이 더 이상 out_of_scope로 걸러지지 않고 category 1/5/6/7과
    동일한 rewrite->scope->groundedness->format->splice 경로를 그대로 통과하는지
    구조적으로 확인(synthetic 픽스처, 구조 계약 검증용 — 실제 Detection 결과 아님)."""
    labels = []
    for cat in (2, 3, 4, 8):
        report = _fake_multi_paragraph_report()
        computed = {"tier": "premium"}
        issue = _ms_issue("칠살은 부담이자 추진력을 뜻하며", category=cat)
        result = br.rewrite_and_validate_issue(
            report, computed, issue, rewrite_fn=_good_rewrite_fn, groundedness_call_fn=_good_groundedness,
        )
        labels.append((f"category {cat} -> ACCEPT(구조적 장벽 없음)", result["accepted"] is True))
    return labels


def testCAT_target_categories_now_includes_2_3_4_8_by_default():
    """target_categories 기본값이 실제로 1~8 전부를 포함하고 9는 제외하는지 확인."""
    return [
        ("1~8 전부 포함", all(c in br._ALL_REWRITABLE_NATURALNESS_CATEGORIES for c in range(1, 9))),
        ("9는 제외", 9 not in br._ALL_REWRITABLE_NATURALNESS_CATEGORIES),
    ]


def testCAT_category9_still_out_of_scope_via_pass():
    """category 9는 여전히 이 폐쇄 루프의 자동 대상이 아니어야 한다(별도 결정론적
    경로 — scan_report_for_internal_field_leaks가 이미 담당하는 영역 유지)."""
    report = _fake_multi_paragraph_report()
    computed = {"tier": "premium"}
    issue = _ms_issue("칠살은 부담이자 추진력을 뜻하며", category=9)
    detection = {"status": "ISSUES_FOUND", "issues": [issue]}
    results = br.run_targeted_rewrite_pass(
        report, computed, detection["issues"], rewrite_fn=_good_rewrite_fn, groundedness_call_fn=_good_groundedness,
    )
    return [
        ("category 9는 out_of_scope_category로 기록됨(자동 rewrite 대상 아님)",
         results[0]["stage"] == "out_of_scope_category"),
    ]


def testMAIN1_wiring_sequence_matches_main_and_never_blocks():
    """main()이 실제로 쓰는 순서(verify_naturalness -> run_targeted_rewrite_pass ->
    is_naturalness_pass_complete -> log_naturalness_pass_result)를 그대로 재현해
    end-to-end로 확인한다. main() 자체는 실제 API 키ㆍCLI 인자ㆍ실제 리포트 생성에
    강하게 의존해 직접 호출하지 않는다 — 이 테스트는 "main()이 쓰는 배선 순서"를
    검증하는 것이지 main() 함수 자체를 호출하는 것은 아님(정직하게 구분해서 명시)."""
    import tempfile

    report = _fake_multi_paragraph_report()
    computed = {"tier": "premium"}

    def mock_detection_call_fn(prompt):
        return _FakeResponse([
            _FakeToolUseBlock("submit_naturalness_issues", {
                "issues": [
                    {"section_kind": "system_sections", "index": 0, "field": "body",
                     "category": 1, "quoted_sentence": "칠살은 부담이자 추진력을 뜻하며", "reason": "r"},
                ],
            }),
        ])

    naturalness_result = br.verify_naturalness(report, tier="premium", call_fn=mock_detection_call_fn)
    rewrite_pass_results = br.run_targeted_rewrite_pass(
        report, computed, naturalness_result["issues"],
        rewrite_fn=_good_rewrite_fn, groundedness_call_fn=_good_groundedness,
    )
    complete = br.is_naturalness_pass_complete(naturalness_result, rewrite_pass_results)

    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "naturalness_pass_log.jsonl"
        br.log_naturalness_pass_result(naturalness_result, rewrite_pass_results, complete, computed, log_path=log_path)
        logged = json.loads(log_path.read_text(encoding="utf-8").strip())

    return [
        ("naturalness_result status가 ISSUES_FOUND", naturalness_result["status"] == "ISSUES_FOUND"),
        ("rewrite_pass_results 길이 1, accepted True",
         len(rewrite_pass_results) == 1 and rewrite_pass_results[0]["accepted"] is True),
        ("complete True(단일 issue가 실제로 해결됐으므로)", complete is True),
        ("로그 파일에 정확히 기록됨(issue_count/resolved_count/complete 일치)",
         logged["issue_count"] == 1 and logged["resolved_count"] == 1 and logged["complete"] is True),
    ]


def testMAIN2_wiring_never_raises_when_incomplete_or_unresolved():
    """complete=False(Detection INCOMPLETE 또는 unresolved issue 존재)여도
    log_naturalness_pass_result()가 예외를 던지지 않아야 한다 — "이미 돈을 낸
    리포트를 부가 검증 때문에 날리면 안 된다"는 기존 원칙과 충돌하지 않는지 직접 확인."""
    import tempfile

    computed = {"tier": "premium"}

    incomplete_result = {"status": "INCOMPLETE", "issues": [], "detail": "stop_reason=max_tokens"}
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "log.jsonl"
        try:
            br.log_naturalness_pass_result(incomplete_result, [], False, computed, log_path=log_path)
            raised1 = False
        except Exception:
            raised1 = True

    unresolved_results = [{
        "accepted": False, "stage": "groundedness", "reason": "r", "category": 1,
        "section_kind": "system_sections", "index": 0, "field": "body", "system_or_key": None,
    }]
    detection = {"status": "ISSUES_FOUND", "issues": [{"category": 1}]}
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "log.jsonl"
        try:
            br.log_naturalness_pass_result(detection, unresolved_results, False, computed, log_path=log_path)
            raised2 = False
        except Exception:
            raised2 = True

    return [
        ("INCOMPLETE여도 예외를 던지지 않음(리포트 저장을 막지 않음)", raised1 is False),
        ("unresolved issue가 있어도 예외를 던지지 않음(리포트 저장을 막지 않음)", raised2 is False),
    ]


# ============================================================================
# TEST MODEL1~3 — 모든 Anthropic LLM 호출 Sonnet 5 통일 검증(2026-09-03).
#
# GROUNDEDNESS_MODEL 기본값을 haiku-4-5에서 claude-sonnet-5로 바꾸고, verify_naturalness/
# verify_field_groundedness/verify_groundedness/quality_rubric.judge_semantic_quality에
# thinking={"type":"disabled"} 호환성 파라미터를 추가했다(sonnet-5는 명시 안 하면
# 적응형 사고가 기본으로 켜져 이미 빠듯한 max_tokens 예산을 먼저 먹을 수 있음 —
# call_llm/_call_targeted_rewrite_llm이 이미 쓰던 것과 같은 패턴). 실제 네트워크 호출은
# 전혀 하지 않는다 — anthropic.Anthropic을 가짜 클래스로 치환하고, 실제 프로덕션 로그
# 파일에 "ACTUAL_API_DATA"로 잘못 남지 않도록 api_usage.log_usage_record도 캡처용으로
# 치환한 뒤, OFFLINE_TEST_MODE 가드만 우회해 실제 함수 코드 경로를 그대로 실행하며
# 최종 model=/thinking= kwargs를 직접 확인한다.
# ============================================================================


def _make_fake_anthropic_client(captured_calls):
    fake_tool_inputs = {
        "submit_naturalness_issues": {"issues": []},
        "submit_field_rewrite": {"new_value": "테스트 문단입니다."},
        "submit_report": {},
        "submit_quality_scores": {},
    }

    class _FakeTextBlock:
        type = "text"
        text = "OK"

    class _FakeMessages:
        @staticmethod
        def create(**kwargs):
            captured_calls.append({"method": "create", **kwargs})
            tools = kwargs.get("tools")
            if tools:
                tool_name = tools[0]["name"]
                block = _FakeToolUseBlock(tool_name, fake_tool_inputs.get(tool_name, {}))
                return _FakeResponse([block], stop_reason="end_turn")
            return _FakeResponse([_FakeTextBlock()], stop_reason="end_turn")

        @staticmethod
        def stream(**kwargs):
            captured_calls.append({"method": "stream", **kwargs})
            tools = kwargs.get("tools")
            tool_name = tools[0]["name"] if tools else None
            block = _FakeToolUseBlock(tool_name, fake_tool_inputs.get(tool_name, {}))
            resp = _FakeResponse([block])

            class _StreamCtx:
                def __enter__(self):
                    return self

                def __exit__(self, *exc):
                    return False

                def get_final_message(self):
                    return resp

            return _StreamCtx()

    class _FakeAnthropic:
        def __init__(self, *a, **kw):
            pass

        messages = _FakeMessages()

    return _FakeAnthropic


def testMODEL1_verify_functions_use_sonnet5_via_real_code_path():
    """TEST MODEL1 — verify_naturalness/verify_field_groundedness/verify_groundedness의
    실제 코드 경로(OFFLINE_TEST_MODE 가드만 우회, 그 외 로직은 전혀 안 바꿈)를 그대로
    실행해, client.messages.create()에 최종적으로 전달되는 model=/thinking= 값을 직접
    캡처해 확인한다. anthropic.Anthropic 자체가 가짜 클래스라 네트워크 호출은 0건."""
    captured_calls = []
    logged_records = []

    fake_anthropic_cls = _make_fake_anthropic_client(captured_calls)

    def _capturing_log(record, *a, **kw):
        logged_records.append(record)
        return record

    original_offline = br.OFFLINE_TEST_MODE
    original_anthropic_cls = br.anthropic.Anthropic
    original_log_fn = br.api_usage.log_usage_record

    br.OFFLINE_TEST_MODE = False
    br.anthropic.Anthropic = fake_anthropic_cls
    br.api_usage.log_usage_record = _capturing_log
    try:
        report = _fake_report()
        computed = {"tier": "single"}
        br.verify_naturalness(report, tier="single")
        br.verify_field_groundedness(computed, "테스트 문단입니다.")
        br.verify_groundedness(report, computed)
    finally:
        br.OFFLINE_TEST_MODE = original_offline
        br.anthropic.Anthropic = original_anthropic_cls
        br.api_usage.log_usage_record = original_log_fn

    results = [
        ("실제 호출 3건 전부 캡처됨(naturalness/field_groundedness/groundedness)", len(captured_calls) == 3),
    ]
    for call in captured_calls:
        results.append((f"{call['method']} 호출의 model == claude-sonnet-5", call.get("model") == "claude-sonnet-5"))
        results.append((f"{call['method']} 호출에 thinking 명시적으로 disabled", call.get("thinking") == {"type": "disabled"}))
    results.append(("로깅된 model 값도 전부 claude-sonnet-5", len(logged_records) == 3 and all(r.get("model") == "claude-sonnet-5" for r in logged_records)))
    results.append(("로깅된 thinking_disabled 전부 True", all(r.get("thinking_disabled") is True for r in logged_records)))
    return results


def testMODEL2_generation_and_rewrite_reference_model_constant():
    """TEST MODEL2 — call_llm()/_call_targeted_rewrite_llm()은 이번 STEP에서 손대지
    않았고 이미 MODEL(=claude-sonnet-5) 상수를 쓰고 있었다 — 소스 코드 직접 대조로
    재확인한다. 이 두 함수는 SYSTEM_PROMPT/REPORT_SCHEMA 전체를 실행해야 해서, kwargs를
    직접 캡처하는 실행 기반 테스트로 만들면 이번 STEP의 목적(모델 통일)과 무관한
    부분까지 무겁게 시뮬레이션해야 해 오히려 취약해진다 — 대신 소스 텍스트 근거로
    확인한다(추측 아님, inspect.getsource로 실제 함수 본문을 읽음)."""
    import inspect
    call_llm_src = inspect.getsource(br.call_llm)
    rewrite_src = inspect.getsource(br._call_targeted_rewrite_llm)
    return [
        ("call_llm()이 MODEL 상수를 사용", "model=MODEL" in call_llm_src),
        ("call_llm()에 thinking disabled 유지됨(기존, 무수정)", 'thinking={"type": "disabled"}' in call_llm_src),
        ("_call_targeted_rewrite_llm()이 MODEL 상수를 사용", "model=MODEL" in rewrite_src),
        ("_call_targeted_rewrite_llm()에 thinking disabled 유지됨(기존, 무수정)", 'thinking={"type": "disabled"}' in rewrite_src),
        ("MODEL 상수 자체가 claude-sonnet-5", br.MODEL == "claude-sonnet-5"),
        ("GROUNDEDNESS_MODEL 상수가 claude-sonnet-5로 통일됨", br.GROUNDEDNESS_MODEL == "claude-sonnet-5"),
    ]


def testMODEL3_quality_rubric_judge_inherits_sonnet5():
    """TEST MODEL3 — test/golden/quality_rubric.py의 judge_semantic_quality()는 실제
    채점 시 진짜 비용이 발생하는 수동 QA 도구라 import/실행하지 않고 소스 텍스트만 직접
    읽어 확인한다. judge_model = model or br.GROUNDEDNESS_MODEL 구조라 GROUNDEDNESS_MODEL
    통일만으로 자동으로 sonnet-5를 쓰게 됨 — thinking도 명시적으로 꺼져 있는지 확인."""
    rubric_path = HERE / "golden" / "quality_rubric.py"
    text = rubric_path.read_text(encoding="utf-8")
    return [
        ("judge_model이 br.GROUNDEDNESS_MODEL을 기본값으로 상속", "judge_model = model or br.GROUNDEDNESS_MODEL" in text),
        ("judge 호출에도 thinking이 명시적으로 꺼져 있음", 'thinking={"type": "disabled"}' in text),
    ]


# ============================================================================
# TEST COMPUTED1~9 — computed.json 핵심 계약 검증(2026-09-03, STEP2).
#
# enforce_computed_core_contract()는 saju.pillars/saju.shensha/saju.correspondence.
# shi_shen_meanings만 검증한다(이 세 개만 "본문 생성ㆍ검증에 실제로 쓰이는 핵심"으로
# 확정됨 — astrology/tarot/tojeong 등 tier별 optional system은 절대 건드리지 않음).
# 실제 프로젝트에 영구히 커밋된 fixture(tools/crossnotics-engine/test/out-*.json)만
# 사용한다 — scratchpad(세션 임시 디렉터리)의 fixture는 향후 실행 환경에서 사라질 수
# 있어 영구 회귀 테스트에 쓰지 않는다.
# ============================================================================


def _real_computed_fixture(name):
    return json.loads((ENGINE_DIR / f"test/{name}").read_text(encoding="utf-8"))


def testCOMPUTED1_valid_computed_passes():
    """COMPUTED1 — 정상 computed 핵심 구조는 예외 없이 통과."""
    computed = _real_computed_fixture("out-single.json")
    try:
        br.enforce_computed_core_contract(computed)
        ok, err = True, None
    except br.ComputedContractError as e:
        ok, err = False, str(e)
    return [("정상 computed -> 예외 없음", ok and err is None)]


def testCOMPUTED2_missing_pillars_fails():
    """COMPUTED2 — pillars 누락은 명시적으로 FAIL(조용히 기본값으로 넘어가지 않음)."""
    computed = _real_computed_fixture("out-single.json")
    del computed["saju"]["pillars"]
    try:
        br.enforce_computed_core_contract(computed)
        raised = False
    except br.ComputedContractError:
        raised = True
    return [("pillars 누락 -> ComputedContractError 발생", raised)]


def testCOMPUTED3_broken_shensha_fails():
    """COMPUTED3 — shensha 구조 오류(meaning 누락)는 명시적으로 FAIL."""
    computed = _real_computed_fixture("out-single.json")
    del computed["saju"]["shensha"]["hwagae"]["meaning"]
    try:
        br.enforce_computed_core_contract(computed)
        raised = False
    except br.ComputedContractError:
        raised = True
    return [("shensha.hwagae.meaning 누락 -> ComputedContractError 발생", raised)]


def testCOMPUTED4_missing_shi_shen_meanings_fails():
    """COMPUTED4 — shi_shen_meanings 누락(타입 오류 포함)은 명시적으로 FAIL."""
    computed = _real_computed_fixture("out-single.json")
    computed["saju"]["correspondence"]["shi_shen_meanings"] = "이건 list가 아니라 문자열임"
    try:
        br.enforce_computed_core_contract(computed)
        raised = False
    except br.ComputedContractError:
        raised = True
    return [("shi_shen_meanings 타입 오류 -> ComputedContractError 발생", raised)]


def testCOMPUTED5_shi_shen_gan_is_scalar():
    """COMPUTED5 — shi_shen_gan은 실제 데이터에서 단일 문자열(scalar) 구조임을 확인
    (STEP2 조사에서 saju.js:48 pillarDetail()이 단일 값을 반환함을 코드로 확인한 것을
    실제 fixture로도 재확인)."""
    computed = _real_computed_fixture("out-single.json")
    year_gan = computed["saju"]["pillars"]["year"]["shi_shen_gan"]
    return [
        ("year pillar의 shi_shen_gan이 문자열(scalar)", isinstance(year_gan, str)),
    ]


def testCOMPUTED6_shi_shen_zhi_is_list():
    """COMPUTED6 — shi_shen_zhi는 실제 데이터에서 리스트(다중값) 구조임을 확인
    (saju.js:49 .map()이 배열을 반환함을 코드로 확인한 것을 실제 fixture로도 재확인 —
    STEP2/gan-zhi 문제의 근본 구조가 실제 데이터에서도 그대로임을 보존 확인)."""
    computed = _real_computed_fixture("out-single.json")
    year_zhi = computed["saju"]["pillars"]["year"]["shi_shen_zhi"]
    return [
        ("year pillar의 shi_shen_zhi가 리스트", isinstance(year_zhi, list)),
    ]


def testCOMPUTED7_optional_systems_absent_does_not_fail():
    """COMPUTED7 — astrology/tarot/tojeong 등 optional system이 없어도(mini tier처럼
    saju만 있는 경우) 계약 검증은 FAIL시키지 않는다."""
    computed = _real_computed_fixture("out-single.json")
    # out-single.json 자체가 이미 astrology/tarot 등을 안 가진 saju-only 구조인지
    # 확인하고, 명시적으로 saju만 남긴 dict로도 재검증한다(다른 tier 오염 없이).
    minimal_computed = {"customer": computed.get("customer"), "tier": "mini", "saju": computed["saju"]}
    try:
        br.enforce_computed_core_contract(minimal_computed)
        ok = True
    except br.ComputedContractError:
        ok = False
    return [
        ("out-single.json에 astrology 없음(saju-only 확인)", "astrology" not in computed),
        ("saju만 있는 computed도 계약 검증 통과(optional system 부재는 FAIL 아님)", ok),
    ]


# 2026-09-03 — 12운성 재검증(3차 라운드). 아래 딕셔너리는 correspondence.js의
# TWELVE_STAGE_MEANING 12개 항목 각각에서 Python STRUCTURAL_TERM_GLOSSARY와 "실제로
# 공유하는 핵심 개념 단어(anchor)"를 사람이 직접 두 텍스트를 대조해 골라낸 것이다(2026-
# 09-03 재조사에서 12개 전부 직접 대조 확인). byte-for-byte 동일성을 요구하지 않으면서
# (정상적인 문구 개선까지 실패시키지 않기 위해), "완전히 다른 개념으로 바뀌는 것"은
# 잡아내기 위한 deterministic anchor 방식 — LLM/API 없이, 이 anchor 단어가 양쪽 텍스트에
# 그대로 남아있는지만 문자열 포함 검사로 확인한다. 이 방식의 한계: anchor가 유지된 채
# 나머지 의미가 왜곡되는 경우까지는 못 잡는다(완전한 의미 동일성 보장은 아님 — 이
# 한계를 숨기지 않고 여기 명시한다).
_TWELVE_STAGE_SHARED_ANCHORS = {
    "장생": "태어나", "목욕": "아직", "관대": "준비", "임관": "인정받",
    "제왕": "왕성", "쇠": "차분", "병": "들여다보", "사": "정리",
    "묘": "갈무리", "절": "시작", "태": "품", "양": "자라나",
}


def _extract_js_dict_block(js_text, const_name):
    block = js_text.split(f"const {const_name}")[1].split("};")[0]
    return dict(re.findall(r'"([^"]+)":\s*"([^"]*)"', block))


def testCOMPUTED8_twelve_stage_meanings_js_python_divergence_documented():
    """COMPUTED8 — 12운성 JS(correspondence.js TWELVE_STAGE_MEANING) ↔ Python
    (STRUCTURAL_TERM_GLOSSARY) 값을 실제로 diff하고, 재검증(2026-09-03)에서 확정된
    결론까지 회귀로 고정한다.

    [재검증 결론 — 실제 코드+실제 프로덕션 사용례 근거]
    1) 키 집합(12개 단계 이름)은 완전히 일치함(회귀 보호 A).
    2) 텍스트 "내용"은 12개 전부 문면상 다르지만, 12개 전부에서 공유하는 핵심 개념
       단어(anchor)가 실제로 존재함을 직접 대조로 확인함(회귀 보호 B — 완전히 다른
       개념이 아니라는 근거).
    3) 포맷은 의도적으로 다름: correspondence.js:230 "완결된 문장체로 다시 씀" vs
       같은 파일 SHI_SHEN_MEANING(214행)ㆍshensha.js SHENSHA_MEANING(41-44행)의
       "{{용어}} 삽입 형식에 맞는 관형구로 다시 씀"(정반대 지시) — JS는 마침표로 끝나는
       완결 문장, Python은 마침표 없는 명사구. 이 성질 자체를 회귀로 고정(회귀 보호 C/D).
    4) correspondence.twelve_stage_meanings는 build_report.py 어디에서도 `.get(...)`으로
       읽히지 않음(grep 전수 확인, production 코드 0건) — build_term_gloss_map()은
       STRUCTURAL_TERM_GLOSSARY만 시드로 쓰고 이 JS 필드를 참조하지 않는다. 즉 이건
       "두 소비 경로가 경쟁하는" 상황이 아니라 "Python이 쓰는 자기 사전"과 "현재 아무도
       안 쓰는 JS 필드"가 우연히 같은 개념을 다르게 담고 있는 상황이다 — 과거 실제
       사고(2026-08-30, saju.js 문서 하단 주석)도 이 JS 필드와의 불일치가 아니라
       STRUCTURAL_TERM_GLOSSARY 키가 saju.js DI_SHI_KO 키(같은 파일)와 안 맞았던
       것이었다.
    5) 결론: 문자열 SSOT 불가(포맷 비호환, 실제 프로덕션 사용례로 증명 — TestCOMPUTED10
       참고), 그리고 의미 SSOT(공유 원천+포맷터 2개)도 "12운성 이름→2문장 서술"을
       "12운성 이름→명사구"로 결정론적으로 변환할 방법이 없어(요약은 비결정론적 창작
       작업) 이번 STEP에서 구현 대상이 아님 — 이 프로젝트의 "지어내지 않는다/결정론적
       처리" 원칙과 충돌하므로 새 포맷터를 만들지 않는다. Python dictionary는 그대로
       유지한다."""
    js_text = (ENGINE_DIR / "correspondence.js").read_text(encoding="utf-8")
    js_dict = _extract_js_dict_block(js_text, "TWELVE_STAGE_MEANING")
    js_keys = set(js_dict.keys())
    py_keys_in_js = set(br.STRUCTURAL_TERM_GLOSSARY.keys()) & js_keys

    results = [
        ("JS TWELVE_STAGE_MEANING이 정확히 12개 키", len(js_keys) == 12),
        ("Python STRUCTURAL_TERM_GLOSSARY가 그 12개 키를 전부 포함(회귀 보호 A)", py_keys_in_js == js_keys),
    ]

    # 회귀 보호 B/E — anchor 단어가 양쪽에 실제로 남아있는지(완전히 다른 개념으로
    # 바뀌는 변경 탐지). 이번 재검증에서 12개 전부 직접 대조해 확정된 anchor.
    for term, anchor in _TWELVE_STAGE_SHARED_ANCHORS.items():
        js_val = js_dict.get(term, "")
        py_val = br.STRUCTURAL_TERM_GLOSSARY.get(term, "")
        results.append((f"{term}: JS/Python 둘 다 공유 개념어 '{anchor}' 포함", anchor in js_val and anchor in py_val))

    # 회귀 보호 C/D — 포맷 성질 자체(JS=완결 문장체, Python=명사구, 마침표 유무로 구분).
    # Python 값이 실수로 JS 문장체로 덮어써지면(사고 재현 방지) 이 검사가 바로 잡는다.
    for term in js_keys:
        js_val = js_dict[term]
        py_val = br.STRUCTURAL_TERM_GLOSSARY.get(term, "")
        results.append((f"{term}: JS 값은 문장 종결형(마침표로 끝남)", js_val.rstrip().endswith(".")))
        results.append((f"{term}: Python 값은 명사구(마침표로 끝나지 않음, JS 문장으로 덮어써지지 않았음)",
                         py_val != "" and not py_val.rstrip().endswith(".")))

    # correspondence.twelve_stage_meanings가 production 코드에서 읽히지 않는다는
    # 사실(위 docstring 4번) — 고정 회귀는 아니고(향후 정당하게 연결해도 막지 않기
    # 위해) 이번 재검증 시점의 사실만 기록.
    build_report_src = (Path(__file__).resolve().parent.parent / "build_report.py").read_text(encoding="utf-8")
    results.append((
        "(참고, 회귀 아님) 현재 build_report.py는 twelve_stage_meanings를 읽지 않음 — 재검증 시점 사실 기록",
        "twelve_stage_meanings" not in build_report_src,
    ))
    return results


def testCOMPUTED10_twelve_stage_js_format_breaks_real_production_usage():
    """COMPUTED10 — 2026-09-03 재검증. "JS 완성형 문장을 Python 삽입 자리에 넣으면
    문법이 깨진다"는 주장을 추상적으로 하지 않고, 실제 프로덕션에서 관찰된 삽입
    위치(scratchpad에 보존된 실제 API raw 응답, grep으로 직접 확인한 실사용 패턴)를
    그대로 재현해 코드로 증명한다. expand_term_placeholders()의 실제 치환 로직
    (build_report.py: `f"{gloss}({term})"`)을 그대로 사용 — 이 테스트만을 위한
    별도 로직을 새로 만들지 않는다."""
    def _apply_real_substitution(sentence, term, gloss):
        # expand_term_placeholders._sub()와 동일한 실제 치환 로직(build_report.py) —
        # 로직을 복사하지 않고 원본 함수 자체를 실행해 검증한다.
        gloss_map = {term: gloss}
        unmapped = []
        return br.expand_term_placeholders(sentence, gloss_map, unmapped)

    # 실제 raw LLM 응답(이번 세션 scratchpad에 보존된 master/tarot2 실제 API 결과)에서
    # 그대로 가져온 실사용 문장 — 지어낸 예문이 아니다.
    real_sentence_1 = "월주의 12운성이 {{제왕}}이라는 점도 눈여겨볼 만합니다."
    real_sentence_2 = "일지(묘)의 12운성은 {{병}}입니다."

    js_dict = _extract_js_dict_block((ENGINE_DIR / "correspondence.js").read_text(encoding="utf-8"), "TWELVE_STAGE_MEANING")

    py_result_1 = _apply_real_substitution(real_sentence_1, "제왕", br.STRUCTURAL_TERM_GLOSSARY["제왕"])
    js_result_1 = _apply_real_substitution(real_sentence_1, "제왕", js_dict["제왕"])
    py_result_2 = _apply_real_substitution(real_sentence_2, "병", br.STRUCTURAL_TERM_GLOSSARY["병"])
    js_result_2 = _apply_real_substitution(real_sentence_2, "병", js_dict["병"])

    return [
        ("[실사용1] Python 삽입 결과는 문장 종결('다.')이 정확히 1번만 나타남(정상)",
         py_result_1.count("다.") == 1),
        ("[실사용1] JS 문장을 그대로 삽입하면 문장 종결이 2번 이상 겹침(문법 파손 재현)",
         js_result_1.count("다.") >= 2),
        ("[실사용1] JS 삽입 결과에 '마침표 직후 괄호' 비정상 패턴이 실제로 나타남",
         ".(제왕)" in js_result_1),
        ("[실사용1] Python 삽입 결과에는 그 비정상 패턴이 없음", ".(제왕)" not in py_result_1),
        ("[실사용2] Python 삽입 결과는 문장 종결이 정확히 1번만 나타남(정상)",
         py_result_2.count("다.") == 1 or py_result_2.count("니다") == 1),
        ("[실사용2] JS 문장을 그대로 삽입하면 문장 종결이 2번 이상 겹침(문법 파손 재현)",
         js_result_2.count("다.") >= 2),
        ("[실사용2] JS 삽입 결과에 '마침표 직후 괄호' 비정상 패턴이 실제로 나타남",
         ".(병)" in js_result_2),
        ("[실사용2] Python 삽입 결과에는 그 비정상 패턴이 없음", ".(병)" not in py_result_2),
    ]


def testCOMPUTED11_js_has_no_sentence_insertion_mechanism():
    """COMPUTED11 — "반대 방향"(Python 문구를 JS 소비 위치에 넣었을 때) 검증.

    2026-09-03 재검증 결과: JS(correspondence.js buildCorrespondence())는
    twelve_stage_meanings를 {name, meaning} 데이터 쌍으로 조립만 할 뿐, 그 텍스트를
    자기 자신의 문장 템플릿에 삽입하는 메커니즘이 JS 어디에도 없다(코드에 문자열
    템플릿/치환 로직 자체가 없음 — buildCorrespondence()는 f-string/template literal로
    meaning을 다른 문장에 끼워넣는 코드가 아니라 순수 데이터 조립 함수). 따라서
    "Python 문구를 JS 소비 위치에 넣었을 때 문제가 없는지"는 애초에 검증 대상(JS 쪽
    삽입 지점)이 존재하지 않아 수행할 수 없다 — "확인 불가"가 아니라 "그런 지점이
    없음을 코드로 확인함"이다. 이 사실 자체를 회귀로 고정한다(JS에 나중에 실제
    템플릿 삽입 로직이 생기면 이 테스트가 실패해, 그 시점에 반대 방향 검증이
    새로 필요하다는 신호를 준다)."""
    js_text = (ENGINE_DIR / "correspondence.js").read_text(encoding="utf-8")
    build_corr_body = js_text.split("function buildCorrespondence")[1].split("\nmodule.exports")[0]
    return [
        ("buildCorrespondence()에 문자열 템플릿 삽입 문법(백틱 템플릿 리터럴)이 없음",
         "`" not in build_corr_body),
        ("twelve_stage_meanings는 {name, meaning} 데이터 배열 조립만 함(문장 삽입 아님)",
         "twelve_stage_meanings: [...usedStages].map" in build_corr_body),
    ]


def testCOMPUTED9_all_committed_tier_fixtures_satisfy_contract():
    """COMPUTED9 — 프로젝트에 실제로 커밋된 모든 tier fixture(mini/light/single/dual/
    master + behavior/gunghap/synastry 변형)가 핵심 계약을 만족하는지 확인.

    참고(회귀 테스트에는 포함하지 않음): premium tier는 프로젝트에 커밋된
    sample-intake-premium.json/out-premium.json 자체가 없다(2026-09-03 확인,
    run-all.js의 cases 배열에도 premium 없음 — 기존에 이미 확인된 별도의 E2E 커버리지
    공백, 이번 STEP 범위 밖). 세션 임시 fixture로 premium computed도 이 계약을
    만족함을 수동으로 확인했으나, scratchpad 경로는 영구 회귀 테스트에 쓰지 않는다."""
    fixtures = [
        "out-mini.json", "out-light.json", "out-single.json", "out-dual.json",
        "out-master.json", "out-behavior.json", "out-gunghap.json", "out-synastry.json",
    ]
    results = []
    for name in fixtures:
        try:
            computed = _real_computed_fixture(name)
            br.enforce_computed_core_contract(computed)
            ok = True
        except br.ComputedContractError as e:
            ok = False
        except FileNotFoundError:
            ok = None
        results.append((f"{name}: 핵심 계약 만족", ok is True))
    return results


def testRT_invariant1_any_unresolved_forces_complete_false():
    """불변조건 1 — Detection issue가 하나라도 resolved가 아니면 complete=False."""
    detection = {"status": "ISSUES_FOUND", "issues": [{"category": 1}, {"category": 1}, {"category": 1}]}
    results = [{"accepted": True}, {"accepted": True}, {"accepted": False, "stage": "groundedness"}]
    return [("불변조건1 확인", br.is_naturalness_pass_complete(detection, results) is False)]


def testRT_invariant2_detection_incomplete_forces_complete_false():
    """불변조건 2 — Detection이 INCOMPLETE이면 complete=False."""
    detection = {"status": "INCOMPLETE", "issues": []}
    return [("불변조건2 확인", br.is_naturalness_pass_complete(detection, []) is False)]


def main():
    any_fail = False
    cases = [
        ("Test 1 — 정상 category5 issue -> 정확한 path", test1_valid_category5_path),
        ("Test 2 — 존재하지 않는 section/index -> 실패", test2_invalid_section_index),
        ("Test 3 — 문자열 아닌 field -> 차단", test3_non_string_field_blocked),
        ("Test 4 — rewrite 결과 타입 오류 -> rollback", test4_rewrite_wrong_type_rollback),
        ("Test 5 — 실패해도 재호출 안 함(1회 제한)", test5_no_retry_on_same_issue),
        ("Test 6 — category9 computed key 탐지", test6_category9_detection),
        ("Test 7 — issue 없는 정상 report -> 무변경", test7_no_issues_no_changes),
        ("Test 8 — quoted_sentence 불일치 -> 폐기", test8_quoted_sentence_mismatch_discarded),
        ("Test 9 — 정상 rewrite -> 대상 필드만 변경", test9_successful_rewrite_only_changes_target_field),
        ("Test 10 — groundedness 실패 -> rollback", test10_groundedness_failure_rollback),
        ("Test 11 — verify_naturalness 정상 완료+issues 있음 -> ISSUES_FOUND", test11_verify_naturalness_issues_found),
        ("Test 12 — verify_naturalness 정상 완료+issues 없음 -> PASS", test12_verify_naturalness_pass_when_complete_and_empty),
        ("Test 13 — [핵심 게이트] max_tokens 잘림 -> 절대 PASS 아님(INCOMPLETE)", test13_verify_naturalness_max_tokens_never_pass),
        ("Test 14 — tool input 불완전(issues 키 없음) -> INCOMPLETE", test14_verify_naturalness_incomplete_tool_input),
        ("Test 15 — tool_use 블록 없음 -> ERROR", test15_verify_naturalness_no_tool_use_block),
        ("Test 16 — issues가 배열 아님 -> ERROR", test16_verify_naturalness_issues_not_a_list),
        ("Test A — 마크다운 없는 동일 문장 -> PASS", testA_markdown_free_identical_sentence),
        ("Test B — ** 제거된 인용 -> PASS", testB_markdown_stripped_by_llm),
        ("Test B2 — 문장 중간 ** 누락(실제 파일럿 재현) -> PASS", testB2_markdown_mid_sentence_stripped),
        ("Test C — 문장 내용 변경 -> FAIL(여전히 거부)", testC_content_changed_still_fails),
        ("Test D — 단어 추가 -> FAIL(여전히 거부)", testD_word_inserted_still_fails),
        ("Test E — 존재하지 않는 문장 -> FAIL(여전히 거부)", testE_nonexistent_sentence_still_fails),
        ("Test F — 한글 조사 결합(카테고리9, 기존 유지 확인)", test6_category9_detection),
        ("Test G1 — field_groundedness call_purpose 등록 확인", testG1_field_groundedness_call_purpose_registered),
        ("Test G2 — 기존 CALL_PURPOSES 미영향 확인", testG2_existing_call_purposes_unaffected),
        ("Test G3 — groundedness PASS -> ACCEPT", testG3_groundedness_pass_accepts_rewrite),
        ("Test G4 — groundedness FAIL -> ROLLBACK", testG4_groundedness_fail_rolls_back),
        ("Test G5 — FAIL이어도 new_value 보존", testG5_new_value_preserved_on_failure),
        ("Test G6 — rollback 후 대상 field 원본과 동일", testG6_rollback_target_field_matches_original),
        ("Test G7 — rollback 후 다른 field 전부 동일", testG7_rollback_other_fields_untouched),
        ("Test G8 — 필드당 rewrite 여전히 최대 1회", testG8_max_one_rewrite_per_field_still_holds),
        ("Test H1 — 정상 rewrite -> Format Integrity PASS -> ACCEPT", testH1_clean_rewrite_passes_and_accepted),
        ("Test H2 — </invoke> 포함 -> FAIL -> ROLLBACK", testH2_invoke_close_tag_rejected),
        ("Test H3 — <invoke> 포함 -> FAIL -> ROLLBACK", testH3_invoke_open_tag_rejected),
        ("Test H4 — <new_value>/</new_value> 포함 -> FAIL -> ROLLBACK", testH4_new_value_tags_rejected),
        ("Test H5 — 복합 protocol residue -> FAIL -> ROLLBACK", testH5_multiple_residues_rejected),
        ("Test H6 — 정상 Markdown 강조 -> PASS(오탐 없음)", testH6_normal_markdown_passes),
        ("Test H7 — 한국어 조사 결합 -> PASS(오탐 없음)", testH7_korean_particle_attached_passes),
        ("Test H8 — FAIL이어도 다른 field 불변", testH8_format_integrity_failure_other_fields_untouched),
        ("Test H9 — FAIL이어도 new_value/matched_pattern 보존", testH9_new_value_preserved_on_format_integrity_failure),
        ("Test H10 — 필드당 rewrite 여전히 최대 1회", testH10_still_max_one_rewrite_per_field),
        ("Test I — 다른 문단의 groundedness 문제가 target을 막지 않음", testI_other_paragraph_groundedness_issue_does_not_block_target),
        ("Test J — target 문단 자체 오류 -> ROLLBACK", testJ_target_paragraph_new_error_rolls_back),
        ("Test K — ACCEPT 후 다른 문단 byte 단위 동일", testK_non_target_paragraphs_byte_identical_after_accept),
        ("Test L — 문단 내 재배열 ACCEPT, 다른 문단 무변경", testL_within_paragraph_sentence_reorder_accepted_and_isolated),
        ("Test M — quoted_sentence가 구(句)여도 문단 전체가 단위", testM_quoted_sentence_is_phrase_within_paragraph_targets_whole_paragraph),
        ("Test N — 마크다운 차이에도 문단 매칭 성공", testN_markdown_difference_still_matches_paragraph),
        ("Test O — 동일 문장 2개 문단 존재 -> AMBIGUOUS", testO_duplicate_sentence_in_two_paragraphs_is_ambiguous),
        ("Test P — scope는 target 문단 기준으로만 판정", testP_rewrite_exceeds_scope_relative_to_paragraph_only),
        ("Test Q — 결과에 새 빈 줄 포함 -> paragraph_structure FAIL", testQ_new_paragraph_contains_blank_line_rejected),
        ("Test R — 문단 단위에서도 tool/XML residue 차단", testR_tool_protocol_residue_in_paragraph_rejected),
        ("Test S — groundedness 프롬프트가 target 문단만 포함(강한 증명)", testS_groundedness_prompt_contains_only_target_paragraph),
        ("Test T — splice 결과가 rewrite 출력과 byte 단위 동일", testT_spliced_paragraph_matches_rewrite_output_exactly),
        ("Test GP1 — groundedness prompt에 gan/zhi 의미 설명 존재", testGP1_prompt_explains_gan_zhi_meaning),
        ("Test GP2 — 실제 out-light.json 값이 가공 없이 prompt에 그대로 존재", testGP2_real_out_light_computed_appears_unfiltered),
        ("Test GP3 — 부분 언급 허용 vs 유일값 단정 차단 동시 명시", testGP3_partial_mention_vs_unique_value_distinction_present),
        ("Test GP4 — prompt 수정 후에도 paragraph isolation 유지", testGP4_paragraph_isolation_unaffected_by_prompt_change),
        ("Test RT1 — issue 0개 -> complete True", testRT1_zero_issues_complete_true),
        ("Test RT2 — issue 1개 resolved -> complete True", testRT2_single_issue_resolved_complete_true),
        ("Test RT3 — 여러 issue 전부 resolved -> complete True", testRT3_multiple_issues_all_resolved),
        ("Test RT4 — 일부만 resolved -> complete False", testRT4_partial_resolution_complete_false),
        ("Test RT5 — rewrite failure가 orchestration에서도 기록됨", testRT5_rewrite_type_failure_via_pass),
        ("Test RT6 — groundedness failure가 orchestration에서도 기록됨", testRT6_groundedness_failure_via_pass),
        ("Test RT7 — format failure가 orchestration에서도 기록됨", testRT7_format_failure_via_pass),
        ("Test RT8 — ROLLBACK은 report를 절대 변경하지 않음", testRT8_rollback_never_mutates_report_via_pass),
        ("Test RT9 — 예외가 배치 전체를 죽이지 않음", testRT9_exception_does_not_kill_batch),
        ("Test RT10 — Detection INCOMPLETE -> complete False", testRT10_detection_incomplete_complete_false),
        ("Test RT11 — results 길이 불일치(issue 누락) 감지", testRT11_length_mismatch_detected),
        ("Test RT12 — duplicate issue도 각각 별도 추적", testRT12_duplicate_issue_entries_each_tracked_separately),
        ("Test RT13 — 동일 paragraph의 서로 다른 두 issue", testRT13_two_distinct_issues_same_paragraph),
        ("Test RT14 — 다른 paragraph의 issue는 영향받지 않음(대조군)", testRT14_earlier_rewrite_does_not_affect_unrelated_paragraph_issue),
        ("Test RT15 — 전부 resolved일 때만 complete True", testRT15_complete_true_only_when_all_resolved),
        ("Test RT16 — out_of_scope_category도 결과에서 사라지지 않음", testRT16_out_of_scope_category_recorded_not_silently_dropped),
        ("Test RT17 — skipped_cap도 결과에서 사라지지 않음", testRT17_skipped_cap_recorded_not_silently_dropped),
        ("Test RT18 — stale 표시는 실제로 그런 경우에만 붙음(오탐 방지)", testRT18_stale_flag_not_set_for_genuinely_nonexistent_quote),
        ("Test RT19 — needs_key=True(new_reference_systems)도 orchestration에서 안전", testRT19_key_based_path_new_reference_systems_in_pass),
        ("Test CAT — category 2/3/4/8도 전체 파이프라인 통과", testCAT_all_non9_categories_flow_through_full_pipeline),
        ("Test CAT — target_categories 기본값이 1~8 포함/9 제외", testCAT_target_categories_now_includes_2_3_4_8_by_default),
        ("Test CAT — category 9는 여전히 out_of_scope_category", testCAT_category9_still_out_of_scope_via_pass),
        ("Test MAIN1 — main() 배선 순서 end-to-end(mock)", testMAIN1_wiring_sequence_matches_main_and_never_blocks),
        ("Test MAIN2 — INCOMPLETE/unresolved여도 예외로 리포트 저장을 막지 않음", testMAIN2_wiring_never_raises_when_incomplete_or_unresolved),
        ("Test MODEL1 — verify 계열 실제 코드 경로가 sonnet-5 사용", testMODEL1_verify_functions_use_sonnet5_via_real_code_path),
        ("Test MODEL2 — generation/rewrite가 MODEL 상수(sonnet-5) 사용", testMODEL2_generation_and_rewrite_reference_model_constant),
        ("Test MODEL3 — quality_rubric judge가 sonnet-5 상속", testMODEL3_quality_rubric_judge_inherits_sonnet5),
        ("Test COMPUTED1 — 정상 computed 통과", testCOMPUTED1_valid_computed_passes),
        ("Test COMPUTED2 — pillars 누락 FAIL", testCOMPUTED2_missing_pillars_fails),
        ("Test COMPUTED3 — shensha 구조 오류 FAIL", testCOMPUTED3_broken_shensha_fails),
        ("Test COMPUTED4 — shi_shen_meanings 누락/타입오류 FAIL", testCOMPUTED4_missing_shi_shen_meanings_fails),
        ("Test COMPUTED5 — shi_shen_gan 단일값 구조 확인", testCOMPUTED5_shi_shen_gan_is_scalar),
        ("Test COMPUTED6 — shi_shen_zhi 다중값 리스트 구조 확인", testCOMPUTED6_shi_shen_zhi_is_list),
        ("Test COMPUTED7 — optional system 부재는 FAIL 아님", testCOMPUTED7_optional_systems_absent_does_not_fail),
        ("Test COMPUTED8 — 12운성 JS/Python diff 문서화(재검증 강화)", testCOMPUTED8_twelve_stage_meanings_js_python_divergence_documented),
        ("Test COMPUTED10 — 12운성 JS 포맷이 실제 프로덕션 문장을 깨뜨림(재현)", testCOMPUTED10_twelve_stage_js_format_breaks_real_production_usage),
        ("Test COMPUTED11 — JS에는 문장 삽입 지점 자체가 없음(반대 방향 확인)", testCOMPUTED11_js_has_no_sentence_insertion_mechanism),
        ("Test COMPUTED9 — 실제 커밋된 tier fixture 전수 계약 검증", testCOMPUTED9_all_committed_tier_fixtures_satisfy_contract),
        ("불변조건1 — 하나라도 unresolved면 complete False", testRT_invariant1_any_unresolved_forces_complete_false),
        ("불변조건2 — Detection INCOMPLETE면 complete False", testRT_invariant2_detection_incomplete_forces_complete_false),
    ]
    for title, fn in cases:
        print("=" * 100)
        print(title)
        print("=" * 100)
        for label, ok in fn():
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
