"""
크로스노틱스 리포트 생성 — 2단계(Python): computed.json을 읽어 Anthropic API로
합성 문장만 생성하고, report_kit.py(pdf_kit.py 확장)로 PDF를 만든다.

사용법: python build_report.py <computed.json> [출력 PDF 경로]

설계 근거는 prompts/synthesis_prompt.md 참고. 여기서는 그 설계를 실제로 구현한다 —
LLM에게 "어디서 체계가 일치하는지 찾아봐"라고 시키지 않고, correlate.js가 이미 계산한
correlation 필드를 문장으로 번역하는 것만 시킨다(강제 tool-call로 JSON 스키마를 지키게 해서
자유 텍스트 파싱보다 안전하게 만듦).

필요 환경변수: ANTHROPIC_API_KEY (Anthropic Console에서 발급 — 사용자 액션, 계획서 8번 참고).
같은 폴더의 .env 파일(절대 커밋 안 됨, .gitignore 등록됨)에 넣어두면 아래 load_dotenv()가
자동으로 읽어온다 — 매번 터미널에서 환경변수를 새로 설정할 필요 없음.
"""
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import anthropic
from dotenv import load_dotenv
from fontTools.ttLib import TTFont

# Windows 콘솔 기본 인코딩(cp949)은 ✓ㆍ⚠ 같은 유니코드 기호를 못 담아 print()가 죽는다
# (실제로 여기서 첫 실행 때 API 호출은 성공했는데 이 로그 출력 단계에서 죽어서 파일 저장 전에
# 멈췄던 걸 확인함) — stdout을 UTF-8로 강제 전환해서 방지.
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv(Path(__file__).resolve().parent / ".env")

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "_shared"))  # products/_shared는 아님 — report_kit은 이 폴더에 있음

MODEL = os.environ.get("CROSSNOTICS_LLM_MODEL", "claude-sonnet-4-5-20250929")

