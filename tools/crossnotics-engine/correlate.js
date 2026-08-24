/*
 * 크로스노틱스 — 체계 간 교차상관(cross-correlation) 알고리즘.
 * 백서 3단계("각 체계별 수학적ㆍ통계적 계산 엔진을 독립 구축")의 핵심 취지를 구현하는
 * 신규 모듈. 사주(오행 5분류)ㆍ점성술(4원소)ㆍ타로(카드별 원소 상응)를 공통 좌표계인
 * "4원소"로 정규화한 뒤, 결정론적 규칙으로 일치도/보완점을 계산한다.
 *
 * LLM은 이 모듈이 계산한 결과를 문장으로 번역만 한다 — "어디서 체계가 일치하는가"를
 * LLM이 스스로 찾게 하지 않는다(환각 방지 핵심 설계, 계획서 4번 참고).
 *
 * ============================================================
 * 매핑 근거 문서화 (오행 5분류 → 4원소, 5→4라 필연적으로 하나는 겹침)
 * ============================================================
 * - 화(火) → 불(Fire): 문자 그대로 "불" — 직접 대응, 이견 없음.
 * - 수(水) → 물(Water): 문자 그대로 "물" — 직접 대응, 이견 없음.
 * - 목(木) → 바람(Air): 나무의 생장ㆍ확장ㆍ상승하는 성질을 바람의 움직임ㆍ확산 성질과
 *   대응시키는 동서양 융합 해석에서 흔히 쓰이는 매핑을 채택.
 * - 토(土) → 땅(Earth): 문자 그대로 "흙/땅" — 직접 대응.
 * - 금(金) → 땅(Earth): 금속은 광물로서 땅에서 나오고, 견고함ㆍ구조라는 속성이 토(Earth)와
 *   겹친다고 보고 땅에 편입. (대안으로 "바람"에 배정하는 해석도 있으나, 여기서는 "물성의
 *   기원"을 기준으로 삼음 — 이 프로젝트 고유의 v1 가설이며, 절대적 정설로 제시하지 않는다.
 *   추후 실제 리포트 검수 과정에서 위화감이 크면 재조정 가능.)
 * → 결과적으로 "땅"만 토+금 두 개의 오행을 받고, 나머지 3원소는 1:1 대응.
 *
 * 타로(메이저 아르카나) → 4원소: Golden Dawn 계열 카발라 타로 전통에서 각 카드에 별자리ㆍ
 * 행성을 배정하는 관행을 단순화해, 별자리가 배정된 카드는 그 별자리의 원소를, 행성이
 * 배정된 카드는 통상적으로 연상되는 원소를 채택했다(예: 화성=불, 토성=땅). 여러 유파 중
 * 하나를 골라 단순화한 것이라 "절대적 해석"이 아니라 "이 프로젝트의 참고 상응표"임을
 * LLM 프롬프트에도 명시한다.
 */

const OHENG_TO_ELEMENT = { 화: "불", 수: "물", 목: "바람", 토: "땅", 금: "땅" };

const MAJOR_ARCANA_ELEMENT = {
  "0. 광대": "바람", "1. 마법사": "바람", "2. 여사제": "물", "3. 여황제": "땅",
  "4. 황제": "불", "5. 교황": "땅", "6. 연인": "바람", "7. 전차": "물",
  "8. 힘": "불", "9. 은둔자": "땅", "10. 운명의 수레바퀴": "불", "11. 정의": "바람",
  "12. 매달린 사람": "물", "13. 죽음": "물", "14. 절제": "불", "15. 악마": "땅",
  "16. 탑": "불", "17. 별": "바람", "18. 달": "물", "19. 태양": "불",
  "20. 심판": "불", "21. 세계": "땅",
};

// 2026-08-21 마이너 아르카나 56장 추가 시 발견ㆍ수정: 이 매핑에 없는 카드가 뽑히면
// tarotToElementVector()의 `if (!el) return;`에서 조용히 스킵돼 교차분석 계산에서 빠지는
// 버그가 될 뻔함(마이너 아르카나 56장이 새로 생겼는데 이 표를 안 넓히면 그 카드들만 원소
// 계산에서 누락됨). 마이너 아르카나는 수트(문양)별 원소가 타로 전통에서 이미 확립돼 있어
// 지어내는 게 아님: 완드=불, 컵=물, 소드=바람, 펜타클=땅.
const MINOR_SUIT_ELEMENT = { "완드": "불", "컵": "물", "소드": "바람", "펜타클": "땅" };
function minorArcanaElement(cardName) {
  const suit = cardName.split(" ")[0];
  return MINOR_SUIT_ELEMENT[suit] || null;
}

const ELEMENTS = ["불", "땅", "바람", "물"];

function normalize(countObj) {
  const total = Object.values(countObj).reduce((a, b) => a + b, 0);
  if (total === 0) return ELEMENTS.reduce((acc, e) => ({ ...acc, [e]: 0 }), {});
  return ELEMENTS.reduce((acc, e) => ({ ...acc, [e]: (countObj[e] || 0) / total }), {});
}

function sajuToElementVector(sajuResult) {
  const elementCount = { 불: 0, 땅: 0, 바람: 0, 물: 0 };
  Object.entries(sajuResult.oheng_count).forEach(([oheng, count]) => {
    const el = OHENG_TO_ELEMENT[oheng];
    if (el) elementCount[el] += count;
  });
  return normalize(elementCount);
}

