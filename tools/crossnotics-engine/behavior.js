/*
 * 크로스노틱스 — 행동DNA(behavior pattern) 계산 엔진.
 * PREMIUM(20만원) 전용. "당신은 왜 그런 선택을 하고, 어디로 향하고 있는가?"를 실제로
 * 계산하기 위한 모듈 — 손님에게 상황극 15문항(성향 축 5개 × 문항 3개)을 묻고, 그 실제
 * 답변 패턴을 이 파일이 결정론적으로 채점한다. LLM은 이미 채점된 결과를 문장으로
 * 옮기기만 하고, "이 사람은 이런 성향이다"를 스스로 판단해서 지어내지 않는다
 * (gunghap.js/correlate.js와 동일한 설계 철학).
 *
 * "행동DNA"라는 이름은 실제 생물학적 유전자와 무관한 비유적 이름이다 — 여러 상황에서
 * 반복되는 선택 패턴을 가리키는 닉네임일 뿐, 유전자 검사를 했다는 뜻이 아니다(2026-08-24
 * 사용자와의 논의로 확정 — 사주ㆍMBTI와 같은 카테고리: 손님이 실제로 답한 진짜 데이터를
 * 결정론적으로 채점하는 시스템).
 *
 * ============================================================
 * 설계 원칙 (2026-08-24 사용자와 합의된 기준)
 * ============================================================
 * 1. 질문은 "당신은 외향적인가요?" 같은 직접 질문이 아니라 상황극(situational judgment)
 *    으로 묻는다 — 사회적으로 바람직해 보이는 답을 고르게 되는 걸 줄이기 위함.
 * 2. 같은 축을 도메인(돈ㆍ시간ㆍ관계ㆍ직장ㆍ가족 등)을 바꿔가며 3번 반복 측정한다 —
 *    표면적 응답이 아니라 반복되는 패턴을 잡기 위함(1번만 물으면 우연과 구분 안 됨).
 *    답이 매번 갈리면(예: 3개 중 1승1무1패) "상황에 따라 유동적"이라는 것 자체가 진짜
 *    신호이지, 억지로 하나의 유형으로 몰아넣지 않는다(근거 없는 확신 금지 원칙과 동일).
 * 3. 축은 사주ㆍ별자리가 이미 말하고 있는 것과 교차검증할 수 있도록 골랐다(crossRef
 *    필드) — "여러 렌즈가 겹칠수록, 상은 선명해집니다"라는 사이트 철학을 행동 데이터에도
 *    그대로 적용. build_report.py가 이 crossRef를 참고해 사주/별자리 신호와 실제로
 *    같은 방향을 가리키는지 비교 서술한다.
 * 4. A=적극/직진, B=절충, C=회피/신중, D=정보수집형(주축 방향 채점에서는 제외하고
 *    "즉흥성 대 계획성" 축과는 별개로 참고 지표로만 집계) — 이 방향 매핑은 축 전체에서
 *    통일했다(한 축 안에서 시나리오마다 A의 의미가 달라지면 패턴을 셀 수 없음).
 */

