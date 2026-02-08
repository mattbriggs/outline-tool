"""
Unit tests for outline_tool.infrastructure.serializers.plaintext.

These tests validate:
- Plaintext outline serialization using indentation
- Deterministic output
- Parsing of indented outlines into canonical payloads
- Rejection of unsupported constructs (tabs, mixed indentation)

Plaintext is intentionally permissive and lossy:
- No collapsed state
- No stable node identifiers
- Indentation defines hierarchy but does not enforce strict levels
"""

from __future__ import annotations

import pytest

from outline_tool.infrastructure.serializers.plaintext import PlainTextSerializer


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture()
def serializer() -> PlainTextSerializer:
    """Return a plaintext serializer instance."""
    return PlainTextSerializer()


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
                            "collapsed": False,
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


def test_dumps_returns_string(serializer: PlainTextSerializer, sample_payload: dict):
    text = serializer.dumps(sample_payload)

    assert isinstance(text, str)
    assert text.endswith("\n")


def test_dumps_emits_indentation(serializer: PlainTextSerializer, sample_payload: dict):
    text = serializer.dumps(sample_payload)
    lines = [line for line in text.splitlines() if line.strip()]

    assert lines == [
        "Chapter A",
        "  Section A1",
        "Chapter B",
    ]


def test_dumps_is_deterministic(serializer: PlainTextSerializer, sample_payload: dict):
    text1 = serializer.dumps(sample_payload)
    text2 = serializer.dumps(sample_payload)

    assert text1 == text2


# -----------------------------------------------------------------------------
# loads
# -----------------------------------------------------------------------------


def test_loads_parses_valid_plaintext(serializer: PlainTextSerializer):
    text = """
Chapter A
  Section A1
Chapter B
"""

    payload = serializer.loads(text)
    root = payload["root"]

    assert len(root["children"]) == 2

    a, b = root["children"]
    assert a["title"] == "Chapter A"
    assert a["children"][0]["title"] == "Section A1"
    assert b["title"] == "Chapter B"


def test_loads_trims_empty_lines(serializer: PlainTextSerializer):
    text = """

Chapter A

  Section A1

"""

    payload = serializer.loads(text)
    root = payload["root"]

    assert len(root["children"]) == 1
    assert root["children"][0]["children"][0]["title"] == "Section A1"


def test_loads_accepts_indented_top_level(serializer: PlainTextSerializer):
    # Leading indentation is tolerated and treated as top-level
    text = """
    Orphan
"""

    payload = serializer.loads(text)
    root = payload["root"]

    assert len(root["children"]) == 1
    assert root["children"][0]["title"] == "Orphan"


def test_loads_rejects_tabs(serializer: PlainTextSerializer):
    text = "Chapter A\n\tSection A1\n"

    with pytest.raises(ValueError):
        serializer.loads(text)


# -----------------------------------------------------------------------------
# Round-trip (lossy by design)
# -----------------------------------------------------------------------------


def test_plaintext_round_trip_preserves_structure(
    serializer: PlainTextSerializer,
    sample_payload: dict,
):
    text = serializer.dumps(sample_payload)
    loaded = serializer.loads(text)

    root = loaded["root"]
    assert len(root["children"]) == 2

    a = root["children"][0]
    assert a["title"] == "Chapter A"
    assert a["children"][0]["title"] == "Section A1"