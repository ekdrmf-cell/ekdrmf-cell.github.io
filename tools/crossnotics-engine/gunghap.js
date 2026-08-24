/*
 * 크로스노틱스 — 사주 궁합(宮合) 계산 엔진.
 * CROSSNOTICS_HANDOFF.md "-7번 업데이트"에서 지적된 구멍(상대방 정보가 없어 궁합 질문이
 * 전부 "redirected"로만 처리됨)을 메우는 신규 모듈. 상대방 생년월일시가 주어지면 saju.js로
 * 상대방의 사주도 계산한 뒤, 두 사람의 **일간(日干) 오행 관계 + 일지(日支) 지지 관계 +
 * 년지(年支) 띠 관계 + 오행 상호보완**을 결정론적 규칙으로 채점한다 — LLM이 "궁합이 좋다/
 * 나쁘다"를 스스로 판단하지 않고, 이 모듈이 이미 계산한 점수ㆍ근거를 문장으로 번역만 하게
 * 한다(correlate.js가 체계 간 교차상관을 다루는 것과 동일한 설계 철학).
 *
 * ============================================================
 * 채점 근거 문서화 (correlate.js 관행과 동일하게, 이 프로젝트의 v1 가설임을 명시)
 * ============================================================
 * 명리학에는 궁합을 보는 여러 유파ㆍ기법(오행 궁합, 십신 궁합, 신살 궁합, 납음 궁합 등)이
 * 있고 "정답"이라 부를 단일 공식은 없다. 이 모듈은 검색 리서치(2026-08-23)로 확인한 가장
 * 널리 통용되는 3가지 기준 — ①일주(日柱)가 결혼궁을 나타내므로 일간ㆍ일지가 핵심,
 * ②지지의 합(合)은 잘 맞음ㆍ충(沖)/형(刑)은 갈등 요소, ③서로 부족한 오행을 채워주는지 —
 * 를 결합해 하나의 점수로 만든 것이다. 가중치(아래 WEIGHT 상수)는 "일주가 가장 중요하다"는
 * 통설을 반영해 일간ㆍ일지에 가장 큰 비중을 두고, 년지(띠) 관계와 오행 보완은 보조 지표로
 * 낮게 둔 이 프로젝트 고유의 배점이다 — 절대적 정설로 제시하지 않으며, 리포트 톤에도
 * "여러 궁합 판단 기준 중 하나"임을 반영해야 한다(build_report.py SYSTEM_PROMPT에 명시).
 *
 * ============================================================
 * relationshipType(관계 유형) — 왜 필요한가 (2026-08-23 추가)
 * ============================================================
 * 크로스노틱스는 손님이 어떤 질문을 남길지 미리 제한하지 않는다(-7번 원칙: "질문 입력 자체는
 * 절대 막지 않는다"). 궁합 질문도 마찬가지로 연인ㆍ배우자만 묻는 게 아니라 동업자ㆍ가족과의
 * 궁합을 묻는 손님도 실제로 있을 수 있다 — 그런데 위 채점 로직(일지=배우자 자리, 비화=단순
 * "성향이 비슷함")은 연애ㆍ결혼 관계를 전제로 설계된 것이라, 그대로 동업ㆍ가족 관계에 쓰면
 * "배우자 자리" 같은 표현이 안 맞거나, 명리학적으로 실제로 다르게 해석해야 할 지점(예: 동업
 * 궁합에서 일간 비화=재물 경쟁 위험)을 놓치게 된다. 점수 산출 공식(WEIGHT)은 그대로 두고
 * (관계 유형별로 가중치 자체를 다르게 매길 만한 명확한 학설적 근거까지는 확인 못 함),
 * **해석 문구(highlights)만 관계 유형별로 다르게** 만들어 "질문에 실제로 답할 수 있는
 * 수준"까지 맞춘다.
 */
const { computeSaju } = require("./saju.js");
const { ohengRelation, jijiRelation, ZODIAC } = require("./correspondence.js");

const WEIGHT = {
  // 오행 상생은 목→화→토→금→수→목의 단방향 순환이라, 서로 다른 두 오행 사이엔 항상 한쪽
  // 방향의 상생만 성립한다("서로가 서로를 생하는" 완전한 상호 상생은 이론상 존재하지 않음).
  ILGAN_SANGSAENG_HANJJOK: 18, // 일간끼리 상생 관계(한쪽이 다른 쪽을 생함)
  ILGAN_BIHWA: 8, // 일간이 같은 오행(비화) — 성향은 비슷하나 특별히 좋지도 나쁘지도 않음
  ILGAN_SANGGEUK: -20, // 일간끼리 상극
  ILJI_YUKHAP: 20,
  ILJI_SAMHAP: 26,
  ILJI_YUKCHUNG: -26,
  ILJI_HYEONG: -16,
  ILJI_YUKPA: -8,
  ILJI_YUKHAE: -10,
  YEONJI_SAMHAP: 12,
  YEONJI_YUKHAP: 8,
  YEONJI_YUKCHUNG: -12,
  OHENG_BOWAN_EACH: 5, // 한쪽에 부족한 오행을 상대가 채워줄 때마다(최대 아래 CAP까지)
  OHENG_BOWAN_CAP: 15,
};

