"""Acquire selected source frames privately, without publishing source media."""
import argparse
import json
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "sources/private"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lectures", nargs="+", type=int, required=True)
    parser.add_argument("--high-quality", action="store_true")
    args = parser.parse_args()
    manifest = json.loads((ROOT / "source-manifest.json").read_text(encoding="utf-8"))
    records = {r["number"]: r for r in manifest["recordings"]}
    targets = {}
    for path in (ROOT / "work/source-maps").glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        for frame in data.get("frames_needed", []) + data.get("required_visual_checks", []):
            lecture = frame.get("lecture")
            second = frame.get("time_seconds", frame.get("timestamp_seconds"))
            if lecture in args.lectures and second is not None:
                targets.setdefault(lecture, set()).add(float(second))
            if lecture in args.lectures:
                targets.setdefault(lecture, set()).update(float(t) for t in frame.get("seconds", []))
    extra_path = RAW / "visual-targets.json"
    if extra_path.exists():
        for lecture, times in json.loads(extra_path.read_text(encoding="utf-8")).items():
            if int(lecture) in args.lectures:
                targets.setdefault(int(lecture), set()).update(float(t) for t in times)
    videos, frames = RAW / "videos", RAW / "frames"
    videos.mkdir(exist_ok=True)
    frames.mkdir(exist_ok=True)
    report = []
    for lecture in args.lectures:
        record = records[lecture]
        times = sorted(targets.get(lecture, {record["duration_seconds"] / 2}))
        video = videos / f'{record["video_id"]}.mp4'
        if args.high_quality:
            result = subprocess.run(["yt-dlp", "--no-playlist", "--no-warnings", "--socket-timeout", "20", "--retries", "1", "-g",
                                     "-f", "bestvideo[height<=720][ext=mp4]/best[height<=720]", record["url"]], capture_output=True, text=True, timeout=90)
            if result.returncode:
                report.append(dict(lecture=lecture, status="stream_resolution_failed"))
                continue
            media_input = result.stdout.strip().splitlines()[0]
        elif not video.exists():
            command = ["yt-dlp", "--no-playlist", "--no-warnings", "--socket-timeout", "20", "--retries", "1",
                       "-f", "worst[ext=mp4]/worstvideo[ext=mp4]", "-o", str(video), record["url"]]
            result = subprocess.run(command, capture_output=True, timeout=300)
            (videos / f'{lecture:02d}-download.log').write_bytes(result.stdout + result.stderr)
            if result.returncode:
                report.append(dict(lecture=lecture, status="download_failed"))
                continue
        if not args.high_quality:
            media_input = str(video)
        images = []
        for second in times:
            suffix = "-hi" if args.high_quality else ""
            target = frames / f"L{lecture:02d}-{second:.3f}{suffix}.jpg"
            if not target.exists():
                try:
                    command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", str(second)]
                    if args.high_quality:
                        command.extend(["-rw_timeout", "15000000"])
                    command.extend(["-i", media_input, "-frames:v", "1", "-q:v", "2", str(target)])
                    result = subprocess.run(command, capture_output=True, timeout=45)
                except subprocess.TimeoutExpired:
                    report.append(dict(lecture=lecture, time=second, status="frame_timeout"))
                    continue
                if result.returncode:
                    report.append(dict(lecture=lecture, time=second, status="frame_failed"))
                    continue
            image = Image.open(target).convert("RGB")
            image.thumbnail((640, 360))
            canvas = Image.new("RGB", (640, 390), "#15191e")
            canvas.paste(image, (0, 25))
            ImageDraw.Draw(canvas).text((8, 5), f"L{lecture} at {second:.3f}s", fill="white")
            images.append(canvas)
        sheet = Image.new("RGB", (1280, 390 * ((len(images) + 1) // 2)), "#15191e")
        for i, image in enumerate(images):
            sheet.paste(image, ((i % 2) * 640, (i // 2) * 390))
        if images:
            sheet.save(frames / f"L{lecture:02d}-contact{suffix}.jpg")
        report.append(dict(lecture=lecture, status="acquired_not_reviewed", times=times))
        print(json.dumps(report[-1]), flush=True)
    (RAW / ("frame-acquisition-hi.json" if args.high_quality else "frame-acquisition.json")).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
