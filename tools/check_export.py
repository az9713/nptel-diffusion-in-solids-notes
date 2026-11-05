"""Create and test a public reading edition without private authoring inputs."""
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from build_book import input_signature

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "dist/reading-edition"
EXCLUDE = {".git", ".serena", ".venv", "work", "dist", "__pycache__", ".ruff_cache"}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if not TARGET.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError("Export target must remain inside the project workspace")
    TARGET.mkdir(parents=True, exist_ok=True)
    copied = []
    for path in ROOT.rglob("*"):
        relative = path.relative_to(ROOT)
        if any(part in EXCLUDE for part in relative.parts) or relative.parts[:2] == ("sources", "private"):
            continue
        if not path.is_file() or path.suffix == ".pyc" or path.name == "HANDOFF.md":
            continue
        destination = TARGET / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
        copied.append(relative.as_posix())
    # Do not retain files removed from the public input set on subsequent runs.
    allowed = set(copied)
    for path in TARGET.rglob("*"):
        if path.is_file() and path.relative_to(TARGET).as_posix() not in allowed:
            path.unlink()
    before = {p.name: digest(p) for p in TARGET.glob("*.html")}
    result = subprocess.run([sys.executable, "-X", "utf8", "tools/build_book.py"], cwd=TARGET,
                            capture_output=True, text=True, encoding="utf-8", timeout=60)
    after = {p.name: digest(p) for p in TARGET.glob("*.html")}
    check = subprocess.run([sys.executable, "-X", "utf8", "tools/check_book.py"], cwd=TARGET,
                           capture_output=True, text=True, encoding="utf-8", timeout=60)
    figures_before = {p.relative_to(TARGET).as_posix(): digest(p) for folder in ("assets", "figures")
                      for p in (TARGET/folder).glob("*.svg")}
    labs = subprocess.run([sys.executable, "-X", "utf8", "tools/run_labs.py"], cwd=TARGET,
                          capture_output=True, text=True, encoding="utf-8", timeout=600)
    figures_after = {p.relative_to(TARGET).as_posix(): digest(p) for folder in ("assets", "figures")
                     for p in (TARGET/folder).glob("*.svg")}
    report = dict(input_signature=input_signature(), laboratories_exit_code=labs.returncode,
                  figures_reproduced_byte_identically=figures_before == figures_after,
                  private_inputs_absent=not (TARGET/"sources/private").exists() and not (TARGET/"work").exists(),
                  copied_files=len(copied), build_exit_code=result.returncode,
                  checks_exit_code=check.returncode, html_byte_identical=before == after,
                  build_stdout=result.stdout, check_stdout=check.stdout)
    report["passed"] = report["private_inputs_absent"] and result.returncode == 0 and check.returncode == 0 and before == after and labs.returncode == 0 and figures_before == figures_after
    (ROOT/"validation/export-checks.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    raise SystemExit(not report["passed"])


if __name__ == "__main__":
    main()
