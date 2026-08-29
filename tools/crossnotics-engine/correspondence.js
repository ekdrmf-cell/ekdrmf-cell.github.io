/*
 * 크로스노틱스 — 명리학 대응표 지식베이스.
 * CROSSNOTICS_HANDOFF.md "-7번 업데이트"에서 지적된 구멍(띠ㆍ오행별 색/방향/숫자/음식/
 * 신체장기/직업, 십신ㆍ12운성의 "의미" 자체가 saju.js에는 없고 한글 명칭 번역만 있었음)을
 * 메우는 모듈. 여기 있는 값은 전부 명리학 고전 이론(오행 상생상극, 지지 합충형파해,
 * 십신ㆍ12운성의 통설적 해석)에서 가져온 **결정론적 룩업 테이블**이다 — LLM이 매번
 * "일반 지식"으로 지어내지 않고, saju.js가 이미 계산한 값(우세 오행ㆍ띠ㆍ사용된 십신 등)을
 * 키로 삼아 이 표에서 찾아 쓰기만 하면 되므로 크로스노틱스 0번 원칙(환각 차단)을 지키면서
 * "direct" 답변 가능 범위를 넓힌다(build_report.py SYSTEM_PROMPT 10번 규칙 참고).
 *
 * 주의: 오행 생활 정보(색ㆍ방향ㆍ음식ㆍ직업 등)와 띠 성격은 수천 년간 전해 내려온 **전통
 * 상징 체계**이지 과학적으로 검증된 사실이 아니다 — "~라고 전통적으로 여겨진다" 톤을
 * 유지해야 하며(SYSTEM_PROMPT 4번 규칙과 동일한 원칙), 의료ㆍ직업 선택의 확정적 근거처럼
 * 제시하면 안 된다. 이 파일은 데이터만 제공하고, 톤 규율은 build_report.py가 담당한다.
 */

// ============================================================
// 오행(五行) 생활 대응표 — 색ㆍ방향ㆍ숫자ㆍ계절ㆍ신체ㆍ음식ㆍ직업ㆍ성격
// 출처: 사주 색상/숫자/방향/계절은 명리학 표준 오행 배속(사주만세 등 다수 사이트 교차확인,
// 2026-08-23 리서치). 신체장기ㆍ음식ㆍ직업ㆍ성격은 전통 오행학설의 통설(여러 명리 칼럼
// 교차확인)을 정리한 것으로, 학파에 따라 세부 표현은 다를 수 있는 "일반적으로 통용되는
// 참고 상응표"임을 리포트 톤에도 반영할 것(절대적 정설로 제시하지 않음, correlate.js의
// 매핑 근거 문서화 관행과 동일).
// ============================================================
const OHENG_INFO = {
  목: {
    color: "청색(초록색 계열)",
    direction: "동쪽",
    numbers: [3, 8],
    season: "봄",
    organ: "간ㆍ담(쓸개)ㆍ눈",
    food: "신맛, 녹색 채소(브로콜리ㆍ시금치ㆍ오이 등), 신 과일",
    jobs: "교육ㆍ기획ㆍ디자인ㆍ출판ㆍ의류ㆍ원예ㆍ법조처럼 성장ㆍ확장ㆍ창조와 관련된 분야",
    personality: "인자함, 성장 지향, 추진력, 명예를 중시하는 경향",
  },
  화: {
    color: "적색(붉은색 계열)",
    direction: "남쪽",
    numbers: [2, 7],
    season: "여름",
    organ: "심장ㆍ소장ㆍ혈액순환ㆍ시력",
    food: "쓴맛, 붉은 음식(토마토ㆍ고추ㆍ대추 등)",
    jobs: "방송ㆍ예술ㆍ미용ㆍ전기전자ㆍ요식업ㆍ엔터테인먼트ㆍ영업처럼 표현ㆍ열정ㆍ확산과 관련된 분야",
    personality: "열정적, 예의를 중시함, 성격이 급한 편, 표현력이 풍부함",
  },
  토: {
    color: "황색(노란색 계열)",
    direction: "중앙",
    numbers: [5, 10],
    season: "환절기(계절이 바뀌는 사이)",
    organ: "비장ㆍ위장ㆍ소화기",
    food: "단맛, 노란 음식(호박ㆍ고구마ㆍ감자ㆍ꿀 등)",
    jobs: "부동산ㆍ농업ㆍ건축ㆍ중개ㆍ종교처럼 중재ㆍ신뢰ㆍ터전과 관련된 분야",
    personality: "신용을 중시함, 중재력과 포용력, 보수적이고 안정 지향적인 경향",
  },
  금: {
    color: "백색(흰색 계열)",
    direction: "서쪽",
    numbers: [4, 9],
    season: "가을",
    organ: "폐ㆍ대장ㆍ호흡기ㆍ피부",
    food: "매운맛, 흰 음식(무ㆍ마늘ㆍ양파ㆍ배 등)",
    jobs: "금융ㆍ기계ㆍ의료ㆍ군경ㆍ재무회계처럼 원칙ㆍ결단ㆍ절제와 관련된 분야",
    personality: "의리를 중시함, 결단력, 원칙주의, 냉철하게 판단하는 경향",
  },
  수: {
    color: "흑색(검은색 계열)",
    direction: "북쪽",
    numbers: [1, 6],
    season: "겨울",
    organ: "신장ㆍ방광ㆍ비뇨생식기ㆍ귀",
    food: "짠맛, 검은 음식(미역ㆍ검은콩ㆍ해산물 등)",
    jobs: "유통ㆍ물류ㆍ무역ㆍ서비스업ㆍ철학ㆍ역술ㆍ법률ㆍ교육처럼 지혜ㆍ유동성ㆍ소통과 관련된 분야",
    personality: "지혜로움, 융통성, 유연하게 상황에 적응하는 경향",
  },
};

