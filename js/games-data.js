/*
 * 게임 목록 — 새 게임을 추가할 때는 이 배열에 한 줄만 추가하면
 * 홈 화면과 게임 목록 페이지에 자동으로 노출됩니다.
 */
const GAMES = [
  {
    id: "2048",
    title: "2048 퍼즐",
    genre: "퍼즐",
    emoji: "🧩",
    desc: "숫자를 합쳐 2048을 만드는 캐주얼 퍼즐. 짧은 세션, 높은 재도전율.",
    path: "games/2048/index.html",
  },
  {
    id: "runner",
    title: "장애물 러너",
    genre: "아케이드",
    emoji: "🏃",
    desc: "점프로 장애물을 피하며 최고 기록에 도전하는 엔드리스 러너.",
    path: "games/runner/index.html",
  },
  {
    id: "match3",
    title: "매치3 캔디",
    genre: "퍼즐",
    emoji: "🍬",
    desc: "인접한 캔디를 맞바꿔 3개 이상을 맞추고 제한된 이동 횟수 안에 최고 점수에 도전하는 퍼즐 게임입니다.",
    path: "games/match3/index.html",
  },
  {
    id: "whackamole",
    title: "두더지 잡기",
    genre: "아케이드",
    emoji: "🐹",
    desc: "제한시간 60초 동안 구멍에서 튀어나오는 두더지를 최대한 많이 잡아 점수를 올리는 반사신경 게임입니다.",
    path: "games/whackamole/index.html",
  },
  {
    id: "memory",
    title: "카드 짝맞추기",
    genre: "카드",
    emoji: "🃏",
    desc: "카드를 뒤집어 같은 그림끼리 짝을 맞추는 두뇌 트레이닝 게임입니다.",
    path: "games/memory/index.html",
  },
  {
    id: "quiz",
    title: "상식퀴즈 챌린지",
    genre: "퀴즈",
    emoji: "🧠",
    desc: "4지선다 상식 문제를 풀며 목숨이 다하기 전까지 최고 점수에 도전하는 퀴즈 게임입니다.",
    path: "games/quiz/index.html",
  },
];