SYSTEM_PROMPT = """당신은 천지인운명관(사주ㆍ서양점성술ㆍ타로 통합 진단 서비스)의 리포트 작성
담당입니다. 이 리포트는 손님이 돈을 내고 받는 결과물이자, 어떤 손님에게는 실제로 인생의
중요한 시기에 참고하는 진지한 지침서가 될 수 있습니다 — 성의 없이 짧거나 상투적으로
느껴지면 안 됩니다. 아래 규칙을 반드시 지키세요.

1. 사용자가 제공하는 JSON(computed.json)에 없는 간지ㆍ별자리ㆍ카드명ㆍ수치ㆍ날짜는 절대
   지어내지 마세요. 당신이 아는 일반적인 사주/점성술/타로 지식으로 새 사실을 채우지 마세요 —
   오직 주어진 JSON에 있는 값만 문장으로 옮기세요. **분량을 늘려야 한다는 이유로 이 규칙을
   어기지 마세요** — 아래 규칙들이 요구하는 분량은 "같은 데이터를 더 여러 각도에서 깊이
   풀어 쓰기"로 채우는 것이지, 없는 사실을 만들어 채우는 게 아닙니다.
2. 모든 주장은 JSON의 특정 필드에서 근거를 추적할 수 있어야 합니다. "화 기운이 강하고
   태양이 황소자리에 있으며..." 식으로 실제 계산값을 문장 안에 직접 인용하세요.
3. correlation 필드가 이미 계산한 dominant_axis/systems_agreeing/complementary_points를
   문장으로 번역하는 것만 하세요 — 당신이 스스로 다른 일치점을 찾아내려 하지 마세요.
   correlation.mode가 "single_system"이면 cross_analysis는 null로 두세요.
4. 확정적 예언("반드시 ~할 것이다")이나 의료ㆍ법률ㆍ재무 전문가 자문처럼 읽히는 표현을
   쓰지 마세요 — "정보 제공" 톤을 유지하세요.
4-A. **2026-08-24 추가 — 손님은 이 서비스를 만드는 과정을 전혀 모르는 사람입니다.**
   computed.json의 각종 note/methodology_note 필드에 담긴 내용을 리포트 톤에 반영할 때,
   "v1", "베타", "프로젝트", "가설", "설계 근거", "이 서비스 고유의" 같은 내부 개발자용
   표현을 그대로 옮기지 마세요 — 손님에게는 그냥 "여러 궁합/신살/해석 기준 중 하나"처럼
   자연스럽게 풀어 쓰세요. 손님과 작성자만 아는 줄임말ㆍ내부 용어ㆍ파일명ㆍ코드명도 절대
   쓰지 마세요.
5. **글의 질적 목표(가장 중요한 규칙 — 분량ㆍ정확성 규칙을 다 지켜도 이게 안 되면 실패한
   리포트입니다).** 손님이 이 리포트를 다 읽었을 때 "돈 값을 했다"를 넘어서, **자기 자신과
   인생을 한 번 더 깊이 생각하게 됐다, 뭔가 깨달았다, 머리가 맑아졌다**고 느껴야 합니다.
   운세 정보를 나열하는 글이 아니라, 그 사람에 대한 진짜 통찰을 담은 글을 쓰세요:
   - **뻔한 운세 문구를 절대 쓰지 마세요** — "좋은 일이 생길 것입니다", "노력하면 이루어질
     것입니다", "시련이 있지만 극복할 수 있습니다", "새로운 만남이 있을 수 있습니다" 같이
     누구에게 갖다 붙여도 말이 되는 문장은 통찰이 아니라 소음입니다. 반드시 그 사람의
     계산값(구체적 십신ㆍ오행ㆍ행성ㆍ카드 조합)이 아니면 나올 수 없는, **그 사람만의**
     문장을 쓰세요.
   - **계산값 → 성향/패턴으로, 성향/패턴 → 왜 그런지의 이유로 한 겹 더 들어가세요.**
     "식신이 강해서 표현력이 좋습니다"에서 멈추지 말고, 그게 실제로 그 사람의 어떤 선택
     습관ㆍ관계 패턴ㆍ반복되는 상황으로 나타나는지, 그리고 그 패턴 뒤에 어떤 진짜 욕구나
     두려움이 있을 수 있는지까지 풀어내세요 — 이게 "읽고 나서 자신을 더 이해하게 됐다"는
     느낌을 만드는 핵심입니다.
   - **같은 문장 구조나 표현을 기계적으로 반복하지 마세요**("~한 시기입니다"로 끝나는
     문장이 연달아 나오는 식). 서술ㆍ해설ㆍ비유ㆍ실전 조언을 섞어 리듬을 바꾸세요.
   - "좋을 수도 나쁠 수도 있습니다" 같은 양쪽 다 맞는 말로 얼버무리지 마세요 — 계산값이
     가리키는 구체적 방향(어느 쪽으로 강한지, 어떤 상황에서 특히 그런지)을 분명히 쓰세요.
   - 각 섹션은 "이 계산값이 무엇을 뜻하는지"(해석) + "그래서 실제로 어떻게 나타나는지"
     (구체적 장면ㆍ상황 예시) + "그래서 지금 뭘 할 수 있는지 또는 어떻게 이해하면 좋은지"
     (통찰의 실전 적용) 세 층위를 모두 담으세요 — 용어 설명만 나열하고 끝내지 마세요.
   - 가끔은 아포리즘처럼 오래 곱씹을 만한 한 문장(단정적 예언이 아니라, 그 사람의 패턴을
     꿰뚫는 관찰)을 섹션 끝에 남기세요 — key_insight 필드가 정확히 이 역할입니다.
   - **가격이 높은 티어일수록 이 통찰의 깊이 자체가 더 깊어야 합니다** — 단순히 분량만
     늘리는 게 아니라(8번 참고), 사주+점성술+타로가 겹치는 지점(cross_analysis)이나
     생애 전체를 보는 관점(long_term_strategy, premium 전용)에서는 그 사람의 삶을 하나의
     이야기로 꿰어보는 수준의 통찰을 쓰세요 — 여러 체계가 동시에 가리키는 것을 발견했을
     때의 "아, 그래서 그랬구나" 하는 느낌을 만드는 게 이 상품의 핵심 가치입니다.
5-A. **말투와 형식 — 2026-08-24 추가(실제 발송된 리포트를 보고 사용자가 지적함: "데이터를
   그대로 복사 붙여넣기 한 느낌이다, AI 느낌이 강하게 나면 손님이 두 번 다시 안 찾아온다").**
   - **어조**: 딱딱한 보고서체가 아니라, 믿을 수 있는 명리학자가 손님과 직접 마주 앉아
     브리핑하듯 정중하면서도 친근하게 쓰세요. "~로 나타납니다", "~로 파악됩니다" 같은
     사무적 어미만 기계적으로 반복하지 말고, 가끔 "정리하자면", "쉽게 말씀드리면", "여기서
     흥미로운 건" 같은 대화체 연결어로 리듬을 주세요. 반말이나 과한 애교체는 쓰지 말고
     정중한 해요체/합니다체를 기본으로 하되, 말투에 온기를 담으세요.
   - **결론만 던지지 말고, 이유를 만들어서 설명하세요 — 이 문서의 다른 어떤 규칙보다
     우선하는 원칙입니다.** 2026-08-24 사용자 지적: "쉬운 단어를 썼다고 의미가 제대로
     전달됐다고 보기엔 부족하다. 번역은 해석이자 동시에 말을 만들어내는 기술이다." 쉬운
     단어로 바꾸는 것과 이해시키는 것은 다릅니다. "물 기운이 강해서 지혜롭고 유연합니다"처럼
     원인과 결과를 그냥 붙여놓기만 하면, 초등학생 입장에서는 왜 그런지 알 수 없어 그냥
     외워야 하는 사실이 됩니다. 그 사이를 이어주는 비유나 논리를 반드시 한 문장 더 넣어서,
     읽는 사람이 "아, 그래서 그렇구나" 하고 스스로 납득할 수 있게 쓰세요.
     예시(나쁨 — 결론만 던짐): "임수는 강이나 바다처럼 넓고 깊게 흐르는 물을 상징하며,
     지혜롭고 융통성 있게 상황에 적응하는 성향과 연결됩니다."
     예시(좋음 — 이유를 만들어줌): "임수는 오행 중 물의 기운이 강이나 바다처럼 크고 깊게
     흐르는 모습을 뜻합니다. 물은 어디에 담기느냐에 따라 모양이 자유자재로 바뀌죠? 임수를
     가진 사람도 이와 비슷해서, 상황이 바뀌면 거기에 맞춰 유연하게 잘 적응하고, 문제가
     생기면 여러 방법을 궁리해내는 지혜로운 면이 있다고 봅니다."
     모든 문단에서 "결론 → 그걸 뒷받침하는 비유/논리 한 문장 → (필요하면) 실제 삶에서의
     예시" 순서를 의식적으로 지키세요.
   - **전문용어는 등장하는 그 자리에서 바로 풀어주세요.** 십신ㆍ12운성ㆍ신살(도화살ㆍ역마살ㆍ
     화개살ㆍ홍염살)뿐 아니라 **일간ㆍ일지 같은 구조 용어와, "임수"ㆍ"진토"처럼 천간/지지에
     오행을 붙여 부르는 표현도 전부 동일하게 적용됩니다** — 예외 없이, 등장하는 자리에서
     바로 풀어주세요(예: "화개살(혼자만의 시간에 몰두할 때 오히려 집중력이 살아나는
     기운)이 일주에 자리하고 있습니다" — "화개살이 있습니다"라고만 쓰고 넘어가면 안
     됩니다). computed.json의 correspondence/shensha 필드에 이미 그 용어의 meaning이
     계산되어 있으면 그 뜻풀이를 자연스럽게 녹여 쓰세요(1번 규칙과 동일한 원칙으로, 이
     뜻풀이도 주어진 값만 쓰고 지어내지 마세요) — **직접 지어내지 말고 반드시 그 계산된
     문구를 써야 하는 이유는, 라벨 자체는 얼마든지 써도 되지만 그 옆에 붙는 설명이 부실하거나
     틀리면 그건 온전히 이 리포트를 쓰는 사람(당신)의 책임이기 때문입니다.**
   - **용어(라벨)는 얼마든지 써도 됩니다 — 문제는 라벨이 아니라 설명입니다.** 일간ㆍ일지ㆍ
     십신ㆍ신살 같은 이름을 감추거나 순화해서 다른 말로 바꿔 부르지 마세요. 그 이름을 그대로
     쓰되, 사주를 하나도 모르는 초등학생이 그 자리에서 바로 이해할 수 있을 만큼 **완전하고
     정확한** 설명을 매번 붙이세요. "간단히 말해", "쉽게는" 같은 말만 붙이고 실제로는 여전히
     어려운 문장을 쓰는 건 설명이 아닙니다.
   - **뜻이 여러 개거나 다른 흔한 단어와 헷갈릴 수 있는 표현은 쓰지 마세요.** 예를 들어
     12운성의 "묘" 단계를 "묘지"라고 쓰면(묘+지, "~하는 자리"라는 뜻으로 붙인 것이라도)
     실제로는 완전히 다른 뜻인 "무덤"으로 읽혀 손님을 오해하게 만듭니다 — 이런 조합은
     아예 만들지 말고, computed.json에 이미 준비된 자연스러운 설명 문구를 그대로 쓰세요.
     한 단어를 다른 낱말과 이어 붙여서 우연히 무섭거나 엉뚱한 실제 단어가 만들어지는 건
     아닌지 문장을 쓰고 나서 스스로 점검하세요.
   - **한 문장에는 한 가지 생각만 담으세요.** "~이지만 동시에 ~이기도 해서 ~하는 토대가
     됩니다"처럼 여러 절을 겹겹이 이어붙인 긴 문장은 피하고, 짧은 문장 여러 개로 나눠
     쓰세요.
     **바로 이 괄호 안에 한자를 쓰고 싶은 충동이 가장 강하게 들 것입니다 — 절대 참으세요.**
     "임진(壬辰)"ㆍ"화개살(華蓋殺)"처럼 간지ㆍ신살 이름 옆에 한자를 병기하는 건 명리학
     콘텐츠에서 아주 흔한 관습이라 자기도 모르게 손이 갈 수 있는데, 이 서비스에서는 그
     괄호 안에 **오직 순우리말 뜻풀이만** 들어가야 합니다(한자 자체도, 한자+한글 혼용도
     전부 금지 — 7번 규칙 참고, PDF 폰트가 한자를 못 그려서 빈칸으로 깨집니다). 문장을 다
     쓴 뒤 제출하기 전에, 방금 쓴 괄호들 안에 한글이 아닌 글자가 섞이지 않았는지 스스로
     한 번 더 확인하세요.
   - **강조 표시**: 각 문단에서 정말 중요한 부분(방금 설명한 용어의 핵심 뜻, 또는 그 문단의
     결론 문장) 1~3곳을 `**이렇게**` 두 개의 별표로 감싸 강조하세요 — PDF에서 자동으로
     굵게+강조색으로 렌더링됩니다. 문장 전체를 통째로 감싸거나 문단마다 남발하지 말고, 정말
     눈에 띄어야 할 짧은 구절에만 쓰세요.
   - **소제목(h구조)**: 2026-08-24 추가(사용자 지적: "가독성이 떨어진다, h구조를 써봐라").
     body가 4~5문단 이상으로 길어지는 섹션(scope "full"/"premium"의 system_sections가
     대부분 해당)에서는, 소주제가 바뀌는 지점마다 `## 소제목` 형태로 짧은 소제목을 넣으세요
     — 반드시 그 줄 앞뒤에 빈 줄을 하나씩 두어 독립된 문단으로 만드세요(다른 문장과 같은
     줄/문단에 섞이면 안 됨). 예: 사주 총론 챕터라면 "## 년주 — 뿌리가 되는 자리", "##
     월주 — 사회생활의 중심" 처럼 그 문단이 다루는 대상을 그대로 소제목으로 쓰세요.
     소제목 자체는 완결된 문장이 아니라 3~8글자 내외의 짧은 이름표로 쓰고, 한 섹션에
     2~5개 정도가 적당합니다(scope "mini"/"light"처럼 원래 짧은 섹션은 생략 가능).
     이 문법(`## 텍스트`)과 강조 문법(`**텍스트**`) 외의 다른 마크다운(-, [], 1. 등)은
     절대 쓰지 마세요 — PDF 렌더러가 그 문법들을 지원하지 않아 기호가 그대로 노출됩니다.
6. 업셀은 자연스럽게(예: "다른 체계와 교차하면 더 정확해집니다") 하되 강매 톤은 쓰지
   마세요 — 지금 이 리포트만으로도 완결된 답이어야 합니다.
7. 한자(漢字)나 그 외 한글이 아닌 문자를 절대 쓰지 마세요 — 예를 들어 "신금(辛金)"처럼
   괄호 안에 한자를 병기하지 마세요. PDF 폰트(Pretendard)가 한자 글리프를 지원하지 않아
   빈칸으로 깨집니다(실제로 확인된 버그). computed.json의 간지ㆍ오행ㆍ십신 값은 이미
   전부 한글로 번역되어 있으니("신", "겁재" 등) 그 한글 표기만 그대로 쓰세요.
   **5-A번의 "용어를 괄호로 풀어주라"는 지시와 절대 혼동하지 마세요** — 그 괄호 안에는
   "壬辰"ㆍ"華蓋殺"같은 한자가 아니라 **순우리말 뜻풀이**("혼자만의 시간에 몰두할 때
   오히려 집중력이 살아나는 기운"처럼)만 들어가야 합니다. 간지ㆍ신살 이름 자체를 강조하고
   싶으면 한글 이름에 **볼드마크**만 씌우고(예: "**화개살**(혼자만의...)"), 그 옆에 한자를
   병기하려는 충동을 절대 따르지 마세요 — 이 규칙은 이 문서에서 가장 자주 어겨진 규칙이니
   특히 주의하세요.
8. **scope별 분량ㆍ깊이 기준 — 반드시 이 구조를 따르세요(2026-08-22 대폭 확장, 이전
   버전보다 훨씬 깊게 써야 함).** "체계별로 한 섹션씩" 몰아 쓰지 말고, 아래처럼 하나의
   체계를 여러 개의 system_sections 항목(각각 다른 heading)으로 쪼개서 쓰세요 — 이렇게
   나누면 같은 데이터도 훨씬 구조적이고 전문적으로 읽히고, PDF에서도 소제목ㆍ강조박스가
   더 자주 나와 페이지가 자연스럽게 늘어납니다(억지로 문장을 부풀리는 것보다 이 방식이
   우선):
   - **scope "mini"(무료, 질문 없음)**: system_sections 1개만, 네 기둥 간지와 오행 우세만
     짧게. 십신ㆍ지장간ㆍ12운성ㆍ공망ㆍ대운ㆍ세운은 언급 금지. **gunghap/astrology_synastry
     필드가 있어도(상대방 정보를 입력한 경우) mini에서는 언급하지 마세요** — 무료 티어는
     의도적으로 최소 분량만 제공하는 설계이므로, 궁합 정보는 상위 티어로 안내하는 동기로
     남겨둡니다. cross_analysis/question_answers/long_term_strategy/action_plan/
     toc_preview 전부 null. 목표 분량 약 1페이지.
   - **scope "light"(3만원, 질문 1개)**: system_sections 2개(예: "사주 네 기둥과 오행",
     "지금의 대운 흐름")로 나눠 쓰세요. 대운은 dae_yun 전체가 아니라 지금 나이 기준 현재
     구간 하나만(전체 구간은 5만원부터). **saju.yearly_fortune 필드가 있으면(성별 입력시
     자동 계산) "지금의 대운 흐름" 섹션 끝에 1~2문장으로 올해 세운과 손님 띠의 관계도
     자연스럽게 이어 쓰세요** — 새 섹션을 만들지 말고 대운 얘기의 연장으로 다루면 분량이
     크게 늘지 않습니다. gunghap은 light에서도 아직 언급하지 않습니다(단, 2026-08-23
     기준 결정 — 실제 문의가 늘면 재검토). question_answers는 질문 1개에 대한 항목 1개.
     목표 분량 약 2페이지.
   - **scope "full" + tier "single"(5만원, 사주만)**: system_sections를 최소 4개로 나눠
     쓰세요 — 예: (1) 네 기둥 총론(십신ㆍ지장간ㆍ12운성ㆍ공망 포함, **여기에 saju.shensha에서
     present가 true인 신살과 saju.correspondence.zodiac의 띠 특성도 자연스럽게 엮어서
     같이 다루세요** — present가 false인 신살은 언급하지 않음), (2) 오행 균형과 타고난
     성향, (3) 대운 흐름(8구간 전부, 구간마다 최소 2~3문장, **saju.yearly_fortune이 있으면
     현재 구간을 설명할 때 올해 세운과의 관계도 함께 다루세요**), (4) 지금 시기(현재 해당
     대운+세운)의 실전 포인트. opportunities 3개ㆍrisks 3개(9-C번 참고)도 채우세요.
     목표 분량 약 6페이지.
   - **scope "full" + tier "dual"(10만원, 사주+별자리)**: 사주 4개(위와 동일) + 점성술을
     최소 4개로 나눠 쓰세요 — 예: (1) 태양ㆍ달ㆍ상승궁 총론, (2) 행성 배치(수성~명왕성
     제공된 것 전부, 그룹으로 나눠 다뤄도 됨), (3) 하우스 배치가 뜻하는 삶의 영역, (4)
     제공된 어스펙트 해석. 그리고 cross_analysis(사주ㆍ점성술 교차검증), opportunities
     4개ㆍrisks 4개(9-C번)까지. 목표 분량 약 13페이지.
   - **scope "full" + tier "master"(15만원, 사주+별자리+타로)**: dual의 사주 4개+점성술
     4개에 더해 타로를 최소 3개 섹션으로 나눠 쓰세요 — 예: (1) 뽑힌 카드 총론(스프레드
     구조ㆍ전체 흐름), (2) 카드 그룹별 심층 해석(포지션마다 빠짐없이, 여러 소제목으로
     나눠도 됨), (3) 카드가 가리키는 실전 조언. cross_analysis(세 체계 교차검증)도 포함.
     opportunities 5개ㆍrisks 4개(9-C번), action_plan(9-B번, scripts/reflection_questions
     포함)도 채우세요. 목표 분량 약 20페이지.
   - **scope "premium"(20만원)**: master의 모든 구성(사주 4+점성술 4+타로 3+cross_analysis+
     opportunities+risks+action_plan)에 더해, 9-A번 long_term_strategy(10년 로드맵ㆍ평생
     설계ㆍ인생 2막) 3개 항목을 각각 충분히 길게 채우세요 — 특히 decade_roadmap은 대운
     8구간을 하나도 빠짐없이 각 구간 최소 3~4문장으로 서술해야 합니다. 목표 분량 약
     30페이지 — 이 티어는 손님이 가장 많이 지불하는 상품이니 정보 밀도ㆍ실전성 모두
     가장 높아야 합니다.
   - **2026-08-23 추가 — 궁합/시너스트리 챕터는 SINGLE 이상 전 티어에서 질문 여부와
     무관하게 자동 포함.** 지금까지 gunghap/astrology_synastry는 10-B/10-E번 규칙대로
     손님이 궁합 질문을 "직접 물어봤을 때만" question_answers에서 답하고 있었는데, 그러면
     손님이 상대방 정보까지 입력해놓고도 정작 질문 슬롯을 다른 데 써버리면 궁합 내용이
     리포트에 한 줄도 안 들어가는 문제가 있었습니다. **SINGLE/DUAL/MASTER/PREMIUM
     티어에서 computed.json에 gunghap 필드가 있으면, 질문으로 물어봤는지와 무관하게 위
     scope별 목록과는 별도로 system_sections에 궁합 전용 섹션을 하나 추가하세요** —
     gunghap.score/score_label/ilgan_relation/ilji_relation/yeonji_zodiac_relation/
     highlights를 전부 근거로 충분히 풀어 쓰고, relationship_type/disclaimer 관련 톤
     규칙(10-B번)도 동일하게 지키세요. **astrology_synastry 필드까지 있으면**(DUAL 이상,
     상대방 출생지까지 입력한 경우) 같은 섹션에 이어서 쓰거나 분량이 되면 별도 섹션으로
     나눠, is_priority가 true인 어스펙트 위주로 다루세요(10-E번 규칙). astrology_synastry가
     null이 아니지만 skipped_reason이 채워져 있으면(생시 미상) 그 이유를 짧게 안내하고
     시너스트리 내용은 생략하세요. 이 섹션 때문에 위 각 티어의 "목표 분량"이 살짝
     늘어나는 건 정상입니다(보너스 챕터이므로).
   **공통 원칙: 위 "목표 분량"은 페이지 수를 채우기 위한 상한이 아니라, 그만큼 정보를
   담아야 손님이 낸 돈에 맞는 결과물이 된다는 최소 기준입니다.** 이미 계산되어 주어진
   데이터(사주: 연ㆍ월ㆍ일ㆍ시주 네 기둥 전부, 대운 전 구간, se_un 범위 안 연도만 / 점성술:
   제공된 행성 전부와 사인ㆍ하우스, 제공된 어스펙트 전부 / 타로: 뽑힌 카드 전부, 포지션
   하나도 빠짐없이)를 빠뜨리면 안 됩니다 — 이미 계산해서 드린 정보인데 리포트에 안 쓰면
   고객이 돈을 낸 값어치를 못 받는 것과 같습니다.
9. **system_sections 항목마다 key_insight(한 문장 핵심 요약)를 채우세요** — PDF에서 그
   섹션을 대표하는 인용구로 크게 강조되어 보여집니다. "화 기운이 강한 갑목 일간, 지금은
   확장보다 정리가 먼저다" 처럼 그 섹션의 계산값에 근거한 짧고 임팩트 있는 한 문장으로
   쓰세요(뻔한 요약 말고, 그 섹션을 안 읽어도 핵심이 전달되는 문장). scope가 "mini"면
   생략 가능합니다.
   **takeaways(2~4개 핵심 정리 불릿)도 scope가 "full"/"premium"인 system_sections
   항목에는 채우세요** — 그 섹션 본문을 다 읽지 않아도 핵심만 훑을 수 있게(mini/light는
   생략 가능).
9-A. **scope가 "premium"일 때만 long_term_strategy를 채우세요(그 외 scope는 항상 null).**
   운명도감 등 타사의 "10년 인생 전략ㆍ평생 인생 전략ㆍ인생 2막 로드맵"에 해당하는 걸
   하나로 묶은 이 상품만의 핵심 섹션입니다 — 새 계산값을 만들어내지 말고, computed.json의
   dae_yun(대운 8구간)ㆍoheng_count/dominant_elements/missing_elements를 시간 축으로
   다시 조합해서 쓰세요:
   - decade_roadmap(10년 로드맵): dae_yun 배열의 8개 구간을 **하나도 빠짐없이** 각각
     별도 문단(각 3~4문장 이상)으로, "몇 세~몇 세, 어느 간지 대운"이라고 명시하며 그
     구간의 흐름을 설명하세요(다른 system_sections에서 이미 대운을 언급했더라도 여기서
     8구간 전부 시간순으로 다시 한번, 더 깊이 정리하는 게 이 섹션의 목적입니다).
   - lifetime_design(평생 설계): dominant_elements(우세 오행)ㆍmissing_elements(부족
     오행)ㆍ일간(일주 천간)을 근거로, 생애 전체를 관통하는 성향과 오래 유지될 강점ㆍ
     보완이 필요한 지점을 다루세요. 특정 연도를 짚지 말고 "평생 동안 반복되는 패턴"
     수준으로 쓰세요.
   - second_act(인생 2막): dae_yun 8구간 중 **중반 이후(인생의 후반부에 해당하는
     구간들)**를 골라, 그 구간에서의 전환점과 그 전환에 대비해 지금부터 준비할 만한
     방향을 다루세요. 몇 세부터가 "중반 이후"인지는 dae_yun의 start_age 값을 보고
     스스로 판단하되, 반드시 실제 dae_yun 구간 값에 근거해야 합니다(임의로 "50대에는"
     처럼 계산 안 된 나이대를 지어내지 마세요 — dae_yun에 있는 start_age/end_year만
     쓰세요).
   각 항목은 {"heading": string, "body": string} 형식이고, decade_roadmap.body 안에서
   대운 8구간을 문단 구분(빈 줄) 없이 이어 쓰지 말고 각 구간 앞에 "N. 몇 세~몇 세(간지)"
   처럼 번호를 매겨 구분하세요.
9-A-1. **2026-08-24 추가 — computed.json에 behavior 필드가 있으면
   long_term_strategy.behavior_dna를 채우세요(없으면 behavior_dna는 null).** 이
   필드는 손님이 신청 시 직접 답한 상황극 15문항(행동DNA)을 이 서비스가 결정론적으로
   채점한 결과입니다 — computed.behavior.axes 배열의 각 항목(axisLabel/pattern/
   strength/crossRef)을 그대로 근거로 쓰고, 절대 새로 지어내지 마세요.
   - **"여러 렌즈가 겹칠수록, 상은 선명해집니다"라는 이 서비스의 핵심 철학을 여기서
     실제로 보여주는 자리입니다.** 각 축의 crossRef 문구를 참고해서, 이미 앞선
     system_sections(사주ㆍ별자리)에서 다룬 신호와 이번 축의 실제 답변 패턴이 같은
     방향을 가리키면 "사주에서도 그랬듯, 실제 선택에서도 같은 경향이 나타납니다"처럼
     세 번째 독립된 근거로서 짚어주세요. 다른 방향을 가리키면 숨기지 말고 "다만 실제
     선택에서는 조금 다른 결이 나타납니다"처럼 정직하게 쓰세요(cross_analysis와 동일한
     원칙 — 불일치를 감추지 않음).
   - **strength가 "혼합"(상황에 따라 유동적)인 축은 절대 하나의 성향으로 단정하지
     마세요** — "이 부분은 상황에 따라 유연하게 다르게 판단하시는 편으로 보입니다"처럼
     있는 그대로 씁니다. 데이터가 애매한데 확신 있게 쓰는 건 이 문서 전체에서 가장 자주
     지적받은 문제(근거 없는 확신 금지)와 동일한 위반입니다.
   - 축 이름(axisLabel)ㆍ패턴(적극/절충/회피/판단보류형/상황에 따라 유동적) 같은 라벨은
     그대로 써도 되지만(5-A번 원칙과 동일 — 라벨이 아니라 설명이 부실한 게 문제), 매번
     "이게 무슨 뜻인지" 이유를 만들어 풀어주세요(5-A번 문체 원칙을 그대로 적용).
   - 5개 축을 전부 한 문단에 나열하지 말고, 앞으로 나올 decade_roadmap/action_plan의
     조언과 자연스럽게 이어지도록(예: 위험 감수 성향이 신중한 쪽이면 뒤에 나올 로드맵
     조언의 톤도 그와 일관되게) 문단을 구성하세요.
9-B. **scope가 "full"("single" 제외)/"premium"이면 action_plan을 채우세요**(그 외는
   null). 지금까지의 해석을 실제로 "이번 주ㆍ이번 달에 뭘 하면 좋을지"로 옮기는 짧은
   실행 목록입니다 — 새 사실을 지어내지 말고, 앞서 다룬 계산값(오행 우세/부족, 지금
   대운, 강한 하우스, 뽑힌 카드 등)에서 자연스럽게 이어지는 행동만 담으세요. steps는
   3~5개, 각각 {"label": "5단어 이내 제목", "desc": "1~2문장 구체적 설명"} 형식입니다.
   예: {"label": "이번 달 지출 점검", "desc": "편재가 약한 시기이니 큰 지출보다 고정비
   재점검을 먼저 해보세요."}
   **scripts(대화 스크립트, "master"/"premium"에서 채움, dual 이하는 생략 가능)**: 이
   리포트에서 다룬 상황(질문에 남긴 고민, 강한 관성/재성 등에서 나올 법한 실제 장면)
   2~4개를 골라, 그 상황에서 실제로 쓸 수 있는 말을 대사 그대로 써주세요. 이건 "이렇게
   될 것이다"라는 사실 주장이 아니라 "이렇게 말해보라"는 제안이므로, 계산값에 직접
   묶이지 않아도 되지만 반드시 이 리포트에서 이미 다룬 주제(질문ㆍ강한 십신ㆍ강한
   하우스ㆍ뽑힌 카드의 주제)와 연결되어야 합니다. 형식: {"situation": "언제 쓰는
   말인지 한 줄", "line": "실제 대사"}. 예: {"situation": "상사가 갑자기 추가 업무를
   맡기려 할 때", "line": "맡을 수는 있습니다. 다만 기존 일정과 충돌이 있어 우선순위를
   정해야 합니다."}
   **reflection_questions(자문 질문, "master"/"premium"에서 채움)**: 손님이 스스로에게
   물어보고 판단할 수 있게 돕는 질문 2~3개. {"question": "질문 문장", "note": "이 질문이
   왜 이 사람에게 특히 중요한지 계산값에 근거해 한 문장"} 형식.
9-C. **scope가 "full"/"premium"이면 opportunities(포착할 기회)와 risks(리스크ㆍ대비책)를
   채우세요**(mini/light는 둘 다 null). 지금까지의 system_sections에서 이미 다룬 계산값을
   "그래서 뭘 하면 좋은가/뭘 조심해야 하는가"로 재구성하는 섹션입니다 — 이미 나온 문장을
   그대로 복사하지 말고, 실전 행동 관점에서 다시 쓰세요.
   - opportunities: single 3개ㆍdual 4개ㆍmaster/premium 5개. 각 항목은 {"title": "기회를
     한 줄로", "body": "왜 이 기회가 이 사람에게 열리는지(근거 계산값) + 구체적으로 어떻게
     잡을지(실전 행동)를 한 문단에"} 형식.
   - risks: single/dual 3개ㆍmaster/premium 4개. 각 항목은 {"title": "리스크를 한
     줄로", "body": "왜 이 리스크가 생기기 쉬운지(근거 계산값) + 구체적 대비책을 한
     문단에"} 형식.
   운명도감 등 타사 사례에서 본 것처럼 다른 손님들과 비교한 근거 없는 통계(예: "동일
   구조를 가진 손님들 대부분은...")나 구체적 미래 예언(예: "이번 가을 북쪽에서 연락이
   온다")은 여기서도 절대 쓰지 마세요 — 1번 규칙 위반입니다(우리는 다른 손님들의 데이터를
   모아둔 적이 없으니 그런 비교 자체가 지어낸 것입니다). **주의: 이건 "%"라는 기호를
   금지하는 게 아닙니다** — 이 손님 본인의 실제 계산값을 비율ㆍ퍼센트로 표현하는 것(예:
   "오행 중 흙 기운이 54%로 우세합니다")은 얼마든지 써도 됩니다, 오히려 권장됩니다
   (2026-08-24 사용자 확인). 금지 대상은 어디까지나 "다른 손님/집단과 비교한, 근거
   없는 수치"입니다. "기회"와 "리스크"는 계산값이 가리키는 경향성을 설명하는 것이지,
   확정된 사건을 예언하는 게 아닙니다.
10. **고객이 questions 필드에 남긴 질문마다 question_answers 배열에 항목 하나씩 반드시
   작성하세요.** questions는 티어에 따라 0개일 수도, 최대 12개일 수도 있습니다. 질문
   개수만큼 정확히 그 개수만큼 항목을 만드세요 — 하나도 빠뜨리거나 합치지 마세요.
   각 항목은 반드시 먼저 answerability를 스스로 판정한 뒤, 그 판정에 맞는 방식으로만
   답하세요:
   - **"direct"** — computed.json에 있는 이 손님의 실제 데이터(사주ㆍ점성술ㆍ타로)로
     직접 답할 수 있는 질문. 이직운ㆍ연애운ㆍ이 시기 조심할 점처럼 대부분의 질문이 여기
     해당합니다. unanswerable_reason은 null. body에 그 데이터에 근거해 정면으로,
     확신 있게 답하세요 — 애매하게 양쪽 다 맞는 말로 흐리지 마세요.
   - **"redirected"** — 질문을 문자 그대로 계산할 방법은 없지만(예: 상대방 생년월일이
     필요한 궁합 질문인데 상대방 정보가 없는 경우), 그 질문 뒤에 있는 진짜 관심사는 이
     손님의 실제 데이터로 부분적으로 답할 수 있는 경우. unanswerable_reason에 "왜 문자
     그대로는 답할 수 없는지"를 한 문장으로 명시하고, body 맨 앞에 그 이유를 손님에게
     먼저 밝힌 뒤(예: "궁합의 정확한 수치는 상대방 정보 없이는 계산할 수 없습니다."),
     이어서 이 손님 데이터만으로 답할 수 있는 부분을 다른 질문 답변만큼 깊이 있게
     쓰세요. **이 답을 마치 원래 질문에 직접 답한 것처럼 위장하지 마세요** — 손님이
     "내가 물어본 것과 다른 걸 받았다"는 걸 명확히 알 수 있어야 합니다.
   - **"unanswerable"** — 어떤 방법으로도(문자 그대로도, 관련 주제로 우회해도) 이 손님의
     실제 데이터로는 답할 근거가 전혀 없는 질문(복권 번호, 정확한 사망 시점, 타인의
     확정적 미래 사건 등). unanswerable_reason에 이유를 명시하고, body에는 왜 이게
     계산 범위를 벗어나는지 정중하게 설명하세요 — 이때도 그럴듯한 숫자나 사실을
     지어내서 채우면 절대 안 됩니다(1번 규칙 위반).
   **어느 경우든 다른 질문의 답과 거의 같은 문장을 복사한 것처럼 쓰지 마세요** — 질문마다
   실제로 다른 데이터를 근거로 다르게 답해야 합니다. questions가 비어있으면
   question_answers는 null로 두세요.
10-A. **2026-08-23 추가 — saju.correspondence 필드(명리학 대응표 지식베이스)로 answerability가
   바뀌는 질문 유형.** 손님의 띠 특징, 우세/부족 오행에 어울리는 색ㆍ방향ㆍ숫자ㆍ음식ㆍ신체ㆍ
   직업, 사주에 등장한 십신ㆍ12운성의 "의미"를 묻는 질문(예: "제 띠 특징이 뭔가요", "저한테
   부족한 오행 채우는 음식이 뭔가요", "제 사주에 있는 정관이 무슨 뜻이에요")은 이제
   computed.json의 saju.correspondence 필드에 이미 계산되어 있으므로 **"direct"로
   답하세요** — 예전처럼 일반 명리학 지식으로 답하면 안 되고, 반드시 이 필드의 값만
   근거로 삼으세요(1번 규칙과 동일 원칙). correspondence 필드에 없는 항목(예: 이 손님의
   네 기둥에 등장하지 않은 십신)을 묻는 질문이면 "이 손님 사주에는 등장하지 않는
   요소"라고 답하고 지어내지 마세요.
10-B. **2026-08-23 추가 — computed.json에 gunghap 필드가 있으면 궁합 질문도 "direct"로
   승격됩니다.** (SINGLE 이상 티어는 8번 규칙 마지막 항목에 따라 이 내용이 system_sections
   궁합 섹션에 이미 들어가 있을 수 있습니다 — question_answers에서 또 답할 때는 그 섹션과
   완전히 같은 문장을 복사하지 말고, 질문의 구체적 표현에 맞춰 조금 다른 각도로 다시
   풀어 쓰세요.) gunghap 필드는 상대방 생년월일 정보가 intake에 있을 때만 run.js가
   계산해 넣어줍니다(gunghap.js). 이 필드가 있으면 궁합 질문(예: "저희 궁합이 어떤가요")을
   "direct"로 판정하고, gunghap.score/score_label/ilgan_relation/ilji_relation/
   yeonji_zodiac_relation/oheng_complement_points/highlights를 근거로 정면으로
   답하세요 — gunghap.methodology_note에 있듯 이건 이 서비스가 채택한 궁합 채점 기준이라는 걸
   리포트 톤에도 가볍게 반영하되(예: "여러 궁합 판단 기준 중 하나로 볼 때"), 절대 "v1",
   "베타", "프로젝트" 같은 내부 개발 용어를 손님에게 노출하지 마세요 — 확신 있게
   구체적으로 쓰세요. **gunghap.relationship_type이 "business"ㆍ"family"면 highlights
   문구가 이미 그 관계에 맞게 조정되어 있으니(예: business는 "배우자 자리" 대신 "생활
   리듬" 표현), 그 관계 유형에 맞는 톤을 그대로 이어가고 romantic 전제(결혼ㆍ연애)로
   되돌리지 마세요.** gunghap.disclaimer가 null이 아니면(family일 때만 채워짐) 답변
   어딘가에 그 취지를 자연스럽게 녹여 쓰세요(그대로 복사하지 말고 문맥에 맞게). **gunghap
   필드가 없는데 궁합 질문이 들어오면 여전히 "redirected"로 판정하세요** — 상대방 정보
   없이는 계산할 수 없다는 걸 먼저 밝히고(unanswerable_reason에 "상대방 생년월일 정보가
   없어 정확한 궁합 계산이 불가능함"처럼 명시), 그 다음 이 손님 본인의 사주 특성(일지
   특징 등)만으로 답할 수 있는 부분을 이어서 쓰세요 — 원래 질문과 다른 걸 받았다는 걸
   숨기지 마세요(10번 규칙 원칙 동일 적용).
10-C. **2026-08-23 추가 — saju.shensha 필드로 신살(도화ㆍ역마ㆍ화개ㆍ홍염) 질문도
   "direct"로 승격됩니다.** "저 도화살 있나요", "역마살이 있어서 이사를 자주 다니나요"
   같은 질문은 이제 saju.shensha.taohua/yeokma/hwagae/hongyeom의 present(있음/없음)ㆍ
   meaning(의미)ㆍfound_in(어느 기둥에 있는지)만 근거로 답하세요 — present가 false면
   "이 손님 사주에는 해당 신살이 없다"고 명확히 답하고, 있지도 않은데 있는 것처럼
   얼버무리지 마세요. shensha.basis_note에 있듯 일지 기준이 기본이고 by_year_branch는
   참고용 고전식 기준이니, 둘이 다르게 나오면 "일지 기준으로는 ~하지만, 년지 기준(고전식)
   으로는 ~하다"처럼 둘 다 밝혀도 됩니다(지어내는 게 아니라 이미 계산된 두 값을 그대로
   전달하는 것이므로 1번 규칙 위반이 아님). meaning 문구는 "전통적으로 여겨진다" 톤을
   유지하고, 확정적 사건 예언으로 바꿔 쓰지 마세요(4번 규칙과 동일).
10-D. **2026-08-23 추가 — astrology.correspondence 필드로 점성술 "의미" 질문도 "direct"로
   승격됩니다.** "제 태양이 처녀자리인데 무슨 뜻이에요", "이 하우스가 무슨 의미인가요",
   "이 어스펙트는 어떤 관계예요" 같은 질문은 astrology.correspondence.planet_meanings/
   ascendant_meaning/house_meanings/aspect_meanings만 근거로 답하세요 — 10-A번과 동일한
   원칙(이 손님 차트에 실제로 등장한 것만 담겨 있음, 검증 안 된 일반 점성술 지식 사용 금지).
10-E. **2026-08-23 추가 — computed.json에 astrology_synastry 필드가 있으면 "두 사람의
   별자리ㆍ궁합" 질문도 "direct"로 승격됩니다.** 이 필드는 astrology가 포함된 티어에서
   intake.customer.partner에 상대방 생년월일**과 출생 위경도**까지 있을 때만 run.js가
   계산해 넣어줍니다(synastry.js) — gunghap(사주 궁합)보다 요구 조건이 하나 더 있다는 뜻이라,
   gunghap 필드는 있는데 astrology_synastry 필드가 없는 경우도 정상입니다(그때는 점성술
   쪽 궁합 질문만 10-B번 gunghap 답변으로 충분히 못 채운 부분이 남을 수 있으니, "사주 쪽
   궁합은 계산했지만 점성술 쪽 궁합은 상대방 출생지 정보가 없어 계산하지 못했다"고 솔직히
   밝히세요). astrology_synastry.skipped_reason이 null이 아니면(둘 중 한쪽이라도 생시
   미상) 그 이유를 그대로 안내하고 aspects는 비어있다고 보세요. skipped_reason이 null이면
   astrology_synastry.aspects 배열(각 항목의 person_a_body/person_b_body/type/orb/
   person_a_body_meaning/person_b_body_meaning/aspect_meaning)만 근거로 삼아, "손님의
   X행성과 상대방의 Y행성이 Z 관계"라는 실제 계산값을 자연스러운 문장으로 엮어 답하세요 —
   500가지에 가까운 조합이 나올 수 있으므로 is_priority가 true인 항목(태양ㆍ달ㆍ금성ㆍ
   화성ㆍ토성 사이의 조합, 관계 궁합에서 특히 비중이 크다고 통용되는 천체들) 위주로
   추려서 언급하고, aspects가 비어있으면(어스펙트가 실제로 하나도 안 걸린 경우) "뚜렷하게
   걸리는 시너스트리 어스펙트는 없다"고 그대로 답하세요(있는 것처럼 지어내지 말 것 — 1번
   규칙과 동일). astrology_synastry.note에 있듯 이것도 서양 점성술의 표준 상징 체계를
   참고한 것이지 확정적 예언이 아니라는 톤을 유지하세요.
10-F. **2026-08-23 추가 — saju.yearly_fortune 필드로 "올해 띠 운세" 질문도 "direct"로
   승격됩니다.** "저 올해 운세 어때요", "쥐띠는 올해 어떤 해예요" 같은 질문은 이제
   saju.yearly_fortune.zhi_relation/gan_relation/highlights만 근거로 답하세요 — 이 필드는
   손님의 띠(년지)ㆍ년간과 올해 세운의 간지 사이의 합충형파해ㆍ상생상극 관계만 계산한
   것으로, 인터넷에 흔한 "매년 새로 지어내는 신년운세 서사"가 아닙니다. **절대로 이
   필드에 없는 내용(예: "이달의 재물운", "몇 월에 좋은 일이 생긴다")을 일반 지식으로
   지어내 덧붙이지 마세요** — highlights에 없는 관계는 언급하지 않는 게 맞습니다(1번
   규칙과 동일 원칙). saju.yearly_fortune이 null이면(성별 미입력으로 세운 자체가 없거나
   se_un 범위에 올해가 없는 경우) "성별 정보가 없어 올해 세운을 계산할 수 없다"고 명확히
   답하고 지어내지 마세요. methodology_note에 있듯 이것도 이 서비스가 채택한 해석 기준
   중 하나라는 톤을 자연스럽게 반영하되, "v1"ㆍ"베타"ㆍ"프로젝트" 같은 내부 개발 용어는
   절대 손님에게 노출하지 마세요.
11. **toc_preview(목차 미리보기)를 scope "full"/"premium"이면 채우세요**(mini/light는
   null) — 이번 리포트에 실제로 들어간 system_sections/opportunities/risks/
   cross_analysis/action_plan/long_term_strategy/question_answers의 heading(또는 그
   섹션을 대표하는 제목)을 등장 순서 그대로 문자열 배열로 나열하세요(새로 지어내지 말고,
   실제로 이 응답에 채운 것만 옮기세요).
"""

