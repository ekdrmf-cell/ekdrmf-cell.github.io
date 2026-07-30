/**
 * 견적서 자동생성 템플릿 — Apps Script
 *
 * 설치 방법:
 * 1. 구글시트를 새로 만들고 "설정", "항목입력", "견적서" 3개 시트를 만든다
 *    (정확한 칸 구조는 같은 폴더의 템플릿_구조.md 참고)
 * 2. 상단 메뉴 [확장 프로그램 > Apps Script]를 클릭
 * 3. 열린 편집기에 이 파일 내용을 전부 붙여넣고 저장 (Ctrl+S)
 * 4. 구글시트로 돌아오면 "견적서 자동화"라는 메뉴가 새로 생긴다 (새로고침 필요할 수 있음)
 */

const SHEET_SETTINGS = "설정";
const SHEET_ITEMS = "항목입력";
const SHEET_QUOTE = "견적서";

// 시트를 열 때마다 커스텀 메뉴를 추가한다
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu("견적서 자동화")
    .addItem("① 견적서 생성/새로고침", "generateQuote")
    .addItem("② PDF로 저장 (내 드라이브)", "saveQuoteAsPdf")
    .addItem("③ 이메일로 보내기", "emailQuote")
    .addToUi();
}

function getSettings_() {
  const sheet = SpreadsheetApp.getActive().getSheetByName(SHEET_SETTINGS);
  if (!sheet) throw new Error(`"${SHEET_SETTINGS}" 시트를 찾을 수 없습니다.`);
  // 설정 시트는 B열에 값이 들어있는 구조 (A열=항목명, B열=값)
  const data = sheet.getRange("A1:B10").getValues();
  const map = {};
  data.forEach((row) => {
    if (row[0]) map[row[0]] = row[1];
  });
  return map;
}

function getItems_() {
  const sheet = SpreadsheetApp.getActive().getSheetByName(SHEET_ITEMS);
  if (!sheet) throw new Error(`"${SHEET_ITEMS}" 시트를 찾을 수 없습니다.`);
  const lastRow = sheet.getLastRow();
  if (lastRow < 2) return [];
  // 2행부터 데이터 시작, 컬럼: 품목 | 규격 | 수량 | 단가 | 비고
  const values = sheet.getRange(2, 1, lastRow - 1, 5).getValues();
  return values
    .filter((row) => row[0]) // 품목명이 있는 행만
    .map((row) => ({
      name: row[0],
      spec: row[1],
      qty: Number(row[2]) || 0,
      price: Number(row[3]) || 0,
      note: row[4],
    }));
}

/**
 * "항목입력" 시트의 내용을 읽어 "견적서" 시트를 다시 그린다.
 * 여러 번 실행해도 안전하도록 매번 표 영역을 초기화하고 새로 채운다.
 */
