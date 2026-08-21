#!/usr/bin/env node
/*
 * 크로스노틱스 계산 엔진 — CLI 진입점.
 * 사용법: node run.js <intake.json> [출력경로]
 * intake.json 예시는 test/sample-intake-master.json 참고.
 *
 * intake의 tier/systems_included에 따라 필요한 엔진만 돌리고, computed.json 하나로
 * 합쳐서 출력한다(계획서 1번 파이프라인의 1단계 — 이 결과물을 사람이 먼저 검증한 뒤에만
 * 2단계 Python/LLM 파이프라인으로 넘긴다).
 */
const fs = require("fs");
const path = require("path");

const { computeSaju } = require("./saju.js");
const { computeAstrology } = require("./astrology.js");
const { computeTarot } = require("./tarot.js");
const { computeCorrelation } = require("./correlate.js");

function main() {
  const [, , intakePath, outPath] = process.argv;
  if (!intakePath) {
    console.error("사용법: node run.js <intake.json> [출력경로]");
    process.exit(1);
  }

  const intake = JSON.parse(fs.readFileSync(path.resolve(intakePath), "utf8"));
  const systems = intake.systems_included || [];
  const result = {
    customer: intake.customer,
    tier: intake.tier,
    systems_included: systems,
    generated_at_note: "타임스탬프는 배송 파이프라인(2단계)에서 채움 — 이 엔진은 순수 계산만 담당",
  };

  if (systems.includes("saju")) {
    result.saju = computeSaju({
      year: intake.customer.birth_year,
      month: intake.customer.birth_month,
      day: intake.customer.birth_day,
      hour: intake.customer.birth_hour,
      unknownTime: !!intake.customer.unknown_time,
      gender: intake.customer.gender, // "M" | "F"
    });
  }

  if (systems.includes("astrology")) {
    if (intake.customer.latitude == null || intake.customer.longitude == null) {
      throw new Error("점성술 계산에는 출생지 위도/경도가 필요함 — intake.customer.latitude/longitude 확인");
    }
    result.astrology = computeAstrology({
      year: intake.customer.birth_year,
      month: intake.customer.birth_month,
      day: intake.customer.birth_day,
      hour: intake.customer.birth_hour,
      minute: intake.customer.birth_minute || 0,
      unknownTime: !!intake.customer.unknown_time,
      latitude: intake.customer.latitude,
      longitude: intake.customer.longitude,
    });
  }

  if (systems.includes("tarot")) {
    // 백서/계획서 9번: 싱글ㆍ듀얼은 3장, 마스터는 켈틱크로스(10장)
    const spreadType = intake.tier === "master" ? "celtic_cross" : "three_card";
    result.tarot = computeTarot({ spreadType });
  }

  result.correlation = computeCorrelation({
    saju: result.saju,
    astrology: result.astrology,
    tarot: result.tarot,
  });

  const outputPath = path.resolve(outPath || "computed.json");
  fs.writeFileSync(outputPath, JSON.stringify(result, null, 2), "utf8");
  console.log(`완료: ${outputPath}`);
}

main();