REPORT_SCHEMA = {
    "name": "submit_report",
    "description": "완성된 크로스노틱스 리포트를 구조화된 형식으로 제출한다.",
    "input_schema": {
        "type": "object",
        "properties": {
            "intro": {"type": "string", "description": "리포트 도입부"},
            "toc_preview": {
                "type": ["array", "null"],
                "description": "scope가 full/premium일 때만 채우는 목차 미리보기(이 응답에 실제로 채운 heading들을 순서대로).",
                "items": {"type": "string"},
            },
            "system_sections": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "system": {"type": "string", "enum": ["saju", "astrology", "tarot"]},
                        "heading": {"type": "string"},
                        "body": {"type": "string"},
                        "key_insight": {"type": "string", "description": "이 섹션의 핵심을 담은 한 문장(PDF 인용구용). scope가 mini면 생략 가능."},
                        "takeaways": {
                            "type": "array",
                            "description": "2~4개 핵심 정리 불릿. scope가 full/premium일 때만 채움.",
                            "items": {"type": "string"},
                        },
                    },
                    "required": ["system", "heading", "body"],
                },
            },
            "cross_analysis": {
                "type": ["object", "null"],
                "properties": {"heading": {"type": "string"}, "body": {"type": "string"}},
            },
            "opportunities": {
                "type": ["array", "null"],
                "description": "scope가 full/premium일 때만 채우는 기회 목록(3~5개). mini/light는 null.",
                "items": {
                    "type": "object",
                    "properties": {"title": {"type": "string"}, "body": {"type": "string"}},
                    "required": ["title", "body"],
                },
            },
            "risks": {
                "type": ["array", "null"],
                "description": "scope가 full/premium일 때만 채우는 리스크ㆍ대비책 목록(3~4개). mini/light는 null.",
                "items": {
                    "type": "object",
                    "properties": {"title": {"type": "string"}, "body": {"type": "string"}},
                    "required": ["title", "body"],
                },
            },
            "action_plan": {
                "type": ["object", "null"],
                "description": "scope가 full('single' 제외)/premium일 때만 채우는 실전 액션 목록. 그 외엔 null.",
                "properties": {
                    "heading": {"type": "string"},
                    "steps": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {"label": {"type": "string"}, "desc": {"type": "string"}},
                            "required": ["label", "desc"],
                        },
                    },
                    "scripts": {
                        "type": "array",
                        "description": "상황별 대화 스크립트(master/premium). 2~4개.",
                        "items": {
                            "type": "object",
                            "properties": {"situation": {"type": "string"}, "line": {"type": "string"}},
                            "required": ["situation", "line"],
                        },
                    },
                    "reflection_questions": {
                        "type": "array",
                        "description": "자문 질문(master/premium). 2~3개.",
                        "items": {
                            "type": "object",
                            "properties": {"question": {"type": "string"}, "note": {"type": "string"}},
                            "required": ["question", "note"],
                        },
                    },
                },
            },
            "question_answers": {
                "type": ["array", "null"],
                "description": "고객이 questions에 남긴 질문마다 하나씩. 질문이 없으면 null. 2026-08-23 재설계 — 답변 전 반드시 answerability를 direct/redirected/unanswerable 중 하나로 스스로 판정(10번 규칙 참고), 원래 질문과 다른 걸 답하면서 숨기는 것 금지.",
                "items": {
                    "type": "object",
                    "properties": {
                        "question": {"type": "string", "description": "고객이 실제로 남긴 질문 원문 그대로"},
                        "answerability": {"type": "string", "enum": ["direct", "redirected", "unanswerable"]},
                        "unanswerable_reason": {
                            "type": ["string", "null"],
                            "description": "answerability가 redirected/unanswerable일 때만 채움 — 왜 문자 그대로는 답할 수 없는지 한 문장.",
                        },
                        "body": {"type": "string"},
                    },
                    "required": ["question", "answerability", "body"],
                },
            },
            "long_term_strategy": {
                "type": ["object", "null"],
                "description": "scope가 'premium'일 때만 채우는 10년/평생/인생 2막 전략 섹션. 그 외엔 null.",
                "properties": {
                    "decade_roadmap": {"type": "object", "properties": {"heading": {"type": "string"}, "body": {"type": "string"}}},
                    "lifetime_design": {"type": "object", "properties": {"heading": {"type": "string"}, "body": {"type": "string"}}},
                    "second_act": {"type": "object", "properties": {"heading": {"type": "string"}, "body": {"type": "string"}}},
                    "behavior_dna": {"type": ["object", "null"], "properties": {"heading": {"type": "string"}, "body": {"type": "string"}}},
                },
            },
            "closing": {"type": "string"},
        },
        "required": ["intro", "system_sections", "question_answers", "long_term_strategy", "closing"],
    },
}


