# 천지인운명관 — 주문 처리 체크리스트 (PREMIUM 기준, 2026-08-23 작성)

`천지인운명관_사업운영가이드.md` 7번 "다음에 할 일" #3(결제·발송 전 체크리스트 문서화)에
대응해 작성. 여기 적힌 절차는 6개 티어(FREE~PREMIUM) 전부 동일하고, 이 문서는 가장 비싼
PREMIUM(200,000원) 기준으로 구체적인 파일명·경로·비용을 채워넣었다. 다른 티어를 처리할 땐
가격ㆍ질문개수ㆍ페이지수만 `tools/crossnotics-engine/catalog.js`의 `CROSSNOTICS_TIERS`에서
바꿔 대입하면 된다.

**주의**: 이 문서를 작성하는 시점 기준으로 **실제 Anthropic API 호출로 PREMIUM 리포트를
만들어본 적이 아직 없다.** SINGLE(33~50원)ㆍMASTER(150~250원)만 2026-08-21에 실측됐고,
PREMIUM은 250~400원 추정치뿐이며 그 이후 궁합ㆍ신살ㆍ대응표ㆍ시너스트리 기능이 추가돼
`computed.json` 입력 데이터 자체가 커진 상태라 이 추정치가 지금은 낮게 잡혔을 수 있다.
**첫 PREMIUM 주문 처리가 사실상 이 티어의 첫 실전 검증이다.**

## 0. 사전 게이트 — 입금 확인 (자동화 없음, 반드시 사람이 할 것)

고객이 사이트 결제 팝업에서 "입금 완료, 문의 이메일 보내기"를 누르면 `ekdrmf@gmail.com`으로
메일이 온다. **이건 고객의 자기 신고일 뿐 입금 증거가 아니다** — 케이뱅크 앱에서 실제
입금 내역(금액ㆍ보낸 사람 이름)을 대조하기 전엔 아래 파이프라인을 시작하지 말 것.

## 1. intake.json 저장

받은 이메일 맨 아래 "운영자 메모: 아래 JSON을 그대로 intake.json으로 저장해 node run.js로
실행하면 됩니다" 아래 JSON 블록을 그대로 복사해 `intake.json`으로 저장.
(권장 보관 위치: `tools/crossnotics-engine/orders/YYYY-MM-DD_고객명.json` — 아직 정해진
폴더가 없으니 새로 만들어 쓸 것. 이 폴더에는 고객 개인정보가 담기므로 `.gitignore`에
추가할 것, 절대 커밋 금지.)

## 2. 계산 엔진 실행 (비용 없음, 로컬)

```bash
cd 서비스허브/tools/crossnotics-engine
node run.js intake.json computed.json
```

에러 없이 끝나는지 콘솔 확인. 상대방 정보가 있으면 궁합(`gunghap`)ㆍ상대방 사주
(`partner_saju`)가, 상대방 출생지까지 있으면 점성술 시너스트리도 자동 포함된다.

## 3. 리포트 문장 생성 (여기서 API 비용 발생)

```bash
cd ../crossnotics-report
python build_report.py ../crossnotics-engine/computed.json computed.report.json
```

- 모델: `claude-sonnet-4-5-20250929`, $3/100만 입력토큰 · $15/100만 출력토큰.
- 실행 화면에 찍히는 실제 토큰 사용량으로 진짜 원가를 확인할 것(PREMIUM은 아직 실측
  기록이 없으므로 이번이 처음).
- ⚠ 경고(% 문자, 연도 불일치, 별자리 용어 불일치 등) 뜨는지 확인.
- 질문별 direct/redirected/unanswerable 판정은 `logs/question_answerability_log.jsonl`에
  자동 기록됨 — 고객 질문 원문이 담기므로 **절대 커밋 금지**(이미 .gitignore 처리됨).

## 4. PDF 생성 (비용 없음)

```bash
python report_kit.py ../crossnotics-engine/computed.json computed.report.json 결과_고객명.pdf
```

## 5. 발송 전 육안 확인 체크리스트 (자동화 안 됨 — 매번 사람이 볼 것)

- [ ] 페이지 수가 카탈로그 약속(PREMIUM=30페이지)과 크게 어긋나지 않는가
- [ ] 3단계에서 뜬 경고가 없었는가
- [ ] redirected/unanswerable 답변이 있다면 위장 없이 이유를 먼저 밝히고 있는가
- [ ] 궁합 정보를 넣었다면 점수ㆍ근거가 자연스럽게 녹아들었는가
- [ ] PDF를 실제로 열어 표지 엠블럼ㆍ챕터별 색상(사주=주황 #e8562f · 별자리=보라 #6d4aff ·
      타로=초록 #0a7d5e · 종합=골드 #a67c1e)이 정상인가

## 6. 고객 발송

받은 신청 메일에 "답장"만 누르면 됨(회신 주소가 고객 이메일로 이미 세팅되어 있음) → PDF
첨부 → 발송. (선택, 강요 없이) "SNS에 공유해주시면 감사하겠습니다" 한 줄 고려 가능
(`sales_marketing_strategy.md` 4번 참고).

## 7. 이후 참고사항

- 환불 불가 정책이 사이트에 이미 명시되어 있음.
- **사업자등록증 없음**(2026-08-23 확인) — 세금계산서 발행 불가, 개인 간 거래로 처리됨.
  정확한 신고 의무는 세무 영역이라 이 문서에서 단정하지 않음, 매출 규모가 커지면 세무사
  상담 권장.
- 다른 티어(FREE/LIGHT/SINGLE/DUAL/MASTER) 처리 시 위 절차는 동일, 가격ㆍ질문개수ㆍ
  페이지수만 `catalog.js` 기준으로 바꿔 대입.

## 참고 파일 위치

- 가격ㆍ상품 단일 소스: `tools/crossnotics-engine/catalog.js`
- 계산 엔진: `tools/crossnotics-engine/`
- 리포트 생성(LLM+PDF): `tools/crossnotics-report/`
- 신청 접수 스크립트: `crossnotics/apps-script/Code.gs`
- 전체 운영 가이드: `천지인운명관_사업운영가이드.md`(바탕화면)
