/**
 * CS 자주문의 · 리뷰 답글 자동매칭 시트 — Apps Script
 *
 * 설치 방법:
 * 1. 구글시트를 새로 만들고 "설정", "FAQ규칙", "리뷰답글규칙", "처리이력" 4개 시트를 만든다
 *    (정확한 칸 구조는 같은 폴더의 템플릿_구조.md 참고)
 * 2. 상단 메뉴 [확장 프로그램 > Apps Script]를 클릭
 * 3. 열린 편집기에 이 파일 내용을 전부 붙여넣고 저장 (Ctrl+S)
 * 4. 구글시트로 돌아오면 "CS·리뷰 자동응답"이라는 메뉴가 새로 생긴다 (새로고침 필요할 수 있음)
 */

const SHEET_SETTINGS = "설정";
const SHEET_FAQ = "FAQ규칙";
const SHEET_REVIEW = "리뷰답글규칙";
const SHEET_LOG = "처리이력";

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu("CS·리뷰 자동응답")
    .addItem("① FAQ 답변 찾기", "findFaqAnswer")
    .addItem("② 리뷰 답글 만들기", "generateReviewReply")
    .addSeparator()
    .addItem("③ 오늘 처리이력 PDF로 저장", "saveLogAsPdf")
    .addItem("④ 오늘 처리이력 이메일로 보내기", "emailTodayLog")
    .addToUi();
}

function getSettings_() {
  const sheet = SpreadsheetApp.getActive().getSheetByName(SHEET_SETTINGS);
  if (!sheet) throw new Error(`"${SHEET_SETTINGS}" 시트를 찾을 수 없습니다.`);
  const lastRow = sheet.getLastRow();
  const data = sheet.getRange(1, 1, lastRow, 2).getValues();
  const map = {};
  data.forEach((row) => {
    if (row[0]) map[row[0]] = row[1];
  });
  return map;
}

function getFaqRules_() {
  const sheet = SpreadsheetApp.getActive().getSheetByName(SHEET_FAQ);
  if (!sheet) throw new Error(`"${SHEET_FAQ}" 시트를 찾을 수 없습니다.`);
  const lastRow = sheet.getLastRow();
  if (lastRow < 2) return [];
  const values = sheet.getRange(2, 1, lastRow - 1, 3).getValues();
  return values
    .filter((row) => row[0])
    .map((row) => ({
      keywords: String(row[0]).split(",").map((k) => k.trim()).filter(Boolean),
      type: row[1],
      template: row[2],
    }));
}

function getReviewRules_() {
  const sheet = SpreadsheetApp.getActive().getSheetByName(SHEET_REVIEW);
  if (!sheet) throw new Error(`"${SHEET_REVIEW}" 시트를 찾을 수 없습니다.`);
  const lastRow = sheet.getLastRow();
  if (lastRow < 2) return [];
  const values = sheet.getRange(2, 1, lastRow - 1, 3).getValues();
  return values
    .filter((row) => row[0])
    .map((row) => ({
      rating: Number(row[0]),
      keywords: String(row[1] || "").split(",").map((k) => k.trim()).filter(Boolean),
      template: row[2],
    }));
}

function fillTemplate_(template, vars) {
  let result = template || "";
  Object.keys(vars).forEach((key) => {
    result = result.split(`{${key}}`).join(vars[key] || "");
  });
  return result;
}

function logEntry_(type, input, matchedType, output) {
  const sheet = SpreadsheetApp.getActive().getSheetByName(SHEET_LOG);
  if (!sheet) return;
  sheet.appendRow([new Date(), type, input, matchedType, output]);
}

/**
 * 문의 내용을 입력받아 FAQ규칙과 매칭한다. 키워드가 가장 많이 일치하는 규칙을 우선한다.
 */
function findFaqAnswer() {
  const ui = SpreadsheetApp.getUi();
  const inputResult = ui.prompt("고객 문의 내용을 붙여넣거나 입력하세요:", ui.ButtonSet.OK_CANCEL);
  if (inputResult.getSelectedButton() !== ui.Button.OK) return;
  const inquiry = inputResult.getResponseText().trim();
  if (!inquiry) return;

  const customerResult = ui.prompt("고객명(선택, 비워도 됨):", ui.ButtonSet.OK_CANCEL);
  const customerName = customerResult.getSelectedButton() === ui.Button.OK ? customerResult.getResponseText().trim() : "";

  const productResult = ui.prompt("상품명(선택, 비워도 됨):", ui.ButtonSet.OK_CANCEL);
  const productName = productResult.getSelectedButton() === ui.Button.OK ? productResult.getResponseText().trim() : "";

  const rules = getFaqRules_();
  let best = null;
  let bestScore = 0;
  rules.forEach((rule) => {
    const score = rule.keywords.filter((k) => inquiry.indexOf(k) !== -1).length;
    if (score > bestScore) {
      bestScore = score;
      best = rule;
    }
  });

  const settings = getSettings_();
  if (!best) {
    ui.alert("일치하는 답변이 없습니다. 직접 답변해주신 뒤, FAQ규칙 시트에 이 유형을 새로 추가해두면 다음부터 자동으로 나옵니다.");
    logEntry_("FAQ", inquiry, "매칭없음", "");
    return;
  }

  let answer = fillTemplate_(best.template, { 고객명: customerName, 상품명: productName });
  if (settings["서명"]) answer += "\n\n" + settings["서명"];

  ui.alert(`[${best.type}] 답변 초안\n\n${answer}\n\n(이 창을 닫고 위 내용을 복사해서 사용하세요)`);
  logEntry_("FAQ", inquiry, best.type, answer);
}

