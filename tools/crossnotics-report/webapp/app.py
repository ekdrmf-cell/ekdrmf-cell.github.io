"""
천지인운명관 주문 처리 프로그램 — 로컬 웹앱.

실행: python app.py  (브라우저가 자동으로 http://127.0.0.1:5151 을 엶)
또는 상위 폴더의 "천지인운명관_프로그램_실행.bat"을 더블클릭.

1단계(주문접수)ㆍ2단계(입금확인, 이 프로그램 밖에서 케이뱅크 앱으로 직접)ㆍ
8단계(고객 발송)ㆍ9단계(사후처리)는 이 프로그램이 대신하지 않는다 — 사용자 지시로
확정된 자동화 범위(order_fulfillment_checklist.md 참고)는 3~7단계뿐이다.
"""
import threading
import webbrowser
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file

import pipeline

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/list-orders", methods=["POST"])
def api_list_orders():
    """2026-08-24 신설 — 사용자 지시: "주문이 1개든 100개든 한 번에 처리되면 좋겠다."
    아직 리포트를 생성 안 한 주문 이메일을 전부 가져와서, 각각 미리보기까지 만들어
    한 번에 돌려준다. 이메일 하나가 파싱에 실패해도(예: 형식이 깨짐) 전체 목록이
    죽지 않도록 항목별로 개별 처리한다."""
    try:
        emails = pipeline.fetch_all_pending_orders()
    except pipeline.PipelineError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"ok": False, "error": f"예상치 못한 오류: {e}"}), 500

    catalog = pipeline.load_tier_catalog()
    orders = []
    for item in emails:
        try:
            intake = pipeline.extract_intake_json(item["raw"])
            reply_email = pipeline.extract_reply_email(item["raw"])
            preview = pipeline.summarize_intake(intake, catalog, reply_email)
            orders.append({
                "message_key": item["message_key"],
                "date": item["date"],
                "intake": intake,
                "reply_email": reply_email,
                "preview": preview,
                "parse_error": None,
            })
        except pipeline.PipelineError as e:
            # 이 항목만 "파싱 실패"로 표시하고, 나머지 정상 항목은 그대로 목록에 남긴다.
            orders.append({
                "message_key": item["message_key"], "date": item["date"],
                "intake": None, "reply_email": None, "preview": None,
                "parse_error": str(e),
            })
    return jsonify({"ok": True, "orders": orders})


@app.route("/api/parse", methods=["POST"])
def api_parse():
    raw = (request.json or {}).get("raw", "")
    try:
        intake = pipeline.extract_intake_json(raw)
        catalog = pipeline.load_tier_catalog()
        reply_email = pipeline.extract_reply_email(raw)
        preview = pipeline.summarize_intake(intake, catalog, reply_email)
    except pipeline.PipelineError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"ok": False, "error": f"예상치 못한 오류: {e}"}), 500
    return jsonify({"ok": True, "preview": preview, "intake": intake, "reply_email": reply_email})


@app.route("/api/generate", methods=["POST"])
def api_generate():
    body = request.json or {}
    intake = body.get("intake")
    reply_email = body.get("reply_email")
    message_key = body.get("message_key")  # Gmail 목록에서 온 주문이면 있음, 수동 붙여넣기면 없음
    if not intake:
        return jsonify({"ok": False, "error": "intake 데이터가 없습니다 — 먼저 주문 확인을 진행하세요."}), 400
    try:
        order_id = pipeline.make_order_id((intake.get("customer") or {}).get("name"))
        result = pipeline.run_full_pipeline(intake, order_id, reply_email)
        # 2026-08-24 추가 — 리포트 생성이 실제로 성공했을 때만 "처리 완료"로 기록한다.
        # 목록에 보여준 것만으로는 기록 안 하므로(list-orders 참고), 도중에 실패하면
        # 다음 목록 조회에도 이 주문이 그대로 다시 나타난다(재시도 가능).
        pipeline.mark_order_fetched(message_key)
    except pipeline.PipelineError as e:
        return jsonify({"ok": False, "error": str(e)}), 500
    except Exception as e:
        return jsonify({"ok": False, "error": f"예상치 못한 오류: {e}"}), 500
    return jsonify({"ok": True, "result": result})


@app.route("/api/orders")
def api_orders():
    return jsonify({"ok": True, "orders": pipeline.list_past_orders()})


@app.route("/api/pdf/<order_id>")
def api_pdf(order_id):
    pdf_path = pipeline.ORDERS_DIR / order_id / "report.pdf"
    if not pdf_path.exists():
        return jsonify({"ok": False, "error": "PDF를 찾을 수 없습니다."}), 404
    return send_file(pdf_path, as_attachment=False, download_name=f"{order_id}.pdf")


@app.route("/api/open-folder/<order_id>", methods=["POST"])
def api_open_folder(order_id):
    import os
    order_dir = pipeline.ORDERS_DIR / order_id
    if not order_dir.exists():
        return jsonify({"ok": False, "error": "폴더를 찾을 수 없습니다."}), 404
    try:
        os.startfile(str(order_dir))  # Windows 전용 — 이 프로그램은 사용자 로컬 PC에서만 실행됨
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
    return jsonify({"ok": True})


def _open_browser():
    webbrowser.open("http://127.0.0.1:5151")


if __name__ == "__main__":
    threading.Timer(1.0, _open_browser).start()
    app.run(host="127.0.0.1", port=5151, debug=False)
