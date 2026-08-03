/**
 * 급여명세서 자동계산기 — Apps Script
 *
 * 설치 방법:
 * 1. 구글시트를 새로 만들고 "설정", "직원정보", "급여명세서" 3개 시트를 만든다
 *    (정확한 칸 구조는 같은 폴더의 템플릿_구조.md 참고)
 * 2. 상단 메뉴 [확장 프로그램 > Apps Script]를 클릭
 * 3. 열린 편집기에 이 파일 내용을 전부 붙여넣고 저장 (Ctrl+S)
 * 4. 구글시트로 돌아오면 "급여명세서 자동화"라는 메뉴가 새로 생긴다 (새로고침 필요할 수 있음)
 */

const SHEET_SETTINGS = "설정";
const SHEET_STAFF = "직원정보";
const SHEET_PAYSLIP = "급여명세서";

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu("급여명세서 자동화")
    .addItem("① 급여명세서 생성/새로고침", "generatePayslip")
    .addItem("② PDF로 저장 (내 드라이브)", "savePayslipAsPdf")
    .addItem("③ 이메일로 보내기", "emailPayslip")
    .addSeparator()
    .addItem("④ 전체 직원 일괄 이메일 발송", "emailAllPayslips")
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
  // 2행부터 데이터, 컬럼: 성명 | 기본급 | 상여금등 | 비과세수당 | 소득세 | 이메일 | 부양가족수
  const values = sheet.getRange(2, 1, lastRow - 1, 7).getValues();
  return values
    .filter((row) => row[0])
    .map((row) => ({
      name: row[0],
      base: Number(row[1]) || 0,
      bonus: Number(row[2]) || 0,
      nonTaxable: Number(row[3]) || 0,
      incomeTax: Number(row[4]) || 0,
      email: row[5],
      dependents: row[6],
    }));
}

function findStaff_(name) {
  const staff = getStaffList_();
  const found = staff.find((s) => s.name === name);
  if (!found) throw new Error(`직원정보 시트에서 "${name}"을(를) 찾을 수 없습니다.`);
  return found;
}

/**
 * 한 직원의 급여 항목을 받아 4대보험·실수령액을 계산한다.
 * 소득세는 직접입력값을 그대로 쓰고(직원정보 E열), 지방소득세만 소득세의 10%로 자동계산한다.
 */
function calcPayroll_(staff, settings) {
  const taxableIncome = staff.base + staff.bonus - staff.nonTaxable;

  const npRate = Number(settings["국민연금_근로자요율"]) || 0.0475;
  const npCap = Number(settings["국민연금_상한액"]) || 6370000;
  const npFloor = Number(settings["국민연금_하한액"]) || 400000;
  // 국민연금 기준소득월액은 1,000원 미만을 절사하고 상/하한을 적용한다
  let npBase = Math.floor(taxableIncome / 1000) * 1000;
  npBase = Math.min(Math.max(npBase, npFloor), npCap);
  const nationalPension = Math.round(npBase * npRate);

  const hiRate = Number(settings["건강보험_근로자요율"]) || 0.03595;
  const healthInsurance = Math.round(taxableIncome * hiRate);

  const ltcRate = Number(settings["장기요양보험_요율"]) || 0.1295;
  const longTermCare = Math.round(healthInsurance * ltcRate);

  const eiRate = Number(settings["고용보험_근로자요율"]) || 0.009;
  const employmentInsurance = Math.round(taxableIncome * eiRate);

  const incomeTax = staff.incomeTax || 0;
  const localIncomeTax = Math.round(incomeTax * 0.1);

  const totalDeduction =
    nationalPension + healthInsurance + longTermCare + employmentInsurance + incomeTax + localIncomeTax;
  const totalPay = staff.base + staff.bonus + staff.nonTaxable;
  const netPay = totalPay - totalDeduction;

  // 참고용 — 사업주 부담분(인건비 총액 파악용, 명세서에는 별도 표기)
  const npRateEmployer = Number(settings["국민연금_사업주요율"]) || 0.0475;
  const hiRateEmployer = Number(settings["건강보험_사업주요율"]) || 0.03595;
  const eiRateEmployer = Number(settings["고용보험_사업주요율"]) || 0.0115;
  const nationalPensionEmployer = Math.round(npBase * npRateEmployer);
  const healthInsuranceEmployer = Math.round(taxableIncome * hiRateEmployer);
  const longTermCareEmployer = Math.round(healthInsuranceEmployer * ltcRate);
  const employmentInsuranceEmployer = Math.round(taxableIncome * eiRateEmployer);

  return {
    taxableIncome,
    totalPay,
    nationalPension,
    healthInsurance,
    longTermCare,
    employmentInsurance,
    incomeTax,
    localIncomeTax,
    totalDeduction,
    netPay,
    employerBurden:
      nationalPensionEmployer + healthInsuranceEmployer + longTermCareEmployer + employmentInsuranceEmployer,
  };
}

