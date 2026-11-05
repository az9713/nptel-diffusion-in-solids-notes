"""Check public reader integrity; --release additionally enforces completion."""
import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit
from bs4 import BeautifulSoup
from build_book import input_signature

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--release", action="store_true")
    args = parser.parse_args()
    errors, warnings = [], []
    completion = json.loads((ROOT / "completion.json").read_text(encoding="utf-8"))
    pages = sorted(ROOT.glob("*.html"))
    sources = json.loads((ROOT / "source-manifest.json").read_text(encoding="utf-8"))
    durations = {r["video_id"]: r["duration_seconds"] for r in sources["recordings"]}
    for path in pages:
        raw = path.read_text(encoding="utf-8")
        # The inherited skill scripts scan dollar math; this reader uses \( and \[.
        segments = re.findall(r"\\\((.*?)\\\)|\\\[(.*?)\\\]", raw, re.S)
        if raw.count(r"\(") != raw.count(r"\)") or raw.count(r"\[") != raw.count(r"\]"):
            errors.append(f"{path.name}: unmatched mathematics delimiters")
        for pair in segments:
            segment = pair[0] or pair[1]
            if "<" in segment or ">" in segment:
                errors.append(f"{path.name}: literal angle bracket inside mathematics")
            depth = 0
            for match in re.finditer(r"(?<!\\)[{}]", segment):
                depth += 1 if match[0] == "{" else -1
                if depth < 0:
                    break
            if depth != 0:
                errors.append(f"{path.name}: unmatched mathematics braces")
            if any(char in segment for char in "\a\b\f\v"):
                errors.append(f"{path.name}: control character in mathematics")
        for tag in ("section", "details", "figure", "table"):
            if len(re.findall(rf"<{tag}(?:\s|>)", raw)) != len(re.findall(rf"</{tag}\s*>", raw)):
                errors.append(f"{path.name}: unbalanced {tag} elements")
        soup = BeautifulSoup(raw, "html.parser")
        for required in (soup.title, soup.find("meta", attrs={"name": "viewport"}), soup.find("main")):
            if required is None:
                errors.append(f"{path.name}: missing semantic/document element")
        ids = [tag["id"] for tag in soup.find_all(id=True)]
        if len(ids) != len(set(ids)):
            errors.append(f"{path.name}: duplicate ids")
        for node in soup.find_all(["a", "script", "link", "img"]):
            url = node.get("href", node.get("src", ""))
            parts = urlsplit(url)
            if parts.scheme in ("http", "https"):
                if node.name in ("script", "link"):
                    errors.append(f"{path.name}: remote dependency {url}")
                if "youtube.com/watch" in url and "&t=" in url:
                    match = re.search(r"[?&]v=([A-Za-z0-9_-]+).*?[&]t=(\d+)s", url)
                    if not match or match[1] not in durations or int(match[2]) > durations[match[1]]:
                        errors.append(f"{path.name}: invalid timestamp {url}")
                continue
            if parts.scheme or not url:
                continue
            target = (path.parent / unquote(parts.path)).resolve() if parts.path else path
            if not target.is_relative_to(ROOT):
                errors.append(f"{path.name}: escaping local target {url}")
            elif not target.exists():
                errors.append(f"{path.name}: missing target {url}")
            elif parts.fragment and target.suffix == ".html":
                destination = soup if target == path else BeautifulSoup(target.read_text(encoding="utf-8"), "html.parser")
                if not destination.find(id=unquote(parts.fragment)):
                    errors.append(f"{path.name}: missing anchor {url}")
        if re.search(r"C:[\\/]Users[\\/]|sk-proj-|ghp_[A-Za-z0-9]", raw):
            errors.append(f"{path.name}: private-path or secret pattern")
        for svg in soup.find_all("svg"):
            if len(svg.get("viewbox", "").split()) != 4:
                errors.append(f"{path.name}: malformed SVG viewBox")
        solutions = sum(s.get_text(" ", strip=True).lower() in ("solution", "worked solution") for s in soup.find_all("summary"))
        if path.name.startswith("chapter-") and solutions < 5:
            warnings.append(f"{path.name}: fewer than five worked exercises; justify scope")
    if args.release:
        if not completion.get("editorial_complete"):
            errors.append("Full course and two current-content reviews per chapter are not complete")
        if len(sources["recordings"]) != 60 or not all(r.get("transcript_read") for r in sources["recordings"]):
            errors.append("Complete source-reading records are missing")
        for chapter in completion.get("chapters", []):
            number = chapter["number"]
            body = ROOT / f"chapters/ch{number:02d}.html"
            if not body.exists() or hashlib.sha256(body.read_bytes()).hexdigest() != chapter.get("body_sha256"):
                errors.append(f"Stale chapter inventory: Ch{number}")
            for review in chapter.get("review", {}).get("rounds", []):
                for asset, digest in review.get("assets", {}).items():
                    if not (ROOT/asset).exists() or hashlib.sha256((ROOT/asset).read_bytes()).hexdigest() != digest:
                        errors.append(f"Stale scientific asset review: Ch{number} {asset}")
        labs_path = ROOT / "validation/laboratory-checks.json"
        labs = json.loads(labs_path.read_text()) if labs_path.exists() else {}
        if not labs.get("passed") or len(labs.get("chapters", [])) != 28:
            errors.append("Complete laboratory execution evidence is missing")
        for lab in labs.get("chapters", []):
            code = ROOT / f'code/ch{lab["chapter"]:02d}.py'
            if not code.exists() or hashlib.sha256(code.read_bytes()).hexdigest() != lab.get("code_sha256"):
                errors.append(f'Stale lab evidence: Ch{lab["chapter"]}')
        reader_records = []
        for report in (ROOT / "validation").glob("reader-checks*.json"):
            record = json.loads(report.read_text())
            fresh = all((ROOT / "assets" / name).exists() and hashlib.sha256((ROOT / "assets" / name).read_bytes()).hexdigest() == value
                        for name, value in record.get("shared_assets", {}).items())
            if not record.get("errors") and record.get("shared_assets") and fresh:
                reader_records.extend(record.get("pages", []))
        for reader_page in pages:
            filename = reader_page.name
            current = hashlib.sha256((ROOT/filename).read_bytes()).hexdigest() if (ROOT/filename).exists() else None
            for width in (1280, 650, 390):
                if not any(r.get("page") == filename and r.get("width") == width and r.get("html_sha256") == current for r in reader_records):
                    errors.append(f"Missing current browser check: {filename} at {width}px")
        for name in ("figure-checks.json", "export-checks.json", "controls-checks.json"):
            path = ROOT / "validation" / name
            record = json.loads(path.read_text()) if path.exists() else {}
            if not record.get("passed"):
                errors.append(f"Required check not passed: {name}")
            if name in ("figure-checks.json", "export-checks.json") and record.get("input_signature") != input_signature():
                errors.append(f"Stale input signature: {name}")
            if name == "controls-checks.json" and any(hashlib.sha256((ROOT/"assets"/asset).read_bytes()).hexdigest() != digest
                    for asset, digest in record.get("shared_assets", {}).items()):
                errors.append("Stale control asset checks")
    report = dict(mode="release" if args.release else "development", pages=len(pages), errors=errors, warnings=warnings)
    if args.release:
        report["input_signature"] = input_signature()
    (ROOT / "validation").mkdir(exist_ok=True)
    (ROOT / "validation" / ("release-checks.json" if args.release else "development-checks.json")).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    raise SystemExit(bool(errors))


if __name__ == "__main__":
    main()
