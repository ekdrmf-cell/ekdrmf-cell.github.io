/**
 * 학원 수강료 자동계산 + 수납관리 시트 — Apps Script
 *
 * 설치 방법:
 * 1. 구글시트를 새로 만들고 "설정", "수강생정보", "수납기록", "수납현황" 4개 시트를 만든다
 *    (정확한 칸 구조는 같은 폴더의 템플릿_구조.md 참고)
 * 2. 상단 메뉴 [확장 프로그램 > Apps Script]를 클릭
 * 3. 열린 편집기에 이 파일 내용을 전부 붙여넣고 저장 (Ctrl+S)
 * 4. 구글시트로 돌아오면 "수강료 자동관리"라는 메뉴가 새로 생긴다 (새로고침 필요할 수 있음)
 */

const SHEET_SETTINGS = "설정";
const SHEET_STUDENTS = "수강생정보";
const SHEET_PAYMENTS = "수납기록";
const SHEET_STATUS = "수납현황";

const COLOR_UNPAID = "#f4cccc"; // 빨강 — 미납
const COLOR_PAID = "#ffffff"; // 흰색 — 완납

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu("수강료 자동관리")
    .addItem("① 이번달 수납현황 새로고침", "generateTuitionStatus")
    .addItem("② 수납현황 PDF로 저장", "saveStatusAsPdf")
    .addSeparator()
    .addItem("③ 원장님에게 미납자 요약 이메일 발송", "emailAdminSummary")
    .addItem("④ 미납 수강생 학부모에게 개별 납부안내 발송", "emailUnpaidGuardians")
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

function getStudents_() {
  const sheet = SpreadsheetApp.getActive().getSheetByName(SHEET_STUDENTS);
  if (!sheet) throw new Error(`"${SHEET_STUDENTS}" 시트를 찾을 수 없습니다.`);
  const lastRow = sheet.getLastRow();
  if (lastRow < 2) return [];
  // 2행부터, 컬럼: 성명 | 연락처 | 과목/반 | 월수강료 | 학부모이메일 | 등록일
  const values = sheet.getRange(2, 1, lastRow - 1, 6).getValues();
  return values
    .filter((row) => row[0])
    .map((row) => ({
      name: row[0],
      phone: row[1],
      className: row[2],
      tuition: Number(row[3]) || 0,
      parentEmail: row[4],
      joinDate: row[5],
    }));
}

function getPayments_() {
  const sheet = SpreadsheetApp.getActive().getSheetByName(SHEET_PAYMENTS);
  if (!sheet) throw new Error(`"${SHEET_PAYMENTS}" 시트를 찾을 수 없습니다.`);
  const lastRow = sheet.getLastRow();
  if (lastRow < 2) return [];
  // 2행부터, 컬럼: 납부일 | 수강생명 | 납부액 | 메모
  const values = sheet.getRange(2, 1, lastRow - 1, 4).getValues();
  return values
    .filter((row) => row[1])
    .map((row) => ({
      date: row[0],
      name: row[1],
      amount: Number(row[2]) || 0,
      note: row[3],
    }));
}

function isSameMonth_(date, ref) {
  if (!(date instanceof Date)) return false;
  return date.getFullYear() === ref.getFullYear() && date.getMonth() === ref.getMonth();
}

/**
 * 오늘이 속한 달의 수납기록만 모아서 수강생별 이번달 납부액과 완납/미납 여부를 계산한다.
 */
function calcTuitionStatus_() {
  const students = getStudents_();
  const payments = getPayments_();
  const today = new Date();

  return students.map((s) => {
    const paidThisMonth = payments
      .filter((p) => p.name === s.name && isSameMonth_(p.date, today))
      .reduce((sum, p) => sum + p.amount, 0);
    const shortfall = Math.max(s.tuition - paidThisMonth, 0);
    return Object.assign({}, s, {
      paidThisMonth,
      shortfall,
      isPaid: shortfall === 0,
    });
  });
}

/**
 * "수납현황" 시트를 다시 그린다.
 */
