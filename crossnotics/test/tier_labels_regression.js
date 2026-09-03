/**
 * CN_TIERS systems ↔ systemLabels 정합성 회귀 테스트 — 2026-09-03.
 *
 * 배경: crossnotics/index.html의 CN_TIERS(고객 표시용)에서 두 건의 실제 불일치가
 * 발견됨.
 *  1) dual: systems에 tojeong이 있는데 systemLabels에 "토정비결"이 빠져 있었음(수정됨).
 *  2) premium: systems가 4개(saju/astrology/tarot/behavior)인데 systemLabels는
 *     3개뿐이라 "behavior"(행동DNA)의 고객 표시 라벨이 아예 없었음(수정됨) — behavior의
 *     공식 한글 표시명 "행동DNA"는 이 파일 안에서 이미 반복적으로 쓰이던 기존 용어를
 *     그대로 재사용함(91/411/532/733/792행 등, build_report.py:739도 동일 용어 사용 —
 *     새로 지어낸 라벨이 아님).
 *
 * 이 테스트는 "길이만 같다"가 아니라 "systems[i]가 실제로 그 한글 라벨을 의미하는가"까지
 * SYSTEM_LABEL_KO 매핑으로 검증한다 — 앞으로 새 tier/시스템 조합이 추가돼도 이 매핑에
 * 없는 systems 값이나 순서 어긋남을 자동으로 잡아낸다.
 *
 * 새 프레임워크 없이 plain Node + assert만 사용. 실행: node crossnotics/test/tier_labels_regression.js
 * 외부 API 호출 없음, 브라우저 없이 파일 파싱만으로 검증.
 */
const assert = require("assert");
const fs = require("fs");
const path = require("path");

const INDEX_HTML_PATH = path.join(__dirname, "..", "index.html");

// systems 키 → 고객 표시용 공식 한글 라벨. 프로젝트 기존 코드에서 실제로 쓰이는
// 명칭만 등록한다(behavior→"행동DNA"는 index.html/build_report.py에서 이미 확인된
// 기존 용어를 그대로 옮긴 것 — 새 명칭 발명 아님).
const SYSTEM_LABEL_KO = {
  saju: "사주",
  astrology: "별자리",
  tarot: "타로",
  behavior: "행동DNA",
  tojeong: "토정비결",
};

function extractCnTiers(html) {
  const startMarker = "const CN_TIERS = [";
  const startIdx = html.indexOf(startMarker);
  if (startIdx === -1) throw new Error("CN_TIERS 선언을 찾지 못함 — index.html 구조가 바뀌었을 수 있음");

  // 대괄호 짝을 직접 세어 배열 리터럴의 끝을 찾는다 — 정규식으로 nested object/array를
  // 안전하게 자르기 어려우므로 문자 단위 스캔을 쓴다.
  let depth = 0;
  let i = startIdx + startMarker.length - 1; // 첫 '[' 위치에서 시작
  let endIdx = -1;
  for (; i < html.length; i++) {
    const ch = html[i];
    if (ch === "[") depth++;
    else if (ch === "]") {
      depth--;
      if (depth === 0) {
        endIdx = i;
        break;
      }
    }
  }
  if (endIdx === -1) throw new Error("CN_TIERS 배열의 닫는 대괄호를 찾지 못함");

  const arrayLiteral = html.slice(startIdx + startMarker.length - 1, endIdx + 1);
  // eslint-disable-next-line no-eval -- 신뢰된 로컬 프로젝트 파일만 파싱하는 회귀
  // 테스트 전용 eval(외부 입력 아님, 사용자 데이터 아님).
  return eval(arrayLiteral);
}

