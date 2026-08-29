/*
 * 크로스노틱스 — 토정비결(土亭祕訣) 계산 엔진.
 *
 * 2026-08-29 신설. 상괘(1~8)ㆍ중괘(1~6)ㆍ하괘(1~3) 3자리 숫자로 그 해의 운을 보는 전통
 * 방식 — 이지함이 독자적으로 고안한 수리 체계라 공식으로 유도되지 않고, 60갑자별
 * 태세수ㆍ월건수ㆍ일진수를 정해진 조견표에서 찾아야 한다(tojeong_table.json). 이 조견표는
 * 여러 출처가 서로 다른 값을 내놓아(사장님과 함께 실제로 세 개의 서로 다른 표를 비교
 * 검증함) 검증 없이 아무 표나 쓰면 안 된다 — 아래 실제 사례로 계산 전체(상괘ㆍ중괘ㆍ하괘)를
 * 교차검증했다:
 *   1976년 음력 8월 26일생의 2005년 토정비결 = 212
 *   - 상괘: (한국나이 30 + 을유년 태세수 20) % 8 = 2
 *   - 중괘: (2005년 음력 8월 작은달 29일 + 을유월 월건수 14) % 6 = 1
 *   - 하괘: (음력 생일 26 + 병진일 일진수 18) % 3 = 2
 * lunar-javascript로 이 세 값(태세수ㆍ월건수ㆍ일진수를 뺀 나머지 전부)을 그대로 재현해
 * 실제로 212가 나오는 것까지 확인함(saju.js가 이미 이 라이브러리로 음력 변환을 하고
 * 있으므로 여기서도 그대로 재사용 — 새 라이브러리를 들이지 않음).
 *
 * 나머지 0이면 각각 8ㆍ6ㆍ3을 취한다(전통 작괘법 원칙).
 *
 * 2026-08-29 추가 — 144가지(8×6×3) 조합 각각에 별도 문구를 새로 짓는 대신(타로 78장과
 * 달리 원전 시구 없이 순수 숫자 조합이라 그럴 근거도 없음), 상괘(8개)ㆍ중괘(6개)ㆍ하괘(3개)
 * 각각의 의미를 따로 정리해서 LLM이 세 조각을 엮어 이 손님만의 문장으로 합성하게 한다 —
 * astrology(행성+별자리+하우스)ㆍsaju(십신+오행) 등 이 프로젝트의 다른 모든 엔진과 같은
 * 설계 원칙(작은 뜻풀이 재료를 주고 조합은 LLM이 함). 8개 상괘는 전통 팔괘(건ㆍ태ㆍ리ㆍ진ㆍ
 * 손ㆍ감ㆍ간ㆍ곤)의 상징을 참고해 지었고, 6개 중괘(그 기운이 드러나는 영역)ㆍ3개 하괘(그
 * 해 안에서의 시기별 흐름)는 이 서비스가 정리한 해석 기준이다 — "천 년 전 원문 그대로"라고
 * 주장하지 않고 methodology_note로 그 취지를 밝힌다(gunghap.js/yearly-fortune.js와 동일
 * 원칙).
 */
const SANGGWAE_MEANING = {
  1: { name: "건(하늘)", meaning: "확장하고 앞장서서 주도하려는 기운입니다. 벌여놓은 일을 키우거나 새로운 자리에 나서고 싶은 마음이 커집니다." },
  2: { name: "태(못)", meaning: "사람이 모이고 관계가 활발해지는 기운입니다. 말ㆍ만남ㆍ소통에서 기회가 열리기 쉽습니다." },
  3: { name: "리(불)", meaning: "드러나고 주목받는 기운입니다. 해왔던 노력이 성과로 눈에 보이거나, 원치 않게 주변의 시선이 쏠리는 일이 같이 따라오기 쉽습니다." },
  4: { name: "진(우레)", meaning: "갑작스러운 변화나 시작이 따르는 기운입니다. 정체돼 있던 일이 갑자기 움직이기 쉽습니다." },
  5: { name: "손(바람)", meaning: "천천히 스며들듯 넓어지는 기운입니다. 한 번에 크게 바뀌기보다, 조금씩 쌓아온 게 서서히 자리를 넓혀갑니다." },
  6: { name: "감(물)", meaning: "안으로 깊어지는 기운입니다. 겉으로 화려하진 않아도 내실을 다지거나, 어려움을 겪으며 오히려 단단해지기 쉽습니다." },
  7: { name: "간(산)", meaning: "멈춰서 정리하고 준비하는 기운입니다. 무리해서 밀어붙이기보다 지금까지 벌인 일을 추스르는 게 맞는 시기입니다." },
  8: { name: "곤(땅)", meaning: "묵묵히 받아들이고 쌓아가는 기운입니다. 눈에 띄는 큰 사건보다, 꾸준함이 결국 힘이 되는 흐름입니다." },
};
const JUNGGWAE_MEANING = {
  1: "이 기운은 특히 사람과의 관계(가까운 인연ㆍ새로운 만남ㆍ주변 평판)에서 두드러지게 나타나기 쉽습니다.",
  2: "이 기운은 특히 돈ㆍ재물이 오가는 흐름에서 두드러지게 나타나기 쉽습니다.",
  3: "이 기운은 특히 일ㆍ성과ㆍ맡은 역할에서 두드러지게 나타나기 쉽습니다.",
  4: "이 기운은 특히 몸과 마음의 상태(건강ㆍ기분ㆍ체력)에서 두드러지게 나타나기 쉽습니다.",
  5: "이 기운은 특히 가족이나 가까운 인연과의 관계에서 두드러지게 나타나기 쉽습니다.",
  6: "이 기운은 특히 배움ㆍ내면의 생각이 정리되는 방식에서 두드러지게 나타나기 쉽습니다.",
};
const HAGWAE_MEANING = {
  1: "이 흐름은 한 해의 초반에 강하게 오고, 후반에는 그 힘을 다스리는 쪽으로 마음을 써야 합니다.",
  2: "이 흐름은 초반보다 중반부터 본격적으로 열리기 시작합니다.",
  3: "이 흐름은 처음부터 끝까지 꾸준히 이어지다, 후반에 가장 뚜렷한 결실로 나타납니다.",
};
const { Solar, Lunar, LunarMonth } = require("lunar-javascript");
const TOJEONG_TABLE = require("./tojeong_table.json");

