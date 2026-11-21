# Review procedure and implementation handoff

This is a proposed procedure for the independent case study. It is not an
operator-approved process or a record of approvals obtained.

1. **Establish the source pack.** Record the AD identity, effective date, source,
   checksum, referenced SB/Requirements Bulletin revisions, exceptions, credit
   provisions and any authorized AMOC. Verify currency in the applicable controlled
   system. A downloaded snapshot alone cannot establish current obligations.
2. **Establish configuration.** Record model, airframe identity, component position,
   part/serial identifiers, installed-part history and evidence completeness. A
   serial range is inclusive only where the controlled rule explicitly says so.
3. **Review applicability.** Evaluate each action's scope independently. MATCH is a
   rule match, not approval. UNKNOWN requires missing evidence to be obtained.
   NO_MATCH needs a known exclusion, with source and configuration hashes retained.
4. **Define the work.** An authorized engineer establishes instructions, due-time
   basis, dependencies, parts traceability, task access, labor and acceptance
   evidence. This program does not generate maintenance instructions from an AD.
5. **Plan implementation.** Compare only technically permissible options. Record
   line/base windows, completion time, quotations, operational impacts, responsible
   roles and review milestones. Mandatory timing constrains the cost comparison.
6. **Execute and close through the applicable organization.** Record approved
   signoffs, actual findings, new configuration, task completion and exceptions.
   Re-review if a source revision, configuration or approved method changes.
7. **Follow up.** Reliability reviews actual results and exposure. Supply/warranty
   coordinates a supported claim with the contract holder. Neither assumed economic
   benefit nor a complete packet is actual recovery.

The synthetic implementation example uses USD assumptions and a three-year annual
discounted-benefit calculation. Cost is labor hours × labor rate + quoted parts +
downtime hours × assumed downtime cost. NPV is the discounted avoided-event cost
minus implementation cost. Different windows are assumed to deliver the same
technical outcome; if that assumption fails they cannot be compared solely by cost.
No currency conversion, tax, escalation, probabilistic benefit or warranty recovery
is silently added. Completion, rather than window start, must precede the deadline.

The example's dates and approval booleans are synthetic inputs. Its day-14 deadline
does not come from the public Boeing AD. Real deadlines require the incorporated
requirements, exceptions, configuration and an authorized interpretation.
