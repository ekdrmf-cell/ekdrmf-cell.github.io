"""
천지인운명관 주문 처리 프로그램 — 핵심 로직 (app.py가 이 모듈을 불러다 씀).

order_fulfillment_checklist.md의 3~7단계(intake.json 만들기 ~ 발송 전 검증)를
코드 한 곳에 모았다. 1단계(주문접수)ㆍ2단계(입금확인)ㆍ8단계(고객발송)ㆍ9단계(사후처리)는
사람이 판단할 부분이라 이 프로그램 밖에 남겨둔다(2026-08-23, 사용자 지시로 자동화
범위 확정).

가격 계산은 Sonnet 4.5($3/100만 입력토큰ㆍ$15/100만 출력토큰, claude-api 스킬로
2026-08-23 확인) 기준이며, 환율은 화면에 "약"으로만 표기하는 참고용 추정치다.
"""
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPORT_DIR = HERE.parent
ENGINE_DIR = REPORT_DIR.parent / "crossnotics-engine"
ORDERS_DIR = REPORT_DIR / "orders"

INPUT_PRICE_PER_M = 3.00
OUTPUT_PRICE_PER_M = 15.00
USD_KRW_APPROX = 1400  # 참고용 추정 환율일 뿐, 실제 결제 통화 아님

CHAPTER_COLORS = {
    "saju": "#e8562f", "astrology": "#6d4aff", "tarot": "#0a7d5e", "cross_analysis": "#a67c1e",
}


class PipelineError(Exception):
    pass


def load_tier_catalog():
    """tools/crossnotics-engine/catalog.js가 유일한 가격표 소스 — Python이 값을
    베껴 들고 있으면 나중에 가격이 바뀔 때 어긋날 수 있어서, node로 그 파일을 직접
    읽어 JSON으로 받는다."""
    proc = subprocess.run(
        ["node", "-e", "console.log(JSON.stringify(require('./catalog.js').CROSSNOTICS_TIERS))"],
        cwd=ENGINE_DIR, capture_output=True, text=True, encoding="utf-8",
    )
    if proc.returncode != 0:
        raise PipelineError(f"catalog.js 로드 실패: {proc.stderr}")
    raw = json.loads(proc.stdout)
    # tierKey(single/master/...) 기준으로 다시 인덱싱
    return {v["tier"]: v for v in raw.values()}


def extract_intake_json(raw_text):
    """이메일 원문(또는 intake.json 그 자체)에서 intake JSON을 뽑아낸다."""
    text = raw_text.strip()
    if not text:
        raise PipelineError("입력이 비어있습니다.")
    if text.startswith("{"):
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise PipelineError(f"JSON 파싱 실패: {e}")

    marker = "운영자 메모"
    idx = text.find(marker)
    if idx == -1:
        raise PipelineError(
            "이메일 원문에서 '운영자 메모' 표시를 찾지 못했습니다. "
            "이메일 전체(제목 아래 본문 전부)를 복사해 붙여넣었는지 확인해주세요."
        )
    brace_start = text.find("{", idx)
    if brace_start == -1:
        raise PipelineError("'운영자 메모' 뒤에서 JSON 시작 지점을 찾지 못했습니다.")
    depth = 0
    for i in range(brace_start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[brace_start:i + 1])
                except json.JSONDecodeError as e:
                    raise PipelineError(f"JSON 파싱 실패: {e}")
    raise PipelineError("JSON 블록이 중간에 잘린 것 같습니다 — 이메일 본문 전체를 다시 복사해주세요.")


def extract_reply_email(raw_text):
    m = re.search(r"전달받을 이메일:\s*(\S+@\S+)", raw_text)
    return m.group(1) if m else None


def summarize_intake(intake, catalog, reply_email=None):
    """미리보기 화면에 보여줄 요약 — 아직 아무 스크립트도 실행하지 않는다(비용 0)."""
    customer = intake.get("customer") or {}
    tier_key = intake.get("tier")
    tier_info = catalog.get(tier_key)
    partner = customer.get("partner")

    calendar_label = "음력(윤달)" if customer.get("is_leap_month") else (
        "양력" if customer.get("calendar_type") == "solar" else "음력"
    )

    return {
        "tier": tier_key,
        "tier_name": tier_info["name"] if tier_info else f"알 수 없는 티어({tier_key})",
        "tier_price": tier_info["price"] if tier_info else None,
        "tier_pages": tier_info.get("pages_approx") if tier_info else None,
        "question_limit": tier_info.get("question_limit") if tier_info else None,
        "customer_name": customer.get("name"),
        "gender": "여성" if customer.get("gender") == "F" else "남성",
        "birth": {
            "year": customer.get("birth_year"), "month": customer.get("birth_month"),
            "day": customer.get("birth_day"), "calendar": calendar_label,
            "hour": customer.get("birth_hour"), "unknown_time": customer.get("unknown_time"),
        },
        "reply_email": reply_email,
        "questions": customer.get("questions") or [],
        "has_partner": partner is not None,
        "partner_relationship": {
            "romantic": "연인ㆍ부부", "business": "동업ㆍ사업 파트너", "family": "가족ㆍ기타",
        }.get((partner or {}).get("relationship_type")) if partner else None,
        "has_synastry": bool(partner and partner.get("latitude") is not None),
    }


