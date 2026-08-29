/*
 * 크로스노틱스 — 서양 점성술(네이탈 차트) 계산 엔진.
 * circular-natal-horoscope-js(0xStarcat, Unlicense, npm v1.1.0 — 최종 배포 2022-04,
 * 내부적으로 실제 천체력 계산을 하므로 유지보수 중단과 무관하게 계산 정확도는 그대로 유지됨.
 * 1990-05-14 등 알려진 생일로 태양궁 계산을 대조 검증함)로 실제 행성 위치ㆍ하우스ㆍ어스펙트를
 * 계산한다. 여기서도 지어내는 부분 없이 라이브러리 산출값을 한국어로 옮기기만 한다.
 */
const { Origin, Horoscope } = require("circular-natal-horoscope-js");
const { buildAstroCorrespondence } = require("./astrology-correspondence.js");

const SIGN_KO = {
  Aries: { label: "양자리", element: "불" },
  Taurus: { label: "황소자리", element: "땅" },
  Gemini: { label: "쌍둥이자리", element: "바람" },
  Cancer: { label: "게자리", element: "물" },
  Leo: { label: "사자자리", element: "불" },
  Virgo: { label: "처녀자리", element: "땅" },
  Libra: { label: "천칭자리", element: "바람" },
  Scorpio: { label: "전갈자리", element: "물" },
  Sagittarius: { label: "사수자리", element: "불" },
  Capricorn: { label: "염소자리", element: "땅" },
  Aquarius: { label: "물병자리", element: "바람" },
  Pisces: { label: "물고기자리", element: "물" },
};

const BODY_KO = {
  sun: "태양", moon: "달", mercury: "수성", venus: "금성", mars: "화성",
  jupiter: "목성", saturn: "토성", uranus: "천왕성", neptune: "해왕성",
  pluto: "명왕성", chiron: "키론", sirius: "시리우스",
};

const HOUSE_NUM_KO = {
  First: 1, Second: 2, Third: 3, Fourth: 4, Fifth: 5, Sixth: 6,
  Seventh: 7, Eighth: 8, Ninth: 9, Tenth: 10, Eleventh: 11, Twelfth: 12,
};

// 2026-08-30 추가 — "하우스 지배행성"(house ruler) 개념: 지금까지는 computed.json에 이
// 값이 아예 없어서 LLM이 검증 안 된 일반 점성술 지식으로 스스로 추론해 썼다(예: "화성이
// 6하우스를 이끈다"). 이 하우스가 어떤 별자리인지는 whole-sign 하우스제(아래 houseSystem
// 참고)에서 이미 계산되고 있었으니, 그 별자리의 전통 지배행성만 표준 매핑으로 붙이면 코드로
// 검증 가능한 값이 된다(1번 규칙 — 지어내지 않기 — 을 이 개념에도 적용). 현대 점성술은
// 일부 별자리에 외행성 공동지배(예: 물병자리=천왕성)를 추가로 인정하지만, "주인은 OO입니다"
// 식 단일 답을 요구하는 리포트 문체에 맞춰 전통 단일 지배행성 하나만 채택한다(오행→4원소
// 매핑과 같은 성격의 "이 프로젝트가 채택한 하나의 기준" — 정설로 제시하지 않음).
const SIGN_RULER_KO = {
  "양자리": "화성", "황소자리": "금성", "쌍둥이자리": "수성", "게자리": "달",
  "사자자리": "태양", "처녀자리": "수성", "천칭자리": "금성", "전갈자리": "화성",
  "사수자리": "목성", "염소자리": "토성", "물병자리": "토성", "물고기자리": "목성",
};

const ASPECT_KO = {
  conjunction: "합(컨정션)", opposition: "대립(오퍼지션)", trine: "삼각(트라인)",
  square: "사각(스퀘어)", sextile: "육각(섹스타일)",
};

// 2026-08-21 확장: 천왕성ㆍ해왕성ㆍ명왕성은 라이브러리가 이미 계산해주고 있었는데 리포트에
// 안 쓰고 버리고 있었음(사용자 지적으로 발견) — 개인적 성향보다 세대적ㆍ심층적 주제를
// 다루는 외행성 3개를 추가해 실제로 있는 데이터를 활용한다. 지어내는 게 아니라 이미 계산되던
// 값을 리포트에 반영하는 것뿐이라 환각 위험 없음.
const CORE_BODIES = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto"];

