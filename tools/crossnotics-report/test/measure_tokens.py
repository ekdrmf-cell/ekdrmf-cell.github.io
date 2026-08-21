"""
실제 토큰 사용량 근사 측정 스크립트.

중요한 한계(반드시 사용자에게 고지할 것): Anthropic(클로드)의 정확한 토큰 계산기는
API 키로 인증해야 하는 온라인 기능뿐이라, 여기서는 OpenAI의 공개 토크나이저(tiktoken,
cl100k_base)를 "근사치 대용"으로 쓴다. 클로드 자체 토크나이저와 완전히 같지 않고,
특히 한국어는 토크나이저마다 나뉘는 방식이 달라 오차가 있을 수 있다 — 이건 "실측값"이
아니라 "실제 프롬프트/데이터 분량을 기반으로 한 훨씬 근거 있는 근사치"다.
"""
import json
import sys
from pathlib import Path

import tiktoken

HERE = Path(__file__).resolve().parent
REPORT_DIR = HERE.parent
ENGINE_DIR = REPORT_DIR.parent / "crossnotics-engine"

sys.path.insert(0, str(REPORT_DIR))
import build_report  # noqa: E402

enc = tiktoken.get_encoding("cl100k_base")


def count(text):
    return len(enc.encode(text)), len(text)


sys_tok, sys_char = count(build_report.SYSTEM_PROMPT)
print(f"시스템 프롬프트(고정): {sys_char}자 -> 약 {sys_tok} 토큰")

schema_text = json.dumps(build_report.REPORT_SCHEMA, ensure_ascii=False)
schema_tok, schema_char = count(schema_text)
print(f"도구 스키마 정의(고정): {schema_char}자 -> 약 {schema_tok} 토큰")

computed_master = json.loads((ENGINE_DIR / "test/out-master.json").read_text(encoding="utf-8"))
cm_text = json.dumps(computed_master, ensure_ascii=False, indent=2)
cm_tok, cm_char = count(cm_text)
print(f"입력 데이터(마스터 티어 computed.json): {cm_char}자 -> 약 {cm_tok} 토큰")

computed_single = json.loads((ENGINE_DIR / "test/out-single.json").read_text(encoding="utf-8"))
cs_text = json.dumps(computed_single, ensure_ascii=False, indent=2)
cs_tok, cs_char = count(cs_text)
print(f"입력 데이터(싱글 티어 computed.json): {cs_char}자 -> 약 {cs_tok} 토큰")

mock_master = (HERE / "mock-report-master.json").read_text(encoding="utf-8")
mm_tok, mm_char = count(mock_master)
print(f"출력 참고치(목업 마스터 리포트, 실제 LLM 응답 아님): {mm_char}자 -> 약 {mm_tok} 토큰")

mock_single = (HERE / "mock-report-single.json").read_text(encoding="utf-8")
ms_tok, ms_char = count(mock_single)
print(f"출력 참고치(목업 싱글 리포트, 실제 LLM 응답 아님): {ms_char}자 -> 약 {ms_tok} 토큰")

print()
print("=== 합산 ===")
fixed_input = sys_tok + schema_tok
print(f"고정 입력(시스템프롬프트+도구스키마): 약 {fixed_input} 토큰 (모든 주문에 동일하게 들어감)")
master_in = fixed_input + cm_tok
single_in = fixed_input + cs_tok
print(f"마스터 티어 총 입력: 약 {master_in} 토큰")
print(f"싱글 티어 총 입력: 약 {single_in} 토큰")

print()
print("=== 비용 계산 (Sonnet 5, 2026-08-31까지 적용 단가: 입력 $2/MTok, 출력 $10/MTok) ===")
USD_KRW = 1400
in_price, out_price = 2.0, 10.0
for label, in_tok, out_tok in [("싱글", single_in, ms_tok), ("마스터", master_in, mm_tok)]:
    cost_usd = (in_tok * in_price + out_tok * out_price) / 1_000_000
    cost_krw = cost_usd * USD_KRW
    print(f"{label} 티어: 입력 {in_tok}토큰 + 출력 {out_tok}토큰 -> ${cost_usd:.5f} (약 {cost_krw:.1f}원, 환율 {USD_KRW}원/$ 가정)")

print()
print("=== 비용 계산 (Sonnet 5, 2026-09-01부터 표준 단가: 입력 $3/MTok, 출력 $15/MTok) ===")
in_price, out_price = 3.0, 15.0
for label, in_tok, out_tok in [("싱글", single_in, ms_tok), ("마스터", master_in, mm_tok)]:
    cost_usd = (in_tok * in_price + out_tok * out_price) / 1_000_000
    cost_krw = cost_usd * USD_KRW
    print(f"{label} 티어: 입력 {in_tok}토큰 + 출력 {out_tok}토큰 -> ${cost_usd:.5f} (약 {cost_krw:.1f}원, 환율 {USD_KRW}원/$ 가정)")
