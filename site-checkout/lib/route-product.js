/*
 * 상품 코드별 후처리 라우팅. 웹훅에서 결제 금액 검증까지 끝난 뒤 이 함수가 호출된다.
 *
 * 2026-08-23 — 크로스노틱스(천지인운명관) 전용 후처리(fulfillCrossnotics)는 여기서
 * 제거됐다(사용자 지시: 서비스허브와 천지인운명관 사이의 공유 파일을 전부 분리할 것).
 * 이 site-checkout은 이제 서비스허브(전자책ㆍ서비스)만 다루는 결제 백엔드다 — 애초에
 * 카드결제 자동화 자체가 아직 배포 전(계좌이체 수동 확인 방식 사용 중)이라 지금 당장
 * 영향받는 실사용은 없다. 천지인운명관이 카드결제 자동화가 필요해지면, 이 파일을 공유하지
 * 말고 별도의 독립된 체크아웃을 새로 만들 것.
 */
const { sendDeliveryEmail } = require("./deliver-email");

async function fulfillEbookOrService(product, order) {
  // TODO(계획서 9번 미해결 항목): 기존 전자책ㆍ서비스 파일을 Vercel 함수에서 접근 가능한 곳에
  // 호스팅하는 방식(예: GitHub Pages 공개 경로로 옮기기, 또는 별도 스토리지)이 아직 결정 안 됨 —
  // 현재 파일들은 사용자 로컬 PC(products/, 전자책 자동화/ 폴더)에만 있어 서버리스 함수가 못 읽음.
  // 사용자에게 "기존 상품도 지금 이 시스템으로 옮길지" 확인 후 파일 소스를 정하고 구현할 것.
  throw new Error(
    `NOT_IMPLEMENTED: ${product.name} 자동발송은 아직 미구현 — 기존 상품 파일 호스팅 방식을 ` +
    `먼저 정해야 함(계획서 9번 "남은 판단 사항" 참고). 지금은 계좌이체+수동발송 방식을 계속 쓸 것.`
  );
}

/**
 * @param {object} product - catalog.js의 상품 정보
 * @param {object} order - {paymentId, customer, email}
 */
async function routeProduct(product, type, order) {
  return fulfillEbookOrService(product, order);
}

module.exports = { routeProduct };
