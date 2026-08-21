/*
 * 상품 코드별 후처리 라우팅. 웹훅에서 결제 금액 검증까지 끝난 뒤 이 함수가 호출된다.
 *
 * 아키텍처 메모(중요, 다음 세션이 헷갈리지 않도록 기록):
 * - 이 파일은 Vercel Node.js 서버리스 함수 안에서 실행된다. Node 런타임에서는 로컬 Python을
 *   그냥 spawn할 수 없다(Vercel Node 함수엔 Python 인터프리터가 없음) — 그래서 크로스노틱스의
 *   "계산(Node) → LLM합성+PDF(Python)" 2단계 파이프라인 중 Node 부분은 여기서 바로 돌리고,
 *   Python 부분은 같은 Vercel 프로젝트 안의 별도 Python 런타임 함수(`api/generate-report.py`,
 *   Vercel이 파일 확장자로 런타임을 자동 인식함)를 내부 HTTP 호출로 실행한다.
 * - `api/generate-report.py`는 아직 없음 — 계획서 3ㆍ4단계(LLM 프롬프트 연동, report_kit.py)가
 *   끝나야 만들 수 있음. 지금은 그 지점까지 명확하게 연결해두고 TODO로 표시한다.
 */
const path = require("path");
const { execFile } = require("child_process");
const { promisify } = require("util");
const execFileAsync = promisify(execFile);

const { sendDeliveryEmail } = require("./deliver-email");

const ENGINE_DIR = path.resolve(__dirname, "../../tools/crossnotics-engine");

async function fulfillEbookOrService(product, order) {
  // TODO(계획서 9번 미해결 항목): 기존 전자책ㆍ서비스 파일을 Vercel 함수에서 접근 가능한 곳에
  // 호스팅하는 방식(예: GitHub Pages 공개 경로로 옮기기, 또는 별도 스토리지)이 아직 결정 안 됨 —
  // 현재 파일들은 사용자 로컬 PC(products/, 전자책 자동화/ 폴더)에만 있어 서버리스 함수가 못 읽음.
  // 사용자에게 "기존 상품도 지금 이 시스템으로 옮길지" 확인 후 파일 소스를 정하고 구현할 것.
  throw new Error(
    `NOT_IMPLEMENTED: ${product.name} 자동발송은 아직 미구현 — 기존 상품 파일 호스팅 방식을 ` +
    `먼저 정해야 함(계획서 9번 "남은 판단 사항" 참고). 지금은 계좌이체+수동발송 방식을 계속 쓸 것.`
  );
}

async function fulfillCrossnotics(product, order) {
  // 1) Node 계산 엔진 실행 — 이건 지금 당장 실행 가능(1단계 완료됨)
  const intake = {
    tier: product.tier,
    systems_included: product.systems,
    customer: order.customer, // 결제 시 입력폼에서 받은 생년월일시 등 (webhook.js에서 채움)
  };
  // Vercel 함수는 파일시스템이 읽기전용이지만 os.tmpdir()(=/tmp)만은 쓰기 가능함.
  // os.tmpdir()을 쓰는 이유: 하드코딩된 "/tmp"는 로컬 Windows 개발환경에서 안 맞고(실제로
  // 이 세션에서 ENOENT로 확인됨), os.tmpdir()은 Windows/Vercel(Linux) 둘 다에서 알아서
  // 올바른 임시폴더로 해석돼 로컬 테스트와 배포 환경 코드가 같아짐.
  const os = require("os");
  const fs = require("fs");
  const tmpIntake = path.join(os.tmpdir(), `intake-${order.paymentId}.json`);
  const tmpComputed = path.join(os.tmpdir(), `computed-${order.paymentId}.json`);
  fs.writeFileSync(tmpIntake, JSON.stringify(intake));
  await execFileAsync("node", [path.join(ENGINE_DIR, "run.js"), tmpIntake, tmpComputed]);
  const computed = JSON.parse(fs.readFileSync(tmpComputed, "utf8"));

  // 2) Python 리포트 생성(LLM 합성 + PDF)
  // tools/crossnotics-report/build_report.py(LLM 합성)ㆍreport_kit.py(PDF)는 완성ㆍ검증됨
  // (목업 데이터로 실제 PDF 생성 확인 완료). 다만 이 route-product.js는 Vercel Node 함수 안에서
  // 돌아서 Python을 직접 spawn할 수 없다 — 같은 Vercel 프로젝트의 Python 런타임 함수
  // (`api/generate-report.py`)로 HTTP 위임해야 하는데 그 브리지 파일이 아직 없다.
  // TODO: api/generate-report.py 작성 후 아래 fetch 활성화. 그 함수 안에서는
  // build_report.py의 call_llm()과 report_kit.py의 build_pdf()를 그대로 import해서 쓰면 됨
  // (ANTHROPIC_API_KEY 없이는 실제 호출 테스트 불가 — 계획서 8번, 사용자 액션 대기 중).
  // const reportRes = await fetch(`${process.env.SITE_CHECKOUT_BASE_URL}/api/generate-report`, {
  //   method: "POST", body: JSON.stringify(computed), headers: { "Content-Type": "application/json" },
  // });
  // const { pdfBase64, filename } = await reportRes.json();
  throw new Error(
    "NOT_IMPLEMENTED: computed.json까지는 정상 생성됨(아래 로그 참고). LLM 합성ㆍPDF 코드 " +
    "자체는 완성됐지만(tools/crossnotics-report/) 이 Node 함수에서 Python을 직접 실행 못해 " +
    "api/generate-report.py 브리지가 아직 필요함.\n" +
    `computed.json 요약: dominant_axis=${computed.correlation.dominant_axis}, ` +
    `agreement_score=${computed.correlation.agreement_score}`
  );
}

/**
 * @param {object} product - catalog.js의 상품 정보
 * @param {object} order - {paymentId, customer, email}
 */
async function routeProduct(product, type, order) {
  if (type === "crossnotics") return fulfillCrossnotics(product, order);
  return fulfillEbookOrService(product, order);
}

module.exports = { routeProduct };
