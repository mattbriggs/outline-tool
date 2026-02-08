"""
Unit tests for outline_tool.infrastructure.serializers.json_format.

These tests validate:
- Correct JSON serialization and deserialization
- Deterministic round-tripping
- Failure modes for invalid input
- Structural expectations (top-level object)

No schema validation or domain reconstruction is performed here.
"""

from __future__ import annotations

import json
import pytest

from outline_tool.infrastructure.serializers.json_format import JSONSerializer


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture()
def serializer() -> JSONSerializer:
    return JSONSerializer()


@pytest.fixture()
def sample_payload() -> dict:
    return {
        "doc_id": "doc-1",
        "title": "Test Document",
        "root": {
            "node_id": "root",
            "title": "Root",
            "collapsed": False,
            "children": [
                {
                    "node_id": "a",
                    "title": "A",
                    "collapsed": False,
                    "children": [],
                },
                {
                    "node_id": "b",
                    "title": "B",
                    "collapsed": True,
                    "children": [],
                },
            ],
        },
    }


# -----------------------------------------------------------------------------
# dumps
# -----------------------------------------------------------------------------


def test_dumps_returns_string(serializer: JSONSerializer, sample_payload: dict):
    text = serializer.dumps(sample_payload)

    assert isinstance(text, str)
    assert text.strip().startswith("{")
    assert text.strip().endswith("}")


def test_dumps_produces_valid_json(serializer: JSONSerializer, sample_payload: dict):
    text = serializer.dumps(sample_payload)

    parsed = json.loads(text)
    assert parsed == sample_payload


def test_dumps_is_deterministic(serializer: JSONSerializer, sample_payload: dict):
    text1 = serializer.dumps(sample_payload)
    text2 = serializer.dumps(sample_payload)

    assert text1 == text2


def test_dumps_raises_for_non_serializable_object(serializer: JSONSerializer):
    payload = {"bad": set([1, 2, 3])}

    with pytest.raises(TypeError):
        serializer.dumps(payload)


# -----------------------------------------------------------------------------
# loads
# -----------------------------------------------------------------------------


def test_loads_parses_valid_json(serializer: JSONSerializer, sample_payload: dict):
    text = json.dumps(sample_payload)

    loaded = serializer.loads(text)

    assert loaded == sample_payload


def test_loads_raises_for_invalid_json(serializer: JSONSerializer):
    text = "{ this is not valid JSON }"

    with pytest.raises(json.JSONDecodeError):
        serializer.loads(text)


def test_loads_raises_if_top_level_is_not_object(serializer: JSONSerializer):
    text = json.dumps(["not", "a", "dict"])

    with pytest.raises(ValueError):
        serializer.loads(text)


# -----------------------------------------------------------------------------
# Round-trip
# -----------------------------------------------------------------------------


def test_json_round_trip(serializer: JSONSerializer, sample_payload: dict):
    text = serializer.dumps(sample_payload)
    loaded = serializer.loads(text)

    assert loaded == sample_payload