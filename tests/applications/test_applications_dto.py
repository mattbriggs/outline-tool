"""
Unit tests for application-layer DTOs.

These tests validate:
- DTO construction and immutability
- Payload round-trip correctness
- Error handling for malformed payloads
- Helper utilities (timestamps, touch-updated)
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone

from outline_tool.application.dto import (
    AddNodeRequest,
    CreateDocumentRequest,
    CreateDocumentResponse,
    DeleteNodeRequest,
    DocumentDTO,
    ExportDocumentRequest,
    ImportDocumentRequest,
    LoadDocumentRequest,
    MoveNodeRequest,
    NodeDTO,
    RenameNodeRequest,
    SaveDocumentRequest,
    ToggleCollapseRequest,
    UseCaseResult,
    utc_now_iso,
    with_touched_updated,
)


# -----------------------------------------------------------------------------
# NodeDTO
# -----------------------------------------------------------------------------


def test_node_dto_to_payload_simple():
    node = NodeDTO(node_id="n1", title="Root")
    payload = node.to_payload()

    assert payload == {
        "node_id": "n1",
        "title": "Root",
        "collapsed": False,
        "children": [],
    }


def test_node_dto_round_trip_with_children():
    node = NodeDTO(
        node_id="n1",
        title="Root",
        collapsed=True,
        children=(
            NodeDTO(node_id="n2", title="Child A"),
            NodeDTO(node_id="n3", title="Child B"),
        ),
    )

    payload = node.to_payload()
    reconstructed = NodeDTO.from_payload(payload)

    assert reconstructed == node
    assert reconstructed.children[0].title == "Child A"
    assert reconstructed.children[1].node_id == "n3"


def test_node_dto_from_payload_invalid_children_type():
    payload = {
        "node_id": "n1",
        "title": "Bad",
        "collapsed": False,
        "children": "not-a-sequence",
    }

    with pytest.raises(TypeError):
        NodeDTO.from_payload(payload)


# -----------------------------------------------------------------------------
# DocumentDTO
# -----------------------------------------------------------------------------


def test_document_dto_to_payload_minimal():
    doc = DocumentDTO(
        doc_id="doc-1",
        title="Test Document",
        root=NodeDTO(node_id="root", title="Root"),
    )

    payload = doc.to_payload()

    assert payload["doc_id"] == "doc-1"
    assert payload["title"] == "Test Document"
    assert "created_utc" not in payload
    assert "updated_utc" not in payload
    assert "meta" not in payload


def test_document_dto_round_trip_with_metadata():
    doc = DocumentDTO(
        doc_id="doc-1",
        title="Doc",
        root=NodeDTO(node_id="root", title="Root"),
        created_utc="2024-01-01T00:00:00+00:00",
        updated_utc="2024-01-02T00:00:00+00:00",
        meta={"source": "unit-test"},
    )

    payload = doc.to_payload()
    reconstructed = DocumentDTO.from_payload(payload)

    assert reconstructed == doc
    assert reconstructed.meta["source"] == "unit-test"


def test_document_dto_from_payload_invalid_meta_type():
    payload = {
        "doc_id": "doc-1",
        "title": "Bad Meta",
        "root": {
            "node_id": "n1",
            "title": "Root",
            "collapsed": False,
            "children": [],
        },
        "meta": ["not", "a", "mapping"],
    }

    with pytest.raises(TypeError):
        DocumentDTO.from_payload(payload)


# -----------------------------------------------------------------------------
# UseCaseResult and basic request DTOs
# -----------------------------------------------------------------------------


def test_use_case_result_basic():
    result = UseCaseResult(ok=True, message="Success")

    assert result.ok is True
    assert result.message == "Success"


def test_create_document_request():
    req = CreateDocumentRequest(title="New Doc")
    assert req.title == "New Doc"


def test_load_document_request():
    req = LoadDocumentRequest(doc_id="doc-1")
    assert req.doc_id == "doc-1"


def test_save_document_request_defaults():
    doc = DocumentDTO(
        doc_id="doc-1",
        title="Doc",
        root=NodeDTO(node_id="root", title="Root"),
    )
    req = SaveDocumentRequest(document=doc)

    assert req.document == doc
    assert req.touch_updated is True


# -----------------------------------------------------------------------------
# Node operation request DTOs
# -----------------------------------------------------------------------------


def test_add_node_request():
    req = AddNodeRequest(
        doc_id="doc-1",
        parent_id="n1",
        title="Child",
        position=2,
    )

    assert req.doc_id == "doc-1"
    assert req.parent_id == "n1"
    assert req.title == "Child"
    assert req.position == 2


def test_rename_node_request():
    req = RenameNodeRequest(
        doc_id="doc-1",
        node_id="n2",
        new_title="Renamed",
    )

    assert req.new_title == "Renamed"


def test_delete_node_request():
    req = DeleteNodeRequest(doc_id="doc-1", node_id="n2")
    assert req.node_id == "n2"


def test_move_node_request():
    req = MoveNodeRequest(
        doc_id="doc-1",
        node_id="n2",
        new_parent_id="n3",
        new_position=None,
    )

    assert req.new_parent_id == "n3"
    assert req.new_position is None


def test_toggle_collapse_request():
    req = ToggleCollapseRequest(
        doc_id="doc-1",
        node_id="n2",
        collapsed=None,
    )

    assert req.collapsed is None


# -----------------------------------------------------------------------------
# Import / Export DTOs
# -----------------------------------------------------------------------------


def test_export_document_request():
    req = ExportDocumentRequest(
        doc_id="doc-1",
        format_name="markdown",
        include_meta=False,
    )

    assert req.format_name == "markdown"
    assert req.include_meta is False


def test_import_document_request():
    req = ImportDocumentRequest(
        format_name="json",
        text='{"doc_id": "x"}',
        override_title="Override",
    )

    assert req.override_title == "Override"


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------


def test_utc_now_iso_format():
    value = utc_now_iso()
    parsed = datetime.fromisoformat(value)

    assert parsed.tzinfo == timezone.utc


def test_with_touched_updated_changes_timestamp():
    doc = DocumentDTO(
        doc_id="doc-1",
        title="Doc",
        root=NodeDTO(node_id="root", title="Root"),
        updated_utc="2000-01-01T00:00:00+00:00",
    )

    new_doc = with_touched_updated(doc)

    assert new_doc.updated_utc != doc.updated_utc
    assert new_doc.doc_id == doc.doc_id
    assert new_doc.root == doc.root