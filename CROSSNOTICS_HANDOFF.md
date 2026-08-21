# 크로스노틱스(Cross-Notics) 트랙 인수인계 문서

이 문서는 전자책 트랙(`EBOOK_HANDOFF.md`), 서비스 트랙(`SERVICES_HANDOFF.md`), 마케팅 트랙
(`MARKETING_HANDOFF.md`), 배포 트랙(`DEPLOY_HANDOFF.md`)과 독립적인 **다섯 번째 트랙**입니다.
크로스노틱스(프리미엄 사주ㆍ점성술ㆍ타로 통합 진단 서비스) 관련 요청이 오면 이 문서부터 읽으세요.

**전체 설계는 `C:\Users\ekdrm\.claude\plans\idempotent-rolling-hopcroft.md`에 승인된 계획으로 남아있음
— 큰 방향이 헷갈리면 그 파일부터 참고할 것.**

## 0-0. 가격ㆍ상품명ㆍ차별화 기준 최종 확정 (2026-08-21, 4차)

**"싱글ㆍ듀얼ㆍ마스터"는 코드 내부 식별자일 뿐, 고객에게 노출되는 이름이 아니다.** 사용자가
이 용어를 자기가 쓴 적 없는데 왜 당연하다는 듯 쓰냐고 지적함 — 앞으로 사용자와 대화할 때도
이 용어 쓰지 말고, 아래 고객용 이름으로 부를 것.

**가격 차별화 기준 — 두 가지를 검토해서 하나를 기각하고 하나를 채택함**:
- ❌ 순수 질문개수제(질문 3/6/10개 = 5/10/15만원)만으로 가격을 나누는 안은 기각됨 — 질문당
  단가가 16,667/16,667/15,000원으로 거의 평평해서 비싼 걸 살 이유(업셀 유인)가 없고,
  이 상품의 핵심 차별점(체계를 여러 개 겹쳐 교차검증)이 가격표에서 안 드러남.
- ✅ **채택안: "체계 개수"를 1차 기준, "질문 개수"를 딸린 혜택으로.** 즉 비쌀수록 계산
  자체가 더 깊어지고(체계 추가+교차분석), 부가적으로 질문도 더 받아준다 — 두 가지 이유가
  겹쳐서 가격 차이가 설득력을 가짐.

**최종 확정 3종 (`site-checkout/lib/catalog.js`의 `CROSSNOTICS_TIERS`에 코드로 반영됨)**:

| 상품코드 | 고객용 이름 | 가격 | 체계 | 질문 개수 | 타로 스프레드 |
|---|---|---|---|---|---|
| `crossnotics-saju-only` | 사주 단독 진단 | 5만원 | 사주만 | 3개 | (해당없음) |
| `crossnotics-saju-astrology` | 사주 + 별자리 교차진단 | 10만원 | 사주+별자리 | 6개 | (해당없음) |
| `crossnotics-full` | 사주 + 별자리 + 타로 통합진단 | 15만원 | 3체계 전부 | 10개 | 켈틱크로스 10장(하위 티어는 3장) |

질문 개수 제한은 `tools/crossnotics-engine/run.js`가 `catalog.js`의 `getCrossnoticsTierConfig()`를
직접 불러와서 강제함(초과 시 비싼 LLM 호출 전에 바로 에러) — 실제 테스트로 정상 통과ㆍ정상
차단 둘 다 확인함. `build_report.py` SYSTEM_PROMPT 9번 규칙으로 질문이 여러 개면 각각 소제목
붙여 따로따로 답하게 강제함(뭉뚱그리거나 복사한 듯한 답변 방지).

## 0-1. 결제 방식 확정 (2026-08-21, 3차 — 가장 중요한 변경사항)

**카드결제 자동화(포트원+Vercel) 보류, 계좌이체로 시작.** 벤치마킹 영상 속 대표도 매출을 제일
많이 낸 방식은 카드결제가 아니라 **순수 계좌이체**(카톡으로 계좌번호 보내고 입금 확인 후 처리)
였음을 사용자가 대본으로 직접 확인 후 "그렇게 가자"고 확정. `site-checkout/`(포트원 웹훅 백엔드)
코드는 이미 만들어놨지만 **당장은 안 씀** — 나중에 주문량이 많아져서 자동화가 필요해지면 그때
다시 꺼내 쓸 것(코드는 삭제하지 않고 남겨둠).

