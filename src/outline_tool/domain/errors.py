"""
Domain-level errors for the outline tool.

These exceptions represent violations of domain invariants or invalid domain
operations. They are raised by domain models and may be translated or handled
by higher layers (application, presentation, infrastructure).

Domain errors:
- Do not perform logging
- Do not depend on external frameworks
- Express intent, not implementation detail
"""

from __future__ import annotations

from typing import Optional


class DomainError(Exception):
    """Base class for all domain-level errors.

    This class exists to allow callers to catch all domain-related errors
    explicitly without accidentally swallowing infrastructure or system
    exceptions.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)


class InvalidNodeOperationError(DomainError):
    """Raised when an invalid operation is attempted on a node.

    Examples include:
    - Attempting to remove a non-existent child
    - Attempting to move a node into one of its descendants
    """

    def __init__(self, node_id: str, message: Optional[str] = None) -> None:
        detail = message or f"Invalid operation on node '{node_id}'."
        super().__init__(detail)
        self.node_id: str = node_id


class NodeNotFoundError(DomainError):
    """Raised when a node cannot be found in an outline document."""

    def __init__(self, node_id: str) -> None:
        super().__init__(f"Node not found: '{node_id}'.")
        self.node_id: str = node_id


class DocumentInvariantError(DomainError):
    """Raised when a document-level invariant is violated.

    Examples include:
    - Root node is missing
    - Document structure becomes disconnected
    """

    def __init__(self, doc_id: Optional[str], message: str) -> None:
        prefix = f"Document '{doc_id}': " if doc_id else "Document invariant violated: "
        super().__init__(prefix + message)
        self.doc_id: Optional[str] = doc_id


class InvalidDocumentOperationError(DomainError):
    """Raised when an invalid operation is attempted on a document.

    Examples include:
    - Attempting to delete the root node
    - Attempting to save a document in an invalid state
    """

    def __init__(self, doc_id: Optional[str], message: str) -> None:
        prefix = f"Document '{doc_id}': " if doc_id else ""
        super().__init__(prefix + message)
        self.doc_id: Optional[str] = doc_id