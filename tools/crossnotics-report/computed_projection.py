"""
computed.json → LLM 입력 projection.

2026-08-30 추가 — API 비용 절감 2단계. 목적은 "LLM에게 불필요한 computed 데이터를
전달하지 않는 구조를 확보하는 것"이지, 그 자체로 API 비용 문제를 해결하는 게 아니다
(절감률은 티어별로 0.9%~12.2%에 불과 — SYSTEM_PROMPT 절감과 합산해서 평가할 것).

핵심 원칙(사용자 승인 조건 그대로):
  1. computed.json 원본은 이 모듈이 절대 수정하지 않는다 — project_computed()는 항상
     deepcopy 위에서만 필드를 제거하고, 원본 dict는 입력으로 받은 그대로 남는다.
  2. projection은 LLM 호출 직전에만 만들어지는 view이고, 원본과 완전히 독립적으로 보존된다.
  3. 제거 후보는 REMOVED_FIELD_MANIFEST에 코드+근거(evidence)와 함께 명시된 것만 제거한다 —
     "혹시 몰라서" 넣은 필드는 없다, 전부 build_report.SYSTEM_PROMPT 원문 grep + 엔진 코드
     대조로 검증됨(evidence 필드에 그 근거를 남겨둠).
  4. fallback 지시가 본문에 내장된 필드(PRESERVED_FALLBACK_FIELDS)는 필드명이 SYSTEM_PROMPT에
     안 나와도 항상 보존한다 — 값 자체가 곧 규칙인 경우들(예: se_un_note).
  5. question_answers는 자유 질문이라 코드가 필요 데이터를 완벽히 예측할 수 없으므로, 이번
     단계에서는 system_sections/cross_analysis가 이미 쓰는 데이터 밖의 새로운 제거를 하지
     않는다 — REMOVED_FIELD_MANIFEST의 모든 항목은 규칙10-A~10-K 중 어느 것도 참조하지
     않는다는 것까지 확인된 것만 포함(아래 자체 검증 참고).
"""
import copy
import re


# ============================================================================
# 제거 후보 manifest — 각 항목은 "왜 안전한가"의 근거(evidence)를 코드/규칙 인용으로 남긴다.
# path는 dot-path(배열은 "[]"로 표기, 배열 원소 내부 필드는 별도 SUB_ARRAY_FIELD_REMOVALS로 처리).
# ============================================================================

