"""용어 뜻풀이 GLOSSARY VALIDATOR 회귀 테스트 — 무료(실제 LLM 호출 없음).

Claude_Code_Memory_to_Validator_Enforcement_Protocol.txt 11번 항목이 요구하는 정확히 그
시나리오를 고정 회귀 테스트로 승격한다:

    TERM = 화개살
    최초 등장:   화개살(뜻풀이)              → PASS(뜻풀이가 실제로 붙어야 함)
    두 번째 등장: 화개살만(뜻풀이 반복 없음)   → PASS(반복되면 FAIL)
    세 번째 등장: 화개살만(뜻풀이 반복 없음)   → PASS(반복되면 FAIL)

"용어가 등장할 때마다 매번 괄호가 있어야 한다"는 예전 설계가 아니라 "챕터 묶음별로
최초 1회만 풀어쓰고 그 뒤로는 반복 안 한다"는 2026-08-30 설계를 검증 대상으로 삼는다
(build_report.apply_term_glosses_by_group 참고). shensha.js의 실제 화개살 정의를
build_term_gloss_map()으로 가져와 쓰므로, 엔진 쪽 정의 텍스트가 바뀌어도(오늘 있었던
"용어(뜻풀이)"→"뜻풀이(용어)" 형식 전환처럼) 이 테스트가 그 변화를 실제로 반영해서
검증한다 — 하드코딩된 가짜 gloss_map을 쓰지 않는다.

사용법:
    cd tools/crossnotics-report
    python test/glossary_validator_regression.py
"""
import io
import contextlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPORT_TOOL_DIR = HERE.parent
sys.path.insert(0, str(REPORT_TOOL_DIR))

import build_report as br  # noqa: E402

RESULTS = []


def check(name, condition, detail=""):
    RESULTS.append((name, bool(condition), detail))
    mark = "✓ PASS" if condition else "✗ FAIL"
    print(f"{mark}  {name}")
    if not condition and detail:
        print(f"       {detail}")


def _fresh_computed():
    """shensha.js의 실제 화개살 정의를 담은 최소 computed.json. run.js 전체를 안 돌리고
    (무료) 이 필드 하나만 직접 채워 shensha 엔진 로직과 동일한 모양을 만든다."""
    return {
        "saju": {
            "shensha": {
                "hwagae": {"present": True, "meaning": _real_hwagae_meaning()},
            },
            "correspondence": {"shi_shen_meanings": []},
        }
    }


def _real_hwagae_meaning():
    """shensha.js가 실제로 계산하는 화개살 뜻풀이 값을 node로 직접 읽어온다(하드코딩
    금지 — 엔진 정의가 바뀌면 이 테스트도 그 변화를 그대로 반영해야 하므로).

    2026-08-30 — 처음엔 `require('./shensha.js').SHENSHA_MEANING`을 직접 읽으려 했는데
    "TypeError: Cannot read properties of undefined" 로 실패했다. 처음엔 이걸 윈도우
    콘솔 코드페이지가 한글을 깨뜨리는 인코딩 문제로 오판할 뻔했다(에러 메시지 자체가
    터미널에서 깨져 보였음) — 실제로는 인코딩과 무관하게, shensha.js가 SHENSHA_MEANING을
    애초에 module.exports로 내보내지 않는다는 게 진짜 원인이었다(export 목록:
    computeShensha/TAOHUA_BY_SAMHAP/YEOKMA_BY_SAMHAP/HWAGAE_BY_SAMHAP/HONGYEOM_BY_GAN 뿐).
    그래서 private 딕셔너리를 직접 뜯어보는 대신, 실제 프로덕션과 똑같은 경로(saju.js의
    computeSaju() → 그 결과를 shensha.js의 computeShensha()에 넣기)로 값을 얻는다 —
    build_term_gloss_map()이 실제로 읽는 saju.shensha.hwagae.meaning과 완전히 같은 값."""
    import subprocess
    import tempfile
    engine_dir = REPORT_TOOL_DIR.parent / "crossnotics-engine"
    script = (
        "const { computeSaju } = require('./saju.js');\n"
        "const { computeShensha } = require('./shensha.js');\n"
        "const saju = computeSaju({ year: 1988, month: 10, day: 6, hour: 10, minute: 0, unknownTime: false, calendarType: 'solar', isLeapMonth: false });\n"
        "const shensha = computeShensha(saju);\n"
        "console.log(JSON.stringify(shensha.hwagae.meaning));\n"
    )
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".js", delete=False, dir=str(engine_dir), encoding="utf-8"
    ) as f:
        f.write(script)
        tmp_path = f.name
    try:
        out = subprocess.run(
            ["node", tmp_path],
            cwd=str(engine_dir), capture_output=True, text=True, encoding="utf-8",
        )
    finally:
        Path(tmp_path).unlink(missing_ok=True)
    if out.returncode != 0:
        raise RuntimeError(f"shensha 계산 실패: {out.stderr}")
    return json.loads(out.stdout.strip())


