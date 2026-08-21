# 크로스노틱스 합성 프롬프트 — 설계 문서

이 파일은 `build_report.py`가 시스템 프롬프트를 만들 때 참고하는 **고정 규칙 원본**이다.
실제 시스템 프롬프트 문자열은 `build_report.py`의 `SYSTEM_PROMPT` 상수에 있음 — 이 문서는
그 문구 뒤에 있는 설계 근거를 남겨서, 나중에 프롬프트를 고칠 때 왜 이렇게 짰는지 잊지 않기
위한 것.

## 왜 이렇게 설계했나 (계획서 4번 "LLM 합성 단계 설계" 근거)

**LLM에게 "체계 간 어디서 일치하는지 찾아봐"라고 시키지 않는다.** `tools/crossnotics-engine/
correlate.js`가 이미 결정론적으로 계산해서 `computed.json`에 넣어준 `correlation` 필드
(dominant_axis, agreement_score, systems_agreeing, complementary_points)를 LLM에게 **사실로
그대로 주고, 그 결과를 컨설팅 언어로 번역하는 것만** LLM의 일로 제한한다. 이게 백서의 "LLM은
지어내는 게 아니라 번역만 한다"는 원칙을 코드 구조로 강제하는 방법이다 — 프롬프트로 "지어내지
마세요"라고 부탁하는 것보다,애초에 LLM이 손댈 수 없는 숫자는 안 주고 이미 계산된 결과만 주는
쪽이 훨씬 안전하다.

## 입력 데이터 (computed.json 전체를 그대로 프롬프트에 넣음)

- `customer`: 이름, 생년월일시, 질문(고객이 직접 입력한 궁금한 점)
- `tier`: single | dual | master
- `saju` / `astrology` / `tarot`: 각 엔진이 계산한 원본 데이터(선택된 체계만 존재)
- `correlation`: 교차상관 알고리즘 결과 — mode가 "single_system"이면 교차분석 없음,
  "cross_correlation"이면 dominant_axis/agreement_score/complementary_points 등 존재

## 출력 JSON 스키마 (LLM이 반드시 이 형식으로만 응답)

```json
{
  "intro": "리포트 도입부 — 이 진단이 무엇을 다루는지, 고객의 질문에 대한 짧은 인사",
  "system_sections": [
    { "system": "saju", "heading": "...", "body": "..." }
  ],
  "cross_analysis": { "heading": "...", "body": "..." } 또는 mode가 single_system이면 null,
  "closing": "마무리 — 다음 단계 제안(상위 티어 업셀은 자연스럽게, 강매 톤 금지)",
  "disclaimer": "정보 제공 목적 명시, 확정적 예언 아님, 중요한 결정은 전문가 상담 권장"
}
```

## 고정 규칙 (SYSTEM_PROMPT에 그대로 들어감)

1. `computed.json`에 없는 간지ㆍ별자리ㆍ카드명ㆍ수치ㆍ날짜는 절대 지어내지 않는다.
2. 모든 주장은 입력 데이터의 특정 필드에서 근거를 추적할 수 있어야 한다 — "화 기운이 강하고
   태양이 황소자리에 있으며..." 식으로 실제 계산값을 문장 안에 직접 인용한다.
3. `cross_analysis`는 `correlation` 필드가 이미 계산한 dominant_axis/systems_agreeing/
   complementary_points를 문장으로 번역하는 것만 한다 — LLM이 스스로 다른 일치점을 찾아내려
   하지 않는다.
4. 확정적 예언("반드시 ~할 것이다"), 의료ㆍ법률ㆍ재무 전문가 자문처럼 읽히는 표현 금지 —
   "정보 제공" 톤 유지(전자책 13종과 동일 원칙).
5. 티어별 분량: single은 system_sections 1개로 충분히 깊게, dual/master는 여러 체계를
   균형 있게 다루되 cross_analysis가 리포트의 핵심이 되도록 강조.
6. 업셀은 자연스럽게(예: "다른 체계와 교차하면 더 정확해집니다") — 강매 톤 금지, 하위 티어도
   그 자체로 완결된 답을 주는 게 우선(백서 1번 원칙).

## 환각 방지 후처리 (build_report.py의 `check_hallucination()`)

LLM 응답에서 간지ㆍ별자리ㆍ카드명ㆍ원소명 등 핵심 용어를 정규식으로 추출해 `computed.json`
안에 실제로 존재하는 값인지 대조한다. 못 찾은 용어가 있으면 콘솔에 경고를 남기고(발송을 막지는
않음 — 한국어 표현이 다양해서 오탐이 있을 수 있음), 발송 전 사람이 한 번 훑어보라는 신호로 쓴다.
