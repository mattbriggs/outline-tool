"""
Unit tests for outline_tool.infrastructure.serializers.markdown.

These tests validate:
- Markdown serialization structure
- Deserialization into canonical payload shape
- Round-trip stability (within serializer constraints)
- Failure on unsupported Markdown constructs

The serializer supports a strict subset of Markdown:
- Headings define hierarchy
- Collapsed state via HTML comment markers
- Top-level headings may begin at any depth
"""

from __future__ import annotations

import pytest

from outline_tool.infrastructure.serializers.markdown import MarkdownSerializer


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture()
def serializer() -> MarkdownSerializer:
    """Return a Markdown serializer instance."""
    return MarkdownSerializer()


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


def test_dumps_returns_string(serializer: MarkdownSerializer, sample_payload: dict):
    text = serializer.dumps(sample_payload)

    assert isinstance(text, str)
    assert text.endswith("\n")


def test_dumps_emits_correct_heading_structure(
    serializer: MarkdownSerializer,
    sample_payload: dict,
):
    text = serializer.dumps(sample_payload)
    lines = [line for line in text.splitlines() if line.strip()]

    # Top-level siblings reset to H1.
    # Nesting only increases within a subtree.
    assert lines == [
        "# Chapter A",
        "## Section A1 <!-- collapsed -->",
        "# Chapter B",
    ]


def test_dumps_encodes_collapsed_state(
    serializer: MarkdownSerializer,
    sample_payload: dict,
):
    text = serializer.dumps(sample_payload)

    assert "<!-- collapsed -->" in text


# -----------------------------------------------------------------------------
# loads
# -----------------------------------------------------------------------------


def test_loads_parses_valid_markdown(serializer: MarkdownSerializer):
    text = """
# Chapter A
## Section A1 <!-- collapsed -->
# Chapter B
"""

    payload = serializer.loads(text)
    root = payload["root"]

    assert len(root["children"]) == 2

    a, b = root["children"]
    assert a["title"] == "Chapter A"
    assert a["children"][0]["collapsed"] is True
    assert b["title"] == "Chapter B"


def test_loads_accepts_top_level_non_h1(serializer: MarkdownSerializer):
    # The serializer is structurally tolerant:
    # any heading level may appear at the top level.
    text = """
### Orphan heading
"""

    payload = serializer.loads(text)
    root = payload["root"]

    assert len(root["children"]) == 1
    assert root["children"][0]["title"] == "Orphan heading"


def test_loads_rejects_non_heading_lines(serializer: MarkdownSerializer):
    text = """
# Chapter A
This line is not allowed
"""

    with pytest.raises(ValueError):
        serializer.loads(text)


# -----------------------------------------------------------------------------
# Round-trip
# -----------------------------------------------------------------------------


def test_markdown_round_trip_preserves_structure(
    serializer: MarkdownSerializer,
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