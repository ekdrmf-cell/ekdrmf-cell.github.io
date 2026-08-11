(function () {
  const active = document.body.dataset.active || "";
  const root = document.body.dataset.root || "./";

  const nav = [
    { href: `${root}index.html`, key: "home", label: "홈" },
    { href: `${root}games/index.html`, key: "games", label: "게임" },
    { href: `${root}services.html`, key: "services", label: "서비스" },
    { href: `${root}ebooks.html`, key: "ebooks", label: "전자책" },
  ];

  const logoSvg = `
    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="12" cy="12" r="3" fill="white" />
      <circle cx="5" cy="6" r="2.2" fill="white" fill-opacity="0.85" />
      <circle cx="19" cy="6" r="2.2" fill="white" fill-opacity="0.85" />
      <circle cx="12" cy="20" r="2.2" fill="white" fill-opacity="0.85" />
      <path d="M12 12L5 6M12 12L19 6M12 12L12 20" stroke="white" stroke-opacity="0.6" stroke-width="1.4" />
    </svg>
  `;

  const headerEl = document.getElementById("site-header");
  if (headerEl) {
    headerEl.innerHTML = `
      <div class="wrap">
        <a class="brand" href="${root}index.html">
          <span class="logo-mark">${logoSvg}</span>
          서비스허브
        </a>
        <nav class="nav-links">
          ${nav
            .map(
              (item) =>
                `<a href="${item.href}" class="${item.key === active ? "active" : ""}">${item.label}</a>`
            )
            .join("")}
        </nav>
      </div>
    `;
  }

  const footerEl = document.getElementById("site-footer");
  if (footerEl) {
    footerEl.innerHTML = `
      <div class="wrap footer-inner">
        <a class="brand" href="${root}index.html">
          <span class="logo-mark">${logoSvg}</span>
          서비스허브
        </a>
        <div class="tagline">데이터로 검증된 빈틈만 골라 만듭니다 · 무자본으로 시작한 실험 프로젝트</div>
        <a class="footer-link" href="${root}privacy.html">개인정보처리방침</a>
      </div>
    `;
  }
})();
