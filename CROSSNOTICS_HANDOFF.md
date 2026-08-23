# 크로스노틱스(Cross-Notics) 트랙 인수인계 문서

이 문서는 전자책 트랙(`EBOOK_HANDOFF.md`), 서비스 트랙(`SERVICES_HANDOFF.md`), 마케팅 트랙
(`MARKETING_HANDOFF.md`), 배포 트랙(`DEPLOY_HANDOFF.md`)과 독립적인 **다섯 번째 트랙**입니다.
크로스노틱스(사주ㆍ별자리ㆍ타로 교차진단 서비스) 관련 요청이 오면 이 문서부터 읽으세요.

**전체 설계는 `C:\Users\ekdrm\.claude\plans\idempotent-rolling-hopcroft.md`에 승인된 계획으로
남아있음 — 큰 방향이 헷갈리면 그 파일부터 참고할 것.**

**2026-08-23(-12번) 이후로 천지인운명관은 서비스허브와 코드ㆍ콘텐츠상 완전히 분리됐다** —
같은 GitHub 저장소ㆍ같은 배포 도메인은 유지하되(URL 안 바뀜), 공유 파일(js/config.js,
js/common.js, css/style.css, pdf_kit.py, catalog.js)은 전부 독립 사본으로 갈라졌고,
`crossnotics/index.html`ㆍ`crossnotics/privacy.html`까지 포함해 **분리가 완료됨**. 아래
-11ㆍ-12번 항목 참고. **크로스노틱스 관련 작업을 할 때 이제 서비스허브 쪽 공유 파일을
참고하거나 고칠 필요가 없다 — 전부 crossnotics/ 폴더 또는 tools/crossnotics-* 폴더 안에서
끝난다.**

## -12. 2026-08-23 업데이트 — 분리 마무리(index.html/privacy.html 배관 전환) + 그 사이
다른 세션이 진행한 상세페이지 개편 반영 확인

-11번에서 "다른 세션이 crossnotics/index.html·crossnotics.css를 동시에 수정 중"이라 그 두
파일만 보류해뒀는데, 사용자가 "작업 시작하자"고 재개 지시 → git log로 그 사이 다른 세션이
커밋한 내용을 먼저 확인한 뒤 진행함(중요 — 다음에도 "대기" 뒤에 재개할 땐 무작정 이어가지
말고 git log부터 확인할 것, 실제로 이번에 상세페이지가 대폭 바뀌어 있었음).

### 그 사이 다른 세션이 이미 해놓은 것 (git log로 확인, 내용 겹치지 않게 조율함)

- **`crossnotics/privacy.html` 신규** — 개인정보처리방침이 서비스허브 루트 페이지 대신
  천지인운명관 자체 페이지로 이미 분리되어 있었음(-11번 "다음에 할 일"에 남겨뒀던 항목이
  이미 해결됨). 서버ㆍDB에 개인정보 저장 안 함, Google Apps Script로만 전달한다는 내용.
- **신청 흐름 개편** — mailto 팝업 대신 Google Apps Script 웹앱(`crossnotics/apps-script/
  Code.gs`, `CN_MAIL_ENDPOINT`)으로 조용히 접수 후 진행상황 패널 표시. 엔드포인트가
  비어있으면 예전 mailto로 자동 폴백하는 안전장치 있음.
- **질문칸 placeholder 개선** — 이 세션이 만든 `question_taxonomy.md`의 "direct 판정 가능한
  유형"을 그대로 가져다 써서, 예전에 전부 "올해 이직운이 궁금해요"로 똑같던 placeholder를
  티어별 보유 체계에 맞게 다양화함(`CN_QUESTION_EXAMPLES` 배열).
- **다크 럭셔리 리디자인** — 글래스모피즘ㆍ노이즈텍스처ㆍ스크롤 등장 애니메이션, 가격
  비교표를 카드 스펙으로 통합, 신뢰배지, 환불 불가 정책 명시 등.
- **이번 세션이 신설한 궁합 상대방 입력칸(관계유형 선택 포함)은 그대로 보존되어 있었음** —
  다른 세션이 지우거나 바꾸지 않고 그 위에 얹어서 작업했음, 충돌 없음.

### 이번 세션이 마무리한 것

`crossnotics/index.html`ㆍ`crossnotics/privacy.html` 둘 다:
- `<link rel="stylesheet" href="../css/style.css">` → `href="css/base.css"`(같은 폴더 안의
  독립 사본이라 상대경로가 `../css/`가 아니라 `css/`로 바뀜, 헷갈리지 않게 기록).
- `<script src="../js/config.js">` → `src="js/config.js"`.
- 헤더ㆍ푸터는 애초에 `#site-header`/`#site-footer`를 common.js로 채우는 방식이 아니라
  두 파일 다 마크업이 직접 하드코딩되어 있어서(다른 세션의 "-8c442f0 서비스허브 공용
  헤더/푸터에서 분리" 커밋에서 이미 그렇게 됨) `crossnotics/js/common.js`를 이 두 파일에
  연결할 필요가 없었음 — 무료 도구 7개(saju/gunghap/tarot/dream/name/bloodtype/unse)만
  common.js를 실제로 씀.

### 검증

- 로컬 서버로 `crossnotics/index.html`ㆍ`privacy.html` 둘 다 콘솔 에러 없이 로드 확인.
- `SITE_CONFIG`가 새 `crossnotics/js/config.js`에서 정상 로드되는 것, 다크 배경(rgb(10,8,20))
  등 crossnotics.css 스타일이 그대로 적용되는 것 확인.
- 유료 티어(SINGLE) 선택 → 이름ㆍ이메일 입력 → 궁합 토글 켜기(관계유형 select 정상 노출
  확인) → 폼 제출 → **입금 안내 모달이 정상적으로 뜨는 것까지 확인**(실제 Google Apps
  Script 엔드포인트로 네트워크 요청을 보내는 단계 직전에서 멈춤 — 실제 배포된 엔드포인트에
  진짜 요청을 보내면 운영자에게 실제 이메일이 갈 수 있어 의도적으로 거기까지는 테스트 안 함).
- `node test/run-all.js` 재확인 통과.
- 저장소 전체 U+3186(가운뎃점 오타) 재확인 — 없음.

이제 -11번 "다음에 이어서 할 일"의 4개 항목 중 **완료**: crossnotics/index.html·privacy.html
전환, 개인정보처리방침(다른 세션이 이미 처리). **여전히 남음**: 파비콘ㆍGoogle Analytics
분리(계정 작업 필요), URL 경로(`/crossnotics/`) 자체 분리(완전 별도 저장소 전환은 아직 안
함, 원하면 그때 다시 논의).

## -11. 2026-08-23 업데이트 — 서비스허브와 완전 분리(사용자 지시: "연결된 모든 것을 끊어라")

사용자가 pdf_kit.py 공유 이유를 묻다가, "애초에 천지인운명관은 서비스허브와 별개로 제대로 된
사주 사이트를 만들겠다고 시작한 것이니 지금이라도 완전히 분리하라"고 명확히 지시함. 확인
질문(AskUserQuestion)으로 범위를 좁힘 — **①같은 저장소ㆍ같은 배포 URL(ekdrmf-cell.github.io/
crossnotics/) 유지, 코드만 완전 독립(사용자가 "2번" 선택ㆍ화면에 보이는 사이트 이름은 이미
전부 "천지인운명관"이라 이 조건 만족 확인함) ②동시에 다른 세션이 crossnotics/index.html
ㆍcrossnotics/css/crossnotics.css를 수정 중이라 그 두 파일은 "일단 대기"(그 세션이 끝날 때까지
건드리지 않되, 충돌 없는 나머지는 지금 바로 진행)로 확정.**

### 1. 천지인운명관 전용 공유 자산 신설 (crossnotics/js/, crossnotics/css/)

- `crossnotics/js/config.js` — 서비스허브 js/config.js의 독립 사본(연락처ㆍ결제안내ㆍ
  contactMail/contactPurchase/showPaymentGuide).
- `crossnotics/js/common.js` — 서비스허브 js/common.js를 그대로 복제하지 않고 **새로 작성**:
  브랜드명 "천지인운명관", 내비게이션(홈/무료 도구/신청하기), FAQ 챗봇 내용을
  question_taxonomy.md를 참고해 천지인운명관 전용으로 재작성(서비스허브의 게임ㆍ전자책ㆍ
  서비스 안내가 더 이상 안 나옴).
- `crossnotics/css/base.css` — 서비스허브 css/style.css(942줄)를 그대로 복제한 독립 사본.
- `crossnotics/js/unse-data.js` — 서비스허브 js/unse-data.js(운세 도구 목록, 내용 전체가
  천지인운명관 전용이었음)를 **이전**(복제 아님, 원본 삭제) — 두 사이트에 나눠 가질 이유가
  없는 데이터였음.

### 2. 무료 도구 7개(saju/gunghap/tarot/dream/name/bloodtype/unse) 배관 교체

각 `index.html`의 `<link rel="stylesheet" href="../css/style.css">` → `../crossnotics/css/
base.css`, `<script src="../js/config.js">`/`js/common.js` → `../crossnotics/js/` 아래
사본으로 교체. `data-active="saju"`(전부 똑같이 saju였음, 기존 오타 겸 방치됐던 부분) →
`data-active="tools"`로 통일. `<title>` 태그의 "— 서비스허브"도 전부 "— 천지인운명관"으로
수정. 브라우저로 4개 페이지(saju/dream/name/gunghap) 실제 폼 제출까지 확인 — 헤더ㆍ푸터
브랜드명ㆍ내비게이션ㆍFAQ봇 전부 천지인운명관으로 정상 표시됨.

### 3. PDF 엔진 완전 분리 (`tools/crossnotics-report/pdf_kit.py` 신규)

-10번에서 `products/_shared/pdf_kit.py`(전자책 13종과 공유)에 "선택적 파라미터"로 추가했던
크로스노틱스 전용 기능(accent/accent2, brand_emblem)을 **전부 되돌리고**, 그 기능을 포함한
완전한 사본을 `tools/crossnotics-report/pdf_kit.py`로 새로 만듦(author 기본값도 "천지인운명관"
으로, watermark_text 기본값도 "천지인운명관 · ..."으로). 폰트도 `tools/crossnotics-report/
fonts/`에 별도 복사(Pretendard 6종) — 이제 SHARED_DIR이 이 폴더 자신을 가리켜 완전히
독립적으로 동작함. `report_kit.py`의 import 경로도 `products/_shared`에서 로컬 파일로 변경.
**격리 테스트로 양쪽 다 확인**: 로컬 pdf_kit.py로 크로스노틱스 PDF 빌드 성공(3페이지), 되돌린
공유 pdf_kit.py로 회귀 테스트 PDF 빌드 성공(2페이지) — 서로 전혀 참조하지 않음 확인.

### 4. 가격표 분리 (`tools/crossnotics-engine/catalog.js` 신규)

`site-checkout/lib/catalog.js`에 있던 `CROSSNOTICS_TIERS`ㆍ`getCrossnoticsTierConfig`를
`tools/crossnotics-engine/catalog.js`로 통째로 옮김(EBOOKS/SERVICES/getProduct/productType은
site-checkout 쪽에 그대로 남김). `run.js`의 require 경로도 로컬 파일로 변경. `productType()`의
"crossnotics" 분기도 제거(더 이상 site-checkout이 처리할 상품 타입이 아님).
**site-checkout/lib/route-product.js의 `fulfillCrossnotics()` 함수 전체를 제거** — 원래
`NOT_IMPLEMENTED` 스텁이었고 카드결제 자동화 자체가 아직 배포 전(계좌이체 수동 확인만
씀)이라 지금 당장 영향받는 실사용은 없음. **천지인운명관이 카드결제 자동화가 필요해지면
site-checkout을 공유하지 말고 별도로 새로 만들 것.**

### 5. 서비스허브 쪽에서 천지인운명관을 홍보ㆍ링크하던 곳 전부 제거

grep으로 찾은 실제 잔여 연결 3곳을 발견해 제거:
- `index.html`(서비스허브 홈) — "운세" 섹션(featured-unse 카드 3개), 히어로 통계의 "무료
  운세 도구 6개" 항목, `<script src="js/unse-data.js">` 전부 제거.
- `services.html` — "천지인운명관 — 사주ㆍ별자리ㆍ타로 교차진단" 상품 카드(5~15만원 표기,
  다른 실제 서비스 상품들과 나란히 판매중으로 노출되고 있었음) 전체 제거.
- `js/search-data.js` — 사이트 전체 검색 인덱스에 있던 운세 도구 6개 항목(사주ㆍ궁합ㆍ타로ㆍ
  꿈해몽ㆍ혈액형ㆍ이름풀이) 전부 제거.
- `js/common.js`(서비스허브 자체 공용 헤더/FAQ) — 내비게이션의 "운세" 링크, FAQ 챗봇의
  "운세 도구도 결제해야 하나요?" 항목 제거.

브라우저로 서비스허브 홈ㆍservices.html을 직접 열어 콘솔 에러 없음ㆍ운세 관련 요소가 실제로
안 남아있음(`document.getElementById('featured-unse')` → null)을 확인.

### 검증

- `node tools/crossnotics-engine/test/run-all.js` 통과(새 catalog.js 사용).
- `python -c "import ast; ast.parse(...)"`로 로컬ㆍ공유 pdf_kit.py 둘 다 문법 확인.
- 로컬 서버로 서비스허브 홈/services.html/unse 허브, 그리고 무료 도구 4개(saju/dream/name/
  gunghap)까지 전부 브라우저로 직접 열어 실제 동작(폼 제출, 결과 표시, 업셀 링크, 헤더ㆍ푸터
  브랜드명) 확인.
- 저장소 전체를 U+3186(가운뎃점 대신 반복적으로 잘못 입력되는 한글 자모) 문자로 다시 grep해
  이번 세션에서도 재발한 것을 발견ㆍ전부 제거 확인.

### 다음에 이어서 할 일 (남겨둠, 이번 세션에서 결정하지 않음)

- **crossnotics/index.html ㆍ crossnotics/css/crossnotics.css 전환** — 다른 세션의
  다크ㆍ골드 리디자인 작업이 끝나면, 그 두 파일도 `../css/style.css`/`../js/config.js`/
  `../js/common.js` 대신 `crossnotics/css/base.css`(또는 새로 만들 전용 CSS)ㆍ`crossnotics/
  js/config.js`ㆍ`crossnotics/js/common.js`를 쓰도록 바꿔야 분리가 완성됨. **지금은 이
  두 파일만 아직 서비스허브 공유 경로를 그대로 쓰고 있음(사용자 지시로 의도적으로 보류).**
- **개인정보처리방침** — `crossnotics/js/common.js`의 푸터가 여전히 서비스허브의
  `privacy.html`을 가리키고 있음(`${root}privacy.html`). 천지인운명관은 생년월일시ㆍ질문
  내용ㆍ결제정보 등 서비스허브(전자책 쇼핑몰)와는 다른 개인정보를 수집하므로, 완전히
  분리하려면 천지인운명관 전용 개인정보처리방침 페이지가 필요할 수 있음(법적 문서라
  임의로 새로 쓰지 않고 다음에 사용자 확인 후 작성할 것).
- **파비콘ㆍGoogle Analytics** — favicon.svg/apple-touch-icon.png와 GA 추적 ID
  (G-NR3D3FD597)는 아직 공유 중. 파비콘은 브랜드 아이덴티티 문제라 원하면 천지인운명관
  전용으로 새로 만들 수 있고, GA는 별도 속성(계정)을 새로 만들어야 분리 가능(사용자의
  구글 계정 작업 필요) — 둘 다 이번 세션 범위 밖으로 남겨둠.
- **URL 경로("crossnotics")** — 사이트 "이름"은 이미 전부 천지인운명관이지만, 배포 경로
  자체는 여전히 `/crossnotics/`. 사용자가 이후 URL까지 바꾸고 싶다면(예: 완전 별도 저장소로
  독립) 처음 확인했던 "완전 독립(새 저장소+새 주소)" 옵션으로 다시 전환 가능.

## -10. 2026-08-23 업데이트 — 무료 도구 콘텐츠 확장ㆍPDF 브랜딩ㆍ마케팅 전략 메모 (-9번 이후
계속 진행, "끝에 다다를 때까지 끊임없이 넓혀"라는 사용자 지시에 따라 사주 인접 영역까지 확장)

