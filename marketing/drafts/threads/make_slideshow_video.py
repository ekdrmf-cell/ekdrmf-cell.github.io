"""카드뉴스 이미지 폴더를 릴스용 세로 슬라이드쇼 mp4로 합치는 공용 함수.

ffmpeg concat demuxer를 그대로 사용 — 재인코딩 품질 손실 없이 이미지별 노출
시간만 다르게 줄 수 있어서 간단하고 안정적이다. 소리는 넣지 않는다(사용자가
인스타그램 앱에서 직접 트렌드 음원을 고르는 게 더 잘 맞고, 저작권 문제도 없음).
"""
import subprocess
from pathlib import Path


def build_slideshow(image_dir: Path, out_path: Path, durations: list, fps: int = 30) -> Path:
    image_dir = Path(image_dir)
    frames = sorted(image_dir.glob("card_*.png"), key=lambda p: int(p.stem.split("_")[1]))
    if len(frames) != len(durations):
        raise ValueError(f"이미지 수({len(frames)})와 durations 길이({len(durations)})가 다릅니다")

    list_path = image_dir / "_concat_list.txt"
    lines = []
    for frame, dur in zip(frames, durations):
        lines.append(f"file '{frame.name}'")
        lines.append(f"duration {dur}")
    lines.append(f"file '{frames[-1].name}'")  # concat demuxer 특성상 마지막 항목을 한 번 더 적어야 함
    list_path.write_text("\n".join(lines), encoding="utf-8")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(list_path),
        "-pix_fmt", "yuv420p", "-r", str(fps),
        str(out_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    list_path.unlink()
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg 실패:\n{result.stderr[-2000:]}")
    return out_path
