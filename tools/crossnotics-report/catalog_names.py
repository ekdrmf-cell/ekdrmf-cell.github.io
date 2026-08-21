# -*- coding: utf-8 -*-
"""
site-checkout/lib/catalog.js의 CROSSNOTICS_TIERS와 이름을 맞춰 둔 표지용 상품명 헬퍼.
Node/Python 두 언어에 걸쳐 있어서 자동 동기화가 안 됨 — catalog.js를 고치면 여기도 같이 고칠 것.
"""

TIER_PRODUCT_NAME = {
    "single": "크로스노틱스 싱글 진단",
    "dual": "크로스노틱스 듀얼 크로스 매트릭스 진단",
    "master": "크로스노틱스 마스터 다차원 통합 진단",
}


def tier_product_name(tier):
    return TIER_PRODUCT_NAME.get(tier, "크로스노틱스 진단")
