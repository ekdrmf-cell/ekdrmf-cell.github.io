/**
 * 천지인운명관 신청서 → 이메일 발송 (Google Apps Script Web App)
 *
 * 이 스크립트는 site-checkout 서버가 아니라 사장님(ekdrmf@gmail.com) 본인의 구글
 * 계정에 배포됩니다 — 낯선 제3자 회사를 거치지 않고, 사장님 계정이 직접 메일을
 * 보내는 구조입니다(2026-08-23, "왜 제3자 업체를 거치는건데? 내 이메일과 연동시키면
 * 되는거 아닌가?" 요청에 따라 FormSubmit 대신 이 방식으로 결정).
 *
 * 배포 방법은 대화창에서 안내받은 순서를 따르세요(script.google.com → 이 코드
 * 붙여넣기 → 웹앱으로 배포 → 발급된 URL을 crossnotics/index.html의
 * CN_MAIL_ENDPOINT에 붙여넣기).
 */

// 신청 메일을 받을 주소 — SITE_CONFIG.contactEmail(js/config.js)과 동일하게 유지할 것.
var RECEIVE_EMAIL = "ekdrmf@gmail.com";

function doPost(e) {
  try {
    var data = JSON.parse(e.postData.contents);
    var subject = data.subject || "천지인운명관 신청";
    var body = data.body || "";

    var options = {};
    // 손님 이메일을 회신 주소로 넣어두면, 운영자가 이 메일에 "답장"만 눌러도
    // 바로 손님에게 리포트를 보낼 수 있다.
    if (data.replyTo) {
      options.replyTo = data.replyTo;
    }

    MailApp.sendEmail(RECEIVE_EMAIL, subject, body, options);

    return ContentService.createTextOutput(JSON.stringify({ success: true }))
      .setMimeType(ContentService.MimeType.JSON);
  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({ success: false, error: String(err) }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}
