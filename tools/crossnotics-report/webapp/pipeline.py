"""
천지인운명관 주문 처리 프로그램 — 핵심 로직 (app.py가 이 모듈을 불러다 씀).

order_fulfillment_checklist.md의 3~7단계(intake.json 만들기 ~ 발송 전 검증)를
코드 한 곳에 모았다. 1단계(주문접수)ㆍ2단계(입금확인)ㆍ8단계(고객발송)ㆍ9단계(사후처리)는
사람이 판단할 부분이라 이 프로그램 밖에 남겨둔다(2026-08-23, 사용자 지시로 자동화
범위 확정).

가격 계산은 Sonnet 5($3/100만 입력토큰ㆍ$15/100만 출력토큰 표준가 기준, claude-api 스킬로
2026-08-29 확인) 기준이며, 환율은 화면에 "약"으로만 표기하는 참고용 추정치다.

2026-08-29 — 실제 리포트 생성 모델을 claude-sonnet-4-5(64K 출력 한도)에서 claude-sonnet-5
(128K 출력 한도)로 옮김(build_report.py MODEL 상수) — premium 티어가 64K에서 실제로 잘리는
사고가 나서다. 이 가격 상수는 두 모델 다 표준가가 같아 그대로 유지.
"""
import email
import imaplib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from email.header import decode_header
from pathlib import Path

from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent
REPORT_DIR = HERE.parent
ENGINE_DIR = REPORT_DIR.parent / "crossnotics-engine"
ORDERS_DIR = REPORT_DIR / "orders"

load_dotenv(REPORT_DIR / ".env")
GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")
ORDER_SUBJECT_MARKER = "천지인운명관"
FETCHED_IDS_PATH = HERE / "fetched_email_ids.json"

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
    """이메일 원문(또는 intake.json 그 자체)에서 intake JSON을 뽑아낸다.

    2026-08-24 원인 분석 — 실제로 "Invalid control character at: line 1 column 71" 같은
    에러가 반복됨. index.html이 JSON.stringify(intakeJson)로 만드는 건 원래 줄바꿈 없는
    한 줄짜리 텍스트인데, 이메일이 Gmail/SMTP를 거치는 과정에서 너무 긴 줄을 자동으로
    줄바꿈해버리는 경우가 있다(70~76자 부근에서 실제로 끊김 — 표준 이메일 줄바꿈 관례와
    일치). 그 줄바꿈이 JSON 문자열 값 한가운데 들어가면 Python json 모듈이 기본(strict)
    모드에서는 "제어 문자(줄바꿈 등)가 문자열 안에 그대로 있으면 안 된다"며 거부한다.
    strict=False를 주면 그런 제어 문자를 문자열의 일부로 그냥 허용하므로(의미상으로도
    문제 없음 — 어차피 원래 있던 게 아니라 전송 중 끼어든 줄바꿈일 뿐), 이 사고의 원인을
    코드 쪽에서 흡수한다."""
    text = raw_text.strip()
    if not text:
        raise PipelineError("입력이 비어있습니다.")
    if text.startswith("{"):
        try:
            return json.loads(text, strict=False)
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
                    return json.loads(text[brace_start:i + 1], strict=False)
                except json.JSONDecodeError as e:
                    raise PipelineError(f"JSON 파싱 실패: {e}")
    raise PipelineError("JSON 블록이 중간에 잘린 것 같습니다 — 이메일 본문 전체를 다시 복사해주세요.")


def extract_reply_email(raw_text):
    m = re.search(r"전달받을 이메일:\s*(\S+@\S+)", raw_text)
    return m.group(1) if m else None


def _load_fetched_ids():
    if not FETCHED_IDS_PATH.exists():
        return set()
    try:
        return set(json.loads(FETCHED_IDS_PATH.read_text(encoding="utf-8")))
    except json.JSONDecodeError:
        return set()


def _save_fetched_ids(ids):
    FETCHED_IDS_PATH.write_text(json.dumps(sorted(ids), ensure_ascii=False, indent=2), encoding="utf-8")


def _decode_subject(raw_subject):
    if not raw_subject:
        return ""
    decoded = ""
    for text, enc in decode_header(raw_subject):
        decoded += text.decode(enc or "utf-8", errors="replace") if isinstance(text, bytes) else text
    return decoded


def _extract_body_text(msg):
    """text/plain 파트를 우선 찾고, 없으면 text/html에서 태그만 벗겨낸다."""
    if msg.is_multipart():
        html_fallback = None
        for part in msg.walk():
            disp = str(part.get("Content-Disposition") or "")
            if "attachment" in disp:
                continue
            charset = part.get_content_charset() or "utf-8"
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    return payload.decode(charset, errors="replace")
            elif part.get_content_type() == "text/html" and html_fallback is None:
                payload = part.get_payload(decode=True)
                if payload:
                    html_fallback = payload.decode(charset, errors="replace")
        return re.sub(r"<[^>]+>", "", html_fallback) if html_fallback else ""
    charset = msg.get_content_charset() or "utf-8"
    payload = msg.get_payload(decode=True)
    return payload.decode(charset, errors="replace") if payload else ""


