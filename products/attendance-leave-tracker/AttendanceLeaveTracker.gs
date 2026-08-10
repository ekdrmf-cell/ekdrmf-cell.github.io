/**
 * 근태관리 + 연차 자동집계 시트 — Apps Script
 *
 * 이 스크립트는 노무 자문이 아니며, 근로기준법 표준 공식(80% 이상 출근 가정)에 따른
 * 참고치를 계산해줍니다. 정확한 연차·수당 산정은 노무사와 상담하세요.
 *
 * 설치 방법:
 * 1. 구글시트를 새로 만들고 "설정", "직원정보", "근태기록", "집계월선택", "근태현황" 5개 시트를 만든다
 *    (정확한 칸 구조는 같은 폴더의 템플릿_구조.md 참고)
 * 2. 상단 메뉴 [확장 프로그램 > Apps Script]를 클릭
 * 3. 열린 편집기에 이 파일 내용을 전부 붙여넣고 저장 (Ctrl+S)
 * 4. 구글시트로 돌아오면 "근태·연차 자동관리"라는 메뉴가 새로 생긴다 (새로고침 필요할 수 있음)
 */

const SHEET_SETTINGS = "설정";
const SHEET_STAFF = "직원정보";
const SHEET_RECORDS = "근태기록";
const SHEET_MONTH = "집계월선택";
const SHEET_STATUS = "근태현황";

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu("근태·연차 자동관리")
    .addItem("① 근태현황 생성/새로고침", "generateAttendanceStatus")
    .addItem("② 근태현황 PDF로 저장", "saveStatusAsPdf")
    .addSeparator()
    .addItem("③ 관리자에게 요약 이메일 발송", "emailAdminSummary")
    .addItem("④ 직원별 근태확인서 개별 이메일 발송", "emailStaffIndividually")
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
  const values = sheet.getRange(2, 1, lastRow - 1, 3).getValues();
  return values
    .filter((row) => row[0])
    .map((row) => ({ name: row[0], joinDate: row[1], email: row[2] }));
}

function getRecords_() {
  const sheet = SpreadsheetApp.getActive().getSheetByName(SHEET_RECORDS);
  if (!sheet) throw new Error(`"${SHEET_RECORDS}" 시트를 찾을 수 없습니다.`);
  const lastRow = sheet.getLastRow();
  if (lastRow < 2) return [];
  const values = sheet.getRange(2, 1, lastRow - 1, 5).getValues();
  return values
    .filter((row) => row[0] && row[1])
    .map((row) => ({
      date: row[0],
      name: row[1],
      clockIn: String(row[2] || "").trim(),
      clockOut: String(row[3] || "").trim(),
      note: String(row[4] || "").trim(),
    }));
}

function getTargetMonth_() {
  const sheet = SpreadsheetApp.getActive().getSheetByName(SHEET_MONTH);
  if (!sheet) throw new Error(`"${SHEET_MONTH}" 시트를 찾을 수 없습니다.`);
  const value = String(sheet.getRange("B1").getValue()).trim();
  const parts = value.split("-");
  if (parts.length !== 2) throw new Error('"집계월선택" 시트 B1을 YYYY-MM 형식으로 입력해주세요.');
  return { year: Number(parts[0]), month: Number(parts[1]) }; // month: 1~12
}

function toMinutes_(hhmm) {
  if (!hhmm) return null;
  const parts = hhmm.split(":");
  if (parts.length !== 2) return null;
  const h = Number(parts[0]);
  const m = Number(parts[1]);
  if (isNaN(h) || isNaN(m)) return null;
  return h * 60 + m;
}

function isApprovedAbsence_(note) {
  const keywords = ["연차", "공가", "경조사", "반차", "병가", "휴가"];
  return keywords.some((k) => note.indexOf(k) !== -1);
}

/**
 * 근로기준법 제60조 기준 연차 발생일수를 계산한다(참고치, 80% 이상 출근 가정).
 * asOfDate 시점까지의 근속 기간을 기준으로 계산한다.
 */
function calcAnnualLeaveEntitlement_(joinDate, asOfDate) {
  if (!(joinDate instanceof Date)) return 0;
  let months = (asOfDate.getFullYear() - joinDate.getFullYear()) * 12 + (asOfDate.getMonth() - joinDate.getMonth());
  if (asOfDate.getDate() < joinDate.getDate()) months--;
  if (months < 0) return 0;

  const years = Math.floor(months / 12);
  if (years < 1) {
    return Math.min(months, 11);
  }
  const entitlement = 15 + Math.floor((years - 1) / 2);
  return Math.min(entitlement, 25);
}

/**
 * 선택한 달의 근태를 집계하고, 연차는 그 달 말일 기준 누적치로 계산한다.
 */
