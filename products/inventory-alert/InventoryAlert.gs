/**
 * 재고 부족 자동알림 + 입출고 관리 시트 — Apps Script
 *
 * 설치 방법:
 * 1. 구글시트를 새로 만들고 "설정", "품목마스터", "입출고기록", "재고현황" 4개 시트를 만든다
 *    (정확한 칸 구조는 같은 폴더의 템플릿_구조.md 참고)
 * 2. 상단 메뉴 [확장 프로그램 > Apps Script]를 클릭
 * 3. 열린 편집기에 이 파일 내용을 전부 붙여넣고 저장 (Ctrl+S)
 * 4. 구글시트로 돌아오면 "재고 자동알림"이라는 메뉴가 새로 생긴다 (새로고침 필요할 수 있음)
 */

const SHEET_SETTINGS = "설정";
const SHEET_ITEM_MASTER = "품목마스터";
const SHEET_MOVEMENTS = "입출고기록";
const SHEET_STATUS = "재고현황";

const LOW_STOCK_COLOR = "#f4cccc"; // 연한 빨강
const OK_STOCK_COLOR = "#ffffff";

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu("재고 자동알림")
    .addItem("① 재고현황 새로고침", "generateInventoryStatus")
    .addItem("② 재고현황 PDF로 저장", "saveStatusAsPdf")
    .addItem("③ 재고부족 알림 이메일 발송", "emailLowStockAlert")
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

function getItemMaster_() {
  const sheet = SpreadsheetApp.getActive().getSheetByName(SHEET_ITEM_MASTER);
  if (!sheet) throw new Error(`"${SHEET_ITEM_MASTER}" 시트를 찾을 수 없습니다.`);
  const lastRow = sheet.getLastRow();
  if (lastRow < 2) return [];
  // 2행부터, 컬럼: 품목명 | 단위 | 최소재고기준 | 초기재고
  const values = sheet.getRange(2, 1, lastRow - 1, 4).getValues();
  return values
    .filter((row) => row[0])
    .map((row) => ({
      name: row[0],
      unit: row[1],
      minStock: Number(row[2]) || 0,
      initialStock: Number(row[3]) || 0,
    }));
}

function getMovements_() {
  const sheet = SpreadsheetApp.getActive().getSheetByName(SHEET_MOVEMENTS);
  if (!sheet) throw new Error(`"${SHEET_MOVEMENTS}" 시트를 찾을 수 없습니다.`);
  const lastRow = sheet.getLastRow();
  if (lastRow < 2) return [];
  // 2행부터, 컬럼: 날짜 | 품목명 | 구분(입고/출고) | 수량 | 메모
  const values = sheet.getRange(2, 1, lastRow - 1, 5).getValues();
  return values
    .filter((row) => row[1])
    .map((row) => ({
      date: row[0],
      name: row[1],
      type: String(row[2]).trim(),
      qty: Number(row[3]) || 0,
      note: row[4],
    }));
}

/**
 * 품목마스터의 초기재고에 입출고기록을 더하고 빼서 품목별 현재재고를 계산한다.
 */
function calcStock_() {
  const items = getItemMaster_();
  const movements = getMovements_();

  return items.map((item) => {
    let stock = item.initialStock;
    movements.forEach((m) => {
      if (m.name !== item.name) return;
      if (m.type === "입고") stock += m.qty;
      else if (m.type === "출고") stock -= m.qty;
    });
    return {
      name: item.name,
      unit: item.unit,
      minStock: item.minStock,
      stock: stock,
      isLow: stock <= item.minStock,
    };
  });
}

/**
 * "재고현황" 시트를 다시 그린다. 부족한 품목은 빨간색으로 표시한다.
 */
