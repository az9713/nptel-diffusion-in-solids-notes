"""Check shared reader interactions and actual private print proofs."""
import hashlib
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def main():
    with sync_playwright() as api:
        chrome = Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Google/Chrome/Application/chrome.exe"
        browser = api.chromium.launch(executable_path=str(chrome)) if chrome.exists() else api.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.goto((ROOT/"index.html").as_uri(), wait_until="networkidle")
        page.locator('#course-search').fill('Kirkendall')
        links = page.locator('#search-results a').all()
        assert links and all(link.get_attribute('href') for link in links)
        assert all('undefined' not in link.inner_text() for link in links)
        assert any(link.inner_text().startswith('13.') for link in links)
        assert any('chapter-13.html' in link.get_attribute('href') for link in links)
        page.goto((ROOT/"chapter-01.html").as_uri(), wait_until="networkidle")
        page.evaluate('MathJax.startup.promise')
        original_size = page.evaluate('parseFloat(getComputedStyle(document.body).fontSize)')
        page.locator('[data-action=larger]').click()
        assert page.evaluate('parseFloat(getComputedStyle(document.body).fontSize)') > original_size
        page.locator('[data-action=smaller]').click()
        assert page.evaluate('parseFloat(getComputedStyle(document.body).fontSize)') == original_size
        # Verify exact copy payload without replacing the user's OS clipboard.
        page.evaluate("Object.defineProperty(navigator, 'clipboard', {configurable:true, value:{writeText:async text=>{window.__copiedText=text;}}})")
        block = page.locator('pre').first
        block.evaluate("el => { const d=el.closest('details'); if(d)d.open=true; }")
        expected = block.inner_text()
        block.locator('..').locator('.copybtn').click()
        assert page.evaluate('window.__copiedText') == expected
        for number in (1, 20):
            page.goto((ROOT/f'chapter-{number:02d}.html').as_uri(), wait_until="networkidle")
            page.evaluate('MathJax.startup.promise')
            assert page.locator('main img').evaluate_all('ims=>ims.every(im=>im.complete&&im.naturalWidth>0)')
            proof = ROOT/f'work/print-ch{number:02d}.pdf'
            page.pdf(path=str(proof), format="A4", print_background=True)
            assert proof.read_bytes().startswith(b'%PDF-')
        browser.close()
    report = dict(passed=True, search="Kirkendall reaches Ch13", font_controls="passed",
                  copy_control="exact code payload captured through isolated clipboard mock; OS clipboard unchanged",
                  print_proofs=["Ch1 motion/static/solutions", "Ch20 eager offscreen scientific image"],
                  shared_assets={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/"assets/book.js", ROOT/"assets/book.css", ROOT/"assets/search-index.js")})
    (ROOT/"validation/controls-checks.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