function renderPayslip_(quoteSheet, staff, calc, settings) {
  quoteSheet.clear();
  quoteSheet.getRange("A1").setValue("급 여 명 세 서").setFontSize(20).setFontWeight("bold");
  quoteSheet.getRange("A3").setValue(`발행일: ${Utilities.formatDate(new Date(), "GMT+9", "yyyy-MM-dd")}`);
  quoteSheet.getRange("A4").setValue(`회사명: ${settings["회사명"] || ""} (${settings["사업자번호"] || ""})`);
  quoteSheet.getRange("A5").setValue(`성명: ${staff.name}`);
  quoteSheet.getRange("A6").setValue(`부양가족수(참고): ${staff.dependents || ""}`);

  let row = 8;
  quoteSheet.getRange(row, 1).setValue("지급 항목").setFontWeight("bold");
  quoteSheet.getRange(row, 2).setValue("금액").setFontWeight("bold");
  row++;
  quoteSheet.getRange(row, 1).setValue("기본급");
  quoteSheet.getRange(row, 2).setValue(staff.base);
  row++;
  quoteSheet.getRange(row, 1).setValue("상여금 등(과세)");
  quoteSheet.getRange(row, 2).setValue(staff.bonus);
  row++;
  quoteSheet.getRange(row, 1).setValue("비과세수당");
  quoteSheet.getRange(row, 2).setValue(staff.nonTaxable);
  row++;
  quoteSheet.getRange(row, 1).setValue("지급 총액").setFontWeight("bold");
  quoteSheet.getRange(row, 2).setValue(calc.totalPay).setFontWeight("bold");

  row += 2;
  quoteSheet.getRange(row, 1).setValue("공제 항목").setFontWeight("bold");
  quoteSheet.getRange(row, 2).setValue("금액").setFontWeight("bold");
  row++;
  quoteSheet.getRange(row, 1).setValue("국민연금");
  quoteSheet.getRange(row, 2).setValue(calc.nationalPension);
  row++;
  quoteSheet.getRange(row, 1).setValue("건강보험");
  quoteSheet.getRange(row, 2).setValue(calc.healthInsurance);
  row++;
  quoteSheet.getRange(row, 1).setValue("장기요양보험");
  quoteSheet.getRange(row, 2).setValue(calc.longTermCare);
  row++;
  quoteSheet.getRange(row, 1).setValue("고용보험");
  quoteSheet.getRange(row, 2).setValue(calc.employmentInsurance);
  row++;
  quoteSheet.getRange(row, 1).setValue("소득세(간이세액표 조회값 입력)");
  quoteSheet.getRange(row, 2).setValue(calc.incomeTax);
  row++;
  quoteSheet.getRange(row, 1).setValue("지방소득세(소득세의 10%)");
  quoteSheet.getRange(row, 2).setValue(calc.localIncomeTax);
  row++;
  quoteSheet.getRange(row, 1).setValue("공제 총액").setFontWeight("bold");
  quoteSheet.getRange(row, 2).setValue(calc.totalDeduction).setFontWeight("bold");

  row += 2;
  quoteSheet.getRange(row, 1).setValue("차인지급액(실수령액)").setFontSize(13).setFontWeight("bold");
  quoteSheet.getRange(row, 2).setValue(calc.netPay).setFontSize(13).setFontWeight("bold");

  row += 2;
  quoteSheet.getRange(row, 1).setValue("참고: 회사 부담분(4대보험 사업주 몫, 인건비 총액 파악용)");
  row++;
  quoteSheet.getRange(row, 1).setValue("사업주 부담 4대보험 합계");
  quoteSheet.getRange(row, 2).setValue(calc.employerBurden);
  row++;
  quoteSheet
    .getRange(row, 1)
    .setValue("※ 산재보험은 업종별 요율이 달라 이 표에 포함되지 않았습니다. 근로복지공단에서 별도 확인하세요.");

  quoteSheet.autoResizeColumns(1, 2);
}

/**
 * "급여명세서" 시트 B1에서 선택한 직원 기준으로 명세서를 다시 그린다.
 */
function generatePayslip() {
  const ss = SpreadsheetApp.getActive();
  const payslipSheet = ss.getSheetByName(SHEET_PAYSLIP);
  if (!payslipSheet) throw new Error(`"${SHEET_PAYSLIP}" 시트를 찾을 수 없습니다.`);

  const selectedName = payslipSheet.getRange("B1").getValue();
  if (!selectedName) {
    SpreadsheetApp.getUi().alert("먼저 B1 셀에서 직원을 선택해주세요.");
    return;
  }

  const settings = getSettings_();
  const staff = findStaff_(selectedName);
  const calc = calcPayroll_(staff, settings);

  // B1 선택값은 유지한 채 나머지만 다시 그리기 위해 임시 저장 후 복원
  renderPayslip_(payslipSheet, staff, calc, settings);
  payslipSheet.getRange("B1").setValue(selectedName);

  SpreadsheetApp.getUi().alert(`${staff.name}님 급여명세서를 생성했습니다. 실수령액: ${calc.netPay.toLocaleString()}원`);
}