### 1. 무료 도구 콘텐츠 확장

- `dream/js/dream-data.js` — 꿈해몽 사전 24개 → **82개**(동물ㆍ신체ㆍ자연ㆍ장소ㆍ물건ㆍ식물ㆍ
  사람ㆍ행동ㆍ숫자색깔 카테고리 추가). 국내 전통 해몽에서 널리 통용되는 상징을 리서치(2026-08-23
  WebSearch)해서 새로 집필, 기존 24개와 같은 톤 유지. `node --check` 통과ㆍ`searchDream()`
  실제 호출로 82개 로드ㆍ검색 정상 동작 확인.
- `bloodtype/index.html` — 4개 항목(성격+최고궁합 한 줄)만 있던 걸 연애ㆍ직장ㆍ스트레스
  대처법 + **4개 혈액형 전부와의 궁합**(기존엔 "잘 맞는 상대" 1개만)으로 확장. 일본 혈액형
  성격론은 학문적 근거가 약하다는 게 정설이라 "전통적으로 통용되는 대중문화" 톤 유지.
- **명리학 대응표(correspondence.js)ㆍ궁합 엔진(gunghap.js)ㆍ신살(shensha.js) 자체는
  이미 -8ㆍ-9번에서 완성** — 이번엔 그 옆의 무료 도구 콘텐츠 깊이를 넓힌 것.
- 타로(`tarot/js/tarot-data.js`, 78장 전체 이미 완비)는 점검만 하고 추가 작업 없음 확인(-9번 4절).

### 2. PDF 퀄리티 개선 — "고급스럽게" 요청 반영

**`products/_shared/pdf_kit.py`(13종 전자책과 공유하는 파일)를 선택적(optional, 기본값 None)
파라미터만 추가하는 방식으로 확장** — 기존 호출부가 안 바뀌면 100% 예전과 동일하게 동작:
- `chapter_header(accent=None, accent2=None)` 신설 — 크로스노틱스가 체계별로 다른 배지 색을
  쓸 수 있게 함.
- `build(brand_emblem=None)` 신설 — (색1,색2,색3)을 주면 표지 오른쪽 위에 웹 로고와 동일한
  3원 겹침 엠블럼을 그림.
- **회귀 검증**: 격리 테스트(새 파라미터 없이 `PDFKit` 호출) 정상 빌드 확인, 기존 전자책
  (`youtube-monetization-guide/build_pdf.py`)을 실제로 실행해 `k.build()`까지 에러 없이
  도달하는 것 확인(마지막 파일 저장 단계에서만 실패했는데, 원인은 스크립트에 하드코딩된
  다른 컴퓨터의 사용자 경로(`C:\Users\nalla\...`) — 이번 세션과 무관한 기존 버그라 손대지
  않음).

**`tools/crossnotics-report/report_kit.py`**:
- `SYSTEM_ACCENT`(사주=#e8562f 주황ㆍ별자리=#6d4aff 보라ㆍ타로=#0a7d5e 초록 — 웹 로고
  `<svg class="logo-mark">`의 원 색과 정확히 동일)를 `chapter_header()`에 전달해 체계별
  챕터가 색으로 바로 구분되게 함. cross_analysis는 골드(#a67c1e, "종합"을 뜻함).
- `k.build(brand_emblem=CROSSNOTICS_EMBLEM, watermark_text="천지인운명관 · ...")` —
  **watermark_text를 명시적으로 오버라이드하지 않으면 기본값이 "서비스허브"(상위 우산
  브랜드)라서, 표지엔 "CHUNJIIN PERSONAL REPORT"라고 써놓고 워터마크는 다른 브랜드명이
  반복되는 불일치가 실제로 있었음 — pypdfium2로 실제 렌더링해서 시각 확인 중 발견.**
- 신살(shensha) callout_box의 `found_in`이 "year"/"month"/"day"/"hour" 영문 키를 그대로
  노출하던 버그도 같은 시각 점검에서 발견ㆍ수정(년주/월주/일주/시주로 번역).

**검증 방법(중요 — 처음으로 실제 PDF를 눈으로 봄)**: `pymupdf`가 이 컴퓨터에서 DLL 로드
실패로 안 됐고(`pip install --force-reinstall`로도 미해결, VC++ 재배포 패키지 문제로 추정,
더 안 팠음), 대신 **`pypdfium2`(프리빌드 wheel이 안정적으로 동작)로 mock PDF를 실제
PNG로 렌더링해 Read 도구로 시각 확인** — 이번 세션 전까지는 텍스트 추출로만 검증했었는데,
이번에 처음으로 색ㆍ레이아웃ㆍ엠블럼 배치까지 실제로 눈으로 봤고 그 결과 위 두 버그(워터마크
브랜드명ㆍ신살 영문 키)를 잡아냄 — **다음 세션도 디자인 관련 변경은 텍스트 추출만으로
끝내지 말고 pypdfium2로 실제 렌더링해서 볼 것.**

### 3. `tools/crossnotics-report/knowledge/sales_marketing_strategy.md` 신규 — 판매ㆍ마케팅 전략 메모

사용자가 "판매는 어떻게 할지 생각해보라"고 요청 → 기존 계획(성장엔진 원안ㆍ운영가이드ㆍ
`MARKETING_HANDOFF.md`)을 재작성하지 않고, **이번 세션에 새로 생긴 기능(궁합ㆍ신살ㆍ대응표)이
기존 홍보 자료(이미 완성된 `marketing/drafts/blog/naver/20260821_crossnotics.md`, 아직
미발행)에 반영이 안 됐다는 것**과 **가격 비교표에 정직하게 추가할 수 있게 된 항목**을
중심으로 정리. 후기 0건 문제에 대한 "베타 체험가로 실제 후기 받기(가짜 후기 금지 원칙은
유지)" 제안도 포함.

### 4. 무료 도구 → 크로스노틱스 업셀 CTA 실태 점검 (3번 메모에서 예고한 것을 바로 실행)

