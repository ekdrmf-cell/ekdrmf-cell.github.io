/*
 * 크로스노틱스 — 육효(六爻)/주역(周易) 계산 엔진.
 *
 * 2026-08-29 신설. 사주ㆍ점성술처럼 생년월일 기반이 아니라, "지금 이 순간의 질문"에
 * 대해 그 자리에서 괘를 뽑는 방식이다(전통적으로 동전 3개를 던져 효 하나씩 6번 뽑음) —
 * tarot.js가 Math.random()으로 그 자리에서 카드를 뽑는 것과 같은 성격의 도구라, 같은
 * 피셔-예이츠/무작위 원칙을 그대로 따른다.
 *
 * 동전 3개 던지기(3전법) — 표준 방식: 동전 하나가 앞이면 3, 뒤면 2로 치고 세 개를 더해
 * 6/7/8/9 중 하나가 나온다. 6=노음(변효, 지금은 음ㆍ변한 뒤엔 양), 7=소양(양ㆍ안 변함),
 * 8=소음(음ㆍ안 변함), 9=노양(변효, 지금은 양ㆍ변한 뒤엔 음). 이 여섯 효를 아래부터
 * 위로 쌓아 하괘(1~3번째 효)ㆍ상괘(4~6번째 효) 3효씩 묶어 팔괘 하나씩을 이룬다.
 *
 * 3효 조합 → 팔괘 이름 매핑은 라이프니츠가 정리한 것으로 알려진 표준 이진수 표기를
 * 그대로 따른다(2026-08-29 검증 — 나무위키/위키백과 교차확인): 건=111, 태=110, 리=101,
 * 진=100, 손=011, 감=010, 간=001, 곤=000 (맨 아래 효가 가장 오른쪽 자리, 양=1ㆍ음=0).
 *
 * 8괘 각각의 뜻풀이는 tojeong.js의 SANGGWAE_MEANING(상괘 8개 풀이)을 그대로 재사용한다 —
 * 토정비결의 상괘도, 육효의 상ㆍ하괘도 결국 같은 팔괘 여덟 개이므로 새 풀이를 또 만들지
 * 않는다(크로스노틱스 0번 원칙, 내용 중복 방지).
 */
const { SANGGWAE_MEANING } = require("./tojeong.js");

// 3효(아래→위, 1=양ㆍ0=음)를 이어붙인 문자열 → 팔괘 번호(SANGGWAE_MEANING의 키와 동일:
// 1건 2태 3리 4진 5손 6감 7간 8곤).
const TRIGRAM_BY_BITS = {
  "111": 1, "110": 2, "101": 3, "100": 4,
  "011": 5, "010": 6, "001": 7, "000": 8,
};

function tossCoinLine() {
  const coins = [0, 0, 0].map(() => (Math.random() < 0.5 ? 3 : 2));
  const sum = coins[0] + coins[1] + coins[2];
  // sum: 6=노음(변효,현재음) 7=소양(현재양) 8=소음(현재음) 9=노양(변효,현재양)
  const current = sum === 7 || sum === 9 ? 1 : 0; // 1=양, 0=음
  const changing = sum === 6 || sum === 9;
  return { sum, current, changing };
}

function trigramFromLines(lines) {
  // lines: 아래→위 3개, 각 {current}
  const bits = lines.map((l) => l.current).join("");
  return TRIGRAM_BY_BITS[bits];
}

/**
 * @returns {object} computed.json의 saju.yukhyo에 그대로 들어갈 구조. 매번 그 자리에서
 *   새로 뽑으므로 tarot.js처럼 항상 값이 있고 null이 없다(생년월일이 아니라 즉석에서
 *   무작위로 뽑는 도구라서).
 */
function computeYukhyo() {
  const lines = Array.from({ length: 6 }, () => tossCoinLine());
  const haGwaeLines = lines.slice(0, 3);
  const sangGwaeLines = lines.slice(3, 6);

  const haGwae = trigramFromLines(haGwaeLines);
  const sangGwae = trigramFromLines(sangGwaeLines);

  const changingIndexes = lines.map((l, i) => (l.changing ? i + 1 : null)).filter(Boolean); // 1~6번째 효

  let jiGwae = null;
  if (changingIndexes.length > 0) {
    const changedLines = lines.map((l) => ({ current: l.changing ? 1 - l.current : l.current }));
    jiGwae = {
      ha: trigramFromLines(changedLines.slice(0, 3)),
      sang: trigramFromLines(changedLines.slice(3, 6)),
    };
  }

  return {
    lines: lines.map((l, i) => ({ position: i + 1, yang: !!l.current, changing: l.changing })),
    bon_gwae: { // 본괘 — 지금 상황을 나타내는 현재 괘
      ha: haGwae, sang: sangGwae,
      ha_meaning: SANGGWAE_MEANING[haGwae], sang_meaning: SANGGWAE_MEANING[sangGwae],
    },
    ji_gwae: jiGwae && { // 지괘 — 변효가 있을 때만, 변화 이후를 나타내는 괘
      ha: jiGwae.ha, sang: jiGwae.sang,
      ha_meaning: SANGGWAE_MEANING[jiGwae.ha], sang_meaning: SANGGWAE_MEANING[jiGwae.sang],
    },
    changing_line_count: changingIndexes.length,
    methodology_note:
      "동전 3개를 6번 던지는 전통 3전법을 그대로 재현(무작위). 하괘(아래 3효)ㆍ상괘(위 " +
      "3효) 조합으로 지금 상황을 보는 본괘를 얻고, 변하는 효(변효)가 있으면 그 변화 " +
      "이후를 보는 지괘도 함께 얻는다. 생년월일이 아니라 질문을 던진 지금 이 순간을 " +
      "보는 도구라, 같은 질문이라도 다시 물으면 다른 괘가 나올 수 있다는 게 전통적 원리다.",
  };
}

module.exports = { computeYukhyo };