function calcAttendance_() {
  const settings = getSettings_();
  const isEligible = String(settings["상시근로자5인이상"] || "").trim() === "예";
  const scheduledStart = toMinutes_(String(settings["소정근로시작"] || "09:00"));
  const scheduledEnd = toMinutes_(String(settings["소정근로종료"] || "18:00"));
  const scheduledHours = Number(settings["소정근로시간"]) || 8;
  const lateGraceMin = Number(settings["지각허용분"]) || 0;
  const hourlyWage = Number(settings["통상시급"]) || 0;

  const target = getTargetMonth_();
  const staffList = getStaffList_();
  const records = getRecords_();
  const monthEnd = new Date(target.year, target.month, 0); // 그 달의 마지막 날

  return staffList.map((s) => {
    const myRecords = records.filter((r) => r.name === s.name);
    const monthRecords = myRecords.filter(
      (r) => r.date instanceof Date && r.date.getFullYear() === target.year && r.date.getMonth() + 1 === target.month
    );

    let workDays = 0,
      lateCount = 0,
      earlyLeaveCount = 0,
      absentDays = 0,
      overtimeMinutes = 0,
      leaveUsedThisMonth = 0;

    monthRecords.forEach((r) => {
      const inMin = toMinutes_(r.clockIn);
      const outMin = toMinutes_(r.clockOut);

      if (inMin === null && outMin === null) {
        if (isApprovedAbsence_(r.note)) {
          if (r.note.indexOf("연차") !== -1) leaveUsedThisMonth++;
        } else {
          absentDays++;
        }
        return;
      }

      workDays++;
      if (inMin !== null && scheduledStart !== null && inMin > scheduledStart + lateGraceMin) lateCount++;
      if (outMin !== null && scheduledEnd !== null && outMin < scheduledEnd) earlyLeaveCount++;
      if (inMin !== null && outMin !== null && outMin > inMin) {
        const workedMinutes = outMin - inMin;
        const overMinutes = workedMinutes - scheduledHours * 60;
        if (overMinutes > 0) overtimeMinutes += overMinutes;
      }
    });

    // 연차 사용일수(누적, 이번 달 말일까지)
    const leaveUsedTotal = myRecords.filter(
      (r) => r.date instanceof Date && r.date <= monthEnd && r.note.indexOf("연차") !== -1
    ).length;

    const overtimeHours = Math.round((overtimeMinutes / 60) * 10) / 10;
    const overtimePay = isEligible ? Math.round(overtimeHours * hourlyWage * 1.5) : null;
    const leaveEntitlement = isEligible ? calcAnnualLeaveEntitlement_(s.joinDate, monthEnd) : null;
    const leaveRemaining = isEligible ? leaveEntitlement - leaveUsedTotal : null;

    return {
      name: s.name,
      workDays,
      lateCount,
      earlyLeaveCount,
      absentDays,
      overtimeHours,
      overtimePay,
      leaveEntitlement,
      leaveUsedTotal,
      leaveRemaining,
    };
  });
}

function generateAttendanceStatus() {
  const ss = SpreadsheetApp.getActive();
  const statusSheet = ss.getSheetByName(SHEET_STATUS);
  if (!statusSheet) throw new Error(`"${SHEET_STATUS}" 시트를 찾을 수 없습니다.`);

  const settings = getSettings_();
  const isEligible = String(settings["상시근로자5인이상"] || "").trim() === "예";
  const target = getTargetMonth_();
  const list = calcAttendance_();

  statusSheet.clear();
  let row = 1;
  statusSheet.getRange(row, 1).setValue("근 태 · 연 차 현 황").setFontSize(18).setFontWeight("bold");
  row++;
  statusSheet.getRange(row, 1).setValue(`${settings["회사명"] || ""} · 집계월: ${target.year}년 ${target.month}월`);
  row += 2;

  const headers = ["성명", "근무일수", "지각", "조퇴", "결근", "초과근무(시간)", "예상수당", "연차발생", "연차사용(누적)", "연차잔여"];
  statusSheet.getRange(row, 1, 1, headers.length).setValues([headers]).setFontWeight("bold");
  const headerRow = row;
  row++;

  list.forEach((s) => {
    statusSheet
      .getRange(row, 1, 1, headers.length)
      .setValues([[
        s.name,
        s.workDays,
        s.lateCount,
        s.earlyLeaveCount,
        s.absentDays,
        s.overtimeHours,
        isEligible ? s.overtimePay.toLocaleString() + "원" : "해당없음",
        isEligible ? s.leaveEntitlement : "해당없음",
        isEligible ? s.leaveUsedTotal : "해당없음",
        isEligible ? s.leaveRemaining : "해당없음",
      ]]);
    if (s.absentDays > 0 || s.lateCount >= 3) {
      statusSheet.getRange(row, 1, 1, headers.length).setBackground("#f4cccc");
    }
    row++;
  });

  row++;
  if (!isEligible) {
    statusSheet
      .getRange(row, 1)
      .setValue("※ 상시근로자 5인 미만 사업장으로 설정되어 있어 연차·초과근무수당은 계산하지 않았습니다(근로기준법 적용 제외).")
      .setFontColor("#666666");
    row++;
  }
  statusSheet
    .getRange(row, 1)
    .setValue("※ 연차 발생일수는 80% 이상 출근을 가정한 참고치이며, 초과근무수당은 연장근로 가산(50%)만 반영한 예상치입니다. 정확한 산정은 노무사와 상담하세요.")
    .setFontStyle("italic")
    .setFontColor("#666666");

  statusSheet.setColumnWidths(1, headers.length, 110);
  statusSheet.getRange(headerRow, 1, row - headerRow + 1, headers.length).setWrap(true);

  SpreadsheetApp.getUi().alert(`${target.year}년 ${target.month}월 근태현황을 생성했습니다.`);
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
  const target = getTargetMonth_();

  const blob = exportSheetAsPdfBlob_(ss, statusSheet);
  const folderName = "근태현황_PDF";
  const folders = DriveApp.getFoldersByName(folderName);
  const folder = folders.hasNext() ? folders.next() : DriveApp.createFolder(folderName);

  const fileName = `근태현황_${target.year}${("0" + target.month).slice(-2)}.pdf`;
  folder.createFile(blob.setName(fileName));

  SpreadsheetApp.getUi().alert(`"${folderName}" 폴더에 저장했습니다: ${fileName}`);
}

