/*
 * 광고 · 결제 모듈
 * js/config.js에 애드센스 퍼블리셔 ID와 광고 단위 ID가 채워지면
 * 실제 광고를 자리에 띄우고, 비어있으면 지금처럼 "준비중" 대기 화면만 보여줍니다.
 *
 * 참고(중요): 구글 애드센스는 웹사이트용 "진짜 보상형(rewarded) 광고 API"를
 * 제공하지 않습니다(그건 앱 전용 애드몹 기능). 그래서 여기서는 광고 단위를
 * 화면에 보여주고, 일정 시간(카운트다운)이 지나면 보상을 주는 방식으로
 * 비슷한 흐름을 만듭니다 — 실제로 광고를 끝까지 봤는지 애드센스가 확인해주지는
 * 않지만, 웹에서 흔히 쓰는 현실적인 대안입니다.
 */
const AdStub = (function () {
  let backdrop, modal;

  function ensureModal() {
    if (backdrop) return;
    backdrop = document.createElement("div");
    backdrop.className = "modal-backdrop";
    backdrop.innerHTML = `<div class="modal" id="ad-stub-modal"></div>`;
    document.body.appendChild(backdrop);
    modal = backdrop.querySelector("#ad-stub-modal");
  }

  function open(html) {
    ensureModal();
    modal.innerHTML = html;
    backdrop.classList.add("open");
  }

  function close() {
    if (backdrop) backdrop.classList.remove("open");
  }

  function adReady() {
    return !!(window.SITE_CONFIG && window.SITE_CONFIG.adsensePublisherId);
  }

  function adSlotHtml(slotId) {
    if (!adReady() || !slotId) return "";
    return `<div class="ad-slot" data-ad-slot="${slotId}" style="min-height:100px;margin:12px 0;"></div>`;
  }

  function mountAdSlot(slotId) {
    if (!adReady() || !slotId || typeof renderAdSlot !== "function") return;
    const el = modal.querySelector(".ad-slot");
    if (el) renderAdSlot(el);
  }

  function showRewardAd(onComplete) {
    const slotId = window.SITE_CONFIG && window.SITE_CONFIG.rewardAdSlot;
    let seconds = 3;
    open(`
      <h3>${adReady() ? "잠깐, 광고를 보면 이어할 수 있어요" : "보상형 광고 (준비중)"}</h3>
      <p>${adReady() ? "아래 광고가 노출되는 동안 잠시만 기다려주세요." : "실제 서비스에서는 여기서 짧은 광고가 표시되고, 끝까지 보면 보상을 드립니다."}</p>
      ${adSlotHtml(slotId)}
      <div class="countdown" id="ad-countdown">${seconds}</div>
      <button class="btn btn-block" disabled id="ad-skip-btn">시청 중...</button>
    `);
    mountAdSlot(slotId);
    const timer = setInterval(() => {
      seconds -= 1;
      const el = document.getElementById("ad-countdown");
      if (el) el.textContent = String(Math.max(seconds, 0));
      if (seconds <= 0) {
        clearInterval(timer);
        const btn = document.getElementById("ad-skip-btn");
        if (btn) {
          btn.disabled = false;
          btn.textContent = "보상 받기";
          btn.onclick = () => {
            close();
            onComplete && onComplete();
          };
        }
      }
    }, 1000);
  }

  function showInterstitialAd(onClose) {
    const slotId = window.SITE_CONFIG && window.SITE_CONFIG.interstitialAdSlot;
    open(`
      <h3>${adReady() ? "광고" : "광고 (준비중)"}</h3>
      ${adSlotHtml(slotId) || "<p>실제 서비스에서는 여기에 전면 광고가 표시됩니다. 지금은 자리표시자입니다.</p>"}
      <button class="btn btn-primary btn-block" id="ad-close-btn">계속하기</button>
    `);
    mountAdSlot(slotId);
    const btn = document.getElementById("ad-close-btn");
    if (btn) {
      btn.onclick = () => {
        close();
        onClose && onClose();
      };
    }
  }

  function showRemoveAdsPurchase() {
    const hasPayment = window.SITE_CONFIG && (window.SITE_CONFIG.paymentLink || window.SITE_CONFIG.paymentGuideText);
    open(`
      <h3>광고 제거</h3>
      <p>${hasPayment ? "결제 후 광고 제거 코드는 별도로 안내드립니다(자동 처리 전까지 수동 확인)." : "결제 연동은 아직 준비 중입니다. 서비스 오픈 시 1회 결제로 모든 광고를 영구히 제거할 수 있습니다."}</p>
      ${hasPayment ? '<button class="btn btn-primary btn-block" id="ad-purchase-go">결제하러 가기</button>' : ""}
      <button class="btn btn-block" id="ad-purchase-close">닫기</button>
    `);
    const goBtn = document.getElementById("ad-purchase-go");
    if (goBtn) {
      goBtn.onclick = () => {
        contactPurchase("광고 제거 구매 문의", "게임 광고 제거 결제를 원합니다. 결제 확인 후 처리 방법을 안내해주세요.");
      };
    }
    const btn = document.getElementById("ad-purchase-close");
    if (btn) btn.onclick = close;
  }

  return { showRewardAd, showInterstitialAd, showRemoveAdsPurchase, close };
})();