def test_single_group_no_repeat():
    """같은 묶음(system_sections) 안에서 화개살이 세 번 나오면: 1회만 풀어쓰고 2ㆍ3회는
    라벨만 남아야 한다."""
    computed = _fresh_computed()
    gloss_map = br.build_term_gloss_map(computed)
    gloss_text = gloss_map["화개살"]

    report = {
        "system_sections": [
            {"system": "saju", "body": "이 사람은 {{화개살}}이 있습니다."},
            {"system": "saju2", "body": "화개살이 또 등장합니다."},
            {"system": "saju3", "body": "화개살이 세 번째로 나옵니다."},
        ]
    }
    unmapped = []
    br.apply_term_glosses_by_group(report, gloss_map, unmapped)

    b1 = report["system_sections"][0]["body"]
    b2 = report["system_sections"][1]["body"]
    b3 = report["system_sections"][2]["body"]

    check("최초 등장 — 뜻풀이가 실제로 붙음", f"{gloss_text}(화개살)" in b1, b1)
    check("두 번째 등장 — 뜻풀이 반복 없이 라벨만", b2 == "화개살이 또 등장합니다." and gloss_text not in b2, b2)
    check("세 번째 등장 — 뜻풀이 반복 없이 라벨만", b3 == "화개살이 세 번째로 나옵니다." and gloss_text not in b3, b3)


def test_cross_group_reexplains_once_each():
    """다른 챕터 묶음(system_sections 대 question_answers)으로 넘어가면, 그 묶음에서는
    처음 보는 것처럼 다시 한 번 풀어써야 한다(2026-08-30 설계 — 47페이지 전체를 한
    번으로 묶으면 뒤쪽에서 설명이 영영 안 나오는 결함이 생긴다는 걸 재검토 후 반영)."""
    computed = _fresh_computed()
    gloss_map = br.build_term_gloss_map(computed)
    gloss_text = gloss_map["화개살"]

    report = {
        "system_sections": [{"system": "saju", "body": "이 사람은 {{화개살}}이 있습니다."}],
        "question_answers": [{"question": "Q", "answerability": "direct", "body": "화개살이 궁금합니다."}],
    }
    unmapped = []
    br.apply_term_glosses_by_group(report, gloss_map, unmapped)

    a = report["system_sections"][0]["body"]
    c = report["question_answers"][0]["body"]
    check("그룹A(system_sections) — 뜻풀이 붙음", f"{gloss_text}(화개살)" in a, a)
    check("그룹C(question_answers) — 별도 묶음이라 여기서도 다시 뜻풀이 붙음", f"{gloss_text}(화개살)" in c, c)


def test_check_term_glosses_validator():
    """check_term_glosses()가 이 설계를 정확히 판정하는지: 최소 한 번 풀어썼으면 PASS,
    한 번도 안 풀어썼으면 FAIL."""
    computed = _fresh_computed()
    gloss_map = br.build_term_gloss_map(computed)

    good_report = {
        "system_sections": [
            {"system": "saju", "body": "이 사람은 {{화개살}}이 있습니다."},
            {"system": "saju2", "body": "화개살이 또 등장합니다."},
        ]
    }
    br.apply_term_glosses_by_group(good_report, gloss_map, [])
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        br.check_term_glosses(good_report)
    check("정상 케이스 — validator PASS", "✓" in buf.getvalue(), buf.getvalue())

    bad_report = {"system_sections": [{"system": "saju", "body": "화개살이 뜻풀이 없이 그냥 나옵니다."}]}
    buf2 = io.StringIO()
    with contextlib.redirect_stdout(buf2):
        br.check_term_glosses(bad_report)
    check("누락 케이스 — validator FAIL(경고)", "⚠" in buf2.getvalue() and "화개살" in buf2.getvalue(), buf2.getvalue())


def main():
    test_single_group_no_repeat()
    test_cross_group_reexplains_once_each()
    test_check_term_glosses_validator()

    print(f"\n{'=' * 60}")
    passed = sum(1 for _, ok, _ in RESULTS if ok)
    total = len(RESULTS)
    print(f"{passed}/{total} 통과")
    if passed < total:
        sys.exit(1)


if __name__ == "__main__":
    main()
