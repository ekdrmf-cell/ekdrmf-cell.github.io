/*
 * 크로스노틱스 — 띠별 신년(세운) 운세 계산 엔진.
 * 인수인계 문서(천지인운명관_다음세션_인수인계222.md "C. 무료 도구 콘텐츠 계속 확장" /
 * CROSSNOTICS_TODO_NEXT.md)에서 지적된 구멍을 메운다: 무료 사주 계산기는 손님의 띠만
 * 알려주고, 유료 리포트 계산 엔진(saju.js)에는 "올해가 이 띠에게 어떤 해인지" 계산이
 * 아예 없었다.
 *
 * ============================================================
 * 왜 "지어낸 신년운세 서사"가 아닌가
 * ============================================================
 * 흔히 보는 "2026년 쥐띠 운세" 같은 콘텐츠는 매년 근거 없이 새로 지어내는 서사가
 * 대부분이라, 이 프로젝트의 0번 원칙(환각 차단)과 정면으로 배치된다. 그래서 여기서는
 * 명리학에서 실제로 쓰이는 결정론적 근거만 쓴다 — **손님의 년지(띠)와 올해 세운(歲運)의
 * 년지가 합ㆍ충ㆍ삼합 등 어떤 관계인지, 손님의 년간 오행과 올해 세운의 천간 오행이
 * 상생ㆍ상극인지** — 이고, 판정 로직도 새로 만들지 않고 correspondence.js의
 * jijiRelation()/ohengRelation()을 그대로 재사용한다(gunghap.js가 "두 사람의 지지 관계"를
 * 비교하는 것과 완전히 같은 함수를 "손님의 지지 vs 올해 세운의 지지" 비교에 재사용하는 것뿐).
 *
 * saju.js의 se_un은 이미 최근 4개년(작년~내후년)만 제공하므로(se_un_note 참고), 여기서도
 * 그 범위를 벗어나면(예: se_un 자체가 없는 성별 미입력 케이스) 계산하지 않고 null을 반환해
 * "계산 범위 밖"임을 명확히 한다 — 지어내서 채우지 않음.
 *
 * KO_GAN_OHENG/KO_ZHI_OHENG은 saju.js의 GAN_OHENG/ZHI_OHENG(한자 키)과 정확히 같은 표를
 * 한글 키로 다시 적은 것이다. saju.js를 require하지 않고 새로 적은 이유는, se_un.ganzhi_ko가
 * 이미 한글로 변환되어 있어 한글 키 맵이 필요한데, saju.js를 require하면 saju.js가 이 파일을
 * 다시 require하는 순환 참조가 생기기 때문(saju.js 파일 헤더 주석에도 있듯, 이 프로젝트는
 * 무료 도구ㆍ유료 엔진 사이에서도 같은 표를 이미 각자 유지하고 있어 이 방식이 기존 관례와
 * 일치함).
 */
const { jijiRelation, ohengRelation, ZODIAC } = require("./correspondence.js");

const KO_GAN_OHENG = { 갑: "목", 을: "목", 병: "화", 정: "화", 무: "토", 기: "토", 경: "금", 신: "금", 임: "수", 계: "수" };
const KO_ZHI_OHENG = { 인: "목", 묘: "목", 사: "화", 오: "화", 진: "토", 술: "토", 축: "토", 미: "토", 신: "금", 유: "금", 해: "수", 자: "수" };

/**
 * @param {object} sajuResult computeSaju()가 지금까지 계산한 결과(호출 시점 기준 아직
 *   correspondence/shensha/yearly_fortune을 붙이기 전이라도 pillars.year와 se_un만 있으면
 *   동작함)
 * @returns {object|null} computed.json의 saju.yearly_fortune에 들어갈 구조. se_un이 없거나
 *   (성별 미입력) 올해에 해당하는 세운 항목이 없으면 null.
 */
