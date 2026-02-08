"""
GUI views for the Outline Tool (MVC View layer).

This module defines presentation-only GUI components.
Views render domain state and collect user input.
They contain no business logic and know nothing about repositories.
"""

from __future__ import annotations

import logging
from typing import Callable, Optional

import toga
from toga.style import Pack
from toga.style.pack import COLUMN

from outline_tool.domain.models import OutlineDocument, OutlineNode

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Tree-based Document View
# -----------------------------------------------------------------------------


class TreeDocumentView:
    """Tree-based view of an outline document.

    This view renders an :class:`OutlineDocument` using a tree widget and
    reports selection changes via a callback registered by the controller.
    """

    def __init__(self) -> None:
        self._tree = toga.Tree(
            headings=["Outline"],
            style=Pack(flex=1, padding=8),
            on_select=self._on_select,
        )

        self._selected_node_id: Optional[str] = None
        self._on_selection_changed: Optional[
            Callable[[Optional[str]], None]
        ] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def widget(self) -> toga.Widget:
        """Return the underlying Toga widget."""
        return self._tree

    @property
    def selected_node_id(self) -> Optional[str]:
        """Return the currently selected node id."""
        return self._selected_node_id

    def set_selection_callback(
        self,
        callback: Callable[[Optional[str]], None],
    ) -> None:
        """Register a callback for selection changes.

        Parameters
        ----------
        callback:
            Function called with the selected node id, or ``None``.
        """
        self._on_selection_changed = callback

    def clear(self) -> None:
        """Clear the tree view."""
        self._tree.data.clear()
        self._selected_node_id = None

    def render(self, document: OutlineDocument) -> None:
        """Render the document into the tree widget.

        Parameters
        ----------
        document:
            The outline document to render.
        """
        previous_selection = self._selected_node_id
        self.clear()

        def build(node: OutlineNode) -> toga.TreeNode:
            tree_node = toga.TreeNode(
                node.title,
                data=node.node_id,
            )
            for child in node.children:
                tree_node.add(build(child))
            return tree_node

        root_node = build(document.root)
        self._tree.data.append(root_node)

        # Restore selection if possible
        if previous_selection:
            self._select_node_by_id(previous_selection)

        logger.debug("Rendered document %s into tree", document.doc_id)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _on_select(self, widget, node) -> None:
        if node is None:
            self._set_selected(None)
            return

        self._set_selected(node.data)

    def _set_selected(self, node_id: Optional[str]) -> None:
        self._selected_node_id = node_id
        logger.debug("Tree selection changed to %s", node_id)

        if self._on_selection_changed:
            self._on_selection_changed(node_id)

    def _select_node_by_id(self, node_id: str) -> None:
        """Attempt to reselect a node after re-rendering."""
        for tree_node in self._tree.data.walk():
            if tree_node.data == node_id:
                self._tree.selection = tree_node
                self._set_selected(node_id)
                return


# -----------------------------------------------------------------------------
# Status View
# -----------------------------------------------------------------------------


class StatusView:
    """Simple status line view."""

    def __init__(self) -> None:
        self._label = toga.Label(
            "",
            style=Pack(padding=(4, 8)),
        )

    @property
    def widget(self) -> toga.Widget:
        """Return the status label widget."""
        return self._label

    def set(self, message: str) -> None:
        """Set the status message."""
        self._label.text = message
        logger.debug("Status updated: %s", message)

    def clear(self) -> None:
        """Clear the status message."""
        self._label.text = ""


# -----------------------------------------------------------------------------
# Dialog Helpers
# -----------------------------------------------------------------------------


class Dialogs:
    """Wrapper for common dialogs."""

    def __init__(self, window: toga.MainWindow) -> None:
        self._window = window

    def info(self, message: str, *, title: str = "Info") -> None:
        self._window.info_dialog(title, message)

    def error(self, message: str, *, title: str = "Error") -> None:
        self._window.error_dialog(title, message)

    def confirm(self, message: str, *, title: str = "Confirm") -> bool:
        return self._window.confirm_dialog(title, message)

    def prompt_text(
        self,
        prompt: str,
        *,
        title: str = "Input",
        default: str = "",
    ) -> Optional[str]:
        return self._window.question_dialog(
            title,
            prompt,
            default=default,
        )

    def pick_open_file(
        self,
        *,
        title: str = "Open",
    ) -> Optional[str]:
        return self._window.open_file_dialog(title=title)

    def pick_save_file(
        self,
        *,
        title: str = "Save",
        suggested_name: str = "",
    ) -> Optional[str]:
        return self._window.save_file_dialog(
            title=title,
            suggested_filename=suggested_name,
        )


# -----------------------------------------------------------------------------
# Main View Composition
# -----------------------------------------------------------------------------


class MainView:
    """Top-level composed view for the application."""

    def __init__(self, window: toga.MainWindow) -> None:
        self.document_view = TreeDocumentView()
        self.status_view = StatusView()
        self.dialogs = Dialogs(window)

        self._container = toga.Box(
            children=[
                self.document_view.widget,
                self.status_view.widget,
            ],
            style=Pack(direction=COLUMN, flex=1),
        )

    @property
    def widget(self) -> toga.Widget:
        """Return the root view widget."""
        return self._container

    def clear(self) -> None:
        """Clear all view state."""
        self.document_view.clear()
        self.status_view.clear()