"""
API usage 계측 구조 — 2026-08-30 추가, API 비용 절감 3단계.

목적은 비용을 줄이는 게 아니라 "현재 API가 실제로 어디에서 얼마만큼 쓰이는가"를 정확히
측정할 수 있는 구조를 만드는 것이다(사용자 명시). 이 모듈은 기존 네트워크 호출 함수
(call_llm/verify_groundedness/verify_naturalness/_call_targeted_rewrite_llm)가 실제로
보내는 요청ㆍ받는 응답을 단 하나도 바꾸지 않고, 그 응답에 이미 실려오는 usage 메타데이터를
구조화해서 기록만 하는 관측 계층(observability layer)이다.

[전수 조사 결과 — network를 호출하는 함수와 usage 접근 가능 여부]
  call_llm()                    — client.messages.stream(), response.usage 이미 반환값에
                                   포함(build_report.py:1480), 이번에 로그 기록만 추가.
  verify_groundedness()         — client.messages.create(), resp.usage가 SDK 응답 객체에
                                   존재하지만 기존 코드는 resp.content만 읽고 resp.usage는
                                   한 번도 참조 안 함(grep 확인) — 이번에 캡처+기록 추가.
  verify_naturalness()          — 위와 동일 구조, 위와 동일 문제, 위와 동일 조치.
  _call_targeted_rewrite_llm()  — client.messages.stream(), response.usage 이미 반환값에
                                   포함(build_report.py:1568)이나 이 함수를 부르는
                                   apply_targeted_rewrite()가 그 usage를 반환 dict에만
                                   담을 뿐 어디에도 기록하지 않음 — 이번에 기록 추가.
  이 4개 외에 client.messages.create/stream을 호출하는 곳은 build_report.py 전체
  grep으로 재확인해도 없음(2026-08-30 기준).

[cache_creation_input_tokens / cache_read_input_tokens]
  build_report.py 전체에 cache_control/prompt_caching 관련 코드가 전혀 없음(grep 확인,
  0건) — 즉 이 프로젝트의 어떤 호출도 현재 프롬프트 캐싱을 쓰지 않는다. 따라서 이 두
  필드는 실제로 호출해도 항상 0(또는 SDK가 아예 안 채움)이어야 정상이고, 0이 아닌 값이
  기록되면 그 자체가 "프롬프트 캐싱이 의도치 않게 켜졌다"는 이상 신호로 볼 수 있다.

[thinking_tokens]
  Anthropic Messages API의 usage 객체에는 별도 "thinking_tokens" 필드가 없다 — thinking
  블록을 쓰면 그 내용이 output_tokens 총량 안에 포함되는 구조다. call_llm()은 항상
  thinking={"type":"disabled"}로 호출하므로(build_report.py 확인), 이 프로젝트에서는
  thinking이 usage에 별도로 잡힐 여지 자체가 없다 — 그래서 이 모듈은 별도 thinking_tokens
  필드를 만들지 않고 "thinking_disabled"라는 bool 플래그만 남긴다(호출부가 실제로 disabled를
  넘겼는지 자체 기록용, 값 자체를 추정하지 않음).
"""
import json
from datetime import datetime, timezone
from pathlib import Path

USAGE_LOG_PATH = Path(__file__).resolve().parent / "logs" / "api_usage_log.jsonl"

# 이 프로젝트가 실제로 쓰는 네트워크 호출 목적(그 외 추가되면 여기 갱신할 것).
# 2026-09-01 추가 — field_groundedness: targeted rewrite 폐쇄 루프의 축소판
# groundedness 검사(verify_field_groundedness, build_report.py) 전용. 실제 파일럿에서
# 이 값이 없어 정상 API 호출 뒤 로깅 단계에서 ValueError로 죽고, 그 예외가 "검증 실패"로
# 오인식되어 정상 재작성 2건이 콘텐츠와 무관하게 전부 rollback된 사고가 실제로 있었음.
CALL_PURPOSES = ("generation", "verify_groundedness", "verify_naturalness", "targeted_rewrite", "field_groundedness")


def extract_usage_fields(usage):
    """Anthropic SDK 응답의 usage 객체(response.usage / resp.usage)에서 표준 필드를 뽑는다.

    getattr 기본값을 쓰는 이유: 실제 SDK든 테스트용 mock이든 cache_* 필드가 아예 없는
    객체가 들어올 수 있어서(이 프로젝트는 캐싱을 안 쓰므로 실제로도 없을 수 있음), 없으면
    None이 아니라 0으로 명확히 채운다(캐싱을 안 썼다는 뜻이지 "측정 실패"가 아니므로).
    input_tokens/output_tokens는 반대로 없으면 None으로 남겨 "정말 못 잡았다"를 구분한다.
    """
    return {
        "input_tokens": getattr(usage, "input_tokens", None),
        "output_tokens": getattr(usage, "output_tokens", None),
        "cache_creation_input_tokens": getattr(usage, "cache_creation_input_tokens", 0) or 0,
        "cache_read_input_tokens": getattr(usage, "cache_read_input_tokens", 0) or 0,
    }


