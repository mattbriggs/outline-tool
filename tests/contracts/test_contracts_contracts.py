"""
Tests for outline_tool.contracts.contracts.

These tests verify:
- Schema loading from package resources
- Validator caching behavior
- Successful validation of a valid payload
- Proper exception behavior for invalid payloads
- Clear failure modes when schema or payload is broken
"""

from __future__ import annotations

import copy

import pytest
from jsonschema.exceptions import ValidationError

from outline_tool.contracts.contracts import (
    _get_outline_validator,
    _load_outline_schema,
    validate_outline_payload,
)


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture()
def valid_payload() -> dict:
    """Return a minimal valid outline payload."""
    return {
        "doc_id": "doc-1",
        "title": "Test Document",
        "root": {
            "node_id": "root",
            "title": "Root",
            "collapsed": False,
            "children": [],
        },
    }


# -----------------------------------------------------------------------------
# Schema loading
# -----------------------------------------------------------------------------


def test_schema_loads_from_package_data():
    schema = _load_outline_schema()

    assert isinstance(schema, dict)
    assert "$schema" in schema
    assert "properties" in schema


def test_schema_is_cached():
    schema_1 = _load_outline_schema()
    schema_2 = _load_outline_schema()

    # Same object instance due to lru_cache
    assert schema_1 is schema_2


def test_validator_is_cached():
    validator_1 = _get_outline_validator()
    validator_2 = _get_outline_validator()

    assert validator_1 is validator_2


# -----------------------------------------------------------------------------
# Validation success
# -----------------------------------------------------------------------------


def test_validate_outline_payload_accepts_valid_payload(valid_payload):
    # Should not raise
    validate_outline_payload(valid_payload)


# -----------------------------------------------------------------------------
# Validation failures
# -----------------------------------------------------------------------------


def test_validate_outline_payload_rejects_missing_required_field(valid_payload):
    payload = copy.deepcopy(valid_payload)
    payload.pop("title")

    with pytest.raises(ValidationError):
        validate_outline_payload(payload)


def test_validate_outline_payload_rejects_invalid_node_structure(valid_payload):
    payload = copy.deepcopy(valid_payload)
    payload["root"].pop("node_id")

    with pytest.raises(ValidationError):
        validate_outline_payload(payload)


def test_validate_outline_payload_rejects_extra_properties(valid_payload):
    payload = copy.deepcopy(valid_payload)
    payload["unexpected"] = "nope"

    with pytest.raises(ValidationError):
        validate_outline_payload(payload)


def test_validate_outline_payload_rejects_empty_title(valid_payload):
    payload = copy.deepcopy(valid_payload)
    payload["title"] = ""

    with pytest.raises(ValidationError):
        validate_outline_payload(payload)


def test_validate_outline_payload_rejects_invalid_child(valid_payload):
    payload = copy.deepcopy(valid_payload)
    payload["root"]["children"].append(
        {
            "node_id": "child-1",
            "title": "",  # invalid: minLength 1
            "collapsed": False,
            "children": [],
        }
    )

    with pytest.raises(ValidationError):
        validate_outline_payload(payload)