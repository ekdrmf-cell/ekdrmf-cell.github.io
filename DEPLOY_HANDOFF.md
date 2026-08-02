# 배포·수익화 인프라 인수인계 — 새 세션에서 이어받을 때 읽는 문서

**작성일**: 2026-08-03
**용도**: 전자책 제작(`EBOOK_HANDOFF.md`)과는 별개 트랙. "사이트를 실제로 배포하고 광고·결제를
붙여서 진짜 돈을 벌기 시작하는" 작업의 진행상황을 정리한 문서. 새 세션에서 이어받으면
이 문서부터 읽을 것.

---

## 0. 지금 막힌 지점 — 가장 먼저 해결할 것

**GitHub에 코드를 올리는(`git push`) 작업이 반복적으로 타임아웃되고 있음.**

- 사용자가 GitHub 계정을 만들고 빈 저장소를 생성함: `https://github.com/ekdrmf-cell/akdlfem`
- 로컬 저장소(`C:\Users\nalla\Desktop\수익화허브`)에 원격(origin)을 이 주소로 연결하고
  브랜치를 `master`→`main`으로 변경 완료.
- `git push -u origin main`을 여러 번 시도함:
  - 1차: 60초 타임아웃(백그라운드로 재시도)
  - 사용자가 "로그인 했어"라고 확인
  - 2차: 20초 타임아웃으로 재확인 시도 → 또 타임아웃
  - `git ls-remote origin` 결과 **원격 저장소가 여전히 비어있음을 확인**(push 성공 안 함)
- Git Credential Manager(GCM)는 시스템에 설치돼 있음(`C:\Program Files\Git\mingw64\bin\git-credential-manager.exe`,
  `credential.helper=manager`로 시스템 설정에 등록됨) — 정상적으로는 `git push` 시 브라우저 로그인
  창이 자동으로 떠야 함.

### 다음 세션에서 시도해볼 것 (우선순위 순)
1. **가장 먼저**: `cd "C:\Users\nalla\Desktop\수익화허브" && git push -u origin main`을
   **타임아웃 없이 포그라운드로** 실행하고, 브라우저에 로그인/권한승인 창이 뜨는지
   실제 화면으로 직접 확인할 것(에이전트가 백그라운드로 실행하면 창이 떴는지 알 수 없어서
   계속 같은 문제가 반복됐을 가능성이 있음).
2. 그래도 안 되면 GCM 캐시 문제일 수 있음 — `git credential-manager github logout` 후
   재시도, 또는 Windows 자격 증명 관리자(제어판 → 자격 증명 관리자)에서 `git:https://github.com`
   항목을 삭제하고 재시도.
3. 그래도 안 되면 **GitHub Desktop 앱 설치**가 제일 확실한 대안(비개발자용 GUI, 브라우저
   로그인만으로 push 가능, 이후 명령줄 인증 문제 없음). `desktop.github.com`에서 설치 후
   저장소를 열어 "Publish repository"로 올리면 됨.
4. 최후 수단(비상용): GitHub에서 Personal Access Token을 발급받아 쓰는 방법도 있지만,
   **토큰은 절대 이 대화(에이전트)에 붙여넣지 말 것** — 에이전트는 안전 규칙상 API
   키/토큰을 대신 입력하거나 다루면 안 됨. 이 방법은 사용자가 터미널에서 직접 처리하거나,
   GitHub Desktop 등 GUI로 우회할 것.

push가 성공하면, 그 다음은 **GitHub Pages 켜기**(저장소 Settings → Pages → Branch를
`main`으로 선택 → Save)만 하면 `https://ekdrmf-cell.github.io/akdlfem/` 같은 형태의
실제 인터넷 주소로 사이트가 뜸. 이건 웹 화면에서 클릭 몇 번이면 되는 작업.

---

## 1. 지금까지 완료한 것 (로컬에는 이미 다 돼 있음, 커밋도 완료)

사용자가 "1번(배관공사)부터 하자, 진짜 실제 돈 좀 벌어보자"고 요청해서, 애드센스·결제·
개인정보처리방침 인프라를 코드 레벨로 전부 준비함. 커밋 `5485bf3`에 전부 포함됨.

