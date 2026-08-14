# -*- coding: utf-8 -*-
"""전자책 PDF의 페이지별 빈 여백을 검사하는 스크립트.

주의: 페이지 하단에는 항상 페이지 번호가 찍히므로, 그냥 "마지막 잉크가 있는 행"만
찾으면 항상 페이지 번호 위치(하단 근처)가 잡혀서 실제로는 본문 중간에 큰 공백이
있어도 못 잡아낸다(이 프로젝트에서 실제로 겪은 실수). 그래서 하단 페이지 번호
영역은 제외하고, 그 위쪽 "본문 영역"에서 콘텐츠가 어디까지 차 있는지를 본다.
"""
import fitz
from PIL import Image
import io

PDF = r"C:\Users\nalla\Desktop\서비스허브\products\gov-subsidy-guide\정부지원금_찾기_가이드.pdf"
doc = fitz.open(PDF)
print("total pages:", doc.page_count)

flagged = []
for i in range(doc.page_count):
    page = doc[i]
    pix = page.get_pixmap(matrix=fitz.Matrix(1.0, 1.0))
    img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("L")
    w, h = img.size
    px = img.load()
    bottom_exclude = int(h * 0.06)  # 페이지 번호가 찍히는 하단 영역 제외
    last_content_y = 0
    for y in range(h - 1 - bottom_exclude, -1, -1):
        row_has_content = False
        for x in range(0, w, 4):
            if px[x, y] < 235:
                row_has_content = True
                break
        if row_has_content:
            last_content_y = y
            break
    usable_bottom = h - bottom_exclude
    blank_ratio = (usable_bottom - last_content_y) / usable_bottom
    if blank_ratio > 0.25:
        flagged.append((i + 1, round(blank_ratio, 2)))

print("flagged pages (본문 영역 기준 하단 공백 비율 > 0.25):")
for pg, ratio in flagged:
    print(f"  page {pg}: {ratio}")
if not flagged:
    print("  없음 — 전 페이지 정상")
