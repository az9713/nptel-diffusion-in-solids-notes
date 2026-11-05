"""Assemble the portable reader from directly authored chapter fragments."""
import hashlib
import html
import json
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]


def read(path, default=None):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def input_signature():
    """Bind release acceptance to public scientific and reader inputs."""
    paths = []
    for folder in ("chapters", "code", "assets", "figures", "frontmatter", "tools"):
        paths.extend(p for p in (ROOT/folder).rglob("*") if p.is_file()
                     and "__pycache__" not in p.parts and p.name != "reader-preview.png")
    paths.extend(ROOT/name for name in ("plan/chapters.json", "source-manifest.json", "analysis-ir.json", "requirements-lock.txt"))
    checksum = hashlib.sha256()
    for path in sorted(paths):
        checksum.update(path.relative_to(ROOT).as_posix().encode())
        checksum.update(sha(path).encode())
    return checksum.hexdigest()


def text(fragment):
    soup = BeautifulSoup(fragment, "html.parser")
    for node in soup(["script", "style", "pre"]):
        node.decompose()
    return soup.get_text(" ", strip=True)


def section_headings(soup):
    """Support either heading IDs or the enclosing authored section ID."""
    found, seen = [], set()
    for heading in soup.find_all(["h2", "h3"]):
        section = heading.find_parent("section", id=True)
        anchor = heading.get("id") or (section.get("id") if section else None)
        if anchor and anchor not in seen:
            found.append((heading, anchor))
            seen.add(anchor)
    return found


def reviews(number, digest):
    evidence = read(ROOT / f"validation/chapters/ch{number:02d}.json", {})
    verdicts = evidence.get("reviews", [])
    code = ROOT / f"code/ch{number:02d}.py"
    accepted = (len(verdicts) == 2
                and len({r.get("reviewer") for r in verdicts}) == 2
                and all(r.get("independent_context") for r in verdicts)
                and all(r.get("full_review") and not r.get("open_blockers", 0) for r in verdicts)
                and all(r.get("verdict") in ("accept", "accepted")
                        and r.get("body_sha256") == digest
                        and (not code.exists() or r.get("code_sha256") == sha(code))
                        and all((ROOT / asset).exists() and sha(ROOT / asset) == value
                                for asset, value in r.get("assets", {}).items())
                        for r in verdicts))
    return {"accepted": accepted, "rounds": verdicts}


def shell(title, body, chapters, current=None):
    links = "".join(f'<li><a {"aria-current=page " if c["number"] == current else ""}href="chapter-{c["number"]:02d}.html">{c["number"]}. {html.escape(c["title"])}</a></li>' for c in chapters)
    return f'''<!DOCTYPE html>
<html lang="en" data-theme="dark"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Independent study notes for Diffusion in Solids, NPTEL IIT Hyderabad: derivations, worked solutions, and Python laboratories.">
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self' data:; object-src 'none'; base-uri 'none'">
<title>{html.escape(title)} — Diffusion in Solids</title>
<link rel="stylesheet" href="assets/book.css">
<script defer src="assets/math-config.js"></script><script defer src="assets/mathjax-tex-svg.js"></script>
<script defer src="assets/search-index.js"></script><script defer src="assets/book.js"></script>
<script defer src="assets/diffusion.js"></script></head><body>
<a class="skip" href="#main">Skip to content</a>
<header class="toolbar"><a class="brand" href="index.html">DIFFUSION IN SOLIDS</a>
<div class="controls"><button type="button" data-action="theme">Theme</button>
<button type="button" data-action="smaller" aria-label="Smaller text">A−</button>
<button type="button" data-action="larger" aria-label="Larger text">A+</button>
<button type="button" data-action="print">Print / PDF</button></div></header>
<div class="layout"><aside class="sidebar"><details open><summary>Course contents</summary><ol>{links}</ol>
<nav class="utility" aria-label="Companion pages"><a href="index.html">Home and search</a>
<a href="study-guide.html">Study guide</a><a href="source-map.html">Recordings and timestamps</a>
<a href="laboratory.html">Python laboratory</a><a href="references.html">References and attribution</a>
<a href="about.html">Sources and verification</a></nav></details></aside>
<main id="main"><p class="eyebrow">IIT Hyderabad · NPTEL · Independent study edition</p>
<h1>{html.escape(title)}</h1>{body}
<footer>Independent educational notes following Prof. Mayur Vaidya’s course.
No institutional endorsement. Source recordings remain with their creators.</footer></main></div></body></html>'''