const AXES = [
  {
    key: "risk_tolerance",
    label: "위험 감수 성향",
    crossRef:
      "사주: 화ㆍ목 기운이 강하면 진취적, 수ㆍ금 기운이 강하면 신중한 경향으로 전통적으로 봄. " +
      "별자리: 불 원소(양자리ㆍ사자자리ㆍ사수자리)는 대담함, 흙 원소는 신중함과 연결됨.",
  },
  {
    key: "boundary_setting",
    label: "관계 경계 설정",
    crossRef:
      "사주: 비겁(비견ㆍ겁재)이 강하면 나누는 쪽, 재성(정재ㆍ편재)이 강하면 지키는 쪽에 가까운 경향. " +
      "별자리: 금성의 위치, 2/7하우스가 관계에서의 경계ㆍ소유 감각과 연결됨.",
  },
  {
    key: "trust_verification",
    label: "신뢰ㆍ검증 성향",
    crossRef:
      "사주: 정인ㆍ편인이 강하면 직관적 신뢰, 화개살은 혼자 판단하는 경향과 연결됨. " +
      "별자리: 물 원소는 직관적 신뢰, 공기 원소는 논리적 검증을 우선하는 경향과 연결됨.",
  },
  {
    key: "spontaneity_planning",
    label: "즉흥성 대 계획성",
    crossRef:
      "사주 12운성: 관대ㆍ제왕 단계는 적극적 실행, 쇠ㆍ병ㆍ사 단계는 신중한 준비와 연결됨. " +
      "별자리: 변통궁(쌍둥이ㆍ처녀ㆍ사수ㆍ물고기)은 즉흥적, 활동궁ㆍ고정궁은 계획적인 경향과 연결됨.",
  },
  {
    key: "conflict_response",
    label: "갈등 대응 방식",
    crossRef:
      "사주: 칠살(편관)이 강하면 정면 대응, 상관이 강하면 직설적 표현과 연결됨. " +
      "별자리: 화성의 위치가 추진력ㆍ대응 방식과 연결됨.",
  },
];

