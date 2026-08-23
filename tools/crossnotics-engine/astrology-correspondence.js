/*
 * 크로스노틱스 — 서양 점성술 대응표 지식베이스. saju.js에 correspondence.js(명리학 대응표)를
 * 붙인 것과 완전히 같은 이유로 신설한다: astrology.js는 지금까지 별자리ㆍ행성ㆍ하우스ㆍ
 * 어스펙트의 "이름 번역"만 있었고, 그게 실제로 뭘 뜻하는지(의미) 사전이 전혀 없었다 —
 * "제 태양이 황소자리인데 무슨 뜻이에요" 같은 질문에 LLM이 검증 안 된 일반 점성술 지식으로
 * 답해야 하는 위험이 있었다(question_taxonomy.md에서 사주 쪽과 동일한 유형의 구멍으로 확인).
 *
 * 여기 있는 값은 서양 점성술에서 수백 년간 통용되어 온 표준 상징 체계(별자리 12개 기질,
 * 행성 10개 상징, 하우스 12개 삶의 영역, 어스펙트 5종 관계)를 정리한 것으로, 명리학의
 * 지지 합충형파해처럼 유파마다 세부 해석이 갈리는 영역보다는 훨씬 널리 합의된 편이지만,
 * 그래도 "전통적으로 여겨지는 상징 체계"이지 과학적 사실이 아니라는 톤은 saju쪽
 * correspondence.js와 동일하게 유지해야 한다.
 */

const SIGN_MEANING = {
  양자리: "도전적이고 추진력이 강한 기질을 상징함. 즉흥적으로 일을 시작하는 리더십, 빠른 결단력과 관련됨.",
  황소자리: "안정과 편안함을 추구하는 기질을 상징함. 인내심ㆍ고집, 감각적이고 실용적인 태도와 관련됨.",
  쌍둥이자리: "호기심이 많고 소통을 즐기는 기질을 상징함. 다재다능함ㆍ재빠른 사고, 변화무쌍한 관심사와 관련됨.",
  게자리: "감정이 풍부하고 보호본능이 강한 기질을 상징함. 가정ㆍ소속감을 중시하는 태도, 예민한 감수성과 관련됨.",
  사자자리: "자신감이 넘치고 주목받길 좋아하는 기질을 상징함. 리더십ㆍ강한 자존심, 관대함과 관련됨.",
  처녀자리: "분석적이고 꼼꼼한 기질을 상징함. 완벽주의ㆍ실용적인 태도, 봉사정신과 관련됨.",
  천칭자리: "균형과 조화를 추구하는 기질을 상징함. 사교적인 태도, 미적 감각, 때로는 우유부단함과 관련됨.",
  전갈자리: "깊이 있고 강렬한 기질을 상징함. 통찰력, 한번 몰입하면 놓지 않는 집중력, 비밀스러운 면과 관련됨.",
  사수자리: "자유롭고 낙천적인 기질을 상징함. 모험심, 철학적 사고, 직설적인 화법과 관련됨.",
  염소자리: "책임감이 강하고 현실적인 기질을 상징함. 인내심ㆍ야망, 신중하고 보수적인 태도와 관련됨.",
  물병자리: "독창적이고 개혁적인 기질을 상징함. 독립적인 태도, 인도주의적 관심, 예측하기 어려운 면과 관련됨.",
  물고기자리: "감수성이 풍부하고 상상력이 넘치는 기질을 상징함. 공감 능력, 몽상가적 기질, 희생적인 태도와 관련됨.",
};

const BODY_MEANING = {
  태양: "자아 정체성ㆍ핵심 성격ㆍ삶의 목적을 상징함(가장 기본이 되는 기질).",
  달: "감정ㆍ무의식ㆍ내면의 욕구를 상징함(겉으로 잘 드러나지 않는 정서적 반응 패턴).",
  수성: "사고방식ㆍ소통 스타일ㆍ학습 능력을 상징함.",
  금성: "사랑ㆍ미적 취향ㆍ관계에서의 가치관을 상징함.",
  화성: "행동력ㆍ욕망ㆍ추진 에너지를 상징함.",
  목성: "확장ㆍ행운ㆍ성장의 기회를 상징함.",
  토성: "책임ㆍ제약ㆍ인내를 통한 성숙을 상징함.",
  천왕성: "변화ㆍ개혁ㆍ독창성을 상징함(개인보다 세대 전체에 걸쳐 나타나는 느린 기운).",
  해왕성: "꿈ㆍ영성ㆍ이상과 환상을 상징함(개인보다 세대 전체에 걸쳐 나타나는 느린 기운).",
  명왕성: "근본적인 변형ㆍ권력ㆍ재생을 상징함(개인보다 세대 전체에 걸쳐 나타나는 느린 기운).",
};