function astrologyToElementVector(astrologyResult) {
  return normalize(astrologyResult.element_count);
}

function tarotToElementVector(tarotResult) {
  const elementCount = { 불: 0, 땅: 0, 바람: 0, 물: 0 };
  tarotResult.draws.forEach((d) => {
    const el = MAJOR_ARCANA_ELEMENT[d.card_name] || minorArcanaElement(d.card_name);
    if (!el) return;
    // 역방향은 해당 원소 에너지가 절반만 발현된다고 보고 가중치 0.5 적용(v1 가설, 문서화됨)
    const weight = d.orientation === "역방향" ? 0.5 : 1;
    elementCount[el] += weight;
  });
  return normalize(elementCount);
}

function cosineSimilarity(vecA, vecB) {
  const dot = ELEMENTS.reduce((s, e) => s + vecA[e] * vecB[e], 0);
  const magA = Math.sqrt(ELEMENTS.reduce((s, e) => s + vecA[e] ** 2, 0));
  const magB = Math.sqrt(ELEMENTS.reduce((s, e) => s + vecB[e] ** 2, 0));
  if (magA === 0 || magB === 0) return 0;
  return dot / (magA * magB);
}

function topElement(vec) {
  return Object.entries(vec).sort((a, b) => b[1] - a[1])[0][0];
}

/**
 * @param {object} params {saju, astrology, tarot} — 각 엔진의 computeXxx() 결과(선택된 티어에
 *   따라 saju/astrology/tarot 중 일부만 있을 수 있음 — Step1 싱글 티어는 1개만 옴).
 * @returns {object} computed.json의 "correlation" 필드 — LLM은 이 결과만 문장으로 번역한다.
 */
function computeCorrelation({ saju, astrology, tarot }) {
  const vectors = {};
  if (saju) vectors.saju = sajuToElementVector(saju);
  if (astrology) vectors.astrology = astrologyToElementVector(astrology);
  if (tarot) vectors.tarot = tarotToElementVector(tarot);

  const systemKeys = Object.keys(vectors);
  if (systemKeys.length === 0) {
    throw new Error("최소 1개 이상의 체계 결과가 필요함");
  }

  // 단일 체계만 있으면(Step1) 교차상관 자체가 불가능 — 그 체계의 원소 분포만 반환
  if (systemKeys.length === 1) {
    const key = systemKeys[0];
    return {
      mode: "single_system",
      dominant_axis: topElement(vectors[key]),
      element_vectors: vectors,
      agreement_score: null,
      systems_agreeing: [],
      complementary_points: [],
      note: "단일 체계 진단(Step1)이라 교차상관 계산 대상이 아님 — 이 체계 자체의 원소 분포만 제공.",
    };
  }

  // 평균 벡터 = "통합 원소 분포" (백서의 "정보의 결합도" 값을 실제 수치로 구현)
  const combined = ELEMENTS.reduce((acc, e) => {
    const avg = systemKeys.reduce((s, k) => s + vectors[k][e], 0) / systemKeys.length;
    return { ...acc, [e]: avg };
  }, {});
  const dominantAxis = topElement(combined);

  // 체계 쌍별 코사인 유사도 → 어떤 체계끼리 일치하는지 판정(top1 원소가 같은 쌍)
  const pairs = [];
  for (let i = 0; i < systemKeys.length; i++) {
    for (let j = i + 1; j < systemKeys.length; j++) {
      const a = systemKeys[i], b = systemKeys[j];
      const sim = cosineSimilarity(vectors[a], vectors[b]);
      pairs.push({ pair: [a, b], similarity: Math.round(sim * 1000) / 1000, same_top_element: topElement(vectors[a]) === topElement(vectors[b]) });
    }
  }
  const systemsAgreeing = pairs.filter((p) => p.same_top_element).flatMap((p) => p.pair);
  const uniqueAgreeing = [...new Set(systemsAgreeing)];

  // 전체 일치도 점수 = 쌍별 코사인 유사도 평균(0~1)
  const agreementScore = Math.round((pairs.reduce((s, p) => s + p.similarity, 0) / pairs.length) * 1000) / 1000;

  // 보완점: 한 체계에서 강한(0.35 이상) 원소가 다른 체계에서 거의 없는(0.1 이하) 경우
  const complementaryPoints = [];
  ELEMENTS.forEach((el) => {
    const strongIn = systemKeys.filter((k) => vectors[k][el] >= 0.35);
    const weakIn = systemKeys.filter((k) => vectors[k][el] <= 0.1);
    if (strongIn.length > 0 && weakIn.length > 0) {
      complementaryPoints.push({ element: el, strong_in: strongIn, weak_in: weakIn });
    }
  });

  return {
    mode: "cross_correlation",
    dominant_axis: dominantAxis,
    element_vectors: vectors,
    combined_vector: combined,
    agreement_score: agreementScore,
    pairwise_similarity: pairs,
    systems_agreeing: uniqueAgreeing,
    complementary_points: complementaryPoints,
    mapping_note: "오행→4원소, 타로카드→4원소 매핑은 이 서비스가 채택한 하나의 상응표(파일 상단 주석 참고)이며, 절대적 정설이 아님을 리포트 톤에도 반영할 것.",
  };
}

module.exports = { computeCorrelation, OHENG_TO_ELEMENT, MAJOR_ARCANA_ELEMENT };
