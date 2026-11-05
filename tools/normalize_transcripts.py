"""Remove only exact rolling-caption overlaps, retaining ordered new words."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "sources/private"


def main():
    target = RAW / "readable"
    target.mkdir(exist_ok=True)
    summary = []
    for path in sorted((RAW / "transcripts").glob("*.json")):
        cues = json.loads(path.read_text(encoding="utf-8"))
        history = []
        segments = []
        for cue in cues:
            words = cue["text"].split()
            overlap = 0
            for size in range(min(len(history), len(words)), 0, -1):
                if history[-size:] == words[:size]:
                    overlap = size
                    break
            new = words[overlap:]
            if new:
                segments.append(dict(start=cue["start"], text=" ".join(new)))
                history.extend(new)
        # Keep all new words; group at roughly minute intervals for readable navigation.
        paragraphs = []
        group = []
        group_start = 0
        for cue in segments:
            if group and cue["start"] - group_start >= 60:
                paragraphs.append(f"[{group_start:.3f}s] " + " ".join(group))
                group = []
            if not group:
                group_start = cue["start"]
            group.append(cue["text"])
        if group:
            paragraphs.append(f"[{group_start:.3f}s] " + " ".join(group))
        output = target / (path.stem + ".txt")
        output.write_text("\n\n".join(paragraphs) + "\n", encoding="utf-8")
        summary.append(dict(lecture=int(path.name[:2]), words=len(history), paragraphs=len(paragraphs)))
    (target / "normalization.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(dict(lectures=len(summary), words=sum(s["words"] for s in summary))))


if __name__ == "__main__":
    main()
