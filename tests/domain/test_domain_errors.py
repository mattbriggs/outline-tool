"""
Unit tests for outline_tool.domain.errors.

These tests verify:
- Exception hierarchy and inheritance
- Attribute preservation (node_id, doc_id)
- Message construction semantics
- Catchability via the DomainError base class

No logging is tested here; logging belongs to callers.
"""

from __future__ import annotations

import pytest

from outline_tool.domain.errors import (
    DomainError,
    DocumentInvariantError,
    InvalidDocumentOperationError,
    InvalidNodeOperationError,
    NodeNotFoundError,
)


# -----------------------------------------------------------------------------
# Base class
# -----------------------------------------------------------------------------


def test_domain_error_is_exception():
    error = DomainError("something went wrong")

    assert isinstance(error, Exception)
    assert str(error) == "something went wrong"


def test_domain_error_is_catchable_as_domain_error():
    with pytest.raises(DomainError):
        raise NodeNotFoundError("node-123")


# -----------------------------------------------------------------------------
# Node-related errors
# -----------------------------------------------------------------------------


def test_node_not_found_error_properties():
    node_id = "node-abc"
    error = NodeNotFoundError(node_id)

    assert error.node_id == node_id
    assert node_id in str(error)


def test_invalid_node_operation_error_default_message():
    node_id = "node-xyz"
    error = InvalidNodeOperationError(node_id)

    assert error.node_id == node_id
    assert "Invalid operation" in str(error)
    assert node_id in str(error)


def test_invalid_node_operation_error_custom_message():
    node_id = "node-xyz"
    message = "Cannot move node into its descendant"
    error = InvalidNodeOperationError(node_id, message=message)

    assert error.node_id == node_id
    assert message in str(error)


# -----------------------------------------------------------------------------
# Document-related errors
# -----------------------------------------------------------------------------


def test_document_invariant_error_with_doc_id():
    doc_id = "doc-1"
    message = "Root node is missing"
    error = DocumentInvariantError(doc_id, message)

    assert error.doc_id == doc_id
    assert doc_id in str(error)
    assert message in str(error)


def test_document_invariant_error_without_doc_id():
    message = "Document structure is disconnected"
    error = DocumentInvariantError(None, message)

    assert error.doc_id is None
    assert message in str(error)


def test_invalid_document_operation_error_with_doc_id():
    doc_id = "doc-2"
    message = "Cannot delete root node"
    error = InvalidDocumentOperationError(doc_id, message)

    assert error.doc_id == doc_id
    assert doc_id in str(error)
    assert message in str(error)


def test_invalid_document_operation_error_without_doc_id():
    message = "Invalid document operation"
    error = InvalidDocumentOperationError(None, message)

    assert error.doc_id is None
    assert message in str(error)


# -----------------------------------------------------------------------------
# Hierarchy semantics
# -----------------------------------------------------------------------------


def test_all_domain_errors_inherit_from_domain_error():
    errors = [
        NodeNotFoundError("n1"),
        InvalidNodeOperationError("n2"),
        DocumentInvariantError("d1", "bad state"),
        InvalidDocumentOperationError("d2", "bad op"),
    ]

    for error in errors:
        assert isinstance(error, DomainError)