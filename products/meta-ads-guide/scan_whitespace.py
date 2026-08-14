# -*- coding: utf-8 -*-
"""전자책 PDF의 페이지별 빈 여백을 검사하는 스크립트."""
import fitz
from PIL import Image
import io

PDF = r"C:\Users\nalla\Desktop\서비스허브\products\meta-ads-guide\메타_광고_최적화_가이드.pdf"
doc = fitz.open(PDF)
print("total pages:", doc.page_count)

flagged = []
for i in range(doc.page_count):
    page = doc[i]
    pix = page.get_pixmap(matrix=fitz.Matrix(1.0, 1.0))
    img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("L")
    w, h = img.size
    px = img.load()
    bottom_exclude = int(h * 0.06)
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

print("flagged pages (bottom whitespace ratio > 0.25):")
for pg, ratio in flagged:
    print(f"  page {pg}: {ratio}")
if not flagged:
    print("  none - all pages normal")
