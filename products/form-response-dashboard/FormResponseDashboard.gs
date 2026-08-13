/**
 * 구글폼 응답 자동집계 + 조건부 알림 대시보드 — Apps Script
 *
 * 설치 방법:
 * 1. 구글폼과 이미 연결된 응답 스프레드시트를 연다 (폼 편집 화면의 "응답" 탭에서
 *    스프레드시트 아이콘을 누르면 생성/이동된다).
 * 2. "설정", "문항설정" 2개 시트를 만든다 ("집계결과", "알림이력"은 자동 생성됨,
 *    정확한 칸 구조는 같은 폴더의 템플릿_구조.md 참고).
 * 3. 상단 메뉴 [확장 프로그램 > Apps Script]를 클릭.
 * 4. 열린 편집기에 이 파일 내용을 전부 붙여넣고 저장 (Ctrl+S).
 * 5. 구글시트로 돌아오면 "응답 대시보드" 메뉴가 새로 생긴다 (새로고침 필요할 수 있음).
 */

const SHEET_SETTINGS = "설정";
const SHEET_QUESTIONS = "문항설정";
const SHEET_SUMMARY = "집계결과";
const SHEET_ALERT_LOG = "알림이력";

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu("응답 대시보드")
    .addItem("① 응답 집계 새로고침", "refreshAggregation")
    .addItem("② 새 응답 위험 검사 + 알림", "checkNewResponsesAndAlert")
    .addSeparator()
    .addItem("③ 집계 대시보드 PDF로 저장", "saveAggregationAsPdf")
    .addItem("④ 집계 요약 이메일로 보내기", "emailSummary")
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

function saveSetting_(key, value) {
  const sheet = SpreadsheetApp.getActive().getSheetByName(SHEET_SETTINGS);
  const lastRow = sheet.getLastRow();
  const keys = sheet.getRange(1, 1, lastRow, 1).getValues();
  for (let i = 0; i < keys.length; i++) {
    if (keys[i][0] === key) {
      sheet.getRange(i + 1, 2).setValue(value);
      return;
    }
  }
  sheet.appendRow([key, value]);
}

function getQuestionConfigs_() {
  const sheet = SpreadsheetApp.getActive().getSheetByName(SHEET_QUESTIONS);
  if (!sheet) throw new Error(`"${SHEET_QUESTIONS}" 시트를 찾을 수 없습니다.`);
  const lastRow = sheet.getLastRow();
  if (lastRow < 2) return [];
  const values = sheet.getRange(2, 1, lastRow - 1, 3).getValues();
  return values
    .filter((row) => row[0])
    .map((row) => ({
      column: String(row[0]).trim(),
      type: String(row[1] || "").trim(),
      riskDetect: String(row[2] || "").trim().toUpperCase() === "Y",
    }));
}

function getResponseSheet_(settings) {
  const name = settings["응답시트이름"];
  if (!name) throw new Error('"설정" 시트의 응답시트이름 칸이 비어있습니다.');
  const sheet = SpreadsheetApp.getActive().getSheetByName(name);
  if (!sheet) throw new Error(`"${name}" 시트를 찾을 수 없습니다. 설정 시트의 응답시트이름을 확인해주세요.`);
  return sheet;
}

/**
 * 응답 시트의 헤더(1행)와 문항설정을 매칭해 각 열의 인덱스를 구한다.
 */
function mapColumns_(responseSheet, questionConfigs) {
  const lastCol = responseSheet.getLastColumn();
  const headers = responseSheet.getRange(1, 1, 1, lastCol).getValues()[0];
  return questionConfigs
    .map((q) => ({ ...q, colIndex: headers.indexOf(q.column) }))
    .filter((q) => q.colIndex !== -1);
}

/**
 * 문항별로 선택형은 옵션별 응답수, 척도형은 평균/최고/최저/분포, 주관식은 응답수만 집계해
 * "집계결과" 시트에 표로 정리한다. 실행할 때마다 시트를 새로 만들어 최신 내용으로 덮어쓴다.
 */
