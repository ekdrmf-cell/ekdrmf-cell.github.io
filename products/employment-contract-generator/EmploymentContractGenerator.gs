/**
 * 근로계약서 자동생성기 (고용노동부 표준근로계약서 양식 기반 서식 자동채움) — Apps Script
 *
 * 이 스크립트는 법률 자문이 아니며, 표준 양식의 빈칸을 입력값으로 채워주는 도구입니다.
 * 특수 고용형태나 분쟁 소지가 있는 경우 노무사 등 전문가 검토를 받으시길 권합니다.
 *
 * 설치 방법:
 * 1. 구글시트를 새로 만들고 "설정", "근로자정보", "계약서생성", "계약서" 4개 시트를 만든다
 *    (정확한 칸 구조는 같은 폴더의 템플릿_구조.md 참고)
 * 2. 상단 메뉴 [확장 프로그램 > Apps Script]를 클릭
 * 3. 열린 편집기에 이 파일 내용을 전부 붙여넣고 저장 (Ctrl+S)
 * 4. 구글시트로 돌아오면 "근로계약서 자동생성"이라는 메뉴가 새로 생긴다 (새로고침 필요할 수 있음)
 */

const SHEET_SETTINGS = "설정";
const SHEET_STAFF = "근로자정보";
const SHEET_CONTROL = "계약서생성";
const SHEET_CONTRACT = "계약서";

const MIN_HOURLY_WAGE_2026 = 10320; // 2026년 최저시급(원). 매년 바뀌므로 새해에는 이 값을 갱신할 것.

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu("근로계약서 자동생성")
    .addItem("① 계약서 생성/새로고침", "generateContract")
    .addItem("② PDF로 저장 (내 드라이브)", "saveContractAsPdf")
    .addItem("③ 이메일로 보내기", "emailContract")
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

function getStaffList_() {
  const sheet = SpreadsheetApp.getActive().getSheetByName(SHEET_STAFF);
  if (!sheet) throw new Error(`"${SHEET_STAFF}" 시트를 찾을 수 없습니다.`);
  const lastRow = sheet.getLastRow();
  if (lastRow < 2) return [];
  // 2행부터, 컬럼 A~U (21개): 템플릿_구조.md 표 참고
  const values = sheet.getRange(2, 1, lastRow - 1, 21).getValues();
  return values
    .filter((row) => row[0])
    .map((row) => ({
      name: row[0],
      birthDate: row[1],
      address: row[2],
      phone: row[3],
      email: row[4],
      startDate: row[5],
      termType: row[6],
      endDate: row[7],
      workplace: row[8],
      duties: row[9],
      workDays: row[10],
      startTime: row[11],
      endTime: row[12],
      breakTime: row[13],
      weeklyHoliday: row[14],
      wageType: row[15],
      wageAmount: Number(row[16]) || 0,
      bonus: row[17],
      otherPay: row[18],
      payDate: row[19],
      payMethod: row[20],
    }));
}

function findStaff_(name) {
  const staff = getStaffList_();
  const found = staff.find((s) => s.name === name);
  if (!found) throw new Error(`근로자정보 시트에서 "${name}"을(를) 찾을 수 없습니다.`);
  return found;
}

function formatDate_(d) {
  if (d instanceof Date) return Utilities.formatDate(d, "GMT+9", "yyyy년 M월 d일");
  return String(d || "");
}

/**
 * "계약서생성" 시트에서 고른 근로자 기준으로 "계약서" 시트를 표준근로계약서 양식으로 채운다.
 */
