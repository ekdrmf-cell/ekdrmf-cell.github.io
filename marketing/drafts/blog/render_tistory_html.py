"""티스토리용 .md 초안을 실제 서식(H2/번호목록/링크)이 적용된 HTML로 변환.

메모장으로 보면 구조가 안 보인다는 문제(2026-08-11) 해결용 — 이 HTML을
브라우저로 열어서 통째로 복사(Ctrl+A, Ctrl+C)한 뒤 티스토리 에디터에
붙여넣으면(Ctrl+V), 리치 페이스트로 제목ㆍ목록ㆍ링크 서식이 그대로
들어간다(에디터에서 수동으로 스타일 버튼을 누를 필요가 없어짐).

사용법: python render_tistory_html.py 초안파일.md
"""
import re
import sys
from pathlib import Path

HEADING_RE = re.compile(r"^▶\s*(.+?)\s*\(제목2\)\s*$")
IMAGE_RE = re.compile(r'^\(※ 여기에 사진 삽입: 이미지 폴더의 "(.+?)"\)$')
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

        m = HEADING_RE.match(line)
        if m:
            html_parts.append(f"<h2>{m.group(1)}</h2>")
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

        m = NUMBERED_RE.match(line)
        if m:
            items = []
            while i < len(lines) and NUMBERED_RE.match(lines[i].strip()):
                items.append(NUMBERED_RE.match(lines[i].strip()).group(2))
                i += 1
            li = "".join(f"<li>{item}</li>" for item in items)
            html_parts.append(f"<ol>{li}</ol>")
            continue

        def is_special(idx):
            s = lines[idx].strip()
            if not s:
                return True
            if HEADING_RE.match(s) or IMAGE_RE.match(s) or NUMBERED_RE.match(s):
                return True
            if s.startswith("- ") and idx + 1 < len(lines) and LINK_LINE_RE.match(lines[idx + 1].strip()):
                return True
            return False

        if line.startswith("- ") and i + 1 < len(lines) and LINK_LINE_RE.match(lines[i + 1].strip()):
            label = line[2:].strip()
            url = lines[i + 1].strip()
            html_parts.append(f'<p><a href="{url}">{label}</a></p>')
            i += 2
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
    for key in ["제목", "메타 설명", "본문", "링크", "태그", "쓰는 법"]:
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
<p class="tag-label">🏷 태그 (본문에 붙여넣지 말고, 발행 설정의 "태그" 입력란에 따로 입력하세요)</p>
<p class="tag-text">{tags}</p>
</div>"""

    html = f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><title>{title}</title>
<style>
body {{ font-family: -apple-system, "Malgun Gothic", sans-serif; max-width: 720px;
  margin: 40px auto; line-height: 1.8; color: #222; padding: 0 16px; }}
h1 {{ font-size: 26px; }}
h2 {{ font-size: 20px; margin-top: 36px; border-left: 4px solid #444; padding-left: 10px; }}
p {{ font-size: 16px; }}
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
<h1>{title}</h1>
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