function emailAdminSummary() {
  const ss = SpreadsheetApp.getActive();
  const statusSheet = ss.getSheetByName(SHEET_STATUS);
  const settings = getSettings_();
  const to = settings["알림받을이메일"];
  const target = getTargetMonth_();

  generateAttendanceStatus();
  const list = calcAttendance_();
  const flagged = list.filter((s) => s.absentDays > 0 || s.lateCount >= 3);

  if (!to) {
    SpreadsheetApp.getUi().alert('"설정" 시트의 알림받을이메일 칸이 비어있어 발송하지 못했습니다.');
    return;
  }

  const lines = flagged.map((s) => `- ${s.name}: 지각 ${s.lateCount}회, 결근 ${s.absentDays}일`);
  const body =
    (flagged.length > 0
      ? `${target.year}년 ${target.month}월 근태 확인이 필요한 직원이 ${flagged.length}명 있습니다.\n\n` + lines.join("\n")
      : `${target.year}년 ${target.month}월 근태 특이사항이 없습니다.`) +
    "\n\n전체 근태현황은 첨부 PDF를 확인하세요.";
  const blob = exportSheetAsPdfBlob_(ss, statusSheet);

  GmailApp.sendEmail(to, `[근태알림] ${settings["회사명"] || ""} ${target.year}년 ${target.month}월 근태현황`, body, {
    attachments: [blob.setName("근태현황.pdf")],
    name: settings["회사명"] || "",
  });

  SpreadsheetApp.getUi().alert(`${to} 로 요약 알림을 보냈습니다.`);
}

function emailStaffIndividually() {
  const ui = SpreadsheetApp.getUi();
  const confirm = ui.alert(
    "직원 개별 발송",
    "이메일이 등록된 직원 각자에게 이번달 근태·연차 확인서를 보냅니다. 계속할까요?",
    ui.ButtonSet.YES_NO
  );
  if (confirm !== ui.Button.YES) return;

  const settings = getSettings_();
  const isEligible = String(settings["상시근로자5인이상"] || "").trim() === "예";
  const target = getTargetMonth_();
  const staffList = getStaffList_();
  const list = calcAttendance_();

  let sent = 0;
  list.forEach((s) => {
    const staff = staffList.find((st) => st.name === s.name);
    if (!staff || !staff.email) return;

    const leaveText = isEligible ? `연차 발생 ${s.leaveEntitlement}일, 사용(누적) ${s.leaveUsedTotal}일, 잔여 ${s.leaveRemaining}일` : "연차 규정 적용 대상 아님";
    const message = `${s.name}님,\n\n${target.year}년 ${target.month}월 근태 확인서입니다.\n- 근무일수: ${s.workDays}일\n- 지각: ${s.lateCount}회 / 조퇴: ${s.earlyLeaveCount}회 / 결근: ${s.absentDays}일\n- 초과근무: ${s.overtimeHours}시간\n- ${leaveText}\n\n확인 후 다른 내용이 있으면 담당자에게 알려주세요.\n\n${settings["회사명"] || ""} 드림`;

    GmailApp.sendEmail(staff.email, `[${settings["회사명"] || ""}] ${target.year}년 ${target.month}월 근태·연차 확인서`, message, {
      name: settings["회사명"] || "",
    });
    sent++;
  });

  ui.alert(`${sent}명에게 근태 확인서를 보냈습니다.`);
}