def call_llm(computed):
    client = anthropic.Anthropic()  # ANTHROPIC_API_KEY 환경변수 자동 사용
    user_message = (
        "아래는 한 고객의 크로스노틱스 계산 결과(computed.json)입니다. 이 데이터만 근거로 "
        "리포트를 작성해 submit_report 도구로 제출하세요.\n\n"
        f"```json\n{json.dumps(computed, ensure_ascii=False, indent=2)}\n```"
    )
    # 2026-08-21: 8번ㆍ9번 규칙(모든 데이터 빠짐없이 다루기 + 질문답변 섹션) 추가 후
    # 4096->8192->16000까지 올렸는데도 마스터 티어(3체계+질문 3개)에서 16000마저 실제로
    # 잘리는 걸 확인함(질문 최대 10개까지 갈 수 있으니 이보다 더 필요할 수 있음) — 32000으로
    # 재상향. call_llm()의 stop_reason 검사가 있어 그래도 잘리면 조용히 넘어가지 않고 죽는다.
    #
    # 2026-08-22: premium(20만원, 목표 약 30페이지)ㆍmaster(목표 약 20페이지) 신설로 요구
    # 분량이 크게 늘어서(사주 4섹션+점성술 4섹션+타로 3섹션+cross_analysis+action_plan+
    # long_term_strategy 3부까지) 32000으로는 부족할 가능성이 높아 64000으로 재상향. 실제
    # API로 검증 전이라 그래도 잘리면 아래 stop_reason 검사가 죽여서 알려준다 — 잘리면
    # 여기를 더 올릴 것.
    #
    # max_tokens가 크면(오래 걸릴 수 있으면) Anthropic SDK가 non-streaming 호출을 거부하고
    # 스트리밍을 요구함(실제로 32000에서 ValueError로 확인) — messages.stream()으로 전환.
    max_tokens = 64000
    with client.messages.stream(
        model=MODEL,
        max_tokens=max_tokens,
        system=SYSTEM_PROMPT,
        tools=[REPORT_SCHEMA],
        tool_choice={"type": "tool", "name": "submit_report"},
        messages=[{"role": "user", "content": user_message}],
    ) as stream:
        response = stream.get_final_message()
    # 그래도 잘릴 가능성에 대비해 명시적으로 검사 — 잘린 걸 모르고 그대로 발송하는 사고를 막는다.
    if response.stop_reason == "max_tokens":
        raise RuntimeError(
            f"LLM 응답이 max_tokens({max_tokens})에서 잘림 — 리포트가 불완전할 수 있음. "
            f"이대로 저장/발송하면 안 됨. max_tokens를 더 늘리거나 프롬프트를 손볼 것."
        )
    for block in response.content:
        if block.type == "tool_use" and block.name == "submit_report":
            report = block.input
            missing = [f for f in REPORT_SCHEMA["input_schema"]["required"] if f not in report]
            if missing:
                raise RuntimeError(f"LLM 응답에 필수 필드 누락: {missing} — 이대로 저장/발송하면 안 됨")
            return report, response.usage
    raise RuntimeError("LLM이 submit_report 도구를 호출하지 않음 — 응답 확인 필요")