grep으로 확인한 결과 **saju/tarot에만 실제로 `crossnotics/index.html`로 연결되는 업셀이
있었고, dream/name/gunghap(무료)은 `contactPurchase()`(구식 이메일 문의 팝업)로 연결되고
있었으며, bloodtype은 업셀 자체가 아예 없었음**(성장엔진 계획서의 "무료 도구 결과 화면에
업셀 CTA" 의도와 실제 구현 사이의 간극 — 이번에 발견). 네 파일 전부 saju/tarot와 동일한
패턴(`<a href="../crossnotics/index.html">천지인운명관에서 자세히 보기</a>`)으로 통일하고,
낡은 `contactPurchase()` 클릭 핸들러는 제거함(CSS `.upsell-card a#upsell-btn` 셀렉터가
이미 준비되어 있어서 스타일 깨짐 없음). 브라우저로 4개 페이지 전부 실제 폼 제출 → 업셀
링크가 `../crossnotics/index.html`을 정확히 가리키는지 JS로 직접 확인.

### 검증

- `node tools/crossnotics-engine/test/run-all.js` 통과(4개 케이스).
- `python -c "import ast; ast.parse(...)"`로 `build_report.py`ㆍ`report_kit.py`ㆍ`pdf_kit.py`
  전부 문법 확인.
- 로컬 서버(`python -m http.server`)로 bloodtype/dream/name/gunghap 4개 페이지를 브라우저로
  직접 열어 콘솔 에러 없음ㆍ결과 정상 표시ㆍ업셀 링크 정확함을 확인.
- 저장소 전체를 U+3186(편집 중 가운뎃점 U+318D 대신 반복적으로 잘못 입력된 한글 자모) 문자로
  다시 grep해 전부 제거 확인(이번에도 여러 파일에서 재발 — 다음 세션도 편집 후 이 문자를
  한 번 grep해보는 습관을 들일 것).

### 다음에 이어서 할 일 (남겨둠)

- `sales_marketing_strategy.md` 6번 "다음 세션이 결정해야 할 것" 참고(로테이션 시작 여부,
  베타 후기 수집 여부, 블로그 초안 반영 여부).
- pymupdf DLL 문제 — 필요해지면 Visual C++ 재배포 패키지 설치 여부부터 확인. 지금은
  pypdfium2로 대체 가능해서 급하지 않음.
- 랜딩페이지 담당 세션(동시 진행 중, 다크ㆍ골드 리디자인)과 "가격 비교표에 궁합ㆍ신살 항목
  추가" 반영 여부 조율 필요.

## -9. 2026-08-23 업데이트 — 지식베이스 2차 확장(신살ㆍ궁합 관계유형ㆍ점성술 대응표) — "상품화는
나중, 지금은 어떤 질문이 와도 대응 가능한 방대한 데이터베이스 구축이 우선"이라는 사용자
방향 확정 후 진행

-8번 작업 직후 사용자가 "왜 신살ㆍ관계유형을 사용자 판단이 필요하다고 미뤘냐"고 지적함 —
돌아보니 신살은 "판단 필요"가 아니라 "라이브러리 지원 여부 미확인 + 세션 범위상 보류"였고,
관계유형(동업ㆍ가족 궁합)은 애초에 손님이 어떤 질문을 할지 막지 않는 이 서비스 설계상
**질문에 답하기 위해 반드시 필요한 것**이지 나중에 결정할 마케팅 문제가 아니었음(사용자가
직접 지적: "데이터베이스를 구축하려는 이유와 같다"). 이어서 사용자가 "상품화ㆍ가격 결정은
나중 일이고, 지금은 사주와 유사한 모든 것을 총망라한 데이터베이스 구축이 목표"라고 명확히
방향을 확정 → 그 방향에 따라 세 가지를 추가로 구현.

### 1. `tools/crossnotics-engine/shensha.js` 신규 — 신살(도화ㆍ역마ㆍ화개ㆍ홍염) 계산

lunar-javascript(EightChar API)에 이 네 신살을 계산하는 메서드가 없음을 코드 직접 확인
(라이브러리에 `sn.*` 신살 상수가 있지만 이는 택일용 황력(通勝) 신살이지 사주 명리학의
도화ㆍ역마ㆍ화개ㆍ홍염살이 아님) → 삼합 그룹 기준 고정 지지 표(도화ㆍ역마ㆍ화개)와 일간
기준 표(홍염)를 직접 구현. 2026-08-23 WebSearch로 sajustudy.com/namu.wiki/daysaju.com
교차확인(홍염살은 갑ㆍ경ㆍ임 일간이 지지 2개를 함께 보는 "국내 실무 표"를 채택 —
namu.wiki가 언급한 변형과 daysaju.com의 완전한 10간 표가 서로 모순 없이 겹침을 확인).
일지 기준을 기본으로 삼고 년지 기준(고전식)은 `by_year_branch`에 참고용으로 병기.
`saju.js`의 `computeSaju()`가 `result.shensha`로 자동 포함. `report_kit.py`의 "종합
지표" 페이지에 "이 손님 사주에 있는 신살" callout_box 추가(present인 것만 나열, LLM 개입
없음).

### 2. `gunghap.js` — relationshipType(연인ㆍ동업ㆍ가족) 파라미터화

`computeGunghap(sajuA, sajuB, relationshipType)` 3번째 인자 신설(기본값 "romantic").
**점수 산출 공식(WEIGHT)은 관계 유형과 무관하게 동일** — 관계 유형별로 가중치 자체를
다르게 매길 명확한 학설적 근거까지는 확인하지 못했기 때문. 대신 **해석 문구(highlights)
만 관계 유형별로 분기**: business는 "배우자 자리" 대신 "생활 리듬을 보는 일지"로, 일간
비화(같은 오행)는 "성향이 비슷함"이 아니라 "같은 오행끼리는 자원ㆍ주도권을 두고 경쟁하는
비겁 관계로 흐르기 쉬우니 역할ㆍ지분을 명확히 나누는 게 중요"로 재해석(명리학에서 동업
궁합을 볼 때 비겁 과다를 재물 다툼 위험으로 보는 통설 반영). family는 disclaimer 필드가
자동으로 채워져 "이 점수는 잘 맞는지 판정이 아니라 기질 차이 이해용 참고자료"라는 안내가
붙음(가족은 선택해서 맺는 관계가 아니므로). `run.js`가 `intake.customer.partner.
relationship_type`을 그대로 전달, `crossnotics/index.html`에 "상대방과의 관계"
선택지(연인ㆍ부부 / 동업ㆍ사업 파트너 / 가족ㆍ기타) 추가, `build_report.py` SYSTEM_PROMPT
10-B번에 관계 유형별 톤 유지 지시 추가.

### 3. `tools/crossnotics-engine/astrology-correspondence.js` 신규 — 점성술 대응표 지식베이스

saju쪽 `correspondence.js`와 완전히 같은 이유로 신설 — `astrology.js`는 지금까지 별자리ㆍ
행성ㆍ하우스ㆍ어스펙트의 "이름 번역"만 있었고 "의미" 사전이 전혀 없었음(같은 유형의 구멍이
점성술 쪽에도 그대로 있었던 것). 서양 점성술의 표준 상징 체계(별자리 12개 기질, 행성 10개
상징, 하우스 12개 삶의 영역, 어스펙트 5종 관계)를 정리 — 명리학 지지 합충형파해보다 유파
간 이견이 훨씬 적은 편이지만 "전통적으로 여겨지는 상징" 톤은 동일하게 유지. `buildAstroCorrespondence()`
가 이 손님 차트에 **실제로 등장한 행성ㆍ하우스ㆍ어스펙트만** 걸러서 반환(saju쪽과 동일한
필터링 원칙). `astrology.js`의 `computeAstrology()`가 `result.correspondence`로 자동
포함. `build_report.py` SYSTEM_PROMPT 10-D번 추가.

### 4. `tarot.js`/`tarot-data.js` 점검 결과 — 추가 작업 불필요

"총망라" 방향에 맞춰 타로 쪽에도 같은 유형의 구멍이 있는지 점검함 — 78장 전체(메이저22+
마이너56) 카드마다 keyword/text가 이미 전부 집필되어 있고(2026-08-21 완료분), 뽑힌 카드는
`computed.tarot.draws`로 이미 direct 답변 가능한 구조라 **추가 작업 없음**으로 확인.

### 검증

- `node tools/crossnotics-engine/test/run-all.js` — 기존 4개 케이스 전부 통과(shensha/
  astrology.correspondence 필드가 자동으로 채워지는 것 확인).
- `shensha.js`를 실제 생년월일로 직접 호출해 도화ㆍ역마ㆍ화개ㆍ홍염 판정이 삼합/일간 표와
  일치하는지 확인 — 일지가 진술축미(화개 지지)인 손님은 "일지 자신이 곧 화개살"이 되는
  자기지시적 케이스가 실제로 나왔는데, 이건 버그가 아니라 명리학에서 실제로 언급되는
  "일지 화개" 패턴과 일치함을 확인.
- `gunghap.js`를 romantic/business/family 세 관계 유형으로 직접 호출해 문구가 올바르게
  분기되는지, family에서 disclaimer가 채워지는지 확인.
- `astrology-correspondence.js`를 dual 티어 샘플로 확인 — planet_meanings/house_meanings/
  aspect_meanings가 이 손님 차트에 실제 등장한 것만 담겨 반환됨을 확인.
- `python -c "import ast; ast.parse(...)"`로 build_report.py 문법 오류 없음 확인(SYSTEM_PROMPT
  안에 10-D번 추가 후에도 파싱 정상).
- 오타 발견ㆍ수정: 편집 도중 가운뎃점(U+318D) 대신 U+3186(다른 한글 자모, 오타)를
  반복적으로 잘못 입력한 걸 발견 — 전체 저장소를 grep해서 남김없이 수정함(index.html,
  run.js, gunghap.js, astrology-correspondence.js, question_taxonomy.md).

### 다음에 이어서 할 일 (남겨둠)

- 점성술 시너스트리(궁합용 점성술) — 지금 gunghap.js는 사주 궁합만 계산함, 점성술까지
  다루려면 상대방 위경도 입력 + synastry 어스펙트 계산이 추가로 필요.
- 무료 도구(`bloodtype/`ㆍ`dream/`ㆍ`name/`)는 크로스노틱스처럼 "질문에 direct로 답하는"
  구조 자체가 없는 별도 정적 도구라 이번 조사 범위 밖 — "총망라" 방향을 계속 넓힐 거면
  다음 세션에서 이 도구들의 데이터 깊이도 별도로 점검할 만함.
- 실제 API로 신살ㆍ궁합(3개 관계유형)ㆍ점성술 의미 질문이 포함된 리포트 최소 1건씩 생성해
  사람이 읽고 확인 — 여전히 API 비용 발생 항목이라 이 세션에서 호출 안 함(기존 원칙 유지).

## -8. 2026-08-23 업데이트 — 명리학 대응표 지식베이스 + 궁합 계산 엔진 신설(-7번 "다음에
이어서 할 일" 두 항목을 실제로 구현하고 배관까지 전부 연결)

