"""
Data Transfer Objects (DTOs) for the application layer.

This module defines immutable request/response DTOs used by application use cases.
DTOs provide a stable boundary between presentation (GUI/CLI) and application logic,
and between application logic and infrastructure adapters (repositories/serializers).

Design goals:
- Explicit, typed structures for use case inputs/outputs
- Immutable objects (frozen dataclasses) to avoid accidental mutation
- Minimal conversion helpers for canonical payload representation

The canonical persisted/interchange representation is the "outline payload" dict that
conforms to the JSON Schema in ``outline_tool.contracts/outline.schema.json``.

No domain logic belongs here. DTOs are boring by design.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal, Mapping, Sequence

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Type aliases
# -----------------------------------------------------------------------------

NodeId = str
DocId = str
FormatName = Literal[
    "opml",
    "markdown",
    "plaintext",
    "json",
    "yaml",
    "custom_json",
]

# -----------------------------------------------------------------------------
# DTOs for the canonical outline payload representation
# -----------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class NodeDTO:
    """A transferable representation of an outline node.

    Args:
        node_id: Stable unique identifier for the node.
        title: Human-readable node title.
        collapsed: Whether the node is collapsed in the UI.
        children: Child nodes.
    """

    node_id: NodeId
    title: str
    collapsed: bool = False
    children: tuple["NodeDTO", ...] = field(default_factory=tuple)

    def to_payload(self) -> dict[str, Any]:
        """Convert this node to a canonical payload dict.

        Returns:
            A JSON-serializable dict representation suitable for schema validation.
        """
        return {
            "node_id": self.node_id,
            "title": self.title,
            "collapsed": self.collapsed,
            "children": [c.to_payload() for c in self.children],
        }

    @staticmethod
    def from_payload(payload: Mapping[str, Any]) -> "NodeDTO":
        """Create a NodeDTO from a canonical payload mapping.

        Args:
            payload: Mapping with keys: node_id, title, collapsed, children.

        Returns:
            Parsed NodeDTO.

        Raises:
            KeyError: If required keys are missing.
            TypeError: If payload types are incompatible.
        """
        node_id = str(payload["node_id"])
        title = str(payload["title"])
        collapsed = bool(payload.get("collapsed", False))
        children_raw = payload.get("children", [])
        if not isinstance(children_raw, Sequence):
            raise TypeError("Node payload 'children' must be a sequence.")
        children = tuple(NodeDTO.from_payload(c) for c in children_raw)
        return NodeDTO(node_id=node_id, title=title, collapsed=collapsed, children=children)


@dataclass(frozen=True, slots=True)
class DocumentDTO:
    """A transferable representation of an outline document.

    Args:
        doc_id: Stable unique identifier for the document.
        title: Document title.
        root: Root node of the outline tree.
        created_utc: Optional created timestamp (UTC ISO-8601 string).
        updated_utc: Optional updated timestamp (UTC ISO-8601 string).
        meta: Optional metadata bag for future expansion (e.g., pipeline hooks).
    """

    doc_id: DocId
    title: str
    root: NodeDTO
    created_utc: str | None = None
    updated_utc: str | None = None
    meta: Mapping[str, Any] = field(default_factory=dict)

    def to_payload(self) -> dict[str, Any]:
        """Convert this document to the canonical payload dict.

        Notes:
            The JSON Schema contract may not require created/updated/meta today.
            These fields are included to support forward-compatible extensions.

        Returns:
            A JSON-serializable dict representation suitable for schema validation.
        """
        payload: dict[str, Any] = {
            "doc_id": self.doc_id,
            "title": self.title,
            "root": self.root.to_payload(),
        }

        # Optional fields: only include if present (keeps exports clean)
        if self.created_utc is not None:
            payload["created_utc"] = self.created_utc
        if self.updated_utc is not None:
            payload["updated_utc"] = self.updated_utc
        if self.meta:
            payload["meta"] = dict(self.meta)

        return payload

    @staticmethod
    def from_payload(payload: Mapping[str, Any]) -> "DocumentDTO":
        """Create a DocumentDTO from a canonical payload mapping.

        Args:
            payload: Mapping containing at minimum: doc_id, title, root.

        Returns:
            Parsed DocumentDTO.

        Raises:
            KeyError: If required keys are missing.
            TypeError: If payload types are incompatible.
        """
        doc_id = str(payload["doc_id"])
        title = str(payload["title"])
        root = NodeDTO.from_payload(payload["root"])

        created_utc = payload.get("created_utc")
        updated_utc = payload.get("updated_utc")
        meta = payload.get("meta", {})

        if created_utc is not None:
            created_utc = str(created_utc)
        if updated_utc is not None:
            updated_utc = str(updated_utc)
        if meta is None:
            meta = {}
        if not isinstance(meta, Mapping):
            raise TypeError("Document payload 'meta' must be a mapping if present.")

        return DocumentDTO(
            doc_id=doc_id,
            title=title,
            root=root,
            created_utc=created_utc,
            updated_utc=updated_utc,
            meta=meta,
        )


# -----------------------------------------------------------------------------
# Use case request/response DTOs
# -----------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class UseCaseResult:
    """Standardized use case result.

    Args:
        ok: True when the use case completed successfully.
        message: Human-readable summary (safe for UI display).
    """

    ok: bool
    message: str


@dataclass(frozen=True, slots=True)
class CreateDocumentRequest:
    """Input for a create-document use case.

    Args:
        title: Title for the new document.
    """

    title: str


@dataclass(frozen=True, slots=True)
class CreateDocumentResponse(UseCaseResult):
    """Output from a create-document use case.

    Args:
        ok: True when the document was created.
        message: Human-readable summary.
        doc_id: Identifier of the created document if ok.
        document: Optional canonical document snapshot.
    """

    doc_id: DocId | None = None
    document: DocumentDTO | None = None


@dataclass(frozen=True, slots=True)
class LoadDocumentRequest:
    """Input for a load-document use case.

    Args:
        doc_id: Identifier of the document to load.
    """

    doc_id: DocId


@dataclass(frozen=True, slots=True)
class LoadDocumentResponse(UseCaseResult):
    """Output from a load-document use case."""

    document: DocumentDTO | None = None


@dataclass(frozen=True, slots=True)
class SaveDocumentRequest:
    """Input for a save-document use case.

    Args:
        document: The document to save.
        touch_updated: If True, update the document's updated_utc field.
    """

    document: DocumentDTO
    touch_updated: bool = True


@dataclass(frozen=True, slots=True)
class SaveDocumentResponse(UseCaseResult):
    """Output from a save-document use case."""

    saved_doc_id: DocId | None = None


@dataclass(frozen=True, slots=True)
class AddNodeRequest:
    """Input for an add-node use case.

    Args:
        doc_id: Document to modify.
        parent_id: Parent node under which to add the new node.
        title: Title of the new node.
        position: Optional insertion index; append if None.
    """

    doc_id: DocId
    parent_id: NodeId
    title: str
    position: int | None = None


@dataclass(frozen=True, slots=True)
class AddNodeResponse(UseCaseResult):
    """Output from an add-node use case."""

    document: DocumentDTO | None = None
    new_node_id: NodeId | None = None


@dataclass(frozen=True, slots=True)
class RenameNodeRequest:
    """Input for a rename-node use case.

    Args:
        doc_id: Document to modify.
        node_id: Node to rename.
        new_title: New title value.
    """

    doc_id: DocId
    node_id: NodeId
    new_title: str


@dataclass(frozen=True, slots=True)
class RenameNodeResponse(UseCaseResult):
    """Output from a rename-node use case."""

    document: DocumentDTO | None = None


@dataclass(frozen=True, slots=True)
class DeleteNodeRequest:
    """Input for a delete-node use case.

    Args:
        doc_id: Document to modify.
        node_id: Node to delete.
    """

    doc_id: DocId
    node_id: NodeId


@dataclass(frozen=True, slots=True)
class DeleteNodeResponse(UseCaseResult):
    """Output from a delete-node use case."""

    document: DocumentDTO | None = None


@dataclass(frozen=True, slots=True)
class MoveNodeRequest:
    """Input for a move-node use case.

    Supports moving a node to a new parent and/or position.

    Args:
        doc_id: Document to modify.
        node_id: Node to move.
        new_parent_id: Destination parent node id.
        new_position: Destination index under new parent.
    """

    doc_id: DocId
    node_id: NodeId
    new_parent_id: NodeId
    new_position: int | None = None


@dataclass(frozen=True, slots=True)
class MoveNodeResponse(UseCaseResult):
    """Output from a move-node use case."""

    document: DocumentDTO | None = None


@dataclass(frozen=True, slots=True)
class ToggleCollapseRequest:
    """Input for a toggle-collapse use case.

    Args:
        doc_id: Document to modify.
        node_id: Node to toggle.
        collapsed: Optional explicit value; if None, invert existing state.
    """

    doc_id: DocId
    node_id: NodeId
    collapsed: bool | None = None


@dataclass(frozen=True, slots=True)
class ToggleCollapseResponse(UseCaseResult):
    """Output from a toggle-collapse use case."""

    document: DocumentDTO | None = None


@dataclass(frozen=True, slots=True)
class ExportDocumentRequest:
    """Input for an export-document use case.

    Args:
        doc_id: Document to export.
        format_name: Export format.
        include_meta: Whether to include optional metadata fields.
    """

    doc_id: DocId
    format_name: FormatName
    include_meta: bool = True


@dataclass(frozen=True, slots=True)
class ExportDocumentResponse(UseCaseResult):
    """Output from an export-document use case.

    Args:
        exported_text: The serialized document text for the chosen format.
    """

    exported_text: str | None = None


@dataclass(frozen=True, slots=True)
class ImportDocumentRequest:
    """Input for an import-document use case.

    Args:
        format_name: Format of the provided text.
        text: Serialized content to import.
        override_title: If provided, replace the imported title with this.
    """

    format_name: FormatName
    text: str
    override_title: str | None = None


@dataclass(frozen=True, slots=True)
class ImportDocumentResponse(UseCaseResult):
    """Output from an import-document use case."""

    document: DocumentDTO | None = None


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------


def utc_now_iso() -> str:
    """Return the current UTC time in ISO-8601 format.

    Returns:
        ISO-8601 string with timezone offset (UTC).
    """
    return datetime.now(tz=timezone.utc).isoformat(timespec="seconds")


def with_touched_updated(document: DocumentDTO) -> DocumentDTO:
    """Return a copy of the document with updated_utc set to now.

    Args:
        document: Existing document.

    Returns:
        New DocumentDTO with updated_utc changed.

    Notes:
        This is intentionally placed in DTO-land because it's a boundary concern,
        not a domain rule.
    """
    new_doc = DocumentDTO(
        doc_id=document.doc_id,
        title=document.title,
        root=document.root,
        created_utc=document.created_utc,
        updated_utc=utc_now_iso(),
        meta=document.meta,
    )
    logger.debug("Touched updated_utc for doc_id=%s", document.doc_id)
    return new_doc