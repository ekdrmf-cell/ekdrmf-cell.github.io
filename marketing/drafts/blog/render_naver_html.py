"""네이버용 .md 초안을 실제 링크(<a href>)가 적용된 HTML로 변환.

티스토리와 달리 네이버는 소제목에 별도 스타일(제목2)을 적용하는 절차 자체가
없어서(■ 기호만으로 충분), 이 스크립트가 필요한 이유는 딱 하나 — "글 제목"과
"URL"이 서로 다른 텍스트/링크 쌍으로 들어가는 부분(예: 이전 글 소개)을 에디터의
링크 버튼을 누르지 않고도 붙여넣기만으로 실제 하이퍼링크가 걸리게 하기 위함이다.

사용법: python render_naver_html.py 초안파일.md
출력: 같은 이름의 .html — 브라우저로 열어 Ctrl+A, Ctrl+C 한 뒤
blog.naver.com 에디터 본문에 Ctrl+V 하면 링크가 실제 하이퍼링크로 붙는다.
"""
import re
import sys
from pathlib import Path

IMAGE_RE = re.compile(r'^\(※ 여기에 사진 삽입: 이미지 폴더의 "(.+?)"\)$')
KICKER_RE = re.compile(r"^■\s*(.+)$")
NUMBERED_RE = re.compile(r"^(\d+)\.\s+(.+)$")
LINK_LINE_RE = re.compile(r"^https?://\S+$")


def parse_body(lines: list) -> list:
    html_parts = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue

        m = KICKER_RE.match(line)
        if m:
            html_parts.append(f"<p class='kicker'><b>■ {m.group(1)}</b></p>")
            i += 1
            continue

        m = IMAGE_RE.match(line)
        if m:
            html_parts.append(
                f'<div class="img-slot">📷 사진 자리 — 이미지 폴더의 "{m.group(1)}" '
                f"끌어다 놓기(이 상자는 복사되지 않게, 붙여넣은 뒤 직접 사진으로 바꿔주세요)</div>"
            )
            i += 1
            continue

        def is_special(idx):
            s = lines[idx].strip()
            if not s:
                return True
            if KICKER_RE.match(s) or IMAGE_RE.match(s) or NUMBERED_RE.match(s):
                return True
            if s.startswith("- ") and idx + 1 < len(lines) and LINK_LINE_RE.match(lines[idx + 1].strip()):
                return True
            if s.startswith("[") and s.endswith("]"):
                return True
            return False

        m = NUMBERED_RE.match(line)
        if m:
            items = []
            while i < len(lines) and NUMBERED_RE.match(lines[i].strip()):
                item_text = NUMBERED_RE.match(lines[i].strip()).group(2)
                i += 1
                # 번호 목록 항목이 줄바꿈으로 이어지는 경우(다음 줄이 번호로
                # 시작하지 않고 특수 줄도 아니면) 같은 항목에 계속 이어붙인다.
                while i < len(lines) and lines[i].strip() and not is_special(i):
                    item_text += " " + lines[i].strip()
                    i += 1
                items.append(item_text)
            li = "".join(f"<li>{item}</li>" for item in items)
            html_parts.append(f"<ol>{li}</ol>")
            continue

        if line.startswith("- ") and i + 1 < len(lines) and LINK_LINE_RE.match(lines[i + 1].strip()):
            label = line[2:].strip()
            url = lines[i + 1].strip()
            html_parts.append(f'<p><a href="{url}">{label}</a></p>')
            i += 2
            continue

        if line.startswith("[") and line.endswith("]"):
            html_parts.append(f"<p class='todo'>⚠ {line} (이 안내문은 붙여넣기 전에 지우거나, 위 '- 제목/URL' 형식으로 바꿔서 실제 링크로 만들어주세요)</p>")
            i += 1
            continue

        para_lines = []
        while i < len(lines) and lines[i].strip() and not is_special(i):
            para_lines.append(lines[i].strip())
            i += 1
        html_parts.append(f"<p>{' '.join(para_lines)}</p>")

    return html_parts


def render(md_path: Path) -> Path:
    text = md_path.read_text(encoding="utf-8")
    sections = {}
    for key in ["제목", "본문", "링크", "태그", "쓰는 법"]:
        m = re.search(rf"\[{key}[^\]]*\]\n(.*?)(?=\n\[|\Z)", text, re.S)
        if m:
            sections[key] = m.group(1).strip()

    title = sections.get("제목", "").split("\n")[0]
    body_lines = sections.get("본문", "").split("\n")
    body_html = "\n".join(parse_body(body_lines))

    cta_html = ""
    link = sections.get("링크", "").strip()
    if link:
        cta_html = f'<p><a href="{link}">{title} — 전체 가이드 보러가기</a></p>'

    tags = sections.get("태그", "").strip()
    tags_html = ""
    if tags:
        tags_html = f"""<div class="tag-box">
<p class="tag-label">🏷 태그 (본문에 붙여넣지 말고, 발행 화면의 "태그 편집"란에 따로 입력하세요)</p>
<p class="tag-text">{tags}</p>
</div>"""

    html = f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><title>{title}</title>
<style>
body {{ font-family: -apple-system, "Malgun Gothic", sans-serif; max-width: 720px;
  margin: 40px auto; line-height: 1.8; color: #222; padding: 0 16px; }}
h2.post-title {{ font-size: 26px; }}
p {{ font-size: 16px; }}
p.kicker {{ font-size: 17px; margin-top: 30px; }}
p.todo {{ color: #c0392b; background: #fdecea; padding: 10px; border-radius: 6px; }}
ol {{ font-size: 16px; }}
.img-slot {{ background: #f0f0f0; border: 2px dashed #999; padding: 24px;
  text-align: center; color: #777; margin: 16px 0; font-size: 14px; }}
.tag-box {{ margin-top: 40px; padding: 14px 16px; background: #f4f7ff;
  border: 1px solid #cdd8f5; border-radius: 8px; }}
.tag-label {{ font-size: 13px; color: #555; margin: 0 0 6px; }}
.tag-text {{ font-size: 15px; color: #1a3a8f; margin: 0; font-weight: 600; }}
a {{ color: #1a5fd0; }}
</style></head>
<body>
<h2 class="post-title">{title}</h2>
{body_html}
{cta_html}
{tags_html}
</body></html>"""

    out_path = md_path.with_suffix(".html")
    out_path.write_text(html, encoding="utf-8")
    return out_path


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        p = render(Path(arg))
        print(p)
