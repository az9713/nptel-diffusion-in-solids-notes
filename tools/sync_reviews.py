"""Import compact public summaries of actual private review records.

The portable builder consumes the public summaries and does not need these
private reports. This tool never invents reviews or changes their verdicts.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    count = 0
    for chapter in range(1, 29):
        summaries = []
        for round_number in (1, 2):
            path = ROOT / f"work/reviews/ch{chapter:02d}-r{round_number}.json"
            if not path.exists():
                continue
            raw = json.loads(path.read_text(encoding="utf-8"))
            kind = raw.get("review_type", raw.get("review_kind", ""))
            full = raw.get("full_review", "full" in kind.lower())
            independent = raw.get("independent_context", "independent" in kind.lower())
            assets = raw.get("assets", {})
            if not isinstance(assets, dict):
                assets = {}
            if chapter == 1 and isinstance(raw.get("asset_sha256"), str):
                assets["assets/diffusion.js"] = raw["asset_sha256"]
            verdict = str(raw.get("verdict", "pending")).lower()
            if verdict == "accept":
                verdict = "accepted"
            record = dict(chapter=chapter, round=round_number, reviewer=raw["reviewer"],
                          independent_context=bool(independent), full_review=bool(full),
                          verdict=verdict, body_sha256=raw.get("body_sha256"),
                          code_sha256=raw.get("code_sha256"), assets=assets,
                          open_blockers=len(raw.get("blocking_findings", [])),
                          limitations=raw.get("limitations", []),
                          private_review_record_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
            summaries.append(record)
            count += 1
        if summaries:
            target = ROOT / f"validation/chapters/ch{chapter:02d}.json"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(dict(reviews=summaries), indent=2) + "\n", encoding="utf-8")
    print(json.dumps(dict(actual_review_records=count)))


if __name__ == "__main__":
    main()