const BASE_SCORE = 50; // 기준점 — 위 가감 요소가 없으면 "중립"으로 봄

const RELATIONSHIP_TYPES = ["romantic", "business", "family"];
const RELATIONSHIP_LABEL = { romantic: "연인ㆍ부부", business: "동업ㆍ사업 파트너", family: "가족ㆍ기타 관계" };

// 관계 유형별 해석 문구. 점수 산출 공식(WEIGHT)은 관계 유형과 무관하게 동일하게 적용하고
// (관계 유형별로 가중치 자체를 다르게 매길 학설적 근거까지는 확인하지 못함 — 파일 상단
// "relationshipType" 주석 참고), highlights 문구만 관계 유형에 맞게 바꾼다.
const MESSAGES = {
  ilgan_bihwa: {
    romantic: (a) => `두 분의 일간이 똑같이 ${a} 기운이라 성향이 비슷한 편으로 봅니다.`,
    business: (a) => `두 분의 일간이 똑같이 ${a} 기운이라 사업 스타일이나 강점이 비슷한 편으로 봅니다. 다만 명리학에서는 같은 오행끼리는 자원ㆍ주도권을 두고 경쟁하는 비겁(比劫) 관계로 흐르기 쉽다고 보는 시각이 있어, 역할과 지분을 명확히 나누는 게 특히 중요한 조합입니다.`,
    family: (a) => `두 분의 일간이 똑같이 ${a} 기운이라 기질이나 가치관이 비슷한 편으로 봅니다.`,
  },
  ilgan_sangsaeng: {
    romantic: (dir) => `일간 오행 관계가 ${dir} 방향으로 상생이라, 한쪽이 다른 쪽을 도와주는 흐름으로 봅니다.`,
    business: (dir) => `일간 오행 관계가 ${dir} 방향으로 상생이라, 한쪽이 다른 쪽을 이끌어주거나 지원하는 멘토ㆍ서포터 구도로 보기 좋은 조합입니다.`,
    family: (dir) => `일간 오행 관계가 ${dir} 방향으로 상생이라, 한쪽이 다른 쪽을 챙겨주는 흐름으로 봅니다.`,
  },
  ilgan_sanggeuk: {
    romantic: (a, b) => `일간 오행이 서로 상극(${a}↔${b}) 관계라 초반엔 부딪히는 지점이 있을 수 있지만, 상극도 서로를 긴장시켜 발전시키는 자극제로 보는 시각도 있습니다.`,
    business: (a, b) => `일간 오행이 서로 상극(${a}↔${b}) 관계라 사업 방향이나 의사결정에서 주도권 다툼ㆍ의견 충돌이 생기기 쉽다고 봅니다. 다만 서로 다른 관점이 부딪히며 시너지를 내는 경우도 있어, 역할과 의사결정 권한을 미리 명확히 나누는 게 중요합니다.`,
    family: (a, b) => `일간 오행이 서로 상극(${a}↔${b}) 관계라 가치관 차이로 부딪히는 지점이 있을 수 있습니다.`,
  },
  ilji_label: {
    romantic: "배우자 자리로 보는 일지",
    business: "함께 지내는 생활 리듬을 보는 일지",
    family: "함께 지내는 생활 리듬을 보는 일지",
  },
};

function pick(bucket, type) {
  return MESSAGES[bucket][type] || MESSAGES[bucket].romantic;
}

function dayZhiOf(sajuResult) {
  return sajuResult.pillars.day.ganzhi_ko.slice(-1);
}
function yearZhiOf(sajuResult) {
  return sajuResult.pillars.year.ganzhi_ko.slice(-1);
}

function scoreLabel(score) {
  if (score >= 80) return "매우 좋음";
  if (score >= 65) return "좋은 편";
  if (score >= 45) return "무난함(장단점 공존)";
  if (score >= 30) return "노력이 필요함";
  return "상극 요소가 뚜렷함(그렇다고 관계가 불가능하다는 뜻은 아님)";
}

