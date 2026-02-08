"""
Unit tests for application-layer ports.

These tests validate:
- StoredDocument immutability and structure
- Runtime Protocol compliance via runtime_checkable
- Helper assertion functions
- Exception semantics

No infrastructure is tested here. These are *contract tests*.
"""

from __future__ import annotations

import pytest
from typing import Mapping, Any

from outline_tool.application.ports import (
    StoredDocument,
    DocumentRepository,
    Serializer,
    RepositoryError,
    DocumentNotFoundError,
    SerializationError,
    assert_repository,
    assert_serializer,
)


# -----------------------------------------------------------------------------
# StoredDocument
# -----------------------------------------------------------------------------


def test_stored_document_is_immutable():
    doc = StoredDocument(doc_id="doc-1", payload={"a": 1})

    assert doc.doc_id == "doc-1"
    assert doc.payload == {"a": 1}

    with pytest.raises(Exception):
        doc.doc_id = "doc-2"


def test_stored_document_accepts_mapping_payload():
    payload: Mapping[str, Any] = {"root": {"node_id": "n1"}}
    doc = StoredDocument(doc_id="doc-1", payload=payload)

    assert isinstance(doc.payload, Mapping)
    assert doc.payload["root"]["node_id"] == "n1"


# -----------------------------------------------------------------------------
# DocumentRepository Protocol
# -----------------------------------------------------------------------------


class DummyRepository:
    """Minimal repository implementation for protocol testing."""

    def __init__(self) -> None:
        self._store: dict[str, StoredDocument] = {}

    def load(self, doc_id: str) -> StoredDocument:
        if doc_id not in self._store:
            raise DocumentNotFoundError(doc_id)
        return self._store[doc_id]

    def save(self, doc: StoredDocument) -> None:
        self._store[doc.doc_id] = doc


def test_document_repository_protocol_accepts_valid_implementation():
    repo = DummyRepository()
    validated = assert_repository(repo)

    assert validated is repo
    assert isinstance(validated, DocumentRepository)


def test_document_repository_protocol_rejects_invalid_object():
    with pytest.raises(TypeError):
        assert_repository(object())


def test_document_repository_load_not_found_raises():
    repo = DummyRepository()

    with pytest.raises(DocumentNotFoundError):
        repo.load("missing-doc")


def test_document_repository_save_and_load_round_trip():
    repo = DummyRepository()
    doc = StoredDocument(doc_id="doc-1", payload={"x": 1})

    repo.save(doc)
    loaded = repo.load("doc-1")

    assert loaded == doc


# -----------------------------------------------------------------------------
# Serializer Protocol
# -----------------------------------------------------------------------------


class DummySerializer:
    """Minimal serializer for protocol testing."""

    format_name = "dummy"

    def dumps(self, payload: Mapping[str, Any]) -> str:
        return str(payload)

    def loads(self, text: str) -> Mapping[str, Any]:
        if not text:
            raise SerializationError("Empty input")
        return {"text": text}


def test_serializer_protocol_accepts_valid_implementation():
    serializer = DummySerializer()
    validated = assert_serializer(serializer)

    assert validated is serializer
    assert isinstance(validated, Serializer)
    assert serializer.format_name == "dummy"


def test_serializer_protocol_rejects_invalid_object():
    with pytest.raises(TypeError):
        assert_serializer(object())


def test_serializer_dumps_and_loads_round_trip():
    serializer = DummySerializer()
    payload = {"a": 1}

    text = serializer.dumps(payload)
    loaded = serializer.loads(text)

    assert loaded["text"] == str(payload)


def test_serializer_loads_raises_serialization_error():
    serializer = DummySerializer()

    with pytest.raises(SerializationError):
        serializer.loads("")


# -----------------------------------------------------------------------------
# Exception hierarchy
# -----------------------------------------------------------------------------


def test_repository_error_is_runtime_error():
    assert issubclass(RepositoryError, RuntimeError)


def test_document_not_found_is_repository_error():
    assert issubclass(DocumentNotFoundError, RepositoryError)


def test_serialization_error_is_runtime_error():
    assert issubclass(SerializationError, RuntimeError)