function exportSheetAsPdfBlob_(ss, sheet) {
  const url =
    `https://docs.google.com/spreadsheets/d/${ss.getId()}/export` +
    `?format=pdf&gid=${sheet.getSheetId()}&size=A4&portrait=true&fitw=true&gridlines=false`;
  const token = ScriptApp.getOAuthToken();
  const response = UrlFetchApp.fetch(url, { headers: { Authorization: "Bearer " + token } });
  return response.getBlob();
}

/**
 * 현재 "급여명세서" 시트 내용을 PDF로 저장한다.
 */
function savePayslipAsPdf() {
  const ss = SpreadsheetApp.getActive();
  const payslipSheet = ss.getSheetByName(SHEET_PAYSLIP);
  if (!payslipSheet) throw new Error(`"${SHEET_PAYSLIP}" 시트를 찾을 수 없습니다.`);

  const staffName = payslipSheet.getRange("B1").getValue() || "직원";
  const blob = exportSheetAsPdfBlob_(ss, payslipSheet);

  const folderName = "급여명세서_PDF";
  const folders = DriveApp.getFoldersByName(folderName);
  const folder = folders.hasNext() ? folders.next() : DriveApp.createFolder(folderName);

  const fileName = `급여명세서_${staffName}_${Utilities.formatDate(new Date(), "GMT+9", "yyyyMM")}.pdf`;
  folder.createFile(blob.setName(fileName));

  SpreadsheetApp.getUi().alert(`"${folderName}" 폴더에 저장했습니다: ${fileName}`);
}

/**
 * 현재 선택된 직원의 명세서를 이메일로 발송한다.
 * 직원정보 시트에 이메일이 입력돼 있으면 자동으로 채워서 확인창을 띄운다.
 */
function emailPayslip() {
  const ss = SpreadsheetApp.getActive();
  const payslipSheet = ss.getSheetByName(SHEET_PAYSLIP);
  if (!payslipSheet) throw new Error(`"${SHEET_PAYSLIP}" 시트를 찾을 수 없습니다.`);

  const staffName = payslipSheet.getRange("B1").getValue();
  if (!staffName) {
    SpreadsheetApp.getUi().alert("먼저 급여명세서를 생성해주세요.");
    return;
  }
  const staff = findStaff_(staffName);

  const ui = SpreadsheetApp.getUi();
  const result = ui.prompt(`${staffName}님에게 보낼 이메일 주소를 확인/입력하세요:`, staff.email || "", ui.ButtonSet.OK_CANCEL);
  if (result.getSelectedButton() !== ui.Button.OK) return;
  const to = result.getResponseText().trim();
  if (!to) return;

  const settings = getSettings_();
  const blob = exportSheetAsPdfBlob_(ss, payslipSheet);
  GmailApp.sendEmail(to, `${settings["회사명"] || ""} 급여명세서 (${staffName})`, "급여명세서를 첨부해 드립니다. 확인 부탁드립니다.", {
    attachments: [blob.setName(`급여명세서_${staffName}.pdf`)],
    name: settings["회사명"] || "",
  });

  SpreadsheetApp.getUi().alert(`${to} 로 발송했습니다.`);
}

/**
 * 직원정보 시트에 등록된 전체 직원에게 순서대로 급여명세서를 만들어 이메일로 발송한다.
 * 이메일이 비어있는 직원은 건너뛴다.
 */
function emailAllPayslips() {
  const ui = SpreadsheetApp.getUi();
  const confirm = ui.alert(
    "전체 직원 일괄 발송",
    "직원정보 시트에 이메일이 입력된 모든 직원에게 급여명세서를 발송합니다. 계속할까요?",
    ui.ButtonSet.YES_NO
  );
  if (confirm !== ui.Button.YES) return;

  const ss = SpreadsheetApp.getActive();
  const payslipSheet = ss.getSheetByName(SHEET_PAYSLIP);
  const settings = getSettings_();
  const staffList = getStaffList_();

  let sent = 0;
  let skipped = 0;
  staffList.forEach((staff) => {
    if (!staff.email) {
      skipped++;
      return;
    }
    const calc = calcPayroll_(staff, settings);
    renderPayslip_(payslipSheet, staff, calc, settings);
    payslipSheet.getRange("B1").setValue(staff.name);
    SpreadsheetApp.flush();

    const blob = exportSheetAsPdfBlob_(ss, payslipSheet);
    GmailApp.sendEmail(
      staff.email,
      `${settings["회사명"] || ""} 급여명세서 (${staff.name})`,
      "급여명세서를 첨부해 드립니다. 확인 부탁드립니다.",
      { attachments: [blob.setName(`급여명세서_${staff.name}.pdf`)], name: settings["회사명"] || "" }
    );
    sent++;
  });

  ui.alert(`발송 완료: ${sent}명, 이메일 없어서 건너뜀: ${skipped}명`);
}