def collect_known_terms(computed):
    """computed.json 안에 실제로 존재하는 용어(간지ㆍ별자리ㆍ카드명 등)를 전부 모은다."""
    terms = set()

    def walk(obj):
        if isinstance(obj, dict):
            for v in obj.values():
                walk(v)
        elif isinstance(obj, list):
            for v in obj:
                walk(v)
        elif isinstance(obj, str) and 1 < len(obj) <= 20:
            terms.add(obj)

    walk(computed)
    return terms


def collect_valid_years(computed):
    """se_un/dae_yun/생년 등 computed.json에 실제로 등장하는 '정당한' 연도만 모은다.
    이 목록 밖의 연도가 리포트에 나오면 se_un 없이 AI가 일반 지식으로 채운 것일 가능성이
    높다(실사용 테스트에서 실제로 발견된 문제 — build_report.py 8번 규칙 참고)."""
    years = set()
    saju = computed.get("saju") or {}
    if saju.get("birth_solar"):
        years.add(int(saju["birth_solar"][:4]))
    for entry in saju.get("se_un") or []:
        years.add(entry["year"])
    for entry in saju.get("dae_yun") or []:
        years.add(entry["start_year"])
        years.add(entry["end_year"])
    return years


_PDF_FONT_CMAP = None


def _pdf_font_cmap():
    """PDF에 실제로 쓰이는 Pretendard-Regular.ttf의 글리프 테이블(cmap)을 읽어, 이 폰트가
    그릴 수 있는 유니코드 코드포인트 집합을 반환한다(최초 호출 때만 파일을 읽고 캐시함).
    Pretendard 6종 굵기는 전부 같은 글자 집합을 공유하므로 Regular 하나만 확인하면 된다."""
    global _PDF_FONT_CMAP
    if _PDF_FONT_CMAP is None:
        font_path = HERE / "fonts" / "Pretendard-Regular.ttf"
        _PDF_FONT_CMAP = set(TTFont(str(font_path)).getBestCmap().keys())
    return _PDF_FONT_CMAP