def build_usage_record(*, call_purpose, model, usage, tier=None, order_id=None,
                        thinking_disabled=None, source="ACTUAL_API_DATA"):
    """source는 반드시 'ACTUAL_API_DATA' 또는 'MOCK_TEST' 중 하나 — 실제 응답 기록과
    mock 테스트 기록이 같은 로그 파일에 섞여도 이 필드로 항상 구분할 수 있게 강제한다."""
    if call_purpose not in CALL_PURPOSES:
        raise ValueError(f"알 수 없는 call_purpose: {call_purpose!r} (허용: {CALL_PURPOSES})")
    if source not in ("ACTUAL_API_DATA", "MOCK_TEST"):
        raise ValueError(f"source는 'ACTUAL_API_DATA' 또는 'MOCK_TEST'여야 함(받은 값: {source!r})")
    fields = extract_usage_fields(usage)
    return {
        "logged_at": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "call_purpose": call_purpose,
        "model": model,
        "tier": tier,
        "order_id": order_id,
        "thinking_disabled": thinking_disabled,
        **fields,
    }


def log_usage_record(record, log_path=USAGE_LOG_PATH):
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


# ============================================================================
# 비용 계산 — 가격표는 코드에 하드코딩하지 않고 별도 config 파일(api_pricing_config.json)에서
# 읽는다. 확인 안 된 모델의 가격은 null로 남겨두고, 그 경우 계산 결과는 반드시 UNKNOWN으로
# 표시한다(추정해서 숫자를 만들지 않음 — 사용자 명시적 금지).
# ============================================================================

PRICING_CONFIG_PATH = Path(__file__).resolve().parent / "api_pricing_config.json"


def load_pricing_config(path=PRICING_CONFIG_PATH):
    return json.loads(path.read_text(encoding="utf-8"))


def compute_cost_for_record(record, pricing_config):
    """record 하나(build_usage_record 결과물 또는 그 형태의 dict)의 비용을 계산한다.

    반환: {"status": "OK", "usd": float} 또는 {"status": "UNKNOWN", "reason": str} —
    가격표에 없는 모델이거나 input_tokens/output_tokens가 기록 안 됐으면 절대 숫자를
    지어내지 않고 UNKNOWN을 반환한다.
    """
    model = record.get("model")
    model_price = pricing_config.get("models", {}).get(model)
    if not model_price:
        return {"status": "UNKNOWN", "reason": f"'{model}' 가격 정보가 config에 없음"}

    in_price = model_price.get("input_price_per_million_usd")
    out_price = model_price.get("output_price_per_million_usd")
    if in_price is None or out_price is None:
        return {"status": "UNKNOWN", "reason": f"'{model}' 가격이 null(미확인) — {model_price.get('source', '근거 없음')}"}

    in_tok = record.get("input_tokens")
    out_tok = record.get("output_tokens")
    if in_tok is None or out_tok is None:
        return {"status": "UNKNOWN", "reason": "input_tokens 또는 output_tokens가 기록되지 않음"}

    usd = in_tok / 1_000_000 * in_price + out_tok / 1_000_000 * out_price
    return {"status": "OK", "usd": round(usd, 6)}


def aggregate_costs(records, pricing_config):
    """여러 usage record를 call_purpose별/tier별로 집계한다.

    UNKNOWN인 record는 합계에서 조용히 빠뜨리지 않고 별도 리스트(unknown_records)로
    남긴다 — "총 비용"이 실제로는 일부만 반영된 부분합이라는 걸 항상 알 수 있게.
    """
    by_purpose = {}
    by_tier = {}
    unknown_records = []
    total_usd = 0.0
    known_count = 0

    for r in records:
        cost = compute_cost_for_record(r, pricing_config)
        if cost["status"] != "OK":
            unknown_records.append({**r, "unknown_reason": cost.get("reason")})
            continue
        usd = cost["usd"]
        total_usd += usd
        known_count += 1
        purpose = r.get("call_purpose", "unknown_purpose")
        tier = r.get("tier") or "unknown_tier"
        by_purpose[purpose] = by_purpose.get(purpose, 0.0) + usd
        by_tier[tier] = by_tier.get(tier, 0.0) + usd

    return {
        "total_usd_known_only": round(total_usd, 6),
        "known_record_count": known_count,
        "unknown_record_count": len(unknown_records),
        "by_purpose_usd": {k: round(v, 6) for k, v in by_purpose.items()},
        "by_tier_usd": {k: round(v, 6) for k, v in by_tier.items()},
        "unknown_records": unknown_records,
    }
