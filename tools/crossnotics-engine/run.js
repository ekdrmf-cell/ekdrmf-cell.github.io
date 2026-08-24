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

const { computeSaju, resolveSolarDate } = require("./saju.js");
const { computeAstrology } = require("./astrology.js");
const { computeTarot } = require("./tarot.js");
const { computeCorrelation } = require("./correlate.js");
const { computeGunghap } = require("./gunghap.js");
const { computeSynastry } = require("./synastry.js");
const { computeBehaviorProfile } = require("./behavior.js");
// 2026-08-23: 서비스허브의 site-checkout/lib/catalog.js에서 분리된 이 폴더의 로컬 가격표
const { getCrossnoticsTierConfig } = require("./catalog.js");

function main() {
  const [, , intakePath, outPath] = process.argv;
  if (!intakePath) {
    console.error("사용법: node run.js <intake.json> [출력경로]");
    process.exit(1);
  }

  const intake = JSON.parse(fs.readFileSync(path.resolve(intakePath), "utf8"));
  const systems = intake.systems_included || [];

  // 가격표(catalog.js)의 질문 개수 제한을 여기서 강제 — 초과 주문은 비싼 LLM 호출까지
  // 가기 전에 여기서 바로 걸러낸다(2026-08-21, 사용자가 확정한 "체계 개수+질문 개수"
  // 가격 구조를 실제로 지키게 하는 코드).
  const tierConfig = getCrossnoticsTierConfig(intake.tier);
  const questionCount = (intake.customer.questions || []).length;
  if (questionCount > tierConfig.question_limit) {
    throw new Error(
      `질문이 ${questionCount}개인데 "${intake.tier}" 티어는 최대 ${tierConfig.question_limit}개까지만 ` +
      `허용됨(${tierConfig.name}, ${tierConfig.price}원). 초과분을 빼거나 상위 티어로 안내할 것.`
    );
  }

  // 음력 생일이면 사주ㆍ점성술 두 엔진 모두 같은 양력 날짜를 써야 하므로 여기서 한 번만
  // 변환한다(saju.js에 따로 맡기면 astrology.js는 변환 안 된 음력 숫자를 양력인 것처럼
  // 받아 별자리가 완전히 틀어짐 — 2026-08-22 발견).
  const resolvedDate = resolveSolarDate({
    year: intake.customer.birth_year,
    month: intake.customer.birth_month,
    day: intake.customer.birth_day,
    calendarType: intake.customer.calendar_type || "solar",
    isLeapMonth: !!intake.customer.is_leap_month,
  });

  const result = {
    customer: intake.customer,
    tier: intake.tier,
    // build_report.py가 리포트 분량ㆍ깊이를 조절하는 데 쓰는 필드(mini/light/full) —
    // 여기서 catalog.js 값을 그대로 실어 보내서, 가격표와 리포트 프롬프트가 서로 다른
    // 파일에 따로 정의된 채 어긋나지 않게 한다.
    scope: tierConfig.scope,
    systems_included: systems,
    lunar_conversion_note: resolvedDate.lunar_conversion_note,
    generated_at_note: "타임스탬프는 배송 파이프라인(2단계)에서 채움 — 이 엔진은 순수 계산만 담당",
  };

  if (systems.includes("saju")) {
    result.saju = computeSaju({
      year: resolvedDate.year,
      month: resolvedDate.month,
      day: resolvedDate.day,
      hour: intake.customer.birth_hour,
      unknownTime: !!intake.customer.unknown_time,
      gender: intake.customer.gender, // "M" | "F"
    });
  }

  // intake.customer.partner의 양력 변환 날짜 — 사주 궁합(gunghap.js)과 점성술 시너스트리
  // (synastry.js)가 둘 다 상대방의 같은 생년월일을 다른 형식으로 필요로 해서 한 번만 계산해
  // 아래 두 블록에서 공유한다(위쪽 resolvedDate와 같은 이유로 여기서도 한 번만 변환해야
  // 사주ㆍ점성술이 서로 다른 날짜를 보는 사고를 막을 수 있음).
  const partnerResolved = intake.customer.partner
    ? resolveSolarDate({
        year: intake.customer.partner.birth_year,
        month: intake.customer.partner.birth_month,
        day: intake.customer.partner.birth_day,
        calendarType: intake.customer.partner.calendar_type || "solar",
        isLeapMonth: !!intake.customer.partner.is_leap_month,
      })
    : null;

  // 2026-08-23 추가 — 궁합 계산 엔진(gunghap.js). intake.customer.partner에 상대방 생년월일이
  // 있으면(사주가 계산 대상일 때만 의미가 있음) 상대방 사주까지 계산해 궁합을 산출한다.
  // CROSSNOTICS_HANDOFF.md "-7번"에서 지적된 구멍(상대방 정보 없어 궁합 질문이 전부
  // "redirected"였던 것)을 메움 — build_report.py는 이 필드가 있으면 궁합 질문을 "direct"로
  // 승격해 답한다.
  if (systems.includes("saju") && intake.customer.partner) {
    const partnerSaju = computeSaju({
      year: partnerResolved.year,
      month: partnerResolved.month,
      day: partnerResolved.day,
      hour: intake.customer.partner.birth_hour,
      unknownTime: !!intake.customer.partner.unknown_time,
      gender: intake.customer.partner.gender,
    });
    result.partner_saju = partnerSaju;
    // 2026-08-23 추가 — relationship_type(연인ㆍ동업ㆍ가족). 손님이 폼에서 선택 안 하면
    // "romantic"으로 기본 처리(gunghap.js의 기본값과 동일).
    result.gunghap = computeGunghap(result.saju, partnerSaju, intake.customer.partner.relationship_type);
  }

  if (systems.includes("astrology")) {
    if (intake.customer.latitude == null || intake.customer.longitude == null) {
      throw new Error("점성술 계산에는 출생지 위도/경도가 필요함 — intake.customer.latitude/longitude 확인");
    }
    result.astrology = computeAstrology({
      year: resolvedDate.year,
      month: resolvedDate.month,
      day: resolvedDate.day,
      hour: intake.customer.birth_hour,
      minute: intake.customer.birth_minute || 0,
      unknownTime: !!intake.customer.unknown_time,
      latitude: intake.customer.latitude,
      longitude: intake.customer.longitude,
    });

    // 2026-08-23 추가 — 점성술 시너스트리(synastry.js). 인수인계 문서 "B. 궁합 계산 엔진
    // 확장" 항목을 메움. 상대방의 출생 위경도까지 있어야만 상대방 네이탈 차트를 완전히
    // 계산할 수 있으므로(어센던트ㆍ하우스는 위경도와 무관하지만 astrology.js가 latitude/
    // longitude를 필수값으로 요구함), partner.latitude/longitude가 있을 때만 계산한다 —
    // 궁합(gunghap.js)은 상대방 생년월일만 있으면 되지만 시너스트리는 그보다 요구 조건이
    // 하나 더 있다는 뜻이라, gunghap과 다르게 이 조건을 따로 검사함.
    if (intake.customer.partner && intake.customer.partner.latitude != null && intake.customer.partner.longitude != null) {
      const partnerAstrology = computeAstrology({
        year: partnerResolved.year,
        month: partnerResolved.month,
        day: partnerResolved.day,
        hour: intake.customer.partner.birth_hour,
        minute: intake.customer.partner.birth_minute || 0,
        unknownTime: !!intake.customer.partner.unknown_time,
        latitude: intake.customer.partner.latitude,
        longitude: intake.customer.partner.longitude,
      });
      result.partner_astrology = partnerAstrology;
      result.astrology_synastry = computeSynastry(result.astrology, partnerAstrology);
    }
  }

  // 2026-08-24 추가 — 행동DNA(behavior.js). PREMIUM 전용, 손님이 신청 폼에서 실제로
  // 답한 15문항(customer.behavior_answers)이 있을 때만 계산한다 — 사주 궁합이
  // partner 정보 유무로 계산 여부를 가르는 것과 같은 패턴. 답변이 없으면 조용히
  // 건너뛴다(이 축을 안 물어본 티어에서 에러가 나면 안 되므로).
  if (systems.includes("behavior") && intake.customer.behavior_answers) {
    result.behavior = computeBehaviorProfile(intake.customer.behavior_answers);
  }

  if (systems.includes("tarot")) {
    // 백서/계획서 9번: 싱글ㆍ듀얼은 3장, 마스터ㆍ프리미엄은 켈틱크로스(10장) — 2026-08-22
    // premium(20만원) 신설 시 마스터와 같은 최상급 스프레드 유지.
    const spreadType = ["master", "premium"].includes(intake.tier) ? "celtic_cross" : "three_card";
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