def _is_glyph_supported(ch):
    # 공백ㆍ줄바꿈 등 제어문자는 애초에 그려지는 글자가 아니므로 항상 통과.
    if ch.isspace() or ord(ch) < 0x20:
        return True
    return ord(ch) in _pdf_font_cmap()


_PAREN_LEADING_SEP_RE = re.compile(r"\(\s*[,ㆍ·]+\s*")
_PAREN_TRAILING_SEP_RE = re.compile(r"[\s,ㆍ·]+\)")
_PAREN_EMPTY_RE = re.compile(r"\(\s*[,ㆍ·]*\s*\)")


def _strip_unsupported_glyphs(text):
    """2026-08-24 추가 — 사용자 지시: "경고만 하지 말고, 폰트가 완벽하게 그릴 수 있는
    글자만 쓰도록 만들어라. 한자는 빼버려라." check_hallucination()의 경고는 사람이 보고
    다시 생성 버튼을 눌러야만 고쳐지는데, 그러면 같은 문제가 계속 재발할 여지가 남는다.
    대신 여기서 폰트가 못 그리는 글자를 실제로 제거해서, 그 문제 자체가 최종 산출물에
    나갈 수 없게 만든다. 한자만 쏙 빠지면 "화개살(壬辰)" → "화개살()"처럼 빈 괄호나
    "임진(壬辰, 물의 기운)" → "임진(, 물의 기운)"처럼 군더더기 구두점이 남을 수 있어
    그것도 같이 정리한다."""
    if not text:
        return text
    cleaned = "".join(ch for ch in text if _is_glyph_supported(ch))
    cleaned = _PAREN_LEADING_SEP_RE.sub("(", cleaned)
    cleaned = _PAREN_TRAILING_SEP_RE.sub(")", cleaned)
    cleaned = _PAREN_EMPTY_RE.sub("", cleaned)
    cleaned = re.sub(r" {2,}", " ", cleaned)
    return cleaned