// direction: "적극" | "절충" | "회피" | "정보수집" — 축 전체에서 A/B/C/D 의미를 통일.
const BEHAVIOR_QUESTIONS = [
  // --- 위험 감수 성향 ---
  {
    axis: "risk_tolerance",
    situation: "친한 사람이 갚을 가능성이 낮다는 걸 알면서도 100만원을 빌려달라고 한다.",
    options: [
      { key: "A", text: "빌려준다", direction: "적극" },
      { key: "B", text: "일부만 빌려준다", direction: "절충" },
      { key: "C", text: "거절한다", direction: "회피" },
      { key: "D", text: "이유를 듣고 결정한다", direction: "정보수집" },
    ],
  },
  {
    axis: "risk_tolerance",
    situation: "몇 달간 준비한 프로젝트가 막판에 예산 문제로 취소될 위기다. 성공 확률은 낮지만 며칠 밤을 새우면 살릴 수도 있다.",
    options: [
      { key: "A", text: "끝까지 매달린다", direction: "적극" },
      { key: "B", text: "되는 데까지만 해본다", direction: "절충" },
      { key: "C", text: "깔끔하게 접는다", direction: "회피" },
      { key: "D", text: "다른 사람 의견부터 구한다", direction: "정보수집" },
    ],
  },
  {
    axis: "risk_tolerance",
    situation: "동업자가 손실 위험은 있지만 잘되면 큰 사업 확장을 제안한다.",
    options: [
      { key: "A", text: "동참한다", direction: "적극" },
      { key: "B", text: "일부만 투자한다", direction: "절충" },
      { key: "C", text: "거절한다", direction: "회피" },
      { key: "D", text: "더 알아보고 결정한다", direction: "정보수집" },
    ],
  },
  // --- 관계 경계 설정 ---
  {
    axis: "boundary_setting",
    situation: "친구가 술자리에서 계속 무리한 부탁을 한다.",
    options: [
      { key: "A", text: "들어준다", direction: "적극" },
      { key: "B", text: "한 번은 들어주고 다음부턴 선을 긋는다", direction: "절충" },
      { key: "C", text: "그 자리에서 거절한다", direction: "회피" },
      { key: "D", text: "농담으로 넘기며 피한다", direction: "정보수집" },
    ],
  },
  {
    axis: "boundary_setting",
    situation: "가족이 상의 없이 내 물건을 남에게 빌려줬다.",
    options: [
      { key: "A", text: "넘어간다", direction: "적극" },
      { key: "B", text: "다음에 조용히 얘기한다", direction: "절충" },
      { key: "C", text: "그 자리에서 바로 말한다", direction: "회피" },
      { key: "D", text: "서운함을 감추고 참는다", direction: "정보수집" },
    ],
  },
  {
    axis: "boundary_setting",
    situation: "동료가 자기 업무를 습관적으로 나에게 떠넘긴다.",
    options: [
      { key: "A", text: "계속 도와준다", direction: "적극" },
      { key: "B", text: "이번까지만 돕고 다음부턴 거절한다", direction: "절충" },
      { key: "C", text: "바로 선을 긋고 거절한다", direction: "회피" },
      { key: "D", text: "상사에게 먼저 알린다", direction: "정보수집" },
    ],
  },
  // --- 신뢰ㆍ검증 성향 ---
  {
    axis: "trust_verification",
    situation: "처음 만난 사람이 좋은 투자 정보라며 함께하자고 한다.",
    options: [
      { key: "A", text: "바로 믿고 함께한다", direction: "적극" },
      { key: "B", text: "관심은 가지되 직접 알아본다", direction: "절충" },
      { key: "C", text: "일단 거리를 둔다", direction: "회피" },
      { key: "D", text: "주변 사람에게 물어본다", direction: "정보수집" },
    ],
  },
  {
    axis: "trust_verification",
    situation: "새로 알게 된 사람이 첫 만남부터 아주 친근하게 다가온다.",
    options: [
      { key: "A", text: "나도 편하게 마음을 연다", direction: "적극" },
      { key: "B", text: "좋게 보되 시간을 두고 지켜본다", direction: "절충" },
      { key: "C", text: "다소 경계하며 거리를 둔다", direction: "회피" },
      { key: "D", text: "그 사람의 행동을 유심히 관찰한다", direction: "정보수집" },
    ],
  },
  {
    axis: "trust_verification",
    situation: "SNS에서 본 놀라운 소식을 지인이 사실이라며 전해준다.",
    options: [
      { key: "A", text: "그대로 믿고 넘어간다", direction: "적극" },
      { key: "B", text: "믿되 한 번 더 찾아본다", direction: "절충" },
      { key: "C", text: "믿지 않고 직접 검색해본다", direction: "회피" },
      { key: "D", text: "다른 사람들 반응부터 살핀다", direction: "정보수집" },
    ],
  },
  // --- 즉흥성 대 계획성 ---
  {
    axis: "spontaneity_planning",
    situation: "갑자기 다음 주에 휴가가 하루 생겼다.",
    options: [
      { key: "A", text: "바로 떠날 곳을 정해 움직인다", direction: "적극" },
      { key: "B", text: "가까운 곳 위주로 계획을 짠다", direction: "절충" },
      { key: "C", text: "정한 게 없으면 그냥 집에서 쉰다", direction: "회피" },
      { key: "D", text: "같이 갈 사람부터 찾아본다", direction: "정보수집" },
    ],
  },
  {
    axis: "spontaneity_planning",
    situation: "새로운 업무 방식을 도입하자는 제안이 갑자기 나왔다.",
    options: [
      { key: "A", text: "일단 바로 시도해본다", direction: "적극" },
      { key: "B", text: "작게 시범 적용부터 해본다", direction: "절충" },
      { key: "C", text: "충분히 검토한 뒤 결정한다", direction: "회피" },
      { key: "D", text: "다른 팀 사례부터 찾아본다", direction: "정보수집" },
    ],
  },
  {
    axis: "spontaneity_planning",
    situation: "평소 갖고 싶던 물건을 마침 큰 폭으로 할인하는 걸 봤다.",
    options: [
      { key: "A", text: "바로 구매한다", direction: "적극" },
      { key: "B", text: "하루 정도 고민하고 산다", direction: "절충" },
      { key: "C", text: "정말 필요한지부터 따져본다", direction: "회피" },
      { key: "D", text: "다른 사람에게 물어보고 결정한다", direction: "정보수집" },
    ],
  },
  // --- 갈등 대응 방식 ---
  {
    axis: "conflict_response",
    situation: "회의에서 내 의견에 누군가 강하게 반박한다.",
    options: [
      { key: "A", text: "곧바로 맞서 논리로 반박한다", direction: "적극" },
      { key: "B", text: "침착하게 근거를 들어 설명한다", direction: "절충" },
      { key: "C", text: "일단 물러서고 나중에 다시 얘기한다", direction: "회피" },
      { key: "D", text: "다른 사람들 의견부터 들어본다", direction: "정보수집" },
    ],
  },
  {
    axis: "conflict_response",
    situation: "친한 친구와 오해로 다투게 됐다.",
    options: [
      { key: "A", text: "바로 전화해서 끝장을 본다", direction: "적극" },
      { key: "B", text: "시간을 두고 차분히 대화를 청한다", direction: "절충" },
      { key: "C", text: "먼저 연락하지 않고 기다린다", direction: "회피" },
      { key: "D", text: "다른 친구에게 먼저 상황을 얘기한다", direction: "정보수집" },
    ],
  },
  {
    axis: "conflict_response",
    situation: "가족과 중요한 문제로 의견이 크게 갈린다.",
    options: [
      { key: "A", text: "내 뜻을 강하게 주장한다", direction: "적극" },
      { key: "B", text: "절충안을 먼저 제안한다", direction: "절충" },
      { key: "C", text: "갈등을 피해 대화를 미룬다", direction: "회피" },
      { key: "D", text: "다른 가족에게 먼저 의견을 구한다", direction: "정보수집" },
    ],
  },
];

