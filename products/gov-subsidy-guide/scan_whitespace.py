# -*- coding: utf-8 -*-
import fitz
from PIL import Image

PDF = r"C:\Users\nalla\Desktop\수익화허브\products\gov-subsidy-guide\정부지원금_찾기_가이드.pdf"
doc = fitz.open(PDF)
print("total pages:", doc.page_count)

flagged = []
for i in range(doc.page_count):
    page = doc[i]
    pix = page.get_pixmap(matrix=fitz.Matrix(1.0, 1.0))
    img = Image.open(fitz_io := __import__("io").BytesIO(pix.tobytes("png"))).convert("L")
    w, h = img.size
    px = img.load()
    # 아래에서부터 위로 올라가며, "거의 흰색이 아닌"(즉 텍스트/그래픽이 있는) 첫 행을 찾는다
    last_content_y = 0
    for y in range(h - 1, -1, -1):
        row_has_content = False
        for x in range(0, w, 4):
            if px[x, y] < 235:
                row_has_content = True
                break
        if row_has_content:
            last_content_y = y
            break
    bottom_blank_ratio = (h - last_content_y) / h
    if bottom_blank_ratio > 0.35:
        flagged.append((i + 1, round(bottom_blank_ratio, 2)))

print("flagged pages (bottom blank ratio > 0.35):")
for pg, ratio in flagged:
    print(f"  page {pg}: {ratio}")
