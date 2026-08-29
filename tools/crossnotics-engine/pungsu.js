/*
 * 크로스노틱스 — 풍수지리(오행 기반 공간 배치) 계산 엔진.
 *
 * 2026-08-29 신설. 전통 풍수지리는 집터의 실제 지형ㆍ건물 방향(좌향)ㆍ주변 지세(배산임수
 * 등)까지 따지는 학문인데, 이 서비스는 손님의 생년월일시만 받고 실제 주소ㆍ건물 방향
 * 정보를 받지 않는다 — 그래서 그 부분은 계산 근거가 없어 다루지 않는다(1번 규칙). 대신
 * **이미 계산된 손님의 오행 우세ㆍ부족(saju.dominant_elements/missing_elements)을
 * 근거로, 부족한 기운을 보완하는 방향의 공간 활용법**만 다룬다 — correspondence.js의
 * OHENG_INFO(색ㆍ방향)를 그대로 재사용하고 새 표를 만들지 않는다(크로스노틱스 0번 원칙).
 *
 * 즉 이건 "이 집이 명당인가"를 보는 고전 풍수지리가 아니라, "부족한 오행을 방향ㆍ색으로
 * 보완하는 생활 풍수" 수준이라는 걸 methodology_note에 명확히 밝힌다.
 */
const { OHENG_INFO } = require("./correspondence.js");

// 공간별로 "그 공간의 성격상 어떤 목적에 오행 보완이 특히 잘 맞는지"만 짧게 다르게
// 써서, 같은 방향ㆍ색을 5번 복사한 것처럼 보이지 않게 한다.
const SPACES = [
  { key: "entrance", label: "현관", purpose: "밖의 기운이 처음 들어오는 자리라, 여기서 보완하면 하루의 시작 기운을 바꾸는 효과가 크다고 봅니다." },
  { key: "bedroom", label: "침실", purpose: "가장 오래 머무는 공간이라, 여기서 보완하면 몸에 스며드는 시간이 길어 효과가 누적된다고 봅니다." },
  { key: "desk", label: "책상ㆍ작업 공간", purpose: "집중력ㆍ판단력과 직결되는 자리라, 여기서 보완하면 일ㆍ공부의 흐름에 바로 영향을 준다고 봅니다." },
  { key: "living_room", label: "거실", purpose: "가족ㆍ손님을 맞는 공간이라, 여기서 보완하면 관계ㆍ소통의 기운에 영향을 준다고 봅니다." },
];

/**
 * @param {string[]} dominantElements saju.dominant_elements(우세 오행, 이미 계산됨)
 * @param {string[]} missingElements saju.missing_elements(부족 오행, 이미 계산됨)
 * @returns {object|null} computed.json의 saju.pungsu에 들어갈 구조. 부족한 오행이 없으면
 *   (오행이 전부 골고루 있는 드문 경우) recommendations는 빈 배열.
 */
function computePungsu(dominantElements, missingElements) {
  if (!missingElements) return null;

  const recommendations = missingElements
    .filter((o) => OHENG_INFO[o])
    .map((oheng) => ({
      oheng,
      color: OHENG_INFO[oheng].color,
      direction: OHENG_INFO[oheng].direction,
      spaces: SPACES.map((s) => ({ label: s.label, purpose: s.purpose })),
    }));

  const dominantNote = (dominantElements || [])
    .filter((o) => OHENG_INFO[o])
    .map((o) => `${o}(${OHENG_INFO[o].direction}) 기운은 이미 우세하니, 그 방향ㆍ색을 굳이 더 보태지 않아도 됩니다.`);

  return {
    dominant_elements: dominantElements || [],
    missing_elements: missingElements,
    recommendations,
    dominant_note: dominantNote,
    methodology_note:
      "이 서비스는 손님의 실제 주소ㆍ건물 방향 정보를 받지 않아, 지형ㆍ좌향까지 보는 " +
      "고전 풍수지리(집터가 명당인지 등)는 계산 근거가 없어 다루지 않습니다. 대신 이미 " +
      "계산된 손님의 오행 우세ㆍ부족을 근거로, 부족한 기운을 방향ㆍ색으로 보완하는 생활 " +
      "풍수 수준의 참고 정보만 제공합니다.",
  };
}

module.exports = { computePungsu };
