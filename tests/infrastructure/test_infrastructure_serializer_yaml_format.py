"""
Unit tests for outline_tool.infrastructure.serializers.yaml_format.

These tests validate:
- YAML serialization and deserialization
- Deterministic output
- Structural preservation on round-trip
- Normalized failure modes for invalid input

The serializer intentionally normalizes all failures to ValueError,
shielding callers from PyYAML implementation details.
"""

from __future__ import annotations

import pytest
import yaml

from outline_tool.infrastructure.serializers.yaml_format import YAMLSerializer


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture()
def serializer() -> YAMLSerializer:
    """Return a YAML serializer instance."""
    return YAMLSerializer()


@pytest.fixture()
def sample_payload() -> dict:
    """Return a representative outline payload."""
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
                    "title": "Chapter A",
                    "collapsed": False,
                    "children": [
                        {
                            "node_id": "a1",
                            "title": "Section A1",
                            "collapsed": True,
                            "children": [],
                        }
                    ],
                },
                {
                    "node_id": "b",
                    "title": "Chapter B",
                    "collapsed": False,
                    "children": [],
                },
            ],
        },
    }


# -----------------------------------------------------------------------------
# dumps
# -----------------------------------------------------------------------------


def test_dumps_returns_string(serializer: YAMLSerializer, sample_payload: dict):
    text = serializer.dumps(sample_payload)

    assert isinstance(text, str)
    assert text.strip() != ""


def test_dumps_produces_valid_yaml(serializer: YAMLSerializer, sample_payload: dict):
    text = serializer.dumps(sample_payload)

    parsed = yaml.safe_load(text)
    assert parsed == sample_payload


def test_dumps_is_deterministic(serializer: YAMLSerializer, sample_payload: dict):
    text1 = serializer.dumps(sample_payload)
    text2 = serializer.dumps(sample_payload)

    assert text1 == text2


def test_dumps_rejects_non_serializable_object(serializer: YAMLSerializer):
    payload = {"bad": object()}

    with pytest.raises(ValueError):
        serializer.dumps(payload)


# -----------------------------------------------------------------------------
# loads
# -----------------------------------------------------------------------------


def test_loads_parses_valid_yaml(serializer: YAMLSerializer, sample_payload: dict):
    text = yaml.safe_dump(sample_payload)

    loaded = serializer.loads(text)

    assert loaded == sample_payload


def test_loads_rejects_invalid_yaml(serializer: YAMLSerializer):
    text = """
    root:
      - this: [is: not: valid
    """

    with pytest.raises(ValueError):
        serializer.loads(text)


def test_loads_rejects_non_mapping_top_level(serializer: YAMLSerializer):
    text = yaml.safe_dump(["this", "is", "a", "list"])

    with pytest.raises(ValueError):
        serializer.loads(text)


# -----------------------------------------------------------------------------
# Round-trip
# -----------------------------------------------------------------------------


def test_yaml_round_trip_preserves_structure(
    serializer: YAMLSerializer,
    sample_payload: dict,
):
    text = serializer.dumps(sample_payload)
    loaded = serializer.loads(text)

    root = loaded["root"]
    assert len(root["children"]) == 2

    a = root["children"][0]
    assert a["title"] == "Chapter A"
    assert a["children"][0]["title"] == "Section A1"
    assert a["children"][0]["collapsed"] is True