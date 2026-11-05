"""Execute companion laboratories and compare their saved JSON outputs."""
import argparse
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def equivalent(a, b):
    if isinstance(a, bool) or isinstance(b, bool):
        return type(a) is type(b) and a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isfinite(a) and math.isfinite(b) and math.isclose(a, b, rel_tol=1e-10, abs_tol=0)
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(equivalent(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(equivalent(x, y) for x, y in zip(a, b))
    return type(a) is type(b) and a == b


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--chapters", nargs="+", type=int)
    args = parser.parse_args()
    numbers = args.chapters or list(range(1, 29))
    records = []
    for number in numbers:
        path = ROOT / f"code/ch{number:02d}.py"
        saved = ROOT / f"code/ch{number:02d}-output.json"
        record = dict(chapter=number)
        try:
            result = subprocess.run([sys.executable, "-X", "utf8", str(path)], cwd=ROOT,
                                    capture_output=True, text=True, encoding="utf-8", timeout=90)
            record.update(exit_code=result.returncode,
                          code_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                          stdout_sha256=hashlib.sha256(result.stdout.encode()).hexdigest())
            if result.returncode:
                record.update(passed=False, error=result.stderr[-3000:])
            else:
                actual = json.loads(result.stdout)
                expected = json.loads(saved.read_text(encoding="utf-8"))
                record["saved_output_agrees"] = equivalent(actual, expected)
                record["passed"] = record["saved_output_agrees"]
        except (OSError, ValueError, subprocess.TimeoutExpired) as error:
            record.update(passed=False, error=str(error))
        records.append(record)
        print(json.dumps(dict(chapter=number, passed=record["passed"])), flush=True)
    report = dict(chapters=records, passed=all(r["passed"] for r in records))
    name = "laboratory-checks" + ("-" + "-".join(map(str, numbers)) if args.chapters else "") + ".json"
    (ROOT / "validation" / name).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    raise SystemExit(not report["passed"])


if __name__ == "__main__":
    main()