// 오행 상생(내가 낳는 관계, 화살표 방향으로 다음 오행을 도움)
const OHENG_SAENG_NEXT = { 목: "화", 화: "토", 토: "금", 금: "수", 수: "목" };
// 오행 상극(내가 극하는 관계, 화살표 방향의 오행을 억제)
const OHENG_GEUK_NEXT = { 목: "토", 토: "수", 수: "화", 화: "금", 금: "목" };

/**
 * 두 오행 a, b의 관계를 a 기준으로 판정한다.
 * @returns {"상생(내가 생함)"|"상생(내가 생받음)"|"상극(내가 극함)"|"상극(내가 극받음)"|"비화(같은 오행)"}
 */
function ohengRelation(a, b) {
  if (a === b) return "비화(같은 오행)";
  if (OHENG_SAENG_NEXT[a] === b) return "상생(내가 생함)";
  if (OHENG_SAENG_NEXT[b] === a) return "상생(내가 생받음)";
  if (OHENG_GEUK_NEXT[a] === b) return "상극(내가 극함)";
  if (OHENG_GEUK_NEXT[b] === a) return "상극(내가 극받음)";
  return "무관계"; // 이론상 5개 오행끼리는 항상 위 다섯 관계 중 하나에 해당하므로 실제로는 도달하지 않음
}

