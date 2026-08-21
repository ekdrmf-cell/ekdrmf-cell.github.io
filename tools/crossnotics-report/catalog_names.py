# -*- coding: utf-8 -*-
"""
site-checkout/lib/catalog.js의 CROSSNOTICS_TIERS와 이름을 맞춰 둔 표지용 상품명 헬퍼.
Node/Python 두 언어에 걸쳐 있어서 자동 동기화가 안 됨 — catalog.js를 고치면 여기도 같이 고칠 것.
"""

TIER_PRODUCT_NAME = {
    "single": "크로스노틱스 — 사주 단독 진단",
    "dual": "크로스노틱스 — 사주 + 별자리 교차진단",
    "master": "크로스노틱스 — 사주 + 별자리 + 타로 통합진단",
}


def tier_product_name(tier):
    return TIER_PRODUCT_NAME.get(tier, "크로스노틱스 진단")
