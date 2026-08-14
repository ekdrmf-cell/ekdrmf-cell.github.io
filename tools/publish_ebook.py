# -*- coding: utf-8 -*-
"""전자책 완성 후 반복되는 뒷정리 작업을 한 번에 처리하는 스크립트.

기존에 사람이 순서대로 손으로 하던 것:
  1) products/<slug>/scan_whitespace.py 실행해서 빈여백 있는지 확인
  2) 완성 PDF를 데스크톱 "전자책 자동화/NN_제목/" 폴더에 번호 매겨서 복사
  3) git add로 저장소 쪽 변경사항 스테이징

이 스크립트가 위 세 가지를 한 번에 처리한다. ebooks.html/index.html 카드 문구와
git commit은 책마다 내용이 달라서(설명·태그·가격) 사람이 쓰고 확정한 뒤에
별도로 진행한다 — 이 스크립트가 대신 지어내지 않는다.

사용법:
    python tools/publish_ebook.py <slug> "<한글 제목>"

예:
    python tools/publish_ebook.py coupang-seller-guide "쿠팡 셀러 창업 가이드"
"""
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PRODUCTS_DIR = REPO_ROOT / "products"
EBOOK_HOME = Path.home() / "Desktop" / "전자책 자동화"


def find_pdf(product_dir: Path) -> Path:
    pdfs = list(product_dir.glob("*.pdf"))
    if not pdfs:
        raise FileNotFoundError(f"{product_dir} 안에 PDF가 없습니다 — 먼저 build_pdf.py로 완성본을 만들 것.")
    if len(pdfs) > 1:
        raise RuntimeError(f"{product_dir} 안에 PDF가 여러 개({[p.name for p in pdfs]})라 어느 걸 배포할지 모르겠습니다 — 하나만 남기고 정리할 것.")
    return pdfs[0]


def run_whitespace_scan(product_dir: Path) -> str:
    scanner = product_dir / "scan_whitespace.py"
    if not scanner.exists():
        return "(scan_whitespace.py 없음 — 빈여백 검증 건너뜀)"
    result = subprocess.run(
        [sys.executable, str(scanner)],
        cwd=str(product_dir),
        capture_output=True,
        text=True,
    )
    output = (result.stdout or "") + (result.stderr or "")
    return output.strip()


def next_sequence_number() -> int:
    EBOOK_HOME.mkdir(parents=True, exist_ok=True)
    numbers = []
    for entry in EBOOK_HOME.iterdir():
        m = re.match(r"^(\d+)_", entry.name)
        if m:
            numbers.append(int(m.group(1)))
    return (max(numbers) + 1) if numbers else 1


def safe_folder_name(seq: int, title: str) -> str:
    cleaned = re.sub(r"[\\/:*?\"<>|]", "", title).strip()
    cleaned = re.sub(r"\s+", "_", cleaned)
    return f"{seq:02d}_{cleaned}"


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)

    slug, title = sys.argv[1], sys.argv[2]
    product_dir = PRODUCTS_DIR / slug
    if not product_dir.is_dir():
        print(f"products/{slug} 폴더가 없습니다.")
        sys.exit(1)

    pdf_path = find_pdf(product_dir)
    print(f"[1/3] PDF 확인: {pdf_path.relative_to(REPO_ROOT)}")

    print("[2/3] 빈여백 검사 실행 중...")
    scan_result = run_whitespace_scan(product_dir)
    print(scan_result)
    if "flagged pages" in scan_result and "none" not in scan_result.split("flagged pages")[-1][:20]:
        print("  ⚠ 위 flagged 페이지는 사람이 직접 열어서 실제로 비어있는지 확인할 것 (오탐 가능).")

    seq = next_sequence_number()
    folder_name = safe_folder_name(seq, title)
    dest_dir = EBOOK_HOME / folder_name
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_pdf = dest_dir / pdf_path.name
    shutil.copy2(pdf_path, dest_pdf)
    print(f"[3/3] 복사 완료 -> {dest_pdf}")

    subprocess.run(["git", "-C", str(REPO_ROOT), "add", str(product_dir.relative_to(REPO_ROOT))])
    print(f"\ngit add 완료: products/{slug}/ (아직 커밋은 안 함)")
    print("\n남은 수동 작업 (내용이 책마다 달라서 자동화 안 함):")
    print("  - ebooks.html / index.html에 카드 추가")
    print("  - git commit (+ push)")


if __name__ == "__main__":
    main()