**새 흐름(훨씬 단순함)**:
1. 손님이 폼(구글폼 등)에 생년월일시ㆍ티어ㆍ질문 입력
2. 기존 전자책과 똑같이 계좌번호 안내(`js/config.js`의 `paymentGuideText` 그대로 재사용) → 손님이
   직접 이체
3. 사장님이 입금 확인(수동)
4. 사장님(또는 다음 세션의 나)이 로컬에서 이미 만들어둔 파이프라인 실행: `node run.js` →
   `build_report.py` → `report_kit.py` → PDF 완성
5. 이메일로 PDF 첨부해서 발송(수동, 또는 나중에 자동화)

**이 결정으로 필요 없어진 것**: 포트원 가입, Vercel 가입, `api/generate-report.py` 브리지 작성 —
전부 미룸. **남는 것은 사실상 Anthropic API 키 하나뿐.**

## 0. 지금 상태 요약 (2026-08-21, 2차 갱신)

**1ㆍ3ㆍ4ㆍ5단계 핵심 코드 전부 작성ㆍ검증 완료.** "무료 우선, 어려운 것부터"라는 사용자
지시에 따라 API 키 없이도 진행 가능한 하드코어 엔지니어링(계산 엔진 → 결제 백엔드 → LLM
프롬프트+PDF)을 먼저 끝냈다. 남은 건 대부분 **사용자 액션(계정 가입ㆍAPI 키)이나 콘텐츠
집필**이지 추가 설계가 아니다.

완료:
- `tools/crossnotics-engine/saju.js` — 사주 엔진. lunar-javascript(npm, MIT, v1.7.7)의 EightChar API를
  깊이 활용해 십신ㆍ지장간ㆍ12운성ㆍ공망ㆍ대운까지 계산. 1990/2000/1988년생 연주 간지를 잘 알려진
  띠(백말띠/백룡띠/무진년)와 대조해 정확성 확인 완료.
- `tools/crossnotics-engine/astrology.js` — 점성술 엔진. circular-natal-horoscope-js(npm, Unlicense,
  v1.1.0, 최종 배포 2022-04지만 천체력 계산이라 정확도엔 문제없음)로 실제 네이탈 차트(행성 7개ㆍ
  하우스ㆍ어스펙트) 계산. 1990-05-14 생일 → 황소자리로 정확히 검증.
- `tools/crossnotics-engine/tarot.js` — 타로 셔플/스프레드 엔진 신규 구현(기존 무료 도구는 랜덤 1장
  뽑기뿐이었음). Fisher-Yates 셔플, 3장/켈틱크로스(10장) 스프레드, 정/역방향 랜덤 결정.
  **주의: 현재 메이저 아르카나 22장만 있음 — 마이너 아르카나 56장은 미집필(2단계 콘텐츠 작업 대상)**,
  `tarot/js/tarot-data.js`를 파일에서 직접 읽어와서 씀(78장 채워지면 자동으로 반영됨, 코드 수정 불필요).
- `tools/crossnotics-engine/correlate.js` — **교차상관 알고리즘(신규, 이 프로젝트의 핵심 차별점)**.
  사주 오행 5분류ㆍ점성술 4원소ㆍ타로 카드를 공통 좌표계(4원소)로 정규화해 일치도(코사인 유사도)ㆍ
  보완점을 결정론적으로 계산. LLM은 이 결과를 문장으로 번역만 함(3단계에서 아직 구현 안 됨).
  **매핑 근거(오행→4원소, 타로→4원소)는 이 프로젝트의 v1 가설이며 파일 상단 주석에 문서화돼 있음 —
  절대 정설 아님, 실제 리포트 검수하면서 위화감 있으면 조정 가능.**
- `tools/crossnotics-engine/run.js` — CLI 진입점. `node run.js intake.json [출력경로]`로 실행하면
  `computed.json` 1개 생성(1단계 파이프라인의 최종 산출물, 2단계 Python/LLM으로 넘기기 전 사람이
  먼저 검증하는 지점).
