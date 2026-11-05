"""Verify served reader bytes and representative live browser behavior."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    parser.add_argument("--commit", required=True,
                        help="Content commit independently verified at origin")
    parser.add_argument("--report", default="validation/publication-checks.json")
    args = parser.parse_args()
    base = args.base.rstrip("/") + "/"
    paths = list(ROOT.glob("*.html"))
    for folder in ("assets", "figures", "code"):
        paths.extend(p for p in (ROOT/folder).rglob("*") if p.is_file()
                     and "__pycache__" not in p.parts)
    paths = sorted(set(paths))

    def check(path):
        relative = path.relative_to(ROOT).as_posix()
        request = Request(base + relative + "?v=" + args.commit[:12],
                          headers={"User-Agent": "DiffusionNotesVerification/1.0",
                                   "Cache-Control": "no-cache"})
        try:
            with urlopen(request, timeout=45) as response:
                actual = response.read()
                status = response.status
            expected = digest(path.read_bytes())
            return dict(path=relative, status=status, local_sha256=expected,
                        served_sha256=digest(actual), passed=digest(actual) == expected)
        except Exception as error:
            return dict(path=relative, passed=False, error=str(error))

    with ThreadPoolExecutor(max_workers=8) as pool:
        served = list(pool.map(check, paths))
    layouts, errors = [], []
    with sync_playwright() as api:
        chrome = Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Google/Chrome/Application/chrome.exe"
        browser = api.chromium.launch(executable_path=str(chrome)) if chrome.exists() else api.chromium.launch()
        for width in (1280, 390):
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.on("pageerror", lambda error: errors.append(str(error)))
            for filename in ("index.html", "chapter-01.html", "chapter-18.html", "chapter-20.html"):
                page.goto(base + filename + "?v=" + args.commit[:12], wait_until="networkidle")
                page.evaluate("MathJax.startup.promise")
                state = page.evaluate("""() => ({
                    overflow:document.documentElement.scrollWidth>innerWidth+2,
                    mathErrors:document.querySelectorAll('mjx-merror,[data-mjx-error]').length,
                    headings:document.querySelectorAll('h1').length,
                    loadedImages:[...document.querySelectorAll('main img')].every(im=>im.complete&&im.naturalWidth>0)
                })""")
                state.update(page=filename, width=width)
                state["passed"] = not state["overflow"] and not state["mathErrors"] and state["headings"] == 1 and state["loadedImages"]
                layouts.append(state)
                if filename == "index.html":
                    page.locator("#course-search").fill("Kirkendall")
                    assert page.locator('#search-results a[href="chapter-13.html"]').count() > 0
                    assert "undefined" not in page.locator("#search-results").inner_text()
            page.close()
        browser.close()
    report = dict(base_url=base, content_commit=args.commit,
                  scope="All served reader/code/asset bytes; representative live desktop/mobile rendering and search",
                  served_files=served, live_layouts=layouts, javascript_errors=errors,
                  passed=all(r["passed"] for r in served + layouts) and not errors)
    target = (ROOT / args.report).resolve()
    if not target.is_relative_to(ROOT):
        raise ValueError("Report must remain inside the project workspace")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(dict(served_files=len(served), live_layouts=len(layouts),
                          mismatches=[r["path"] for r in served if not r["passed"]],
                          passed=report["passed"])))
    raise SystemExit(not report["passed"])


if __name__ == "__main__":
    main()
