"""
Unit tests for application-layer use cases.

These tests validate:
- Happy-path behavior for each use case
- Contract enforcement via payload validation
- Failure handling (not found, invalid operations)
- Repository interaction semantics

No filesystem, no UI, no serializers.
These are *application-layer* tests.
"""

from __future__ import annotations

from outline_tool.application.dto import (
    AddNodeRequest,
    CreateDocumentRequest,
    DeleteNodeRequest,
    LoadDocumentRequest,
    RenameNodeRequest,
    SaveDocumentRequest,
    ToggleCollapseRequest,
)
from outline_tool.application.ports import (
    DocumentNotFoundError,
    StoredDocument,
)
from outline_tool.application.use_cases import (
    AddNode,
    CreateDocument,
    DeleteNode,
    LoadDocument,
    RenameNode,
    SaveDocument,
    ToggleCollapse,
)


# -----------------------------------------------------------------------------
# In-memory repository for testing
# -----------------------------------------------------------------------------


class InMemoryRepository:
    """Simple in-memory repository for use case tests."""

    def __init__(self) -> None:
        self._store: dict[str, StoredDocument] = {}

    def load(self, doc_id: str) -> StoredDocument:
        if doc_id not in self._store:
            raise DocumentNotFoundError(doc_id)
        return self._store[doc_id]

    def save(self, doc: StoredDocument) -> None:
        self._store[doc.doc_id] = doc


# -----------------------------------------------------------------------------
# Create / Load / Save
# -----------------------------------------------------------------------------


def test_create_and_load_document_round_trip():
    repo = InMemoryRepository()

    create = CreateDocument(repo)
    load = LoadDocument(repo)

    create_resp = create(CreateDocumentRequest(title="Test Doc"))

    assert create_resp.ok is True
    assert create_resp.doc_id is not None

    load_resp = load(LoadDocumentRequest(doc_id=create_resp.doc_id))

    assert load_resp.ok is True
    assert load_resp.document is not None
    assert load_resp.document.title == "Test Doc"


def test_load_document_not_found():
    repo = InMemoryRepository()
    load = LoadDocument(repo)

    resp = load(LoadDocumentRequest(doc_id="missing"))

    assert resp.ok is False
    assert resp.document is None


def test_save_document_updates_timestamp():
    repo = InMemoryRepository()

    create = CreateDocument(repo)
    save = SaveDocument(repo)

    create_resp = create(CreateDocumentRequest(title="Doc"))
    document = create_resp.document

    assert document is not None

    save_resp = save(SaveDocumentRequest(document=document, touch_updated=True))

    assert save_resp.ok is True
    assert save_resp.saved_doc_id == document.doc_id


# -----------------------------------------------------------------------------
# Node operations
# -----------------------------------------------------------------------------


def _create_doc_with_root(repo: InMemoryRepository) -> str:
    create = CreateDocument(repo)
    resp = create(CreateDocumentRequest(title="Doc"))
    assert resp.ok
    return resp.doc_id  # type: ignore[return-value]


def test_add_node_to_root():
    repo = InMemoryRepository()
    doc_id = _create_doc_with_root(repo)

    add_node = AddNode(repo)

    resp = add_node(
        AddNodeRequest(
            doc_id=doc_id,
            parent_id=repo.load(doc_id).payload["root"]["node_id"],
            title="Child",
        )
    )

    assert resp.ok is True
    assert resp.new_node_id is not None
    assert len(resp.document.root.children) == 1  # type: ignore[union-attr]


def test_rename_node():
    repo = InMemoryRepository()
    doc_id = _create_doc_with_root(repo)

    add_node = AddNode(repo)
    rename_node = RenameNode(repo)

    add_resp = add_node(
        AddNodeRequest(
            doc_id=doc_id,
            parent_id=repo.load(doc_id).payload["root"]["node_id"],
            title="Old Name",
        )
    )

    node_id = add_resp.new_node_id
    assert node_id is not None

    rename_resp = rename_node(
        RenameNodeRequest(
            doc_id=doc_id,
            node_id=node_id,
            new_title="New Name",
        )
    )

    assert rename_resp.ok is True
    assert rename_resp.document.root.children[0].title == "New Name"  # type: ignore[union-attr]


def test_toggle_collapse():
    repo = InMemoryRepository()
    doc_id = _create_doc_with_root(repo)

    add_node = AddNode(repo)
    toggle = ToggleCollapse(repo)

    add_resp = add_node(
        AddNodeRequest(
            doc_id=doc_id,
            parent_id=repo.load(doc_id).payload["root"]["node_id"],
            title="Child",
        )
    )

    node_id = add_resp.new_node_id
    assert node_id is not None

    toggle_resp = toggle(
        ToggleCollapseRequest(
            doc_id=doc_id,
            node_id=node_id,
            collapsed=None,
        )
    )

    assert toggle_resp.ok is True
    assert toggle_resp.document.root.children[0].collapsed is True  # type: ignore[union-attr]


def test_delete_node():
    repo = InMemoryRepository()
    doc_id = _create_doc_with_root(repo)

    add_node = AddNode(repo)
    delete_node = DeleteNode(repo)

    add_resp = add_node(
        AddNodeRequest(
            doc_id=doc_id,
            parent_id=repo.load(doc_id).payload["root"]["node_id"],
            title="Child",
        )
    )

    node_id = add_resp.new_node_id
    assert node_id is not None

    delete_resp = delete_node(
        DeleteNodeRequest(
            doc_id=doc_id,
            node_id=node_id,
        )
    )

    assert delete_resp.ok is True
    assert len(delete_resp.document.root.children) == 0  # type: ignore[union-attr]


def test_delete_missing_node_fails_gracefully():
    repo = InMemoryRepository()
    doc_id = _create_doc_with_root(repo)

    delete_node = DeleteNode(repo)

    resp = delete_node(
        DeleteNodeRequest(
            doc_id=doc_id,
            node_id="missing-node",
        )
    )

    assert resp.ok is False