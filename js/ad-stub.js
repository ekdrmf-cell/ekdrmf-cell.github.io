/*
 * 광고 · 결제 스텁 모듈
 * 실제 구글 애드센스/애드몹, 결제대행사(PG) 연동 전까지
 * UX 흐름만 미리 만들어두는 자리표시자입니다.
 * 나중에 이 파일의 showRewardAd/showInterstitialAd 안쪽만
 * 실제 광고 SDK 호출로 바꾸면 됩니다.
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

  function showRewardAd(onComplete) {
    let seconds = 3;
    open(`
      <h3>보상형 광고 (준비중)</h3>
      <p>실제 서비스에서는 여기서 짧은 광고가 재생되고, 끝까지 보면 보상을 드립니다.</p>
      <div class="countdown" id="ad-countdown">${seconds}</div>
      <button class="btn btn-block" disabled id="ad-skip-btn">시청 중...</button>
    `);
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
    open(`
      <h3>광고 (준비중)</h3>
      <p>실제 서비스에서는 여기에 전면 광고가 표시됩니다. 지금은 자리표시자입니다.</p>
      <button class="btn btn-primary btn-block" id="ad-close-btn">계속하기</button>
    `);
    const btn = document.getElementById("ad-close-btn");
    if (btn) {
      btn.onclick = () => {
        close();
        onClose && onClose();
      };
    }
  }

  function showRemoveAdsPurchase() {
    open(`
      <h3>광고 제거</h3>
      <p>결제 연동은 아직 준비 중입니다. 서비스 오픈 시 1회 결제로 모든 광고를 영구히 제거할 수 있습니다.</p>
      <button class="btn btn-block" id="ad-purchase-close">닫기</button>
    `);
    const btn = document.getElementById("ad-purchase-close");
    if (btn) btn.onclick = close;
  }

  return { showRewardAd, showInterstitialAd, showRemoveAdsPurchase, close };
})();
