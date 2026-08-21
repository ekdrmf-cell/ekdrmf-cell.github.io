"""
크로스노틱스 리포트 생성 — 2단계(Python): computed.json을 읽어 Anthropic API로
합성 문장만 생성하고, report_kit.py(pdf_kit.py 확장)로 PDF를 만든다.

사용법: python build_report.py <computed.json> [출력 PDF 경로]

설계 근거는 prompts/synthesis_prompt.md 참고. 여기서는 그 설계를 실제로 구현한다 —
LLM에게 "어디서 체계가 일치하는지 찾아봐"라고 시키지 않고, correlate.js가 이미 계산한
correlation 필드를 문장으로 번역하는 것만 시킨다(강제 tool-call로 JSON 스키마를 지키게 해서
자유 텍스트 파싱보다 안전하게 만듦).

필요 환경변수: ANTHROPIC_API_KEY (Anthropic Console에서 발급 — 사용자 액션, 계획서 8번 참고).
같은 폴더의 .env 파일(절대 커밋 안 됨, .gitignore 등록됨)에 넣어두면 아래 load_dotenv()가
자동으로 읽어온다 — 매번 터미널에서 환경변수를 새로 설정할 필요 없음.
"""
import json
import os
import re
import sys
from pathlib import Path

import anthropic
from dotenv import load_dotenv

# Windows 콘솔 기본 인코딩(cp949)은 ✓ㆍ⚠ 같은 유니코드 기호를 못 담아 print()가 죽는다
# (실제로 여기서 첫 실행 때 API 호출은 성공했는데 이 로그 출력 단계에서 죽어서 파일 저장 전에
# 멈췄던 걸 확인함) — stdout을 UTF-8로 강제 전환해서 방지.
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv(Path(__file__).resolve().parent / ".env")

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "_shared"))  # products/_shared는 아님 — report_kit은 이 폴더에 있음

MODEL = os.environ.get("CROSSNOTICS_LLM_MODEL", "claude-sonnet-4-5-20250929")