사용자가 "고객 질문에 완벽하게 대처할 수 있도록 광범위한 질문 데이터베이스를 구축해달라"고
요청 → 웹 리서치로 실제 사주ㆍ타로 상담에서 나오는 질문 유형을 조사한 뒤, -7번에서 지적됐던
두 구멍(궁합 계산 엔진 없음, 명리학 대응표 지식베이스 없음)이 바로 이 요청의 핵심이라고
판단해 둘 다 실제로 구현했다. **계산만 만들고 끝내지 않고 saju.js/run.js/build_report.py/
crossnotics/index.html/report_kit.py까지 전부 연결해서 실제로 direct 답변이 나가게
만들었다** — 도중에 `C:\Users\ekdrm\OneDrive\Desktop\천지인운명관_사업운영가이드.md`라는
사업 운영 가이드 문서가 대화 중간에 등장했는데(사용자가 참고자료로 제시), 그 문서가 이
작업의 "마지막 연결"(폼 입력칸ㆍSYSTEM_PROMPT 연동ㆍPDF 시각화)이 아직 안 됐다고 적어둔
스냅샷이었던 것으로 보임 — 이번 세션에서 그 세 가지를 전부 마무리해서 더 이상 유효하지
않은 상태로 만듦(그 가이드 문서 자체는 손대지 않음, 사용자 소유 참고 문서이므로).

### 1. `tools/crossnotics-engine/correspondence.js` 신규 — 명리학 대응표 지식베이스

- 오행(목화토금수)별 색ㆍ방향ㆍ숫자ㆍ계절ㆍ신체장기ㆍ음식ㆍ직업ㆍ성격 대응표(2026-08-23
  WebSearch로 색/방향/숫자/계절은 다수 사이트 교차확인, 신체/음식/직업은 전통 오행학설의
  통설을 정리 — 학파에 따라 세부 표현이 다를 수 있는 "참고 상응표"임을 파일 상단에 명시).
- 12지지 띠(쥐~돼지) 특성 + 지지 관계표(육합ㆍ삼합ㆍ육충ㆍ형ㆍ육파ㆍ육해) — sajustudy.com
  등에서 정확한 짝을 확인(자축합/인해합/묘술합/진유합/사신합/오미합, 해묘미ㆍ인오술ㆍ
  사유축ㆍ신자진 삼합, 육충 6쌍, 삼형/자묘형/자형, 육파 6쌍, 육해 6쌍). **인해가 육합(합목)
  이면서 동시에 육파 표에도 등장하는 고전 명리학의 널리 알려진 모순**을 발견 — "합이
  파보다 우선한다"는 통설에 따라 합을 우선 적용하도록 `jijiRelation()`에 명시적으로 반영.
- 십신 10개ㆍ12운성 12개 "의미" 사전 — saju.js는 지금까지 한글 명칭 번역만 있었고 의미
  설명이 전혀 없었음(예: "정관"이라고만 나오고 그게 뭘 뜻하는지는 LLM이 알아서 채워야
  했음 — 검증 안 된 일반 지식 사용 위험). 이제 이 사전에서 조회만 하면 됨.
- `buildCorrespondence(sajuResult)` — saju.js의 computeSaju() 결과를 받아 **이 손님의
  실제 계산값(연지ㆍ우세오행ㆍ부족오행ㆍ네 기둥에 실제로 등장한 십신ㆍ12운성)만 키로
  조회**해서 반환 — 등장하지 않은 요소까지 나열하면 "이 손님과 무관한 일반 지식"이 되므로
  의도적으로 필터링함.
- `saju.js`의 `computeSaju()`가 반환 직전에 `result.correspondence = buildCorrespondence(result)`
  호출 — 모든 사주 계산 결과에 자동으로 포함됨(추가 입력 불필요).

### 2. `tools/crossnotics-engine/gunghap.js` 신규 — 사주 궁합 계산 엔진

- correlate.js와 동일한 설계 철학(결정론적 채점, LLM은 결과를 문장으로 번역만 함, 채점
  근거를 파일 상단에 문서화하고 "이 프로젝트의 v1 가설"임을 명시 — 명리학에 궁합을 보는
  여러 유파가 있어 절대적 정답이 없다는 걸 숨기지 않음).
- 4가지 요소를 종합: ①일간(日干) 오행 관계(결혼궁인 일주의 핵심, 가장 큰 비중) ②일지(日支)
  관계(배우자 자리, 합/충/형/파/해) ③년지(年支) 띠 관계(흔히 말하는 "띠 궁합", 보조 지표)
  ④오행 상호보완(한쪽 부족 오행을 상대가 채워주는지). 가중치는 `gunghap.js`의 `WEIGHT`
  상수에 문서화(파일 헤더 참고).
- `computeGunghap(sajuA, sajuB)` — 점수(0~100)ㆍ점수 라벨ㆍ근거별 상세ㆍhighlights(자연어
  문장 배열) 반환. `computeGunghapFromPartnerInput()`은 raw 상대방 입력을 받아 사주 계산부터
  이어서 처리하는 편의 함수(run.js가 이걸 안 쓰고 직접 조합해서 씀, 이유는 아래 3번).

### 3. 배관 연결(engine → run.js → build_report.py → index.html → report_kit.py)

- **`run.js`**: `intake.customer.partner`(상대방 생년월일시ㆍ성별ㆍ음양력)가 있고
  `systems_included`에 saju가 있으면, 상대방 사주까지 계산해 `computed.json`에
  `partner_saju`ㆍ`gunghap` 필드를 추가. 음력 변환은 손님 본인과 동일하게
  `resolveSolarDate()`를 상대방 입력에도 별도로 적용(음력 상대방도 정확히 계산됨).
- **`build_report.py` SYSTEM_PROMPT**: 10-A번(correspondence 필드로 띠ㆍ오행생활ㆍ십신ㆍ
  12운성 "의미" 질문이 direct로 승격됨)ㆍ10-B번(gunghap 필드가 있으면 궁합 질문도 direct로
  승격, 없으면 여전히 redirected로 판정하되 상대방 정보 없다는 이유를 먼저 밝히도록 명시)
  규칙 추가. **10번 규칙의 기존 위장 금지 원칙과 완전히 동일한 톤을 유지** — 새 규칙이
  기존 원칙과 충돌하지 않게 신중히 작성함.
- **`crossnotics/index.html`**: "궁합이 궁금해요" 체크박스(모든 티어에 공통 노출, 특정
  티어로 제한하지 않음 — -7번의 "질문 입력 자체는 절대 막지 않는다" 원칙과 같은 선상에서,
  궁합 상대방 정보 입력도 티어로 막을 이유가 없다고 판단). 체크하면 상대방 생년월일시(양력/
  음력/음력윤달, 시간 모름 옵션, 성별) 입력칸이 나타나고, 제출 시 `intake.customer.partner`로
  실림 + 이메일 본문에도 상대방 정보 요약 줄이 추가됨(운영자가 계산 전 확인 가능).
- **`report_kit.py`**: "종합 지표" 페이지에 gunghap 필드가 있으면 궁합 점수를 `stat_hero`
  (예: "52점ㆍ무난함(장단점 공존)")로, highlights를 `callout_box`("궁합 근거")로 렌더 —
  사주 오행 분포ㆍ체계 일치도와 같은 방식(LLM 개입 없이 computed.json 실측값만 그림, 환각
  위험 0인 페이지라는 기존 설계 원칙 그대로 유지).

### 4. `tools/crossnotics-report/knowledge/question_taxonomy.md` 신규 — 질문 유형 리서치 문서

2026-08-23 WebSearch/WebFetch로 실제 사주ㆍ타로 커뮤니티ㆍ상담 가이드에서 확인한 질문
유형을 8개 카테고리(연애ㆍ결혼ㆍ직장이직ㆍ궁합ㆍ금전사업ㆍ건강ㆍ띠오행생활ㆍ타로특유질문)로
정리하고, 카테고리마다 "지금 direct로 답 가능한지"를 표시. 손님에게 노출되는 산출물이
아니라 내부 참고 자료(질문칸 예시 문구 다듬기ㆍSYSTEM_PROMPT 테스트 케이스ㆍ다음 확장 우선
순위 판단용). 신살(도화살ㆍ홍염살 등)이 saju.js에 아직 없어 연애운 질문 일부가 여전히
redirected/unanswerable로 남는다는 점을 다음 확장 후보로 기록해둠(9~10절 참고, lunar-
javascript의 EightChar API에 신살 계산 메서드가 있는지 다음 세션에서 확인 필요).

### 검증

- `node tools/crossnotics-engine/test/run-all.js` — 기존 3개 케이스(single/dual/master)
  + 신규 `sample-intake-gunghap.json`(상대방 정보 포함) 전부 통과, `out-gunghap.json`에
  `saju.correspondence`ㆍ`gunghap` 필드가 실제로 채워지는 것 확인.
- `correspondence.js`의 `jijiRelation()`을 자오(충)ㆍ인해(합/파 겹침, 합 우선 확인)ㆍ
  인사(형+해 동시 성립, 실제 고전 이론상 정상적인 중복임을 확인)ㆍ진진(자형)ㆍ자유(파)ㆍ
  자미(해) 등 알려진 조합으로 직접 호출해 결과가 이론과 일치하는지 확인.
- `report_kit.py`는 **실제 API를 부르지 않고**(기존 "API 테스트는 진짜 돈이 나간다" 원칙
  유지) `test/mock-report-single.json` + `out-gunghap.json`으로 PDF를 실제로 빌드 →
  pypdf로 텍스트 추출해 "궁합 점수"ㆍ"52점"ㆍ"궁합 근거"ㆍ각 highlight 문장이 전부 PDF
  안에 들어간 것 확인(검증용 PDF는 실제 손님 데이터가 아니라서 삭제함).
- `crossnotics/index.html`을 로컬 서버(`python -m http.server 8765`)로 띄워 브라우저로
  직접 "궁합이 궁금해요" 체크박스를 클릭 → 상대방 생년월일시ㆍ성별 입력칸이 정상적으로
  나타나는 것을 실제 화면에서 확인.

### 다음에 이어서 할 일 (남겨둠, 이번 세션에서 결정하지 않음)

- **신살(도화살ㆍ홍염살ㆍ역마살 등) 계산** — question_taxonomy.md 1절에서 확인했듯 연애운
  질문에서 자주 나옴. lunar-javascript EightChar API에 관련 메서드가 있는지 확인 후
  saju.js/correspondence.js 확장 검토.
- **궁합 관계 유형 파라미터화** — 지금 gunghap.js는 연인/부부 기준 가중치로 설계됨. 동업ㆍ
  가족 궁합은 재성/관성 비중을 다르게 보는 명리학 통설이 있어, 필요해지면 관계 유형
  파라미터를 추가하는 걸 고려할 수 있음(사용자 확인 없이 임의로 확장하지 않음).
- **실제 API로 궁합 포함 리포트 최소 1건 생성** — 지금까지 mock으로만 검증했으므로,
  실제 주문이 들어오거나 사용자가 확인용으로 승인하면 build_report.py의 10-A/10-B
  규칙이 실제로 잘 지켜지는지(위장하지 않는지, 톤이 자연스러운지) 사람이 읽어서 확인
  필요(API 비용 발생 항목이라 이 세션에서 실제 호출은 하지 않음 — 기존 원칙 유지).

## -7. 2026-08-23 업데이트 — 질문 답변 구조 재설계(direct/redirected/unanswerable 판정)

**배경 — 반드시 읽을 것.** 사용자가 "궁합ㆍ음식ㆍ띠별 운세 같은 질문에 완벽하게 답할 수
있냐"고 물어서 확인해본 결과, 실제로 구멍이 있었다(궁합은 상대방 정보가 없어 계산
불가능, 명리학 대응표 자체가 엔진에 없음). 이후 "그럼 답 못 하는 질문은 어떻게 하냐"를
두고 매우 긴 논의가 있었고, 결론은 다음 원칙으로 정리됨:
- **질문 입력 자체는 절대 막지 않는다** — 손님은 무엇이든 물을 수 있어야 함(질문 개수가
  상위 티어 가격을 정당화하는 핵심 가치이기 때문).
