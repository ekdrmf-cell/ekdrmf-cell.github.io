/**
 * 매입매출장 자동정리 + 부가세 예상액 계산 시트 — Apps Script
 *
 * 이 스크립트는 세금 신고를 대행하지 않으며, 선택한 기간의 매입매출을 정리해
 * "예상 납부세액"을 계산해주는 참고용 도구입니다. 일반과세자 전용입니다(간이과세자 제외).
 * 실제 신고는 홈택스에서 직접 하거나 세무사와 상담하세요.
 *
 * 설치 방법:
 * 1. 구글시트를 새로 만들고 "설정", "매입매출기록", "집계기간선택", "부가세현황" 4개 시트를 만든다
 *    (정확한 칸 구조는 같은 폴더의 템플릿_구조.md 참고)
 * 2. 상단 메뉴 [확장 프로그램 > Apps Script]를 클릭
 * 3. 열린 편집기에 이 파일 내용을 전부 붙여넣고 저장 (Ctrl+S)
 * 4. 구글시트로 돌아오면 "부가세 예상액 계산"이라는 메뉴가 새로 생긴다 (새로고침 필요할 수 있음)
 */

const SHEET_SETTINGS = "설정";
const SHEET_RECORDS = "매입매출기록";
const SHEET_PERIOD = "집계기간선택";
const SHEET_STATUS = "부가세현황";

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu("부가세 예상액 계산")
    .addItem("① 부가세현황 계산/새로고침", "generateVatStatus")
    .addItem("② 부가세현황 PDF로 저장", "saveStatusAsPdf")
    .addItem("③ 이메일로 보내기 (세무사/본인)", "emailStatus")
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

function getRecords_() {
  const sheet = SpreadsheetApp.getActive().getSheetByName(SHEET_RECORDS);
  if (!sheet) throw new Error(`"${SHEET_RECORDS}" 시트를 찾을 수 없습니다.`);
  const lastRow = sheet.getLastRow();
  if (lastRow < 2) return [];
  // 2행부터, 컬럼: 날짜 | 구분(매출/매입) | 거래처 | 공급가액 | 부가세 | 공제여부 | 비고
  const values = sheet.getRange(2, 1, lastRow - 1, 7).getValues();
  return values
    .filter((row) => row[1])
    .map((row) => ({
      date: row[0],
      type: String(row[1]).trim(),
      partner: row[2],
      supplyAmount: Number(row[3]) || 0,
      vat: Number(row[4]) || 0,
      deductible: String(row[5] || "").trim(),
      note: row[6],
    }));
}

function getPeriod_() {
  const sheet = SpreadsheetApp.getActive().getSheetByName(SHEET_PERIOD);
  if (!sheet) throw new Error(`"${SHEET_PERIOD}" 시트를 찾을 수 없습니다.`);
  const data = sheet.getRange("A1:B2").getValues();
  return { start: data[0][1], end: data[1][1] };
}

function inPeriod_(date, start, end) {
  if (!(date instanceof Date) || !(start instanceof Date) || !(end instanceof Date)) return false;
  const d = new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime();
  const s = new Date(start.getFullYear(), start.getMonth(), start.getDate()).getTime();
  const e = new Date(end.getFullYear(), end.getMonth(), end.getDate()).getTime();
  return d >= s && d <= e;
}

/**
 * 선택한 기간의 매출세액·매입세액(공제가능분)을 집계해서 예상 납부/환급세액을 계산한다.
 */
function calcVat_() {
  const records = getRecords_();
  const period = getPeriod_();
  const inRange = records.filter((r) => inPeriod_(r.date, period.start, period.end));

  const sales = inRange.filter((r) => r.type === "매출");
  const purchases = inRange.filter((r) => r.type === "매입");

  const salesSupplyTotal = sales.reduce((sum, r) => sum + r.supplyAmount, 0);
  const salesVatTotal = sales.reduce((sum, r) => sum + r.vat, 0);

  const deductiblePurchases = purchases.filter((r) => r.deductible === "공제가능");
  const nonDeductiblePurchases = purchases.filter((r) => r.deductible === "공제불가");
  const unmarkedPurchases = purchases.filter((r) => r.deductible !== "공제가능" && r.deductible !== "공제불가");

  const purchaseSupplyTotal = purchases.reduce((sum, r) => sum + r.supplyAmount, 0);
  const deductibleVatTotal = deductiblePurchases.reduce((sum, r) => sum + r.vat, 0);
  const nonDeductibleVatTotal = nonDeductiblePurchases.reduce((sum, r) => sum + r.vat, 0);

  const estimatedVat = salesVatTotal - deductibleVatTotal;

  return {
    period,
    salesCount: sales.length,
    salesSupplyTotal,
    salesVatTotal,
    purchaseCount: purchases.length,
    purchaseSupplyTotal,
    deductibleVatTotal,
    nonDeductibleVatTotal,
    unmarkedCount: unmarkedPurchases.length,
    estimatedVat,
  };
}

function formatDate_(d) {
  if (d instanceof Date) return Utilities.formatDate(d, "GMT+9", "yyyy-MM-dd");
  return String(d || "");
}

