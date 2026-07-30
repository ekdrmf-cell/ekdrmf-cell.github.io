(function () {
  const active = document.body.dataset.active || "";
  const root = document.body.dataset.root || "./";

  const nav = [
    { href: `${root}index.html`, key: "home", label: "홈" },
    { href: `${root}games/index.html`, key: "games", label: "게임" },
    { href: `${root}services.html`, key: "services", label: "서비스" },
    { href: `${root}ebooks.html`, key: "ebooks", label: "전자책" },
  ];

  const headerEl = document.getElementById("site-header");
  if (headerEl) {
    headerEl.innerHTML = `
      <div class="wrap">
        <a class="brand" href="${root}index.html">
          <span class="dot"></span>
          수익화허브
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
      <div class="wrap">
        무자본으로 시작해 게임 · 서비스 · 전자책을 한 곳에 모으는 실험 프로젝트입니다.
      </div>
    `;
  }
})();