def fetch_all_pending_orders():
    """Gmail 받은편지함에서 아직 리포트를 생성하지 않은 '천지인운명관' 주문 이메일을
    전부(최신순) 찾아 리스트로 반환한다 — 2026-08-24, 사용자 지시로 "1개든 100개든
    한 번에" 목록으로 보여주는 방식으로 전면 개편(예전 fetch_latest_order_email은
    한 번에 1건만 가져오던 방식이라 폐기).

    **여기서는 fetched_email_ids.json에 아무것도 기록하지 않는다** — 목록에 보여주는 것과
    "처리 완료"는 다른 일이다. 화면에 뜬 주문 중 사장님이 실제로 입금을 확인하고 체크해서
    리포트를 생성한 것만 mark_order_fetched()로 기록되고, 체크 안 한(=아직 입금 미확인)
    주문은 다음에 또 목록에 그대로 남아있어야 한다."""
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        raise PipelineError(
            "Gmail 연동 정보가 없습니다 — tools/crossnotics-report/.env 파일에 GMAIL_ADDRESS와 "
            "GMAIL_APP_PASSWORD(구글 계정 2단계 인증 설정의 '앱 비밀번호')를 채워주세요."
        )

    fetched_ids = _load_fetched_ids()

    try:
        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        imap.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
    except imaplib.IMAP4.error as e:
        raise PipelineError(f"Gmail 로그인 실패: {e} (앱 비밀번호가 맞는지 확인해주세요)")

    results = []
    try:
        imap.select("INBOX", readonly=True)
        # 2026-08-24 수정 — 예전엔 SUBJECT 검색어로 "천지인운명관"(한글)을 그대로 넘겼는데,
        # charset을 안 정해주면(None) imaplib이 검색 명령 전체를 ASCII로 인코딩하려다
        # UnicodeEncodeError로 죽는 실제 사고가 났음("'ascii' codec can't encode..."). IMAP
        # 서버에 한글 검색어를 안전하게 보내는 방법(CHARSET UTF-8 + 리터럴)은 imaplib
        # 버전별로 까다로워서, 아예 서버 쪽 검색은 ASCII로만 안전한 기준(최근 날짜)으로
        # 좁히고, 실제 "천지인운명관" 여부 판정은 파이썬에서 제목을 디코딩해 직접 비교한다
        # — 원인이 되는 "한글을 IMAP 검색어로 보내는 행위" 자체를 없앤 것.
        since_date = (datetime.now() - timedelta(days=90)).strftime("%d-%b-%Y")
        status, data = imap.search(None, "SINCE", since_date)
        if status != "OK":
            raise PipelineError("Gmail 검색에 실패했습니다.")
        msg_ids = data[0].split()

        for msg_id in reversed(msg_ids):  # 최신 이메일부터
            status, hdr_data = imap.fetch(msg_id, "(BODY.PEEK[HEADER.FIELDS (MESSAGE-ID SUBJECT)])")
            if status != "OK" or not hdr_data or not hdr_data[0]:
                continue
            header_msg = email.message_from_bytes(hdr_data[0][1])
            subject = _decode_subject(header_msg.get("Subject"))
            if ORDER_SUBJECT_MARKER not in subject:
                continue
            message_key = header_msg.get("Message-ID") or msg_id.decode()
            if message_key in fetched_ids:
                continue  # 이미 리포트까지 생성 완료한 주문은 목록에서 제외

            status, msg_data = imap.fetch(msg_id, "(RFC822)")
            if status != "OK" or not msg_data or not msg_data[0]:
                continue
            msg = email.message_from_bytes(msg_data[0][1])
            body = _extract_body_text(msg)
            if not body.strip():
                continue

            results.append({
                "message_key": message_key,
                "subject": subject,
                "date": msg.get("Date"),
                "raw": body,
            })

        return results
    finally:
        imap.logout()


def mark_order_fetched(message_key):
    """리포트를 실제로 생성 완료한 주문만 여기로 기록한다(app.py의 /api/generate가 성공한
    뒤에만 호출) — 목록에 보여준 것만으로는 기록하지 않으므로, 체크 안 한 주문은 다음
    조회에도 계속 목록에 남는다."""
    if not message_key:
        return
    fetched_ids = _load_fetched_ids()
    fetched_ids.add(message_key)
    _save_fetched_ids(fetched_ids)


def estimate_cost_for_tier(tier_key):
    """해당 티어의 과거 실측 비용(krw_approx) 평균 — 지어낸 추정치가 아니라 실제 생성
    이력에서만 계산한다. 이력이 하나도 없는 티어는 None(미실측)을 그대로 반환한다."""
    samples = [
        o["cost"]["krw_approx"]
        for o in list_past_orders()
        if o.get("tier") == tier_key and o.get("cost")
    ]
    if not samples:
        return None
    return {"krw_approx": round(sum(samples) / len(samples)), "sample_count": len(samples)}


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
        "cost_estimate": estimate_cost_for_tier(tier_key),
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
