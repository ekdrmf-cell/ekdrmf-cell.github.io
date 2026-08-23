/*
 * 크로스노틱스 — 점성술 시너스트리(궁합) 계산 엔진.
 * 인수인계 문서(천지인운명관_다음세션_인수인계222.md "B. 궁합 계산 엔진 확장 — 점성술
 * 시너스트리")에서 지적된 구멍을 메운다: gunghap.js는 사주 궁합(일간ㆍ일지ㆍ년지ㆍ오행
 * 보완)만 계산했고, 점성술 쪽 궁합(두 사람의 네이탈 차트 행성끼리 어스펙트를 이루는지)은
 * 계산 자체가 없어서 관련 질문이 전부 "손님 본인 차트만으로 답변 가능한 부분"으로
 * 축소되고 있었다.
 *
 * ============================================================
 * 설계 근거 — 왜 "행성 쌍별 맞춤 해석문"을 쓰지 않았는가
 * ============================================================
 * 시너스트리는 전통적으로 "내 금성과 상대 화성이 트라인이면 강한 끌림" 같은 행성쌍별
 * 고유 해석이 있지만, 그걸 이 파일에 전부 손으로 써두면 (행성 10개 x 행성 10개 x 어스펙트
 * 5종 = 최대 500가지) 검증 안 된 조합을 지어내게 될 위험이 크다(0번 환각 차단 원칙 위반).
 * 대신 이미 검증되어 있는 astrology-correspondence.js의 BODY_MEANING(행성 상징)과
 * ASPECT_MEANING(어스펙트 상징)을 그대로 재사용해서, "이 손님의 A행성 의미 + 상대방의
 * B행성 의미 + 두 행성이 실제로 이루는 어스펙트의 의미"를 계산 결과로만 조합해 제공한다.
 * 이 세 조각을 자연스러운 문장으로 엮는 건 LLM(build_report.py)의 역할이지, 이 모듈이
 * "무슨 뜻인지"를 대신 지어내지 않는다 — correspondence.js/astrology-correspondence.js가
 * 이미 쓰고 있는 것과 동일한 패턴.
 *
 * ============================================================
 * 생시 미상일 때 계산하지 않는 이유
 * ============================================================
 * astrology.js는 생시를 모르면(unknownTime) 어센던트ㆍ하우스ㆍ네이탈 어스펙트 전체를 아예
 * 계산하지 않는다(정오로 대체한 임의 시각 기준으로 계산하면, 특히 달처럼 하루 약 13도씩
 * 움직이는 천체는 실제 위치와 몇 도씩 어긋나 있지도 않은 어스펙트를 있는 것처럼 보여줄 수
 * 있기 때문). 시너스트리는 두 차트를 겹쳐 보는 만큼 이 오차가 두 배로 개입될 수 있어,
 * 같은 원칙을 그대로 적용해 **두 사람 중 한쪽이라도 생시를 모르면 시너스트리 자체를
 * 계산하지 않는다**(부분적으로 안전한 천체만 골라 계산하는 절충안은 이 프로젝트가 아직
 * 검증하지 않은 별도 판단이라 쓰지 않음).
 */
const { BODY_MEANING, ASPECT_MEANING } = require("./astrology-correspondence.js");

// 메이저 어스펙트 5종 — astrology.js가 네이탈 어스펙트에 쓰는 것과 동일한 5종을 그대로
// 씀(마이너 어스펙트는 네이탈 쪽에서도 안 쓰므로 시너스트리에서도 확장하지 않음).
// orb(허용 오차)는 시너스트리 실무에서 흔히 쓰이는 범위(합/충 8도, 삼각/사각 7도, 육각
// 5도)를 따른 이 프로젝트의 v1 가설임 — gunghap.js WEIGHT 상수와 같은 성격의 문서화.
const ASPECT_DEFS = [
  { key: "conjunction", label: "합(컨정션)", angle: 0, orb: 8 },
  { key: "opposition", label: "대립(오퍼지션)", angle: 180, orb: 8 },
  { key: "trine", label: "삼각(트라인)", angle: 120, orb: 7 },
  { key: "square", label: "사각(스퀘어)", angle: 90, orb: 7 },
  { key: "sextile", label: "육각(섹스타일)", angle: 60, orb: 5 },
];

