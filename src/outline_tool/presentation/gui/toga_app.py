"""
Toga GUI application for the Outline Tool.

This module provides a concrete Toga-based GUI implementation that wires
together:

- The GUI views (Toga widgets)
- The GUI controllers
- The application and domain layers
- In-memory infrastructure (repository, serializers)

This file intentionally contains *no business logic*.
All operations are delegated to controllers.
"""

from __future__ import annotations

import logging

import toga
from toga.command import Group

from outline_tool.infrastructure.repo_memory import InMemoryDocumentRepository
from outline_tool.infrastructure.serializers.json_format import JSONSerializer
from outline_tool.infrastructure.serializers.markdown import MarkdownSerializer
from outline_tool.infrastructure.serializers.opml import OPMLSerializer
from outline_tool.infrastructure.serializers.plaintext import PlainTextSerializer
from outline_tool.infrastructure.serializers.yaml_format import YAMLSerializer
from outline_tool.presentation.gui.controllers import OutlineController
from outline_tool.presentation.gui.views import MainView

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Toga Application
# -----------------------------------------------------------------------------


class OutlineTogaApp(toga.App):
    """Toga application entry point for the Outline Tool."""

    def startup(self) -> None:
        """Initialize the application."""
        logger.info("Starting Outline Tool GUI")

        # ------------------------------------------------------------------
        # Infrastructure
        # ------------------------------------------------------------------
        repo = InMemoryDocumentRepository()

        serializers = {
            "json": JSONSerializer(),
            "yaml": YAMLSerializer(),
            "yml": YAMLSerializer(),
            "md": MarkdownSerializer(),
            "markdown": MarkdownSerializer(),
            "opml": OPMLSerializer(),
            "txt": PlainTextSerializer(),
        }

        # ------------------------------------------------------------------
        # Window + View
        # ------------------------------------------------------------------
        self.main_window = toga.MainWindow(title=self.name)

        self._view = MainView(self.main_window)
        self.main_window.content = self._view.widget

        # ------------------------------------------------------------------
        # Controller
        # ------------------------------------------------------------------
        self._controller = OutlineController(
            view=self._view,
            repo=repo,
            serializers=serializers,
        )

        # Wire selection → controller
        self._view.document_view.set_selection_callback(
            self._controller.set_selected_node
        )

        # ------------------------------------------------------------------
        # Commands
        # ------------------------------------------------------------------
        self._add_commands()

        self.main_window.show()

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    def _add_commands(self) -> None:
        """Register application menu commands."""
        self.commands.add(
            toga.Command(
                self._cmd_new,
                label="New Document",
                shortcut="n",
                group=Group.FILE,
            ),
            toga.Command(
                self._cmd_import,
                label="Import…",
                shortcut="i",
                group=Group.FILE,
            ),
            toga.Command(
                self._cmd_export,
                label="Export…",
                shortcut="e",
                group=Group.FILE,
            ),
            toga.Command(
                self._cmd_save,
                label="Save",
                shortcut="s",
                group=Group.FILE,
            ),
            toga.Command(
                self._cmd_add_node,
                label="Add Node",
                shortcut="a",
                group=Group.EDIT,
            ),
            toga.Command(
                self._cmd_rename_node,
                label="Rename Node",
                shortcut="r",
                group=Group.EDIT,
            ),
            toga.Command(
                self._cmd_delete_node,
                label="Delete Node",
                shortcut="d",
                group=Group.EDIT,
            ),
        )

    # ------------------------------------------------------------------
    # Command handlers
    # ------------------------------------------------------------------

    def _cmd_new(self, widget) -> None:
        self._controller.new_document()

    def _cmd_import(self, widget) -> None:
        self._controller.import_document()

    def _cmd_export(self, widget) -> None:
        self._controller.export_document()

    def _cmd_save(self, widget) -> None:
        self._controller.save_current()

    def _cmd_add_node(self, widget) -> None:
        self._controller.add_node_under_selection()

    def _cmd_rename_node(self, widget) -> None:
        self._controller.rename_selected_node()

    def _cmd_delete_node(self, widget) -> None:
        self._controller.delete_selected_node()


# -----------------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------------


def main() -> toga.App:
    """Return the Toga application instance."""
    return OutlineTogaApp("Outline Tool", "org.example.outline")


if __name__ == "__main__":
    main().main_loop()