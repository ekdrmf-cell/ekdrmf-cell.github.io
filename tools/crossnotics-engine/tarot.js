/*
 * 크로스노틱스 — 타로 셔플/스프레드 엔진.
 * 기존 무료 도구(tarot/js/tarot-data.js)는 22장 메이저 아르카나 중 1장을 Math.random()으로
 * 뽑기만 했다 — 셔플/스프레드/역방향 로직이 아예 없었음. 여기서는 진짜 카드게임처럼
 * Fisher-Yates 셔플로 덱을 섞고, 포지션별로 카드를 배분하며, 정/역방향을 무작위 결정한다.
 *
 * 마이너 아르카나 56장(수트별 핍카드+코트카드) 콘텐츠 집필은 백서 2단계(콘텐츠 작업)로 분리돼
 * 아직 없음 — 지금은 기존 22장 메이저 아르카나 데이터로 엔진 매커니즘을 완성한다. 78장 데이터가
 * 채워지면 DECK 배열만 교체하면 되도록 구조를 짜둔다.
 */
const path = require("path");

// tarot/js/tarot-data.js는 브라우저 전역(const TAROT_DECK)이라 Node에서 그대로 require할 수
// 없다 — 파일을 읽어서 배열 리터럴만 안전하게 추출한다(외부 코드 실행 없이 값만 가져옴).
function loadMajorArcana() {
  const fs = require("fs");
  const filePath = path.resolve(__dirname, "../../tarot/js/tarot-data.js");
  const src = fs.readFileSync(filePath, "utf8");
  const match = src.match(/const TAROT_DECK = (\[[\s\S]*?\]);/);
  if (!match) throw new Error("tarot-data.js에서 TAROT_DECK 배열을 찾지 못함");
  // eslint-disable-next-line no-eval
  return eval(match[1]);
}

const MAJOR_ARCANA = loadMajorArcana();
const DECK_COMPLETENESS_NOTE = `현재 메이저 아르카나 22장만 있음(마이너 아르카나 56장은 아직 미집필,
CROSSNOTICS 백서 2단계 콘텐츠 작업 대상) — 78장 완성 전까지는 이 22장 범위 내에서만 뽑는다.`;

const SPREADS = {
  three_card: {
    label: "3장 스프레드(과거-현재-미래)",
    positions: ["과거", "현재", "미래"],
  },
  celtic_cross: {
    label: "켈틱 크로스(10장)",
    positions: [
      "현재 상황", "당면 과제(장애물)", "의식 속 목표", "무의식의 기반",
      "가까운 과거", "가까운 미래", "본인의 태도", "주변 환경/영향",
      "희망 또는 두려움", "최종 결과",
    ],
  },
};

function fisherYatesShuffle(arr) {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

/**
 * @param {object} input {spreadType: "three_card"|"celtic_cross"}
 * @returns {object} computed.json의 "tarot" 필드에 그대로 들어갈 구조
 */
function computeTarot(input) {
  const spreadKey = input.spreadType || "three_card";
  const spread = SPREADS[spreadKey];
  if (!spread) throw new Error(`알 수 없는 스프레드: ${spreadKey}`);
  if (spread.positions.length > MAJOR_ARCANA.length) {
    throw new Error(`덱(${MAJOR_ARCANA.length}장)이 스프레드 포지션 수(${spread.positions.length})보다 적음`);
  }

  const shuffled = fisherYatesShuffle(MAJOR_ARCANA);
  const draws = spread.positions.map((position, i) => {
    const card = shuffled[i];
    const orientation = Math.random() < 0.5 ? "역방향" : "정방향";
    return {
      position,
      card_name: card.name,
      keyword: card.keyword,
      upright_text: card.text,
      orientation,
      orientation_note:
        orientation === "역방향"
          ? "역방향 — 카드 에너지가 막혀있거나 내면화된 상태로 해석(정방향 의미의 반대ㆍ지연ㆍ내적 버전)"
          : null,
    };
  });

  return {
    spread_type: spread.label,
    deck_completeness_note: DECK_COMPLETENESS_NOTE,
    draws,
  };
}

module.exports = { computeTarot, SPREADS, MAJOR_ARCANA };
