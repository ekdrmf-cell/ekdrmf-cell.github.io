/*
 * 포트원(PortOne) V2 결제완료 웹훅 수신 — Vercel Node.js 서버리스 함수.
 * 배포: 이 site-checkout/ 폴더를 별도 Vercel 프로젝트로 배포(무료 Hobby 플랜으로 충분).
 * 엔드포인트: https://<프로젝트>.vercel.app/api/webhook — 포트원 관리자콘솔의
 * "웹훅 설정"에 이 URL을 등록.
 *
 * 보안 핵심 원칙(반드시 지킬 것):
 * 1) 결제 금액은 절대 클라이언트(웹훅 payload)를 그대로 신뢰하지 않는다 — 반드시 포트원
 *    REST API로 해당 paymentId를 서버가 직접 재조회해서 금액을 검증한다(변조 방지).
 * 2) 서버가 재조회한 금액이 catalog.js의 상품 가격과 다르면 즉시 중단하고 알림만 남긴다.
 *
 * 필요 환경변수:
 * - PORTONE_WEBHOOK_SECRET: 포트원 콘솔에서 발급받는 웹훅 검증용 시크릿
 * - PORTONE_API_SECRET: 결제 조회 REST API 호출용 시크릿(웹훅 시크릿과 다름)
 * - GMAIL_USER, GMAIL_APP_PASSWORD: deliver-email.js 참고
 *
 * 검증 안 된 부분(다음 세션이 실제 포트원 테스트 결제로 반드시 확인할 것):
 * - GET /payments/{id} 응답에서 결제금액 필드 경로(`amount.total`로 가정, 공식 문서 fetch로는
 *   PaymentAmount 타입에 total/taxFree/vat 필드가 있다는 것까지만 확인함)
 * - customData(가맹점이 결제 생성 시 넘긴 상품코드+고객정보 JSON)가 응답의 정확히 어느
 *   필드에 실리는지(`customData`로 가정 — PortOne V2 결제창 SDK의 customData 파라미터와
 *   이름을 맞춘 것이라 합리적 추정이지만 실제 응답으로 확인 전까지는 가정임)
 * - Authorization 헤더 형식(`PortOne ${API_SECRET}`로 가정 — PortOne V2 REST API 공통 패턴)
 */
const PortOne = require("@portone/server-sdk");
const { getProduct, productType } = require("../lib/catalog");
const { routeProduct } = require("../lib/route-product");
const { sendDeliveryEmail } = require("../lib/deliver-email");

// Vercel이 body를 자동으로 JSON 파싱하지 않게 막는다 — 웹훅 서명 검증은 raw 텍스트가 필요함.
module.exports.config = { api: { bodyParser: false } };

function readRawBody(req) {
  return new Promise((resolve, reject) => {
    let data = "";
    req.on("data", (chunk) => (data += chunk));
    req.on("end", () => resolve(data));
    req.on("error", reject);
  });
}

async function fetchPaymentFromPortOne(paymentId) {
  const res = await fetch(`https://api.portone.io/payments/${encodeURIComponent(paymentId)}`, {
    headers: { Authorization: `PortOne ${process.env.PORTONE_API_SECRET}` },
  });
  if (!res.ok) throw new Error(`포트원 결제조회 실패: HTTP ${res.status}`);
  return res.json();
}

module.exports = async function handler(req, res) {
  if (req.method !== "POST") {
    res.status(405).end();
    return;
  }

  const rawBody = await readRawBody(req);

  let webhook;
  try {
    webhook = await PortOne.Webhook.verify(process.env.PORTONE_WEBHOOK_SECRET, rawBody, req.headers);
  } catch (e) {
    if (e instanceof PortOne.Webhook.WebhookVerificationError) {
      console.error("웹훅 서명 검증 실패:", e.message);
      res.status(400).end();
      return;
    }
    throw e;
  }

  // 결제완료 타입만 처리, 나머지(취소 등)는 일단 200으로 확인만 하고 무시(추후 필요시 확장)
  if (webhook.type !== "Transaction.Paid") {
    res.status(200).end();
    return;
  }

  const { paymentId } = webhook.data;

  try {
    const payment = await fetchPaymentFromPortOne(paymentId);

    // customData에 결제 생성 시(프론트엔드) 심어둔 상품코드ㆍ고객정보(생년월일시 등)가 들어있음
    const customData = JSON.parse(payment.customData || "{}");
    const productCode = customData.productCode;
    const customer = customData.customer || {};
    const buyerEmail = customData.email;

    const product = getProduct(productCode);
    const type = productType(productCode);

    // 금액 위변조 방지 — 서버가 재조회한 실제 결제금액과 카탈로그 가격이 일치하는지 확인
    const paidAmount = payment.amount && payment.amount.total;
    if (paidAmount !== product.price) {
      console.error(`금액 불일치! paymentId=${paymentId} 결제금액=${paidAmount} 카탈로그가격=${product.price}`);
      res.status(200).end(); // 웹훅 자체는 정상 수신 처리(재시도 방지), 후처리는 여기서 중단
      return;
    }

    const order = { paymentId, customer, email: buyerEmail };
    const fulfillment = await routeProduct(product, type, order);

    await sendDeliveryEmail({
      to: buyerEmail,
      subject: `[서비스허브] ${product.name} 주문이 완료됐습니다`,
      text: `주문하신 "${product.name}"를 첨부해드립니다. 문의사항은 이 메일로 회신해주세요.`,
      attachments: fulfillment.attachments,
    });

    res.status(200).json({ ok: true });
  } catch (e) {
    // NOT_IMPLEMENTED 등 아직 못 만든 단계는 결제 자체는 정상 처리하되 사람이 후속 조치하도록
    // 에러를 로그로 남긴다(Vercel 로그에서 확인 — 3ㆍ4단계 완료 전까지는 예상된 상태).
    console.error(`주문 처리 실패 paymentId=${paymentId}:`, e.message);
    res.status(200).json({ ok: false, note: "결제는 확인됐으나 자동 후처리 실패 — 로그 확인 후 수동 처리 필요", error: e.message });
  }
};