/**
 * 별점과 키워드를 입력받아 리뷰답글규칙과 매칭한다.
 * 같은 별점 안에서 키워드가 일치하는 규칙을 우선하고, 없으면 키워드 없는 기본 규칙을 쓴다.
 */
function generateReviewReply() {
  const ui = SpreadsheetApp.getUi();
  const ratingResult = ui.prompt("리뷰 별점(1~5)을 입력하세요:", ui.ButtonSet.OK_CANCEL);
  if (ratingResult.getSelectedButton() !== ui.Button.OK) return;
  const rating = Number(ratingResult.getResponseText().trim());
  if (!rating || rating < 1 || rating > 5) {
    ui.alert("1~5 사이 숫자를 입력해주세요.");
    return;
  }

  const reviewTextResult = ui.prompt("리뷰 내용(선택, 키워드 매칭용으로 붙여넣으세요):", ui.ButtonSet.OK_CANCEL);
  const reviewText = reviewTextResult.getSelectedButton() === ui.Button.OK ? reviewTextResult.getResponseText().trim() : "";

  const customerResult = ui.prompt("고객명(선택, 비워도 됨):", ui.ButtonSet.OK_CANCEL);
  const customerName = customerResult.getSelectedButton() === ui.Button.OK ? customerResult.getResponseText().trim() : "";

  const productResult = ui.prompt("상품명(선택, 비워도 됨):", ui.ButtonSet.OK_CANCEL);
  const productName = productResult.getSelectedButton() === ui.Button.OK ? productResult.getResponseText().trim() : "";

  const rules = getReviewRules_().filter((r) => r.rating === rating);
  let matched = rules.find((r) => r.keywords.length > 0 && r.keywords.some((k) => reviewText.indexOf(k) !== -1));
  if (!matched) matched = rules.find((r) => r.keywords.length === 0);

  const settings = getSettings_();
  if (!matched) {
    ui.alert(`별점 ${rating}점에 등록된 답글 규칙이 없습니다. 리뷰답글규칙 시트에 추가해주세요.`);
    logEntry_("리뷰", `${rating}점: ${reviewText}`, "매칭없음", "");
    return;
  }

  let reply = fillTemplate_(matched.template, { 고객명: customerName, 상품명: productName });
  if (settings["서명"]) reply += "\n\n" + settings["서명"];

  ui.alert(`별점 ${rating}점 답글 초안\n\n${reply}\n\n(이 창을 닫고 위 내용을 복사해서 사용하세요)`);
  logEntry_("리뷰", `${rating}점: ${reviewText}`, `${rating}점 규칙`, reply);
}

function exportSheetAsPdfBlob_(ss, sheet) {
  const url =
    `https://docs.google.com/spreadsheets/d/${ss.getId()}/export` +
    `?format=pdf&gid=${sheet.getSheetId()}&size=A4&portrait=true&fitw=true&gridlines=false`;
  const token = ScriptApp.getOAuthToken();
  const response = UrlFetchApp.fetch(url, { headers: { Authorization: "Bearer " + token } });
  return response.getBlob();
}

function saveLogAsPdf() {
  const ss = SpreadsheetApp.getActive();
  const logSheet = ss.getSheetByName(SHEET_LOG);
  if (!logSheet) throw new Error(`"${SHEET_LOG}" 시트를 찾을 수 없습니다.`);

  const blob = exportSheetAsPdfBlob_(ss, logSheet);
  const folderName = "CS처리이력_PDF";
  const folders = DriveApp.getFoldersByName(folderName);
  const folder = folders.hasNext() ? folders.next() : DriveApp.createFolder(folderName);

  const fileName = `CS처리이력_${Utilities.formatDate(new Date(), "GMT+9", "yyyyMMdd")}.pdf`;
  folder.createFile(blob.setName(fileName));

  SpreadsheetApp.getUi().alert(`"${folderName}" 폴더에 저장했습니다: ${fileName}`);
}

function emailTodayLog() {
  const ss = SpreadsheetApp.getActive();
  const logSheet = ss.getSheetByName(SHEET_LOG);
  const settings = getSettings_();
  const to = settings["로그받을이메일"];
  if (!to) {
    SpreadsheetApp.getUi().alert('"설정" 시트의 로그받을이메일 칸이 비어있어 발송하지 못했습니다.');
    return;
  }

  const lastRow = logSheet.getLastRow();
  const today = new Date();
  const todayStr = Utilities.formatDate(today, "GMT+9", "yyyy-MM-dd");
  let count = 0;
  if (lastRow >= 1) {
    const values = logSheet.getRange(1, 1, lastRow, 1).getValues();
    values.forEach((row) => {
      if (row[0] instanceof Date && Utilities.formatDate(row[0], "GMT+9", "yyyy-MM-dd") === todayStr) count++;
    });
  }

  const blob = exportSheetAsPdfBlob_(ss, logSheet);
  GmailApp.sendEmail(to, `[CS처리이력] ${settings["사업체명"] || ""} ${todayStr} (총 ${count}건)`, "오늘 처리한 CS·리뷰 응대 이력을 첨부해 드립니다.", {
    attachments: [blob.setName("CS처리이력.pdf")],
    name: settings["사업체명"] || "",
  });

  SpreadsheetApp.getUi().alert(`${to} 로 발송했습니다.`);
}
