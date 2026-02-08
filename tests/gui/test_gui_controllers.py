"""
Unit tests for outline_tool.presentation.gui.controllers.

These tests validate controller behavior in isolation from:
- GUI widgets (Toga)
- Filesystem
- Serialization formats

The controller is exercised using test doubles for the view.
"""

from __future__ import annotations

import pytest

from outline_tool.presentation.gui.controllers import OutlineController
from outline_tool.infrastructure.repo_memory import InMemoryDocumentRepository
from outline_tool.infrastructure.serializers.json_format import JSONSerializer


# -----------------------------------------------------------------------------
# Fake Views (Test Doubles)
# -----------------------------------------------------------------------------


class FakeDocumentView:
    def __init__(self) -> None:
        self.rendered_document = None
        self._selection_callback = None

    def render(self, document) -> None:
        self.rendered_document = document

    def clear(self) -> None:
        self.rendered_document = None

    def set_selection_callback(self, callback) -> None:
        self._selection_callback = callback

    def simulate_select(self, node_id: str | None) -> None:
        if self._selection_callback:
            self._selection_callback(node_id)


class FakeStatusView:
    def __init__(self) -> None:
        self.message = None

    def set(self, message: str) -> None:
        self.message = message

    def clear(self) -> None:
        self.message = None


class FakeDialogs:
    def __init__(self) -> None:
        self.last_error = None
        self.last_info = None
        self.prompt_response = None
        self.confirm_response = True

    def info(self, message: str, *, title: str = "Info") -> None:
        self.last_info = message

    def error(self, message: str, *, title: str = "Error") -> None:
        self.last_error = message

    def confirm(self, message: str, *, title: str = "Confirm") -> bool:
        return self.confirm_response

    def prompt_text(self, prompt: str, *, title: str = "Input", default: str = ""):
        return self.prompt_response


class FakeMainView:
    def __init__(self) -> None:
        self.document_view = FakeDocumentView()
        self.status_view = FakeStatusView()
        self.dialogs = FakeDialogs()


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture()
def controller() -> OutlineController:
    repo = InMemoryDocumentRepository()
    serializers = {"json": JSONSerializer()}
    view = FakeMainView()

    return OutlineController(
        view=view,
        repo=repo,
        serializers=serializers,
    )


# -----------------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------------


def test_new_document_creates_and_renders(controller: OutlineController):
    view = controller._view
    view.dialogs.prompt_response = "My Doc"

    controller.new_document()

    assert controller.current_document is not None
    assert controller.current_document.title == "My Doc"
    assert view.document_view.rendered_document is not None
    assert view.status_view.message == "New document created"


def test_add_node_under_selection(controller: OutlineController):
    view = controller._view
    view.dialogs.prompt_response = "Doc"
    controller.new_document()

    doc = controller.current_document
    root_id = doc.root.node_id

    view.document_view.simulate_select(root_id)

    view.dialogs.prompt_response = "Child"
    controller.add_node()

    assert len(doc.root.children) == 1
    assert doc.root.children[0].title == "Child"


def test_rename_selected_node(controller: OutlineController):
    view = controller._view
    view.dialogs.prompt_response = "Doc"
    controller.new_document()

    view.document_view.simulate_select(
        controller.current_document.root.node_id
    )

    view.dialogs.prompt_response = "Renamed Root"
    controller.rename_selected()

    assert controller.current_document.root.title == "Renamed Root"


def test_delete_selected_node(controller: OutlineController):
    view = controller._view
    view.dialogs.prompt_response = "Doc"
    controller.new_document()

    view.document_view.simulate_select(
        controller.current_document.root.node_id
    )

    controller.delete_selected()

    assert view.dialogs.last_error is not None
    assert "root" in view.dialogs.last_error.lower()


def test_rename_without_selection_is_rejected(controller: OutlineController):
    view = controller._view
    view.dialogs.prompt_response = "Doc"
    controller.new_document()

    view.document_view.simulate_select(None)

    controller.rename_selected()

    assert view.dialogs.last_error is not None
    assert "select" in view.dialogs.last_error.lower()


def test_delete_without_selection_is_rejected(controller: OutlineController):
    view = controller._view
    view.dialogs.prompt_response = "Doc"
    controller.new_document()

    view.document_view.simulate_select(None)

    controller.delete_selected()

    assert view.dialogs.last_error is not None
    assert "select" in view.dialogs.last_error.lower()