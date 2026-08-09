/**
 * 회원권·정기결제 만료 자동알림 시트 — Apps Script
 *
 * 설치 방법:
 * 1. 구글시트를 새로 만들고 "설정", "회원정보", "회원현황" 3개 시트를 만든다
 *    (정확한 칸 구조는 같은 폴더의 템플릿_구조.md 참고)
 * 2. 상단 메뉴 [확장 프로그램 > Apps Script]를 클릭
 * 3. 열린 편집기에 이 파일 내용을 전부 붙여넣고 저장 (Ctrl+S)
 * 4. 구글시트로 돌아오면 "회원만료 자동알림"이라는 메뉴가 새로 생긴다 (새로고침 필요할 수 있음)
 */

const SHEET_SETTINGS = "설정";
const SHEET_MEMBERS = "회원정보";
const SHEET_STATUS = "회원현황";

const COLOR_EXPIRED = "#f4cccc"; // 빨강 — 만료
const COLOR_SOON = "#fff2cc"; // 노랑 — 임박
const COLOR_OK = "#ffffff"; // 흰색 — 정상

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu("회원만료 자동알림")
    .addItem("① 회원현황 새로고침", "generateMemberStatus")
    .addItem("② 회원현황 PDF로 저장", "saveStatusAsPdf")
    .addSeparator()
    .addItem("③ 관리자에게 요약 이메일 발송", "emailAdminSummary")
    .addItem("④ 임박/만료 회원에게 개별 갱신안내 발송", "emailMembersIndividually")
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

function getMembers_() {
  const sheet = SpreadsheetApp.getActive().getSheetByName(SHEET_MEMBERS);
  if (!sheet) throw new Error(`"${SHEET_MEMBERS}" 시트를 찾을 수 없습니다.`);
  const lastRow = sheet.getLastRow();
  if (lastRow < 2) return [];
  // 2행부터, 컬럼: 성명 | 연락처 | 회원권종류 | 시작일 | 종료일 | 이메일 | 비고
  const values = sheet.getRange(2, 1, lastRow - 1, 7).getValues();
  return values
    .filter((row) => row[0])
    .map((row) => ({
      name: row[0],
      phone: row[1],
      planType: row[2],
      startDate: row[3],
      endDate: row[4],
      email: row[5],
      note: row[6],
    }));
}

function daysUntil_(endDate) {
  if (!(endDate instanceof Date)) return null;
  const today = new Date();
  const todayMidnight = new Date(today.getFullYear(), today.getMonth(), today.getDate());
  const end = new Date(endDate.getFullYear(), endDate.getMonth(), endDate.getDate());
  const diffMs = end.getTime() - todayMidnight.getTime();
  return Math.round(diffMs / (1000 * 60 * 60 * 24));
}

/**
 * 회원 목록에 남은일수·상태(정상/임박/만료)를 계산해서 붙여준다.
 */
function calcMemberStatus_() {
  const settings = getSettings_();
  const soonThreshold = Number(settings["임박기준일수"]) || 7;
  const members = getMembers_();

  return members.map((m) => {
    const daysLeft = daysUntil_(m.endDate);
    let status = "정상";
    if (daysLeft === null) status = "종료일 확인필요";
    else if (daysLeft < 0) status = "만료";
    else if (daysLeft <= soonThreshold) status = "임박";
    return Object.assign({}, m, { daysLeft, status });
  });
}

function statusColor_(status) {
  if (status === "만료") return COLOR_EXPIRED;
  if (status === "임박") return COLOR_SOON;
  return COLOR_OK;
}

/**
 * "회원현황" 시트를 다시 그린다.
 */
function generateMemberStatus() {
  const ss = SpreadsheetApp.getActive();
  const statusSheet = ss.getSheetByName(SHEET_STATUS);
  if (!statusSheet) throw new Error(`"${SHEET_STATUS}" 시트를 찾을 수 없습니다.`);

  const settings = getSettings_();
  const list = calcMemberStatus_();

  statusSheet.clear();
  statusSheet.getRange("A1").setValue("회 원 현 황").setFontSize(18).setFontWeight("bold");
  statusSheet.getRange("A2").setValue(`${settings["회사명"] || ""} · 기준일: ${Utilities.formatDate(new Date(), "GMT+9", "yyyy-MM-dd")}`);

  const headerRow = 4;
  const headers = ["성명", "회원권종류", "종료일", "남은일수", "상태", "연락처"];
  statusSheet.getRange(headerRow, 1, 1, headers.length).setValues([headers]).setFontWeight("bold");

  let row = headerRow + 1;
  list.forEach((m) => {
    const endDateText = m.endDate instanceof Date ? Utilities.formatDate(m.endDate, "GMT+9", "yyyy-MM-dd") : String(m.endDate || "");
    statusSheet
      .getRange(row, 1, 1, 6)
      .setValues([[m.name, m.planType, endDateText, m.daysLeft === null ? "" : m.daysLeft, m.status, m.phone]]);
    statusSheet.getRange(row, 1, 1, 6).setBackground(statusColor_(m.status));
    row++;
  });

  const soonCount = list.filter((m) => m.status === "임박").length;
  const expiredCount = list.filter((m) => m.status === "만료").length;
  row++;
  statusSheet.getRange(row, 1).setValue(`임박 ${soonCount}명 · 만료 ${expiredCount}명 / 전체 ${list.length}명`).setFontWeight("bold");

  statusSheet.autoResizeColumns(1, 6);
  SpreadsheetApp.getUi().alert(`회원현황을 새로고침했습니다. 임박 ${soonCount}명, 만료 ${expiredCount}명.`);
}

