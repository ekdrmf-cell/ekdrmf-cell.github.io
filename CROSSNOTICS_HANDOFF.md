# 크로스노틱스(Cross-Notics) 트랙 인수인계 문서

이 문서는 전자책 트랙(`EBOOK_HANDOFF.md`), 서비스 트랙(`SERVICES_HANDOFF.md`), 마케팅 트랙
(`MARKETING_HANDOFF.md`), 배포 트랙(`DEPLOY_HANDOFF.md`)과 독립적인 **다섯 번째 트랙**입니다.
크로스노틱스(프리미엄 사주ㆍ점성술ㆍ타로 통합 진단 서비스) 관련 요청이 오면 이 문서부터 읽으세요.

**전체 설계는 `C:\Users\ekdrm\.claude\plans\idempotent-rolling-hopcroft.md`에 승인된 계획으로 남아있음
— 큰 방향이 헷갈리면 그 파일부터 참고할 것.**

## 0. 지금 상태 요약 (2026-08-21)

**1단계(Node 계산 엔진) 핵심 부분 완료ㆍ검증됨.** 아직 결제 연동ㆍLLM 합성ㆍPDF 생성ㆍ마케팅 콘텐츠는
전혀 안 됨 — 계산 엔진만 끝난 상태.

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
- `.gitignore`에 크로스노틱스 관련 시크릿/PII 경로(`tools/crossnotics-report/orders/`, `.env` 등) 추가.

**다음 세션이 이어받을 때 먼저 할 일**: `node --version`으로 Node 인식되는지 확인(새 창이면 PATH
갱신 안 됐을 수 있음 — 완전히 앱 재시작 필요, Git 설치 때와 동일한 이슈).

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

**3단계(아직 안 함)**: `tools/crossnotics-report/`(Python) 신설 — `synthesis_prompt.md` 작성,
Anthropic API 연동(사용자가 Console 계정+API 키 필요), 리포트 5~10건 생성해 환각/톤 검수, 실사용
단가 확인 후 사용자 승인.

**4단계(아직 안 함)**: `report_kit.py`(products/_shared/pdf_kit.py 확장)로 티어별 PDF 레이아웃.

**5단계(아직 안 함, 비중 큼)**: `site-checkout/` 신설 — 서비스허브 전체(전자책+서비스+크로스노틱스)가
공유하는 결제 백엔드. 포트원 연동 + 웹훅 서버리스 함수(Vercel 등 신규 계정 필요) + 상품별 라우팅 +
이메일 자동발송.

**6단계(아직 안 함)**: `crossnotics/index.html`, `js/crossnotics-data.js`, `services.html` 등재,
기존 무료 사주/궁합/타로 결과 화면에 업셀 CTA, 릴스/스레드 콘텐츠 제작.

**7단계(아직 안 함)**: 실제 주문 1건 처음부터 끝까지(콘텐츠 유입→결제→자동 리포트 수령) 드라이런.

## 3. 재사용 가능한 것들

- `products/_shared/pdf_kit.py` — 4단계에서 report_kit.py로 확장해 재사용.
- `marketing/drafts/` 워크플로우(전자책 홍보용 릴스/카드뉴스 자동생성 스크립트) — 6단계 콘텐츠 제작에
  그대로 재사용 가능(`build_*_reels.py`, `handwritten_card_kit.py` 패턴).
- `js/config.js`의 `contactPurchase()` — 6번(site-checkout) 연동 시 이 함수를 확장.
