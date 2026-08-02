/**
 * 수익화허브 구매 문의 자동 답장 초안 생성기
 *
 * 하는 일: Gmail(ekdrmf@gmail.com)에 "OO 구매 문의" 제목 메일이 오면,
 * 해당 상품 파일을 구글드라이브 폴더에서 찾아 첨부한 "답장 초안"을
 * Gmail 임시보관함에 만들어 둡니다.
 *
 * 하지 않는 일(중요): 이메일을 자동으로 "발송"하지는 않습니다.
 * 실제로 입금이 됐는지는 케이뱅크 앱으로 사람이 직접 확인해야 하므로,
 * 초안까지만 만들어두고 발송 버튼은 사람이 직접 누릅니다.
 *
 * 설치 방법은 파일 맨 아래 주석 참고.
 */

// ── 설정: 이 두 줄만 확인하면 됩니다 ─────────────────────────
const DRIVE_FOLDER_NAME = "수익화허브_전자책"; // 구글드라이브에 만들 폴더 이름
const PROCESSED_LABEL = "자동답장-처리완료";     // 처리 완료 표시용 라벨(자동 생성됨)
// ────────────────────────────────────────────────────────

// 메일 제목에 이 키워드가 들어있으면 → 이 파일을 첨부합니다.
// 폴더에 올릴 파일 이름은 반드시 아래와 정확히 같아야 합니다.
const PRODUCT_MAP = [
  { keyword: "정부지원금", file: "정부지원금_찾기_가이드.pdf" },
  { keyword: "전자책 만들어", file: "전자책_만들어_팔기_가이드.pdf" },
  { keyword: "애드센스", file: "애드센스_블로그_시작_가이드.pdf" },
  { keyword: "인스타그램", file: "인스타그램_마케팅_핵심노하우.pdf" },
  { keyword: "건축기사", file: "건축기사_실기_합격전략_가이드.pdf" },
  { keyword: "유튜브", file: "유튜브_채널_수익화_전략_가이드.pdf" },
  { keyword: "제휴마케팅", file: "제휴마케팅_실전_가이드.pdf" },
  { keyword: "견적서", file: "quote-generator.zip" },
];

function checkPurchaseInquiries() {
  const label = getOrCreateLabel_(PROCESSED_LABEL);
  const folder = getProductFolder_(DRIVE_FOLDER_NAME);

  const threads = GmailApp.search(`in:inbox subject:"구매 문의" -label:${PROCESSED_LABEL}`);
  Logger.log(`검사 대상 문의 ${threads.length}건`);

  threads.forEach((thread) => {
    const subject = thread.getFirstMessageSubject();
    const match = PRODUCT_MAP.find((p) => subject.includes(p.keyword));

    if (!match) {
      Logger.log(`상품을 못 찾음(수동 확인 필요): ${subject}`);
      return; // 라벨을 안 붙여서 다음 실행 때도 계속 검사되고 로그에 남음
    }

    const files = folder.getFilesByName(match.file);
    if (!files.hasNext()) {
      Logger.log(`드라이브 폴더에 파일이 없음: ${match.file} (폴더에 올려주세요)`);
      return;
    }
    const fileBlob = files.next().getBlob();

    const messages = thread.getMessages();
    const lastMessage = messages[messages.length - 1];
    lastMessage.createDraftReply(
      "안녕하세요, 수익화허브입니다.\n\n입금 확인 후 파일을 첨부해 보내드립니다.\n이용해주셔서 감사합니다.",
      { attachments: [fileBlob] }
    );

    thread.addLabel(label);
    Logger.log(`초안 생성 완료: ${subject} → ${match.file}`);
  });
}

// ── 아래는 건드릴 필요 없는 도우미 함수 ─────────────────────
function getOrCreateLabel_(name) {
  return GmailApp.getUserLabelByName(name) || GmailApp.createLabel(name);
}

function getProductFolder_(name) {
  const folders = DriveApp.getFoldersByName(name);
  if (!folders.hasNext()) {
    throw new Error(`구글드라이브에 "${name}" 폴더가 없습니다. 먼저 만들고 상품 파일 8개를 넣어주세요.`);
  }
  return folders.next();
}

/*
 * ───────────── 설치 방법 (한 번만 하면 됨) ─────────────────
 *
 * 1) 구글드라이브(drive.google.com)에서 새 폴더를 만들고 이름을
 *    "수익화허브_전자책"으로 지정합니다.
 *    그 안에 아래 8개 파일을 파일 이름 그대로 업로드합니다.
 *      - 정부지원금_찾기_가이드.pdf
 *      - 전자책_만들어_팔기_가이드.pdf
 *      - 애드센스_블로그_시작_가이드.pdf
 *      - 인스타그램_마케팅_핵심노하우.pdf
 *      - 건축기사_실기_합격전략_가이드.pdf
 *      - 유튜브_채널_수익화_전략_가이드.pdf
 *      - 제휴마케팅_실전_가이드.pdf
 *      - quote-generator.zip
 *
 * 2) script.google.com 접속 → "새 프로젝트" → 이 파일 내용 전체를
 *    복사해서 붙여넣습니다.
 *
 * 3) 상단 실행(▶) 버튼을 누릅니다(함수: checkPurchaseInquiries).
 *    처음 실행하면 "권한 검토" 화면이 뜨는데, ekdrmf@gmail.com 계정으로
 *    로그인 후 "고급" → "이동(안전하지 않음)" → 허용을 눌러줍니다.
 *    (본인이 만든 스크립트라 안전 경고가 뜨는 건 정상입니다.)
 *
 * 4) 왼쪽 메뉴의 시계 모양 아이콘("트리거") → 오른쪽 아래 "트리거 추가":
 *      - 실행할 함수: checkPurchaseInquiries
 *      - 이벤트 소스: 시간 기반
 *      - 시간 기반 트리거 유형: 분 타이머
 *      - 간격: 15분마다
 *    저장.
 *
 * 5) 이제부터 "OO 구매 문의" 메일이 오면 15분 안에 Gmail
 *    "임시보관함(Drafts)"에 파일이 첨부된 답장 초안이 자동으로
 *    만들어집니다. 케이뱅크 앱으로 입금을 확인한 뒤, 그 초안을
 *    열어서 발송 버튼만 누르면 됩니다.
 * ───────────────────────────────────────────────────────
 */
