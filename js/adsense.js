/*
 * 구글 애드센스 로더 — js/config.js의 adsensePublisherId가 비어있으면
 * 아무 것도 하지 않습니다(광고 스크립트 자체가 안 실려서 페이지 속도에 영향 없음).
 * 사용자님이 애드센스에서 도메인 승인을 받고 퍼블리셔 ID를 config.js에 넣으면
 * 이 파일이 자동으로 광고 스크립트를 불러옵니다. 그 외에 손댈 곳 없습니다.
 */
(function () {
  const pubId = window.SITE_CONFIG && window.SITE_CONFIG.adsensePublisherId;
  if (!pubId) return;

  const script = document.createElement("script");
  script.async = true;
  script.src = `https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=${pubId}`;
  script.crossOrigin = "anonymous";
  document.head.appendChild(script);
})();

// 페이지 안에 <div class="ad-slot" data-ad-slot="광고단위ID"></div> 를 넣으면
// 이 함수가 그 자리에 실제 디스플레이 광고를 채워줍니다(퍼블리셔 ID가 설정된 경우에만).
function renderAdSlot(container) {
  const pubId = window.SITE_CONFIG && window.SITE_CONFIG.adsensePublisherId;
  const slotId = container && container.dataset.adSlot;
  if (!pubId || !slotId || !container) return;

  const ins = document.createElement("ins");
  ins.className = "adsbygoogle";
  ins.style.display = "block";
  ins.setAttribute("data-ad-client", pubId);
  ins.setAttribute("data-ad-slot", slotId);
  ins.setAttribute("data-ad-format", "auto");
  ins.setAttribute("data-full-width-responsive", "true");
  container.appendChild(ins);

  window.adsbygoogle = window.adsbygoogle || [];
  window.adsbygoogle.push({});
}
