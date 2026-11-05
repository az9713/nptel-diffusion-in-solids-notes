"""Export public source and artifact discovery metadata."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    manifest = json.loads((ROOT / "source-manifest.json").read_text(encoding="utf-8"))
    manifest["sources"] = [dict(id=f'L{r["number"]:02d}', input=r["url"],
                                status="caption acquired and read",
                                coverage="Complete available English caption text; selected visuals separately recorded")
                           for r in manifest["recordings"]]
    visual_path = ROOT / "validation/source-visual-checks.json"
    if visual_path.exists():
        visuals = json.loads(visual_path.read_text(encoding="utf-8"))
        for record in manifest["recordings"]:
            matching = [v for v in visuals["inspections"] if v["lecture"] == record["number"]]
            record["visual_review"] = "selected frames inspected" if matching else "not visually reviewed"
            record["selected_visual_checks"] = matching
    write(ROOT / "source-manifest.json", manifest)
    plan = json.loads((ROOT / "plan/chapters.json").read_text(encoding="utf-8"))
    artifacts = []
    dependencies = [f'L{n:02d}' for n in range(1, 61)]
    for path in sorted(ROOT.glob("*.html")):
        chapter = next((c for c in plan["chapters"] if path.name == f'chapter-{c["number"]:02d}.html'), None)
        artifacts.append(dict(path=path.name, purpose="Study chapter" if chapter else "Reader companion/navigation page",
                              source_dependencies=[f'L{n:02d}' for n in chapter["lectures"]] if chapter else dependencies))
    for path in sorted((ROOT / "code").glob("ch[0-9][0-9].py")):
        chapter = plan["chapters"][int(path.stem[2:]) - 1]
        artifacts.append(dict(path=path.relative_to(ROOT).as_posix(), purpose="Original executable teaching laboratory",
                              source_dependencies=[f'L{n:02d}' for n in chapter["lectures"]]))
    write(ROOT / "artifact-manifest.json", dict(artifacts=artifacts,
          boundary="Original public reader and laboratories; raw recordings/captions and private research/review files excluded"))
    print(json.dumps(dict(sources=len(manifest["sources"]), artifacts=len(artifacts))))


if __name__ == "__main__":
    main()
