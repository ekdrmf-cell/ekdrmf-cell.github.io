/*
 * 크로스노틱스 엔진 스모크 테스트 — 샘플 intake 2건(싱글/마스터)을 실제로 돌려서
 * 에러 없이 computed.json이 나오는지, 각 필드가 채워지는지 확인한다.
 * 알려진 만세력/점성술 값과의 정확도 대조는 run.js 실행 후 사람이 결과를 직접 눈으로
 * 확인하는 방식으로 진행(계획서 "검증 방법" 1단계 항목).
 */
const { execSync } = require("child_process");
const path = require("path");
const fs = require("fs");

const cases = [
  { intake: "sample-intake-single.json", out: "out-single.json" },
  { intake: "sample-intake-master.json", out: "out-master.json" },
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