function refreshAggregation() {
  const ss = SpreadsheetApp.getActive();
  const settings = getSettings_();
  const responseSheet = getResponseSheet_(settings);
  const configs = getQuestionConfigs_().filter((q) => q.type !== "제외");
  const mapped = mapColumns_(responseSheet, configs);

  const lastRow = responseSheet.getLastRow();
  const totalResponses = Math.max(0, lastRow - 1);

  let summarySheet = ss.getSheetByName(SHEET_SUMMARY);
  if (summarySheet) summarySheet.clear();
  else summarySheet = ss.insertSheet(SHEET_SUMMARY);

  const rows = [
    ["응답 집계 대시보드", "", ""],
    [`총 응답수: ${totalResponses}건`, `업데이트: ${Utilities.formatDate(new Date(), "GMT+9", "yyyy-MM-dd HH:mm")}`, ""],
    ["", "", ""],
  ];

  mapped.forEach((q) => {
    if (totalResponses === 0) return;
    const values = responseSheet.getRange(2, q.colIndex + 1, totalResponses, 1).getValues().map((r) => r[0]);

    rows.push([`[${q.type}] ${q.column}`, "", ""]);

    if (q.type === "척도형") {
      const nums = values.map(Number).filter((n) => !isNaN(n));
      if (nums.length === 0) {
        rows.push(["응답 없음", "", ""]);
      } else {
        const avg = nums.reduce((a, b) => a + b, 0) / nums.length;
        const max = Math.max(...nums);
        const min = Math.min(...nums);
        rows.push([`평균 ${avg.toFixed(2)}점`, `최고 ${max}점`, `최저 ${min}점 (응답 ${nums.length}건)`]);
        const dist = {};
        nums.forEach((n) => (dist[n] = (dist[n] || 0) + 1));
        Object.keys(dist).sort().forEach((score) => {
          const count = dist[score];
          const bar = "■".repeat(Math.max(1, Math.round((count / nums.length) * 20)));
          rows.push([`${score}점`, `${count}건`, bar]);
        });
      }
    } else if (q.type === "선택형") {
      const dist = {};
      values.forEach((v) => {
        String(v).split(",").map((s) => s.trim()).filter(Boolean).forEach((opt) => {
          dist[opt] = (dist[opt] || 0) + 1;
        });
      });
      const keys = Object.keys(dist).sort((a, b) => dist[b] - dist[a]);
      if (keys.length === 0) rows.push(["응답 없음", "", ""]);
      keys.forEach((opt) => {
        const count = dist[opt];
        const bar = "■".repeat(Math.max(1, Math.round((count / values.length) * 20)));
        rows.push([opt, `${count}건`, bar]);
      });
    } else {
      const answered = values.filter((v) => String(v).trim() !== "").length;
      rows.push([`응답 ${answered}건 (내용은 응답 시트에서 직접 확인)`, "", ""]);
    }
    rows.push(["", "", ""]);
  });

  if (rows.length > 0) {
    summarySheet.getRange(1, 1, rows.length, 3).setValues(rows);
    summarySheet.getRange(1, 1, 1, 3).merge().setFontWeight("bold").setFontSize(14);
    summarySheet.setColumnWidths(1, 3, 220);
  }

  SpreadsheetApp.getUi().alert(`집계를 새로고침했습니다 (총 ${totalResponses}건).`);
}

/**
 * "마지막처리행" 이후의 새 응답만 훑어서, 위험감지 대상 문항 중 하나라도 기준에
 * 걸리면 즉시 관리자에게 알림 이메일을 보내고 "알림이력"에 기록한다.
 */