/**
 * answers: BEHAVIOR_QUESTIONS와 같은 순서ㆍ같은 길이의 "A"/"B"/"C"/"D" 배열.
 * 반환값: 축별 패턴(축마다 우세 방향 + 강도 + 원본 집계) — LLM은 이 결과만 문장으로 옮긴다.
 */
function computeBehaviorProfile(answers) {
  if (!Array.isArray(answers) || answers.length !== BEHAVIOR_QUESTIONS.length) {
    throw new Error(
      `행동DNA 답변은 정확히 ${BEHAVIOR_QUESTIONS.length}개여야 합니다(받은 개수: ${answers ? answers.length : 0}).`
    );
  }

  const axisResults = AXES.map((axis) => {
    const indices = BEHAVIOR_QUESTIONS
      .map((q, i) => (q.axis === axis.key ? i : -1))
      .filter((i) => i >= 0);

    const directions = indices.map((i) => {
      const q = BEHAVIOR_QUESTIONS[i];
      const chosen = answers[i];
      const opt = q.options.find((o) => o.key === chosen);
      if (!opt) {
        throw new Error(`문항 ${i + 1}번 답변("${chosen}")이 올바르지 않습니다 — A/B/C/D 중 하나여야 합니다.`);
      }
      return opt.direction;
    });

    const directional = directions.filter((d) => d !== "정보수집");
    const infoSeekingCount = directions.length - directional.length;
    const counts = { 적극: 0, 절충: 0, 회피: 0 };
    directional.forEach((d) => { counts[d] += 1; });

    const maxCount = Math.max(0, ...Object.values(counts));
    const topDirections = Object.keys(counts).filter((k) => counts[k] === maxCount && maxCount > 0);

    let pattern, strength;
    if (directional.length === 0) {
      pattern = "판단보류형";
      strength = "정보수집 위주 — 방향성 신호 부족";
    } else if (topDirections.length === 1 && maxCount >= 2) {
      pattern = topDirections[0];
      strength = maxCount === directional.length ? "일관됨" : "우세";
    } else {
      pattern = "상황에 따라 유동적";
      strength = "혼합 — 도메인에 따라 다르게 판단";
    }

    return {
      axis: axis.key,
      axisLabel: axis.label,
      pattern,
      strength,
      counts,
      infoSeekingCount,
      crossRef: axis.crossRef,
    };
  });

  return { axes: axisResults };
}

module.exports = { AXES, BEHAVIOR_QUESTIONS, computeBehaviorProfile };
