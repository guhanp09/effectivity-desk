"""Small explicit rule language; no inference from unverified narrative text."""

import hashlib
import json
from dataclasses import dataclass
from datetime import date
from enum import Enum


class State(str, Enum):
    MATCH = "MATCH"
    NO_MATCH = "NO_MATCH"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class Finding:
    state: State
    reasons: tuple[str, ...]


def normalized(value):
    if not isinstance(value, str):
        return value
    return value.strip().upper().replace("–", "-").replace("−", "-")


def combine(findings, operation):
    states = [f.state for f in findings]
    if operation == "all":
        state = (
            State.NO_MATCH
            if State.NO_MATCH in states
            else State.UNKNOWN
            if State.UNKNOWN in states
            else State.MATCH
        )
    else:
        state = (
            State.MATCH
            if State.MATCH in states
            else State.UNKNOWN
            if State.UNKNOWN in states
            else State.NO_MATCH
        )
    return Finding(state, tuple(reason for f in findings for reason in f.reasons))


def validate_rule(rule):
    if not isinstance(rule, dict) or len(rule) != 1:
        raise ValueError("Each rule node must have exactly one operator")
    op, value = next(iter(rule.items()))
    if op in {"all", "any"}:
        if not isinstance(value, list) or not value:
            raise ValueError("Empty or malformed logical rule")
        for child in value:
            validate_rule(child)
    elif op == "component":
        validate_rule(value)
    elif op in {"in", "range"}:
        if not isinstance(value, dict) or len(value) != 1:
            raise ValueError("One field per predicate is required")
        field, expected = next(iter(value.items()))
        if not isinstance(field, str) or not field:
            raise ValueError("Field name required")
        if op == "in":
            if (
                not isinstance(expected, list)
                or not expected
                or any(not isinstance(v, str) or not v.strip() for v in expected)
            ):
                raise ValueError("in requires a nonempty list of nonempty strings")
        elif (
            not isinstance(expected, list)
            or len(expected) != 2
            or any(isinstance(v, bool) or not isinstance(v, int) for v in expected)
            or expected[0] > expected[1]
        ):
            raise ValueError("range requires ordered integer bounds")
    else:
        raise ValueError(f"Unsupported rule operator: {op}")


def evaluate(rule, asset, path="asset"):
    validate_rule(rule)
    return _evaluate(rule, asset, path)


def _evaluate(rule, asset, path):
    if not isinstance(asset, dict):
        return Finding(State.UNKNOWN, (f"{path}: malformed configuration",))
    op, value = next(iter(rule.items()))
    if op in {"all", "any"}:
        return combine([_evaluate(child, asset, path) for child in value], op)
    if op == "component":
        components = asset.get("components")
        if not isinstance(components, list):
            return Finding(State.UNKNOWN, (f"{path}.components: inventory missing",))
        # Every predicate is evaluated on ONE installed component. PN and SN cannot
        # be satisfied by unrelated positions.
        findings = [
            _evaluate(value, part, f"{path}.components[{i}]") for i, part in enumerate(components)
        ]
        result = combine(findings, "any") if findings else Finding(State.NO_MATCH, ())
        if result.state == State.NO_MATCH and asset.get("components_complete") is not True:
            return Finding(State.UNKNOWN, result.reasons + (f"{path}: inventory incomplete",))
        return result
    field, expected = next(iter(value.items()))
    actual = asset.get(field)
    if actual is None or actual == "":
        return Finding(State.UNKNOWN, (f"{path}.{field}: missing",))
    if op == "in":
        if not isinstance(actual, str):
            return Finding(State.UNKNOWN, (f"{path}.{field}: invalid type",))
        match = normalized(actual) in [normalized(v) for v in expected]
    else:
        if isinstance(actual, bool) or not isinstance(actual, int):
            return Finding(State.UNKNOWN, (f"{path}.{field}: integer evidence needed",))
        match = expected[0] <= actual <= expected[1]
    return Finding(
        State.MATCH if match else State.NO_MATCH,
        (f"{path}.{field}: {'matches' if match else 'outside known scope'}",),
    )


def select_revision(documents, as_of):
    """Select within the supplied corpus only; this does not establish currency."""
    if len({d["document_id"] for d in documents}) > 1:
        raise ValueError("Select revisions for one document identity at a time")
    identities = set()
    for document in documents:
        key = (document["document_id"], document["revision"])
        if key in identities:
            raise ValueError("Ambiguous duplicate document revision")
        identities.add(key)
        if date.fromisoformat(document["issued_at"]) > date.fromisoformat(document["effective_at"]):
            raise ValueError("Issue date follows effective date")
    eligible = [d for d in documents if date.fromisoformat(d["effective_at"]) <= as_of]
    return max(eligible, key=lambda d: (d["effective_at"], d["revision"])) if eligible else None


def evidence_stamp(document, asset):
    def digest(value):
        return hashlib.sha256(
            json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()

    return {"document_sha256": digest(document), "configuration_sha256": digest(asset)}


def review_is_current(stamp, document, asset):
    return stamp == evidence_stamp(document, asset)