function computeYearlyFortune(sajuResult) {
  if (!sajuResult.se_un || !sajuResult.se_un.length) return null;

  // saju.js가 세운을 계산할 때 쓴 것과 동일한 "지금" 기준(실행 시점) — 이 파일도 Workflow
  // 스크립트가 아니라 일반 Node 실행 파일이라 new Date() 사용에 문제없음.
  const nowYear = new Date().getFullYear();
  const thisYearEntry = sajuResult.se_un.find((s) => s.year === nowYear);
  if (!thisYearEntry) return null;

  const customerYearZhi = sajuResult.pillars.year.ganzhi_ko.slice(-1);
  const customerYearGan = sajuResult.pillars.year.ganzhi_ko.slice(0, 1);
  const thisYearZhi = thisYearEntry.ganzhi_ko.slice(-1);
  const thisYearGan = thisYearEntry.ganzhi_ko.slice(0, 1);

  const zhiRelation = jijiRelation(customerYearZhi, thisYearZhi);
  const ganRelation = ohengRelation(KO_GAN_OHENG[customerYearGan], KO_GAN_OHENG[thisYearGan]);
  const zodiac = ZODIAC[customerYearZhi] || null;
  const animalLabel = zodiac ? `${zodiac.animal}띠` : "손님 띠";

  const highlights = [];
  if (zhiRelation.samhap) {
    highlights.push(`${animalLabel}는 올해(${thisYearEntry.year}년, ${thisYearEntry.ganzhi_ko}년)와 년지가 삼합(${zhiRelation.samhap.element} 기운)을 이뤄, 전통적으로 힘을 받는 해로 여겨지는 조합입니다.`);
  } else if (zhiRelation.yukhap) {
    highlights.push(`${animalLabel}는 올해(${thisYearEntry.year}년, ${thisYearEntry.ganzhi_ko}년)와 년지가 육합(${zhiRelation.yukhap.element} 기운) 관계라, 전통적으로 순조롭게 맞물리는 해로 여겨지는 조합입니다.`);
  }
  if (zhiRelation.yukchung) {
    highlights.push(`${animalLabel}는 올해(${thisYearEntry.year}년, ${thisYearEntry.ganzhi_ko}년)와 년지가 충(沖) 관계라, 전통 역술에서 흔히 "삼재" 논의와 함께 변화ㆍ이동이 잦을 수 있는 해로 언급되는 조합입니다.`);
  }
  if (zhiRelation.hyeong) {
    highlights.push(`${animalLabel}는 올해(${thisYearEntry.year}년, ${thisYearEntry.ganzhi_ko}년)와 ${zhiRelation.hyeong} 관계라, 신경전ㆍ마찰이 생기기 쉬운 기운이 있다고 봅니다.`);
  }
  if (zhiRelation.yukpa) {
    highlights.push(`${animalLabel}는 올해(${thisYearEntry.year}년, ${thisYearEntry.ganzhi_ko}년)와 파(破) 관계라, 계획한 일이 지연되거나 어긋나기 쉬운 기운이 있다고 봅니다.`);
  }
  if (zhiRelation.yukhae) {
    highlights.push(`${animalLabel}는 올해(${thisYearEntry.year}년, ${thisYearEntry.ganzhi_ko}년)와 해(害) 관계라, 사소한 오해나 구설이 생기기 쉬운 기운이 있다고 봅니다.`);
  }
  if (ganRelation === "비화(같은 오행)") {
    highlights.push(`올해 세운의 천간(${thisYearGan}, ${KO_GAN_OHENG[thisYearGan]} 기운)이 손님의 년간과 같은 오행이라, 평소 기질이 더 강하게 드러나는 해로 봅니다.`);
  } else if (ganRelation === "상생(내가 생함)") {
    highlights.push(`손님의 년간(${customerYearGan}, ${KO_GAN_OHENG[customerYearGan]} 기운)이 올해 세운의 천간을 생하는 관계라, 본인의 에너지를 밖으로 쏟아내며 활동하는 흐름으로 봅니다.`);
  } else if (ganRelation === "상생(내가 생받음)") {
    highlights.push(`올해 세운의 천간(${thisYearGan}, ${KO_GAN_OHENG[thisYearGan]} 기운)이 손님의 년간을 생하는 관계라, 도움ㆍ지원을 받는 흐름으로 봅니다.`);
  } else if (ganRelation.startsWith("상극")) {
    highlights.push(`손님의 년간(${customerYearGan})과 올해 세운의 천간(${thisYearGan})이 상극 관계라, 크고 작은 변화나 긴장이 따를 수 있는 해로 봅니다.`);
  }

  return {
    year: thisYearEntry.year,
    year_ganzhi_ko: thisYearEntry.ganzhi_ko,
    customer_zodiac: zodiac ? { zhi: customerYearZhi, animal: zodiac.animal } : null,
    zhi_relation: zhiRelation,
    gan_relation: ganRelation,
    highlights,
    methodology_note:
      "손님의 년지(띠)ㆍ년간과 올해 세운의 간지 사이의 합충형파해ㆍ상생상극 관계만 근거로 한 " +
      "이 서비스의 해석 기준이며, 매년 새로 지어내는 서사형 신년운세가 아니라 이미 " +
      "saju.js가 계산한 세운(se_un) 값에서만 도출됨. 전통 역술의 여러 시각 중 하나로 참고할 것.",
  };
}

module.exports = { computeYearlyFortune, KO_GAN_OHENG, KO_ZHI_OHENG };
