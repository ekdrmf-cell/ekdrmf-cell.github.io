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

// 계좌 안내 팝업(crossnotics/css/base.css의 공용 .modal 스타일 재사용) — 2026-08-24
// 수정: 예전엔 확인 버튼이 "입금 완료, 문의 이메일 보내기"였는데, 사용자 지시로 "신청하기
// → 계좌 안내 → [입금 완료]면 신청 완료, [입금 안 함]이면 신청 취소"라는 명확한 이분법으로
// 바꿈. 실제 입금 여부를 사이트가 검증할 방법은 없다(계좌 API 연동 없음) — 이 버튼은
// 손님이 스스로 밝히는 것뿐이고, 진짜 검증은 사장님이 로컬 프로그램에서 은행 앱과 대조해
// 직접 한다(2026-08-24 논의). onCancel을 추가해 "입금 안 함"을 눌렀을 때도 호출하는 곳에서
// 반응할 수 있게 함(예: "신청이 취소되었습니다" 화면 표시).
function showPaymentGuide(guideText, onConfirm, onCancel) {
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
      <button class="btn btn-primary btn-block" id="payment-guide-confirm">입금 완료</button>
      <button class="btn btn-block" id="payment-guide-close" style="margin-top:8px;">입금 안 함</button>
    </div>`;
  backdrop.classList.add("open");
  document.getElementById("payment-guide-close").onclick = () => {
    backdrop.classList.remove("open");
    onCancel && onCancel();
  };
  document.getElementById("payment-guide-confirm").onclick = () => {
    backdrop.classList.remove("open");
    onConfirm && onConfirm();
  };
}