// 시너스트리에서 관계 궁합에 실질적 비중이 크다고 널리 통용되는 5개 천체(태양ㆍ달ㆍ금성ㆍ
// 화성ㆍ토성) — 계산 자체는 CORE_BODIES 전체(외행성 포함)에 대해 다 하되, highlights에
// 먼저 노출할 우선순위만 이걸로 정렬한다(리포트 분량 통제, correlate.js가 이미 쓰는
// "우선순위로 추리는" 방식과 동일).
const PRIORITY_BODIES = ["태양", "달", "금성", "화성", "토성"];

function angleDiff(deg1, deg2) {
  let d = Math.abs(deg1 - deg2) % 360;
  if (d > 180) d = 360 - d;
  return d;
}

function findAspect(deg1, deg2) {
  const diff = angleDiff(deg1, deg2);
  let best = null;
  for (const def of ASPECT_DEFS) {
    const delta = Math.abs(diff - def.angle);
    if (delta <= def.orb && (!best || delta < best.delta)) {
      best = { def, delta };
    }
  }
  if (!best) return null;
  return { type: best.def.label, orb: Math.round(best.delta * 10) / 10 };
}

/**
 * 두 사람의 네이탈 차트(computeAstrology() 결과)를 비교해 시너스트리 어스펙트를 계산한다.
 * @param {object} astroA 손님 본인의 computeAstrology() 결과
 * @param {object} astroB 상대방의 computeAstrology() 결과
 * @returns {object|null} 둘 중 하나라도 없거나 생시를 모르면 null(위 "생시 미상" 설계 근거 참고)
 */
function computeSynastry(astroA, astroB) {
  if (!astroA || !astroB) return null;
  // unknown_time_note는 생시를 모를 때만 채워짐(astrology.js) — 둘 중 하나라도 있으면 중단.
  if (astroA.unknown_time_note || astroB.unknown_time_note) {
    return {
      aspects: [],
      skipped_reason: "두 분 중 한 분 이상 태어난 시간을 몰라, 정확한 시너스트리 계산을 생략함(생시 미상 시 달 등 " +
        "빠르게 움직이는 천체의 위치가 부정확해질 수 있어 이 프로젝트는 계산 자체를 하지 않음).",
    };
  }

  const aspects = [];
  (astroA.planets || []).forEach((pA) => {
    (astroB.planets || []).forEach((pB) => {
      if (pA.ecliptic_longitude == null || pB.ecliptic_longitude == null) return;
      const found = findAspect(pA.ecliptic_longitude, pB.ecliptic_longitude);
      if (!found) return;
      aspects.push({
        person_a_body: pA.body,
        person_b_body: pB.body,
        type: found.type,
        orb: found.orb,
        person_a_body_meaning: BODY_MEANING[pA.body] || null,
        person_b_body_meaning: BODY_MEANING[pB.body] || null,
        aspect_meaning: ASPECT_MEANING[found.type] || null,
        is_priority: PRIORITY_BODIES.includes(pA.body) && PRIORITY_BODIES.includes(pB.body),
      });
    });
  });

  // 우선순위 조합(태양ㆍ달ㆍ금성ㆍ화성ㆍ토성끼리) 먼저, 그 안에서는 orb(오차)가 좁아 더
  // 정확하게 걸린 어스펙트부터 — build_report.py가 highlights를 추릴 때 앞쪽만 써도
  // 되도록 미리 정렬해둔다.
  aspects.sort((a, b) => {
    if (a.is_priority !== b.is_priority) return a.is_priority ? -1 : 1;
    return a.orb - b.orb;
  });

  return {
    aspects,
    skipped_reason: null,
    note:
      "두 사람의 실제 네이탈 차트 행성 위치(ecliptic_longitude)를 비교해 계산한 시너스트리 " +
      "어스펙트임(지어낸 것이 아니라 이 두 분의 실제 계산값). 행성ㆍ어스펙트 의미는 서양 " +
      "점성술의 표준 상징 체계를 참고한 것이며 확정적 예언이 아님. 어스펙트 개수가 많을 " +
      "수 있으므로 태양ㆍ달ㆍ금성ㆍ화성ㆍ토성 사이의 조합(is_priority: true)을 우선 언급할 것.",
  };
}

module.exports = { computeSynastry, ASPECT_DEFS };