REMOVED_FIELD_MANIFEST = [
    {
        "path": "generated_at_note",
        "reason": "파이프라인 내부 메타데이터 — LLM이 리포트 문장에 옮길 이유가 없음",
        "evidence": "crossnotics-engine/run.js:70 주석: '타임스탬프는 배송 파이프라인(2단계)"
                    "에서 채움 — 이 엔진은 순수 계산만 담당'. SYSTEM_PROMPT 원문에 "
                    "'generated_at_note' 문자열 매치 0건(grep 확인).",
    },
    {
        "path": "saju.lunar_text",
        "reason": "한자(漢字) 표기 음력 문자열 — 규칙7이 한자 사용 자체를 전면 금지, 절대 인용 불가",
        "evidence": "build_report.py 규칙7(r07): '한자(漢字)나 그 외 한글이 아닌 문자를 절대 "
                    "쓰지 마세요 ... PDF 폰트가 한자 글리프를 지원하지 않아 빈칸으로 깨집니다'. "
                    "SYSTEM_PROMPT 원문에 'lunar_text' 문자열 매치 0건.",
    },
    {
        "path": "customer.latitude",
        "reason": "astrology.js 계산 입력값(위경도) — 계산이 끝난 뒤에는 좌표 수치 자체를 "
                  "리포트 문장에서 인용할 근거가 없음",
        "evidence": "SYSTEM_PROMPT 원문에 'latitude'/'위도' 문자열 매치 0건. astrology.js가 "
                    "이 좌표를 소비해 planets/houses/aspects를 이미 계산해 넣은 뒤라, LLM은 "
                    "파생 결과(sun_sign/planets/correspondence 등)만 보면 충분함.",
    },
    {
        "path": "customer.longitude",
        "reason": "위와 동일(경도)",
        "evidence": "SYSTEM_PROMPT 원문에서 '경도'가 매치되는 유일한 문맥은 규칙8의 "
                    "'상대방 생년월일과 출생 위경도까지 있을 때만 run.js가 계산해 넣어줍니다' "
                    "— intake 단계의 계산 조건 설명이지, LLM에게 좌표 수치를 직접 쓰라는 "
                    "지시가 아님.",
    },
    {
        "path": "customer.behavior_answers",
        "reason": "행동DNA 원본 응답 배열(15문항) — 이미 behavior.axes로 결정론적 집계 완료, "
                  "원본 재참조 지시 없음",
        "evidence": "build_report.py 규칙9-A-1: 'computed.behavior.axes 배열의 각 항목"
                    "(axisLabel/pattern/strength/crossRef)을 그대로 근거로 쓰고, 절대 새로 "
                    "지어내지 마세요' — behavior_answers는 이 문장에도, SYSTEM_PROMPT 전체에도 "
                    "언급되지 않음(grep 0건).",
    },
    {
        "path": "astrology.planets",
        "reason": "원본 행성 배열(body/sign/degree/ecliptic_longitude/house/retrograde) — "
                  "astrology.correspondence.planet_meanings가 body/sign/house를 그대로 "
                  "1:1로 이어받고 의미(body_meaning/sign_meaning)까지 추가한 상위호환 버전",
        "evidence": "crossnotics-engine/astrology-correspondence.js:78-84 "
                    "planetMeanings = astrologyResult.planets.map(p => ({body,sign,house,"
                    "body_meaning,sign_meaning})) — degree/ecliptic_longitude/retrograde만 "
                    "버려짐. SYSTEM_PROMPT grep 'degree'/'ecliptic'/'retrograde'/'역행' 전부 0건.",
    },
    {
        "path": "astrology.aspects",
        "reason": "원본 어스펙트 배열(body1/body2/type/orb) — "
                  "astrology.correspondence.aspect_meanings가 body1/body2/type을 그대로 "
                  "1:1로 이어받고 meaning을 추가한 상위호환 버전(orb만 제외)",
        "evidence": "crossnotics-engine/astrology-correspondence.js:100-105 "
                    "aspectMeanings = astrologyResult.aspects.map(a => ({body1,body2,type,"
                    "meaning})). SYSTEM_PROMPT에서 'orb'/'aspects'가 매치되는 유일한 문맥은 "
                    "규칙10-E 'astrology_synastry.aspects 배열의 각 항목의 .../orb/...' — "
                    "전부 astrology_synastry(제거 대상 아님) 얘기이고 astrology.aspects "
                    "자체(natal, 시너스트리 아님)를 가리키는 문장은 0건(직접 원문 대조 확인).",
        # 'aspects'라는 leaf 이름이 astrology_synastry.aspects(규칙10-E, 제거 대상 아님)에서도
        # 쓰여서 단순 문자열 매칭으로는 오탐(false positive)이 남 — 미사용 검증 시 r10e
        # 블록은 제외하고 검사해야 함(아래 verify_removed_fields_unused_in_prompt 참고).
        "disambiguation_exclude_blocks": ["r10e"],
    },
]

# 배열 원소 내부 sub-필드 제거(전체 배열을 지우는 게 아니라 각 원소에서 특정 키만 제거) —
# 별도 구조로 관리(REMOVED_FIELD_MANIFEST의 path 표기로는 표현이 애매해서 분리).
SUB_ARRAY_FIELD_REMOVALS = [
    {
        "array_path": "behavior.axes",
        "sub_fields": ["counts", "infoSeekingCount"],
        "reason": "축별 원 응답 집계 상세(적극/절충/회피 개수, 추가 정보요청 횟수) — "
                  "규칙9-A-1이 사용할 정확한 sub-필드를 axisLabel/pattern/strength/crossRef "
                  "4개로 명시적으로 한정, counts/infoSeekingCount는 그 목록 밖",
        "evidence": "build_report.py 규칙9-A-1 원문 그대로 인용: 'computed.behavior.axes "
                    "배열의 각 항목(axisLabel/pattern/strength/crossRef)을 그대로 근거로'.",
    },
]

