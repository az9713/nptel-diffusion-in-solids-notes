"""Capture actual figure renderings and check loaded images/inline SVG bounds."""
import argparse
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
from build_book import input_signature

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--chapters", type=int, nargs="+")
    args = parser.parse_args()
    numbers = args.chapters or list(range(1, 29))
    target = ROOT / "work/figure-checks"
    target.mkdir(parents=True, exist_ok=True)
    report = []
    with sync_playwright() as api:
        chrome = Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Google/Chrome/Application/chrome.exe"
        browser = api.chromium.launch(executable_path=str(chrome)) if chrome.exists() else api.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        for number in numbers:
            path = ROOT / f"chapter-{number:02d}.html"
            page.goto(path.as_uri(), wait_until="networkidle")
            page.evaluate("MathJax.startup.promise")
            for i, figure in enumerate(page.locator('main figure').all()):
                figure.scroll_into_view_if_needed()
                figure.evaluate("async el => { await Promise.all([...el.querySelectorAll('img')].map(im => im.decode().catch(() => null))); }")
                state = figure.evaluate("""el => ({
                    images: [...el.querySelectorAll('img')].map(im => ({src:im.getAttribute('src'),loaded:im.complete&&im.naturalWidth>0,alt:!!im.alt})),
                    caption: !!el.querySelector('figcaption'),
                    svg: [...el.querySelectorAll(':scope > svg')].map(svg => {
                        const b=svg.getBBox(),v=svg.viewBox.baseVal;
                        return {clipped:b.x<v.x-2||b.y<v.y-2||b.x+b.width>v.x+v.width+2||b.y+b.height>v.y+v.height+2};
                    })
                })""")
                state.update(chapter=number, figure=i+1)
                state["passed"] = state["caption"] and all(im["loaded"] and im["alt"] for im in state["images"]) and all(not s["clipped"] for s in state["svg"])
                figure.screenshot(path=str(target / f"ch{number:02d}-fig{i+1:02d}.png"))
                report.append(state)
        browser.close()
    result = dict(input_signature=input_signature(), figures=report, passed=all(r["passed"] for r in report), scope="Mechanical bounds/loading checks plus captured files for separate visual inspection")
    (ROOT / "validation/figure-checks.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(dict(figures=len(report), passed=result["passed"])))
    raise SystemExit(not result["passed"])


if __name__ == "__main__":
    main()
