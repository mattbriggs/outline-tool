"""
Unit tests for outline_tool.domain.services.

These tests validate:
- Node lookup and parent resolution
- Move semantics and invariants
- Cycle prevention
- Structural integrity checks

No repositories, no schemas, no DTOs, no I/O.
Pure domain behavior only.
"""

from __future__ import annotations

import pytest

from outline_tool.domain.errors import (
    DocumentInvariantError,
    InvalidNodeOperationError,
    NodeNotFoundError,
)
from outline_tool.domain.models import OutlineDocument
from outline_tool.domain.services import (
    assert_tree_integrity,
    find_node,
    find_parent,
    move_node,
)


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture()
def simple_document() -> OutlineDocument:
    """Create a simple document with a small tree."""
    doc = OutlineDocument(title="Doc")
    a = doc.root.add_child("A")
    b = doc.root.add_child("B")
    a.add_child("A1")
    a.add_child("A2")
    b.add_child("B1")
    return doc


# -----------------------------------------------------------------------------
# find_node
# -----------------------------------------------------------------------------


def test_find_node_finds_existing_node(simple_document: OutlineDocument):
    root = simple_document.root
    node = root.children[0]

    found = find_node(simple_document, node.node_id)

    assert found is node


def test_find_node_raises_for_missing_node(simple_document: OutlineDocument):
    with pytest.raises(NodeNotFoundError):
        find_node(simple_document, "missing-node")


# -----------------------------------------------------------------------------
# find_parent
# -----------------------------------------------------------------------------


def test_find_parent_returns_parent(simple_document: OutlineDocument):
    a = simple_document.root.children[0]
    a1 = a.children[0]

    parent = find_parent(simple_document, a1.node_id)

    assert parent is a


def test_find_parent_returns_none_for_root(simple_document: OutlineDocument):
    parent = find_parent(simple_document, simple_document.root.node_id)

    assert parent is None


# -----------------------------------------------------------------------------
# move_node
# -----------------------------------------------------------------------------


def test_move_node_reparents_node(simple_document: OutlineDocument):
    root = simple_document.root
    a = root.children[0]
    b = root.children[1]
    a1 = a.children[0]

    move_node(simple_document, a1.node_id, b.node_id)

    assert a1 not in a.children
    assert a1 in b.children


def test_move_node_preserves_node_identity(simple_document: OutlineDocument):
    a1 = simple_document.root.children[0].children[0]
    node_id = a1.node_id

    move_node(
        simple_document,
        node_id,
        simple_document.root.children[1].node_id,
    )

    moved = find_node(simple_document, node_id)

    assert moved.node_id == node_id


def test_move_node_inserts_at_position(simple_document: OutlineDocument):
    root = simple_document.root
    a = root.children[0]
    b = root.children[1]

    new = a.children[0]
    move_node(simple_document, new.node_id, b.node_id, position=0)

    assert b.children[0] is new


def test_move_root_node_is_disallowed(simple_document: OutlineDocument):
    with pytest.raises(InvalidNodeOperationError):
        move_node(
            simple_document,
            simple_document.root.node_id,
            simple_document.root.children[0].node_id,
        )


def test_move_node_into_descendant_is_disallowed(simple_document: OutlineDocument):
    a = simple_document.root.children[0]
    a1 = a.children[0]

    with pytest.raises(InvalidNodeOperationError):
        move_node(simple_document, a.node_id, a1.node_id)


def test_move_node_missing_target_raises(simple_document: OutlineDocument):
    a = simple_document.root.children[0]

    with pytest.raises(NodeNotFoundError):
        move_node(simple_document, a.node_id, "missing-parent")


def test_move_node_missing_node_raises(simple_document: OutlineDocument):
    b = simple_document.root.children[1]

    with pytest.raises(NodeNotFoundError):
        move_node(simple_document, "missing-node", b.node_id)


# -----------------------------------------------------------------------------
# assert_tree_integrity
# -----------------------------------------------------------------------------


def test_assert_tree_integrity_passes_for_valid_tree(simple_document: OutlineDocument):
    assert_tree_integrity(simple_document)


def test_assert_tree_integrity_detects_duplicate_ids():
    doc = OutlineDocument(title="Doc")
    a = doc.root.add_child("A")
    b = doc.root.add_child("B")

    b.node_id = a.node_id  # force corruption

    with pytest.raises(DocumentInvariantError):
        assert_tree_integrity(doc)