function generateContract() {
  const ss = SpreadsheetApp.getActive();
  const contractSheet = ss.getSheetByName(SHEET_CONTRACT);
  if (!contractSheet) throw new Error(`"${SHEET_CONTRACT}" 시트를 찾을 수 없습니다.`);

  const controlSheet = ss.getSheetByName(SHEET_CONTROL);
  const staffName = controlSheet.getRange("B1").getValue();
  if (!staffName) {
    SpreadsheetApp.getUi().alert('"계약서생성" 시트 B1에서 근로자를 먼저 선택해주세요.');
    return;
  }

  const settings = getSettings_();
  const s = findStaff_(staffName);

  let warning = "";
  if (s.wageType === "시급" && s.wageAmount > 0 && s.wageAmount < MIN_HOURLY_WAGE_2026) {
    warning = `⚠ 경고: 입력된 시급(${s.wageAmount.toLocaleString()}원)이 2026년 최저시급(${MIN_HOURLY_WAGE_2026.toLocaleString()}원)보다 낮습니다. 계약서를 사용하기 전에 반드시 확인하세요.`;
  }

  contractSheet.clear();
  let row = 1;
  contractSheet.getRange(row, 1).setValue("표 준 근 로 계 약 서").setFontSize(18).setFontWeight("bold");
  row += 2;

  contractSheet
    .getRange(row, 1)
    .setValue(`${settings["사업체명"] || ""} (이하 "사업주"라 함)과(와) ${s.name} (이하 "근로자"라 함)은 다음과 같이 근로계약을 체결한다.`);
  row += 2;

  const termText =
    s.termType === "정함있음"
      ? `${formatDate_(s.startDate)}부터 ${formatDate_(s.endDate)}까지`
      : `${formatDate_(s.startDate)}부터 (근로계약기간을 정하지 않음)`;
  contractSheet.getRange(row, 1).setValue("1. 근로계약기간: " + termText).setFontWeight("bold");
  row++;
  contractSheet.getRange(row, 1).setValue("2. 근무장소: " + (s.workplace || ""));
  row++;
  contractSheet.getRange(row, 1).setValue("3. 업무의 내용: " + (s.duties || ""));
  row++;
  contractSheet
    .getRange(row, 1)
    .setValue(`4. 소정근로시간: ${s.startTime || ""}부터 ${s.endTime || ""}까지 (휴게시간: ${s.breakTime || ""})`);
  row++;
  contractSheet.getRange(row, 1).setValue(`5. 근무일/휴일: ${s.workDays || ""}, 주휴일 ${s.weeklyHoliday || ""}`);
  row += 2;

  contractSheet.getRange(row, 1).setValue("6. 임금").setFontWeight("bold");
  row++;
  contractSheet.getRange(row, 1).setValue(`   - ${s.wageType || ""}: ${s.wageAmount.toLocaleString()}원`);
  row++;
  contractSheet.getRange(row, 1).setValue(`   - 상여금: ${s.bonus || "없음"}`);
  row++;
  contractSheet.getRange(row, 1).setValue(`   - 기타급여(제수당 등): ${s.otherPay || "없음"}`);
  row++;
  contractSheet.getRange(row, 1).setValue(`   - 임금지급일: ${s.payDate || ""} (휴일인 경우 전일 지급)`);
  row++;
  contractSheet.getRange(row, 1).setValue(`   - 지급방법: ${s.payMethod || ""}`);
  row += 2;

  contractSheet.getRange(row, 1).setValue("7. 연차유급휴가: 근로기준법에서 정하는 바에 따라 부여함");
  row++;
  contractSheet.getRange(row, 1).setValue("8. 사회보험 적용여부: 고용보험, 산재보험, 국민연금, 건강보험 (법정 요건에 따라 적용)");
  row++;
  contractSheet
    .getRange(row, 1)
    .setValue('9. "사업주"는 근로계약을 체결함과 동시에 본 계약서를 사본하여 "근로자"의 교부요구와 관계없이 "근로자"에게 교부함(근로기준법 제17조)');
  row++;
  contractSheet.getRange(row, 1).setValue("10. 기타: 이 계약에 정함이 없는 사항은 근로기준법령에 의함");
  row += 2;

  contractSheet.getRange(row, 1).setValue(formatDate_(new Date()));
  row += 2;
  contractSheet.getRange(row, 1).setValue(`(사업주) ${settings["사업체명"] || ""}  대표자: ${settings["대표자"] || ""}  (서명)`);
  row++;
  contractSheet.getRange(row, 1).setValue(`   주소: ${settings["사업장주소"] || ""}`);
  row += 2;
  contractSheet.getRange(row, 1).setValue(`(근로자) 성명: ${s.name}  (서명)`);
  row++;
  contractSheet.getRange(row, 1).setValue(`   주소: ${s.address || ""}  연락처: ${s.phone || ""}`);
  row += 2;

  contractSheet
    .getRange(row, 1)
    .setValue("※ 본 계약서는 고용노동부 표준근로계약서 양식을 기반으로 자동 작성되었습니다. 법률 자문이 아니며, 특수 고용형태나 분쟁 소지가 있는 내용은 전문가 검토를 받으시기 바랍니다.");
  contractSheet.getRange(row, 1).setFontStyle("italic").setFontColor("#666666");

  if (warning) {
    row += 2;
    contractSheet.getRange(row, 1).setValue(warning).setFontWeight("bold").setFontColor("#cc0000");
  }

  contractSheet.setColumnWidth(1, 650);
  contractSheet.getRange(1, 1, row, 1).setWrap(true);

  SpreadsheetApp.getUi().alert(warning ? `계약서를 생성했습니다.\n\n${warning}` : `${s.name}님 근로계약서를 생성했습니다.`);
}

