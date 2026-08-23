/*
 * 크로스노틱스 — 신살(神煞) 계산 모듈. question_taxonomy.md 1절(연애운 질문)에서 확인했듯
 * "저 도화살 있나요?ㆍ홍염살 있나요?" 유형 질문이 실제로 자주 나오는데, saju.js가 쓰는
 * lunar-javascript(EightChar API)에는 이 신살들을 계산하는 메서드가 없다(2026-08-23 확인 —
 * 라이브러리에 'sn.*' 신살 상수가 있긴 하나 이는 택일용 황력(通勝) 신살이지 사주 명리학의
 * 도화ㆍ역마ㆍ화개ㆍ홍염살이 아님). 그래서 이 네 가지는 직접 구현한다 — 전부 결정론적
 * 룩업(삼합 그룹ㆍ일간표 기준)이라 correspondence.js/gunghap.js와 같은 원칙(LLM이 지어내지
 * 않고, 이 모듈이 계산한 값만 옮겨 쓰게 함)을 그대로 따른다.
 *
 * ============================================================
 * 계산 근거 문서화 (2026-08-23 리서치로 확인, sajustudy.com/namu.wiki/daysaju.com 교차확인)
 * ============================================================
 * - 도화살ㆍ역마살ㆍ화개살은 "삼합 그룹" 기준으로 정해지는 고정 지지 하나씩이다(correspondence.js
 *   의 JIJI_SAMHAP과 동일한 4개 그룹: 인오술/사유축/신자진/해묘미). 어느 지지를 기준으로 삼는지는
 *   "년지 또는 일지"라는 게 통설인데, 이 프로젝트는 **일지(日支, 오늘날 가장 널리 쓰이는 기준)를
 *   기본으로 삼는다** — 년지 기준은 고전식이라 부기 형태로만 같이 계산해서 보여준다.
 * - 홍염살은 삼합이 아니라 **일간(日干) 기준의 별도 표**다. 갑ㆍ경ㆍ임 일간은 지지 두 개를 함께
 *   보는 게 국내 실무에서 널리 쓰이는 버전(daysaju.com 확인) — 이 표를 채택.
 * - 넷 다 "판정 기준 지지가 사주 네 기둥(연월일시)의 지지 중 어디에라도 있으면 해당 신살이
 *   있다"고 본다. 이 프로젝트 고유의 v1 판정 기준이며, 명리학에 여러 신살 유파가 있는 것처럼
 *   절대적 정설로 제시하지 않는다(correlate.js/gunghap.js와 동일한 겸손 원칙).
 */
const { JIJI_SAMHAP } = require("./correspondence.js");

// 삼합 그룹(화/금/수/목, correspondence.js의 JIJI_SAMHAP 키와 동일)별 도화ㆍ역마ㆍ화개 지지.
const TAOHUA_BY_SAMHAP = { 화: "묘", 금: "오", 수: "유", 목: "자" };
const YEOKMA_BY_SAMHAP = { 화: "신", 금: "해", 수: "인", 목: "사" };
// 화개는 각 삼합 그룹 자신의 마지막 글자(고지庫地) — JIJI_SAMHAP 배열의 3번째 원소와 항상 같다.
const HWAGAE_BY_SAMHAP = Object.fromEntries(
  Object.entries(JIJI_SAMHAP).map(([el, members]) => [el, members[2]])
);

// 일간(한글 1글자) 기준 홍염살 지지 — 갑ㆍ경ㆍ임은 두 지지를 함께 봄(daysaju.com 실무 표).
const HONGYEOM_BY_GAN = {
  갑: ["오", "신"], 을: ["오"], 병: ["인"], 정: ["미"], 무: ["진"],
  기: ["진"], 경: ["신", "술"], 신: ["유"], 임: ["신", "자"], 계: ["신"],
};