function main() {
  const html = fs.readFileSync(INDEX_HTML_PATH, "utf-8");
  const tiers = extractCnTiers(html);
  assert.ok(Array.isArray(tiers) && tiers.length > 0, "CN_TIERS가 비어있거나 배열이 아님");

  const checks = [];

  // A + B — 모든 tier에서 길이 대응 + 위치별 의미 대응(systems[i] -> SYSTEM_LABEL_KO 매핑
  // 값과 systemLabels[i]가 정확히 같은지)을 전수 검사한다. 이번 STEP 1.1에서 premium까지
  // 고쳤으므로 더 이상 특정 tier를 예외 처리하지 않는다.
  for (const t of tiers) {
    const lengthOk = Array.isArray(t.systems) && Array.isArray(t.systemLabels) &&
      t.systems.length === t.systemLabels.length;
    checks.push([`${t.tierKey}: systems(${t.systems.length})/systemLabels(${t.systemLabels.length}) 길이 대응`, lengthOk]);

    if (lengthOk) {
      const mismatches = [];
      t.systems.forEach((sysKey, i) => {
        const expected = SYSTEM_LABEL_KO[sysKey];
        if (expected === undefined) {
          mismatches.push(`systems[${i}]="${sysKey}"의 공식 라벨이 SYSTEM_LABEL_KO에 없음(신규 시스템이면 매핑 추가 필요)`);
        } else if (t.systemLabels[i] !== expected) {
          mismatches.push(`systems[${i}]="${sysKey}" -> systemLabels[${i}]="${t.systemLabels[i]}"(기대값 "${expected}")`);
        }
      });
      checks.push([`${t.tierKey}: systems[i]<->systemLabels[i] 의미 대응`, mismatches.length === 0]);
      if (mismatches.length) mismatches.forEach((m) => console.log(`      - ${m}`));
    }
  }

  // C/D — premium 전용 확정값 확인(이번 STEP 1.1의 직접 목표).
  const premium = tiers.find((t) => t.tierKey === "premium");
  assert.ok(premium, "premium tier 항목을 찾지 못함");
  checks.push([
    "premium systems == [\"saju\",\"astrology\",\"tarot\",\"behavior\"]",
    JSON.stringify(premium.systems) === JSON.stringify(["saju", "astrology", "tarot", "behavior"]),
  ]);
  checks.push([
    "premium systemLabels == [\"사주\",\"별자리\",\"타로\",\"행동DNA\"]",
    JSON.stringify(premium.systemLabels) === JSON.stringify(["사주", "별자리", "타로", "행동DNA"]),
  ]);

  // E — 기존 dual 수정(STEP 1) 유지 확인.
  const dual = tiers.find((t) => t.tierKey === "dual");
  assert.ok(dual, "dual tier 항목을 찾지 못함");
  checks.push([
    "dual systems == [\"saju\",\"astrology\",\"tojeong\"]",
    JSON.stringify(dual.systems) === JSON.stringify(["saju", "astrology", "tojeong"]),
  ]);
  checks.push([
    "dual systemLabels == [\"사주\",\"별자리\",\"토정비결\"]",
    JSON.stringify(dual.systemLabels) === JSON.stringify(["사주", "별자리", "토정비결"]),
  ]);

  // F — mini/light/single/master는 이번 변경과 무관해야 함(스냅샷 가드).
  const expectedUnchanged = {
    mini: { systems: ["saju"], systemLabels: ["사주"] },
    light: { systems: ["saju"], systemLabels: ["사주"] },
    single: { systems: ["saju"], systemLabels: ["사주"] },
    master: { systems: ["saju", "astrology", "tarot"], systemLabels: ["사주", "별자리", "타로"] },
  };
  for (const [tierKey, expected] of Object.entries(expectedUnchanged)) {
    const t = tiers.find((x) => x.tierKey === tierKey);
    checks.push([`${tierKey} systems 미변경`, t && JSON.stringify(t.systems) === JSON.stringify(expected.systems)]);
    checks.push([`${tierKey} systemLabels 미변경`, t && JSON.stringify(t.systemLabels) === JSON.stringify(expected.systemLabels)]);
  }

  let failures = 0;
  for (const [label, ok] of checks) {
    console.log(`  ${label}: [${ok ? "PASS" : "FAIL"}]`);
    if (!ok) failures++;
  }

  if (failures > 0) {
    throw new Error(`${failures}건 실패`);
  }
  console.log("전체 PASS");
}

main();
