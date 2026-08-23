/*
 * 천지인운명관 무료 도구 목록 — 새 도구를 추가할 때는 이 배열에 한 줄만 추가하면
 * 운세 허브 페이지(unse/index.html)에 자동으로 노출됩니다.
 * 2026-08-23: 서비스허브의 js/unse-data.js에서 이전됨(내용 전체가 천지인운명관 전용이라
 * 공유 폴더에 있을 이유가 없었음 — 서비스허브ㆍ천지인운명관 분리 작업의 일부).
 */
const UNSE_TOOLS = [
  {
    id: "saju",
    title: "무료 사주 계산기",
    emoji: "🔮",
    desc: "생년월일시로 띠·별자리·타고난 기운을 쉬운 말로 바로 확인",
    path: "saju/index.html",
  },
  {
    id: "gunghap",
    title: "무료 궁합 계산기",
    emoji: "💑",
    desc: "두 사람의 기운이 서로 어떻게 어우러지는지 확인",
    path: "gunghap/index.html",
  },
  {
    id: "tarot",
    title: "무료 타로 한 장 뽑기",
    emoji: "🃏",
    desc: "궁금한 걸 떠올리고 카드 한 장으로 보는 오늘의 메시지",
    path: "tarot/index.html",
  },
  {
    id: "dream",
    title: "무료 꿈해몽 검색",
    emoji: "💭",
    desc: "꿈에 나온 대상을 검색하면 전통 해몽 풀이를 바로 확인",
    path: "dream/index.html",
  },
  {
    id: "bloodtype",
    title: "혈액형 성격 테스트",
    emoji: "🩸",
    desc: "A·B·O·AB형 성격 특징과 잘 맞는 상대 확인",
    path: "bloodtype/index.html",
  },
  {
    id: "name",
    title: "이름 발음오행 분석",
    emoji: "🈶",
    desc: "이름 소리의 오행 흐름을 무료로 확인",
    path: "name/index.html",
  },
];