/**
 * 두 사람의 사주 궁합을 계산한다.
 * @param {object} sajuA computeSaju() 결과 (예: 손님 본인)
 * @param {object} sajuB computeSaju() 결과 (예: 상대방)
 * @param {string} relationshipType "romantic"(기본값, 연인ㆍ부부) | "business"(동업ㆍ사업
 *   파트너) | "family"(가족ㆍ기타). 점수 산출 공식은 동일하고 해석 문구만 달라진다(파일
 *   상단 "relationshipType" 주석 참고).
 * @returns {object} computed.json의 "gunghap" 필드 — LLM은 이 결과만 문장으로 번역한다.
 */
function computeGunghap(sajuA, sajuB, relationshipType = "romantic") {
  const type = RELATIONSHIP_TYPES.includes(relationshipType) ? relationshipType : "romantic";
  const highlights = [];
  let score = BASE_SCORE;

  // 1. 일간(日干) 오행 관계 — 결혼궁인 일주의 핵심, 가장 큰 비중.
  const ilganA = sajuA.pillars.day.gan_oheng;
  const ilganB = sajuB.pillars.day.gan_oheng;
  const ilganRelation = ohengRelation(ilganA, ilganB);
  let ilganPoints = 0;
  if (ilganRelation === "비화(같은 오행)") {
    ilganPoints = WEIGHT.ILGAN_BIHWA;
    highlights.push(pick("ilgan_bihwa", type)(ilganA));
  } else if (ilganRelation.startsWith("상생")) {
    ilganPoints = WEIGHT.ILGAN_SANGSAENG_HANJJOK;
    highlights.push(pick("ilgan_sangsaeng", type)(ilganRelation === "상생(내가 생함)" ? "A→B" : "B→A"));
  } else if (ilganRelation.startsWith("상극")) {
    ilganPoints = WEIGHT.ILGAN_SANGGEUK;
    highlights.push(pick("ilgan_sanggeuk", type)(ilganA, ilganB));
  }
  score += ilganPoints;

  // 2. 일지(日支) 관계 — romantic이면 배우자 자리, business/family는 생활 리듬을 보는
  // 자리로 재해석(관계 유형과 무관하게 합ㆍ충ㆍ형ㆍ파ㆍ해 판정 자체는 동일).
  const iljiLabel = pick("ilji_label", type);
  const iljiA = dayZhiOf(sajuA);
  const iljiB = dayZhiOf(sajuB);
  const ilji = jijiRelation(iljiA, iljiB);
  let iljiPoints = 0;
  if (ilji.samhap) {
    iljiPoints += WEIGHT.ILJI_SAMHAP;
    highlights.push(`일지(${iljiLabel})끼리 삼합(${ilji.samhap.element} 기운)을 이뤄 강하게 끌어당기는 조합으로 봅니다.`);
  } else if (ilji.yukhap) {
    iljiPoints += WEIGHT.ILJI_YUKHAP;
    highlights.push(`일지(${iljiLabel})끼리 육합(${ilji.yukhap.pair}, ${ilji.yukhap.element} 기운)을 이뤄 서로 잘 맞는 조합으로 봅니다.`);
  }
  if (ilji.yukchung) {
    iljiPoints += WEIGHT.ILJI_YUKCHUNG;
    highlights.push(`일지(${iljiLabel})끼리 충(沖) 관계라 ${type === "business" ? "업무 방식이나 결정 속도" : "생활 방식이나 의견"} 차이로 부딪힐 소지가 있다고 봅니다.`);
  }
  if (ilji.hyeong) {
    iljiPoints += WEIGHT.ILJI_HYEONG;
    highlights.push(`일지(${iljiLabel})끼리 ${ilji.hyeong} 관계가 있어 신경전ㆍ마찰이 생기기 쉬운 조합으로 봅니다.`);
  }
  if (ilji.yukpa) {
    iljiPoints += WEIGHT.ILJI_YUKPA;
    highlights.push(`일지(${iljiLabel})끼리 파(破) 관계라 ${type === "business" ? "함께 벌인 일" : "계획한 일"}이 지연되거나 어긋나기 쉬운 기운이 있다고 봅니다.`);
  }
  if (ilji.yukhae) {
    iljiPoints += WEIGHT.ILJI_YUKHAE;
    highlights.push(`일지(${iljiLabel})끼리 해(害) 관계라 사소한 오해나 구설이 생기기 쉬운 조합으로 봅니다.`);
  }
  score += iljiPoints;

  // 3. 년지(年支) 띠 관계 — 흔히 말하는 "띠 궁합", 보조 지표.
  const yeonjiA = yearZhiOf(sajuA);
  const yeonjiB = yearZhiOf(sajuB);
  const yeonji = jijiRelation(yeonjiA, yeonjiB);
  let yeonjiPoints = 0;
  const zodiacA = ZODIAC[yeonjiA];
  const zodiacB = ZODIAC[yeonjiB];
  if (yeonji.samhap) {
    yeonjiPoints += WEIGHT.YEONJI_SAMHAP;
    highlights.push(`띠로 보면 ${zodiacA.animal}띠와 ${zodiacB.animal}띠가 삼합 그룹에 속해 전통적으로 궁합이 좋다고 여겨지는 조합입니다.`);
  } else if (yeonji.yukhap) {
    yeonjiPoints += WEIGHT.YEONJI_YUKHAP;
    highlights.push(`띠로 보면 ${zodiacA.animal}띠와 ${zodiacB.animal}띠가 육합 관계라 전통적으로 잘 맞는다고 여겨지는 조합입니다.`);
  }
  if (yeonji.yukchung) {
    yeonjiPoints += WEIGHT.YEONJI_YUKCHUNG;
    highlights.push(`띠로 보면 ${zodiacA.animal}띠와 ${zodiacB.animal}띠가 충 관계라 전통적으로 "원진ㆍ상충" 궁합으로 언급되는 조합입니다.`);
  }
  score += yeonjiPoints;

  // 4. 오행 상호보완 — 한쪽에 부족한 오행을 상대가 채워주는지.
  let bowanPoints = 0;
  const bowanNotes = [];
  (sajuA.missing_elements || []).forEach((el) => {
    if ((sajuB.dominant_elements || []).includes(el)) {
      bowanPoints += WEIGHT.OHENG_BOWAN_EACH;
      bowanNotes.push(`본인에게 부족한 ${el} 기운을 상대방이 우세하게 갖고 있어 서로 보완되는 지점입니다.`);
    }
  });
  (sajuB.missing_elements || []).forEach((el) => {
    if ((sajuA.dominant_elements || []).includes(el)) {
      bowanPoints += WEIGHT.OHENG_BOWAN_EACH;
      bowanNotes.push(`상대방에게 부족한 ${el} 기운을 본인이 우세하게 갖고 있어 서로 보완되는 지점입니다.`);
    }
  });
  bowanPoints = Math.min(bowanPoints, WEIGHT.OHENG_BOWAN_CAP);
  highlights.push(...bowanNotes);
  score += bowanPoints;

  score = Math.max(0, Math.min(100, Math.round(score)));

  return {
    score,
    score_label: scoreLabel(score),
    relationship_type: type,
    relationship_type_label: RELATIONSHIP_LABEL[type],
    ilgan_relation: { a: ilganA, b: ilganB, relation: ilganRelation, points: ilganPoints },
    ilji_relation: { a: iljiA, b: iljiB, ...ilji, points: iljiPoints },
    yeonji_zodiac_relation: {
      a: { zhi: yeonjiA, animal: zodiacA.animal },
      b: { zhi: yeonjiB, animal: zodiacB.animal },
      ...yeonji,
      points: yeonjiPoints,
    },
    oheng_complement_points: bowanPoints,
    highlights,
    methodology_note:
      "일간(핵심 기질)ㆍ일지(생활 리듬)ㆍ년지(띠)ㆍ오행 상호보완 4가지를 종합한 이 " +
      "서비스의 궁합 채점 기준이며, 명리학에 여러 궁합 유파가 있는 것처럼 절대적 정답이 " +
      "아니라 참고 지표 중 하나임(파일 상단 주석 참고). 점수 산출 공식은 관계 유형과 무관하게 " +
      "동일하고, 해석 문구만 관계 유형에 맞게 조정됨.",
    // family(가족) 관계는 연인ㆍ동업처럼 "선택해서 맺는" 관계가 아니므로, 점수를 "잘 맞는지
    // 아닌지 판정"으로 읽지 않도록 안내 문구를 별도로 붙인다.
    disclaimer: type === "family"
      ? "가족 관계는 스스로 선택해서 맺는 관계가 아니므로, 이 점수는 '잘 맞는 관계인지' 판정하는 " +
        "용도가 아니라 서로의 기질 차이를 이해하는 참고 자료로 활용하시길 권합니다."
      : null,
  };
}

/**
 * intake의 원본 생년월일 입력(computeSaju 이전 raw input)을 받아 상대방 사주까지 계산한 뒤
 * 궁합을 산출하는 편의 함수 — run.js가 이걸 호출한다.
 * @param {object} sajuA 이미 계산된 손님 본인의 computeSaju() 결과
 * @param {object} partnerInput computeSaju()에 넣을 상대방 raw 입력 {year, month, day, hour, unknownTime, gender, calendarType, isLeapMonth}
 */
function computeGunghapFromPartnerInput(sajuA, partnerInput, relationshipType = "romantic") {
  const sajuB = computeSaju(partnerInput);
  return { partner_saju: sajuB, gunghap: computeGunghap(sajuA, sajuB, relationshipType) };
}

module.exports = { computeGunghap, computeGunghapFromPartnerInput, WEIGHT, RELATIONSHIP_TYPES };