// ============================================================
// 12지지(地支) 띠 대응표 + 지지 관계(합ㆍ충ㆍ형ㆍ파ㆍ해)
// 출처: 명리학 표준 지지 이론(2026-08-23 다수 명리 사이트 교차확인 — sajustudy.com 등).
// 띠별 성격은 한국 민속에서 널리 통용되는 상징적 특성 정리로, 개인차를 무시한 확정적
// 성격 진단이 아니라 "전통적으로 여겨지는 상징"임을 리포트 톤에 반영할 것.
// ============================================================
const ZODIAC = {
  자: { animal: "쥐", traits: "영리함, 재빠른 판단력, 사교성, 생존력과 적응력" },
  축: { animal: "소", traits: "성실함, 근면함, 우직한 뚝심, 인내심" },
  인: { animal: "호랑이", traits: "용맹함, 리더십, 독립적 기질, 성급할 수 있는 추진력" },
  묘: { animal: "토끼", traits: "온화함, 신중함, 평화를 추구하는 성향, 예민한 감수성" },
  진: { animal: "용", traits: "카리스마, 야망, 강한 자신감, 높은 자존심" },
  사: { animal: "뱀", traits: "지혜로움, 신비로운 매력, 날카로운 직관력, 치밀함" },
  오: { animal: "말", traits: "활동적, 자유분방함, 사교적, 성급한 면" },
  미: { animal: "양", traits: "온순함, 예술적 감수성, 배려심, 결정을 미루는 우유부단함" },
  신: { animal: "원숭이", traits: "재치, 영리함, 뛰어난 융통성, 변덕스러울 수 있음" },
  유: { animal: "닭", traits: "부지런함, 꼼꼼함, 철저한 자기관리, 완벽주의 성향" },
  술: { animal: "개", traits: "충직함, 정의감, 강한 책임감, 보수적인 면" },
  해: { animal: "돼지", traits: "낙천적, 포용력, 재물복이 있다고 여겨짐, 솔직담백함" },
};

// 지지 육합(六合) — 짝ㆍ합화 오행. 인해합은 육파(六破) 표에도 동시에 등장하는 이론상 겹침이
// 있는데(합충형파해가 서로 다른 기준의 분류라 발생하는 고전 명리학의 널리 알려진 모순),
// 이 프로젝트에서는 "합이 파보다 강하게 작용한다"는 통설(합충형파해 세기 순서: 합/충 >
// 형 > 파/해)을 따라 합을 우선 적용한다 — gunghap.js의 판정 순서에 반영됨.
const JIJI_YUKHAP = {
  "자축": "토", "인해": "목", "묘술": "화", "진유": "금", "사신": "수", "오미": "화",
};
// 지지 삼합(三合) — 3개 지지가 모여 하나의 오행 기운을 이루는 조합. 육합ㆍ육충보다 강하게
// 작용한다는 게 명리학 통설(2026-08-23 리서치, sajustudy.com).
const JIJI_SAMHAP = {
  화: ["인", "오", "술"],
  수: ["신", "자", "진"],
  금: ["사", "유", "축"],
  목: ["해", "묘", "미"],
};
// 지지 육충(六沖) — 정반대로 부딪히는 관계.
const JIJI_YUKCHUNG = ["자오", "축미", "인신", "묘유", "진술", "사해"];
// 지지 삼형(三刑)ㆍ자묘형ㆍ자형 — 갈등ㆍ마찰을 나타내는 관계. 삼형은 세 글자가 모두 있어야
// 완성되므로 두 사람(2글자) 비교에서는 그 중 한 쌍만 있어도 "형의 기운이 있다" 정도로 약하게
// 취급한다(완전한 삼형은 사주 하나 안에서 세 글자가 다 있을 때 성립하는 개념이라, 두 사람의
// 지지 하나씩 비교하는 궁합 맥락에서는 원래 의미보다 약화해서 반영하는 게 통설적 실무).
const JIJI_SAMHYEONG_PAIRS = ["인사", "사신", "인신", "축술", "술미", "축미"];
const JIJI_JAMYOHYEONG = ["자묘"];
const JIJI_JAHYEONG = ["진진", "오오", "유유", "해해"];
// 지지 육파(六破) — 형ㆍ충보다는 약하지만 일을 지연시키거나 어긋나게 하는 관계.
const JIJI_YUKPA = ["자유", "축진", "인해", "묘오", "사신", "미술"];
// 지지 육해(六害) — 시기ㆍ구설ㆍ작은 갈등을 나타내는 관계(육충보다 약함).
const JIJI_YUKHAE = ["자미", "축오", "인사", "묘진", "신해", "유술"];