- **계산 근거가 없는 걸 있는 척 답하는 건 절대 안 됨**(기존 0번 원칙 그대로).
- **답을 못 준 사실을 숨기고 다른 걸 답인 척 위장하는 것도 안 됨** — 대신 "왜 문자 그대로는
  답 못 하는지"를 먼저 명확히 밝힌 뒤, 그 손님의 진짜 데이터로 답할 수 있는 가장 가까운
  내용을 별개로 붙인다.
- **"답 못 하는 질문이 얼마나 되는지"는 추측하지 않고 실측한다** — 이전에 "극소수일 것"이라고
  근거 없이 단정했던 걸 사용자가 지적함(맞는 지적이었음). 이제 실제 로그로 데이터를 쌓음.

### 스키마 변경 — `question_answer`(단일 객체) → `question_answers`(배열)

`build_report.py`의 REPORT_SCHEMA와 SYSTEM_PROMPT 10번 규칙을 전면 재설계:
- 질문마다 배열 항목 하나, 각 항목은 `question`(원문)ㆍ`answerability`(direct/redirected/
  unanswerable 중 하나, LLM이 먼저 스스로 판정)ㆍ`unanswerable_reason`(redirected/
  unanswerable일 때만)ㆍ`body`.
- **direct**: computed.json 데이터로 직접 답변 가능(이직운ㆍ연애운 등 대부분).
- **redirected**: 문자 그대로는 계산 불가(예: 상대방 정보 없는 궁합 질문)하지만, 그 뒤에
  있는 진짜 관심사는 이 손님 데이터로 부분적으로 답 가능 — 먼저 이유를 밝히고, 위장하지
  않고 이어서 답함.
- **unanswerable**: 어떤 방법으로도 이 손님 데이터로는 근거가 없는 질문(로또 번호, 정확한
  사망 시점 등) — 이유를 설명하고 절대 숫자ㆍ사실을 지어내지 않음.
- `check_hallucination()`도 새 배열 구조에 맞게 수정.

### `report_kit.py` 렌더링

`question_answers` 배열을 순회하며 질문마다 `Q1./Q2.../` 소제목을 붙이고, answerability가
redirected/unanswerable이면 `unanswerable_reason`을 `quote()`(강조 인용 박스)로 본문보다
먼저, 눈에 띄게 보여준 뒤 본문을 이어붙임 — **손님이 "이건 원래 질문과 다른 답이다"를
반드시 알 수 있게, 절대 숨기지 않는 게 핵심.**

### 질문 판정 로그 시스템 신설

- `build_report.py`에 `log_question_answerability()` 추가 — 리포트를 만들 때마다
  `question_answers`의 판정 결과를 `tools/crossnotics-report/logs/question_answerability_log.jsonl`
  에 append(질문 원문ㆍ판정ㆍ이유ㆍ티어ㆍ타임스탬프). **이 로그 폴더는 실제 고객 질문
  원문이 쌓이는 곳이라 `.gitignore`에 추가함(`tools/crossnotics-report/logs/`) — 절대
  커밋되면 안 됨.**
- `python build_report.py --log-summary` — 누적 로그에서 direct/redirected/unanswerable
  비율을 실제 숫자로 계산해서 보여줌. **주문이 실제로 쌓이면 주기적으로 이 명령을 돌려서
  "답 못 하는 질문이 실제로 몇 %인지" 확인할 것** — 추측하지 말 것.

### 다음에 이어서 할 일 (사용자와 논의했지만 아직 구현 안 함)

- **궁합 계산 엔진 신설** — 상대방 생년월일 입력을 받아 실제 사주 궁합(오행 상생상극,
  지지 합충형파해 등)ㆍ점성술 시너스트리를 계산하는 신규 모듈. 지금은 궁합 질문이
  전부 "redirected"로만 처리됨(본인 데이터 기반 부분 답변) — 이 엔진이 생기면 "direct"로
  승격됨. 어느 티어부터 열지는 사용자 확인 필요.
- **명리학 대응표 지식베이스** — 띠(결정론적, 쉬움), 오행별 색ㆍ방향ㆍ숫자ㆍ음식ㆍ신체장기ㆍ
  적합 직업. 지금은 이런 질문이 "direct"로 답하려면 LLM이 검증 안 된 일반 지식을 써야
  해서 위험함 — 실제 룩업 테이블을 `saju.js`나 별도 모듈에 추가해서 "direct"로 편입시킬 것.
- SYSTEM_PROMPT 규칙 5번(글의 질적 목표) 재검토 — 이번 논의에서 "해석의 유연성 vs 날조"의
  경계를 더 정확히 정의함(입력값에 추적 가능한가가 기준). 다음에 규칙 1번ㆍ5번 문구를 이
  기준으로 한 번 더 다듬으면 좋음(지금도 틀리진 않지만 이 대화의 최종 정의만큼 정교하진
  않음).

### 검증

목업 데이터(direct 1ㆍredirected 1ㆍunanswerable 1)로 PDF 빌드 → 3문항 전부 정상 렌더,
redirected/unanswerable 항목에 이유 문구가 본문 앞에 눈에 띄게 들어간 것 확인. 로그
파일도 정상 기록되고 `--log-summary`로 비율 계산되는 것까지 실제로 실행해서 확인함(테스트용
로그는 실제 데이터가 아니라서 삭제함). `node test/run-all.js` 회귀 통과.

## -6. 2026-08-23 업데이트 — 가격 차별화 명확화, 페이지 수 확정 표기, 티어 배지 이름 통일

사용자가 "가격대별 카드만 봐서는 뭐가 달라서 가격이 이렇게 차이나는지 모르겠다"고 지적,
연이어 페이지 수 표기의 "약ㆍ목표" 같은 애매한 표현을 없애라고 지시, 그리고 API 비용을
논할 때 정확한 원화 금액을 말하지 않은 것도 지적함. 마지막으로 대화 중 크로스노틱스
내부적으로 "싱글ㆍ마스터ㆍ프리미엄"이라고 부르는 이름을 사이트에도 실제 상품명으로
노출하라고 지시함(이전 세션에 "코드명 노출하지 말라"고 했던 것을 명시적으로 뒤집음).

### 1. 가격대별 비교표 신설 (`crossnotics/index.html`)

가격 카드 그리드 위에 `<table>` 형식의 비교표를 새로 추가(`#cn-compare-table`,
`renderCompareTable()`) — 행: 페이지 수ㆍ다루는 체계ㆍ대운 범위ㆍ질문 개수ㆍ기회ㆍ리스크
분석ㆍ실전 액션 플랜ㆍ장기 인생 전략. 6개 티어를 열로 나란히 놓아 "가격이 오를 때 정확히
뭐가 늘어나는지"를 한 번에 스캔 가능하게 함. 모바일에서는 `.cn-compare-scroll`
(overflow-x:auto)로 가로 스크롤.

### 2. 페이지 수 확정 표기로 전환

`catalog.js`ㆍ`crossnotics/index.html` 양쪽에서 `pages_note`/`pagesNote`에서 "약"ㆍ"목표"
전부 제거(예: "목표 약 20페이지" → "20페이지"). **이건 LLM 출력이 실제로 페이지 수를
정확히 보장한다는 뜻이 아니다** — `catalog.js` 주석에 명시해뒀듯, single 6pㆍdual 13pㆍ
master 20pㆍpremium 30p는 이제 "추정치"가 아니라 **상품이 지켜야 할 사양(spec)**으로
취급하고, 계획서가 이미 전제하는 "사람이 발송 전 결과물을 검증하는 단계"에서 실제
페이지 수가 이 사양에 못 미치면 재생성하거나 보강하는 걸로 책임진다 — 이 확인은 코드가
자동으로 강제하지 않으니, **다음에 실제 주문을 처리할 때 발송 전 체크리스트에 "페이지
수가 표시된 사양과 일치하는지" 항목을 반드시 넣을 것.**

### 3. API 비용 — 정확한 금액으로 말할 것 (사용자가 재차 지적, 다음 세션도 지킬 것)

크로스노틱스 리포트 1건 생성 시 실측 API 비용(2026-08-21 기준, `-0`번 섹션에도 있음):
**싱글 티어 약 33~50원, 마스터 티어 약 150~250원.** 프리미엄(20만원)은 분량이 더 커서
250~400원 선으로 추정(아직 실측 아님). **앞으로 "API 호출해볼까요?" 같은 제안을 할 때는
반드시 이 원화 숫자를 같이 말할 것 — "비용이 발생하는 항목이라..."처럼 얼버무리지 말 것.**

### 4. 티어 배지 이름(FREE/LIGHT/SINGLE/DUAL/MASTER/PREMIUM) 신설 — 내부 코드명 노출 금지
방침을 뒤집음

`tier` 필드 값(mini/light/single/dual/master/premium)을 대문자로 바꾼 걸 `label`
필드로 신설해서 `catalog.js`ㆍ`crossnotics/index.html`(카드 배지 + 비교표 헤더)ㆍ
`catalog_names.py`(PDF 표지 제목)까지 전부 동일하게 노출. **이전에 "손님에게 코드명
노출하지 말라"고 했던 결정을 사용자가 명시적으로 뒤집은 것** — `catalog.js`의 옛
코멘트를 지우지 않고 왜 바뀌었는지 남겨둠(다음 세션이 또 뒤집을까봐). 김에 PDF 표지
브랜드명도 "크로스노틱스"/"천지인운명관" 혼용되던 걸 "천지인운명관"으로 통일함(-4번에서
발견해 사용자 확인 대기 중이던 항목 — 이번 라벨 작업 하는 김에 같이 정리).

### 검증

`node test/run-all.js` 회귀 통과, `catalog.js`/`catalog_names.py` 문법 확인, 로컬
서버로 실제 페이지 열어 카드 배지(FREE~PREMIUM)ㆍ비교표 헤더에 라벨과 정확한 가격이
전부 정상 표시되는지 브라우저 JS로 직접 확인함.

## -5. 2026-08-22 업데이트 — 운명도감 실사용 벤치마킹(1~4번 도감 전체 열람) 후 반영

사용자가 "PDF 전부 확인하고 벤치마킹해서 저것보다 훨씬 좋게 만들라"고 지시함. claude-in-chrome로
사용자의 실제 Chrome(로그인된 세션)에 붙어 destinybook.co.kr의 실제 발행된 리포트를
1~4번(일별 인생 설계ㆍ주간 인생 설계ㆍ멘탈 관리 전략ㆍ비즈니스 파트너 전략, 전부 8페이지)
전부 끝까지 읽음 — 마케팅 목업이 아니라 실제 계정으로 생성된 리포트. **5번(월간 인생
설계)부터는 "이전 유료 도감을 먼저 결제해주세요" 안내가 떠서 막힘 — 남의 사이트에 실제
결제를 대신 하는 건 안 하는 게 맞다고 판단해 거기서 멈춤(다음에 사용자가 직접 결제하면
이어서 볼 수 있음).**

### 실사용에서 확인한 사실

1. **진짜 품질 버그 발견**: "심층 분석" 챕터가 4개 중 2개(멘탈 관리 전략ㆍ비즈니스 파트너
   전략)에서 챕터 제목만 있고 본문이 완전히 비어있었음(페이지 번호는 정상 출력됨). 유료
   판매 중인 제품에서도 이 정도 결함이 나가고 있다는 뜻 — 우리 QA가 실제 차별점이 될 수
   있음을 확인.