# 필드명이 SYSTEM_PROMPT 원문에 안 나와도 절대 제거하면 안 되는 필드 — 값 자체가 곧
# fallback 지시인 경우들(사용자 승인 조건 4번, 문자 그대로 고정).
PRESERVED_FALLBACK_FIELDS = [
    "saju.se_un_note",
    "saju.dae_yun_note",
    "astrology.unknown_time_note",
    "lunar_conversion_note",
    "saju.lunar_conversion_note",  # top-level과 동일 정보의 saju 하위 사본(run.js가 둘 다 채움)
]

# UNRESOLVED — 안전하다고 확신할 수 없어 이번 단계에서 제거하지 않는 항목(문서화만).
UNRESOLVED_CANDIDATES = [
    {
        "path": "saju.dae_yun",
        "reason_unresolved": "규칙8/9-A가 '이미 지난 대운 구간은 언급 금지'라고 하지만, "
                              "9-A의 lifetime_design 항목은 '전 생애의 기질 패턴을 다루는 것이라 "
                              "위 규칙과 무관'이라고 명시적으로 예외를 둠 — 과거 구간이 정말 "
                              "전혀 필요 없는지 확신할 수 없어 전체 8구간을 그대로 유지함.",
    },
]


def _delete_top_level_path(obj, dot_path):
    """dot_path(예: 'saju.lunar_text')가 있으면 제거, 없으면 아무 것도 안 함(에러 없음)."""
    parts = dot_path.split(".")
    node = obj
    for p in parts[:-1]:
        if not isinstance(node, dict) or p not in node:
            return
        node = node[p]
    if isinstance(node, dict):
        node.pop(parts[-1], None)


def project_computed(computed):
    """computed.json 원본을 절대 수정하지 않고, LLM 호출 직전 전용 view를 새로 만들어 반환한다.

    REMOVED_FIELD_MANIFEST + SUB_ARRAY_FIELD_REMOVALS에 명시된 필드만 제거하고, 그 외
    모든 필드(특히 PRESERVED_FALLBACK_FIELDS)는 원본 그대로 보존한다.
    """
    projection = copy.deepcopy(computed)

    for entry in REMOVED_FIELD_MANIFEST:
        _delete_top_level_path(projection, entry["path"])

    for entry in SUB_ARRAY_FIELD_REMOVALS:
        node = projection
        for p in entry["array_path"].split("."):
            if not isinstance(node, dict) or p not in node:
                node = None
                break
            node = node[p]
        if isinstance(node, list):
            for item in node:
                if isinstance(item, dict):
                    for sub in entry["sub_fields"]:
                        item.pop(sub, None)

    return projection


def _leaf_paths(obj, prefix=""):
    """dict/list를 재귀적으로 훑어 leaf/mid 경로 집합을 만든다(배열은 [0] 대표 원소 기준,
    원소 내부 sub-필드 제거를 잡아내려면 실제로는 원소별 key 차집합도 따로 봐야 하므로
    diff_removed_paths()에서 배열 원소는 별도 처리)."""
    paths = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{prefix}.{k}" if prefix else k
            paths.add(p)
            paths |= _leaf_paths(v, p)
    elif isinstance(obj, list):
        if obj and isinstance(obj[0], (dict, list)):
            paths |= _leaf_paths(obj[0], prefix + "[]")
    return paths


def diff_removed_paths(original, projection):
    """original에는 있었는데 projection에는 없어진 경로 집합을 반환한다(양방향 검증의
    핵심 — 이 결과가 REMOVED_FIELD_MANIFEST + SUB_ARRAY_FIELD_REMOVALS가 선언한 경로와
    정확히 같아야 한다: 그보다 많으면 의도치 않은 제거가 있었다는 뜻, 적으면 제거가 실제로
    적용되지 않았다는 뜻)."""
    before = _leaf_paths(original)
    after = _leaf_paths(projection)
    return before - after


def declared_removed_paths():
    """manifest가 "제거하겠다"고 선언한 "루트" 경로 집합(diff_removed_paths()가 반환하는
    실제 제거 경로들의 기대값 — 단, 배열/객체 하나를 통째로 지우면 그 자손 leaf 경로들도
    diff에 전부 나타나므로, 대조는 declared 자체가 아니라 unauthorized_removed_paths()의
    "조상-자손" 판정으로 해야 한다)."""
    declared = {entry["path"] for entry in REMOVED_FIELD_MANIFEST}
    for entry in SUB_ARRAY_FIELD_REMOVALS:
        for sub in entry["sub_fields"]:
            declared.add(f"{entry['array_path']}[].{sub}")
    return declared


