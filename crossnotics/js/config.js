/*
 * 천지인운명관 전용 사이트 설정 — 서비스허브의 js/config.js와 독립된 사본입니다
 * (2026-08-23, 사용자 지시로 서비스허브와의 공유 파일을 전부 분리하는 작업의 일부).
 * 여기 값만 바꾸면 천지인운명관(크로스노틱스 + 무료 도구 saju/gunghap/tarot/dream/name/
 * bloodtype/unse) 전체에 반영됩니다 — 서비스허브 쪽 js/config.js와는 이제 완전히 무관합니다.
 */
const SITE_CONFIG = {
  contactEmail: "ekdrmf@gmail.com",

  // TODO(사용자): 애드센스에서 이 사이트 전용 도메인을 추가하면 발급되는
  // "ca-pub-여러자리숫자" 형태의 퍼블리셔 ID를 여기 넣으세요.
  adsensePublisherId: "",

  // TODO(사용자): 토스ㆍ카카오페이 개인 송금 링크(예: https://toss.me/아이디)
  // 또는 계좌번호 안내 문구를 넣으세요. 비워두면 이메일 문의로만 안내됩니다.
  paymentLink: "",
  paymentGuideText: "케이뱅크 100-137-259635 (예금주: 최*호)",

  rewardAdSlot: "",
  interstitialAdSlot: "",
};
window.SITE_CONFIG = SITE_CONFIG;

function contactMail(subject, body) {
  const s = encodeURIComponent(subject);
  const b = encodeURIComponent(body || "");
  window.location.href = `mailto:${SITE_CONFIG.contactEmail}?subject=${s}&body=${b}`;
}

// 구매 문의: 결제 링크가 있으면 새 탭으로 열고, 계좌 안내문구만 있으면 입금 안내 팝업을
// 띄운 뒤 이메일 문의로 이어지고, 둘 다 없으면 바로 이메일 문의로 대체합니다.
function contactPurchase(subject, body) {
  if (SITE_CONFIG.paymentLink) {
    window.open(SITE_CONFIG.paymentLink, "_blank", "noopener");
    return;
  }
  if (SITE_CONFIG.paymentGuideText) {
    showPaymentGuide(SITE_CONFIG.paymentGuideText, () => contactMail(subject, body));
    return;
  }
  contactMail(subject, body);
}

// 계좌 안내 팝업(crossnotics/css/base.css의 공용 .modal 스타일 재사용)
function showPaymentGuide(guideText, onConfirm) {
  let backdrop = document.getElementById("payment-guide-backdrop");
  if (!backdrop) {
    backdrop = document.createElement("div");
    backdrop.id = "payment-guide-backdrop";
    backdrop.className = "modal-backdrop";
    document.body.appendChild(backdrop);
  }
  backdrop.innerHTML = `
    <div class="modal">
      <h3>입금 안내</h3>
      <p>아래 계좌로 입금해주시면 확인 후 상품을 보내드립니다.</p>
      <p style="color:var(--text);font-weight:600;">${guideText}</p>
      <button class="btn btn-primary btn-block" id="payment-guide-confirm">입금 완료, 문의 이메일 보내기</button>
      <button class="btn btn-block" id="payment-guide-close" style="margin-top:8px;">닫기</button>
    </div>`;
  backdrop.classList.add("open");
  document.getElementById("payment-guide-close").onclick = () => backdrop.classList.remove("open");
  document.getElementById("payment-guide-confirm").onclick = () => {
    backdrop.classList.remove("open");
    onConfirm && onConfirm();
  };
}
