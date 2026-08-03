/**
 * 거래명세서·발주서·견적서 통합 자동생성기 — Apps Script
 *
 * 설치 방법:
 * 1. 구글시트를 새로 만들고 "설정", "거래처마스터", "항목입력", "문서생성", "문서" 5개 시트를 만든다
 *    (정확한 칸 구조는 같은 폴더의 템플릿_구조.md 참고)
 * 2. 상단 메뉴 [확장 프로그램 > Apps Script]를 클릭
 * 3. 열린 편집기에 이 파일 내용을 전부 붙여넣고 저장 (Ctrl+S)
 * 4. 구글시트로 돌아오면 "문서 자동생성"이라는 메뉴가 새로 생긴다 (새로고침 필요할 수 있음)
 */

const SHEET_SETTINGS = "설정";
const SHEET_PARTNERS = "거래처마스터";
const SHEET_ITEMS = "항목입력";
const SHEET_CONTROL = "문서생성";
const SHEET_DOC = "문서";

const DOC_TITLES = { 견적서: "견 적 서", 거래명세서: "거 래 명 세 서", 발주서: "발 주 서" };

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu("문서 자동생성")
    .addItem("① 문서 생성/새로고침", "generateDocument")
    .addItem("② PDF로 저장 (내 드라이브)", "saveDocumentAsPdf")
    .addItem("③ 이메일로 보내기", "emailDocument")
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

function getPartners_() {
  const sheet = SpreadsheetApp.getActive().getSheetByName(SHEET_PARTNERS);
  if (!sheet) throw new Error(`"${SHEET_PARTNERS}" 시트를 찾을 수 없습니다.`);
  const lastRow = sheet.getLastRow();
  if (lastRow < 2) return [];
  const values = sheet.getRange(2, 1, lastRow - 1, 6).getValues();
  return values
    .filter((row) => row[0])
    .map((row) => ({
      name: row[0],
      bizNo: row[1],
      ceo: row[2],
      phone: row[3],
      address: row[4],
      email: row[5],
    }));
}

function findPartner_(name) {
  const partners = getPartners_();
  const found = partners.find((p) => p.name === name);
  if (!found) throw new Error(`거래처마스터 시트에서 "${name}"을(를) 찾을 수 없습니다.`);
  return found;
}

function getItems_() {
  const sheet = SpreadsheetApp.getActive().getSheetByName(SHEET_ITEMS);
  if (!sheet) throw new Error(`"${SHEET_ITEMS}" 시트를 찾을 수 없습니다.`);
  const lastRow = sheet.getLastRow();
  if (lastRow < 2) return [];
  const values = sheet.getRange(2, 1, lastRow - 1, 5).getValues();
  return values
    .filter((row) => row[0])
    .map((row) => ({
      name: row[0],
      spec: row[1],
      qty: Number(row[2]) || 0,
      price: Number(row[3]) || 0,
      note: row[4],
    }));
}

function getControl_() {
  const sheet = SpreadsheetApp.getActive().getSheetByName(SHEET_CONTROL);
  if (!sheet) throw new Error(`"${SHEET_CONTROL}" 시트를 찾을 수 없습니다.`);
  const data = sheet.getRange("A1:B4").getValues();
  return {
    partnerName: data[0][1],
    docType: data[1][1],
    deliveryDate: data[2][1],
    deliveryPlace: data[3][1],
  };
}

/**
 * "문서생성" 시트에서 고른 거래처·문서종류에 맞춰 "문서" 시트를 다시 그린다.
 */