// saju.js를 require하면 saju.js가 이 파일을 다시 require하는 순환 참조가 생긴다
// (yearly-fortune.js 파일 헤더 주석과 동일한 이유) — 그래서 이 작은 한글 변환표만
// saju.js와 별개로 그대로 다시 적는다(기존 관례와 일치).
const GAN_KO = { 甲: "갑", 乙: "을", 丙: "병", 丁: "정", 戊: "무", 己: "기", 庚: "경", 辛: "신", 壬: "임", 癸: "계" };
const ZHI_KO = { 子: "자", 丑: "축", 寅: "인", 卯: "묘", 辰: "진", 巳: "사", 午: "오", 未: "미", 申: "신", 酉: "유", 戌: "술", 亥: "해" };
function ganzhiToKo(gz) {
  return gz.split("").map((c) => GAN_KO[c] || ZHI_KO[c] || c).join("");
}

/**
 * @param {object} resolvedBirth resolveSolarDate()를 거친 손님의 양력 생년월일
 *   {year, month, day}. saju.js와 같은 방식으로 이미 음력→양력 변환이 끝난 값을 받는다.
 * @param {number} [targetYear] 토정비결을 볼 연도(기본값: 이 코드를 실행하는 지금 연도 —
 *   yearly-fortune.js의 nowYear와 같은 원칙).
 * @returns {object|null} computed.json의 saju.tojeong에 들어갈 구조. lunar-javascript가
 *   해당 음력월/일을 못 찾는 극히 드문 경우(예: 대상 연도에 그 음력월이 윤달로만 존재)에는
 *   null(지어내지 않음).
 */
function computeTojeong(resolvedBirth, targetYear) {
  const year = targetYear || new Date().getFullYear();

  const birthSolar = Solar.fromYmd(resolvedBirth.year, resolvedBirth.month, resolvedBirth.day);
  const birthLunar = birthSolar.getLunar();
  const lunarMonth = Math.abs(birthLunar.getMonth()); // 음수면 윤달 표시 — 달수 자체는 절대값
  const lunarDay = birthLunar.getDay();

  // 대상 연도의 세수(태세) 간지 — 음력설 경계 오차를 피하려고 그 해 한가운데(음력 6월)
  // 날짜로 조회한다(yearly-fortune.js가 se_un을 쓰는 것과 동일한 목적, 이 파일은 임의
  // 연도까지 다뤄야 해서 se_un 배열 대신 lunar-javascript로 직접 구함).
  const targetYearGanzhi = ganzhiToKo(Lunar.fromYmd(year, 6, 1).getYearInGanZhi());

  const targetLunarMonth = LunarMonth.fromYm(year, lunarMonth);
  if (!targetLunarMonth) return null; // 그 해에 해당 음력월 자체가 없는 예외적 경우
  const monthDayCount = targetLunarMonth.getDayCount();
  const monthGanzhi = ganzhiToKo(targetLunarMonth.getGanZhi());

  const targetDayLunar = Lunar.fromYmd(year, lunarMonth, Math.min(lunarDay, monthDayCount));
  const dayGanzhi = ganzhiToKo(targetDayLunar.getDayInGanZhi());

  const yearRow = TOJEONG_TABLE[targetYearGanzhi];
  const monthRow = TOJEONG_TABLE[monthGanzhi];
  const dayRow = TOJEONG_TABLE[dayGanzhi];
  if (!yearRow || !monthRow || !dayRow) return null; // 조견표에 없는 간지(있을 수 없지만 방어)

  // 한국 나이 — 대상 연도 기준 (실제 생일이 지났는지는 따지지 않는 전통 방식 그대로).
  const koreanAge = year - resolvedBirth.year + 1;

  const mod = (n, m) => {
    const r = n % m;
    return r === 0 ? m : r;
  };
  const sanggwae = mod(koreanAge + yearRow.taesesu, 8);
  const junggwae = mod(monthDayCount + monthRow.wolgeonsu, 6);
  const hagwae = mod(lunarDay + dayRow.iljinsu, 3);

  return {
    target_year: year,
    target_year_ganzhi_ko: targetYearGanzhi,
    birth_lunar_month: lunarMonth,
    birth_lunar_day: lunarDay,
    korean_age: koreanAge,
    gwae: {
      sang: sanggwae, jung: junggwae, ha: hagwae, code: `${sanggwae}${junggwae}${hagwae}`,
      sang_meaning: SANGGWAE_MEANING[sanggwae],
      jung_meaning: JUNGGWAE_MEANING[junggwae],
      ha_meaning: HAGWAE_MEANING[hagwae],
    },
    methodology_note:
      "상괘ㆍ중괘ㆍ하괘를 태세수ㆍ월건수ㆍ일진수 조견표(전통 작괘법)로 산출함. " +
      "이지함이 고안했다고 전해지는 독자적 수리 체계로, 사주의 오행 생극과는 다른 " +
      "별개의 전통 참고 기준. 이 서비스가 채택한 여러 참고 기준 중 하나로 다룰 것.",
  };
}

module.exports = { computeTojeong, TOJEONG_TABLE, SANGGWAE_MEANING };
