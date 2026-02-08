"""
Application ports (interfaces).

This module defines *application-layer boundaries* that must be implemented by
infrastructure adapters (repositories, serializers). Presentation and use cases
depend on these abstractions, never on concrete implementations.

Design principles:
- Explicit contracts, minimal behavior
- No I/O or framework dependencies
- Logging at boundary entry points only
- Typed, immutable transfer objects
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Mapping, Protocol, runtime_checkable

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Exceptions
# -----------------------------------------------------------------------------


class RepositoryError(RuntimeError):
    """Base exception for repository-related failures."""


class DocumentNotFoundError(RepositoryError):
    """Raised when a document cannot be found."""


class SerializationError(RuntimeError):
    """Raised when serialization or deserialization fails."""


# -----------------------------------------------------------------------------
# Data transfer records
# -----------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class StoredDocument:
    """Immutable record representing a persisted document.

    Args:
        doc_id: Stable document identifier.
        payload: Canonical document payload conforming to the JSON Schema
            defined in ``outline_tool.contracts.outline.schema.json``.
    """

    doc_id: str
    payload: Mapping[str, Any]


# -----------------------------------------------------------------------------
# Repository port
# -----------------------------------------------------------------------------


@runtime_checkable
class DocumentRepository(Protocol):
    """Persistence port for outline documents.

    Implementations are responsible for:
    - Durable storage
    - Atomic writes
    - Returning schema-valid payloads

    Implementations are *not* responsible for:
    - Business logic
    - Payload mutation
    - Schema definition
    """

    def load(self, doc_id: str) -> StoredDocument:
        """Load a document by id.

        Args:
            doc_id: Identifier of the document to load.

        Returns:
            StoredDocument containing the canonical payload.

        Raises:
            DocumentNotFoundError: If the document does not exist.
            RepositoryError: For all other persistence failures.
        """
        ...

    def save(self, doc: StoredDocument) -> None:
        """Persist a document.

        Args:
            doc: Document record to persist.

        Raises:
            RepositoryError: If the document cannot be saved.
        """
        ...


# -----------------------------------------------------------------------------
# Serializer port
# -----------------------------------------------------------------------------


@runtime_checkable
class Serializer(Protocol):
    """Serialization port for import/export formats.

    A serializer converts between:
    - Canonical payload dicts (internal)
    - Textual representations (external formats)

    Serializers must be deterministic and reversible where possible.
    """

    #: Stable, lowercase format identifier (e.g. "opml", "markdown")
    format_name: str

    def dumps(self, payload: Mapping[str, Any]) -> str:
        """Serialize a canonical payload to text.

        Args:
            payload: Canonical document payload.

        Returns:
            Serialized textual representation.

        Raises:
            SerializationError: If serialization fails.
        """
        ...

    def loads(self, text: str) -> Mapping[str, Any]:
        """Deserialize text into a canonical payload.

        Args:
            text: Serialized document content.

        Returns:
            Canonical payload mapping.

        Raises:
            SerializationError: If deserialization fails.
        """
        ...


# -----------------------------------------------------------------------------
# Optional runtime helpers (non-invasive, test-friendly)
# -----------------------------------------------------------------------------


def assert_repository(repo: Any) -> DocumentRepository:
    """Assert that an object satisfies the DocumentRepository protocol.

    Args:
        repo: Object to validate.

    Returns:
        The same object, typed as DocumentRepository.

    Raises:
        TypeError: If the object does not satisfy the protocol.
    """
    if not isinstance(repo, DocumentRepository):
        raise TypeError(
            f"Object {repo!r} does not implement DocumentRepository protocol."
        )
    logger.debug("Validated DocumentRepository implementation: %s", type(repo).__name__)
    return repo


def assert_serializer(serializer: Any) -> Serializer:
    """Assert that an object satisfies the Serializer protocol.

    Args:
        serializer: Object to validate.

    Returns:
        The same object, typed as Serializer.

    Raises:
        TypeError: If the object does not satisfy the protocol.
    """
    if not isinstance(serializer, Serializer):
        raise TypeError(
            f"Object {serializer!r} does not implement Serializer protocol."
        )
    logger.debug(
        "Validated Serializer implementation: %s (%s)",
        type(serializer).__name__,
        getattr(serializer, "format_name", "<unknown>"),
    )
    return serializer