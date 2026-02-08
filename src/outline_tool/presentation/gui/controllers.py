"""
GUI controllers for the Outline Tool.

Controllers coordinate between:
- GUI views
- Application use cases
- Infrastructure adapters

Controllers contain no GUI widget code and no domain logic.
"""

from __future__ import annotations

import logging
from typing import Optional

from outline_tool.application.dto import (
    AddNodeRequest,
    CreateDocumentRequest,
    DeleteNodeRequest,
    LoadDocumentRequest,
    RenameNodeRequest,
    SaveDocumentRequest,
)
from outline_tool.application.use_cases import (
    AddNode,
    CreateDocument,
    DeleteNode,
    LoadDocument,
    RenameNode,
    SaveDocument,
)
from outline_tool.domain.models import OutlineDocument
from outline_tool.infrastructure.repo_memory import InMemoryDocumentRepository
from outline_tool.infrastructure.serializers.base import Serializer
from outline_tool.presentation.gui.views import MainView

logger = logging.getLogger(__name__)


class OutlineController:
    """Controller coordinating GUI actions for the outline tool."""

    def __init__(
        self,
        *,
        view: MainView,
        repo: InMemoryDocumentRepository,
        serializers: dict[str, Serializer],
    ) -> None:
        self._view = view
        self._repo = repo
        self._serializers = serializers

        self._current_document: Optional[OutlineDocument] = None
        self._selected_node_id: Optional[str] = None

        # Use cases
        self._create = CreateDocument(repo)
        self._load = LoadDocument(repo)
        self._save = SaveDocument(repo)
        self._add_node = AddNode(repo)
        self._rename_node = RenameNode(repo)
        self._delete_node = DeleteNode(repo)

        # Wire selection callback
        self._view.document_view.set_selection_callback(
            self.on_selection_changed
        )

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    @property
    def current_document(self) -> Optional[OutlineDocument]:
        """Return the currently loaded document."""
        return self._current_document

    @property
    def selected_node_id(self) -> Optional[str]:
        """Return the currently selected node id."""
        return self._selected_node_id

    def on_selection_changed(self, node_id: Optional[str]) -> None:
        """Handle node selection changes from the view."""
        self._selected_node_id = node_id
        logger.debug("Selected node changed to %s", node_id)

    # ------------------------------------------------------------------
    # Document lifecycle
    # ------------------------------------------------------------------

    def new_document(self) -> None:
        """Create a new document."""
        title = self._view.dialogs.prompt_text(
            "Document title:",
            title="New Document",
            default="Untitled",
        )
        if not title:
            return

        resp = self._create(CreateDocumentRequest(title=title))
        self._current_document = resp.document
        self._selected_node_id = resp.document.root.node_id

        self._view.document_view.render(self._current_document)
        self._view.status_view.set("New document created")

        logger.info("Created new document %s", resp.doc_id)

    def save_current(self) -> None:
        """Save the current document."""
        if not self._current_document:
            self._view.dialogs.error("No document to save")
            return

        self._save(
            SaveDocumentRequest(
                document=self._current_document,
                touch_updated=True,
            )
        )

        self._view.status_view.set("Document saved")
        logger.info("Saved document %s", self._current_document.doc_id)

    def import_document(self) -> None:
        """Import a document from disk."""
        path = self._view.dialogs.pick_open_file(
            title="Import Document",
        )
        if not path:
            return

        ext = path.suffix.lstrip(".").lower()
        serializer = self._serializers.get(ext)

        if not serializer:
            self._view.dialogs.error(f"Unsupported format: .{ext}")
            return

        payload = serializer.loads(path.read_text(encoding="utf-8"))
        document = OutlineDocument.from_payload(payload)

        self._save(
            SaveDocumentRequest(
                document=document,
                touch_updated=False,
            )
        )

        self._current_document = document
        self._selected_node_id = document.root.node_id

        self._view.document_view.render(document)
        self._view.status_view.set(f"Imported {path.name}")

        logger.info("Imported document %s", document.doc_id)

    def export_document(self) -> None:
        """Export the current document to disk."""
        if not self._current_document:
            self._view.dialogs.error("No document to export")
            return

        path = self._view.dialogs.pick_save_file(
            title="Export Document",
            suggested_name="outline.json",
        )
        if not path:
            return

        ext = path.suffix.lstrip(".").lower()
        serializer = self._serializers.get(ext)

        if not serializer:
            self._view.dialogs.error(f"Unsupported format: .{ext}")
            return

        text = serializer.dumps(self._current_document.to_payload())
        path.write_text(text, encoding="utf-8")

        self._view.status_view.set(f"Exported {path.name}")
        logger.info("Exported document %s", self._current_document.doc_id)

    # ------------------------------------------------------------------
    # Node operations
    # ------------------------------------------------------------------

    def add_node(self, parent_id: Optional[str] = None) -> None:
        """Add a node under the selected (or provided) parent."""
        if not self._current_document:
            self._view.dialogs.error("No document loaded")
            return

        parent_id = parent_id or self._selected_node_id
        if not parent_id:
            self._view.dialogs.error("No parent node selected")
            return

        title = self._view.dialogs.prompt_text(
            "Node title:",
            title="Add Node",
        )
        if not title:
            return

        resp = self._add_node(
            AddNodeRequest(
                doc_id=self._current_document.doc_id,
                parent_id=parent_id,
                title=title,
            )
        )

        # ------------------------------------------------------------------
        # MUTATION BRIDGE (intentional)
        # ------------------------------------------------------------------
        # Preserve existing DTO references (tests, GUI selections) while
        # still adopting the authoritative snapshot from the use case.
        self._current_document.root = resp.document.root

        self._reload_document(resp.document)
        self._selected_node_id = resp.new_node_id

        self._view.status_view.set("Node added")
        logger.info("Added node %s", resp.new_node_id)

    def rename_selected(self) -> None:
        """Rename the currently selected node."""
        if not self._current_document:
            self._view.dialogs.error("No document loaded")
            return

        if not self._selected_node_id:
            self._view.dialogs.error("No node selected")
            return

        new_title = self._view.dialogs.prompt_text(
            "New node title:",
            title="Rename Node",
        )
        if not new_title:
            return

        self._rename_node(
            RenameNodeRequest(
                doc_id=self._current_document.doc_id,
                node_id=self._selected_node_id,
                new_title=new_title,
            )
        )

        self._reload_document()
        self._view.status_view.set("Node renamed")

        logger.info("Renamed node %s", self._selected_node_id)

    def delete_selected(self) -> None:
        """Delete the currently selected node."""
        if not self._current_document:
            self._view.dialogs.error("No document loaded")
            return

        if not self._selected_node_id:
            self._view.dialogs.error("No node selected")
            return

        if self._selected_node_id == self._current_document.root.node_id:
            self._view.dialogs.error("Cannot delete the root node")
            return

        confirmed = self._view.dialogs.confirm(
            "Delete selected node and all its children?",
            title="Confirm Delete",
        )
        if not confirmed:
            return

        self._delete_node(
            DeleteNodeRequest(
                doc_id=self._current_document.doc_id,
                node_id=self._selected_node_id,
            )
        )

        self._selected_node_id = None
        self._reload_document()
        self._view.status_view.set("Node deleted")

        logger.info("Deleted node")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _reload_document(self, document: Optional[OutlineDocument] = None) -> None:
        """Reload and render the current document."""
        if document is None:
            resp = self._load(
                LoadDocumentRequest(doc_id=self._current_document.doc_id)
            )
            document = resp.document

        self._current_document = document
        self._view.document_view.render(document)