function generateTuitionStatus() {
  const ss = SpreadsheetApp.getActive();
  const statusSheet = ss.getSheetByName(SHEET_STATUS);
  if (!statusSheet) throw new Error(`"${SHEET_STATUS}" 시트를 찾을 수 없습니다.`);

  const settings = getSettings_();
  const list = calcTuitionStatus_();
  const monthLabel = Utilities.formatDate(new Date(), "GMT+9", "yyyy년 M월");

  statusSheet.clear();
  statusSheet.getRange("A1").setValue("수 납 현 황").setFontSize(18).setFontWeight("bold");
  statusSheet.getRange("A2").setValue(`${settings["학원명"] || ""} · 기준월: ${monthLabel}`);

  const headerRow = 4;
  const headers = ["성명", "과목/반", "월수강료", "이번달납부액", "미납액", "상태"];
  statusSheet.getRange(headerRow, 1, 1, headers.length).setValues([headers]).setFontWeight("bold");

  let row = headerRow + 1;
  list.forEach((s) => {
    const status = s.isPaid ? "완납" : "미납";
    statusSheet.getRange(row, 1, 1, 6).setValues([[s.name, s.className, s.tuition, s.paidThisMonth, s.shortfall, status]]);
    statusSheet.getRange(row, 1, 1, 6).setBackground(s.isPaid ? COLOR_PAID : COLOR_UNPAID);
    row++;
  });

  const unpaidCount = list.filter((s) => !s.isPaid).length;
  row++;
  statusSheet.getRange(row, 1).setValue(`미납 ${unpaidCount}명 / 전체 ${list.length}명`).setFontWeight("bold");

  statusSheet.autoResizeColumns(1, 6);
  SpreadsheetApp.getUi().alert(`${monthLabel} 수납현황을 새로고침했습니다. 미납 ${unpaidCount}명.`);
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
  const folderName = "수납현황_PDF";
  const folders = DriveApp.getFoldersByName(folderName);
  const folder = folders.hasNext() ? folders.next() : DriveApp.createFolder(folderName);

  const fileName = `수납현황_${Utilities.formatDate(new Date(), "GMT+9", "yyyyMM")}.pdf`;
  folder.createFile(blob.setName(fileName));

  SpreadsheetApp.getUi().alert(`"${folderName}" 폴더에 저장했습니다: ${fileName}`);
}

/**
 * 원장님(설정 시트의 알림받을이메일)에게 이번달 미납자 요약을 보낸다.
 * 매달 자동으로 실행하고 싶다면 템플릿_구조.md의 트리거 설정 방법을 참고해
 * 이 함수(emailAdminSummary)를 등록하면 된다.
 */
function emailAdminSummary() {
  const ss = SpreadsheetApp.getActive();
  const statusSheet = ss.getSheetByName(SHEET_STATUS);
  const settings = getSettings_();
  const to = settings["알림받을이메일"];

  generateTuitionStatus();
  const list = calcTuitionStatus_();
  const unpaid = list.filter((s) => !s.isPaid);
  const monthLabel = Utilities.formatDate(new Date(), "GMT+9", "yyyy년 M월");

  if (unpaid.length === 0) {
    SpreadsheetApp.getUi().alert(`${monthLabel} 미납자가 없어 이메일을 보내지 않았습니다.`);
    return;
  }
  if (!to) {
    SpreadsheetApp.getUi().alert('"설정" 시트의 알림받을이메일 칸이 비어있어 발송하지 못했습니다.');
    return;
  }

  const lines = unpaid.map((s) => `- ${s.name} (${s.className}): 미납액 ${s.shortfall.toLocaleString()}원, 연락처 ${s.phone || ""}`);
  const body = `${monthLabel} 미납 수강생이 ${unpaid.length}명 있습니다.\n\n` + lines.join("\n");
  const blob = exportSheetAsPdfBlob_(ss, statusSheet);

  GmailApp.sendEmail(to, `[수강료 미납알림] ${settings["학원명"] || ""} ${monthLabel} 미납 ${unpaid.length}명`, body, {
    attachments: [blob.setName("수납현황.pdf")],
    name: settings["학원명"] || "",
  });

  SpreadsheetApp.getUi().alert(`${to} 로 미납 요약 알림을 보냈습니다 (${unpaid.length}명).`);
}

/**
 * 이번달 미납 상태인 수강생의 학부모에게 각자 납부 안내 이메일을 보낸다.
 * 이메일이 비어있는 수강생은 건너뛴다.
 */
function emailUnpaidGuardians() {
  const ui = SpreadsheetApp.getUi();
  const confirm = ui.alert(
    "학부모 개별 발송",
    "이번달 미납 상태인 수강생 중 학부모 이메일이 등록된 분들께 납부 안내 메일을 보냅니다. 계속할까요?",
    ui.ButtonSet.YES_NO
  );
  if (confirm !== ui.Button.YES) return;

  const settings = getSettings_();
  const list = calcTuitionStatus_();
  const targets = list.filter((s) => !s.isPaid && s.parentEmail);
  const monthLabel = Utilities.formatDate(new Date(), "GMT+9", "yyyy년 M월");

  let sent = 0;
  targets.forEach((s) => {
    const message = `${s.name} 학생 학부모님께,\n\n${monthLabel} "${s.className}" 수강료 중 ${s.shortfall.toLocaleString()}원이 아직 납부되지 않았습니다. 확인 부탁드립니다.\n\n${settings["학원명"] || ""} 드림`;
    GmailApp.sendEmail(s.parentEmail, `[${settings["학원명"] || ""}] ${monthLabel} 수강료 납부 안내`, message, {
      name: settings["학원명"] || "",
    });
    sent++;
  });

  ui.alert(`${sent}명의 학부모에게 납부 안내 메일을 보냈습니다.`);
}
