/*
 * 한글 이름 발음오행 분석.
 *
 * 성명학에는 크게 두 갈래가 있다: (1) 한자 획수를 세어 81수리로 길흉을 보는
 * "원형이정" 방식, (2) 훈민정음의 발음 위치(아설순치후)를 오행에 대응시킨
 * "발음오행" 방식. 이 도구는 후자만 쓴다 — 획수법은 한글 획수 세는 기준이
 * 작명소마다 달라 같은 이름도 사이트마다 정반대 결과가 나오고, 국내
 * 성명학 박사 논문에서도 "학술적 근거가 빈약하다"는 평가가 있어 신뢰도
 * 문제가 크다. 발음오행은 초성이 무엇인지만 보는 결정론적 방식이라
 * 모호함이 없다.
 */

const CHO_LIST = ["ㄱ","ㄲ","ㄴ","ㄷ","ㄸ","ㄹ","ㅁ","ㅂ","ㅃ","ㅅ","ㅆ","ㅇ","ㅈ","ㅉ","ㅊ","ㅋ","ㅌ","ㅍ","ㅎ"];

const CHO_OHENG = {
  "ㄱ": "목", "ㄲ": "목", "ㅋ": "목",
  "ㄴ": "화", "ㄷ": "화", "ㄸ": "화", "ㄹ": "화", "ㅌ": "화",
  "ㅁ": "토", "ㅂ": "토", "ㅃ": "토", "ㅍ": "토",
  "ㅅ": "금", "ㅆ": "금", "ㅈ": "금", "ㅉ": "금", "ㅊ": "금",
  "ㅇ": "수", "ㅎ": "수",
};

// 오행 상생(生, 순서대로 다음 것을 살려줌) / 상극(剋, 다음 것을 억누름)
const SAENG_NEXT = { 목: "화", 화: "토", 토: "금", 금: "수", 수: "목" };
const GEUK_NEXT = { 목: "토", 토: "수", 수: "화", 화: "금", 금: "목" };

/** 한글 한 글자를 초성만 분해한다. 한글 완성형 음절이 아니면 null. */
function getChosung(ch) {
  const code = ch.charCodeAt(0) - 0xac00;
  if (code < 0 || code > 11171) return null;
  const choIndex = Math.floor(code / (21 * 28));
  return CHO_LIST[choIndex];
}

/**
 * @param {string} name 한글 이름(성+이름, 예: "김민준")
 * @returns {object|null} 분석 결과, 한글 이름이 아니면 null
 */
function analyzeNameOheng(name) {
  const chars = [...name.trim()].filter((c) => c !== " ");
  if (chars.length < 2) return null;

  const letters = [];
  for (const ch of chars) {
    const cho = getChosung(ch);
    if (!cho) return null; // 한글 완성형이 아닌 글자가 섞여있으면 분석 불가
    letters.push({ char: ch, oheng: CHO_OHENG[cho] });
  }

  const relations = [];
  for (let i = 0; i < letters.length - 1; i++) {
    const a = letters[i].oheng, b = letters[i + 1].oheng;
    let type;
    if (a === b) type = "neutral";
    else if (SAENG_NEXT[a] === b) type = "saeng"; // 상생: a가 b를 살려줌
    else if (GEUK_NEXT[a] === b) type = "geuk"; // 상극: a가 b를 억누름
    else type = "neutral2"; // 상생/상극 사이클에서 역방향(약한 관계)
    relations.push({ from: a, to: b, type });
  }

  const saengCount = relations.filter((r) => r.type === "saeng").length;
  const geukCount = relations.filter((r) => r.type === "geuk").length;

  return { letters, relations, saengCount, geukCount, totalRelations: relations.length };
}

function buildNameSummary(result) {
  const seq = result.letters.map((l) => `${l.char}(${l.oheng})`).join(" → ");
  let flow;
  if (result.geukCount === 0 && result.saengCount > 0) {
    flow = "글자 사이 흐름이 전부 상생(서로 살려주는) 관계라, 소리 흐름이 아주 매끄러운 이름이에요.";
  } else if (result.saengCount > result.geukCount) {
    flow = "상생 관계가 더 많아서, 전체적으로 무난하고 조화로운 흐름의 이름이에요.";
  } else if (result.geukCount > result.saengCount) {
    flow = "상극(부딪히는) 관계가 더 많아요. 소리 흐름 자체가 나쁘다는 뜻이라기보다, 발음할 때 살짝 힘이 들어가는 강한 인상을 주는 이름일 수 있어요.";
  } else {
    flow = "상생과 상극이 고르게 섞여 있어서, 부드러움과 단단함이 함께 느껴지는 이름이에요.";
  }
  return { seq, flow };
}
