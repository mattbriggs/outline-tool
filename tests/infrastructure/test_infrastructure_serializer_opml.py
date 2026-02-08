"""
Unit tests for outline_tool.infrastructure.serializers.opml.

These tests validate:
- OPML serialization structure
- Deserialization into canonical payload shape
- Handling of collapsed state
- Optional preservation of node identifiers
- Failure on malformed or unsupported OPML

The serializer supports a strict, structural subset of OPML.
"""

from __future__ import annotations

import pytest
from xml.etree import ElementTree as ET

from outline_tool.infrastructure.serializers.opml import OPMLSerializer


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture()
def serializer() -> OPMLSerializer:
    """Return an OPML serializer instance."""
    return OPMLSerializer()


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


def test_dumps_returns_xml_string(serializer: OPMLSerializer, sample_payload: dict):
    text = serializer.dumps(sample_payload)

    assert isinstance(text, str)
    assert text.lstrip().startswith("<?xml")
    assert "<opml" in text
    assert "</opml>" in text


def test_dumps_produces_valid_xml(serializer: OPMLSerializer, sample_payload: dict):
    text = serializer.dumps(sample_payload)

    # Should parse without error
    root = ET.fromstring(text)
    assert root.tag == "opml"


def test_dumps_emits_outline_elements(serializer: OPMLSerializer, sample_payload: dict):
    text = serializer.dumps(sample_payload)
    root = ET.fromstring(text)

    body = root.find("body")
    assert body is not None

    outlines = body.findall(".//outline")
    assert len(outlines) == 3  # A, A1, B


def test_dumps_encodes_collapsed_state(serializer: OPMLSerializer, sample_payload: dict):
    text = serializer.dumps(sample_payload)
    root = ET.fromstring(text)

    collapsed_nodes = root.findall(".//outline[@isCollapsed='true']")
    assert len(collapsed_nodes) == 1
    assert collapsed_nodes[0].attrib.get("text") == "Section A1"


# -----------------------------------------------------------------------------
# loads
# -----------------------------------------------------------------------------


def test_loads_parses_valid_opml(serializer: OPMLSerializer):
    text = """<?xml version="1.0" encoding="UTF-8"?>
<opml version="2.0">
  <head>
    <title>Example</title>
  </head>
  <body>
    <outline text="Chapter A">
      <outline text="Section A1" isCollapsed="true"/>
    </outline>
    <outline text="Chapter B"/>
  </body>
</opml>
"""

    payload = serializer.loads(text)
    root = payload["root"]

    assert len(root["children"]) == 2

    a, b = root["children"]
    assert a["title"] == "Chapter A"
    assert a["children"][0]["collapsed"] is True
    assert b["title"] == "Chapter B"


def test_loads_preserves_node_id_if_present(serializer: OPMLSerializer):
    text = """<?xml version="1.0" encoding="UTF-8"?>
<opml version="2.0">
  <body>
    <outline text="Node A" id="node-a"/>
  </body>
</opml>
"""

    payload = serializer.loads(text)
    node = payload["root"]["children"][0]

    assert node["node_id"] == "node-a"


def test_loads_accepts_collapsed_attribute_variants(serializer: OPMLSerializer):
    text = """<?xml version="1.0" encoding="UTF-8"?>
<opml version="2.0">
  <body>
    <outline text="A" collapsed="true"/>
  </body>
</opml>
"""

    payload = serializer.loads(text)
    node = payload["root"]["children"][0]

    assert node["collapsed"] is True


def test_loads_rejects_non_outline_elements(serializer: OPMLSerializer):
    text = """<?xml version="1.0" encoding="UTF-8"?>
<opml version="2.0">
  <body>
    <note>This is not allowed</note>
  </body>
</opml>
"""

    with pytest.raises(ValueError):
        serializer.loads(text)


def test_loads_rejects_missing_text_attribute(serializer: OPMLSerializer):
    text = """<?xml version="1.0" encoding="UTF-8"?>
<opml version="2.0">
  <body>
    <outline />
  </body>
</opml>
"""

    with pytest.raises(ValueError):
        serializer.loads(text)


# -----------------------------------------------------------------------------
# Round-trip (lossy by design)
# -----------------------------------------------------------------------------


def test_opml_round_trip_preserves_titles_and_structure(
    serializer: OPMLSerializer,
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