function normalizePair(a, b) {
  return [a + b, b + a];
}

function findInList(list, a, b) {
  const [p1, p2] = normalizePair(a, b);
  return list.includes(p1) || list.includes(p2);
}

function findInMap(map, a, b) {
  const [p1, p2] = normalizePair(a, b);
  if (map[p1] != null) return map[p1];
  if (map[p2] != null) return map[p2];
  return null;
}

function samhapGroupOf(zhi) {
  return Object.entries(JIJI_SAMHAP).find(([, members]) => members.includes(zhi)) || null;
}

/**
 * 두 지지(地支, 한글 1글자: 자ㆍ축ㆍ인...) 사이의 관계를 전부 판정한다.
 * "합이 파보다 우선"이라는 위 주석의 통설에 따라, 육합이 성립하면 육파 판정은 결과에
 * 넣지 않는다(같은 두 글자가 이론상 동시에 해당하는 유일한 조합인 인해에서만 실제로 발생).
 * @returns {object} { yukhap, samhap, yukchung, hyeong, yukpa, yukhae } — 해당 없으면 null.
 */
function jijiRelation(zhiA, zhiB) {
  const yukhapOheng = findInMap(JIJI_YUKHAP, zhiA, zhiB);
  const isYukhap = yukhapOheng != null;

  const groupA = samhapGroupOf(zhiA);
  const groupB = samhapGroupOf(zhiB);
  const samhap = groupA && groupB && groupA[0] === groupB[0] && zhiA !== zhiB ? groupA[0] : null;

  const yukchung = findInList(JIJI_YUKCHUNG, zhiA, zhiB);

  let hyeong = null;
  if (findInList(JIJI_SAMHYEONG_PAIRS, zhiA, zhiB)) hyeong = "형(삼형의 일부, 마찰ㆍ갈등 소지)";
  else if (findInList(JIJI_JAMYOHYEONG, zhiA, zhiB)) hyeong = "형(자묘형, 무례지형)";
  else if (zhiA === zhiB && JIJI_JAHYEONG.includes(zhiA + zhiA)) hyeong = "형(자형, 스스로와 부딪히는 기운)";

  const yukpa = !isYukhap && findInList(JIJI_YUKPA, zhiA, zhiB);
  const yukhae = findInList(JIJI_YUKHAE, zhiA, zhiB);

  return {
    yukhap: isYukhap ? { pair: zhiA + zhiB, element: yukhapOheng } : null,
    samhap: samhap ? { element: samhap, members: JIJI_SAMHAP[samhap] } : null,
    yukchung,
    hyeong,
    yukpa,
    yukhae,
  };
}

