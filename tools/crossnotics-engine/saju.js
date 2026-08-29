/*
 * 크로스노틱스 — 사주 계산 엔진.
 * lunar-javascript(6tail, MIT, npm v1.7.7 — https://github.com/6tail/lunar-javascript)의
 * EightChar API를 깊이 활용해 십신ㆍ12운성ㆍ지장간ㆍ공망ㆍ대운까지 전부 산출한다.
 * saju/js/saju-calc.js(무료 도구)와 동일한 GAN_KO/ZHI_KO/오행 매핑을 재사용해 두 도구의
 * 번역 결과가 어긋나지 않게 한다. 여기서는 검증 없이 지어내는 부분이 전혀 없다 — 전부
 * lunar-javascript가 계산한 값을 한국어로 옮기기만 한다(크로스노틱스 0번 원칙: 환각 차단).
 */
const { Solar, Lunar } = require("lunar-javascript");
const { buildCorrespondence } = require("./correspondence.js");
const { computeShensha } = require("./shensha.js");
const { computeYearlyFortune } = require("./yearly-fortune.js");
const { computeTojeong } = require("./tojeong.js");

const GAN_KO = { 甲: "갑", 乙: "을", 丙: "병", 丁: "정", 戊: "무", 己: "기", 庚: "경", 辛: "신", 壬: "임", 癸: "계" };
const ZHI_KO = { 子: "자", 丑: "축", 寅: "인", 卯: "묘", 辰: "진", 巳: "사", 午: "오", 未: "미", 申: "신", 酉: "유", 戌: "술", 亥: "해" };

const GAN_OHENG = { 甲: "목", 乙: "목", 丙: "화", 丁: "화", 戊: "토", 己: "토", 庚: "금", 辛: "금", 壬: "수", 癸: "수" };
const ZHI_OHENG = { 寅: "목", 卯: "목", 巳: "화", 午: "화", 辰: "토", 戌: "토", 丑: "토", 未: "토", 申: "금", 酉: "금", 亥: "수", 子: "수" };

// 십신(十神) — 七杀은 현대 명리학 소프트웨어에서 흔히 偏官 대신 쓰는 표기라 병기한다.
const SHI_SHEN_KO = {
  比肩: "비견", 劫财: "겁재", 食神: "식신", 伤官: "상관",
  偏财: "편재", 正财: "정재", 七杀: "칠살(편관)", 正官: "정관",
  偏印: "편인", 正印: "정인",
};

// 12운성(十二运星)
const DI_SHI_KO = {
  长生: "장생", 沐浴: "목욕", 冠带: "관대", 临官: "임관", 帝旺: "제왕", 衰: "쇠",
  病: "병", 死: "사", 墓: "묘", 绝: "절", 胎: "태", 养: "양",
};

function ganzhiToKo(gz) {
  return gz.split("").map((c) => GAN_KO[c] || ZHI_KO[c] || c).join("");
}

function pillarDetail(ec, key) {
  // key: Year | Month | Day | Time
  const gan = ec[`get${key}Gan`]();
  const zhi = ec[`get${key}Zhi`]();
  const hideGan = ec[`get${key}HideGan`]();
  return {
    ganzhi_hanja: gan + zhi,
    ganzhi_ko: ganzhiToKo(gan + zhi),
    gan_oheng: GAN_OHENG[gan] || null,
    zhi_oheng: ZHI_OHENG[zhi] || null,
    shi_shen_gan: key === "Day" ? "일주(일간 본인)" : SHI_SHEN_KO[ec[`get${key}ShiShenGan`]()] || null,
    shi_shen_zhi: ec[`get${key}ShiShenZhi`]().map((s) => SHI_SHEN_KO[s] || s),
    ji_jang_gan: hideGan.map((g) => GAN_KO[g] || g),
    twelve_stage: DI_SHI_KO[ec[`get${key}DiShi`]()] || null,
    gong_mang: ec[`get${key}XunKong`](),
  };
}