def _run(cmd, cwd, log):
    """2026-08-24 발견 — 이 파이썬 프로세스가 자식 프로세스(node.exe)를 띄울 때, 이 환경의
    Windows 콘솔 코드페이지 상속 방식 때문에 node가 한글 섞인 stdout을 UTF-8이 아닌 다른
    인코딩으로 내보내는 경우가 실제로 있었다(intake.json 결로 폴더에 "테스트주문"이
    포함되자 재현됨) — subprocess.run이 그 바이트를 utf-8로 강제 디코딩하다 그대로
    예외를 던져서, **결제 여부와 무관하게** 전체 주문 처리가 통째로 죽는 문제가 있었다.
    이 로그는 화면 표시용일 뿐 실제 계산ㆍ결제 로직에 쓰이지 않으므로, 디코딩 문제로 이
    함수 자체가 죽는 일은 절대 없어야 한다 — errors="replace"로 깨진 바이트는 대체 문자로
    바꾸고 넘어가게 한다(로그 가독성만 살짝 떨어질 뿐, 파이프라인은 절대 안 죽는다)."""
    log.append(f"$ {' '.join(cmd)}")
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.stdout:
        log.append(proc.stdout.strip())
    if proc.stderr:
        log.append("[stderr] " + proc.stderr.strip())
    if proc.returncode != 0:
        raise PipelineError(f"명령 실패(exit {proc.returncode}): {' '.join(cmd)}\n{proc.stderr}")
    return proc.stdout


def run_full_pipeline(intake, order_id, reply_email=None):
    """4~7단계 전체 실행. 5단계에서 실제 Anthropic API 호출(비용 발생)이 나간다 —
    이 함수를 부르는 쪽(app.py)이 그 전에 사람 확인을 받았다고 가정한다."""
    log = []
    catalog = load_tier_catalog()
    tier_info = catalog.get(intake.get("tier"))
    expected_pages = tier_info.get("pages_approx") if tier_info else None
    order_dir = ORDERS_DIR / order_id
    order_dir.mkdir(parents=True, exist_ok=True)

    intake_path = order_dir / "intake.json"
    computed_path = order_dir / "computed.json"
    report_json_path = order_dir / "report.json"
    pdf_path = order_dir / "report.pdf"

    intake_path.write_text(json.dumps(intake, ensure_ascii=False, indent=2), encoding="utf-8")

    # 4단계 — 계산 엔진
    _run(["node", "run.js", str(intake_path.resolve()), str(computed_path.resolve())], ENGINE_DIR, log)
    computed = json.loads(computed_path.read_text(encoding="utf-8"))

    # 5단계 — 리포트 생성 (API 비용 발생)
    build_out = _run(
        ["python", "build_report.py", str(computed_path.resolve()), str(report_json_path.resolve())],
        REPORT_DIR, log,
    )
    report = json.loads(report_json_path.read_text(encoding="utf-8"))

    m = re.search(r"입력\s+(\d+)\s*/\s*출력\s+(\d+)", build_out)
    cost = None
    if m:
        in_tok, out_tok = int(m.group(1)), int(m.group(2))
        usd = in_tok / 1_000_000 * INPUT_PRICE_PER_M + out_tok / 1_000_000 * OUTPUT_PRICE_PER_M
        cost = {
            "input_tokens": in_tok, "output_tokens": out_tok,
            "usd": round(usd, 4), "krw_approx": round(usd * USD_KRW_APPROX),
        }
    warnings = [line for line in build_out.splitlines() if line.strip().startswith("⚠")]

    # 6단계 — PDF 생성
    _run(
        ["python", "report_kit.py", str(computed_path.resolve()), str(report_json_path.resolve()), str(pdf_path.resolve())],
        REPORT_DIR, log,
    )

    # 7단계 — 자동 검증
    from pypdf import PdfReader
    n_pages = len(PdfReader(str(pdf_path)).pages)

    # 페이지 수 검증 — 카탈로그의 "목표 분량"은 최소 기준이지 상한이 아니다(사용자 명확화,
    # 2026-08-24: "페이지 수는 최소치를 정해놓은거지 그 이상 만드는건 아무런 상관없어.
    # 오히려 좋은거야"). 그래서 목표보다 많이 나온 건 절대 REVIEW로 잡지 않고, 약속치보다
    # 눈에 띄게 "부족한" 경우만(60% 미만) REVIEW로 표시한다.
    if expected_pages:
        ratio = n_pages / expected_pages
        page_status = "REVIEW" if ratio < 0.6 else "PASS"
    else:
        page_status = "UNKNOWN"

    qas = report.get("question_answers") or []
    non_direct = [qa for qa in qas if qa.get("answerability") != "direct"]

    result = {
        "order_id": order_id,
        "customer_name": (intake.get("customer") or {}).get("name"),
        "tier": computed.get("tier") or intake.get("tier"),
        "reply_email": reply_email,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "page_count": n_pages,
        "expected_pages": expected_pages,
        "page_status": page_status,
        "cost": cost,
        "warnings": warnings,
        "questions_total": len(qas),
        "questions_non_direct": [
            {"question": qa.get("question"), "answerability": qa.get("answerability"),
             "reason": qa.get("unanswerable_reason")}
            for qa in non_direct
        ],
        "pdf_path": str(pdf_path.resolve()),
        "log": log,
    }

    (order_dir / "meta.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def make_order_id(customer_name):
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    safe_name = re.sub(r"[^0-9A-Za-z가-힣_-]", "_", customer_name or "고객")
    return f"{stamp}_{safe_name}"


def list_past_orders():
    if not ORDERS_DIR.exists():
        return []
    orders = []
    for d in sorted(ORDERS_DIR.iterdir(), reverse=True):
        meta_path = d / "meta.json"
        if meta_path.exists():
            try:
                orders.append(json.loads(meta_path.read_text(encoding="utf-8")))
            except json.JSONDecodeError:
                continue
    return orders