def sanitize_report(obj):
    """report(dict) 전체를 재귀적으로 훑어 모든 문자열 값에서 PDF 폰트가 못 그리는 글자를
    제거한다. intro/body/heading처럼 필드를 하나하나 골라 처리하면 스키마에 필드가 추가될
    때마다 또 빠뜨릴 위험이 있으므로(실제로 이번에 그렇게 놓쳤었음), 구조를 가리지 않고
    모든 문자열을 훑는 일반적인 방식을 쓴다."""
    if isinstance(obj, str):
        return _strip_unsupported_glyphs(obj)
    if isinstance(obj, list):
        return [sanitize_report(v) for v in obj]
    if isinstance(obj, dict):
        return {k: sanitize_report(v) for k, v in obj.items()}
    return obj


def check_hallucination(report, known_terms, valid_years):
    """리포트 본문에서 핵심 용어를 뽑아 known_terms/valid_years와 대조 — 발송을 막지는
    않고 경고만 남긴다.

    2026-08-24 추가 — 실제로 LLM이 action_plan을 dict가 아니라 문자열로 반환한 사례가
    있었음(원인 불명 — 스키마로 강제하는데도 발생. max_tokens 근처까지 간 대형 응답에서
    발생한 것으로 추정되나 확실친 않음). 그때 이 함수가 .get()을 그대로 호출하다
    AttributeError로 죽으면서, **이미 돈을 내고 받은 LLM 응답을 저장도 못 하고 통째로
    날렸다** — 검증 코드의 버그로 API 비용을 날리는 건 절대 안 되므로, 아래 모든 블록을
    isinstance로 방어해서 "이 필드가 예상과 다른 모양이어도 이 함수는 절대 죽지 않는다"를
    보장한다(무엇이 이상한지는 여전히 신호로 남기되, 죽지는 않게)."""
    def _d(v):
        return v if isinstance(v, dict) else {}

    def _l(v):
        return v if isinstance(v, list) else []

    all_text = str(report.get("intro") or "") + str(report.get("closing") or "")
    for sec in _l(report.get("system_sections")):
        sec = _d(sec)
        all_text += str(sec.get("body") or "") + str(sec.get("key_insight") or "") + " ".join(_l(sec.get("takeaways")))
    all_text += str(_d(report.get("cross_analysis")).get("body") or "")
    for item in _l(report.get("opportunities")) + _l(report.get("risks")):
        item = _d(item)
        all_text += str(item.get("title") or "") + str(item.get("body") or "")
    action_plan = _d(report.get("action_plan"))
    for step in _l(action_plan.get("steps")):
        step = _d(step)
        all_text += str(step.get("label") or "") + str(step.get("desc") or "")
    for script in _l(action_plan.get("scripts")):
        script = _d(script)
        all_text += str(script.get("situation") or "") + str(script.get("line") or "")
    for q in _l(action_plan.get("reflection_questions")):
        q = _d(q)
        all_text += str(q.get("question") or "") + str(q.get("note") or "")
    for qa in _l(report.get("question_answers")):
        all_text += str(_d(qa).get("body") or "")
    for part in _d(report.get("long_term_strategy")).values():
        if isinstance(part, dict):
            all_text += str(part.get("body") or "")

    # 2026-08-24 — 이전엔 본문에 "%"가 있으면 무조건 경고했으나, 사용자 확인: "퍼센트가
    # 들어가는건 아무 문제가 없어. 오히려 좋은거야." 손님 본인의 실제 계산값을 %로 표현하는
    # 건 정상이고 권장되므로, 그 신호로는 더 이상 쓰지 않는다(진짜 위험한 건 %라는 기호가
    # 아니라 "다른 손님들과 비교한 근거 없는 통계"인데, 그건 %없이도 쓸 수 있고 %가 있다고
    # 반드시 그런 것도 아니라서 기계적으로 감지하기 어렵다 — 9-C번 프롬프트 규칙으로만 막음).

    # 2026-08-24 추가 — 7번 규칙("한자 절대 쓰지 말 것")이 실제로 여러 번 어겨진 걸 눈으로
    # 확인함(壬辰ㆍ華蓋殺 등, PDF에서 폰트가 없는 글자칸(tofu box)으로 깨짐). 처음엔 "한자
    # 범위(U+4E00–U+9FFF)만 스캔"으로 좁게 고쳤는데, 사용자가 "문제를 발견했으면 같은
    # 실수가 다시는 반복되지 않도록 원인 자체를 제거하라"고 지적함 — 한자는 이 폰트가 못
    # 그리는 여러 문자 종류 중 하나일 뿐이고, 다음엔 다른 미지원 기호(예: 이모지, 다른
    # 언어 문자)가 나올 수도 있다. 그래서 "한자인지"를 묻는 대신 "이 폰트가 실제로 그릴 수
    # 있는 글자인지"를 Pretendard TTF의 cmap(글리프 테이블)에서 직접 조회하는 방식으로
    # 바꿨다 — 원인(폰트가 못 그리는 모든 글자)을 통째로 막는 구조라, 한자든 다른 무엇이든
    # 이 폰트가 지원 안 하는 문자는 종류를 가리지 않고 전부 걸린다.
    unsupported = sorted({ch for ch in all_text if not _is_glyph_supported(ch)})
    if unsupported:
        # 2026-08-24 문구 수정 — 아래 sanitize_report()가 이 글자들을 저장 전에 실제로
        # 전부 제거하므로, 최종 PDF에는 절대 나타나지 않는다(방금 이 파일로 직접 검증함:
        # report.json·PDF 텍스트 추출 둘 다 클린). 그런데도 예전 문구("발송 전 반드시
        # 확인할 것")가 마치 최종 산출물이 아직 깨져 있는 것처럼 읽혀서, 이미 자동으로
        # 고쳐진 걸 보고도 "또 안 고쳤나" 오해를 부를 수 있었음 — 그래서 "이미 자동
        # 제거됨"이라고 명확히 밝히는 쪽으로 문구만 바꿈(로직은 그대로).
        print(f"ℹ 참고: LLM이 PDF 폰트가 못 그리는 문자를 시도함: {''.join(unsupported)} — 이미 자동으로 제거되어 최종 PDF에는 나타나지 않습니다. (7번 규칙을 얼마나 자주 어기는지 추적하는 용도, 조치 불필요)")
    else:
        print("✓ 본문의 모든 문자가 PDF 폰트에서 정상 렌더링됨")

    # 간지(2글자 한글, 예: "경오"), 별자리("~자리"로 끝남), 원소(단일 한글자+조사) 패턴만
    # 가볍게 검사 — 완벽한 NLP가 아니라 "발송 전 훑어볼 신호"로만 쓴다(설계 문서 참고).
    sign_candidates = re.findall(r"[가-힣]+자리", all_text)
    unknown = [s for s in set(sign_candidates) if s not in known_terms]
    if unknown:
        print(f"⚠ 경고: 리포트에 computed.json에 없는 별자리 표현이 있을 수 있음: {unknown}")
    else:
        print("✓ 별자리 용어 대조 통과(단순 패턴 검사, 완벽하지 않음 — 최종 발송 전 사람이 한 번 읽을 것)")

    # 연도 대조 — se_un 없이 특정 연도를 언급했던 실제 사례를 계기로 추가함.
    year_candidates = {int(y) for y in re.findall(r"(?:19|20)\d{2}(?=년)", all_text)}
    unknown_years = year_candidates - valid_years
    if unknown_years:
        print(f"⚠ 경고: computed.json의 se_un/dae_yun/생년에 없는 연도 언급 발견: {sorted(unknown_years)} — AI가 일반 지식으로 채웠을 가능성, 발송 전 확인할 것")
    else:
        print("✓ 연도 언급 전부 se_un/dae_yun/생년 범위 안에 있음")


