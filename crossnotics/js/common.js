/*
 * 천지인운명관 전용 공통 헤더ㆍ푸터ㆍ문의 도우미 — 서비스허브의 js/common.js와 독립된
 * 사본입니다(2026-08-23, 서비스허브와의 공유 파일 분리 작업). 브랜드명ㆍ내비게이션ㆍFAQ
 * 챗봇 내용을 전부 천지인운명관 전용으로 새로 작성했습니다 — "서비스허브"라는 이름이나
 * 게임ㆍ전자책ㆍ서비스 같은 무관한 상품 안내가 더 이상 노출되지 않습니다.
 */
(function () {
  const active = document.body.dataset.active || "";
  const root = document.body.dataset.root || "./";

  const nav = [
    { href: `${root}crossnotics/index.html`, key: "home", label: "홈" },
    { href: `${root}unse/index.html`, key: "tools", label: "무료 도구" },
    { href: `${root}crossnotics/index.html#cn-form`, key: "apply", label: "신청하기" },
  ];

  const logoSvg = `
    <svg viewBox="0 0 36 36" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      <circle cx="18" cy="12" r="10" fill="#e8562f" fill-opacity="0.82" />
      <circle cx="12.5" cy="21.5" r="10" fill="#6d4aff" fill-opacity="0.82" />
      <circle cx="23.5" cy="21.5" r="10" fill="#0a7d5e" fill-opacity="0.82" />
      <circle cx="18" cy="18.3" r="3.2" fill="#ffffff" />
    </svg>
  `;

  const headerEl = document.getElementById("site-header");
  if (headerEl) {
    headerEl.innerHTML = `
      <div class="wrap">
        <a class="brand" href="${root}crossnotics/index.html">
          <span class="logo-mark">${logoSvg}</span>
          천지인운명관
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
        <a class="brand" href="${root}crossnotics/index.html">
          <span class="logo-mark">${logoSvg}</span>
          천지인운명관
        </a>
        <div class="tagline">사주ㆍ서양점성술ㆍ타로 — 독립 계산 후 교차 검증하는 개인 맞춤 진단</div>
        <div style="display:flex; gap:16px;">
          <a class="footer-link" href="javascript:void(0)" onclick="contactMail('천지인운명관 문의', '안녕하세요, 천지인운명관 관련 문의드립니다.\\n\\n')">문의</a>
          <a class="footer-link" href="${root}privacy.html">개인정보처리방침</a>
        </div>
      </div>
    `;
  }

  // ---- 문의 도우미(FAQ 챗봇) — 실시간 AI 아님, 미리 써둔 답변만 보여주는 규칙 기반 위젯
  // (서비스허브와 동일한 이유: 정적 사이트라 API 키 노출 위험 회피). 내용은 천지인운명관
  // 전용으로 새로 작성 — tools/crossnotics-report/knowledge/question_taxonomy.md에서 실제
  // 손님들이 자주 묻는 유형(연애ㆍ궁합ㆍ직업ㆍ신살 등)을 참고해 구성.
  const FAQ_BOT_ITEMS = [
    { q: "천지인운명관은 어떤 서비스인가요?", a: "사주ㆍ서양점성술ㆍ타로를 각각 독립된 계산 엔진으로 먼저 계산한 뒤, 세 체계가 어디서 일치하는지를 수학적으로 비교해드리는 개인 맞춤 진단 서비스예요. AI는 계산 결과를 문장으로 옮기는 역할만 하고, 숫자나 카드ㆍ간지를 스스로 지어내지 않아요." },
    { q: "무료로도 볼 수 있나요?", a: "네, 사주ㆍ궁합ㆍ타로ㆍ꿈해몽ㆍ혈액형ㆍ이름풀이까지 기본 결과는 전부 무료예요. 더 깊은 개인 맞춤 해석(십신ㆍ대운ㆍ신살ㆍ실제 궁합 점수 등)은 유료 진단에서 확인할 수 있어요." },
    { q: "궁합도 실제로 계산해주나요?", a: "네, 상대방 생년월일시를 알려주시면 두 분의 일간ㆍ일지ㆍ띠 관계를 명리학 이론으로 실제 계산해서 궁합 점수를 알려드려요. 연인ㆍ부부뿐 아니라 동업ㆍ가족 관계도 유형에 맞게 다르게 풀어드립니다." },
    { q: "유료 진단은 어떻게 결제하나요?", a: "신청 폼 제출 후 계좌이체 안내가 뜨고, 입금 확인 후 영업일 기준 1~2일 내로 리포트 PDF를 이메일로 보내드려요." },
    { q: "제 질문에 답을 못 하면 어떻게 하나요?", a: "계산 근거가 없는 질문(예: 정확한 복권 번호)은 답 못 한다는 걸 먼저 솔직히 밝히고, 그 대신 손님의 실제 데이터로 답할 수 있는 가장 가까운 내용을 이어서 알려드려요. 답 못 한 걸 숨기거나 지어내지 않는 게 저희의 원칙이에요." },
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
      contactMail("천지인운명관 문의", "안녕하세요, 문의드립니다.\n\n");
    }
  });
})();