def unauthorized_removed_paths(actual_removed, declared=None):
    """actual_removed(diff_removed_paths()의 결과) 중, declared_removed_paths()에 선언된
    어떤 경로의 "자기 자신 또는 자손"도 아닌 것만 골라낸다 — 예를 들어 declared에
    'astrology.planets'가 있으면 diff에 나타나는 'astrology.planets[].degree' 같은 자손
    경로는 전부 승인된 제거로 간주하고, declared에 없는 완전히 다른 경로만 "무단 제거"로
    본다."""
    if declared is None:
        declared = declared_removed_paths()
    unauthorized = set()
    for path in actual_removed:
        is_authorized = any(
            path == d or path.startswith(d + ".") or path.startswith(d + "[]")
            for d in declared
        )
        if not is_authorized:
            unauthorized.add(path)
    return unauthorized


def verify_removed_fields_unused_in_prompt(system_prompt_text, prompt_blocks=None):
    """REMOVED_FIELD_MANIFEST의 각 필드 leaf 이름이 실제로 SYSTEM_PROMPT 원문에 없는지
    재확인한다(수동으로 남긴 evidence를 코드 레벨에서 재검증) — 앞으로 SYSTEM_PROMPT가
    수정되면서 이 필드들이 참조되기 시작하면 이 함수가 그걸 잡아낸다.

    disambiguation_exclude_blocks가 지정된 항목은, prompt_blocks(rule_id -> 블록 텍스트
    딕셔너리, build_report._PROMPT_BLOCKS)가 주어졌을 때 그 블록들의 텍스트를 검사 대상에서
    빼고 확인한다 — 예: 'aspects'라는 leaf 이름은 astrology_synastry.aspects(규칙10-E,
    제거 대상 아님)에서도 쓰여서, 그 블록만 빼고 나머지 전체에서 등장하는지 봐야 진짜
    오탐 없이 확인할 수 있다.

    한계: leaf 이름 문자열 매칭이라 "그 필드를 설명하지만 이름을 안 쓴 서술"은 못 잡는다 —
    그래서 이 함수 하나만으로 안전을 주장하지 않고, manifest의 evidence(사람이 직접 원문을
    읽고 확인한 근거)와 함께 사용한다.
    """
    def _text_for(entry):
        exclude = entry.get("disambiguation_exclude_blocks")
        if not exclude or not prompt_blocks:
            return system_prompt_text
        text = system_prompt_text
        for rule_id in exclude:
            block = prompt_blocks.get(rule_id, "")
            if block:
                text = text.replace(block, "")
        return text

    results = []
    for entry in REMOVED_FIELD_MANIFEST:
        leaf = entry["path"].split(".")[-1]
        found = leaf in _text_for(entry)
        results.append({
            "path": entry["path"], "leaf": leaf, "found_in_prompt": found,
            "excluded_blocks": entry.get("disambiguation_exclude_blocks"),
        })
    for entry in SUB_ARRAY_FIELD_REMOVALS:
        for sub in entry["sub_fields"]:
            found = sub in system_prompt_text
            results.append({
                "path": f"{entry['array_path']}[].{sub}", "leaf": sub, "found_in_prompt": found,
                "excluded_blocks": None,
            })
    return results


def verify_fallback_fields_preserved(original, projection):
    """PRESERVED_FALLBACK_FIELDS가 원본에 존재했다면 projection에도 반드시 존재하는지 확인."""
    results = []
    for path in PRESERVED_FALLBACK_FIELDS:
        parts = path.split(".")

        def _get(node):
            for p in parts:
                if not isinstance(node, dict) or p not in node:
                    return None, False
                node = node[p]
            return node, True

        _, existed_in_original = _get(original)
        _, exists_in_projection = _get(projection)
        ok = (not existed_in_original) or exists_in_projection
        results.append({
            "path": path, "existed_in_original": existed_in_original,
            "exists_in_projection": exists_in_projection, "ok": ok,
        })
    return results