function generateQuote() {
  const ss = SpreadsheetApp.getActive();
  const quoteSheet = ss.getSheetByName(SHEET_QUOTE);
  if (!quoteSheet) throw new Error(`"${SHEET_QUOTE}" 시트를 찾을 수 없습니다.`);

  const settings = getSettings_();
  const items = getItems_();

  quoteSheet.clear();

  // 상단 문서 제목/발행 정보
  quoteSheet.getRange("A1").setValue("견 적 서").setFontSize(20).setFontWeight("bold");
  quoteSheet.getRange("A3").setValue(`발행일: ${Utilities.formatDate(new Date(), "GMT+9", "yyyy-MM-dd")}`);
  quoteSheet.getRange("A4").setValue(`공급자: ${settings["회사명"] || ""} (${settings["사업자번호"] || ""})`);
  quoteSheet.getRange("A5").setValue(`대표자: ${settings["대표자"] || ""}  연락처: ${settings["연락처"] || ""}`);
  quoteSheet.getRange("A6").setValue(`주소: ${settings["주소"] || ""}`);

  // 표 헤더
  const headerRow = 8;
  const headers = ["품목", "규격", "수량", "단가", "금액", "비고"];
  quoteSheet.getRange(headerRow, 1, 1, headers.length).setValues([headers]).setFontWeight("bold");

  // 항목 채우기
  let row = headerRow + 1;
  let subtotal = 0;
  items.forEach((item) => {
    const amount = item.qty * item.price;
    subtotal += amount;
    quoteSheet
      .getRange(row, 1, 1, 6)
      .setValues([[item.name, item.spec, item.qty, item.price, amount, item.note]]);
    row++;
  });

  const vatRate = Number(settings["부가세율"]) || 0.1;
  const vat = Math.round(subtotal * vatRate);
  const total = subtotal + vat;

  row++; // 한 줄 띄우기
  quoteSheet.getRange(row, 4).setValue("소계").setFontWeight("bold");
  quoteSheet.getRange(row, 5).setValue(subtotal);
  row++;
  quoteSheet.getRange(row, 4).setValue(`부가세(${Math.round(vatRate * 100)}%)`).setFontWeight("bold");
  quoteSheet.getRange(row, 5).setValue(vat);
  row++;
  quoteSheet.getRange(row, 4).setValue("합계").setFontWeight("bold");
  quoteSheet.getRange(row, 5).setValue(total).setFontWeight("bold");

  quoteSheet.autoResizeColumns(1, 6);
  SpreadsheetApp.getUi().alert("견적서를 다시 생성했습니다. 합계: " + total.toLocaleString() + "원");
}

/**
 * "견적서" 시트만 PDF로 내보내 내 드라이브의 "견적서_PDF" 폴더에 저장한다.
 */
function saveQuoteAsPdf() {
  const ss = SpreadsheetApp.getActive();
  const quoteSheet = ss.getSheetByName(SHEET_QUOTE);
  if (!quoteSheet) throw new Error(`"${SHEET_QUOTE}" 시트를 찾을 수 없습니다.`);

  const url =
    `https://docs.google.com/spreadsheets/d/${ss.getId()}/export` +
    `?format=pdf&gid=${quoteSheet.getSheetId()}&size=A4&portrait=true&fitw=true&gridlines=false`;

  const token = ScriptApp.getOAuthToken();
  const response = UrlFetchApp.fetch(url, {
    headers: { Authorization: "Bearer " + token },
  });

  const folderName = "견적서_PDF";
  const folders = DriveApp.getFoldersByName(folderName);
  const folder = folders.hasNext() ? folders.next() : DriveApp.createFolder(folderName);

  const fileName = `견적서_${Utilities.formatDate(new Date(), "GMT+9", "yyyyMMdd_HHmm")}.pdf`;
  folder.createFile(response.getBlob().setName(fileName));

  SpreadsheetApp.getUi().alert(`"${folderName}" 폴더에 저장했습니다: ${fileName}`);
}

/**
 * 견적서를 PDF로 만들어 지정한 이메일로 바로 발송한다.
 * 실행하면 받는 사람 이메일을 입력하는 창이 뜬다.
 */
function emailQuote() {
  const ui = SpreadsheetApp.getUi();
  const result = ui.prompt("받는 사람 이메일을 입력하세요:");
  if (result.getSelectedButton() !== ui.Button.OK) return;
  const to = result.getResponseText().trim();
  if (!to) return;

  const ss = SpreadsheetApp.getActive();
  const quoteSheet = ss.getSheetByName(SHEET_QUOTE);
  const url =
    `https://docs.google.com/spreadsheets/d/${ss.getId()}/export` +
    `?format=pdf&gid=${quoteSheet.getSheetId()}&size=A4&portrait=true&fitw=true&gridlines=false`;
  const token = ScriptApp.getOAuthToken();
  const response = UrlFetchApp.fetch(url, { headers: { Authorization: "Bearer " + token } });

  const settings = getSettings_();
  GmailApp.sendEmail(to, `견적서 - ${settings["회사명"] || ""}`, "견적서를 첨부해 드립니다. 확인 부탁드립니다.", {
    attachments: [response.getBlob().setName("견적서.pdf")],
    name: settings["회사명"] || "",
  });

  SpreadsheetApp.getUi().alert(`${to} 로 견적서를 발송했습니다.`);
}
