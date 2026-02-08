"""
Unit tests for outline_tool.presentation.cli.

These tests validate:
- Argument parsing and command dispatch
- Happy-path CLI behavior
- User-facing output and exit codes
- Error handling for invalid operations

The CLI is tested as a thin presentation layer.
Business logic is assumed to be covered by application-layer tests.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from outline_tool.presentation import cli


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------


def run_cli(
    monkeypatch: pytest.MonkeyPatch,
    args: list[str],
) -> tuple[int, str, str]:
    """Run the CLI with patched argv and capture output.

    Returns
    -------
    tuple[int, str, str]
        Exit code, stdout, stderr.
    """
    stdout = []
    stderr = []

    def fake_exit(code: int = 0) -> None:
        raise SystemExit(code)

    monkeypatch.setattr(sys, "argv", ["outline-tool"] + args)
    monkeypatch.setattr(sys, "exit", fake_exit)

    try:
        cli.main()
    except SystemExit as exc:
        code = int(exc.code)
    else:
        code = 0

    return code, sys.stdout.getvalue(), sys.stderr.getvalue()


# -----------------------------------------------------------------------------
# Tests: basic command wiring
# -----------------------------------------------------------------------------


def test_cli_new_creates_document(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture):
    monkeypatch.setattr(sys, "argv", ["outline-tool", "new", "My Doc"])

    cli.main()

    captured = capsys.readouterr()
    assert captured.out.strip() != ""
    assert captured.err == ""


def test_cli_new_missing_title_fails(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(sys, "argv", ["outline-tool", "new"])

    with pytest.raises(SystemExit):
        cli.main()


# -----------------------------------------------------------------------------
# Tests: export / import
# -----------------------------------------------------------------------------


def test_cli_export_fails_for_missing_document(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture,
):
    out_file = tmp_path / "out.json"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "outline-tool",
            "export",
            "missing-doc",
            str(out_file),
            "--format",
            "json",
        ],
    )

    with pytest.raises(SystemExit):
        cli.main()

    captured = capsys.readouterr()
    assert "Document not found" in captured.err


def test_cli_import_and_export_round_trip(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture,
):
    input_file = tmp_path / "doc.json"
    output_file = tmp_path / "exported.json"

    input_file.write_text(
        """
{
  "doc_id": "doc-1",
  "title": "Imported",
  "root": {
    "node_id": "root",
    "title": "Root",
    "collapsed": false,
    "children": []
  }
}
""",
        encoding="utf-8",
    )

    # import
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "outline-tool",
            "import",
            str(input_file),
            "--format",
            "json",
        ],
    )

    cli.main()
    captured = capsys.readouterr()
    doc_id = captured.out.strip()
    assert doc_id != ""

    # export
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "outline-tool",
            "export",
            doc_id,
            str(output_file),
            "--format",
            "json",
        ],
    )

    cli.main()
    assert output_file.exists()


# -----------------------------------------------------------------------------
# Tests: node operations
# -----------------------------------------------------------------------------


def test_cli_add_node_flow(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
):
    # create
    monkeypatch.setattr(sys, "argv", ["outline-tool", "new", "Doc"])
    cli.main()
    doc_id = capsys.readouterr().out.strip()

    # add node
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "outline-tool",
            "add-node",
            doc_id,
            "root",
            "Child",
        ],
    )

    cli.main()
    captured = capsys.readouterr()
    assert captured.out.strip() != ""


def test_cli_rename_missing_node_fails(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "outline-tool",
            "rename-node",
            "missing-doc",
            "missing-node",
            "New Title",
        ],
    )

    with pytest.raises(SystemExit):
        cli.main()


def test_cli_delete_missing_node_fails(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "outline-tool",
            "delete-node",
            "missing-doc",
            "missing-node",
        ],
    )

    with pytest.raises(SystemExit):
        cli.main()


# -----------------------------------------------------------------------------
# Tests: toggle
# -----------------------------------------------------------------------------


def test_cli_toggle_missing_node_fails(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "outline-tool",
            "toggle",
            "missing-doc",
            "missing-node",
        ],
    )

    with pytest.raises(SystemExit):
        cli.main()


# -----------------------------------------------------------------------------
# Tests: unsupported format
# -----------------------------------------------------------------------------


def test_cli_rejects_unknown_format(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "outline-tool",
            "export",
            "doc-id",
            "out.foo",
            "--format",
            "nonsense",
        ],
    )

    with pytest.raises(SystemExit):
        cli.main()