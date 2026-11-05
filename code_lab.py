"""List or run the chapter laboratories from any working directory."""
import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("chapter", type=int, nargs="?", choices=range(1, 29))
    args = parser.parse_args()
    if args.chapter is None:
        print("Diffusion in Solids: 28 chapter laboratories")
        print("Run python code_lab.py CHAPTER (1 through 28).")
        labs = sorted((ROOT / "code").glob("ch[0-9][0-9].py"))
        for path in labs:
            relative = path.relative_to(ROOT).as_posix()
            print(f"  {int(path.stem[2:]):2d}: {relative}")
        return 0
    path = ROOT / f"code/ch{args.chapter:02d}.py"
    return subprocess.call([sys.executable, str(path)], cwd=ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
