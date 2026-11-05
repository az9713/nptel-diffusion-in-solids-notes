"""Inspect actual reader DOM, controls, widths, printing and motion determinism."""
import hashlib
import argparse
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    selected = parser.add_mutually_exclusive_group()
    selected.add_argument("--chapters", type=int, nargs="+")
    selected.add_argument("--pages", nargs="+")
    args = parser.parse_args()
    findings = []
    errors = []
    if args.pages:
        if any(Path(name).name != name or not name.endswith(".html") for name in args.pages):
            parser.error("Page names must be root HTML filenames")
        pages = [ROOT / name for name in args.pages]
    elif args.chapters:
        pages = [ROOT / "index.html", *[ROOT / f"chapter-{n:02d}.html" for n in args.chapters]]
    else:
        pages = [ROOT / "index.html", *[p for p in sorted(ROOT.glob("*.html")) if p.name != "index.html"]]
    with sync_playwright() as api:
        installed_chrome = Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Google/Chrome/Application/chrome.exe"
        browser = api.chromium.launch(executable_path=str(installed_chrome)) if installed_chrome.exists() else api.chromium.launch()
        context = browser.new_context()
        for width in (1280, 650, 390):
            page = context.new_page()
            page.set_viewport_size({"width": width, "height": 900})
            console = []
            page.on("pageerror", lambda error: console.append(str(error)))
            for path in pages:
                console.clear()
                page.goto(path.as_uri(), wait_until="networkidle")
                page.wait_for_function("!window.MathJax || (MathJax.startup && MathJax.startup.document && document.querySelectorAll('mjx-container').length > 0) || !document.body.innerText.includes('\\\\(')")
                if page.evaluate("!!window.MathJax?.startup?.promise"):
                    page.evaluate("MathJax.startup.promise")
                result = page.evaluate("""() => ({
                    math: document.querySelectorAll('mjx-container').length,
                    mathErrors: document.querySelectorAll('mjx-merror, [data-mjx-error]').length,
                    overflow: document.documentElement.scrollWidth > innerWidth + 2,
                    headings: document.querySelectorAll('h1').length,
                    dark: document.documentElement.dataset.theme === 'dark'
                })""")
                result.update(page=path.name, width=width, javascript_errors=list(console),
                              html_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
                findings.append(result)
                if result["mathErrors"] or result["overflow"] or console or result["headings"] != 1:
                    errors.append(result)
                if path.name == "chapter-01.html":
                    widget = page.locator('.diffusion-widget')
                    widget.evaluate("el => el.renderFrame(0.2)")
                    state_a = widget.locator('.model-curve').get_attribute('points')
                    widget.evaluate("el => el.renderFrame(0.4)")
                    state_b = widget.locator('.model-curve').get_attribute('points')
                    widget.evaluate("el => el.renderFrame(0.2)")
                    assert state_a == widget.locator('.model-curve').get_attribute('points')
                    assert state_a != state_b
                    widget.locator('[data-motion=play]').click()
                    page.wait_for_timeout(200)
                    assert float(widget.get_attribute('data-time')) > 0.2
                    widget.locator('[data-motion=play]').click()
                    widget.locator('[data-motion=reset]').click()
                    assert float(widget.get_attribute('data-time')) == 0
                    widget.locator('[data-motion=speed]').select_option('0.5')
                    widget.locator('[data-motion=play]').click()
                    page.wait_for_timeout(200)
                    assert float(widget.get_attribute('data-time')) > 0
                    widget.locator('[data-motion=play]').click()
                    widget.locator('[data-motion=reset]').click()
                    page.locator('.exercise summary').first.click()
                    assert page.locator('.exercise details').first.get_attribute('open') is not None
                    page.locator('[data-action=theme]').click()
                    assert page.locator('html').get_attribute('data-theme') == 'light'
                    page.locator('[data-action=theme]').click()
                    if width == 1280:
                        page.evaluate('scrollTo(0, 0)')
                        page.screenshot(path=str(ROOT / "assets/reader-preview.png"))
                        widget.screenshot(path=str(ROOT / "work/motion-pilot.png"))
                    page.emulate_media(reduced_motion="reduce")
                    assert widget.locator('[data-motion=play]').inner_text() == 'Play'
                    page.emulate_media(media="print")
                    assert widget.locator('.motion-controls').is_hidden()
                    page.emulate_media(media="screen", reduced_motion="no-preference")
            page.close()
        browser.close()
    assets = {name:hashlib.sha256((ROOT/"assets"/name).read_bytes()).hexdigest()
              for name in ("book.css","book.js","math-config.js","mathjax-tex-svg.js","diffusion.js")}
    report = dict(pages=findings, shared_assets=assets,
                  motion="deterministic states, distinct times, play/pause/reset checked", errors=errors)
    suffix = "-" + "-".join(map(str, args.chapters)) if args.chapters else ("-" + "-".join(Path(p).stem for p in args.pages) if args.pages else "")
    name = "reader-checks" + suffix + ".json"
    (ROOT / "validation" / name).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(dict(layouts=len(findings), errors=len(errors))))
    raise SystemExit(bool(errors))


if __name__ == "__main__":
    main()
