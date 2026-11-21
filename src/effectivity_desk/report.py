"""Publish a source-limited real AD review beside clearly synthetic exercises."""

import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import date
from html import escape
from pathlib import Path

from effectivity_desk.planning import compare_options, warranty_queue
from effectivity_desk.rules import evaluate, evidence_stamp, select_revision


def table(rows, fields):
    result = "<div class='scroll'><table><thead><tr>"
    result += "".join(f"<th scope='col'>{escape(label)}</th>" for _, label in fields)
    result += "</tr></thead><tbody>"
    for row in rows:
        display = dict(row)
        for key, value in display.items():
            if isinstance(value, float):
                display[key] = f"{value:,.2f}" if key.endswith("_usd") else f"{value:.3f}"
        result += (
            "<tr>"
            + "".join(
                "<td>" + escape("—" if display.get(key) is None else str(display[key])) + "</td>"
                for key, _ in fields
            )
            + "</tr>"
        )
    return result + "</tbody></table></div>"


def csv_file(path, rows):
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0], lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build(root, as_of):
    data = root / "data"
    output = root / "reports"
    output.mkdir(exist_ok=True)
    source = json.loads((data / "ad_2026_09_01.json").read_text())
    if as_of < date.fromisoformat(source["effective_date"]):
        raise ValueError("Captured AD is not yet effective at the selected review date")
    pdf = data / source["snapshot_file"]
    if hashlib.sha256(pdf.read_bytes()).hexdigest() != source["sha256"]:
        raise ValueError("AD snapshot checksum mismatch")
    synthetic = json.loads((data / "synthetic_review.json").read_text())
    selected = select_revision(synthetic["documents"], as_of)
    if selected is None:
        raise ValueError("No synthetic document effective by review date")
    reviews = []
    for asset in synthetic["assets"]:
        finding = evaluate(selected["rule"], asset)
        reviews.append(
            {
                "asset": asset["id"],
                "revision": selected["revision"],
                "state": finding.state.value,
                "reason": "; ".join(finding.reasons),
                **evidence_stamp(selected, asset),
            }
        )
    public_reviews = []
    for case in source["review_cases"]:
        for scope, rule in source["public_rules"].items():
            finding = evaluate(rule, case)
            public_reviews.append(
                {
                    "case": case["id"],
                    "review_scope": scope,
                    "state": finding.state.value,
                    "reason": "; ".join(finding.reasons),
                }
            )
    bulletin = json.loads((data / "piper_sb1390_scope.json").read_text())
    bulletin_reviews = []
    for case in bulletin["cases"]:
        for group, rule in bulletin["rules"].items():
            finding = evaluate(rule, case)
            bulletin_reviews.append(
                {
                    "case": case["id"],
                    "captured_group": group,
                    "state": finding.state.value,
                    "reason": "; ".join(finding.reasons),
                }
            )
    planning = compare_options(synthetic["planning"])
    warranties = [
        {"case": record["id"], **warranty_queue(record)} for record in synthetic["warranty"]
    ]
    result = {
        "as_of": as_of.isoformat(),
        "source_snapshot": source,
        "synthetic_document": selected,
        "synthetic_reviews": reviews,
        "state_counts": dict(Counter(r["state"] for r in reviews)),
        "public_ad_case_reviews": public_reviews,
        "manufacturer_bulletin": bulletin,
        "manufacturer_scope_reviews": bulletin_reviews,
        "synthetic_planning": planning,
        "synthetic_warranty": warranties,
        "approval": None,
        "currency": "Known local snapshot only; not a search of all current ADs, AMOCs or SB revisions.",
    }
    (output / "review.json").write_text(json.dumps(result, indent=2) + "\n")
    csv_file(output / "synthetic_effectivity.csv", reviews)
    csv_file(output / "public_ad_scope_review.csv", public_reviews)
    csv_file(output / "manufacturer_scope_review.csv", bulletin_reviews)
    csv_file(output / "synthetic_options.csv", planning["options"])
    csv_file(
        output / "synthetic_warranty.csv",
        [{**r, "missing": "; ".join(r["missing"])} for r in warranties],
    )
    actual_table = table(
        public_reviews,
        [
            ("case", "Fictitious configuration"),
            ("review_scope", "Public paragraph scope"),
            ("state", "Evidence state"),
        ],
    )
    synthetic_table = table(
        reviews,
        [
            ("asset", "Synthetic asset"),
            ("revision", "Known revision"),
            ("state", "Rule result"),
            ("reason", "Evidence trail"),
        ],
    )
    bulletin_table = table(
        bulletin_reviews,
        [
            ("case", "Fictitious configuration"),
            ("captured_group", "Captured SB group"),
            ("state", "Scope state"),
        ],
    )
    bulletin_notes = "".join("<li>" + escape(note) + "</li>" for note in bulletin["review_notes"])
    costs = table(
        planning["options"],
        [
            ("option", "Assumed window"),
            ("cost_usd", "Assumed cost USD"),
            ("benefit_npv_usd", "3-year benefit NPV USD"),
            ("completion_day", "Completion day"),
            ("status", "Constraint result"),
        ],
    )
    warranty_table = table(
        [{**r, "missing": ", ".join(r["missing"])} for r in warranties],
        [
            ("case", "Synthetic claim"),
            ("state", "Review queue"),
            ("missing", "Missing evidence"),
            ("recovery_usd", "Recovery USD"),
        ],
    )
    notes = "".join(
        "<li>" + escape(n["paragraph"] + ": " + n["interpretation"]) + "</li>"
        for n in source["review_notes"]
    )
    html = f"""<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Effectivity Desk | Configuration review</title>
<style>body{{font:16px/1.55 system-ui,sans-serif;margin:0;color:#23343d;background:#f4f6f7}}
main{{max-width:1160px;margin:auto;padding:32px 22px}}h1{{font-size:2.5rem;margin:.2em 0}}
h2{{margin-top:2em}}a{{color:#065b82}}.note{{padding:14px;border-left:4px solid #ab661b;background:#fff6e6}}
.scroll{{overflow-x:auto}}table{{border-collapse:collapse;width:100%;font-size:.9rem;background:white}}
td,th{{padding:8px 10px;border-bottom:1px solid #c3d0d7;text-align:left;vertical-align:top}}
th{{background:#e3edf1}}code{{overflow-wrap:anywhere}}footer{{margin-top:3rem;border-top:1px solid #bccad0;padding-top:16px}}</style>
<main><header><p>Controlled-document and configuration review · {as_of}</p><h1>Effectivity Desk</h1>
<p>Keep an unresolved configuration unresolved, and put evidence before implementation cost.</p>
<a href="https://github.com/guhanp09/effectivity-desk">Source, tests and review procedure</a></header>
<p class="note">Independent study. This tool does not determine airworthiness, approve compliance,
authorize an AMOC or release an aircraft. Synthetic work scopes are not maintenance instructions.</p>
<h2>Public document study: FAA AD 2026-09-01</h2>
<p>Public Federal Register snapshot, effective June 3, 2026, ATA 38 Water/waste; Boeing 787 water-coupling
actions. Incorporated manufacturer Requirements Bulletins are not available in this repository.
The examples below use fictitious configurations. Model identity alone cannot establish effectivity.</p>
{actual_table}<ul>{notes}</ul>
<p>No due date or completed compliance is inferred from a missing incorporated bulletin.
This is a review of the captured AD, not a statement that no later AD, AMOC or manufacturer revision exists.</p>
<a href="{escape(source["url"], quote=True)}">Read the public AD</a> ·
<a href="public_ad_scope_review.csv">Scope review CSV</a>
<h2>Manufacturer bulletin: focused Piper SB 1390 review</h2>
<p>{escape(bulletin["scope"])} All configurations below are fictitious.</p>
{bulletin_table}<ul>{bulletin_notes}</ul>
<p><a href="{escape(bulletin["url"], quote=True)}">Manufacturer source PDF</a> ·
<a href="manufacturer_scope_review.csv">Captured-scope review CSV</a></p>
<h2>Synthetic Service Bulletin and installed-part cases</h2>
<p>Invented SB-SIM-PUMP-01, revision {selected["revision"]}, selected from the supplied corpus as of {as_of}.
Rules combine model, airframe serial range and a single component's part number, serial and position.
MATCH means a synthetic rule matches; it is not approval. NO_MATCH requires known excluding evidence.
UNKNOWN records absent data or an incomplete inventory.</p>{synthetic_table}
<p>Each review records hashes of its selected document and configuration. Any change requires re-review;
a future-effective revision cannot silently replace today's rule.</p>
<a href="synthetic_effectivity.csv">Effectivity evidence CSV</a>
<h2>Synthetic implementation comparison</h2><p>The assumed mandatory scope is due by day 14.
Only this invented scenario assumes applicability, approved scope and authorized review are complete.
Costs are USD assumptions, not vendor quotations or actual savings.</p>{costs}
<p>Candidate for further review: <strong>{escape(str(planning["candidate_for_review"]))}</strong>.
Negative economic NPV does not permit deferral of mandatory work. Late completion is excluded even when
cheaper; missing quotations block the comparison. No approval is issued.</p>
<a href="synthetic_options.csv">Assumed option calculations</a>
<h2>Work-scope handoff</h2><ol>
<li><strong>Engineering:</strong> establish current AD/SB/AMOC corpus and effectivity, verify location-specific configuration and obtain authorized scope review.</li>
<li><strong>Planning and supply:</strong> confirm due-time basis, labor, parts traceability, quoted costs and line/base window. Recalculate if any input changes.</li>
<li><strong>Maintenance and quality:</strong> use approved instructions and authorized signoffs; record actual findings and installed-part history.</li>
<li><strong>Reliability:</strong> reconcile subsequent findings and exposure, then review whether the assumed benefit occurred. Close only with reviewed evidence.</li></ol>
<p>These are proposed role assignments and gates, not meetings held or approvals obtained.</p>
<h2>Warranty evidence queue</h2>{warranty_table}
<p>No claim is approved and no recovery is booked. A complete evidence packet is only a candidate for contract review.</p>
<a href="synthetic_warranty.csv">Warranty queue CSV</a>
<footer><a href="review.json">Machine-readable review</a> ·
<a href="https://www.faa.gov/regulations_policies/airworthiness_directives">FAA AD overview</a>
<p>AD source SHA256: <code>{source["sha256"]}</code>. Public source review and invented examples are kept distinct.</p></footer></main></html>"""
    (output / "index.html").write_text(html)
    manifest = {"as_of": as_of.isoformat(), "inputs": {}, "outputs": {}}
    for group, paths in [
        ("inputs", sorted(data.rglob("*"))),
        ("outputs", sorted(output.glob("*.*"))),
    ]:
        for path in paths:
            if path.is_file() and "raw" not in path.parts and path.name != "build_manifest.json":
                name = str(path.relative_to(data if group == "inputs" else output))
                manifest[group][name] = hashlib.sha256(path.read_bytes()).hexdigest()
    (output / "build_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(
        json.dumps(
            {
                "states": result["state_counts"],
                "public_scope_cases": len(public_reviews),
                "planning_candidate": planning["candidate_for_review"],
                "approval": None,
            }
        )
    )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--as-of", type=date.fromisoformat, default=date(2026, 11, 21))
    args = parser.parse_args()
    build(args.root, args.as_of)


if __name__ == "__main__":
    main()
