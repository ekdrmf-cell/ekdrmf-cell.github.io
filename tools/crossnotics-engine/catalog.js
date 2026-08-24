/*
 * 천지인운명관(크로스노틱스) 전용 상품 카탈로그 — 가격ㆍ상품명ㆍ분량의 단일 소스.
 *
 * 2026-08-23 — 서비스허브의 site-checkout/lib/catalog.js(전자책ㆍ서비스 카탈로그와 함께
 * 있던 CROSSNOTICS_TIERS)에서 완전히 분리된 독립 사본입니다(사용자 지시: 서비스허브와
 * 천지인운명관 사이의 공유 파일을 전부 분리할 것). `crossnotics/index.html`의 `CN_TIERS`
 * 배열도 같은 값을 손으로 맞춰서 갖고 있습니다(두 파일이 자동 동기화되지 않으니, 가격ㆍ
 * 티어를 바꿀 때는 이 파일과 `crossnotics/index.html` 둘 다 고칠 것 — 기존 관행 그대로 유지).
 *
 * price는 전부 실제 확인된 값만 넣었다(추측해서 채우지 않음, verify-before-acting 원칙).
 */
const CROSSNOTICS_TIERS = {
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
    systems: ["saju", "astrology", "tarot", "behavior"],
    question_limit: 12,
    pages_note: "30페이지",
    pages_approx: 30,
  },
};

// tools/crossnotics-engine/run.js가 여기서 question_limit을 가져다 씀.
function getCrossnoticsTierConfig(tier) {
  const found = Object.values(CROSSNOTICS_TIERS).find((p) => p.tier === tier);
  if (!found) throw new Error(`알 수 없는 크로스노틱스 티어: ${tier}`);
  return found;
}

module.exports = { CROSSNOTICS_TIERS, getCrossnoticsTierConfig };
