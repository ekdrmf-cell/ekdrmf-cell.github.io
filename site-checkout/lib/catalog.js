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
  // 2026-08-21 사용자 확정(2차): "체계 개수"를 가격의 1차 기준으로 삼고, "질문 개수"를 그
  // 안에 딸린 혜택으로 얹는 구조. 순수 질문개수제(3/6/10개=5/10/15만원)를 검토했으나,
  // 질문당 단가가 16,667/16,667/15,000원으로 거의 평평해서 업셀 유인이 없고, 이 상품의
  // 핵심 차별점(체계를 여러 개 겹쳐 교차검증)이 가격표에서 안 드러난다는 문제가 있어 기각.
  // 대신 체계 개수(=계산 깊이ㆍ교차분석 유무)로 가격을 정당화하고, 질문 개수는 상위
  // 티어일수록 더 준다: 5만원=1체계+질문3개, 10만원=2체계+교차분석+질문6개,
  // 15만원=3체계+교차분석+질문10개+타로 스프레드 심화(3장->켈틱크로스10장).
  //
  // name은 손님이 보자마자 뭘 받는지 알 수 있게 내용을 그대로 풀어씀. tier 필드
  // (mini/light/single/dual/master/premium)는 원래 내부 식별자였으나, **2026-08-23
  // 사용자가 이 방침을 뒤집음**: "싱글ㆍ마스터ㆍ프리미엄이라고 부를 거면 사이트에도 실제
  // 상품명으로 노출해라, 혼자만 알아듣는 말 쓰지 말라"고 명시 지시 — 그래서 label 필드
  // (FREE/LIGHT/SINGLE/DUAL/MASTER/PREMIUM, tier 값을 대문자로만 바꾼 것)를 신설해 이제
  // `crossnotics/index.html`의 티어 카드ㆍ비교표ㆍ`catalog_names.py`의 PDF 표지에까지
  // 전부 고객에게 그대로 노출한다. (이전 코멘트에 "코드명을 노출하지 말라고 지적함"이라고
  // 적혀 있었는데, 그 반대 방향으로 확정 지시가 다시 내려온 것 — 다음 세션에서 헷갈리지
  // 않도록 이 변경 이력을 남겨둠.)
  //
  // 2026-08-22 추가(사용자 요청): 5만원부터 시작하면 진입장벽이 높아 저가 진입 상품 2개를
  // 추가함(운명도감처럼 가볍고 저렴한 진입점을 여러 개 두는 방식 참고). "체계 개수" 축은
  // 그대로 두고(둘 다 사주 1체계), 그 안에서 "깊이"(scope)로 5만원 상품과 구분되게 함 —
  // 안 그러면 1만원짜리가 5만원짜리와 내용이 똑같아져 상위 티어를 잠식함. scope는
  // build_report.py가 리포트 분량ㆍ어디까지 다룰지를 조절하는 데 쓰는 필드(각 값의 의미는
  // build_report.py SYSTEM_PROMPT 주석 참고).
  //
  // 2026-08-22(2차) 사용자 지시로 추가 변경:
  // (a) "오늘의 사주 미니 진단"을 무료(price: 0)로 전환 — 진입 장벽을 아예 없애는 리드
  //     확보용 상품(운명도감의 "무료 분석 시작하기"와 같은 역할).
  // (b) crossnotics-premium(20만원) 신설 — 운명도감의 "10년 인생 전략 설계ㆍ평생 인생
  //     전략 설계ㆍ인생 2막 로드맵" 3개를 하나로 묶은 장기 전략 프리미엄. 새 계산 엔진은
  //     필요 없음 — saju.js가 이미 계산해주는 대운 8구간(dae_yun)을 build_report.py가
  //     scope: "premium"일 때 전용 섹션(long_term_strategy)으로 더 깊이 풀어 쓰는 방식.
  //
  // 2026-08-22(3차) 사용자 지시로 pages_note/pages_approx 재조정 — "가격대비 분량이 너무
  // 적어 보인다"는 지적으로 목표 분량을 single 6pㆍdual 13pㆍmaster 20pㆍpremium 30p로
  // 크게 올림. build_report.py의 SYSTEM_PROMPT를 "체계 하나당 섹션 1개"에서 "체계 하나당
  // 3~4개 하위 섹션(총론/세부해석/실전포인트 등)" 구조로 대폭 확장하고, report_kit.py도
  // pdf_kit.py의 미사용 컴포넌트(bar_row/stat_hero/flow_diagram/icon_steps/summary_box)를
  // 전부 실제로 쓰도록 고쳤다.
  //
  // 2026-08-22(4차) 사용자 지시: "약ㆍ목표 같은 애매한 표현 쓰지 말고 정확한 페이지 수를
  // 못박아라." pages_note를 확정 수치로 바꿈 — single 6pㆍdual 13pㆍmaster 20pㆍpremium
  // 30p는 이제 "추정"이 아니라 **이 상품이 지켜야 할 사양(spec)**이다. 이걸 실제로
  // 지키는 방법: LLM 출력은 본질적으로 분량이 정확히 고정되지 않으므로(스캐폴딩과 max_tokens로
  // 방향만 유도 가능), 계획서 1번 파이프라인이 이미 전제하는 "사람이 결과물을 먼저 검증한
  // 뒤에만 발송한다" 단계에서 **실제 생성된 PDF의 페이지 수가 이 사양에 못 미치면 재생성
  // 하거나 사람이 보강할 것** — 이 확인은 build_report.py/report_kit.py 코드가 자동으로
  // 강제하지 않으니, 발송 전 체크리스트에 "페이지 수가 사양과 맞는지"를 반드시 포함할 것.
  "crossnotics-mini": {
    name: "오늘의 사주 미니 진단",
    label: "FREE",
    price: 0,
    tier: "mini",
    scope: "mini",
    systems: ["saju"],
    question_limit: 0,
    pages_note: "1페이지",
    pages_approx: 1,
  },
  "crossnotics-saju-light": {
    name: "사주 라이트 진단 (질문 1개)",
    label: "LIGHT",
    price: 30000,
    tier: "light",
    scope: "light",
    systems: ["saju"],
    question_limit: 1,
    pages_note: "2페이지",
    pages_approx: 2,
  },
  "crossnotics-saju-only": {
    name: "사주 단독 진단 (질문 3개)",
    label: "SINGLE",
    price: 50000,
    tier: "single",
    scope: "full",
    systems: ["saju"],
    question_limit: 3,
    pages_note: "6페이지",
    pages_approx: 6,
  },
  "crossnotics-saju-astrology": {
    name: "사주 + 별자리 교차진단 (질문 6개)",
    label: "DUAL",
    price: 100000,
    tier: "dual",
    scope: "full",
    systems: ["saju", "astrology"],
    question_limit: 6,
    pages_note: "13페이지",
    pages_approx: 13,
  },
  "crossnotics-full": {
    name: "사주 + 별자리 + 타로 통합진단 (질문 10개)",
    label: "MASTER",
    price: 150000,
    tier: "master",
    scope: "full",
    systems: ["saju", "astrology", "tarot"],
    question_limit: 10,
    pages_note: "20페이지",
    pages_approx: 20,
  },
  "crossnotics-premium": {
    name: "장기 인생 전략 프리미엄 (질문 12개)",
    label: "PREMIUM",
    price: 200000,
    tier: "premium",
    scope: "premium",
    systems: ["saju", "astrology", "tarot"],
    question_limit: 12,
    pages_note: "30페이지",
    pages_approx: 30,
  },
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

// tools/crossnotics-engine/run.js가 여기서 question_limit을 가져다 씀 — 가격표(이 파일)를
// 유일한 기준으로 삼아서, 질문 개수 제한이 여러 파일에 따로 적혀 어긋나는 걸 방지한다.
function getCrossnoticsTierConfig(tier) {
  const found = Object.values(CROSSNOTICS_TIERS).find((p) => p.tier === tier);
  if (!found) throw new Error(`알 수 없는 크로스노틱스 티어: ${tier}`);
  return found;
}

module.exports = { CATALOG, getProduct, productType, getCrossnoticsTierConfig };
