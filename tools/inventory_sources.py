"""Reconcile official NPTEL order with playlist positions and private captions."""
import csv
import hashlib
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "sources/private"


def read_vtt(path):
    cues = []
    for block in re.split(r"\n\s*\n", path.read_text(encoding="utf-8-sig")):
        lines = block.splitlines()
        for i, line in enumerate(lines):
            match = re.search(r"(?:(\d+):)?(\d{2}):(\d{2}\.\d+)\s+-->", line)
            if match:
                hh, mm, ss = match.groups()
                content = html.unescape(re.sub(r"<[^>]+>", "", " ".join(lines[i + 1:])))
                if content.strip():
                    cues.append(dict(start=3600 * int(hh or 0) + 60 * int(mm) + float(ss), text=content.strip()))
                break
    return cues


def main():
    playlist = json.loads((RAW / "playlist.json").read_text(encoding="utf-8-sig"))
    positions = {e["id"]: (i + 1, e) for i, e in enumerate(playlist["entries"])}
    official = (RAW / "official-course.html").read_text(encoding="utf-8")
    pattern = r'\{id:(\d+),name:("(?:\\.|[^"\\])*"),youtube_id:"([^"]+)"'
    lessons = re.findall(pattern, official.split('name:"Live Session"')[0])
    lessons = [item for item in lessons if 1 <= int(item[0]) <= 60][:60]
    if len(lessons) != 60:
        raise ValueError("Official lesson structure changed; inspect the source")
    records = []
    textdir = RAW / "transcripts"
    textdir.mkdir(exist_ok=True)
    for number, title, video in lessons:
        path = RAW / "lectures" / f"{video}.info.json"
        meta = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        caption = RAW / "lectures" / f"{video}.en.vtt"
        cues = read_vtt(caption) if caption.exists() else []
        if cues:
            stem = textdir / f"{int(number):02d}-{video}"
            stem.with_suffix(".json").write_text(json.dumps(cues, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            stem.with_suffix(".txt").write_text("\n".join(f'[{c["start"]:.3f}s] {c["text"]}' for c in cues) + "\n", encoding="utf-8")
        pos, flat = positions.get(video, (None, {}))
        records.append(dict(number=int(number), title=json.loads(title), video_id=video,
                            url=f"https://www.youtube.com/watch?v={video}", playlist_position=pos,
                            duration_seconds=meta.get("duration", flat.get("duration")),
                            caption_status="acquired" if cues else "pending", caption_cues=len(cues),
                            caption_type="publisher-delivered; authorship not established" if meta.get("subtitles", {}).get("en") else "automatic-or-unavailable",
                            caption_sha256=hashlib.sha256(caption.read_bytes()).hexdigest() if cues else None,
                            last_cue_start_seconds=cues[-1]["start"] if cues else None,
                            transcript_read=False, visual_review="not reviewed"))
    records.sort(key=lambda r: r["number"])
    ids = {r["video_id"] for r in records}
    extras = [dict(video_id=v, playlist_position=p, title=e["title"], url=f"https://www.youtube.com/watch?v={v}")
              for v, (p, e) in positions.items() if v not in ids]
    result = dict(course=dict(title="Diffusion in Solids", instructor="Mayur Vaidya", institution="IIT Hyderabad",
                              course_id="113106635", official_url="https://nptel.ac.in/courses/113106635",
                              playlist=playlist["webpage_url"]), retrieved_at_utc=datetime.now(timezone.utc).isoformat(),
                  sequence_basis="official NPTEL lesson IDs", recordings=records, supplementary_entries=extras,
                  limitations="Caption acquisition is distinct from reading and visual verification; raw sources are private.")
    (ROOT / "source-manifest.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (ROOT / "lecture-inventory.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["number", "title", "video_id", "playlist_position", "duration_seconds", "caption_status", "url"], extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)
    print(json.dumps(dict(official=len(records), captions=sum(bool(r["caption_cues"]) for r in records), extras=extras)))


if __name__ == "__main__":
    main()