- `tools/crossnotics-engine/test/` — 샘플 intake(싱글/마스터) + 스모크 테스트(`node test/run-all.js`),
  둘 다 통과 확인.
- Node.js 자체가 이 컴퓨터에 없어서 winget으로 신규 설치함(v24.19.0) — 사용자 승인받고 진행.
- `saju/lib/lunar.js`(기존 무료 도구가 쓰는 vendored 사본)에 라이선스/버전 주석 추가.
- `.gitignore`에 크로스노틱스 관련 시크릿/PII 경로(`tools/crossnotics-report/orders/`, `.env`,
  `__pycache__/` 등) 추가.
- **`site-checkout/`(신규, 계획서 5단계) — 서비스허브 전체가 공유하는 결제 웹훅 백엔드 완성.**
  포트원(PortOne) V2 웹훅 서명 검증(`@portone/server-sdk`), 결제금액 서버 재조회로 위변조 방지,
  상품 카탈로그(`lib/catalog.js` — 전자책 13종 실제 가격 확정 반영, 서비스 11종은 가격 미확인이라
  TODO로 남김, 크로스노틱스 3티어는 백서 제안가로 임시 채움), Gmail SMTP 기반 무료 이메일 발송
  (`lib/deliver-email.js`, 유료 SendGrid 등 안 씀). 크로스노틱스 주문이 오면 Node 계산 엔진을
  서브프로세스로 실행해 `computed.json`까지 실제로 생성하는 것까지 mock 결제로 확인함.
  **PortOne REST API 응답의 정확한 필드명(금액/customData 위치)은 문서로 100% 확정 못해 합리적
  추정으로 작성 — 실제 테스트 결제 때 재확인 필요(`api/webhook.js` 상단 주석 참고).**
- **`tools/crossnotics-report/`(신규, 계획서 3ㆍ4단계) — LLM 합성 + PDF 생성 파이프라인 완성.**
  `build_report.py`: computed.json을 Anthropic API(tool-forced JSON 스키마로 강제해 자유 텍스트
  파싱보다 안전하게)에 넣어 리포트 문장만 생성 — correlate.js가 계산한 결과를 "번역"만 하도록
  프롬프트로 강제(환각 방지). `report_kit.py`: pdf_kit.py를 확장해 실제 브랜드 PDF 생성, 오행/원소
  분포를 stat_row로 병기해 LLM 문장 옆에 원본 숫자도 같이 보여줌. **목업 데이터로 싱글/마스터
  티어 PDF를 실제로 뽑아봄**(`tools/crossnotics-report/test/sample-*.pdf`) — 디자인 정상 확인.
  이 과정에서 **Pretendard 폰트가 한자 글리프를 지원 안 해 "신금(辛金)"처럼 한자가 섞이면 빈칸으로
  깨지는 버그 발견**(큐텐재팬 전자책 때와 동일 부류) → SYSTEM_PROMPT에 "한자 절대 금지" 규칙 추가로
  방지 완료.
  **Anthropic API 실제 호출은 아직 한 번도 안 해봄** — ANTHROPIC_API_KEY가 없어서 테스트 불가.
- **연결 안 된 부분(다음 세션 최우선)**: `site-checkout/lib/route-product.js`의 크로스노틱스
  처리 로직이 Node 계산까지는 실행하지만, 그 다음 `tools/crossnotics-report/`(Python)로 못
  넘어감 — Vercel Node 함수는 Python을 직접 spawn 못하기 때문. **`site-checkout/api/generate-report.py`
  (Vercel Python 런타임 함수)를 새로 만들어서 build_report.py의 `call_llm()`ㆍreport_kit.py의
  `build_pdf()`를 그 안에서 import해 쓰고, route-product.js가 HTTP로 그 함수를 호출하게 이어붙이는
  작업이 남음.** ANTHROPIC_API_KEY가 있어야 실제 테스트 가능.

**다음 세션이 이어받을 때 먼저 할 일**: `node --version`/`python --version`으로 둘 다 인식되는지
확인(새 창이면 PATH 갱신 안 됐을 수 있음 — 완전히 앱 재시작 필요, Git 설치 때와 동일한 이슈).