SYSTEM_PROMPT = """당신은 크로스노틱스(사주ㆍ서양점성술ㆍ타로 통합 진단 서비스)의 리포트 작성
담당입니다. 아래 규칙을 반드시 지키세요.

1. 사용자가 제공하는 JSON(computed.json)에 없는 간지ㆍ별자리ㆍ카드명ㆍ수치ㆍ날짜는 절대
   지어내지 마세요. 당신이 아는 일반적인 사주/점성술/타로 지식으로 새 사실을 채우지 마세요 —
   오직 주어진 JSON에 있는 값만 문장으로 옮기세요.
2. 모든 주장은 JSON의 특정 필드에서 근거를 추적할 수 있어야 합니다. "화 기운이 강하고
   태양이 황소자리에 있으며..." 식으로 실제 계산값을 문장 안에 직접 인용하세요.
3. correlation 필드가 이미 계산한 dominant_axis/systems_agreeing/complementary_points를
   문장으로 번역하는 것만 하세요 — 당신이 스스로 다른 일치점을 찾아내려 하지 마세요.
   correlation.mode가 "single_system"이면 cross_analysis는 null로 두세요.
4. 확정적 예언("반드시 ~할 것이다")이나 의료ㆍ법률ㆍ재무 전문가 자문처럼 읽히는 표현을
   쓰지 마세요 — "정보 제공" 톤을 유지하세요.
5. tier가 "single"이면 system_sections 하나를 충분히 깊게, "dual"/"master"면 여러 체계를
   균형 있게 다루되 cross_analysis를 리포트의 핵심으로 삼으세요.
6. 업셀은 자연스럽게(예: "다른 체계와 교차하면 더 정확해집니다") 하되 강매 톤은 쓰지
   마세요 — 지금 이 리포트만으로도 완결된 답이어야 합니다.
7. 한자(漢字)나 그 외 한글이 아닌 문자를 절대 쓰지 마세요 — 예를 들어 "신금(辛金)"처럼
   괄호 안에 한자를 병기하지 마세요. PDF 폰트(Pretendard)가 한자 글리프를 지원하지 않아
   빈칸으로 깨집니다(실제로 확인된 버그). computed.json의 간지ㆍ오행ㆍ십신 값은 이미
   전부 한글로 번역되어 있으니("신", "겁재" 등) 그 한글 표기만 그대로 쓰세요.
8. **JSON에 있는 데이터를 절대 빠짐없이 전부 다루세요 — 요약하거나 일부만 골라 쓰지
   마세요.** 이건 분량을 늘리라는 뜻이 아니라, 이미 계산되어 주어진 실제 정보를 버리지
   말라는 뜻입니다:
   - 사주: 연ㆍ월ㆍ일ㆍ시주 네 기둥 전부(십신ㆍ지장간ㆍ12운성ㆍ공망 포함), 대운이 있다면
     제공된 대운 구간을 전부(현재 구간만이 아니라 처음부터 끝까지) 각각 짧게라도 언급.
   - 점성술: 제공된 행성 전부(태양부터 명왕성까지)와 그 사인ㆍ하우스, 제공된 어스펙트를
     전부(일부만 골라 쓰지 말고) 다루세요.
   - 타로: 뽑힌 카드를 전부(포지션 하나도 빠짐없이) 해석하세요.
   빠뜨린 데이터가 있으면 안 됩니다 — 이미 계산해서 드린 정보인데 리포트에 안 쓰면 고객이
   돈을 낸 값어치를 못 받는 것과 같습니다.
9. **고객이 questions 필드에 남긴 질문마다 각각 직접 답하는 전용 섹션(question_answer)을
   반드시 작성하세요.** questions는 티어에 따라 1개일 수도, 최대 10개일 수도 있습니다.
   질문이 여러 개면 뭉뚱그려 한 문단으로 답하지 말고, **질문마다 소제목(예: "Q1. OOO")을
   따로 붙여 각각 독립된 문단으로 답하세요.** 다른 섹션에서 슬쩍 언급하고 넘어가지 말고,
   각 질문과 가장 관련 있는 데이터(예: 이직운 질문이면 관련 대운 구간, 관련 하우스, 관련
   카드)를 다시 모아서 정면으로 답하세요. 서로 다른 질문에 거의 같은 문장을 복사한 것처럼
   답하지 마세요 — 질문마다 실제로 다른 데이터를 근거로 다르게 답해야 합니다.
   questions가 비어있으면 question_answer는 null로 두세요.
"""

REPORT_SCHEMA = {
    "name": "submit_report",
    "description": "완성된 크로스노틱스 리포트를 구조화된 형식으로 제출한다.",
    "input_schema": {
        "type": "object",
        "properties": {
            "intro": {"type": "string", "description": "리포트 도입부"},
            "system_sections": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "system": {"type": "string", "enum": ["saju", "astrology", "tarot"]},
                        "heading": {"type": "string"},
                        "body": {"type": "string"},
                    },
                    "required": ["system", "heading", "body"],
                },
            },
            "cross_analysis": {
                "type": ["object", "null"],
                "properties": {"heading": {"type": "string"}, "body": {"type": "string"}},
            },
            "question_answer": {
                "type": ["object", "null"],
                "description": "고객이 questions에 남긴 질문에 직접 답하는 전용 섹션. 질문이 없으면 null.",
                "properties": {"heading": {"type": "string"}, "body": {"type": "string"}},
            },
            "closing": {"type": "string"},
            "disclaimer": {"type": "string"},
        },
        "required": ["intro", "system_sections", "question_answer", "closing", "disclaimer"],
    },
}


