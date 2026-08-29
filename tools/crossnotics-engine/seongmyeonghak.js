/*
 * 크로스노틱스 — 성명학(姓名學) 계산 엔진. 이름의 발음오행(소리오행ㆍ음령오행)만 다룬다.
 *
 * 2026-08-29 신설. 성명학은 전통적으로 발음오행(소리)ㆍ수리오행(한자 획수)ㆍ자원오행(한자
 * 뜻) 세 갈래를 종합하는데, 이 서비스는 손님 이름을 한글로만 받고 있어(한자 획수 정보가
 * 없음) 뒤 두 갈래는 계산할 근거가 없다 — 그래서 **발음오행 한 갈래만** 다룬다(1번 규칙:
 * 근거 없는 계산 안 함).
 *
 * 발음오행 원리 — 훈민정음 해례본에 기술된 발음기관 위치별 오행 배속(2026-08-29,
 * miso.co.kr/mumyeong.kr 등 다수 성명학 사이트 교차확인):
 *   목(牙音, 어금닛소리) — ㄱㄲㅋ / 화(舌音, 혓소리) — ㄴㄷㄸㄹㅌ / 토(喉音, 목청소리) — ㅇㅎ
 *   금(齒音, 잇소리) — ㅅㅆㅈㅉㅊ / 수(唇音, 입술소리) — ㅁㅂㅃㅍ
 * 이 배속은 초성(첫소리) 기준이며, 이 파일은 그 초성을 유니코드 한글 완성형 코드포인트에서
 * 직접 계산한다(외부 라이브러리 없이 정확함 — 한글 완성형은 (코드 - 0xAC00) = 초성*588 +
 * 중성*28 + 종성 이라는 고정 공식을 따르므로 지어낼 여지가 없음).
 *
 * 이름 글자 사이의 오행이 상생인지 상극인지는 correspondence.js의 ohengRelation()을 그대로
 * 재사용한다(gunghap.js가 "두 사람"을 비교하는 것과 같은 함수를, 여기서는 "이름 두 글자"를
 * 비교하는 데 씀 — 새 판정 로직을 만들지 않음, 크로스노틱스 0번 원칙).
 */
const { ohengRelation } = require("./correspondence.js");

const CHO_JAMO = ["ㄱ","ㄲ","ㄴ","ㄷ","ㄸ","ㄹ","ㅁ","ㅂ","ㅃ","ㅅ","ㅆ","ㅇ","ㅈ","ㅉ","ㅊ","ㅋ","ㅌ","ㅍ","ㅎ"];
const CHO_OHENG = ["목","목","화","화","화","화","수","수","수","금","금","토","금","금","금","목","화","수","토"];

/**
 * 한글 완성형 음절 하나에서 초성 자모와 그 발음오행을 구한다. 완성형(가~힣)이 아니면(성
 * 뒤에 공백ㆍ영문 등이 섞인 경우) null.
 */
function choOheng(syllable) {
  const code = syllable.codePointAt(0);
  if (code < 0xAC00 || code > 0xD7A3) return null;
  const choIndex = Math.floor((code - 0xAC00) / (21 * 28));
  return { jamo: CHO_JAMO[choIndex], oheng: CHO_OHENG[choIndex] };
}

/**
 * @param {string} name 손님이 입력한 한글 이름(예: "최광호"). 성ㆍ이름 구분 없이 통째로
 *   받아 음절 순서대로 분석한다(한국 이름은 성명 구분이 발음오행 분석에 필수는 아님 —
 *   전체 이름의 흐름을 본다).
 * @returns {object|null} computed.json의 saju.seongmyeonghak에 들어갈 구조. 한글 완성형
 *   음절이 2개 미만이면(관계를 볼 짝이 없음) null.
 */
function computeSeongmyeonghak(name) {
  if (!name || typeof name !== "string") return null;
  const syllables = Array.from(name).filter((ch) => choOheng(ch));
  if (syllables.length < 2) return null;

  const letters = syllables.map((ch) => {
    const c = choOheng(ch);
    return { char: ch, jamo: c.jamo, oheng: c.oheng };
  });

  const pairs = [];
  for (let i = 0; i < letters.length - 1; i++) {
    const a = letters[i], b = letters[i + 1];
    pairs.push({
      from: a.char, to: b.char,
      from_oheng: a.oheng, to_oheng: b.oheng,
      relation: ohengRelation(a.oheng, b.oheng),
    });
  }

  const saengCount = pairs.filter((p) => p.relation.startsWith("상생")).length;
  const geukCount = pairs.filter((p) => p.relation.startsWith("상극")).length;
  const flowSummary = geukCount === 0
    ? "이름 전체가 상생 또는 비화로만 이어져, 소리 흐름이 걸림 없이 순조롭습니다."
    : saengCount === 0
      ? "이름 전체가 상극으로만 이어져, 소리 흐름에 마찰이 있는 편입니다."
      : "이름 안에 상생과 상극이 섞여 있어, 흐름이 순조로운 구간과 부딫히는 구간이 같이 있습니다.";

  return {
    name,
    letters,
    pairs,
    flow_summary: flowSummary,
    methodology_note:
      "이름의 발음오행(소리오행)만 근거로 함 — 성명학은 전통적으로 한자 획수(수리오행)ㆍ" +
      "한자 뜻(자원오행)도 함께 보지만, 이 서비스는 한글 이름만 입력받아 그 두 갈래는 " +
      "계산 근거가 없어 다루지 않음. 발음오행은 훈민정음 해례본의 발음기관 오행 배속을 " +
      "따름. 이 서비스가 채택한 여러 참고 기준 중 하나로 다룰 것.",
  };
}

module.exports = { computeSeongmyeonghak, choOheng };