/**
 * "부가세현황" 시트를 다시 그린다.
 */
function generateVatStatus() {
  const ss = SpreadsheetApp.getActive();
  const statusSheet = ss.getSheetByName(SHEET_STATUS);
  if (!statusSheet) throw new Error(`"${SHEET_STATUS}" 시트를 찾을 수 없습니다.`);

  const settings = getSettings_();
  const c = calcVat_();

  statusSheet.clear();
  let row = 1;
  statusSheet.getRange(row, 1).setValue("부 가 세 예 상 액 현 황").setFontSize(18).setFontWeight("bold");
  row++;
  statusSheet.getRange(row, 1).setValue(`${settings["상호(사업자명)"] || ""} · 집계기간: ${formatDate_(c.period.start)} ~ ${formatDate_(c.period.end)}`);
  row += 2;

  statusSheet.getRange(row, 1).setValue(`매출 ${c.salesCount}건 · 공급가액 합계 ${c.salesSupplyTotal.toLocaleString()}원 · 매출세액 ${c.salesVatTotal.toLocaleString()}원`);
  row++;
  statusSheet.getRange(row, 1).setValue(`매입 ${c.purchaseCount}건 · 공급가액 합계 ${c.purchaseSupplyTotal.toLocaleString()}원`);
  row++;
  statusSheet.getRange(row, 1).setValue(`  - 공제가능 매입세액 합계: ${c.deductibleVatTotal.toLocaleString()}원`);
  row++;
  statusSheet.getRange(row, 1).setValue(`  - 공제불가 매입세액 합계: ${c.nonDeductibleVatTotal.toLocaleString()}원`);
  row++;
  if (c.unmarkedCount > 0) {
    statusSheet
      .getRange(row, 1)
      .setValue(`  ⚠ 공제여부가 "공제가능"/"공제불가"로 입력되지 않은 매입 ${c.unmarkedCount}건이 있어 집계에서 제외했습니다. 매입매출기록 F열을 확인하세요.`)
      .setFontColor("#cc6600");
    row++;
  }
  row++;

  statusSheet
    .getRange(row, 1)
    .setValue(`예상 ${c.estimatedVat >= 0 ? "납부" : "환급"}세액: ${Math.abs(c.estimatedVat).toLocaleString()}원`)
    .setFontSize(14)
    .setFontWeight("bold");
  row += 2;

  statusSheet
    .getRange(row, 1)
    .setValue("※ 이 금액은 참고용 예상치입니다. 실제 신고서 작성·제출은 홈택스에서 직접 하거나 세무사와 상담하세요. 이 템플릿은 세금 신고를 대행하지 않으며, 일반과세자 전용입니다(간이과세자는 계산방식이 다릅니다).")
    .setFontStyle("italic")
    .setFontColor("#666666");

  statusSheet.setColumnWidth(1, 650);
  statusSheet.getRange(1, 1, row, 1).setWrap(true);

  SpreadsheetApp.getUi().alert(`계산 완료. 예상 ${c.estimatedVat >= 0 ? "납부" : "환급"}세액: ${Math.abs(c.estimatedVat).toLocaleString()}원`);
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
  const folderName = "부가세현황_PDF";
  const folders = DriveApp.getFoldersByName(folderName);
  const folder = folders.hasNext() ? folders.next() : DriveApp.createFolder(folderName);

  const fileName = `부가세현황_${Utilities.formatDate(new Date(), "GMT+9", "yyyyMMdd_HHmm")}.pdf`;
  folder.createFile(blob.setName(fileName));

  SpreadsheetApp.getUi().alert(`"${folderName}" 폴더에 저장했습니다: ${fileName}`);
}

/**
 * 부가세현황을 이메일로 보낸다. 설정 시트에 세무사이메일이 있으면 기본값으로 채워준다.
 */
function emailStatus() {
  const ss = SpreadsheetApp.getActive();
  const statusSheet = ss.getSheetByName(SHEET_STATUS);
  if (!statusSheet) throw new Error(`"${SHEET_STATUS}" 시트를 찾을 수 없습니다.`);

  const settings = getSettings_();
  const ui = SpreadsheetApp.getUi();
  const result = ui.prompt("보낼 이메일 주소를 확인/입력하세요:", settings["세무사이메일"] || "", ui.ButtonSet.OK_CANCEL);
  if (result.getSelectedButton() !== ui.Button.OK) return;
  const to = result.getResponseText().trim();
  if (!to) return;

  const blob = exportSheetAsPdfBlob_(ss, statusSheet);
  GmailApp.sendEmail(to, `${settings["상호(사업자명)"] || ""} 부가세 예상액 현황`, "부가세 예상액 현황을 첨부해 드립니다. 참고용 자료이며 실제 신고 시 세무사와 다시 확인해주세요.", {
    attachments: [blob.setName("부가세현황.pdf")],
    name: settings["상호(사업자명)"] || "",
  });

  SpreadsheetApp.getUi().alert(`${to} 로 발송했습니다.`);
}