## 1. 백서 원본과 벤치마킹 영상

사용자가 직접 작성한 크로스노틱스 백서(사주+별자리+타로 독립 계산, 3단계 가격 3~5만/8~10만/15만+)와,
유튜브 벤치마킹 영상("지금 가장 쉬운 부업일걸요?", 실전부업클럽, e3m-GnCVij4 — 28살 '사주남매' 대표
인터뷰) 전체 캡션 분석 내용은 승인된 계획 파일에 원문 그대로 남아있음. **영상에서 배운 건 계산
방식이 아니라 성장 엔진**(릴스+자동DM+카톡/완전자동화 결제, 저가·고빈도 판매)이고, raw GPT 계산은
쓰지 않기로 확정(사용자 명시적 지시) — 실제 계산 엔진을 만들었다.

## 2. 미해결/다음 단계 (계획서 7번 "빌드 순서" 기준)

**0단계(사용자 액션, 아직 안 함)**:
- 포트원(PortOne) 가입 페이지에서 사업자등록 없이 개인 자격 가입되는지 확인 — 안 되면 사업자등록
  여부 결정 필요.
- Vrew를 직접 켜서 "캐릭터 선택형 말하는 아바타" 기능이 실제로 있는지 확인(검색으로는 확인 안 됨,
  Vrew는 자막/AI보이스/AI이미지 중심으로만 확인됨) — 없으면 HeyGen/Vidu/Kling 등 대체 도구 조사.

**1단계 남은 것**: 없음(엔진 핵심은 완료). 다만 실전 배포 전 사주 결과를 실제 만세력 사이트와,
점성술 결과를 실제 점성술 사이트와 몇 건 더 대조하면 좋음(지금은 well-known 연도/생일로만 검증함).

**2단계(콘텐츠, 병행 가능, 아직 안 함)**: 마이너 아르카나 56장 신규 집필(전자책 한 챕터 분량).

**3ㆍ4단계(코드 완료, 실사용 검증만 남음)**: `tools/crossnotics-report/`(Python) — `build_report.py`
(LLM 합성)ㆍ`report_kit.py`(PDF) 둘 다 작성ㆍ목업 테스트 완료. **남은 건 오직**: ①사용자가
Anthropic Console에서 API 키 발급 ②실제 리포트 5~10건 생성해 환각/톤 검수 ③Console 사용량으로
실사용 단가 확인 후 승인.

**5단계(코드 완료, 실사용 검증만 남음)**: `site-checkout/` — 결제 웹훅 백엔드 작성ㆍmock 테스트
완료. **남은 건**: ①포트원 가입(사업자등록 필요 여부 확인) ②Vercel 계정 개설+배포 ③`api/
generate-report.py` 브리지 작성(Node→Python 연결, 위 0번 "연결 안 된 부분" 참고) ④Gmail 앱
비밀번호 발급 ⑤실제 테스트 결제로 PortOne 응답 필드 가정 검증(`api/webhook.js` 주석 참고).

**6단계(아직 안 함)**: `crossnotics/index.html`, `js/crossnotics-data.js`, `services.html` 등재,
기존 무료 사주/궁합/타로 결과 화면에 업셀 CTA, 릴스/스레드 콘텐츠 제작. 결제 버튼이 실제로
site-checkout을 호출하도록 `js/config.js`의 `contactPurchase()` 확장도 이 단계.

**7단계(아직 안 함)**: 실제 주문 1건 처음부터 끝까지(콘텐츠 유입→결제→자동 리포트 수령) 드라이런.

## 3. 재사용 가능한 것들

- `products/_shared/pdf_kit.py` — 4단계에서 report_kit.py로 확장해 재사용.
- `marketing/drafts/` 워크플로우(전자책 홍보용 릴스/카드뉴스 자동생성 스크립트) — 6단계 콘텐츠 제작에
  그대로 재사용 가능(`build_*_reels.py`, `handwritten_card_kit.py` 패턴).
- `js/config.js`의 `contactPurchase()` — 6번(site-checkout) 연동 시 이 함수를 확장.
