"""
Unit tests for outline_tool.infrastructure.repo_memory.

These tests validate:
- Save and load behavior
- Copy-on-read and copy-on-write semantics
- Not-found handling
- Convenience helpers (exists, count, clear)

No filesystem, no mocks, no application logic.
"""

from __future__ import annotations

import copy
import pytest

from outline_tool.application.ports import DocumentNotFoundError, StoredDocument
from outline_tool.infrastructure.repo_memory import InMemoryDocumentRepository


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------


def make_doc(doc_id: str, title: str = "Doc") -> StoredDocument:
    """Create a simple StoredDocument payload."""
    return StoredDocument(
        doc_id=doc_id,
        payload={
            "doc_id": doc_id,
            "title": title,
            "root": {
                "node_id": "root",
                "title": "Root",
                "collapsed": False,
                "children": [],
            },
        },
    )


# -----------------------------------------------------------------------------
# Basic save / load
# -----------------------------------------------------------------------------


def test_save_and_load_round_trip():
    repo = InMemoryDocumentRepository()
    doc = make_doc("doc-1")

    repo.save(doc)
    loaded = repo.load("doc-1")

    assert loaded.doc_id == doc.doc_id
    assert loaded.payload == doc.payload


def test_load_missing_document_raises():
    repo = InMemoryDocumentRepository()

    with pytest.raises(DocumentNotFoundError):
        repo.load("missing-doc")


# -----------------------------------------------------------------------------
# Copy semantics
# -----------------------------------------------------------------------------


def test_copy_on_read_prevents_payload_mutation():
    repo = InMemoryDocumentRepository(copy_on_read=True)
    doc = make_doc("doc-1")

    repo.save(doc)
    loaded = repo.load("doc-1")

    loaded.payload["title"] = "MUTATED"

    reloaded = repo.load("doc-1")
    assert reloaded.payload["title"] == "Doc"


def test_copy_on_write_prevents_post_save_mutation():
    repo = InMemoryDocumentRepository(copy_on_write=True)
    doc = make_doc("doc-1")

    repo.save(doc)
    doc.payload["title"] = "MUTATED"

    loaded = repo.load("doc-1")
    assert loaded.payload["title"] == "Doc"


def test_copy_on_read_disabled_allows_mutation():
    repo = InMemoryDocumentRepository(copy_on_read=False)
    doc = make_doc("doc-1")

    repo.save(doc)
    loaded = repo.load("doc-1")
    loaded.payload["title"] = "MUTATED"

    reloaded = repo.load("doc-1")
    assert reloaded.payload["title"] == "MUTATED"


def test_copy_on_write_disabled_allows_post_save_mutation():
    repo = InMemoryDocumentRepository(copy_on_write=False)
    doc = make_doc("doc-1")

    repo.save(doc)
    doc.payload["title"] = "MUTATED"

    loaded = repo.load("doc-1")
    assert loaded.payload["title"] == "MUTATED"


# -----------------------------------------------------------------------------
# Upsert semantics
# -----------------------------------------------------------------------------


def test_save_overwrites_existing_document():
    repo = InMemoryDocumentRepository()

    repo.save(make_doc("doc-1", title="First"))
    repo.save(make_doc("doc-1", title="Second"))

    loaded = repo.load("doc-1")
    assert loaded.payload["title"] == "Second"


# -----------------------------------------------------------------------------
# Initial preload
# -----------------------------------------------------------------------------


def test_initial_documents_are_loaded():
    docs = [make_doc("doc-1"), make_doc("doc-2")]
    repo = InMemoryDocumentRepository(initial=docs)

    assert repo.count() == 2
    assert repo.exists("doc-1")
    assert repo.exists("doc-2")


# -----------------------------------------------------------------------------
# Convenience helpers
# -----------------------------------------------------------------------------


def test_exists_returns_correct_value():
    repo = InMemoryDocumentRepository()
    repo.save(make_doc("doc-1"))

    assert repo.exists("doc-1") is True
    assert repo.exists("missing") is False


def test_count_returns_number_of_documents():
    repo = InMemoryDocumentRepository()
    repo.save(make_doc("doc-1"))
    repo.save(make_doc("doc-2"))

    assert repo.count() == 2


def test_clear_removes_all_documents():
    repo = InMemoryDocumentRepository()
    repo.save(make_doc("doc-1"))
    repo.save(make_doc("doc-2"))

    repo.clear()

    assert repo.count() == 0
    assert not repo.exists("doc-1")