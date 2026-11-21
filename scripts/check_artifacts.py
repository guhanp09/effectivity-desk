"""Check reviewed evidence and report integrity, with no implicit approval."""

import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
manifest = json.loads((root / "reports/build_manifest.json").read_text())
for group, directory in [("inputs", "data"), ("outputs", "reports")]:
    for name, expected in manifest[group].items():
        assert hashlib.sha256((root / directory / name).read_bytes()).hexdigest() == expected, name
review = json.loads((root / "reports/review.json").read_text())
assert review["approval"] is None
assert review["synthetic_planning"]["release_authority"] is None
assert sum(review["state_counts"].values()) == len(review["synthetic_reviews"])
assert all(r["recovery_usd"] is None for r in review["synthetic_warranty"])
assert len(review["manufacturer_scope_reviews"]) == 12
assert len(review["manufacturer_bulletin"]["sha256"]) == 64
for row in review["public_ad_case_reviews"]:
    if "paragraph(c)" in row["review_scope"] or "paragraph(j)" in row["review_scope"]:
        assert row["state"] == "UNKNOWN"
html = (root / "reports/index.html").read_text()
assert "Synthetic Service Bulletin" in html
assert review["source_snapshot"]["sha256"] in html
assert review["synthetic_planning"]["candidate_for_review"] in html
print(
    "Snapshot hashes, unresolved public effectivity, synthetic outputs and authority boundaries agree."
)