const SHENSHA_MEANING = {
  도화살: "이성에게 매력적으로 비치는 기운을 상징함. 전통적으로는 다소 경계하는 시선으로 다뤄졌지만, 현대적으로는 인기ㆍ매력ㆍ사교성으로 긍정적으로 해석되는 경우도 많음.",
  역마살: "이동ㆍ변화의 기운을 상징함. 이사ㆍ출장ㆍ해외ㆍ이직처럼 한곳에 머무르지 않는 변화와 관련이 깊다고 전통적으로 여겨짐.",
  화개살: "학문ㆍ예술ㆍ종교 등 정신세계에 깊이 파고드는 기질을 상징함. 혼자만의 시간에서 오히려 집중력ㆍ창조성을 발휘하는 성향으로 전통적으로 해석됨.",
  홍염살: "도화살과 비슷하게 이성에게 인기 있는 매력을 상징하되, 좀 더 화려하고 표현이 강한 매력으로 구분되는 경우가 많음(전통 문헌에서는 여성 사주에서 더 자주 언급되었으나, 현대에는 남녀 모두에 적용해 해석함).",
};

function pillarZhis(sajuResult) {
  const zhis = [];
  Object.entries(sajuResult.pillars).forEach(([key, p]) => {
    if (p) zhis.push({ pillar: key, zhi: p.ganzhi_ko.slice(-1) });
  });
  return zhis;
}

function samhapElementOf(zhi) {
  const entry = Object.entries(JIJI_SAMHAP).find(([, members]) => members.includes(zhi));
  return entry ? entry[0] : null;
}

function findPillarsWithZhi(zhis, targetZhi) {
  return zhis.filter((z) => z.zhi === targetZhi).map((z) => z.pillar);
}

/**
 * saju.js의 computeSaju() 결과를 받아 신살(도화ㆍ역마ㆍ화개ㆍ홍염) 판정 결과를 만든다.
 * @param {object} sajuResult computeSaju()의 반환값
 * @returns {object} computed.json의 saju.shensha에 들어갈 구조
 */
function computeShensha(sajuResult) {
  const zhis = pillarZhis(sajuResult);
  const dayZhi = sajuResult.pillars.day.ganzhi_ko.slice(-1);
  const yearZhi = sajuResult.pillars.year.ganzhi_ko.slice(-1);
  const dayGan = sajuResult.pillars.day.ganzhi_ko.slice(0, 1);

  const dayGroup = samhapElementOf(dayZhi);
  const yearGroup = samhapElementOf(yearZhi);

  function judge(name, byGroupTable, group) {
    if (!group) return { present: false, basis: null, found_in: [] };
    const target = byGroupTable[group];
    const foundIn = findPillarsWithZhi(zhis, target);
    return { present: foundIn.length > 0, basis_zhi: target, found_in: foundIn };
  }

  const taohua = judge("도화살", TAOHUA_BY_SAMHAP, dayGroup);
  const yeokma = judge("역마살", YEOKMA_BY_SAMHAP, dayGroup);
  const hwagae = judge("화개살", HWAGAE_BY_SAMHAP, dayGroup);

  // 년지 기준(고전식) 부기 — 일지 기준과 다를 수 있어 참고용으로만 같이 제공.
  const taohuaByYear = judge("도화살", TAOHUA_BY_SAMHAP, yearGroup);
  const yeokmaByYear = judge("역마살", YEOKMA_BY_SAMHAP, yearGroup);
  const hwagaeByYear = judge("화개살", HWAGAE_BY_SAMHAP, yearGroup);

  const hongyeomTargets = HONGYEOM_BY_GAN[dayGan] || [];
  const hongyeomFoundIn = [...new Set(hongyeomTargets.flatMap((t) => findPillarsWithZhi(zhis, t)))];
  const hongyeom = { present: hongyeomFoundIn.length > 0, basis_zhi: hongyeomTargets, found_in: hongyeomFoundIn };

  return {
    basis_note: "일지(日支) 기준으로 판정(현대에 가장 널리 쓰이는 기준). 년지 기준(고전식)은 by_year_branch에 참고용으로 별도 제공 — 두 기준이 다르게 나올 수 있음.",
    taohua: { ...taohua, meaning: SHENSHA_MEANING.도화살 },
    yeokma: { ...yeokma, meaning: SHENSHA_MEANING.역마살 },
    hwagae: { ...hwagae, meaning: SHENSHA_MEANING.화개살 },
    hongyeom: { ...hongyeom, meaning: SHENSHA_MEANING.홍염살 },
    by_year_branch: { taohua: taohuaByYear, yeokma: yeokmaByYear, hwagae: hwagaeByYear },
  };
}

module.exports = { computeShensha, TAOHUA_BY_SAMHAP, YEOKMA_BY_SAMHAP, HWAGAE_BY_SAMHAP, HONGYEOM_BY_GAN };
