# Quality review

The review focused on dangerous shortcuts in a seemingly simple applicability
table: treating absence as exclusion, flattening installed components, selecting
future revisions, and allowing financial convenience to override technical gates.

| Case | Result |
| --- | --- |
| Correct PN on one part, qualifying SN on another | NO_MATCH with a complete inventory; no cross-component match |
| Known nonmatching part, inventory incomplete | UNKNOWN; an unobserved matching installation remains possible |
| Known excluded model plus missing serial | NO_MATCH for an AND rule; known exclusion is sufficient |
| Missing serial with otherwise matching data | UNKNOWN; no type coercion or inferred serial |
| Future-effective revision | Current known revision remains selected |
| Configuration or source changes after review | Evidence-stamp comparison invalidates the saved result |
| Malformed rule with absent data | Rule validation fails rather than hiding invalid syntax behind UNKNOWN |
| Window starts before due date but finishes afterward | Excluded; start time alone cannot establish feasibility |
| Mandatory scope has negative assumed NPV | Still constrained by the due date; no economic-deferral recommendation |
| Quote missing or technical gate unresolved | No financial implementation candidate |
| Warranty packet complete | Candidate for contract review only; no recovery booked |

Forty-one tests cover the rule truth tables, same-component correlation, serial
boundaries and types, inventory completeness, document selection, changed evidence,
source-specific AD gaps, missing costs, completion timing and warranty state.
Artifact checks verify the source snapshot checksum, unresolved actual bulletin
membership, report totals and absence of approval/recovery claims.

The code uses explicit reviewed predicates. It does not extract executable rules
from prose, infer serial effectivity or interpret an SB it has not read. The small
standard-library core is deliberate: introducing document-search or language-model
services would not supply the missing controlled evidence.
