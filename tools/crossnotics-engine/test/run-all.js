/*
 * 크로스노틱스 엔진 스모크 테스트 — 샘플 intake 3건(사주단독/사주+별자리/전체)을 실제로
 * 돌려서 에러 없이 computed.json이 나오는지, 각 필드가 채워지는지, 질문 개수 제한이
 * 정상 통과하는지 확인한다(초과 케이스는 test/sample-intake-overlimit.json으로 수동
 * 확인 — 의도적으로 에러가 나야 정상이라 이 스모크 테스트엔 안 넣음).
 * 알려진 만세력/점성술 값과의 정확도 대조는 run.js 실행 후 사람이 결과를 직접 눈으로
 * 확인하는 방식으로 진행(계획서 "검증 방법" 1단계 항목).
 */
const { execSync } = require("child_process");
const path = require("path");
const fs = require("fs");

const cases = [
  { intake: "sample-intake-single.json", out: "out-single.json" },
  { intake: "sample-intake-dual.json", out: "out-dual.json" },
  { intake: "sample-intake-master.json", out: "out-master.json" },
  // 2026-08-23 추가 — 궁합 계산 엔진(gunghap.js) 스모크 테스트. partner 정보가 있으면
  // computed.json에 gunghap 필드가 채워지는지 확인한다.
  { intake: "sample-intake-gunghap.json", out: "out-gunghap.json" },
  // 2026-08-23 추가 — 점성술 시너스트리(synastry.js) 스모크 테스트. partner에 위경도까지
  // 있으면 computed.json에 astrology_synastry 필드가 채워지는지 확인한다.
  { intake: "sample-intake-synastry.json", out: "out-synastry.json" },
];

let allOk = true;
for (const c of cases) {
  const intakePath = path.join(__dirname, c.intake);
  const outPath = path.join(__dirname, c.out);
  try {
    execSync(`node "${path.join(__dirname, "..", "run.js")}" "${intakePath}" "${outPath}"`, { stdio: "pipe" });
    const result = JSON.parse(fs.readFileSync(outPath, "utf8"));
    console.log(`✅ ${c.intake} → tier=${result.tier}, systems=${result.systems_included.join(",")}, correlation.mode=${result.correlation.mode}`);
  } catch (e) {
    allOk = false;
    console.error(`❌ ${c.intake} 실패:`, e.message);
  }
}
process.exit(allOk ? 0 : 1);