def call_llm(computed):
    client = anthropic.Anthropic()  # ANTHROPIC_API_KEY 환경변수 자동 사용
    user_message = (
        "아래는 한 고객의 크로스노틱스 계산 결과(computed.json)입니다. 이 데이터만 근거로 "
        "리포트를 작성해 submit_report 도구로 제출하세요.\n\n"
        f"```json\n{json.dumps(computed, ensure_ascii=False, indent=2)}\n```"
    )
    # 2026-08-21: 8번ㆍ9번 규칙(모든 데이터 빠짐없이 다루기 + 질문답변 섹션) 추가로 응답
    # 길이가 늘어날 것으로 예상돼 4096->8192에 이어 16000으로 재상향.
    max_tokens = 16000
    response = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=SYSTEM_PROMPT,
        tools=[REPORT_SCHEMA],
        tool_choice={"type": "tool", "name": "submit_report"},
        messages=[{"role": "user", "content": user_message}],
    )
    # 그래도 잘릴 가능성에 대비해 명시적으로 검사 — 잘린 걸 모르고 그대로 발송하는 사고를 막는다.
    if response.stop_reason == "max_tokens":
        raise RuntimeError(
            f"LLM 응답이 max_tokens({max_tokens})에서 잘림 — 리포트가 불완전할 수 있음. "
            f"이대로 저장/발송하면 안 됨. max_tokens를 더 늘리거나 프롬프트를 손볼 것."
        )
    for block in response.content:
        if block.type == "tool_use" and block.name == "submit_report":
            report = block.input
            missing = [f for f in REPORT_SCHEMA["input_schema"]["required"] if f not in report]
            if missing:
                raise RuntimeError(f"LLM 응답에 필수 필드 누락: {missing} — 이대로 저장/발송하면 안 됨")
            return report, response.usage
    raise RuntimeError("LLM이 submit_report 도구를 호출하지 않음 — 응답 확인 필요")


def collect_known_terms(computed):
    """computed.json 안에 실제로 존재하는 용어(간지ㆍ별자리ㆍ카드명 등)를 전부 모은다."""
    terms = set()

    def walk(obj):
        if isinstance(obj, dict):
            for v in obj.values():
                walk(v)
        elif isinstance(obj, list):
            for v in obj:
                walk(v)
        elif isinstance(obj, str) and 1 < len(obj) <= 20:
            terms.add(obj)

    walk(computed)
    return terms


def check_hallucination(report, known_terms):
    """리포트 본문에서 핵심 용어를 뽑아 known_terms와 대조 — 발송을 막지는 않고 경고만 남긴다."""
    all_text = report.get("intro", "") + report.get("closing", "")
    for sec in report.get("system_sections", []):
        all_text += sec.get("body", "")
    if report.get("cross_analysis"):
        all_text += report["cross_analysis"].get("body", "")

    # 간지(2글자 한글, 예: "경오"), 별자리("~자리"로 끝남), 원소(단일 한글자+조사) 패턴만
    # 가볍게 검사 — 완벽한 NLP가 아니라 "발송 전 훑어볼 신호"로만 쓴다(설계 문서 참고).
    sign_candidates = re.findall(r"[가-힣]+자리", all_text)
    unknown = [s for s in set(sign_candidates) if s not in known_terms]
    if unknown:
        print(f"⚠ 경고: 리포트에 computed.json에 없는 별자리 표현이 있을 수 있음: {unknown}")
    else:
        print("✓ 별자리 용어 대조 통과(단순 패턴 검사, 완벽하지 않음 — 최종 발송 전 사람이 한 번 읽을 것)")


def main():
    if len(sys.argv) < 2:
        print("사용법: python build_report.py <computed.json> [출력 PDF 경로]")
        sys.exit(1)

    computed_path = Path(sys.argv[1])
    computed = json.loads(computed_path.read_text(encoding="utf-8"))

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY 환경변수가 없음 — Anthropic Console에서 API 키 발급 필요")
        print("(계획서 8번 '사용자가 직접 해야 하는 일' 참고, 에이전트가 대신 만들 수 없음)")
        sys.exit(1)

    print(f"LLM 호출 중... (모델: {MODEL})")
    report, usage = call_llm(computed)
    print(f"완료. 토큰 사용량: 입력 {usage.input_tokens} / 출력 {usage.output_tokens}")

    known_terms = collect_known_terms(computed)
    check_hallucination(report, known_terms)

    out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else computed_path.with_suffix(".report.json")
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"리포트 JSON 저장: {out_path}")
    print("(PDF 생성은 report_kit.py 완성 후 build_pdf_from_report()로 이어서 처리)")


if __name__ == "__main__":
    main()
