# -*- coding: utf-8 -*-
"""
site-checkout/lib/catalog.js의 CROSSNOTICS_TIERS와 이름을 맞춰 둔 표지용 상품명 헬퍼.
Node/Python 두 언어에 걸쳐 있어서 자동 동기화가 안 됨 — catalog.js를 고치면 여기도 같이 고칠 것.

2026-08-23: 두 가지 반영.
1. tier 배지(FREE/LIGHT/SINGLE/DUAL/MASTER/PREMIUM)를 표지 제목에도 포함 — 사용자 지시로
   crossnotics/index.html에 노출한 것과 동일한 이름을 PDF 표지까지 통일함(catalog.js의
   label 필드와 동일한 값).
2. 기존에 "크로스노틱스"/"천지인운명관"이 섞여 있던 것도 "천지인운명관"으로 통일 —
   브랜드명이 이미 천지인운명관으로 바뀐 지 오래인데 single/dual/master만 옛 이름이
   남아있던 불일치를 발견해서 같이 고침(2026-08-22 세션에서 사용자에게 확인 필요 항목으로
   플래그했던 것 — 이번 라벨 통일 작업 김에 함께 정리).
"""

TIER_PRODUCT_NAME = {
    "mini": "천지인운명관 FREE — 오늘의 사주 미니 진단",
    "light": "천지인운명관 LIGHT — 사주 라이트 진단",
    "single": "천지인운명관 SINGLE — 사주 단독 진단",
    "dual": "천지인운명관 DUAL — 사주 + 별자리 교차진단",
    "master": "천지인운명관 MASTER — 사주 + 별자리 + 타로 통합진단",
    "premium": "천지인운명관 PREMIUM — 장기 인생 전략",
}


def tier_product_name(tier):
    return TIER_PRODUCT_NAME.get(tier, "크로스노틱스 진단")