function exportSheetAsPdfBlob_(ss, sheet) {
  const url =
    `https://docs.google.com/spreadsheets/d/${ss.getId()}/export` +
    `?format=pdf&gid=${sheet.getSheetId()}&size=A4&portrait=true&fitw=true&gridlines=false`;
  const token = ScriptApp.getOAuthToken();
  const response = UrlFetchApp.fetch(url, { headers: { Authorization: "Bearer " + token } });
  return response.getBlob();
}

function saveContractAsPdf() {
  const ss = SpreadsheetApp.getActive();
  const contractSheet = ss.getSheetByName(SHEET_CONTRACT);
  const controlSheet = ss.getSheetByName(SHEET_CONTROL);
  const staffName = controlSheet.getRange("B1").getValue() || "근로자";

  const blob = exportSheetAsPdfBlob_(ss, contractSheet);
  const folderName = "근로계약서_PDF";
  const folders = DriveApp.getFoldersByName(folderName);
  const folder = folders.hasNext() ? folders.next() : DriveApp.createFolder(folderName);

  const fileName = `근로계약서_${staffName}_${Utilities.formatDate(new Date(), "GMT+9", "yyyyMMdd")}.pdf`;
  folder.createFile(blob.setName(fileName));

  SpreadsheetApp.getUi().alert(`"${folderName}" 폴더에 저장했습니다: ${fileName}`);
}

function emailContract() {
  const ss = SpreadsheetApp.getActive();
  const contractSheet = ss.getSheetByName(SHEET_CONTRACT);
  const controlSheet = ss.getSheetByName(SHEET_CONTROL);
  const staffName = controlSheet.getRange("B1").getValue();
  if (!staffName) {
    SpreadsheetApp.getUi().alert("먼저 계약서를 생성해주세요.");
    return;
  }
  const s = findStaff_(staffName);

  const ui = SpreadsheetApp.getUi();
  const result = ui.prompt(`${staffName}님에게 보낼 이메일 주소를 확인/입력하세요:`, s.email || "", ui.ButtonSet.OK_CANCEL);
  if (result.getSelectedButton() !== ui.Button.OK) return;
  const to = result.getResponseText().trim();
  if (!to) return;

  const settings = getSettings_();
  const blob = exportSheetAsPdfBlob_(ss, contractSheet);
  GmailApp.sendEmail(to, `${settings["사업체명"] || ""} 근로계약서 - ${s.name}`, "근로계약서를 첨부해 드립니다. 확인 부탁드립니다.", {
    attachments: [blob.setName(`근로계약서_${s.name}.pdf`)],
    name: settings["사업체명"] || "",
  });

  SpreadsheetApp.getUi().alert(`${to} 로 발송했습니다.`);
}
