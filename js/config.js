/*
 * 사이트 전역 설정 — 여기 값만 바꾸면 모든 페이지(문의 버튼ㆍ광고ㆍ결제 안내)에 반영됩니다.
 *
 * TODO(사용자): 지금은 개인 이메일이 임시로 연결되어 있습니다.
 * 사이트를 공개하기 전에 전용 문의 채널(카카오톡 채널, 사업용 이메일 등)로 교체하세요.
 */
const SITE_CONFIG = {
  contactEmail: "ekdrmf@gmail.com",

  // TODO(사용자): 애드센스에서 수익화허브 도메인을 추가하면 발급되는
  // "ca-pub-여러자리숫자" 형태의 퍼블리셔 ID를 여기 넣으세요.
  // 비워두면(빈 문자열) 광고 스크립트가 아예 로드되지 않습니다.
  adsensePublisherId: "ca-pub-9038430968074722",

  // TODO(사용자): 토스ㆍ카카오페이 개인 송금 링크(예: https://toss.me/아이디)
  // 또는 계좌번호 안내 문구를 넣으세요. 비워두면 지금처럼 이메일 문의로만 안내됩니다.
  paymentLink: "",
  paymentGuideText: "",

  // TODO(사용자, 선택): 애드센스 사이트에서 "광고 단위"를 따로 만들면
  // "숫자로 된 광고 단위 ID"가 나옵니다. 게임 리워드/전면 광고 자리에 넣고 싶으면
  // 여기 채우세요. 비워두면 광고 자리 없이 지금과 같은 대기 화면만 보여줍니다.
  rewardAdSlot: "",
  interstitialAdSlot: "",
};

function contactMail(subject, body) {
  const s = encodeURIComponent(subject);
  const b = encodeURIComponent(body || "");
  window.location.href = `mailto:${SITE_CONFIG.contactEmail}?subject=${s}&body=${b}`;
}

// 구매 문의: 결제 링크가 설정돼 있으면 새 탭으로 열고, 없으면 기존 이메일 문의로 대체합니다.
function contactPurchase(subject, body) {
  if (SITE_CONFIG.paymentLink) {
    window.open(SITE_CONFIG.paymentLink, "_blank", "noopener");
    return;
  }
  contactMail(subject, body);
}
