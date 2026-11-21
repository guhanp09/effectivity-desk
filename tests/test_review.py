import json
from copy import deepcopy
from datetime import date
from pathlib import Path

import pytest

from effectivity_desk.planning import compare_options, warranty_queue
from effectivity_desk.rules import (
    State,
    evaluate,
    evidence_stamp,
    review_is_current,
    select_revision,
)

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "data/synthetic_review.json").read_text())
REVISION = DATA["documents"][1]


@pytest.mark.parametrize(
    "asset,expected",
    list(
        zip(
            DATA["assets"],
            [
                State.MATCH,
                State.NO_MATCH,
                State.UNKNOWN,
                State.NO_MATCH,
                State.UNKNOWN,
                State.UNKNOWN,
                State.NO_MATCH,
                State.NO_MATCH,
                State.UNKNOWN,
            ],
        )
    ),
)
def test_review_cases_have_independent_expected_results(asset, expected):
    assert evaluate(REVISION["rule"], asset).state == expected


def test_pn_and_serial_cannot_cross_match_different_components():
    rule = {"component": {"all": [{"in": {"pn": ["A"]}}, {"range": {"sn": [1, 10]}}]}}
    asset = {
        "components_complete": True,
        "components": [{"pn": "A", "sn": 20}, {"pn": "B", "sn": 5}],
    }
    assert evaluate(rule, asset).state == State.NO_MATCH


def test_incomplete_inventory_cannot_exclude_but_a_known_match_is_sufficient():
    rule = {"component": {"in": {"pn": ["A"]}}}
    assert evaluate(rule, {"components": []}).state == State.UNKNOWN
    assert evaluate(rule, {"components_complete": True, "components": []}).state == State.NO_MATCH
    assert (
        evaluate(rule, {"components_complete": False, "components": [{"pn": "A"}]}).state
        == State.MATCH
    )


def test_known_exclusion_beats_unknown_in_all_but_not_any():
    predicates = [{"in": {"model": ["A"]}}, {"range": {"sn": [1, 10]}}]
    assert evaluate({"all": predicates}, {"model": "B"}).state == State.NO_MATCH
    assert evaluate({"any": predicates}, {"model": "B"}).state == State.UNKNOWN


@pytest.mark.parametrize("value", [True, "100", 100.0, None])
def test_serial_evidence_requires_integer_not_coercion(value):
    assert evaluate({"range": {"sn": [100, 200]}}, {"sn": value}).state == State.UNKNOWN


@pytest.mark.parametrize(
    "value,expected",
    [(99, State.NO_MATCH), (100, State.MATCH), (200, State.MATCH), (201, State.NO_MATCH)],
)
def test_serial_bounds_are_inclusive(value, expected):
    assert evaluate({"range": {"sn": [100, 200]}}, {"sn": value}).state == expected


@pytest.mark.parametrize(
    "rule",
    [
        {"all": []},
        {"any": []},
        {"in": {"pn": []}},
        {"range": {"sn": [20, 10]}},
        {"unknown": 1},
        {"component": {"range": {"sn": [True, 2]}}},
    ],
)
def test_invalid_rules_fail_even_when_data_or_inventory_is_absent(rule):
    with pytest.raises(ValueError):
        evaluate(rule, {"components": [], "components_complete": True})


def test_unicode_dash_and_case_normalization_is_explicit_not_fuzzy():
    rule = {"in": {"pn": ["14C02-08C"]}}
    assert evaluate(rule, {"pn": " 14c02–08c "}).state == State.MATCH
    assert evaluate(rule, {"pn": "14C0208C"}).state == State.NO_MATCH


def test_future_revision_cannot_replace_effective_one():
    assert select_revision(DATA["documents"], date(2026, 11, 21))["revision"] == 2
    assert select_revision(DATA["documents"], date(2026, 11, 14))["revision"] == 1
    assert select_revision(DATA["documents"], date(2026, 8, 1)) is None
    with pytest.raises(ValueError, match="duplicate"):
        select_revision([REVISION, REVISION], date(2026, 11, 21))


def test_rule_and_configuration_changes_invalidate_review():
    asset = DATA["assets"][0]
    stamp = evidence_stamp(REVISION, asset)
    assert review_is_current(stamp, REVISION, deepcopy(asset))
    changed = deepcopy(asset)
    changed["components"][0]["serial"] = 700
    assert not review_is_current(stamp, REVISION, changed)
    assert not review_is_current(stamp, DATA["documents"][0], asset)


def test_real_ad_model_never_supplies_missing_bulletin_membership():
    public = json.loads((ROOT / "data/ad_2026_09_01.json").read_text())
    for case in public["review_cases"]:
        for scope in ["paragraph(c) overall effectivity", "paragraph(j) new actions"]:
            assert evaluate(public["public_rules"][scope], case).state == State.UNKNOWN
    scope = "paragraph(m) location-specific installation prohibition"
    assert evaluate(public["public_rules"][scope], public["review_cases"][1]).state == State.MATCH


def test_negative_npv_cannot_defer_assumed_mandatory_work():
    result = compare_options(DATA["planning"])
    assert result["candidate_for_review"] == "Base window"
    assert result["options"][1]["cost_usd"] == 1390
    assert result["options"][1]["benefit_npv_usd"] < 0
    assert result["options"][2]["status"] == "excluded: completes after due date"
    assert result["options"][3]["cost_usd"] is None
    assert result["release_authority"] is None


def test_window_start_before_deadline_but_completion_after_is_excluded():
    case = deepcopy(DATA["planning"])
    case["options"] = [{**case["options"][0], "day": 13.9, "downtime_hours": 12}]
    assert compare_options(case)["candidate_for_review"] is None


@pytest.mark.parametrize(
    "gate", ["applicability_confirmed", "approved_scope_available", "authorized_review"]
)
def test_unknown_technical_gates_block_financial_recommendation(gate):
    case = deepcopy(DATA["planning"])
    case[gate] = None
    assert compare_options(case)["candidate_for_review"] is None


def test_optional_negative_value_can_remain_unselected():
    case = deepcopy(DATA["planning"])
    case["mandatory"] = False
    assert compare_options(case)["candidate_for_review"] is None


@pytest.mark.parametrize("amount", [None, -1, "NaN", True])
def test_missing_or_invalid_costs_never_default_to_zero(amount):
    case = deepcopy(DATA["planning"])
    case["options"] = [{**case["options"][0], "parts_cost": amount}]
    assert compare_options(case)["options"][0]["cost_usd"] is None


def test_warranty_never_books_assumed_recovery():
    results = [warranty_queue(record) for record in DATA["warranty"]]
    assert [r["state"] for r in results] == [
        "evidence needed",
        "candidate for contract review",
        "outside supplied terms; review exceptions",
    ]
    assert all(r["recovery_usd"] is None for r in results)