QUESTION_LOG_PATH = HERE / "logs" / "question_answerability_log.jsonl"


def log_question_answerability(report, computed, log_path=QUESTION_LOG_PATH):
    """2026-08-23 추가 — "계산 불가능한 질문이 실제로 얼마나 되냐"를 추측(예: "극소수")이
    아니라 실측하기 위한 로그. 리포트를 만들 때마다 question_answers의 판정
    (direct/redirected/unanswerable)을 그대로 append한다 — 절대 덮어쓰지 않음, 계속
    쌓기만 함. 이 로그가 쌓이면 print_log_summary()로 실제 비율을 확인할 수 있다."""
    qas = report.get("question_answers") or []
    if not qas:
        return
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        for qa in qas:
            record = {
                "logged_at": datetime.now(timezone.utc).isoformat(),
                "tier": computed.get("tier"),
                "scope": computed.get("scope"),
                "question": qa.get("question"),
                "answerability": qa.get("answerability"),
                "unanswerable_reason": qa.get("unanswerable_reason"),
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    counts = Counter(qa.get("answerability") for qa in qas)
    print(f"질문 판정 로그 기록 완료: {dict(counts)} (누적 로그 위치: {log_path})")


def print_log_summary(log_path=QUESTION_LOG_PATH):
    """지금까지 쌓인 로그로 실제 비율을 계산해서 보여준다 — "극소수"였는지 아닌지 추측이
    아니라 숫자로 확인. 사용법: python build_report.py --log-summary"""
    if not log_path.exists():
        print(f"로그 파일이 아직 없습니다({log_path}) — 리포트를 몇 건 생성한 뒤 다시 확인하세요.")
        return
    records = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not records:
        print("로그는 있지만 기록이 비어있습니다.")
        return
    total = len(records)
    counts = Counter(r["answerability"] for r in records)
    print(f"누적 질문 {total}건 (리포트 여러 건 합산):")
    for kind in ("direct", "redirected", "unanswerable"):
        n = counts.get(kind, 0)
        print(f"  {kind}: {n}건 ({n / total * 100:.1f}%)")
    unanswerable = [r for r in records if r["answerability"] == "unanswerable"]
    if unanswerable:
        print("\nunanswerable로 판정된 질문 예시(패턴 파악용, 최대 10개):")
        for r in unanswerable[:10]:
            print(f"  - {r['question']!r} ({r.get('unanswerable_reason')})")


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "--log-summary":
        print_log_summary()
        return

    if len(sys.argv) < 2:
        print("사용법: python build_report.py <computed.json> [출력 PDF 경로]")
        print("        python build_report.py --log-summary   (누적된 질문 판정 통계 확인)")
        sys.exit(1)

    computed_path = Path(sys.argv[1])
    computed = json.loads(computed_path.read_text(encoding="utf-8"))

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY 환경변수가 없음 — Anthropic Console에서 API 키 발급 필요")
        print("(계획서 8번 '사용자가 직접 해야 하는 일' 참고, 에이전트가 대신 만들 수 없음)")
        sys.exit(1)

    print(f"LLM 호출 중... (모델: {MODEL})")
    report, usage = call_llm(computed)
    print(f"완료. 토큰 사용량: 입력 {usage.input_tokens} / 출력 {usage.output_tokens}")

    out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else computed_path.with_suffix(".report.json")
    # 2026-08-24 추가 — 실제로 이 아래(check_hallucination)에서 예상 못 한 응답 모양 때문에
    # 죽으면서, 이미 돈을 내고 받은 LLM 응답이 저장도 안 된 채 통째로 날아간 사고가 있었음.
    # 그래서 LLM 호출이 끝나는 즉시(뒤에 나올 검증ㆍ정제 단계가 뭘 하든 상관없이) 원본을
    # 먼저 디스크에 저장해둔다 — 이후 단계가 죽어도 최소한 이 raw 파일로 복구할 수 있다.
    raw_backup_path = out_path.with_suffix(".raw.json")
    raw_backup_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    known_terms = collect_known_terms(computed)
    valid_years = collect_valid_years(computed)
    check_hallucination(report, known_terms, valid_years)  # 원본 그대로 측정 — 얼마나 자주 규칙을 어기는지 계속 눈으로 볼 것

    # 2026-08-24 추가 — 위 경고는 "얼마나 자주 어겼는지" 계속 지켜보기 위한 것일 뿐,
    # 실제로 저장ㆍ발송되는 리포트에는 폰트가 못 그리는 글자가 아예 없어야 한다(사용자
    # 지시: "완벽하게 생성할 수 있는 폰트만 사용하도록, 한자는 빼버려"). 경고 후 사람이
    # 다시 눌러야만 고쳐지는 구조를 없애고, 여기서 실제로 제거해 최종 산출물은 항상
    # 안전하게 만든다.
    report = sanitize_report(report)

    log_question_answerability(report, computed)

    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"리포트 JSON 저장: {out_path}")
    # 최종 저장이 여기까지 문제없이 왔다는 건 raw 백업이 더 이상 필요 없다는 뜻 — 폴더에
    # 쌍둥이 파일이 계속 쌓이지 않도록 정리한다.
    raw_backup_path.unlink(missing_ok=True)
    print("(PDF 생성은 report_kit.py 완성 후 build_pdf_from_report()로 이어서 처리)")


if __name__ == "__main__":
    main()
