/*
 * 사주 계산 로직 — lunar.js(오픈소스 만세력 라이브러리) 결과를 전부 한국어로
 * 번역하고, 전문 용어(간지) 대신 쉬운 오행 성향 설명으로 바꿔서 반환한다.
 * 화면에는 이 파일이 만든 한국어 결과만 노출되고, lunar.js 자체나 원본
 * 한자 결과는 어디에도 표시하지 않는다.
 */

// 60갑자 한자 -> 한국어 음독 (표준 한자음, 모호함 없음)
const GAN_KO = { "甲": "갑", "乙": "을", "丙": "병", "丁": "정", "戊": "무", "己": "기", "庚": "경", "辛": "신", "壬": "임", "癸": "계" };
const ZHI_KO = { "子": "자", "丑": "축", "寅": "인", "卯": "묘", "辰": "진", "巳": "사", "午": "오", "未": "미", "申": "신", "酉": "유", "戌": "술", "亥": "해" };

const SHENGXIAO_KO = { "鼠": "쥐띠", "牛": "소띠", "虎": "호랑이띠", "兔": "토끼띠", "龙": "용띠", "蛇": "뱀띠", "马": "말띠", "羊": "양띠", "猴": "원숭이띠", "鸡": "닭띠", "狗": "개띠", "猪": "돼지띠" };
const SHENGXIAO_EMOJI = { "鼠": "🐭", "牛": "🐮", "虎": "🐯", "兔": "🐰", "龙": "🐲", "蛇": "🐍", "马": "🐴", "羊": "🐑", "猴": "🐵", "鸡": "🐔", "狗": "🐶", "猪": "🐷" };
const XINGZUO_KO = { "白羊": "양자리", "金牛": "황소자리", "双子": "쌍둥이자리", "巨蟹": "게자리", "狮子": "사자자리", "处女": "처녀자리", "天秤": "천칭자리", "天蝎": "전갈자리", "射手": "사수자리", "摩羯": "염소자리", "水瓶": "물병자리", "双鱼": "물고기자리" };

// 천간/지지 -> 오행(五行) 매핑 (쉬운 성향 설명용 — 지장간까지 따지는 전문가용 정밀 계산은 생략)
const GAN_OHENG = { "甲": "목", "乙": "목", "丙": "화", "丁": "화", "戊": "토", "己": "토", "庚": "금", "辛": "금", "壬": "수", "癸": "수" };
const ZHI_OHENG = { "寅": "목", "卯": "목", "巳": "화", "午": "화", "辰": "토", "戌": "토", "丑": "토", "未": "토", "申": "금", "酉": "금", "亥": "수", "子": "수" };

const OHENG_INFO = {
  "목": { emoji: "🌳", label: "나무(목)", trait: "성장과 유연함, 앞으로 나아가려는 추진력" },
  "화": { emoji: "🔥", label: "불(화)", trait: "열정과 표현력, 사람을 끌어당기는 밝은 에너지" },
  "토": { emoji: "⛰️", label: "흙(토)", trait: "안정감과 신뢰, 꾸준히 버텨내는 포용력" },
  "금": { emoji: "⚔️", label: "쇠(금)", trait: "결단력과 원칙, 맺고 끊는 게 분명한 판단력" },
  "수": { emoji: "💧", label: "물(수)", trait: "지혜와 유연한 사고, 상황에 맞춰 흐르는 적응력" },
};

function ganzhiToKo(gz) {
  return gz.split("").map((c) => GAN_KO[c] || ZHI_KO[c] || c).join("");
}

/**
 * @param {object} input {year, month, day, hour(0-23 또는 null), unknownTime}
 * @returns {object} 화면에 그대로 쓸 수 있는 한국어 결과
 */