// ============================================================
// 십신(十神) 의미 사전 — saju.js의 SHI_SHEN_KO 번역값과 정확히 같은 한글 키를 쓴다(순환
// require를 피하려고 값을 새로 옮겨적지 않고 동일 문자열을 그대로 키로 사용).
// ============================================================
// 2026-08-24 재작성 — 사용자 지적: "월주의 천간인 병은 일간에게 편재입니다" 같은 문장이
// 나온 근본 원인이 바로 이 사전이었음(LLM이 여기 있는 압축된 명리학 전문 문체를 그대로
// 참고해서 옮겨 씀). "음양이 같음/다름", "내가 극하는" 같은 용어를 안 배운 사람도 바로
// 이해할 수 있도록, 완결된 문장으로 풀어서 다시 썼다 — 개념 자체는 그대로 유지하고
// 표현만 쉽게 바꿈(지어낸 내용 없음).
// 2026-08-30 수정 — 사용자 지시: "괄호(용어) 안의 내용이 주가 되어야 한다"는 원칙에 맞춰
// build_report.py의 삽입 형식을 "용어(뜻풀이)" → "뜻풀이(용어)"로 뒤집으면서, 종결어미로
// 끝나는 문장체("~합니다")가 아니라 뒤에 오는 명사(기운ㆍ자리ㆍ쪽)를 수식하는 관형구로
// 다시 씀 — 개념ㆍ정보는 그대로, 문장 구조만 바꿈(자동 diff 검증 완료, scratchpad/
// gloss_transform_validate.py 참고).
const SHI_SHEN_MEANING = {
  "비견": "나와 기운이 똑같은 존재로 형제자매나 동료 같으며, 힘을 합치면 든든하지만 같은 걸 두고 겨루게 되면 만만치 않은 경쟁자가 되기도 하는 자리",
  "겁재": "나와 비슷하지만 결이 살짝 다르며 경쟁자에 가깝고, 밀어붙이는 힘은 좋지만 그만큼 손에 쥔 재물이 빠져나가기 쉽다고 여겨지는 기운",
  "식신": "스스로 만들어내는 표현력과 생활의 활력을 뜻하며, 느긋하고 온화하게 자기만의 것을 빚어내는 창조력에 가까운 기운",
  "상관": "내가 만들어내는 기운 중에서도 좀 더 날카로우며, 재능과 말솜씨가 뛰어나고 발상이 자유롭지만 정해진 규칙과는 부딪히기 쉬운 쪽",
  "편재": "내가 다루는 재물 중에서도 흘러 다니며, 사업 수완이 좋아 여러 경로로 돈이 들어오지만 그만큼 씀씀이도 여기저기로 흩어지기 쉬운 쪽",
  "정재": "내가 다루는 재물 중에서도 차곡차곡 쌓이며, 성실하고 계획적으로 모으는 안정적인 수입이나 고정적인 벌이와 잘 맞는 쪽",
  "칠살(편관)": "나를 강하게 누르며 부담과 긴장이 따르고, 힘들게 느껴질 수 있지만 그만큼 도전정신과 밀어붙이는 추진력의 원천이 되기도 하는 기운",
  "정관": "나를 적당히 다스려주며 명예와 책임감을 뜻하고, 안정된 조직 생활ㆍ사회적으로 인정받는 자리와 잘 맞는 기운",
  "편인": "나를 키워주는 기운 중에서도 남다르며, 특별한 재능이나 직관이 뛰어나지만 독창적인 만큼 변덕스럽게 비칠 때도 있는 쪽",
  "정인": "나를 키워주며 학문이나 문서와 관련된 운을 뜻하고, 누군가에게 보호받는 듯한 안정감이나 인정받고 명예를 얻는 것과 관련이 깊은 기운",
};

// ============================================================
// 12운성(十二運星) 의미 사전 — saju.js의 DI_SHI_KO 번역값과 동일한 키.
// ============================================================
// 2026-08-24 재작성 — SHI_SHEN_MEANING과 같은 이유(위 주석 참고)로 완결된 문장체로 다시 씀.
const TWELVE_STAGE_MEANING = {
  "장생": "막 태어나는 순간의 기운입니다. 때묻지 않은 순수한 생명력과 새로운 출발을 뜻합니다.",
  "목욕": "갓 태어나 몸을 씻기는 시기입니다. 아직 여물지는 않았지만 변화가 많고 매력이 도드라지는, 다소 불안정한 기운입니다.",
  "관대": "갓을 쓰고 띠를 두르며 어른이 되어가는 시기입니다. 사회로 나갈 준비를 하며 자신감이 차오르는 기운입니다.",
  "임관": "나라의 녹봉을 받기 시작하는 시기입니다(건록이라고도 부릅니다). 실력을 인정받아 스스로의 힘으로 성취를 이루는 기운입니다.",
  "제왕": "인생에서 가장 왕성한 시기입니다. 강한 리더십과 주도권을 쥐지만, 정상에 선 만큼 외로움도 함께 따를 수 있습니다.",
  "쇠": "절정을 지나 차분해지는 시기입니다. 노련하고 원숙해지지만, 활동력은 서서히 줄어드는 기운입니다.",
  "병": "기운이 약해지기 시작하는 시기입니다. 예민해지고 자기 내면을 들여다보는 시간이 늘어납니다.",
  "사": "활동이 멈추는 시기입니다. 벌여둔 일을 정리하고 마무리하며, 깊은 생각에 잠기는 때입니다.",
  "묘": "지난 것을 갈무리해 저장해두는 시기입니다. 과거의 경험을 간직하는 기운이지만, 자칫 한자리에 머물러 정체될 수도 있습니다.",
  "절": "완전히 끊어지는 시기입니다. 다음 시작을 앞둔 공백기로, 겉보기엔 멈춘 듯해도 변화의 씨앗을 품고 있습니다.",
  "태": "새 생명이 잉태되는 시기입니다. 아직 겉으로 드러나지는 않았지만 가능성과 잠재력을 품은 기운입니다.",
  "양": "보살핌을 받으며 자라나는 시기입니다. 안정감과 온화함이 두드러지는 기운입니다.",
};

