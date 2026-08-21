/*
 * 서비스허브 전체 상품 카탈로그 — site-checkout이 결제 금액 검증(서버에서 재확인, 클라이언트
 * 값을 절대 신뢰하지 않음)과 상품별 후처리 라우팅에 쓰는 단일 소스.
 *
 * price는 전부 이 세션에서 실제 확인한 값만 넣었다 — 확인 안 된 값을 추측해서 채우지 않는다
 * (verify-before-acting 원칙). 서비스(구글시트 자동화) 11종은 현재 가격을 이 세션에서 직접
 * 확인하지 못해 price: null로 남겨둠 — 실제 연동 전에 services.html에서 최신가를 다시 확인할 것.
 */

const EBOOKS = {
  "ebook-gov-subsidy": { name: "소상공인 정부지원금 찾기 가이드", price: 19900, file: "gov-subsidy-guide/정부지원금_찾기_가이드.pdf" },
  "ebook-writing-guide": { name: "전자책 만들어 팔기 실전 가이드", price: 12900, file: "ebook-writing-guide/전자책_만들어_팔기_가이드.pdf" },
  "ebook-adsense": { name: "구글 애드센스 블로그 시작 가이드", price: 13900, file: "adsense-blog-guide/애드센스_블로그_시작_가이드.pdf" },
  "ebook-instagram": { name: "인스타그램 마케팅 핵심노하우", price: 12900, file: "instagram-marketing-guide/인스타그램_마케팅_핵심노하우.pdf" },
  "ebook-architecture": { name: "건축기사 실기 합격 전략 가이드", price: 9900, file: "architecture-exam-strategy-guide/건축기사_실기_합격전략_가이드.pdf" },
  "ebook-youtube": { name: "유튜브 채널 수익화 전략 가이드", price: 13900, file: "youtube-monetization-guide/유튜브_채널_수익화_전략_가이드.pdf" },
  "ebook-affiliate": { name: "제휴마케팅 실전 가이드", price: 12900, file: "affiliate-marketing-guide/제휴마케팅_실전_가이드.pdf" },
  "ebook-coupang": { name: "쿠팡 셀러 창업 가이드", price: 21900, file: "coupang-seller-guide/쿠팡_셀러_창업_가이드.pdf" },
  "ebook-meta-ads": { name: "메타 광고 최적화 가이드", price: 19900, file: "meta-ads-guide/메타_광고_최적화_가이드.pdf" },
  "ebook-chatgpt": { name: "챗GPT 실무 활용 가이드", price: 11900, file: "chatgpt-usage-guide/챗GPT_실무_활용_가이드.pdf" },
  "ebook-shopping-cs": { name: "쇼핑몰 CS 고객응대 가이드", price: 19900, file: "shopping-cs-guide/쇼핑몰_CS_고객응대_가이드.pdf" },
  "ebook-vat-check": { name: "1인사업자 부가세 셀프 체크리스트", price: 19900, file: "vat-self-check-guide/1인사업자_부가세_셀프_체크리스트.pdf" },
  "ebook-qoo10-japan": { name: "큐텐재팬 셀러 판매전략 가이드", price: 36900, file: "qoo10-japan-seller-guide/큐텐재팬_셀러_판매전략_가이드.pdf" },
};

// TODO(연동 전 필수): 서비스 11종 최신 가격을 services.html에서 재확인 후 채울 것 — 지금은
// 이 세션에서 직접 검증하지 못한 값이라 추측해서 채우지 않음.
const SERVICES = {
  // "service-quote-generator": { name: "견적서 자동생성 템플릿", price: null, file: "quote-generator.zip" },
};

const CROSSNOTICS_TIERS = {
  // TODO(0단계 완료 후 확정): 백서 제안가 그대로 — 계획서 9번 "다중소스 시장조사" 아직 안 함.
  "crossnotics-single": { name: "크로스노틱스 싱글 진단(1체계)", price: 39900, tier: "single", systems: ["saju"] },
  "crossnotics-dual": { name: "크로스노틱스 듀얼 크로스 매트릭스(2체계)", price: 89900, tier: "dual", systems: ["saju", "astrology"] },
  "crossnotics-master": { name: "크로스노틱스 마스터 다차원 통합(3체계)", price: 159000, tier: "master", systems: ["saju", "astrology", "tarot"] },
};

const CATALOG = { ...EBOOKS, ...SERVICES, ...CROSSNOTICS_TIERS };

function getProduct(productCode) {
  const product = CATALOG[productCode];
  if (!product) throw new Error(`알 수 없는 상품 코드: ${productCode}`);
  if (product.price == null) throw new Error(`상품 "${productCode}"는 가격 미확정 상태(TODO) — 결제 연동 전에 catalog.js에서 채울 것`);
  return product;
}

function productType(productCode) {
  if (productCode.startsWith("ebook-")) return "ebook";
  if (productCode.startsWith("service-")) return "service";
  if (productCode.startsWith("crossnotics-")) return "crossnotics";
  throw new Error(`상품 코드 접두어로 타입을 판별할 수 없음: ${productCode}`);
}

module.exports = { CATALOG, getProduct, productType };
