"""
Application use cases for the Outline Tool.

Each use case is a small, command-style object that:
- Accepts explicit inputs
- Coordinates domain logic
- Enforces contracts
- Delegates persistence and serialization to ports

Use cases do not:
- Perform I/O directly
- Manipulate UI state
- Contain business rules beyond orchestration
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Mapping

from outline_tool.application.dto import (
    AddNodeRequest,
    AddNodeResponse,
    CreateDocumentRequest,
    CreateDocumentResponse,
    DeleteNodeRequest,
    DeleteNodeResponse,
    DocumentDTO,
    LoadDocumentRequest,
    LoadDocumentResponse,
    MoveNodeRequest,
    MoveNodeResponse,
    RenameNodeRequest,
    RenameNodeResponse,
    SaveDocumentRequest,
    SaveDocumentResponse,
    ToggleCollapseRequest,
    ToggleCollapseResponse,
    with_touched_updated,
)
from outline_tool.application.ports import (
    DocumentNotFoundError,
    DocumentRepository,
    RepositoryError,
    StoredDocument,
)
from outline_tool.contracts.contracts import validate_outline_payload
from outline_tool.domain.models import OutlineDocument, OutlineNode

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------


def _node_to_dict(node: OutlineNode) -> dict:
    """Convert a domain node to a canonical payload dict."""
    return {
        "node_id": node.node_id,
        "title": node.title,
        "collapsed": node.collapsed,
        "children": [_node_to_dict(c) for c in node.children],
    }


def _document_to_payload(document: OutlineDocument) -> dict:
    """Convert a domain document to a canonical payload dict."""
    return {
        "doc_id": document.doc_id,
        "title": document.title,
        "root": _node_to_dict(document.root),
    }


def _payload_to_dto(payload: Mapping) -> DocumentDTO:
    """Convert a canonical payload to a DocumentDTO."""
    return DocumentDTO.from_payload(payload)


def _find_node(root: OutlineNode, node_id: str) -> OutlineNode:
    """Find a node by id or raise KeyError."""
    for node in root.walk():
        if node.node_id == node_id:
            return node
    raise KeyError(f"Node not found: {node_id}")


def _remove_child(parent: OutlineNode, node_id: str) -> OutlineNode:
    """Remove a child node and return it."""
    for idx, child in enumerate(parent.children):
        if child.node_id == node_id:
            return parent.children.pop(idx)
    raise KeyError(node_id)


# -----------------------------------------------------------------------------
# Use cases
# -----------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CreateDocument:
    """Create and persist a new outline document."""

    repo: DocumentRepository

    def __call__(self, request: CreateDocumentRequest) -> CreateDocumentResponse:
        logger.debug("CreateDocument called with title=%r", request.title)

        doc = OutlineDocument(title=request.title)
        payload = _document_to_payload(doc)

        validate_outline_payload(payload)
        self.repo.save(StoredDocument(doc_id=doc.doc_id, payload=payload))

        logger.info("Created document %s", doc.doc_id)
        return CreateDocumentResponse(
            ok=True,
            message="Document created.",
            doc_id=doc.doc_id,
            document=_payload_to_dto(payload),
        )


@dataclass(frozen=True, slots=True)
class LoadDocument:
    """Load a document by id."""

    repo: DocumentRepository

    def __call__(self, request: LoadDocumentRequest) -> LoadDocumentResponse:
        logger.debug("LoadDocument called with doc_id=%s", request.doc_id)

        try:
            stored = self.repo.load(request.doc_id)
        except DocumentNotFoundError:
            logger.warning("Document not found: %s", request.doc_id)
            return LoadDocumentResponse(ok=False, message="Document not found.")

        return LoadDocumentResponse(
            ok=True,
            message="Document loaded.",
            document=_payload_to_dto(stored.payload),
        )


@dataclass(frozen=True, slots=True)
class SaveDocument:
    """Persist an existing document."""

    repo: DocumentRepository

    def __call__(self, request: SaveDocumentRequest) -> SaveDocumentResponse:
        document = request.document
        logger.debug("SaveDocument called for doc_id=%s", document.doc_id)

        if request.touch_updated:
            document = with_touched_updated(document)

        payload = document.to_payload()
        validate_outline_payload(payload)

        try:
            self.repo.save(StoredDocument(doc_id=document.doc_id, payload=payload))
        except RepositoryError as exc:
            logger.error("Failed to save document %s", document.doc_id, exc_info=exc)
            return SaveDocumentResponse(ok=False, message="Failed to save document.")

        logger.info("Saved document %s", document.doc_id)
        return SaveDocumentResponse(
            ok=True,
            message="Document saved.",
            saved_doc_id=document.doc_id,
        )


@dataclass(frozen=True, slots=True)
class AddNode:
    """Add a new node under a parent node."""

    repo: DocumentRepository

    def __call__(self, request: AddNodeRequest) -> AddNodeResponse:
        logger.debug(
            "AddNode called doc_id=%s parent_id=%s",
            request.doc_id,
            request.parent_id,
        )

        stored = self.repo.load(request.doc_id)
        document = OutlineDocument.from_payload(stored.payload)

        parent = _find_node(document.root, request.parent_id)
        new_node = OutlineNode(title=request.title)

        if request.position is None:
            parent.children.append(new_node)
        else:
            parent.children.insert(request.position, new_node)

        payload = _document_to_payload(document)
        validate_outline_payload(payload)
        self.repo.save(StoredDocument(doc_id=document.doc_id, payload=payload))

        logger.info("Added node %s to document %s", new_node.node_id, document.doc_id)
        return AddNodeResponse(
            ok=True,
            message="Node added.",
            new_node_id=new_node.node_id,
            document=_payload_to_dto(payload),
        )


@dataclass(frozen=True, slots=True)
class RenameNode:
    """Rename an existing node."""

    repo: DocumentRepository

    def __call__(self, request: RenameNodeRequest) -> RenameNodeResponse:
        logger.debug("RenameNode called node_id=%s", request.node_id)

        stored = self.repo.load(request.doc_id)
        document = OutlineDocument.from_payload(stored.payload)

        node = _find_node(document.root, request.node_id)
        node.title = request.new_title  # domain allows this mutation

        payload = _document_to_payload(document)
        validate_outline_payload(payload)
        self.repo.save(StoredDocument(doc_id=document.doc_id, payload=payload))

        logger.info("Renamed node %s", request.node_id)
        return RenameNodeResponse(
            ok=True,
            message="Node renamed.",
            document=_payload_to_dto(payload),
        )


@dataclass(frozen=True, slots=True)
class DeleteNode:
    """Delete a node from the document."""

    repo: DocumentRepository

    def __call__(self, request: DeleteNodeRequest) -> DeleteNodeResponse:
        logger.debug("DeleteNode called node_id=%s", request.node_id)

        stored = self.repo.load(request.doc_id)
        document = OutlineDocument.from_payload(stored.payload)

        for parent in document.root.walk():
            try:
                _remove_child(parent, request.node_id)
                break
            except KeyError:
                continue
        else:
            return DeleteNodeResponse(ok=False, message="Node not found.")

        payload = _document_to_payload(document)
        validate_outline_payload(payload)
        self.repo.save(StoredDocument(doc_id=document.doc_id, payload=payload))

        logger.info("Deleted node %s", request.node_id)
        return DeleteNodeResponse(
            ok=True,
            message="Node deleted.",
            document=_payload_to_dto(payload),
        )


@dataclass(frozen=True, slots=True)
class ToggleCollapse:
    """Toggle or set a node's collapsed state."""

    repo: DocumentRepository

    def __call__(self, request: ToggleCollapseRequest) -> ToggleCollapseResponse:
        logger.debug("ToggleCollapse called node_id=%s", request.node_id)

        stored = self.repo.load(request.doc_id)
        document = OutlineDocument.from_payload(stored.payload)

        node = _find_node(document.root, request.node_id)
        node.collapsed = (
            not node.collapsed if request.collapsed is None else request.collapsed
        )

        payload = _document_to_payload(document)
        validate_outline_payload(payload)
        self.repo.save(StoredDocument(doc_id=document.doc_id, payload=payload))

        logger.info("Toggled collapse for node %s", request.node_id)
        return ToggleCollapseResponse(
            ok=True,
            message="Node collapse toggled.",
            document=_payload_to_dto(payload),
        )