/**
 * saju.js의 computeSaju() 결과를 받아 correspondence(대응표 조회 결과) 객체를 만든다.
 * 이 손님의 실제 계산값(연지ㆍ우세오행ㆍ부족오행ㆍ사용된 십신ㆍ12운성)을 키로 삼아서만
 * 조회하므로, LLM이 "일반 명리학 지식"을 지어낼 필요 없이 이 필드를 그대로 옮기기만 하면
 * direct 답변이 된다(build_report.py SYSTEM_PROMPT 참고).
 * @param {object} sajuResult computeSaju()의 반환값
 * @returns {object} computed.json의 saju.correspondence에 들어갈 구조
 */
function buildCorrespondence(sajuResult) {
  const yearZhiKo = sajuResult.pillars.year.ganzhi_ko.slice(-1);
  const zodiac = ZODIAC[yearZhiKo] || null;

  const dominantOhengInfo = sajuResult.dominant_elements.map((e) => ({ oheng: e, ...OHENG_INFO[e] }));
  const missingOhengInfo = sajuResult.missing_elements.map((e) => ({ oheng: e, ...OHENG_INFO[e] }));

  // 실제로 이 손님의 네 기둥에 등장한 십신ㆍ12운성만 모아서 의미를 붙인다(등장 안 한 것까지
  // 전부 나열하면 "이 손님과 무관한 일반 지식"이 되므로 의도적으로 걸러냄).
  const usedShiShen = new Set();
  const usedStages = new Set();
  Object.values(sajuResult.pillars).forEach((p) => {
    if (!p) return;
    if (p.shi_shen_gan && p.shi_shen_gan !== "일주(일간 본인)") usedShiShen.add(p.shi_shen_gan);
    (p.shi_shen_zhi || []).forEach((s) => usedShiShen.add(s));
    if (p.twelve_stage) usedStages.add(p.twelve_stage);
  });

  return {
    zodiac: zodiac ? { zhi: yearZhiKo, ...zodiac } : null,
    dominant_oheng_lifestyle: dominantOhengInfo,
    missing_oheng_lifestyle: missingOhengInfo,
    shi_shen_meanings: [...usedShiShen].map((s) => ({ name: s, meaning: SHI_SHEN_MEANING[s] || null })),
    twelve_stage_meanings: [...usedStages].map((s) => ({ name: s, meaning: TWELVE_STAGE_MEANING[s] || null })),
    note: "색ㆍ방향ㆍ음식ㆍ직업ㆍ띠 성격은 명리학의 전통 상징 체계를 정리한 참고 정보이며, 과학적으로 검증된 사실이나 확정적 권고가 아님.",
  };
}

module.exports = {
  OHENG_INFO,
  ZODIAC,
  JIJI_YUKHAP,
  JIJI_SAMHAP,
  JIJI_YUKCHUNG,
  JIJI_YUKPA,
  JIJI_YUKHAE,
  SHI_SHEN_MEANING,
  TWELVE_STAGE_MEANING,
  ohengRelation,
  jijiRelation,
  buildCorrespondence,
};
