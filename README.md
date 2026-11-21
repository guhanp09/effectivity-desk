# Effectivity Desk

Configuration and technical-document review with explicit **MATCH, NO_MATCH and
UNKNOWN** results. Missing effectivity evidence should create a review task, not
a green compliance badge.

**[Open the engineering review](https://guhanp09.github.io/effectivity-desk/)** ·
[Rule engine](src/effectivity_desk/rules.py) · [Review procedure](docs/review-procedure.md)

The public source study is **FAA AD 2026-09-01**, concerning Boeing 787 water-system
couplings. The AD is available; the complete incorporated manufacturer Requirements
Bulletins are not. Consequently the examples do not infer manufacturer effectivity,
due dates or compliance from model names alone.

A separate [Piper SB 1390 source study](data/piper_sb1390_scope.json) tests captured
model/serial group boundaries. Its configurations are fictitious; the manufacturer
PDF is linked rather than redistributed.

Separate invented SB/configuration cases exercise model, airframe serial, installed
part number, component serial and position. Nine cases produce **one match, four
known exclusions and four unresolved cases**. Component conditions must match the
same installed item. A document or configuration change invalidates a saved review.

## Reproduce

Python 3.12 or later. Core execution uses the standard library; the public AD
snapshot and synthetic inputs are checked in for offline reproduction.

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
python -m pytest -q
ruff check src tests scripts
effectivity-desk
python scripts/check_artifacts.py
```

Open `reports/index.html`. Actions checks the committed report against a fresh
build and publishes that verified artifact to Pages.

## Decisions the examples make visible

- The 787-10 remains in the AD's overall scope discussion; the new-inspection
  discussion does not erase retained requirements or the location-specific parts
  installation prohibition. Incorporated effectivity evidence remains necessary.
- An old part number on one component cannot pair with another component's serial
  number to satisfy an effectivity rule. An incomplete inventory cannot exclude an
  unobserved matching item.
- The known effective revision is selected as of the review date. It is only the
  latest revision in this supplied corpus, not proof the corpus is current.
- In a **separate synthetic mandatory-work scenario**, a cheaper late window is
  excluded; missing part quotes block calculation. A negative three-year benefit
  NPV does not permit deferring mandatory work. Base-window assumed cost is $1,390.
- Warranty examples queue invoices, part identities, installation/removal records
  and contract terms. They do not approve claims or book recovery.

This is an independent engineering study. It does not supply approved maintenance
data, an airworthiness determination, an AMOC or a maintenance release.
The public source and invented planning assumptions are identified in every output.

[Public AD source and paragraph notes](data/ad_2026_09_01.json) ·
[Captured public AD](data/sources/ad-2026-09-01.pdf) ·
[Source interpretation](docs/source-review.md) ·
[Quality review](docs/review-findings.md) ·
[Machine-readable output](reports/review.json)

MIT license applies to repository code. Manufacturer material retains its copyright.
The public Federal Register source retains
its attribution; proprietary incorporated Boeing documents are not redistributed.