/**
 * 손님이 입력한 생년월일이 음력(윤달 포함)이면 양력으로 변환한다. 사주ㆍ점성술 두 엔진
 * 모두 양력 기준으로 계산하므로, 두 엔진에 서로 다른 날짜가 들어가지 않도록 run.js가 이
 * 함수 하나로 먼저 변환한 뒤 양쪽에 같은 결과를 넘긴다 — 여기서만 변환하고, 변환 결과는
 * 그대로 리포트에 노출해 고객이 직접 확인할 수 있게 한다(크로스노틱스 0번 원칙: 지어내지
 * 않고, 검증 가능하게).
 * @param {object} input {year, month, day, calendarType: "solar"|"lunar" (기본 solar), isLeapMonth}
 * @returns {object} {year, month, day, lunar_conversion_note: string|null}
 */
function resolveSolarDate({ year, month, day, calendarType = "solar", isLeapMonth = false }) {
  if (calendarType !== "lunar") {
    return { year, month, day, lunar_conversion_note: null };
  }
  const lunar = Lunar.fromYmd(year, isLeapMonth ? -month : month, day);
  const solar = lunar.getSolar();
  const solarYmd = `${solar.getYear()}-${String(solar.getMonth()).padStart(2, "0")}-${String(solar.getDay()).padStart(2, "0")}`;
  return {
    year: solar.getYear(),
    month: solar.getMonth(),
    day: solar.getDay(),
    lunar_conversion_note:
      `입력하신 음력 ${year}년 ${isLeapMonth ? "윤" : ""}${month}월 ${day}일은 ` +
      `양력 ${solarYmd}로 환산해 계산했습니다.`,
  };
}

/**
 * @param {object} input {year, month, day, hour(0-23 또는 null), unknownTime, gender: "M"|"F",
 *   calendarType: "solar"|"lunar" (기본 solar), isLeapMonth}
 * @returns {object} computed.json의 "saju" 필드에 그대로 들어갈 구조
 */