def main():
    plan = read(ROOT / "plan/chapters.json")
    sources = read(ROOT / "source-manifest.json")
    chapters = [c for c in plan["chapters"] if (ROOT / f'chapters/ch{c["number"]:02d}.html').exists()]
    records, search = [], []
    for c in chapters:
        n = c["number"]
        path = ROOT / f"chapters/ch{n:02d}.html"
        fragment = path.read_text(encoding="utf-8")
        soup = BeautifulSoup(fragment, "html.parser")
        headings = section_headings(soup)
        toc = '<nav class="toc" aria-label="Chapter sections"><ul>' + "".join(f'<li><a href="#{anchor}">{html.escape(h.get_text(" ", strip=True))}</a></li>' for h, anchor in headings) + ('<li><a href="#companion-python">Python laboratory and recorded output</a></li>' if (ROOT / f'code/ch{n:02d}.py').exists() else '') + '</ul></nav>'
        body = toc + fragment
        code = ROOT / f"code/ch{n:02d}.py"
        output = ROOT / f"code/ch{n:02d}-output.json"
        if code.exists():
            body += f'<section id="companion-python"><h2>Python laboratory</h2><p>Run <a href="code/{code.name}"><code>code/{code.name}</code></a>. Inputs and scientific limits are specified in the chapter and program.</p><details><summary>Complete runnable source</summary><pre><code class="language-python">{html.escape(code.read_text(encoding="utf-8"))}</code></pre></details>'
            if output.exists():
                body += f'<details><summary>Recorded execution output</summary><pre><code>{html.escape(output.read_text(encoding="utf-8"))}</code></pre></details>'
            body += '</section>'
        before = f'<a href="chapter-{n-1:02d}.html">← Previous</a>' if n > 1 and any(x["number"] == n - 1 for x in chapters) else '<a href="index.html">← Home</a>'
        after = f'<a href="chapter-{n+1:02d}.html">Next →</a>' if any(x["number"] == n + 1 for x in chapters) else '<a href="index.html">Home →</a>'
        body += f'<nav class="chapter-nav" aria-label="Chapter navigation">{before}{after}</nav>'
        (ROOT / f"chapter-{n:02d}.html").write_text(shell(c["title"], body, chapters, n), encoding="utf-8")
        digest = sha(path)
        records.append(dict(number=n, title=c["title"], body_sha256=digest, words_approx=len(text(fragment).split()),
                            solved_exercises=sum(s.get_text(" ", strip=True).lower() in ("solution", "worked solution") for s in soup.find_all("summary")), review=reviews(n, digest),
                            code_sha256=sha(code) if code.exists() else None, output_sha256=sha(output) if output.exists() else None))
        search.append(dict(number=n, title=c["title"], url=f"chapter-{n:02d}.html", text=text(fragment)))
    (ROOT / "assets/search-index.js").write_text("window.COURSE_SEARCH=" + json.dumps(search, ensure_ascii=False) + ";\n", encoding="utf-8")
    accepted = sum(r["review"]["accepted"] for r in records)
    editorial_complete = len(records) == len(plan["chapters"]) and accepted == len(records)
    release = read(ROOT / "validation/release-checks.json", {})
    complete = editorial_complete and release.get("errors") == [] and release.get("input_signature") == input_signature()
    status = "Complete independently reviewed study edition" if complete else f"In development: {len(records)} of {len(plan['chapters'])} chapters drafted; {accepted} accepted after two current-content reviews"
    home = f'<p class="lede">From conserved matter to atomic jumps, thermodynamic driving forces, and defensible measurements.</p><p class="status">{status}.</p><p>Based on <a href="https://nptel.ac.in/courses/113106635">Mayur Vaidya’s NPTEL course at IIT Hyderabad</a>. All 60 official lectures are inventoried; playlist upload order is preserved separately.</p><label for="course-search">Search the study edition</label><input type="search" id="course-search" placeholder="Try Kirkendall, vacancy, or boundary"><div class="search-results" id="search-results" aria-live="polite"></div><ol class="chapters">'
    home += "".join(f'<li><a class="chapter-title" href="chapter-{c["number"]:02d}.html">{c["number"]}. {html.escape(c["title"])}</a><p>{html.escape(c["question"])}</p></li>' for c in chapters) + '</ol>'
    (ROOT / "index.html").write_text(shell("Diffusion in Solids", home, chapters), encoding="utf-8")
    sourcebody = '<p>Official teaching order, not playlist upload order. Captions, reading, selected-frame checks, and science reviews are distinct evidence. Raw captions and media are excluded.</p><table><thead><tr><th>Lecture</th><th>Source</th><th>Upload position</th><th>Caption status</th></tr></thead><tbody>'
    sourcebody += "".join(f'<tr><td>{r["number"]}</td><td><a href="{r["url"]}">{html.escape(r["title"])}</a></td><td>{r["playlist_position"]}</td><td>{r["caption_status"]}</td></tr>' for r in sources["recordings"]) + '</tbody></table>'
    sourcebody += '<h2 id="introduction">Supplementary introduction</h2><ul>'
    for entry in sources.get("supplementary_entries", []):
        sourcebody += f'<li><a href="{html.escape(entry["url"], quote=True)}">{html.escape(entry["title"])}</a>: {html.escape(entry.get("role", "supplementary source"))}.</li>'
    sourcebody += '</ul>'
    sourcebody += '<h2 id="chapter-navigation">Chapter and timestamp navigation</h2>'
    for chapter in chapters:
        n = chapter["number"]
        authored = BeautifulSoup((ROOT/f"chapters/ch{n:02d}.html").read_text(encoding="utf-8"), "html.parser")
        sourcebody += f'<h3><a href="chapter-{n:02d}.html">{n}. {html.escape(chapter["title"])}</a></h3><ul>'
        for heading, anchor in section_headings(authored):
            recordings = [a for a in heading.find_all("a", href=True) if "youtube.com/watch" in a["href"]]
            if recordings:
                sourcebody += f'<li><a href="chapter-{n:02d}.html#{html.escape(anchor, quote=True)}">{html.escape(heading.get_text(" ", strip=True))}</a> · '
                sourcebody += " · ".join(f'<a href="{html.escape(a["href"], quote=True)}">{html.escape(a.get_text(" ", strip=True))}</a>' for a in recordings) + '</li>'
        sourcebody += '</ul>'
    (ROOT / "source-map.html").write_text(shell("Recordings and source map", sourcebody, chapters), encoding="utf-8")
    study = '<p>Use each chapter’s derivations and worked exercises before running its code. Record the conserved quantity, frame, initial state, boundary data, and observation model before selecting a diffusion coefficient.</p><ol>' + "".join(f'<li><strong>{html.escape(c["title"])}</strong><p>{html.escape(c["result"])}</p><p>Check: {html.escape(c["check"])}.</p></li>' for c in plan["chapters"]) + '</ol>'
    (ROOT / "study-guide.html").write_text(shell("Study guide and learning outcomes", study, chapters), encoding="utf-8")
    labbody = '<p>Install the <a href="requirements-lock.txt">checked Python dependencies</a> with <code>python -m pip install -r requirements-lock.txt</code>. Run <code>python code_lab.py</code> to list the laboratories, or <code>python code_lab.py 1</code> to execute Chapter1. The <a href="code_lab.py">launcher</a> accepts chapter numbers1–28. Run these commands from the extracted repository folder.</p><p>Teaching models with stated synthetic inputs and selected attributed source data. They test specified equations and numerical methods; they do not certify material parameters or reproduce proprietary databases.</p><ul>' + "".join(f'<li><a href="chapter-{r["number"]:02d}.html#companion-python">Chapter {r["number"]}: {html.escape(r["title"])}</a> · <a href="code/ch{r["number"]:02d}.py">Python source</a></li>' for r in records if r["code_sha256"]) + '</ul>'
    (ROOT / "laboratory.html").write_text(shell("Python laboratory", labbody, chapters), encoding="utf-8")
    for slug in ("references", "about"):
        authored = ROOT / f"frontmatter/{slug}.html"
        body = authored.read_text(encoding="utf-8") if authored.exists() else '<p>Course production is in progress. Public provenance is recorded in source-manifest.json and completion.json.</p>'
        (ROOT / f"{slug}.html").write_text(shell("References and attribution" if slug == "references" else "Sources and verification", body, chapters), encoding="utf-8")
    write(ROOT / "completion.json", dict(complete=complete, editorial_complete=editorial_complete, planned_chapters=len(plan["chapters"]), drafted_chapters=len(records), accepted_chapters=accepted, chapters=records))
    print(json.dumps(dict(drafted=len(records), accepted=accepted, planned=len(plan["chapters"]))))


if __name__ == "__main__":
    main()