function generateDocument() {
  const ss = SpreadsheetApp.getActive();
  const docSheet = ss.getSheetByName(SHEET_DOC);
  if (!docSheet) throw new Error(`"${SHEET_DOC}" 시트를 찾을 수 없습니다.`);

  const control = getControl_();
  if (!control.partnerName) {
    SpreadsheetApp.getUi().alert('"문서생성" 시트 B1에서 거래처를 먼저 선택해주세요.');
    return;
  }
  if (!DOC_TITLES[control.docType]) {
    SpreadsheetApp.getUi().alert('"문서생성" 시트 B2에서 문서종류(견적서/거래명세서/발주서)를 선택해주세요.');
    return;
  }

  const settings = getSettings_();
  const partner = findPartner_(control.partnerName);
  const items = getItems_();

  docSheet.clear();
  docSheet.getRange("A1").setValue(DOC_TITLES[control.docType]).setFontSize(20).setFontWeight("bold");
  docSheet.getRange("A3").setValue(`발행일: ${Utilities.formatDate(new Date(), "GMT+9", "yyyy-MM-dd")}`);

  const isPurchaseOrder = control.docType === "발주서";
  // 발주서는 우리 회사가 발주자(수신 거래처가 공급자), 견적서·거래명세서는 우리 회사가 공급자
  const sender = isPurchaseOrder
    ? { label: "발주자", name: settings["회사명"], bizNo: settings["사업자번호"], ceo: settings["대표자"], phone: settings["연락처"], address: settings["주소"] }
    : { label: "공급자", name: settings["회사명"], bizNo: settings["사업자번호"], ceo: settings["대표자"], phone: settings["연락처"], address: settings["주소"] };
  const receiver = isPurchaseOrder
    ? { label: "수신(공급처)", name: partner.name, bizNo: partner.bizNo, ceo: partner.ceo, phone: partner.phone, address: partner.address }
    : { label: "공급받는자", name: partner.name, bizNo: partner.bizNo, ceo: partner.ceo, phone: partner.phone, address: partner.address };

  docSheet.getRange("A4").setValue(`${receiver.label}: ${receiver.name} (${receiver.bizNo || ""})`);
  docSheet.getRange("A5").setValue(`${sender.label}: ${sender.name} (${sender.bizNo || ""})  대표자: ${sender.ceo || ""}  연락처: ${sender.phone || ""}`);
  docSheet.getRange("A6").setValue(`주소: ${sender.address || ""}`);

  let noteRow = 7;
  const messages = {
    견적서: "아래와 같이 견적합니다.",
    거래명세서: "아래와 같이 거래 내역을 통보합니다.",
    발주서: "아래와 같이 발주하오니 확인 후 납품하여 주시기 바랍니다.",
  };
  docSheet.getRange(`A${noteRow}`).setValue(messages[control.docType]);

  if (isPurchaseOrder) {
    noteRow++;
    const deliveryDateText = control.deliveryDate
      ? control.deliveryDate instanceof Date
        ? Utilities.formatDate(control.deliveryDate, "GMT+9", "yyyy-MM-dd")
        : control.deliveryDate
      : "";
    docSheet.getRange(`A${noteRow}`).setValue(`납품희망일: ${deliveryDateText}   납품장소: ${control.deliveryPlace || ""}`);
  }

  const headerRow = noteRow + 2;
  const headers = ["품목", "규격", "수량", "단가", "금액", "비고"];
  docSheet.getRange(headerRow, 1, 1, headers.length).setValues([headers]).setFontWeight("bold");

  let row = headerRow + 1;
  let subtotal = 0;
  items.forEach((item) => {
    const amount = item.qty * item.price;
    subtotal += amount;
    docSheet.getRange(row, 1, 1, 6).setValues([[item.name, item.spec, item.qty, item.price, amount, item.note]]);
    row++;
  });

  const vatRate = Number(settings["부가세율"]) || 0.1;
  const vat = Math.round(subtotal * vatRate);
  const total = subtotal + vat;

  row++;
  docSheet.getRange(row, 4).setValue("소계").setFontWeight("bold");
  docSheet.getRange(row, 5).setValue(subtotal);
  row++;
  docSheet.getRange(row, 4).setValue(`부가세(${Math.round(vatRate * 100)}%)`).setFontWeight("bold");
  docSheet.getRange(row, 5).setValue(vat);
  row++;
  docSheet.getRange(row, 4).setValue("합계").setFontWeight("bold");
  docSheet.getRange(row, 5).setValue(total).setFontWeight("bold");

  docSheet.autoResizeColumns(1, 6);
  SpreadsheetApp.getUi().alert(`${control.docType}를 생성했습니다. 합계: ${total.toLocaleString()}원`);
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
 * 현재 "문서" 시트 내용을 PDF로 저장한다.
 */
function saveDocumentAsPdf() {
  const ss = SpreadsheetApp.getActive();
  const docSheet = ss.getSheetByName(SHEET_DOC);
  if (!docSheet) throw new Error(`"${SHEET_DOC}" 시트를 찾을 수 없습니다.`);

  const control = getControl_();
  const blob = exportSheetAsPdfBlob_(ss, docSheet);

  const folderName = "거래문서_PDF";
  const folders = DriveApp.getFoldersByName(folderName);
  const folder = folders.hasNext() ? folders.next() : DriveApp.createFolder(folderName);

  const fileName = `${control.docType}_${control.partnerName}_${Utilities.formatDate(new Date(), "GMT+9", "yyyyMMdd_HHmm")}.pdf`;
  folder.createFile(blob.setName(fileName));

  SpreadsheetApp.getUi().alert(`"${folderName}" 폴더에 저장했습니다: ${fileName}`);
}

/**
 * 현재 문서를 이메일로 발송한다. 거래처마스터에 이메일이 있으면 자동으로 채워서 확인창을 띄운다.
 */
function emailDocument() {
  const ss = SpreadsheetApp.getActive();
  const docSheet = ss.getSheetByName(SHEET_DOC);
  if (!docSheet) throw new Error(`"${SHEET_DOC}" 시트를 찾을 수 없습니다.`);

  const control = getControl_();
  if (!control.partnerName) {
    SpreadsheetApp.getUi().alert("먼저 문서를 생성해주세요.");
    return;
  }
  const partner = findPartner_(control.partnerName);

  const ui = SpreadsheetApp.getUi();
  const result = ui.prompt(`${partner.name}에게 보낼 이메일 주소를 확인/입력하세요:`, partner.email || "", ui.ButtonSet.OK_CANCEL);
  if (result.getSelectedButton() !== ui.Button.OK) return;
  const to = result.getResponseText().trim();
  if (!to) return;

  const settings = getSettings_();
  const blob = exportSheetAsPdfBlob_(ss, docSheet);
  GmailApp.sendEmail(to, `${settings["회사명"] || ""} ${control.docType} - ${partner.name}`, `${control.docType}를 첨부해 드립니다. 확인 부탁드립니다.`, {
    attachments: [blob.setName(`${control.docType}.pdf`)],
    name: settings["회사명"] || "",
  });

  SpreadsheetApp.getUi().alert(`${to} 로 발송했습니다.`);
}
