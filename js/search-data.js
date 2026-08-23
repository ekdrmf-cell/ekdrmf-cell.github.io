/*
 * 사이트 전체 검색용 데이터 — 실제 판매중/이용가능한 항목만 포함.
 * 서비스·전자책은 개별 페이지가 없어(한 페이지에 전체 나열) 카테고리
 * 페이지로 연결하고, 게임은 각자 페이지로 바로 연결한다.
 * 2026-08-23: 운세 도구(사주ㆍ궁합ㆍ타로 등) 항목은 여기서 제거함 — 천지인운명관은
 * 별개 사이트로 분리되어 서비스허브 검색에는 더 이상 노출하지 않는다.
 */
const SEARCH_DATA = [
  // 전자책 (ebooks.html)
  { title: "소상공인·1인사업자 정부지원금 찾기 가이드", type: "전자책", url: "ebooks.html" },
  { title: "전자책 만들어 팔기 실전 가이드", type: "전자책", url: "ebooks.html" },
  { title: "구글 애드센스 수익형 블로그 시작 가이드", type: "전자책", url: "ebooks.html" },
  { title: "인스타그램 마케팅 핵심노하우", type: "전자책", url: "ebooks.html" },
  { title: "건축기사 실기 합격 전략 가이드", type: "전자책", url: "ebooks.html" },
  { title: "유튜브 채널 수익화 전략 가이드", type: "전자책", url: "ebooks.html" },
  { title: "제휴마케팅 실전 가이드", type: "전자책", url: "ebooks.html" },
  { title: "쿠팡 셀러 창업 가이드", type: "전자책", url: "ebooks.html" },
  { title: "메타 광고 최적화 가이드", type: "전자책", url: "ebooks.html" },
  { title: "챗GPT 실무 활용 가이드", type: "전자책", url: "ebooks.html" },
  { title: "쇼핑몰 CS 고객응대 가이드", type: "전자책", url: "ebooks.html" },
  { title: "1인사업자 부가세 셀프 체크리스트", type: "전자책", url: "ebooks.html" },
  { title: "큐텐재팬 셀러 판매전략 가이드", type: "전자책", url: "ebooks.html" },
  // 서비스 (services.html)
  { title: "견적서 자동생성 템플릿", type: "서비스", url: "services.html" },
  { title: "급여명세서 자동계산기", type: "서비스", url: "services.html" },
  { title: "재고 부족 자동알림 시트", type: "서비스", url: "services.html" },
  { title: "거래명세서·발주서·견적서 통합 자동생성기", type: "서비스", url: "services.html" },
  { title: "회원권·정기결제 만료 자동알림 시트", type: "서비스", url: "services.html" },
  { title: "학원 수강료 자동계산·수납관리 시트", type: "서비스", url: "services.html" },
  { title: "근로계약서 자동생성기", type: "서비스", url: "services.html" },
  { title: "매입매출장·부가세 예상액 계산 시트", type: "서비스", url: "services.html" },
  { title: "근태관리·연차 자동집계 시트", type: "서비스", url: "services.html" },
  { title: "CS 자주문의·리뷰 답글 자동매칭 시트", type: "서비스", url: "services.html" },
  { title: "구글폼 응답 자동집계·조건부 알림 대시보드", type: "서비스", url: "services.html" },
  // 게임 (GAMES 배열과 동일 목록, url만 별도 유지)
  { title: "2048 퍼즐", type: "게임", url: "games/2048/index.html" },
  { title: "장애물 러너", type: "게임", url: "games/runner/index.html" },
  { title: "매치3 캔디", type: "게임", url: "games/match3/index.html" },
  { title: "두더지 잡기", type: "게임", url: "games/whackamole/index.html" },
  { title: "카드 짝맞추기", type: "게임", url: "games/memory/index.html" },
  { title: "상식퀴즈", type: "게임", url: "games/quiz/index.html" },
];

/** 검색어와 제목이 부분적으로 겹치면 매치로 본다(초성/오타 대응 없는 단순 매칭). */
function searchSite(query) {
  const q = query.trim().toLowerCase();
  if (!q) return [];
  return SEARCH_DATA.filter((item) => item.title.toLowerCase().includes(q));
}
