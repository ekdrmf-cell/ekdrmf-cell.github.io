(function () {
  const active = document.body.dataset.active || "";
  const root = document.body.dataset.root || "./";

  const nav = [
    { href: `${root}index.html`, key: "home", label: "홈" },
    { href: `${root}games/index.html`, key: "games", label: "게임" },
    { href: `${root}unse/index.html`, key: "saju", label: "운세" },
    { href: `${root}services.html`, key: "services", label: "서비스" },
    { href: `${root}ebooks.html`, key: "ebooks", label: "전자책" },
    { href: `${root}resources.html`, key: "resources", label: "자료" },
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
        <div style="display:flex; gap:16px;">
          <a class="footer-link" href="${root}about.html">소개</a>
          <a class="footer-link" href="${root}resources.html">무료 자료</a>
          <a class="footer-link" href="${root}privacy.html">개인정보처리방침</a>
        </div>
      </div>
    `;
  }

  // ---- 문의 도우미(FAQ 챗봇) — 실시간 AI 아님, 미리 써둔 답변만 보여주는 규칙 기반 위젯.
  // 사이트가 서버 없는 정적 사이트라 실시간 AI 응답은 API 키 노출 위험이 있어 채택 안 함(같은
  // 이유로 타로/꿈해몽도 정적 콘텐츠로 만들었음, project 메모리 참고).
  const FAQ_BOT_ITEMS = [
    { q: "서비스허브는 어떤 사이트인가요?", a: "게임·서비스(업무 자동화 시트)·전자책·운세 도구를 한 곳에서 제공하는 사이트예요. 게임과 운세 도구는 무료, 서비스와 전자책은 실용 상품 위주로 판매하고 있어요." },
    { q: "게임은 전부 무료인가요?", a: "네, 모든 게임은 무료예요. 게임오버 후 광고를 보면 한 번 더 도전할 수 있고, 광고 없이 하고 싶으면 게임 화면의 '광고 제거' 버튼으로 문의하시면 돼요." },
    { q: "서비스(자동화 시트)는 결제하면 어떻게 받나요?", a: "구매 버튼을 누르면 입금 계좌 안내가 뜨고, 입금 확인 후 이메일로 구글시트 사본과 사용 설명서를 보내드려요. 구글 계정만 있으면 바로 쓸 수 있어요." },
    { q: "전자책은 어떤 형식인가요?", a: "전부 PDF 파일이고, 결제 확인 후 이메일로 바로 전달돼요. 각 전자책 소개에 실제 페이지 수와 화면 캡처 수록 여부가 정확히 표시돼 있어요." },
    { q: "운세 도구도 결제해야 하나요?", a: "사주·궁합·타로·꿈해몽·혈액형·이름풀이 전부 기본 결과는 무료예요. 더 자세한 개인 맞춤 해석만 결제 후 이메일로 신청하는 방식이에요." },
  ];

  const botToggleBtn = document.createElement("button");
  botToggleBtn.className = "faq-bot-toggle";
  botToggleBtn.setAttribute("aria-label", "문의 도우미 열기");
  botToggleBtn.innerHTML = "💬";
  document.body.appendChild(botToggleBtn);

  const botPanel = document.createElement("div");
  botPanel.className = "faq-bot-panel";
  botPanel.innerHTML = `
    <div class="faq-bot-header">
      <span>무엇을 도와드릴까요?</span>
      <button class="faq-bot-close" aria-label="닫기">✕</button>
    </div>
    <div class="faq-bot-body">
      <div class="faq-bot-intro">자주 묻는 질문이에요. 궁금한 걸 눌러보세요.</div>
      <div class="faq-bot-list">
        ${FAQ_BOT_ITEMS.map((item, i) => `<button class="faq-bot-q" data-i="${i}">${item.q}</button>`).join("")}
      </div>
      <div class="faq-bot-answer" id="faq-bot-answer" style="display:none;"></div>
      <button class="faq-bot-contact" id="faq-bot-contact">그 외 문의하기 →</button>
    </div>
  `;
  document.body.appendChild(botPanel);

  botToggleBtn.addEventListener("click", () => {
    botPanel.classList.toggle("open");
  });
  botPanel.querySelector(".faq-bot-close").addEventListener("click", () => {
    botPanel.classList.remove("open");
  });
  botPanel.querySelectorAll(".faq-bot-q").forEach((btn) => {
    btn.addEventListener("click", () => {
      const item = FAQ_BOT_ITEMS[Number(btn.dataset.i)];
      const answerEl = document.getElementById("faq-bot-answer");
      answerEl.textContent = item.a;
      answerEl.style.display = "block";
    });
  });
  document.getElementById("faq-bot-contact").addEventListener("click", () => {
    if (typeof contactMail === "function") {
      contactMail("서비스허브 문의", "안녕하세요, 문의드립니다.\n\n");
    }
  });
})();