function computeSaju(input) {
  const resolved = resolveSolarDate(input);
  const hour = input.unknownTime ? 12 : input.hour;
  const solar = Solar.fromYmdHms(resolved.year, resolved.month, resolved.day, hour, 0, 0);
  const lunar = solar.getLunar();
  const ec = lunar.getEightChar();

  const pillars = {
    year: pillarDetail(ec, "Year"),
    month: pillarDetail(ec, "Month"),
    day: pillarDetail(ec, "Day"),
    hour: input.unknownTime ? null : pillarDetail(ec, "Time"),
  };

  // 오행 집계 (시간 모르면 3기둥만)
  const ohengCount = { 목: 0, 화: 0, 토: 0, 금: 0, 수: 0 };
  const rawPillars = [ec.getYear(), ec.getMonth(), ec.getDay()];
  if (!input.unknownTime) rawPillars.push(ec.getTime());
  rawPillars.forEach((gz) => {
    const gan = gz[0], zhi = gz[1];
    if (GAN_OHENG[gan]) ohengCount[GAN_OHENG[gan]]++;
    if (ZHI_OHENG[zhi]) ohengCount[ZHI_OHENG[zhi]]++;
  });
  const sortedOheng = Object.entries(ohengCount).sort((a, b) => b[1] - a[1]);
  const dominantElements = sortedOheng.filter(([, n]) => n === sortedOheng[0][1] && n > 0).map(([k]) => k);
  const missingElements = sortedOheng.filter(([, n]) => n === 0).map(([k]) => k);

  // 대운 — 생시를 모르면 대운 계산 자체는 가능(연/월주 기반)하나, 정밀도가 떨어짐을 결과에 표시
  let daeYun = null;
  let seUn = null;
  if (input.gender === "M" || input.gender === "F") {
    const yun = ec.getYun(input.gender === "M" ? 1 : 0);
    const daYunRaw = yun.getDaYun().slice(1, 9);
    daeYun = daYunRaw.map((d) => ({
      start_age: d.getStartAge(),
      start_year: d.getStartYear(),
      end_year: d.getEndYear(),
      ganzhi_ko: ganzhiToKo(d.getGanZhi()),
    }));

    // 세운(연도별 간지) — 2026-08-21 추가: LLM이 "2025년 을사년" 식으로 특정 연도를
    // 언급하면서 실제로는 계산 안 된 값을 지어내는 걸 실사용 테스트에서 발견해서 추가함.
    // "지금"은 실행 시점 기준(주문 처리 시점)이라 new Date()를 직접 씀 — 이 파일은 Workflow
    // 스크립트가 아니라 일반 Node 실행 파일이라 여기서 new Date() 쓰는 건 문제없음.
    const nowYear = new Date().getFullYear();
    const relevantDaYun = daYunRaw.find((d) => nowYear >= d.getStartYear() && nowYear <= d.getEndYear())
      || daYunRaw[0];
    seUn = relevantDaYun
      .getLiuNian()
      .filter((l) => l.getYear() >= nowYear - 1 && l.getYear() <= nowYear + 2)
      .map((l) => ({ year: l.getYear(), ganzhi_ko: ganzhiToKo(l.getGanZhi()) }));
  }

  const result = {
    birth_solar: `${resolved.year}-${String(resolved.month).padStart(2, "0")}-${String(resolved.day).padStart(2, "0")}`,
    lunar_conversion_note: resolved.lunar_conversion_note,
    unknown_time: !!input.unknownTime,
    lunar_text: lunar.toString(),
    pillars,
    oheng_count: ohengCount,
    dominant_elements: dominantElements,
    missing_elements: missingElements,
    dae_yun: daeYun,
    dae_yun_note: input.gender ? null : "성별 미입력으로 대운 계산 생략",
    se_un: seUn,
    se_un_note: input.gender
      ? "작년ㆍ올해ㆍ내후년까지(리포트 생성 시점 기준) 세운만 제공 — 이 범위를 벗어난 연도는 언급하지 말 것"
      : "성별 미입력으로 세운 계산 생략",
  };
  // 2026-08-23 추가 — 명리학 대응표 지식베이스(correspondence.js). 띠ㆍ오행 생활정보ㆍ
  // 십신ㆍ12운성의 "의미"까지 이 손님의 실제 계산값을 키로 조회해 붙여준다 — LLM이 이런
  // 질문(예: "제 띠 특징이 뭔가요", "저한테 부족한 오행에 어울리는 음식은요")에 일반
  // 지식으로 답하지 않고 이 필드를 근거로 direct 답변할 수 있게 한다(CROSSNOTICS_HANDOFF.md
  // "다음에 이어서 할 일" 항목 반영).
  result.correspondence = buildCorrespondence(result);
  // 2026-08-23 추가 — 신살(도화ㆍ역마ㆍ화개ㆍ홍염) 계산(shensha.js). question_taxonomy.md
  // 1절에서 확인된 실제 손님 질문("저 도화살 있나요")에 direct로 답할 수 있게 함.
  result.shensha = computeShensha(result);
  // 2026-08-23 추가 — 띠별 신년(세운) 운세 계산(yearly-fortune.js). 인수인계 문서에서
  // 지적된 구멍("올해 이 띠에게 어떤 해인지" 계산이 유료 엔진엔 없었음)을 메움. se_un이
  // 없으면(성별 미입력) null.
  result.yearly_fortune = computeYearlyFortune(result);
  // 2026-08-29 추가 — 토정비결(tojeong.js). 사주 오행 생극과는 별개의 전통 참고 기준을
  // 하나 더 준다(성별 입력과 무관하게 계산 가능 — 대운/세운과 달리 이 계산은 생년월일만
  // 있으면 되므로 gender 체크 없이 항상 시도함). lunar-javascript가 해당 음력월을 못 찾는
  // 극히 드문 경우만 null.
  result.tojeong = computeTojeong(resolved);
  return result;
}

module.exports = { computeSaju, resolveSolarDate, ganzhiToKo, GAN_OHENG, ZHI_OHENG, SHI_SHEN_KO, DI_SHI_KO };
