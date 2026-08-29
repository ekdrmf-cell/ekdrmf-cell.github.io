/*
 * 크로스노틱스 — 택일(擇日) 계산 엔진.
 *
 * 2026-08-29 신설. 전통 택일은 "결혼식엔 이 기준, 이사엔 저 기준"처럼 행사 종류마다
 * 다른 살(예: 손 없는 날, 이사 방위)까지 따지는데, 이 서비스는 손님에게 "어떤 행사를
 * 위한 날짜인지ㆍ언제~언제 사이에서 고르고 싶은지"를 아직 입력받지 않는다(신청서에
 * 그 항목 자체가 없음) — 그래서 행사별 세부 기준은 계산 근거가 없어 다루지 않는다(1번
 * 규칙). 대신 **이미 검증된 correspondence.js의 jijiRelation()을 재사용해, 앞으로 30일
 * 동안 손님의 일지(일주 지지, "나 자신")와 그날의 일진 지지가 삼합ㆍ육합(좋은 관계)인지
 * 충ㆍ형(부딪히는 관계)인지만** 가려서, "이 손님에게 특히 힘이 되는/피하면 좋은 날"
 * 수준으로 제공한다 — 행사 특화 택일이 아니라 그 앞 단계의 일반 참고 정보임을
 * methodology_note에 명확히 밝힌다.
 */
const { Solar } = require("lunar-javascript");
const { jijiRelation } = require("./correspondence.js");

const GAN_KO = { 甲: "갑", 乙: "을", 丙: "병", 丁: "정", 戊: "무", 己: "기", 庚: "경", 辛: "신", 壬: "임", 癸: "계" };
const ZHI_KO = { 子: "자", 丑: "축", 寅: "인", 卯: "묘", 辰: "진", 巳: "사", 午: "오", 未: "미", 申: "신", 酉: "유", 戌: "술", 亥: "해" };
function ganzhiToKo(gz) {
  return gz.split("").map((c) => GAN_KO[c] || ZHI_KO[c] || c).join("");
}

/**
 * @param {string} dayZhi 손님의 일지 한 글자(예: saju.pillars.day.ganzhi_ko의 두 번째 글자).
 * @param {Date} [fromDate] 조회 시작일(기본값: 지금). 테스트가 아니면 생략.
 * @returns {object|null} computed.json의 saju.taekil에 들어갈 구조. dayZhi가 없으면(생시
 *   미상이라 일지 자체가 불확실한 경우는 없음 — 일지는 생년월일만으로 계산되므로 항상 있음,
 *   방어적으로만 null 처리) null.
 */
function computeTaekil(dayZhi, fromDate) {
  if (!dayZhi) return null;
  const start = fromDate || new Date();

  const days = [];
  for (let i = 1; i <= 30; i++) {
    const d = new Date(start.getTime());
    d.setDate(d.getDate() + i);
    const solar = Solar.fromYmd(d.getFullYear(), d.getMonth() + 1, d.getDate());
    const todayGanzhiKo = ganzhiToKo(solar.getLunar().getDayInGanZhi());
    const todayZhi = todayGanzhiKo.slice(-1);
    const rel = jijiRelation(dayZhi, todayZhi);

    let grade = "보통";
    let reason = null;
    if (rel.samhap) { grade = "좋음"; reason = `삼합(${rel.samhap.element} 기운) — 손님의 일지와 크게 힘을 합치는 날`; }
    else if (rel.yukhap) { grade = "좋음"; reason = `육합(${rel.yukhap.element} 기운) — 손님의 일지와 순조롭게 맞물리는 날`; }
    else if (rel.yukchung) { grade = "피하면 좋음"; reason = "충(沖) — 손님의 일지와 정면으로 부딪히는 날"; }
    else if (rel.hyeong) { grade = "피하면 좋음"; reason = `${rel.hyeong} — 마찰ㆍ갈등이 붙기 쉬운 날`; }

    days.push({
      date: `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`,
      day_ganzhi_ko: todayGanzhiKo,
      grade, reason,
    });
  }

  return {
    customer_day_zhi: dayZhi,
    range_days: 30,
    good_days: days.filter((d) => d.grade === "좋음"),
    avoid_days: days.filter((d) => d.grade === "피하면 좋음"),
    methodology_note:
      "행사 종류(결혼ㆍ이사ㆍ개업 등)별 세부 택일 기준은 손님이 그 정보를 입력하지 않아 " +
      "다루지 않음(신청서에 항목 없음). 앞으로 30일 동안 손님의 일지(일주 지지)와 그날의 " +
      "일진 지지 사이의 합ㆍ충 관계만 근거로 한 일반 참고 정보이며, 특정 행사를 위한 " +
      "확정적 길일 지정이 아님.",
  };
}

module.exports = { computeTaekil };