/**
 * @param {object} input {year, month, day, hour(0-23 또는 null), unknownTime, latitude, longitude}
 * @returns {object} computed.json의 "astrology" 필드에 그대로 들어갈 구조
 */
function computeAstrology(input) {
  const hasTime = !input.unknownTime;
  const origin = new Origin({
    year: input.year,
    month: input.month - 1, // 라이브러리는 0-indexed 월 사용
    date: input.day,
    hour: hasTime ? input.hour : 12,
    minute: hasTime ? (input.minute || 0) : 0,
    latitude: input.latitude,
    longitude: input.longitude,
  });

  const horoscope = new Horoscope({
    origin,
    houseSystem: "whole-sign",
    zodiac: "tropical",
    aspectPoints: ["bodies"],
    aspectWithPoints: ["bodies"],
    aspectTypes: ["major"],
    customOrbs: {},
    language: "en",
  });

  const planets = CORE_BODIES.map((key) => {
    const b = horoscope.CelestialBodies[key];
    const signInfo = SIGN_KO[b.Sign.label];
    return {
      body: BODY_KO[key],
      sign: signInfo.label,
      element: signInfo.element,
      degree: Math.round(b.ChartPosition.Ecliptic.DecimalDegrees % 30 * 10) / 10,
      // 시너스트리(synastry.js)가 두 사람의 행성 사이 실제 각도를 계산하려면 별자리 안에서의
      // 위치(위 degree, 0~30)가 아니라 황도 전체 기준 절대 경도(0~360)가 필요해서 추가함
      // (2026-08-23, 시너스트리 엔진 신설과 함께 추가 — 기존 필드는 그대로 두고 덧붙이기만 함).
      ecliptic_longitude: Math.round(b.ChartPosition.Ecliptic.DecimalDegrees * 10) / 10,
      // 생시를 모르면 하우스는 신뢰도가 없으므로 null 처리(어센던트 의존 데이터)
      house: hasTime ? HOUSE_NUM_KO[b.House && b.House.label] || null : null,
      retrograde: !!b.isRetrograde,
    };
  });

  const ascendant = hasTime
    ? { sign: SIGN_KO[horoscope.Angles.ascendant.Sign.label].label }
    : null;

  // 2026-08-30 추가 — whole-sign 하우스제라 하우스마다 이미 별자리 하나가 정확히
  // 대응되므로(라이브러리가 이미 계산한 값, 새로 추론하는 게 아님), 그 별자리의
  // 표준 지배행성만 붙인다. 생시를 모르면(hasTime=false) 하우스 자체가 없으므로 null.
  const houseRulers = hasTime
    ? horoscope.Houses.map((h) => {
        const sign = SIGN_KO[h.Sign.label].label;
        return { house: h.id, sign, ruler: SIGN_RULER_KO[sign] || null };
      })
    : null;

  const aspects = hasTime
    ? horoscope.Aspects.all
        .filter((a) => CORE_BODIES.includes(a.point1Key) && CORE_BODIES.includes(a.point2Key))
        .map((a) => ({
          body1: BODY_KO[a.point1Key],
          body2: BODY_KO[a.point2Key],
          type: ASPECT_KO[a.aspectKey] || a.aspectKey,
          orb: Math.round(a.orb * 10) / 10,
        }))
    : [];

  // 4원소 비중 집계(태양~토성 7개 core body 기준)
  const elementCount = { 불: 0, 땅: 0, 바람: 0, 물: 0 };
  planets.forEach((p) => elementCount[p.element]++);

  const result = {
    sun_sign: planets[0].sign,
    moon_sign: planets[1].sign,
    ascendant: ascendant ? ascendant.sign : null,
    unknown_time_note: hasTime ? null : "생시 미상 — 어센던트ㆍ하우스ㆍ어스펙트는 계산하지 않고 태양/달 등 시간 무관 정보만 제공",
    planets,
    aspects,
    element_count: elementCount,
    house_rulers: houseRulers,
  };
  // 2026-08-23 추가 — 점성술 대응표 지식베이스(astrology-correspondence.js). saju쪽
  // correspondence.js와 동일한 이유(별자리ㆍ행성ㆍ하우스ㆍ어스펙트 "의미" 사전이 없었음)로
  // 신설, 이 손님의 실제 계산값만 근거로 조회한다.
  result.correspondence = buildAstroCorrespondence(result);
  return result;
}

module.exports = { computeAstrology, SIGN_KO, BODY_KO, ASPECT_KO };