function generateInventoryStatus() {
  const ss = SpreadsheetApp.getActive();
  const statusSheet = ss.getSheetByName(SHEET_STATUS);
  if (!statusSheet) throw new Error(`"${SHEET_STATUS}" 시트를 찾을 수 없습니다.`);

  const settings = getSettings_();
  const stockList = calcStock_();

  statusSheet.clear();
  statusSheet.getRange("A1").setValue("재 고 현 황").setFontSize(18).setFontWeight("bold");
  statusSheet.getRange("A2").setValue(`${settings["회사명"] || ""} · 기준일: ${Utilities.formatDate(new Date(), "GMT+9", "yyyy-MM-dd")}`);

  const headerRow = 4;
  const headers = ["품목명", "단위", "현재재고", "최소재고기준", "상태"];
  statusSheet.getRange(headerRow, 1, 1, headers.length).setValues([headers]).setFontWeight("bold");

  let row = headerRow + 1;
  stockList.forEach((item) => {
    const status = item.isLow ? "부족" : "정상";
    statusSheet.getRange(row, 1, 1, 5).setValues([[item.name, item.unit, item.stock, item.minStock, status]]);
    const rowRange = statusSheet.getRange(row, 1, 1, 5);
    rowRange.setBackground(item.isLow ? LOW_STOCK_COLOR : OK_STOCK_COLOR);
    row++;
  });

  const lowCount = stockList.filter((i) => i.isLow).length;
  row++;
  statusSheet.getRange(row, 1).setValue(`부족 품목: ${lowCount}개 / 전체 ${stockList.length}개`).setFontWeight("bold");

  statusSheet.autoResizeColumns(1, 5);
  SpreadsheetApp.getUi().alert(`재고현황을 새로고침했습니다. 부족 품목 ${lowCount}개.`);
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
 * 현재 "재고현황" 시트 내용을 PDF로 저장한다.
 */
function saveStatusAsPdf() {
  const ss = SpreadsheetApp.getActive();
  const statusSheet = ss.getSheetByName(SHEET_STATUS);
  if (!statusSheet) throw new Error(`"${SHEET_STATUS}" 시트를 찾을 수 없습니다.`);

  const blob = exportSheetAsPdfBlob_(ss, statusSheet);
  const folderName = "재고현황_PDF";
  const folders = DriveApp.getFoldersByName(folderName);
  const folder = folders.hasNext() ? folders.next() : DriveApp.createFolder(folderName);

  const fileName = `재고현황_${Utilities.formatDate(new Date(), "GMT+9", "yyyyMMdd_HHmm")}.pdf`;
  folder.createFile(blob.setName(fileName));

  SpreadsheetApp.getUi().alert(`"${folderName}" 폴더에 저장했습니다: ${fileName}`);
}

/**
 * 재고현황을 다시 계산해서, 최소재고 미달 품목이 있으면 설정 시트에 등록된 이메일로 알림을 보낸다.
 * 매일 자동으로 실행하고 싶다면 템플릿_구조.md의 "매일 자동으로 알림받고 싶다면" 항목을 참고해
 * Apps Script 트리거에 이 함수(emailLowStockAlert)를 등록하면 된다.
 */
function emailLowStockAlert() {
  const ss = SpreadsheetApp.getActive();
  const statusSheet = ss.getSheetByName(SHEET_STATUS);
  const settings = getSettings_();
  const to = settings["알림받을이메일"];

  generateInventoryStatus();
  const stockList = calcStock_();
  const lowItems = stockList.filter((i) => i.isLow);

  if (lowItems.length === 0) {
    SpreadsheetApp.getUi().alert("현재 재고 부족 품목이 없어 이메일을 보내지 않았습니다.");
    return;
  }

  if (!to) {
    SpreadsheetApp.getUi().alert('"설정" 시트의 알림받을이메일 칸이 비어있어 발송하지 못했습니다.');
    return;
  }

  const lines = lowItems.map((i) => `- ${i.name}: 현재재고 ${i.stock}${i.unit} (기준 ${i.minStock}${i.unit} 이하)`);
  const body = `재고가 부족한 품목이 ${lowItems.length}개 있습니다.\n\n` + lines.join("\n");
  const blob = exportSheetAsPdfBlob_(ss, statusSheet);

  GmailApp.sendEmail(to, `[재고부족알림] ${settings["회사명"] || ""} 부족 품목 ${lowItems.length}개`, body, {
    attachments: [blob.setName("재고현황.pdf")],
    name: settings["회사명"] || "",
  });

  SpreadsheetApp.getUi().alert(`${to} 로 재고부족 알림을 보냈습니다 (${lowItems.length}개 품목).`);
}
