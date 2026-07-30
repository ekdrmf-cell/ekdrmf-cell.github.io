/*
 * 사이트 전역 설정 — 연락처가 바뀌면 이 파일 한 곳만 고치면
 * 모든 페이지의 문의 버튼에 반영됩니다.
 *
 * TODO(사용자): 지금은 개인 이메일이 임시로 연결되어 있습니다.
 * 사이트를 공개하기 전에 전용 문의 채널(카카오톡 채널, 사업용 이메일 등)로 교체하세요.
 */
const SITE_CONFIG = {
  contactEmail: "ekdrmf@gmail.com",
};

function contactMail(subject, body) {
  const s = encodeURIComponent(subject);
  const b = encodeURIComponent(body || "");
  window.location.href = `mailto:${SITE_CONFIG.contactEmail}?subject=${s}&body=${b}`;
}
