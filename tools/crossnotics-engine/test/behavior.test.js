/*
 * 행동DNA 엔진(behavior.js) 단위 테스트 — 채점 로직이 설계대로 동작하는지 확인.
 * run-all.js의 intake→computed.json 스모크 테스트와 달리, 이건 아직 run.js에
 * 연결되기 전(폼ㆍintake 스키마 작업 전) 채점 함수 자체만 독립적으로 검증한다.
 */
const assert = require("assert");
const { BEHAVIOR_QUESTIONS, computeBehaviorProfile } = require("../behavior.js");

let failed = 0;
function check(label, fn) {
  try {
    fn();
    console.log(`✅ ${label}`);
  } catch (e) {
    failed += 1;
    console.error(`❌ ${label}:`, e.message);
  }
}

check("문항 수는 15개(5축 x 3문항)", () => {
  assert.strictEqual(BEHAVIOR_QUESTIONS.length, 15);
});

check("전부 A(적극) 응답 → 모든 축이 적극/일관됨, 정보수집 0", () => {
  const answers = Array(15).fill("A");
  const result = computeBehaviorProfile(answers);
  assert.strictEqual(result.axes.length, 5);
  result.axes.forEach((a) => {
    assert.strictEqual(a.pattern, "적극");
    assert.strictEqual(a.strength, "일관됨");
    assert.strictEqual(a.infoSeekingCount, 0);
  });
});

check("전부 D(정보수집) 응답 → 모든 축이 판단보류형", () => {
  const answers = Array(15).fill("D");
  const result = computeBehaviorProfile(answers);
  result.axes.forEach((a) => {
    assert.strictEqual(a.pattern, "판단보류형");
    assert.strictEqual(a.infoSeekingCount, 3);
  });
});

check("한 축 안에서 A/B/C가 갈리면 상황에 따라 유동적", () => {
  // 위험 감수 성향(0,1,2번 문항)만 A,B,C로 갈라지게, 나머지는 전부 A
  const answers = Array(15).fill("A");
  answers[0] = "A";
  answers[1] = "B";
  answers[2] = "C";
  const result = computeBehaviorProfile(answers);
  const risk = result.axes.find((a) => a.axis === "risk_tolerance");
  assert.strictEqual(risk.pattern, "상황에 따라 유동적");
  const boundary = result.axes.find((a) => a.axis === "boundary_setting");
  assert.strictEqual(boundary.pattern, "적극");
  assert.strictEqual(boundary.strength, "일관됨");
});

check("2/3 우세는 '우세'로, 3/3 일치는 '일관됨'으로 구분", () => {
  const answers = Array(15).fill("C");
  answers[0] = "C";
  answers[1] = "C";
  answers[2] = "A"; // risk_tolerance: C,C,A → C 우세(2/3)
  const result = computeBehaviorProfile(answers);
  const risk = result.axes.find((a) => a.axis === "risk_tolerance");
  assert.strictEqual(risk.pattern, "회피");
  assert.strictEqual(risk.strength, "우세");
});

check("답변 개수가 다르면 에러", () => {
  assert.throws(() => computeBehaviorProfile(Array(14).fill("A")));
});

check("잘못된 답변 문자(E 등)는 에러", () => {
  const answers = Array(15).fill("A");
  answers[0] = "E";
  assert.throws(() => computeBehaviorProfile(answers));
});

console.log(failed === 0 ? "\n전체 통과" : `\n${failed}건 실패`);
process.exit(failed === 0 ? 0 : 1);