function calculateSaju(input) {
  const hour = input.unknownTime ? 12 : input.hour; // 시간 모르면 오시(정오) 기준으로 계산하되 시주는 안 보여줌
  const solar = Solar.fromYmdHms(input.year, input.month, input.day, hour, 0, 0);
  const lunarDate = solar.getLunar();
  const ec = lunarDate.getEightChar();

  const pillars = {
    year: ganzhiToKo(ec.getYear()),
    month: ganzhiToKo(ec.getMonth()),
    day: ganzhiToKo(ec.getDay()),
    hour: input.unknownTime ? null : ganzhiToKo(ec.getTime()),
  };

  // 오행 집계: 4개(또는 시간 모르면 3개) 기둥의 천간+지지 총 6~8글자
  const ohengCount = { 목: 0, 화: 0, 토: 0, 금: 0, 수: 0 };
  const rawPillars = [ec.getYear(), ec.getMonth(), ec.getDay()];
  if (!input.unknownTime) rawPillars.push(ec.getTime());
  rawPillars.forEach((gz) => {
    const gan = gz[0], zhi = gz[1];
    if (GAN_OHENG[gan]) ohengCount[GAN_OHENG[gan]]++;
    if (ZHI_OHENG[zhi]) ohengCount[ZHI_OHENG[zhi]]++;
  });

  const sorted = Object.entries(ohengCount).sort((a, b) => b[1] - a[1]);
  const dominant = sorted.filter(([, n]) => n === sorted[0][1] && n > 0).map(([k]) => k);
  const missing = sorted.filter(([, n]) => n === 0).map(([k]) => k);

  return {
    lunarText: lunarDate.toString(),
    pillars,
    shengxiao: SHENGXIAO_KO[lunarDate.getYearShengXiao()],
    shengxiaoEmoji: SHENGXIAO_EMOJI[lunarDate.getYearShengXiao()],
    xingzuo: XINGZUO_KO[solar.getXingZuo()],
    ohengCount,
    dominant,
    missing,
  };
}

function buildOhengSummary(result) {
  const domText = result.dominant.map((k) => `${OHENG_INFO[k].emoji} ${OHENG_INFO[k].label}`).join(", ");
  const traitText = result.dominant.map((k) => OHENG_INFO[k].trait).join(" · ");
  let text = `타고난 기운 중에서는 ${domText} 기운이 가장 강해요. ${traitText}이(가) 이 사람의 중심 성향이에요.`;
  if (result.missing.length > 0 && result.missing.length < 5) {
    const missText = result.missing.map((k) => OHENG_INFO[k].label).join(", ");
    text += ` 반대로 ${missText} 기운은 사주에 거의 없어서, 이 부분을 의식적으로 채워주면 균형이 좋아진다고 봐요.`;
  }
  return text;
}

/**
 * 두 사람의 오행 분포를 비교해서 "보완"·"공통" 기운을 찾는다.
 * 특정 띠·별자리 조합이 좋다/나쁘다는 식의 근거 불명확한 궁합론은 쓰지 않고,
 * 이미 검증된 오행 계산 결과만으로 설명 가능한 것만 말한다.
 */
function buildCompatibilitySummary(resultA, resultB) {
  const complementAtoB = resultA.dominant.filter((k) => resultB.missing.includes(k));
  const complementBtoA = resultB.dominant.filter((k) => resultA.missing.includes(k));
  const shared = resultA.dominant.filter((k) => resultB.dominant.includes(k));

  const parts = [];
  if (complementAtoB.length || complementBtoA.length) {
    const names = [...new Set([...complementAtoB, ...complementBtoA])].map((k) => OHENG_INFO[k].label).join(", ");
    parts.push(`한쪽이 강한 ${names} 기운을 다른 쪽이 못 채우고 있어서, 서로 부족한 부분을 채워주는 보완 관계로 볼 수 있어요.`);
  }
  if (shared.length) {
    const names = shared.map((k) => OHENG_INFO[k].label).join(", ");
    parts.push(`둘 다 ${names} 기운이 강해서, 성향이 비슷해 대화가 잘 통하는 대신 같은 지점에서 부딪힐 수도 있어요.`);
  }
  if (!parts.length) {
    parts.push("두 사람의 기운이 서로 겹치는 부분도 크게 없고 보완되는 부분도 뚜렷하지 않아요 — 서로 다른 개성을 있는 그대로 존중하는 관계에 가까워요.");
  }
  return parts.join(" ");
}
