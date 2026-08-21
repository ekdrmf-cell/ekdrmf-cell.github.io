/*
 * 이메일 자동발송 — 유료 이메일 API(SendGrid 등) 대신 기존에 쓰던 Gmail 계정(ekdrmf@gmail.com)을
 * SMTP로 그대로 재사용한다(완전 무료, 신규 가입 불필요). tools/gmail-auto-reply/AutoReply.gs가
 * 같은 계정으로 "초안까지만 만들고 사람이 발송"했다면, 여기서는 결제가 이미 확인된 뒤라
 * 자동 발송까지 한다 — "결제 확인 없이 무료로 새 나가는 것"을 막는다는 기존 정책의 목적은
 * 이미 웹훅이 결제완료를 검증한 시점에서 충족됨.
 *
 * 필요 환경변수: GMAIL_USER(ekdrmf@gmail.com), GMAIL_APP_PASSWORD(Google 계정 설정 →
 * 보안 → 2단계 인증 → 앱 비밀번호에서 무료로 발급, 일반 로그인 비밀번호와 다름).
 */
const nodemailer = require("nodemailer");

function buildTransport() {
  const user = process.env.GMAIL_USER;
  const pass = process.env.GMAIL_APP_PASSWORD;
  if (!user || !pass) {
    throw new Error("GMAIL_USER / GMAIL_APP_PASSWORD 환경변수가 설정되지 않음");
  }
  return nodemailer.createTransport({ service: "gmail", auth: { user, pass } });
}

/**
 * @param {object} params {to, subject, text, attachments: [{filename, path?|content}]}
 */
async function sendDeliveryEmail({ to, subject, text, attachments }) {
  const transporter = buildTransport();
  const info = await transporter.sendMail({
    from: `"서비스허브" <${process.env.GMAIL_USER}>`,
    to,
    subject,
    text,
    attachments,
  });
  return { messageId: info.messageId };
}

module.exports = { sendDeliveryEmail };
