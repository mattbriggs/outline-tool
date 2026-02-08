"""
Unit tests for outline_tool.presentation.gui.views.

These tests verify:
- TreeDocumentView rendering and selection behavior
- StatusView state updates
- Dialog delegation to Toga MainWindow
- MainView composition and clearing

No GUI loop is started.
No real dialogs are shown.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
import toga

from outline_tool.domain.models import OutlineDocument, OutlineNode
from outline_tool.presentation.gui.views import (
    TreeDocumentView,
    StatusView,
    Dialogs,
    MainView,
)


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture()
def simple_document() -> OutlineDocument:
    root = OutlineNode(node_id="root", title="Root")
    child = OutlineNode(node_id="child", title="Child")
    root.children.append(child)

    return OutlineDocument(
        doc_id="doc1",
        title="Test Doc",
        root=root,
    )


@pytest.fixture()
def fake_window() -> toga.MainWindow:
    window = MagicMock(spec=toga.MainWindow)

    window.info_dialog.return_value = None
    window.error_dialog.return_value = None
    window.confirm_dialog.return_value = True
    window.question_dialog.return_value = "input"
    window.open_file_dialog.return_value = "/tmp/input.txt"
    window.save_file_dialog.return_value = "/tmp/output.txt"

    return window


# -----------------------------------------------------------------------------
# TreeDocumentView
# -----------------------------------------------------------------------------


def test_tree_view_renders_document(simple_document: OutlineDocument):
    view = TreeDocumentView()

    view.render(simple_document)

    # One root node in the tree
    assert len(view.widget.data) == 1

    root_node = view.widget.data[0]
    assert root_node.text == "Root"
    assert root_node.data == "root"

    # One child
    assert len(root_node.children) == 1
    assert root_node.children[0].text == "Child"


def test_tree_view_clear_resets_state(simple_document: OutlineDocument):
    view = TreeDocumentView()
    view.render(simple_document)

    view.clear()

    assert len(view.widget.data) == 0
    assert view.selected_node_id is None


def test_tree_view_selection_callback_is_called(simple_document: OutlineDocument):
    view = TreeDocumentView()
    callback = MagicMock()

    view.set_selection_callback(callback)
    view.render(simple_document)

    # Simulate user selecting the root
    root_node = view.widget.data[0]
    view._on_select(view.widget, root_node)

    assert view.selected_node_id == "root"
    callback.assert_called_once_with("root")


def test_tree_view_selection_none_clears_selection():
    view = TreeDocumentView()
    callback = MagicMock()

    view.set_selection_callback(callback)

    view._on_select(view.widget, None)

    assert view.selected_node_id is None
    callback.assert_called_once_with(None)


def test_tree_view_restores_selection_after_render(simple_document: OutlineDocument):
    view = TreeDocumentView()
    callback = MagicMock()

    view.set_selection_callback(callback)
    view.render(simple_document)

    # Select child
    child_node = view.widget.data[0].children[0]
    view._on_select(view.widget, child_node)

    assert view.selected_node_id == "child"

    # Re-render should restore selection
    view.render(simple_document)

    assert view.selected_node_id == "child"


# -----------------------------------------------------------------------------
# StatusView
# -----------------------------------------------------------------------------


def test_status_view_set_and_clear():
    status = StatusView()

    status.set("Hello")
    assert status.widget.text == "Hello"

    status.clear()
    assert status.widget.text == ""


# -----------------------------------------------------------------------------
# Dialogs
# -----------------------------------------------------------------------------


def test_dialogs_delegate_to_window(fake_window: toga.MainWindow):
    dialogs = Dialogs(fake_window)

    dialogs.info("info")
    fake_window.info_dialog.assert_called_once_with("Info", "info")

    dialogs.error("error")
    fake_window.error_dialog.assert_called_once_with("Error", "error")

    assert dialogs.confirm("confirm") is True
    fake_window.confirm_dialog.assert_called_once_with("Confirm", "confirm")

    result = dialogs.prompt_text("prompt", default="x")
    assert result == "input"
    fake_window.question_dialog.assert_called_once()

    open_path = dialogs.pick_open_file()
    assert open_path == "/tmp/input.txt"

    save_path = dialogs.pick_save_file(suggested_name="file.txt")
    assert save_path == "/tmp/output.txt"


# -----------------------------------------------------------------------------
# MainView
# -----------------------------------------------------------------------------


def test_main_view_composition(fake_window: toga.MainWindow):
    view = MainView(fake_window)

    assert view.document_view is not None
    assert view.status_view is not None
    assert view.dialogs is not None

    # Container has document + status widgets
    children = view.widget.children
    assert len(children) == 2


def test_main_view_clear_calls_children(fake_window: toga.MainWindow):
    view = MainView(fake_window)

    view.document_view.clear = MagicMock()
    view.status_view.clear = MagicMock()

    view.clear()

    view.document_view.clear.assert_called_once()
    view.status_view.clear.assert_called_once()