function exportSheetAsPdfBlob_(ss, sheet) {
  const url =
    `https://docs.google.com/spreadsheets/d/${ss.getId()}/export` +
    `?format=pdf&gid=${sheet.getSheetId()}&size=A4&portrait=true&fitw=true&gridlines=false`;
  const token = ScriptApp.getOAuthToken();
  const response = UrlFetchApp.fetch(url, { headers: { Authorization: "Bearer " + token } });
  return response.getBlob();
}

function saveStatusAsPdf() {
  const ss = SpreadsheetApp.getActive();
  const statusSheet = ss.getSheetByName(SHEET_STATUS);
  if (!statusSheet) throw new Error(`"${SHEET_STATUS}" 시트를 찾을 수 없습니다.`);

  const blob = exportSheetAsPdfBlob_(ss, statusSheet);
  const folderName = "회원현황_PDF";
  const folders = DriveApp.getFoldersByName(folderName);
  const folder = folders.hasNext() ? folders.next() : DriveApp.createFolder(folderName);

  const fileName = `회원현황_${Utilities.formatDate(new Date(), "GMT+9", "yyyyMMdd_HHmm")}.pdf`;
  folder.createFile(blob.setName(fileName));

  SpreadsheetApp.getUi().alert(`"${folderName}" 폴더에 저장했습니다: ${fileName}`);
}

/**
 * 관리자(설정 시트의 알림받을이메일)에게 임박/만료 회원 요약을 보낸다.
 * 매일 자동으로 실행하고 싶다면 템플릿_구조.md의 트리거 설정 방법을 참고해
 * 이 함수(emailAdminSummary)를 등록하면 된다.
 */
function emailAdminSummary() {
  const ss = SpreadsheetApp.getActive();
  const statusSheet = ss.getSheetByName(SHEET_STATUS);
  const settings = getSettings_();
  const to = settings["알림받을이메일"];

  generateMemberStatus();
  const list = calcMemberStatus_();
  const targets = list.filter((m) => m.status === "임박" || m.status === "만료");

  if (targets.length === 0) {
    SpreadsheetApp.getUi().alert("현재 임박/만료 회원이 없어 이메일을 보내지 않았습니다.");
    return;
  }
  if (!to) {
    SpreadsheetApp.getUi().alert('"설정" 시트의 알림받을이메일 칸이 비어있어 발송하지 못했습니다.');
    return;
  }

  const lines = targets.map((m) => {
    const endDateText = m.endDate instanceof Date ? Utilities.formatDate(m.endDate, "GMT+9", "yyyy-MM-dd") : String(m.endDate || "");
    return `- ${m.name} (${m.planType}): ${m.status}, 종료일 ${endDateText}, 남은일수 ${m.daysLeft}일, 연락처 ${m.phone || ""}`;
  });
  const body = `임박/만료 회원이 ${targets.length}명 있습니다.\n\n` + lines.join("\n");
  const blob = exportSheetAsPdfBlob_(ss, statusSheet);

  GmailApp.sendEmail(to, `[회원만료알림] ${settings["회사명"] || ""} 임박/만료 회원 ${targets.length}명`, body, {
    attachments: [blob.setName("회원현황.pdf")],
    name: settings["회사명"] || "",
  });

  SpreadsheetApp.getUi().alert(`${to} 로 요약 알림을 보냈습니다 (${targets.length}명).`);
}

/**
 * 임박/만료 상태인 회원 본인에게 각자 갱신 안내 이메일을 보낸다.
 * 이메일이 비어있는 회원은 건너뛴다.
 */
function emailMembersIndividually() {
  const ui = SpreadsheetApp.getUi();
  const confirm = ui.alert(
    "회원 개별 발송",
    "임박/만료 상태인 회원 중 이메일이 등록된 분들께 갱신 안내 메일을 보냅니다. 계속할까요?",
    ui.ButtonSet.YES_NO
  );
  if (confirm !== ui.Button.YES) return;

  const settings = getSettings_();
  const list = calcMemberStatus_();
  const targets = list.filter((m) => (m.status === "임박" || m.status === "만료") && m.email);

  let sent = 0;
  targets.forEach((m) => {
    const endDateText = m.endDate instanceof Date ? Utilities.formatDate(m.endDate, "GMT+9", "yyyy-MM-dd") : String(m.endDate || "");
    const message =
      m.status === "만료"
        ? `${m.name}님, 이용 중이신 "${m.planType}"이 ${endDateText}자로 만료되었습니다. 계속 이용을 원하시면 갱신을 부탁드립니다.`
        : `${m.name}님, 이용 중이신 "${m.planType}"이 ${endDateText}에 만료될 예정입니다(${m.daysLeft}일 남음). 편하신 시간에 갱신 부탁드립니다.`;
    GmailApp.sendEmail(m.email, `[${settings["회사명"] || ""}] 회원권 갱신 안내`, message, {
      name: settings["회사명"] || "",
    });
    sent++;
  });

  ui.alert(`${sent}명에게 갱신 안내 메일을 보냈습니다.`);
}
