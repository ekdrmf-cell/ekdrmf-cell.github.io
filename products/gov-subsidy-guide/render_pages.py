# -*- coding: utf-8 -*-
import fitz
from pathlib import Path

PDF = r"C:\Users\nalla\Desktop\서비스허브\products\gov-subsidy-guide\정부지원금_찾기_가이드.pdf"
OUT = Path(r"C:\Users\nalla\Desktop\서비스허브\products\gov-subsidy-guide\preview")
OUT.mkdir(exist_ok=True)

# 표지, 목차, 1부 시작, 스크린샷 포함 페이지, 용어사전, 사업계획서 가이드, 부록, 마지막 페이지
PAGES = [1, 3, 5, 6, 8, 9, 21, 25, 40, 48, 50]

doc = fitz.open(PDF)
print("total pages:", doc.page_count)
for p in PAGES:
    if p > doc.page_count:
        continue
    page = doc[p - 1]
    pix = page.get_pixmap(matrix=fitz.Matrix(1.8, 1.8))
    pix.save(str(OUT / f"page_{p:02d}.png"))
    print("saved page", p)
