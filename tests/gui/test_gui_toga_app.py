"""
Unit tests for outline_tool.presentation.gui.toga_app.

These tests validate:
- Application startup wiring
- View, controller, and repository creation
- Command registration
- Command → controller delegation

No GUI event loop is started.
No widgets are rendered.
"""

from __future__ import annotations

import types
from unittest.mock import MagicMock

import pytest
import toga

from outline_tool.presentation.gui.toga_app import OutlineTogaApp
from outline_tool.presentation.gui.controllers import OutlineController
from outline_tool.presentation.gui.views import MainView


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture()
def app(monkeypatch: pytest.MonkeyPatch) -> OutlineTogaApp:
    """
    Create an OutlineTogaApp with GUI side effects disabled.
    """

    # Prevent real window rendering
    monkeypatch.setattr(toga.MainWindow, "show", lambda self: None)

    app = OutlineTogaApp("Outline Tool", "org.example.outline")

    return app


# -----------------------------------------------------------------------------
# Startup wiring
# -----------------------------------------------------------------------------


def test_startup_creates_window_view_and_controller(app: OutlineTogaApp):
    app.startup()

    assert hasattr(app, "main_window")
    assert isinstance(app.main_window, toga.MainWindow)

    assert hasattr(app, "_view")
    assert isinstance(app._view, MainView)

    assert hasattr(app, "_controller")
    assert isinstance(app._controller, OutlineController)

    # View is mounted into the window
    assert app.main_window.content is app._view.widget


# -----------------------------------------------------------------------------
# Command registration
# -----------------------------------------------------------------------------


def test_commands_are_registered(app: OutlineTogaApp):
    app.startup()

    command_labels = {cmd.label for cmd in app.commands}

    assert {
        "New Document",
        "Import…",
        "Export…",
        "Save",
        "Add Node",
        "Rename Node",
        "Delete Node",
    }.issubset(command_labels)


# -----------------------------------------------------------------------------
# Command delegation
# -----------------------------------------------------------------------------


def test_new_command_delegates_to_controller(app: OutlineTogaApp):
    app.startup()

    controller = app._controller
    controller.new_document = MagicMock()

    app._cmd_new(widget=None)

    controller.new_document.assert_called_once()


def test_add_node_command_delegates(app: OutlineTogaApp):
    app.startup()

    controller = app._controller
    controller.add_node_under_selection = MagicMock()

    app._cmd_add_node(widget=None)

    controller.add_node_under_selection.assert_called_once()


def test_rename_command_delegates(app: OutlineTogaApp):
    app.startup()

    controller = app._controller
    controller.rename_selected_node = MagicMock()

    app._cmd_rename_node(widget=None)

    controller.rename_selected_node.assert_called_once()


def test_delete_command_delegates(app: OutlineTogaApp):
    app.startup()

    controller = app._controller
    controller.delete_selected_node = MagicMock()

    app._cmd_delete_node(widget=None)

    controller.delete_selected_node.assert_called_once()