const HOUSE_MEANING = {
  1: "자아와 첫인상 — 남에게 비치는 모습, 삶을 대하는 기본 태도를 보는 영역.",
  2: "재물과 소유 — 돈을 대하는 태도, 자기 가치관을 보는 영역.",
  3: "소통과 학습 — 형제자매ㆍ가까운 이웃과의 관계, 일상적 대화 방식을 보는 영역.",
  4: "가정과 뿌리 — 정서적 기반, 가족ㆍ고향과의 관계를 보는 영역.",
  5: "연애와 창조 — 자기표현, 취미ㆍ자녀와 관련된 즐거움을 보는 영역.",
  6: "일상과 건강 — 노동ㆍ습관, 몸을 관리하는 방식을 보는 영역.",
  7: "파트너십과 결혼 — 대인관계에서의 균형, 계약 관계를 보는 영역.",
  8: "공유자원과 변형 — 깊은 유대, 위기를 겪고 재생하는 힘을 보는 영역.",
  9: "철학과 확장 — 여행ㆍ고등교육, 세계관을 넓히는 활동을 보는 영역.",
  10: "사회적 지위와 커리어 — 명예ㆍ성취, 사회에서 인정받는 위치를 보는 영역.",
  11: "친구와 공동체 — 인맥, 미래에 대한 비전을 보는 영역.",
  12: "무의식과 영성 — 마무리, 숨겨진 것들ㆍ휴식이 필요한 영역.",
};

const ASPECT_MEANING = {
  "합(컨정션)": "두 기운이 하나로 융합되어 강하게 발현되는 관계. 좋은 쪽으로도 부담스러운 쪽으로도 작용할 수 있어 두 행성의 성격에 따라 방향이 달라짐.",
  "대립(오퍼지션)": "두 기운이 정반대로 당기는 관계. 긴장이 생기기 쉽지만, 두 힘 사이의 균형점을 찾으면 오히려 폭넓은 시야를 얻을 수 있음.",
  "삼각(트라인)": "두 기운이 자연스럽게 조화를 이루는 관계. 편안하고 순조롭게 재능이 발휘되는 흐름으로 여겨짐.",
  "사각(스퀘어)": "두 기운이 마찰을 일으키는 관계. 도전과 압박이 따르지만, 그만큼 성장의 동력이 되기도 함.",
  "육각(섹스타일)": "두 기운이 기회를 만들어내는 관계. 저절로 되기보다는 본인이 노력해서 활용할 때 빛을 발함.",
};

/**
 * astrology.js의 computeAstrology() 결과를 받아 astro_correspondence(대응표 조회 결과)
 * 객체를 만든다. 이 손님의 실제 계산값(행성이 위치한 별자리ㆍ실제로 점유한 하우스ㆍ실제로
 * 계산된 어스펙트)만 키로 삼아 조회하므로, saju의 buildCorrespondence()와 동일하게 "이
 * 손님과 무관한 일반 지식"을 나열하지 않는다.
 * @param {object} astrologyResult computeAstrology()의 반환값
 * @returns {object} computed.json의 astrology.correspondence에 들어갈 구조
 */
function buildAstroCorrespondence(astrologyResult) {
  const planetMeanings = (astrologyResult.planets || []).map((p) => ({
    body: p.body,
    sign: p.sign,
    house: p.house,
    body_meaning: BODY_MEANING[p.body] || null,
    sign_meaning: SIGN_MEANING[p.sign] || null,
  }));

  const ascendantMeaning = astrologyResult.ascendant
    ? { sign: astrologyResult.ascendant, meaning: SIGN_MEANING[astrologyResult.ascendant] || null }
    : null;

  const occupiedHouses = [...new Set((astrologyResult.planets || []).map((p) => p.house).filter(Boolean))].sort((a, b) => a - b);
  const houseMeanings = occupiedHouses.map((h) => ({ house: h, meaning: HOUSE_MEANING[h] || null }));

  const aspectMeanings = (astrologyResult.aspects || []).map((a) => ({
    body1: a.body1,
    body2: a.body2,
    type: a.type,
    meaning: ASPECT_MEANING[a.type] || null,
  }));

  return {
    planet_meanings: planetMeanings,
    ascendant_meaning: ascendantMeaning,
    house_meanings: houseMeanings,
    aspect_meanings: aspectMeanings,
    note: "별자리ㆍ행성ㆍ하우스ㆍ어스펙트의 의미는 서양 점성술의 표준 상징 체계를 정리한 참고 정보이며, 과학적으로 검증된 사실이나 확정적 예언이 아님.",
  };
}

module.exports = { SIGN_MEANING, BODY_MEANING, HOUSE_MEANING, ASPECT_MEANING, buildAstroCorrespondence };