2. **지어낸 통계ㆍ예언이 일회성이 아니라 시스템적**: 4개 리포트 전부 예외 없이
   "COHORT INSIGHT: 동일 구조의 68%는..." 식 정밀한 %와 "SEALED PROPHECY: 이번 가을
   북쪽/서쪽에서 온 연락이..." 식 구체적 미래 예측이 들어있었음. 우리의 "지어내지 않는다"
   원칙이 왜 실질적 차별화인지 실제 경쟁사 제품에서 재확인.
3. **무료 4개**: destinybook은 8페이지짜리 리포트를 4개나 무료로 준 뒤 5번째부터 결제를
   요구함 — 저희 무료 티어(1개, 1페이지)보다 훨씬 후함. (지금 당장 우리 무료 티어를
   늘리라는 지시는 없었으므로 변경 안 함 — 다음에 논의할 사항으로만 기록.)
4. **가져올 만한 기법(전부 반영 완료, 아래 참고)**: 상황별 실제 대사 스크립트, 자문 질문
   ("결정 프레임"), 기회/리스크를 색으로 구분한 카드형 구성.

### 반영한 것 — `build_report.py` / `report_kit.py`

1. **opportunities(기회)ㆍrisks(리스크) 신규 스키마 필드** — SYSTEM_PROMPT 9-C번. scope
   full이면 opportunities 3~5개ㆍrisks 3~4개, mini/light는 null. **9-C번 안에 운명도감에서
   실제로 목격한 안티패턴(근거 없는 코호트 %, 구체적 미래 예언)을 명시적으로 금지하는
   문장을 넣음** — "1번 규칙 위반"이라고 못박아 재발 방지.
2. **action_plan에 scripts(대화 스크립트)ㆍreflection_questions(자문 질문) 추가** — 9-B번
   확장. scripts는 "상황+실제 대사" 쌍(2~4개, master/premium), reflection_questions는
   "질문+왜 중요한지"(2~3개, master/premium). 사실 주장이 아니라 제안이라 그대로 가져와도
   안전하지만, 리포트에서 이미 다룬 주제와 연결되어야 한다는 제약을 걸어 둠(엉뚱한 상황을
   지어내지 못하게).
3. **`check_hallucination()`에 "%" 문자 탐지 추가** — 우리 리포트 본문(LLM 작성분)엔
   원래 %가 나올 이유가 없음(체계 일치도 %는 report_kit.py가 computed.json에서 직접
   렌더링하지 LLM이 쓰지 않음). 본문에 %가 하나라도 있으면 경고를 띄우는 기계적 안전장치 —
   운명도감의 "68%는..." 패턴을 우리가 재현하고 있는지 자동으로 신호를 준다.
4. **report_kit.py 렌더링**: opportunities는 `tip_box`(파랑ㆍ✓ 아이콘)로 항목마다 별도
   박스, risks는 `warn_box`(주황ㆍ⚠ 아이콘)로 항목마다 별도 박스 — 프로즈에 묻지 않고
   색으로 한눈에 스캔되게 함("색깔로 가독성을 높여달라"는 요청에 대한 핵심 대응. tip_box/
   warn_box는 pdf_kit.py에 이미 있던 걸 이번에 처음 실제로 씀). scripts는 `pull_quote`(대사)
   + attribution(상황), reflection_questions는 `callout_box`(번호 매김)로 렌더.
5. **가독성용 타이포그래피 조정 — pdf_kit.py(공용, 전자책 13종 공유)는 안 건드리고, 이
   report_kit 인스턴스(`k`)의 스타일 딕셔너리만 국소 수정**: 본문 11.8pt→12.4pt, 줄간격
   20→21.5로 소폭 확대. `k.styles["body"].fontSize = ...` 식으로 인스턴스 속성만 바꾸는
   방식이라 다른 상품(전자책 등)에는 전혀 영향 없음 — 이게 이번 세션에서 찾은, pdf_kit.py를
   건드리지 않고도 리포트별로 룩앤필을 조정할 수 있는 재사용 가능한 패턴.

### 검증

목업 데이터(opportunities 5ㆍrisks 4ㆍscripts 3ㆍreflection_questions 2 포함, 이전
회차보다 더 풍부하게)로 premium PDF를 다시 빌드 → **21페이지**(이전 목업은 18페이지였음,
새 섹션들만으로 +3페이지). 새 요소(포착할 기회ㆍ예측 리스크ㆍ대화 스크립트ㆍ자문 질문)가
전부 텍스트 추출로 확인됨. `node test/run-all.js` 회귀도 그대로 통과. **여전히 진짜
API는 안 불렀음** — 목업 문장은 짧고 단조롭게 썼으므로 실제 LLM 결과물은 이보다 길 가능성이
높으나 30p는 확정 아님(카탈로그에도 "목표"로 표기돼 있음, -4번 참고).

## -4. 2026-08-22 업데이트 — 리포트 콘텐츠ㆍPDF 품질 전면 강화 (분량 6/13/20/30p 목표)

사용자가 운명도감 PDF 샘플(랜딩페이지 목업 이미지, 다운로드 가능한 실제 PDF는 없었음)을
참고해서 "우리 리포트가 그보다 훨씬 고급스럽고 퀄리티 높아야 한다ㆍ가격대비 분량이 너무
적다ㆍ읽고 나면 개안이 될 정도로 통찰이 깊어야 한다"고 지시함. -3번에서 만든 페이지수
표시(pages_note)가 실측 기준으로는 너무 작았다는 지적이기도 함(단독 3pㆍ마스터 8~10p였음).

**바뀐 목표 분량(-3번 값을 대체)**: 단독(5만) 6pㆍ듀얼(10만) 13pㆍ마스터(15만) 20pㆍ프리미엄
(20만) 30p. 미니(무료)ㆍ라이트(3만)는 의도적으로 짧은 진입상품이라 1p/2p 그대로 유지.
**주의: 이건 실측이 아니라 목표치다** — `catalog.js`/`index.html`의 pages_note에도 상위
4개 티어는 "목표 약 N페이지"로 명시(확정치처럼 말하지 않음). 실제 API로 첫 주문을 처리해
보면 그 결과로 다시 보정할 것.

### 1. `build_report.py` — SYSTEM_PROMPT를 "체계당 섹션 1개"에서 "체계당 3~4개 하위
섹션"으로 재설계

- 5번(글의 질적 목표) 규칙을 이 프롬프트에서 가장 중요한 규칙으로 승격 — "손님이 다 읽고
  나면 자신과 인생을 더 깊이 이해하게 됐다고 느껴야 한다"는 목표를 명시. 뻔한 운세 문구
  금지 목록, "계산값→성향/패턴→왜 그런지"로 한 겹 더 들어가라는 지시, key_insight를
  아포리즘 수준으로 쓰라는 지시 추가. 사용자가 "읽는 것만으로도 개안이 되고 머리가 맑아질
  정도"를 명시적으로 요구해서 이 부분을 프롬프트 최상단 수준으로 강조함.
- 8번(scope별 분량 기준)을 전면 재작성 — "사주 1섹션"이 아니라 tier/scope별로 몇 개의
  system_sections를 어떤 이름으로 나눌지 구체적으로 지정(예: master는 사주 4+점성술
  4+타로 3 = 11개 섹션 + cross_analysis + action_plan). 분량을 "억지로 문장 늘리기"가
  아니라 "더 많은 하위 주제로 구조화"로 채우게 유도 — 이래야 PDF에서도 소제목ㆍ강조박스가
  자주 나와 자연스럽게 페이지가 늘어남.
- 새 스키마 필드 추가: `system_sections[].key_insight`(섹션당 한 줄 핵심 인용구,
  pull_quote용), `system_sections[].takeaways`(2~4개 정리 불릿, summary_box용),
  `action_plan`(scope full-싱글 제외/premium, 실전 행동 3~5개, icon_steps용),
  `toc_preview`(scope full/premium, 목차 미리보기). 전부 optional/nullable이라 mini/light
  스코프는 예전처럼 짧게 유지됨.
- `check_hallucination()`이 새 필드(key_insight/takeaways/action_plan) 텍스트도 검사
  대상에 포함하도록 확장.
- `max_tokens` 32000 → 64000 — 30페이지 분량 프리미엄 리포트는 기존 한도로는 잘릴
  가능성이 높아서 미리 올림(실제 호출 안 해봐서 확정 아님, 잘리면 더 올릴 것).

### 2. `report_kit.py` — pdf_kit.py의 미사용 고급 컴포넌트를 실제로 사용하도록 재작성

핵심 발견: **"허술해 보인다"의 진짜 원인은 pdf_kit.py(전자책 13종에서 검증된 디자인
시스템)의 성능 부족이 아니라, report_kit.py가 그 도구의 절반도 안 쓰고 있었다는 것.**
`bar_row`/`stat_hero`/`flow_diagram`/`icon_steps`/`summary_box`/`pull_quote`가 전부
이미 있었는데 `stat_row`/`callout_box`/`body`만 쓰고 있었음. 이번에 추가:

- **목차 미리보기 페이지** — `toc_preview` 필드를 `toc_line`으로 나열.
- **"종합 지표" 페이지** — 여기가 핵심: **LLM 문장이 아니라 computed.json의 실측값만으로
  그린다** — 오행 5개ㆍ4원소 4개 분포를 `bar_row`(막대그래프)로, 체계 일치도(agreement_score,
  cross_correlation 모드일 때만)를 `stat_hero`(큰 숫자)로. 지어낼 게 없는 페이지라
  환각 위험이 0이면서도 운명도감의 "지표" 페이지처럼 데이터 밀도가 시각적으로 느껴짐.
- 섹션마다 `key_insight`는 `pull_quote`, `takeaways`는 그 섹션 끝에 `summary_box`로 렌더.
- `action_plan`은 `icon_steps`(번호 원+라벨+설명 가로 배치)로.
- `long_term_strategy`의 대운 8구간은 `flow_diagram`으로 타임라인 시각화한 뒤 산문
  본문(decade_roadmap 등)이 이어짐.
- 리포트 끝에 "한눈에 보기" — 전체 섹션의 key_insight를 다시 모아 `summary_box`로 정리
  (새 문장을 짓는 게 아니라 이미 나온 문장 재사용이라 환각 위험 추가 없음).
- `catalog_names.py`의 `tier_product_name`을 참고해 표지 상품명 그대로 사용, PDF kicker를
  "CROSS-NOTICS"에서 "CHUNJIIN"으로 맞춤(사이트 브랜드가 이미 천지인운명관이므로).

### 3. 검증 방법 — 실제 API 호출 없이 목업으로 구조 검증

**진짜 API는 안 불렀다(비용 발생 항목, 기존 원칙 유지).** 대신:
1. `node run.js`로 premium 티어 computed.json을 실제로 생성(진짜 saju.jsㆍ
   astrology.jsㆍtarot.js 계산값, LLM만 안 부름).
2. Python으로 새 스키마에 맞는 목업 report.json을 직접 작성(사주 4+점성술 4+타로 3=11개
   system_sections, cross_analysis, action_plan 4개, long_term_strategy 3부 — 대운
   8구간을 computed.json에서 그대로 가져와 각 구간 짧은 문단 생성).
