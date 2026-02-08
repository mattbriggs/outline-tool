"""
Unit tests for outline_tool.domain.models.

These tests validate:
- Identity generation
- Tree construction and traversal
- Child add/remove semantics
- Document aggregation behavior
- Symmetric serialization via to_payload / from_payload

The tests exercise only domain logic.
No persistence, no schemas, no I/O.
"""

from __future__ import annotations

import pytest

from outline_tool.domain.models import OutlineDocument, OutlineNode


# -----------------------------------------------------------------------------
# OutlineNode
# -----------------------------------------------------------------------------


def test_outline_node_has_generated_id():
    node = OutlineNode(title="Node")

    assert node.node_id
    assert isinstance(node.node_id, str)


def test_add_child_creates_and_appends_child():
    parent = OutlineNode(title="Parent")

    child = parent.add_child("Child")

    assert child in parent.children
    assert child.title == "Child"
    assert child.node_id != parent.node_id


def test_remove_child_removes_and_returns_child():
    parent = OutlineNode(title="Parent")
    child = parent.add_child("Child")

    removed = parent.remove_child(child.node_id)

    assert removed is child
    assert child not in parent.children


def test_remove_child_missing_raises_key_error():
    parent = OutlineNode(title="Parent")

    with pytest.raises(KeyError):
        parent.remove_child("missing-node")


def test_walk_yields_depth_first_order():
    root = OutlineNode(title="Root")
    a = root.add_child("A")
    b = root.add_child("B")
    a.add_child("A1")
    a.add_child("A2")

    nodes = list(root.walk())
    titles = [n.title for n in nodes]

    assert titles == ["Root", "A", "A1", "A2", "B"]


def test_node_to_payload_round_trip():
    root = OutlineNode(title="Root", node_id="root")
    child = root.add_child("Child")
    child.collapsed = True

    payload = root.to_payload()

    assert payload == {
        "node_id": "root",
        "title": "Root",
        "collapsed": False,
        "children": [
            {
                "node_id": child.node_id,
                "title": "Child",
                "collapsed": True,
                "children": [],
            }
        ],
    }


# -----------------------------------------------------------------------------
# OutlineDocument
# -----------------------------------------------------------------------------


def test_outline_document_has_root_and_id():
    doc = OutlineDocument(title="Doc")

    assert doc.doc_id
    assert doc.root.title == "Root"
    assert doc.root.node_id == "root"


def test_document_walk_delegates_to_root():
    doc = OutlineDocument(title="Doc")
    child = doc.root.add_child("Child")

    nodes = list(doc.walk())

    assert doc.root in nodes
    assert child in nodes


def test_document_to_payload_structure():
    doc = OutlineDocument(title="Doc")
    doc.root.add_child("Child")

    payload = doc.to_payload()

    assert payload["doc_id"] == doc.doc_id
    assert payload["title"] == "Doc"
    assert payload["root"]["node_id"] == "root"
    assert len(payload["root"]["children"]) == 1


# -----------------------------------------------------------------------------
# Reconstruction from payload
# -----------------------------------------------------------------------------


def test_from_payload_reconstructs_tree_structure():
    payload = {
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
                    "children": [
                        {
                            "node_id": "a1",
                            "title": "A1",
                            "collapsed": True,
                            "children": [],
                        }
                    ],
                },
                {
                    "node_id": "b",
                    "title": "B",
                    "collapsed": False,
                    "children": [],
                },
            ],
        },
    }

    doc = OutlineDocument.from_payload(payload)

    assert doc.doc_id == "doc-1"
    assert doc.title == "Test Document"

    root = doc.root
    assert root.node_id == "root"
    assert len(root.children) == 2

    a, b = root.children

    assert a.title == "A"
    assert a.children[0].title == "A1"
    assert a.children[0].collapsed is True

    assert b.title == "B"
    assert not b.children


def test_from_payload_preserves_node_ids():
    payload = {
        "doc_id": "doc-x",
        "title": "Doc",
        "root": {
            "node_id": "root-x",
            "title": "Root",
            "collapsed": False,
            "children": [],
        },
    }

    doc = OutlineDocument.from_payload(payload)

    assert doc.root.node_id == "root-x"


def test_payload_round_trip_document():
    doc = OutlineDocument(title="Doc")
    doc.root.add_child("Child")

    payload = doc.to_payload()
    rebuilt = OutlineDocument.from_payload(payload)

    assert rebuilt.doc_id == doc.doc_id
    assert rebuilt.title == doc.title
    assert rebuilt.root.node_id == "root"
    assert rebuilt.root.children[0].title == "Child"


# -----------------------------------------------------------------------------
# Invariant sanity checks
# -----------------------------------------------------------------------------


def test_children_list_is_not_shared_between_nodes():
    parent1 = OutlineNode(title="Parent 1")
    parent2 = OutlineNode(title="Parent 2")

    parent1.add_child("Child 1")

    assert not parent2.children