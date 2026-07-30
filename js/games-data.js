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
];