- **`js/config.js`**: 사이트 전역 설정 파일에 아래 항목 추가(전부 빈 문자열 상태 —
  값만 채우면 자동으로 작동하도록 설계됨):
  - `adsensePublisherId` — 애드센스 퍼블리셔 ID(`ca-pub-...`)
  - `paymentLink` — 토스/카카오페이 송금 링크
  - `rewardAdSlot`, `interstitialAdSlot` — 게임용 광고 단위 ID(선택)
- **`js/adsense.js`**(신규): `adsensePublisherId`가 채워지면 애드센스 스크립트를 자동으로
  불러옴. 비어있으면 아무 것도 안 함(속도 손해 없음). `renderAdSlot()` 함수로 특정 자리에
  실제 광고를 꽂을 수 있음.
- **`js/ad-stub.js`**(개선): 게임의 "보상형 광고"ㆍ"전면 광고" 모달이 애드센스 설정 여부에
  따라 실제 광고 자리를 보여주거나, 기존처럼 "준비중" 대기화면을 보여줌. **주의**: 구글
  애드센스는 앱용 애드몹과 달리 웹사이트용 "진짜 리워드 광고 API"가 없음 — 그래서 광고를
  보여주고 카운트다운이 끝나면 보상을 주는 방식으로 비슷하게 흉내만 냄(실제로 광고를
  끝까지 봤는지 애드센스가 검증해주지는 않음). 이건 기술적 한계이지 버그가 아님.
  결제 유도 모달(`showRemoveAdsPurchase`)도 `paymentLink`가 있으면 "결제하러 가기"
  버튼이 자동으로 나타남.
- **`privacy.html`**(신규): 애드센스 심사에 필수인 개인정보처리방침 페이지. 쿠키ㆍ광고ㆍ
  게임 로컬저장 안내 포함. 모든 페이지 footer에 링크 추가함(`js/common.js` 수정).
- **`ads.txt`**(신규, 자리만): 애드센스 승인 후 실제 한 줄로 교체해야 함(안내 주석만 있음).
- **전 페이지 스크립트 태그 정리**: `index.html`, `games/index.html`, 게임 6종
  (`2048`, `match3`, `memory`, `quiz`, `runner`, `whackamole`), `ebooks.html`,
  `services.html`, `privacy.html` 전부 `config.js` → `adsense.js` → `common.js` 순서로
  스크립트를 불러오도록 통일함(이전엔 `index.html`과 게임 페이지들에 `config.js` 자체가
  누락돼 있었음).
- **구매 문의 버튼 8개**(`ebooks.html` 7개, `services.html` 1개) `contactMail()` →
  `contactPurchase()`로 교체. `paymentLink`가 설정되면 이메일 대신 결제 링크로 바로
  연결되고, 없으면 지금처럼 이메일 문의로 자연스럽게 대체됨(코드 하나로 두 가지 동작).

## 2. 아직 사용자가 직접 해야 하는 것 (계정 관련이라 에이전트가 대신 못 함)

1. **GitHub push 완료**(위 0번 참고) → GitHub Pages 켜기
2. **애드센스**: 로그인 → 사이트 추가 → 배포된 도메인 입력 → 심사 대기 → 승인되면
   퍼블리셔 ID를 `js/config.js`의 `adsensePublisherId`에 넣어달라고 요청하기
   (기존에 `money-news.tistory.com`으로 승인받은 계정 그대로 사용 가능, 새 계정
   필요 없음 — 단, 새 도메인은 별도 심사를 거침)
3. **결제 수단**: 토스ㆍ카카오페이 개인 송금 링크 만들기(5분) → 링크를
   `js/config.js`의 `paymentLink`에 넣어달라고 요청하기
4. **연락처 분리**: 새 이메일 또는 카카오톡 채널 개설 → `contactEmail`에 반영 요청

## 3. 다음 세션 시작 프롬프트

"수익화허브 배관공사 이어서 하자"라고 말하면 이 문서를 먼저 읽고, 0번(push 문제)부터
해결한 뒤 2번 목록을 하나씩 확인하며 진행하면 됨. `EBOOK_HANDOFF.md`(전자책 제작 트랙)와는
독립적인 작업이므로 서로 순서를 신경 쓸 필요 없음 — 아무거나 사용자가 원하는 쪽부터 진행.