function checkNewResponsesAndAlert() {
  const ss = SpreadsheetApp.getActive();
  const settings = getSettings_();
  const responseSheet = getResponseSheet_(settings);
  const configs = getQuestionConfigs_();
  const mapped = mapColumns_(responseSheet, configs);
  const riskKeywords = String(settings["위험키워드"] || "")
    .split(",")
    .map((k) => k.trim())
    .filter(Boolean);
  const riskThreshold = Number(settings["위험점수기준"]);

  const lastRow = responseSheet.getLastRow();
  const lastCol = responseSheet.getLastColumn();
  const headers = responseSheet.getRange(1, 1, 1, lastCol).getValues()[0];
  let lastProcessed = Number(settings["마지막처리행"]) || 1;
  if (lastProcessed < 1) lastProcessed = 1;

  if (lastRow <= lastProcessed) {
    SpreadsheetApp.getUi().alert("새 응답이 없습니다.");
    return;
  }

  let logSheet = ss.getSheetByName(SHEET_ALERT_LOG);
  if (!logSheet) {
    logSheet = ss.insertSheet(SHEET_ALERT_LOG);
    logSheet.appendRow(["시간", "응답행번호", "감지사유", "응답요약"]);
  }

  const to = settings["관리자이메일"];
  let alertCount = 0;

  for (let r = lastProcessed + 1; r <= lastRow; r++) {
    const rowValues = responseSheet.getRange(r, 1, 1, lastCol).getValues()[0];
    const reasons = [];

    mapped
      .filter((q) => q.riskDetect)
      .forEach((q) => {
        const cell = rowValues[q.colIndex];
        if (q.type === "척도형") {
          const num = Number(cell);
          if (!isNaN(num) && !isNaN(riskThreshold) && num <= riskThreshold) {
            reasons.push(`"${q.column}" 점수 ${num}점 (기준 ${riskThreshold}점 이하)`);
          }
        } else if (q.type === "주관식") {
          const text = String(cell || "");
          const hit = riskKeywords.find((k) => text.indexOf(k) !== -1);
          if (hit) reasons.push(`"${q.column}"에 위험 키워드 "${hit}" 포함`);
        }
      });

    if (reasons.length > 0) {
      alertCount++;
      const summary = headers.map((h, i) => `${h}: ${rowValues[i]}`).join(" / ");
      logSheet.appendRow([new Date(), r, reasons.join("; "), summary]);

      if (to) {
        GmailApp.sendEmail(
          to,
          `[응답 위험 감지] ${settings["사업체명"] || ""} - ${reasons[0]}`,
          `새 응답에서 위험 신호가 감지됐습니다.\n\n감지 사유: ${reasons.join("; ")}\n\n응답 내용:\n${summary}`,
          { name: settings["사업체명"] || "" }
        );
      }
    }
  }

  saveSetting_("마지막처리행", lastRow);
  SpreadsheetApp.getUi().alert(
    alertCount > 0
      ? `새 응답 ${lastRow - lastProcessed}건 확인, ${alertCount}건에서 위험 신호를 감지해 알림을 보냈습니다.`
      : `새 응답 ${lastRow - lastProcessed}건을 확인했지만 위험 신호는 없었습니다.`
  );
}

function exportSheetAsPdfBlob_(ss, sheet) {
  const url =
    `https://docs.google.com/spreadsheets/d/${ss.getId()}/export` +
    `?format=pdf&gid=${sheet.getSheetId()}&size=A4&portrait=true&fitw=true&gridlines=false`;
  const token = ScriptApp.getOAuthToken();
  const response = UrlFetchApp.fetch(url, { headers: { Authorization: "Bearer " + token } });
  return response.getBlob();
}

function saveAggregationAsPdf() {
  const ss = SpreadsheetApp.getActive();
  const summarySheet = ss.getSheetByName(SHEET_SUMMARY);
  if (!summarySheet) {
    SpreadsheetApp.getUi().alert('먼저 "① 응답 집계 새로고침"을 실행해주세요.');
    return;
  }

  const blob = exportSheetAsPdfBlob_(ss, summarySheet);
  const folderName = "응답집계_PDF";
  const folders = DriveApp.getFoldersByName(folderName);
  const folder = folders.hasNext() ? folders.next() : DriveApp.createFolder(folderName);

  const fileName = `응답집계_${Utilities.formatDate(new Date(), "GMT+9", "yyyyMMdd")}.pdf`;
  folder.createFile(blob.setName(fileName));

  SpreadsheetApp.getUi().alert(`"${folderName}" 폴더에 저장했습니다: ${fileName}`);
}

function emailSummary() {
  const ss = SpreadsheetApp.getActive();
  const summarySheet = ss.getSheetByName(SHEET_SUMMARY);
  const settings = getSettings_();
  const to = settings["관리자이메일"];
  if (!summarySheet) {
    SpreadsheetApp.getUi().alert('먼저 "① 응답 집계 새로고침"을 실행해주세요.');
    return;
  }
  if (!to) {
    SpreadsheetApp.getUi().alert('"설정" 시트의 관리자이메일 칸이 비어있어 발송하지 못했습니다.');
    return;
  }

  const blob = exportSheetAsPdfBlob_(ss, summarySheet);
  const todayStr = Utilities.formatDate(new Date(), "GMT+9", "yyyy-MM-dd");
  GmailApp.sendEmail(to, `[응답 집계 요약] ${settings["사업체명"] || ""} ${todayStr}`, "최신 응답 집계 대시보드를 첨부해 드립니다.", {
    attachments: [blob.setName("응답집계.pdf")],
    name: settings["사업체명"] || "",
  });

  SpreadsheetApp.getUi().alert(`${to} 로 발송했습니다.`);
}
