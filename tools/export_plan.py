"""Export source coverage and planning views without generating chapter prose."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    plan = load(ROOT / "plan/chapters.json")
    manifest = load(ROOT / "source-manifest.json")
    maps = sorted((ROOT / "work/source-maps").glob("ch*.json"))
    if maps:
        readings, sections, references = {}, [], []
        for path in maps:
            data = load(path)
            group = data["chapter"]
            for item in data.get("reading_records", []):
                number = item["lecture"]
                digest = item.get("sha256", item.get("transcript_sha256"))
                video = manifest["recordings"][number - 1]["video_id"]
                private = ROOT / f"sources/private/readable/{number:02d}-{video}.txt"
                if private.exists() and sha(private) != digest:
                    raise ValueError(f"Reading digest mismatch in L{number}")
                if not item.get("read_full"):
                    raise ValueError(f"L{number} has no complete reading record")
                readings[number] = dict(lecture=number, video_id=video,
                                        normalized_text_sha256=digest, read_full=True,
                                        reading_context=data["reviewer"],
                                        method="complete sequential reading of exact-overlap-normalized captions")
            for i, item in enumerate(data.get("sections", [])):
                # Only authored coverage summaries and exact locators, not raw captions.
                record = dict(item)
                record.update(source_group=group, node=f"G{group:02d}-S{i+1:02d}")
                record["planned_chapters"] = [c["number"] for c in plan["chapters"]
                    if group in c.get("source_map_groups", [c["source_map_group"]])]
                sections.append(record)
            references.extend(data.get("primary_references", []))
            references.extend(data.get("research_verified", []))
        if set(readings) != set(range(1, 61)):
            raise ValueError("The 60 official lectures do not all have reading records")
        ir = dict(coverage_note="Caption reading and source-topic maps; selected-frame and manuscript checks are separate.",
                  source_reading_records=list(readings.values()), sections=sections, references=references)
        write(ROOT / "analysis-ir.json", ir)
    else:
        ir = load(ROOT / "analysis-ir.json")
    # Private capture locations are useful only in the authoring workspace.
    for reference in ir.get("references", []):
        reference.pop("private_capture", None)
    write(ROOT / "analysis-ir.json", ir)
    readings = {r["lecture"]: r for r in ir["source_reading_records"]}
    for item in manifest["recordings"]:
        item["transcript_read"] = bool(readings.get(item["number"], {}).get("read_full"))
        item["reading_record"] = readings.get(item["number"])
    write(ROOT / "source-manifest.json", manifest)
    architecture = ["# Course architecture", "", "Twenty-eight chapters follow all 60 official lectures. Source-map groups retain their initial evidence identities; they are distinct from reader numbering.", ""]
    outline = ["# Detailed source-grounded outline", "", "Generated planning view. Source coverage statements and editorial dispositions are not manuscript prose or scientific acceptance.", ""]
    results = []
    for chapter in plan["chapters"]:
        n = chapter["number"]
        if any(dep >= n for dep in chapter["depends_on"]):
            raise ValueError(f"Forward or cyclic chapter dependency: Ch{n}")
        architecture.extend([f"## {n}. {chapter['title']}", chapter["question"],
                             "Lectures: " + ", ".join(map(str, chapter["lectures"])),
                             "Check: " + chapter["check"], ""])
        outline.extend([f"## {n}. {chapter['title']}", "", "Central result: " + chapter["result"],
                        "", "Check: " + chapter["check"], ""])
        for section in chapter["sections"]:
            outline.append("- " + section)
        outline.extend(["", "### Located source topics and required dispositions", ""])
        for source in ir["sections"]:
            if n not in source["planned_chapters"]:
                continue
            outline.append("- " + json.dumps(source, ensure_ascii=False))
        outline.append("")
        results.append(dict(id=f"R{n:02d}", statement=chapter["result"],
                            planned_chapter=n, depends_on=[f"R{x:02d}" for x in chapter["depends_on"]],
                            status="developed in the corresponding chapter; see current-content acceptance and numerical evidence in completion.json and validation/",
                            concrete_check=chapter["check"]))
    (ROOT / "plan/architecture.md").write_text("\n".join(architecture).rstrip() + "\n", encoding="utf-8")
    (ROOT / "plan/outline.md").write_text("\n".join(outline).rstrip() + "\n", encoding="utf-8")
    # JSON is valid YAML1.2 and avoids another runtime dependency.
    write(ROOT / "plan/results.yaml", dict(results=results))
    print(json.dumps(dict(lectures_read=len(readings), source_nodes=len(ir["sections"]), chapters=len(plan["chapters"]))))


if __name__ == "__main__":
    main()