3. `report_kit.build_pdf()`를 직접 호출해 PDF를 실제로 만들고 pypdf로 페이지 수 확인:
   **18페이지.** 이 목업 문장은 일부러 짧고 단조롭게 썼음(규칙 5번이 요구하는 "계산값→
   성향/패턴→왜 그런지" 깊이는 흉내 안 냄) — 실제 LLM 결과물은 이보다 길 가능성이 높지만,
   30p를 보장하진 못한다. 목차/종합지표(막대그래프)/한눈에보기/대운타임라인 등 새 렌더링
   요소가 전부 정상적으로 PDF에 들어가는지도 텍스트 추출로 확인함.
4. `node test/run-all.js`(기존 3개 티어 회귀) 통과 확인.
5. `crossnotics/index.html`을 로컬 서버로 띄워 가격 카드 6개의 페이지수 막대ㆍ텍스트가
   전부 새 목표치(1/2/6/13/20/30)로 정상 표시되는지 브라우저에서 직접 확인.

**다음에 반드시 할 일**: 실제 주문이 들어오면(또는 확인용으로 사용자가 승인하면) 진짜
API로 최소 1건은 돌려서 (a) 30p 근처까지 나오는지 (b) 규칙 5번의 "통찰 깊이" 요구가
실제로 지켜지는지(사람이 직접 읽어서 "뻔한 운세 문구"가 없는지) 확인할 것 — 프롬프트
지시만으로는 결과를 완전히 보장 못 함.

## -3. 2026-08-22 업데이트 — 미니 진단 무료화, 페이지수 표시, 20만원 프리미엄 신설

사용자 요청 3가지를 반영했다.

1. **"오늘의 사주 미니 진단"을 무료(0원)로 전환.** `site-checkout/lib/catalog.js`ㆍ
   `crossnotics/index.html`의 CN_TIERS 둘 다 price를 0으로 수정. 무료 티어는 계좌이체
   안내 팝업(`showPaymentGuide`)을 띄울 이유가 없어서, 제출 시 `tier.price === 0`이면
   `contactPurchase()` 대신 `contactMail()`을 바로 호출하도록 분기 추가(제목ㆍ본문도
   "신청"이 아니라 "무료 신청"으로 바뀜). 신청 버튼 문구도 티어 선택에 따라 "무료로
   받기" ↔ "신청하기 (입금 안내로 이동)"로 동적으로 바뀌게 `updateSubmitButton()` 추가.
2. **가격 카드마다 예상 PDF 분량(페이지 수)을 막대 시각화로 표시.** "가격대별로 전문성이
   얼마나 달라지는지 감각적으로" 보여달라는 요청 — **숫자를 지어내지 않고**
   `tools/crossnotics-report/test/`에 있던 실제 API 호출 결과 PDF의 페이지 수를 직접
   세어서 기준으로 삼음(2026-08-22 확인: `real-single-report.pdf`=3p,
   `real-master-report-v2/v4.pdf`=8p/10p). 그 사이ㆍ바깥 티어(라이트ㆍ듀얼ㆍ프리미엄)는
   체계 개수ㆍscope 깊이에 비례해 보간한 추정치라 "약 N페이지"로 표기하고 카드 아래
   "실측 기준 평균치, ±1~2페이지 차이 가능" 각주를 달아 확정치처럼 안 보이게 함. 값은
   `catalog.js`(`pages_note`/`pages_approx`)와 `index.html`의 CN_TIERS 양쪽에 수동으로
   맞춰 넣음(두 파일이 자동 동기화 안 되는 기존 구조 그대로 유지).
3. **crossnotics-premium(20만원, "장기 인생 전략 프리미엄") 신설.** 운명도감의 "10년
   인생 전략 설계ㆍ평생 인생 전략 설계ㆍ인생 2막 로드맵" 3개를 하나로 묶은 컨텐츠.
   - 새 계산 엔진 불필요 — `saju.js`가 이미 계산해주는 대운 8구간(`dae_yun`)을
     `build_report.py`가 scope="premium"일 때만 채우는 새 스키마 필드
     `long_term_strategy`(decade_roadmap/lifetime_design/second_act 3부분)로 더 깊이
     풀어 쓰는 방식 — SYSTEM_PROMPT 9-A번 규칙 참고. 8구간을 절대 빠뜨리지 말 것,
     "인생 2막"은 dae_yun의 실제 start_age 이후 구간에만 근거할 것(나이를 지어내지
     말 것)을 명시함.
   - `report_kit.py`의 `build_pdf()`에 `long_term_strategy` 렌더 블록 추가(대운 8구간을
     `callout_box`로도 병기) — **목업 report.json으로 실제 PDF를 빌드해서 6페이지가
     정상 생성되고 4개 텍스트 마커(10년 로드맵/평생 설계/인생 2막/대운 8구간 요약)가
     전부 PDF 안에 들어갔는지 직접 확인함**(진짜 LLM 호출은 비용 때문에 안 함 — API
     테스트 관련 기존 원칙 유지).
   - `run.js`의 타로 스프레드 분기(`intake.tier === "master"`)에 `"premium"`도 포함시켜
     프리미엄도 켈틱크로스 10장을 받도록 함.
   - `catalog_names.py`(PDF 표지 상품명)에 mini/light/premium 항목 추가 — 이전 세션에
     mini/light를 신설했을 때 이 파일에 등록을 빠뜨려서 지금까지 표지에 "크로스노틱스
     진단"(fallback)으로 나갔을 것으로 보임, 이번에 같이 수정함.
   - `crossnotics/index.html`의 리포트 미리보기 섹션에 "장기 인생 전략 프리미엄 전용"
     예시 블록(대운 1구간 발췌 + 안내문)을 추가로 넣어 20만원짜리만의 구성을 시각적으로
     보여줌.
   - **참고(고친 건 아님)**: `catalog_names.py`의 기존 3개 티어는 여전히 "크로스노틱스 —
     ..." 접두어를 쓰는데, 실제 사이트 브랜드는 이미 "천지인운명관"으로 바뀐 지 오래라
     불일치가 있음(새로 추가한 mini/light/premium은 "천지인운명관"으로 맞춰 넣음). 의도된
     것인지(영문 내부 코드명 유지) 아니면 리브랜딩 때 빠뜨린 건지 사용자에게 확인 후
     기존 3개도 통일할지 결정할 것.
   - `node test/run-all.js` 회귀 통과 확인.

## -2. 2026-08-22 업데이트 — 저가 진입 상품 2개 신설(1만원ㆍ3만원), 네비게이션 정리

사용자 요청으로 두 가지를 바꿨다.

1. **상단 네비게이션에서 "교차진단이란ㆍ리포트 예시ㆍ가치관" 링크를 없애고 "신청하기"만
   남김** — `crossnotics/index.html` 헤더 `<nav class="nav-links">`.
2. **1만원("오늘의 사주 미니 진단")ㆍ3만원("사주 라이트 진단") 티어 신설** — 기존
   최저가가 5만원이라 진입장벽이 높다는 지적. 단순히 5만원짜리를 반값에 파는 게 아니라
   **내용 깊이를 실제로 다르게** 해서 상위 티어를 잠식하지 않도록 설계함:
   - **1만원(mini, 질문 0개)**: 사주 네 기둥 간지+오행 우세만. 십신ㆍ지장간ㆍ12운성ㆍ
     공망ㆍ대운ㆍ세운은 계산은 되지만 리포트에 의도적으로 안 씀.
   - **3만원(light, 질문 1개)**: 사주 네 기둥 전체(십신ㆍ지장간ㆍ12운성ㆍ공망 포함)는
     다루되, 대운은 dae_yun 배열 전체가 아니라 **지금 나이 기준 현재 구간 하나만**.
     전체 대운 구간은 5만원(full) 티어부터.
   - 가격표 단일 소스인 `site-checkout/lib/catalog.js`의 `CROSSNOTICS_TIERS`에 새
     `scope` 필드(mini/light/full)를 추가해서 관리 — `run.js`가 `computed.json`에
     `scope`를 실어 보내고, `tools/crossnotics-report/build_report.py`의
     `SYSTEM_PROMPT`(8-A번 규칙)가 이 값을 보고 리포트 분량ㆍ깊이를 조절함. `saju.js`
     계산 자체는 티어 상관없이 항상 전체(대운 8구간 등)를 계산하고, "일부만 리포트에
     쓴다"는 프롬프트 지시로 깊이를 조절하는 방식 — 계산 엔진을 티어별로 분기하지 않아
     구조가 단순함.
   - `crossnotics/index.html`의 `CN_TIERS`(가격 카드용 JS 배열)도 catalog.js와 수동으로
     맞춰서 5개로 늘림 — **두 파일이 자동 동기화되지 않으니, 다음에 가격ㆍ티어를 또
     바꿀 때는 반드시 이 두 곳(`catalog.js`와 `crossnotics/index.html`) 둘 다 고칠 것.**
   - 질문 0개 티어를 고르면 "궁금한 점" 입력칸 대신 안내 문구가 뜨도록 `renderQuestions()`
     예외 처리 추가. 가격 카드 CSS를 3열 고정에서 `repeat(auto-fit, minmax(200px,1fr))`로
     바꿔 5장이 자연스럽게 줄바꿈되게 함.
   - `node run.js`로 mini/light 케이스ㆍ질문 초과 시 정상 에러ㆍ기존 3개 티어 회귀
     전부 실행 확인 완료(`test/run-all.js` 통과).
   - **다음에 할 일**: build_report.py의 8-A번 규칙은 프롬프트 지시일 뿐이라, 실제 API
     호출로 mini/light 리포트를 최소 1건씩 만들어 "정말 짧게/얕게 나오는지" 사람이 눈으로
     확인하는 절차가 아직 안 끝남(API 비용 발생 항목이라 이 세션에서 실제 호출은 안 함 —
     CROSSNOTICS_HANDOFF 0번 "결정 사항"의 "API 테스트는 진짜 돈이 나간다" 원칙에 따름).

## -1. 2026-08-22 업데이트 — 경쟁사(운명도감ㆍ포스텔러 만세력) 분석 후 정밀도ㆍ신뢰 보강

사용자 요청으로 운명도감(destinybook.co.kr)ㆍ포스텔러 만세력(pro.forceteller.com) 두 사이트를
직접 써보고 분석한 뒤, 크로스노틱스에 실제로 부족했던 부분 두 가지를 고쳤다.

1. **음력 생년월일 지원 추가(실제 계산 버그 수정)** — 포스텔러가 음력(윤달 포함) 입력을
   지원하는 걸 보고 확인했더니, 크로스노틱스 엔진(`saju.js`)은 입력받은 연월일을 무조건
   양력으로 취급하고 있었다. 즉 음력 생일을 가진 손님이 신청하면 사주가 통째로 틀리게
   계산되는 실제 버그였음(그동안 발견 안 된 이유: 실사용 테스트를 전부 양력 생일로만
   했었음). `saju.js`에 `resolveSolarDate()`를 추가해 lunar-javascript로 음력→양력 변환을
   하고, `run.js`가 변환을 한 번만 수행해 사주ㆍ점성술 두 엔진에 같은 양력 날짜를 넘기도록
   고쳤다(따로 변환하면 점성술만 양력인 척 음력 숫자를 그대로 써서 더 크게 틀어짐). 변환된
   날짜는 `lunar_conversion_note`로 결과에 남겨 손님이 확인할 수 있게 함(크로스노틱스 0번
   원칙 — 지어내지 않고 검증 가능하게). `crossnotics/index.html` 폼에도 양력/음력/음력(윤달)
   선택지를 추가했고, `test/run-all.js` 스모크 테스트ㆍ기존 양력 케이스 회귀 확인 완료.
2. **결제 전 리포트 미리보기 섹션 추가** — 운명도감은 결제 전에 실제 리포트 샘플(사주
   네 기둥ㆍ게이지바 등)을 랜딩 페이지에 그대로 보여주는데, 크로스노틱스는 "교차검증"을
   말로만 설명하고 실제로 뭘 받는지 전혀 보여주지 않고 있었다(5~15만원짜리 상품인데
   구매 전 미리보기가 전혀 없다는 게 가장 큰 전환 손실 지점으로 판단). `crossnotics/index.html`에
   `#cn-preview` 섹션을 추가해 사주(네 기둥)ㆍ별자리(태양/달/상승궁)ㆍ타로(카드) 3개 카드와
   "교차검증 일치도" 막대를 실제 엔진 출력 필드 그대로의 형식으로 예시를 만들어 보여준다.
   예시 인물은 "실제 고객 데이터 아님"이라고 명시(가짜 후기ㆍ가짜 이용자 수 같은 조작된
   사회적 증거는 넣지 않음 — 운명도감의 "누적 이용자 수" 카운터ㆍ언론사 수상 배지는 실제
   실적이 없는 상태에서 베끼면 허위 표시가 되므로 의도적으로 가져오지 않았음).
   - CSS는 `crossnotics/css/crossnotics.css`에 `.cn-preview*`/`.cn-match*` 블록으로 추가,
     기존 `--accent`(별자리=보라)/`--accent-2`(타로=초록)/`--accent-3`(사주=주황) 팔레트를
     그대로 재사용해 로고 색과 통일감 유지.
   - **다음에 고려할 것(이번엔 보류)**: 포스텔러처럼 진태양시(경도 기반 시차) 보정ㆍ한국
     역사적 서머타임(1948~51, 1955~60, 1987~88) 보정은 실제 유료 계산 엔진에 잘못된
     역사적 날짜 테이블을 넣으면 안 하느니만 못해서, 정확한 자료 확인 없이는 이번 세션에서
     구현하지 않기로 함 — 필요하면 날짜 테이블부터 출처 확인 후 별도 세션에서 진행할 것.

## 0. 지금 상태 — 계산ㆍAIㆍPDFㆍ손님용 사이트까지 전부 완료, 판매 시작 가능 (2026-08-21)

**계획서 1~7단계 전부 완료.** 실사용(진짜 API 호출, 진짜 브라우저 테스트)으로 검증까지 끝났고,
지금 상태로 실제로 손님을 받을 수 있습니다. 아래는 완료된 것과, 판매를 시작하기 전 사용자가
직접 해야 할 일 순서입니다.

### 완료된 것

1. **계산 엔진** (`tools/crossnotics-engine/`)
   - `saju.js`: lunar-javascript(npm, MIT)로 십신ㆍ지장간ㆍ12운성ㆍ공망ㆍ대운ㆍ세운(연도별 간지)까지 계산.
   - `astrology.js`: circular-natal-horoscope-js(npm)로 행성 10개(태양~명왕성)ㆍ하우스ㆍ어스펙트 계산.
   - `tarot.js`: Fisher-Yates 셔플 + 3장/켈틱크로스(10장) 스프레드. **78장 전체 덱**(메이저22+마이너56,
     마이너는 이번 세션에 신규 집필 — `tarot/js/tarot-data.js`에 있고 무료 타로 도구와 공유함).
   - `correlate.js`: 사주 오행ㆍ점성술 4원소ㆍ타로 카드를 공통 좌표계로 정규화해 일치도를 계산하는
     **교차상관 알고리즘**(이 프로젝트의 핵심 차별점, 완전 신규 설계).
   - `run.js`: CLI 진입점. `catalog.js`의 질문 개수 제한도 여기서 강제.
   - 알려진 연도(1990/2000/1988년생 띠)ㆍ생일(1990-05-14→황소자리)로 정확성 검증 완료.

2. **AI 리포트 생성** (`tools/crossnotics-report/`)
   - `build_report.py`: computed.json을 Anthropic API(tool-forced JSON 스키마)에 넣어 리포트 문장만
     생성 — correlate.js가 계산한 결과를 "번역"만 하도록 프롬프트로 강제(환각 차단).
   - `report_kit.py`: pdf_kit.py를 확장해 실제 브랜드 PDF 생성.
   - **실제 API로 여러 번 검증 완료**(목업 아님) — 싱글/마스터 티어 리포트 실제 생성, 질문 여러 개
     각각 답변, 세운 범위 밖 연도 지어내지 않는지까지 확인.
   - 실제 리포트당 비용(2026-08-21 기준): 싱글 약 33~50원, 마스터 약 150~250원 — 판매가(5~15만원)
     대비 무시할 수준.
   - 실사용 중 버그 2건 발견ㆍ수정: (1) Pretendard 폰트가 한자를 못 그려서 빈칸으로 깨지는 문제
     (2) LLM이 계산 안 된 연도를 일반 지식으로 지어낸 문제(→ se_un 필드 추가로 해결).

3. **가격ㆍ상품 구조 확정**
   - 사주 단독 진단(5만원, 질문 3개) / 사주+별자리 교차진단(10만원, 질문 6개) /
     사주+별자리+타로 통합진단(15만원, 질문 10개, 타로만 켈틱크로스 10장).
   - "체계 개수"가 1차 가격 기준, "질문 개수"는 딸린 혜택 — 순수 질문개수제는 단가가 평평해서
     업셀 유인이 없어 기각함(근거는 아래 "결정 사항" 참고).
   - `site-checkout/lib/catalog.js`가 유일한 가격 기준(Node/Python 양쪽에서 여기 값을 가져다 씀).

4. **손님용 사이트** (`crossnotics/index.html`)
   - 3개 가격 카드 클릭 선택 → 질문 입력칸 개수ㆍ출생지 필드 자동 조정 → 제출 시 기존
     `contactPurchase()`(계좌이체 안내 모달) 흐름 재사용, 이메일 본문에 운영자가 바로 쓸 수 있는
     intake.json도 함께 넣음.
   - `services.html`에 등재, 무료 사주/타로 도구의 업셀 버튼이 여기로 연결됨.
   - **실제 브라우저로 전체 흐름 검증**: 폼 작성 → 제출 → 이메일 JSON 생성 → 그 JSON을 그대로
     `run.js`에 넣어 계산까지 정상 완료(엔드투엔드 드라이런 성공).

### 결정 사항 (다음 세션이 왜 이렇게 됐는지 헷갈리지 않도록)

- **결제는 계좌이체로 시작, 카드결제 자동화(포트원+Vercel)는 보류.** 벤치마킹 영상 속 대표도
  주력 매출은 카드결제가 아니라 순수 계좌이체였음을 확인 후 사용자가 확정. `site-checkout/`
  (포트원 웹훅 백엔드) 코드는 완성해서 남겨뒀지만 지금은 안 씀 — 주문량이 늘어 자동화가
  필요해지면 그때 이어서 쓸 것(`api/generate-report.py` 브리지만 추가하면 됨, `route-product.js`에
  TODO로 표시돼 있음).
- **"싱글ㆍ듀얼ㆍ마스터"는 코드 내부 식별자일 뿐, 고객ㆍ대화에서 쓰지 말 것.** 고객용 이름은
  위 표 참고(사주 단독 진단 등).
- **순수 질문개수제(3/6/10개=5/10/15만원) 가격안은 기각됨** — 질문당 단가가 거의 평평해서
  (16,667/16,667/15,000원) 비싼 걸 살 이유가 없고, 이 서비스의 핵심 가치(교차검증)가 가격표에
  안 드러남. "체계 개수+질문 개수" 조합으로 대체.
- **API 테스트는 진짜 돈이 나간다 — 함부로 반복 호출하지 말 것.** 이번 세션에 이 원칙을 어겨
  사용자에게 지적받음. 코드가 도는지 확인할 땐 먼저 코드 검토로, 정말 실물 검증이 필요할 때만
  최소 횟수로 실제 호출할 것.

## 1. 사용자가 실제로 해야 할 남은 일 (전부 선택사항이지 필수 아님)

지금 상태로도 계좌이체+수동 파이프라인 실행으로 바로 판매 가능함. 아래는 "더 편하게/많이
팔고 싶을 때" 필요한 것들:

- **주문 들어오면**: 이메일에 온 intake JSON을 파일로 저장 → `node tools/crossnotics-engine/run.js
  주문.json computed.json` → `python tools/crossnotics-report/build_report.py computed.json` →
  `python tools/crossnotics-report/report_kit.py computed.json computed.report.json 결과.pdf` →
  메일로 PDF 발송. (Anthropic API 키는 `tools/crossnotics-report/.env`에 이미 저장돼 있음, git에는
  안 올라감.)
- **홍보 콘텐츠용 AI 아바타 영상 도구**: Vrew를 직접 켜서 "캐릭터 선택형 말하는 아바타" 기능이
  있는지 확인 — 검색으로는 확인 못 함(자막/AI보이스/AI이미지 중심으로만 확인됨). 없으면
  HeyGen/Vidu/Kling 등 대체 도구 검토.
- **주문이 많아지면(선택)**: 포트원 가입 + Vercel 배포로 `site-checkout/` 활성화해서 카드결제
  자동화로 전환 가능(코드는 이미 완성돼있음, `api/generate-report.py` 브리지만 추가하면 됨).

## 2. 백서 원본과 벤치마킹 영상 (배경)

사용자가 직접 작성한 크로스노틱스 백서(사주+별자리+타로 독립 계산 후 교차검증)와, 유튜브
벤치마킹 영상("지금 가장 쉬운 부업일걸요?", 실전부업클럽, e3m-GnCVij4 — 28살 '사주남매' 대표
인터뷰) 전체 캡션 분석 내용은 승인된 계획 파일에 원문 그대로 남아있음. **영상에서 배운 건 계산
방식이 아니라 성장 엔진**(릴스+자동DM+계좌이체 결제, 저가·고빈도 판매)이고, raw GPT 계산은
쓰지 않기로 확정(사용자 명시적 지시) — 실제 검증 가능한 계산 엔진을 만들었다는 게 이 프로젝트의
핵심 차별점.

## 3. 재사용 가능한 것들 (다음 콘텐츠 작업용)

- `marketing/drafts/` 워크플로우(전자책 홍보용 릴스/카드뉴스 자동생성 스크립트, `build_*_reels.py`ㆍ
  `handwritten_card_kit.py` 패턴) — 크로스노틱스 홍보 콘텐츠 제작에 그대로 재사용 가능.
- `products/_shared/pdf_kit.py` — `tools/crossnotics-report/report_kit.py`가 이미 확장해서 씀.

## 4. 파일 구조 요약

```
crossnotics/                          # 손님용 정적 페이지
tools/crossnotics-engine/             # Node — 계산 엔진(사주ㆍ점성술ㆍ타로ㆍ교차상관)
tools/crossnotics-report/             # Python — LLM 합성 + PDF (.env에 API 키, git 제외)
site-checkout/                        # Node — 결제 자동화 백엔드(완성됐지만 지금은 안 씀)
```
