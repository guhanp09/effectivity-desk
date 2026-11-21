"""Assumed commercial scenarios are subordinate to technical constraints."""

from decimal import Decimal, InvalidOperation


def number(value, field):
    if value is None:
        raise ValueError(f"Missing {field}")
    if isinstance(value, bool):
        raise ValueError(f"Invalid {field}")
    try:
        result = Decimal(str(value))
    except InvalidOperation as error:
        raise ValueError(f"Invalid {field}") from error
    if not result.is_finite() or result < 0:
        raise ValueError(f"Invalid {field}")
    return result


def compare_options(case):
    """Synthetic scope only. A favorable NPV never overrides a due date or release gate."""
    rows = []
    required_gates = ("applicability_confirmed", "approved_scope_available", "authorized_review")
    gates_complete = all(case.get(gate) is True for gate in required_gates)
    mandatory = case.get("mandatory")
    if not isinstance(mandatory, bool):
        raise ValueError("mandatory status must be explicit")
    due = number(case.get("due_in_days"), "due date") if mandatory else None
    for option in case["options"]:
        row = {"option": option["name"], "basis": "synthetic planning assumptions"}
        try:
            day = number(option.get("day"), "window day")
            hours = number(option.get("labor_hours"), "labor hours")
            rate = number(option.get("labor_rate"), "labor rate")
            parts = number(option.get("parts_cost"), "parts cost")
            downtime = number(option.get("downtime_hours"), "downtime hours")
            downtime_rate = number(option.get("downtime_rate"), "downtime rate")
            cost = hours * rate + parts + downtime * downtime_rate
            annual = number(case.get("avoided_events_per_year"), "avoided events") * number(
                case.get("cost_per_event"), "event cost"
            )
            discount = number(case.get("discount_rate"), "discount rate")
            years = case.get("years")
            if isinstance(years, bool) or not isinstance(years, int) or years < 1:
                raise ValueError("Invalid horizon")
            npv = sum(annual / (1 + discount) ** year for year in range(1, years + 1)) - cost
            # Fractional downtime days are included in completion, not just window start.
            completed = day + downtime / 24
            status = (
                "blocked: technical evidence"
                if not gates_complete
                else "excluded: completes after due date"
                if mandatory and completed > due
                else "feasible assumed scope"
            )
            row.update(
                cost_usd=float(cost.quantize(Decimal("0.01"))),
                benefit_npv_usd=float(npv.quantize(Decimal("0.01"))),
                completion_day=float(completed),
                status=status,
            )
        except ValueError as error:
            row.update(
                cost_usd=None, benefit_npv_usd=None, completion_day=None, status=f"blocked: {error}"
            )
        rows.append(row)
    feasible = [r for r in rows if r["status"] == "feasible assumed scope"]
    if mandatory:
        # Compliance is a constraint. Never offer economic deferral of mandatory work.
        selected = min(feasible, key=lambda r: r["cost_usd"])["option"] if feasible else None
    else:
        favorable = [r for r in feasible if r["benefit_npv_usd"] >= 0]
        selected = (
            max(favorable, key=lambda r: r["benefit_npv_usd"])["option"] if favorable else None
        )
    return {
        "options": rows,
        "candidate_for_review": selected,
        "release_authority": None,
        "note": "Illustrative comparison, conditional on scope and evidence. No operational approval.",
    }


def warranty_queue(record):
    """Create an evidence queue, never an accepted claim or expected recovery."""
    required = [
        "part_number",
        "serial_number",
        "invoice",
        "installation_record",
        "removal_record",
        "contract_terms",
    ]
    missing = [field for field in required if not record.get(field)]
    if missing or record.get("within_terms") is None:
        return {"state": "evidence needed", "missing": missing, "recovery_usd": None}
    if record["within_terms"] is False:
        return {
            "state": "outside supplied terms; review exceptions",
            "missing": [],
            "recovery_usd": None,
        }
    if record["within_terms"] is not True:
        raise ValueError("within_terms must be a reviewed boolean or unknown")
    return {"state": "candidate for contract review", "missing": [], "recovery_usd": None}
