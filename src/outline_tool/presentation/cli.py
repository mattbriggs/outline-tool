"""
Command-line interface for the Outline Tool.

This module provides a user-facing CLI for creating, loading, modifying,
importing, and exporting outline documents.

The CLI is intentionally thin:
- All business logic lives in application use cases
- Persistence and serialization are delegated to infrastructure
- Errors are surfaced clearly and consistently
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Dict

from outline_tool.application.dto import (
    AddNodeRequest,
    CreateDocumentRequest,
    DeleteNodeRequest,
    LoadDocumentRequest,
    RenameNodeRequest,
    SaveDocumentRequest,
    ToggleCollapseRequest,
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
from outline_tool.domain.models import OutlineDocument
from outline_tool.infrastructure.repo_memory import InMemoryDocumentRepository
from outline_tool.infrastructure.serializers.json_format import JSONSerializer
from outline_tool.infrastructure.serializers.markdown import MarkdownSerializer
from outline_tool.infrastructure.serializers.opml import OPMLSerializer
from outline_tool.infrastructure.serializers.plaintext import PlainTextSerializer
from outline_tool.infrastructure.serializers.yaml_format import YAMLSerializer

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Repository (process lifetime)
# -----------------------------------------------------------------------------

_REPO = InMemoryDocumentRepository()


# -----------------------------------------------------------------------------
# Serializer registry
# -----------------------------------------------------------------------------

SERIALIZERS: Dict[str, object] = {
    "json": JSONSerializer(),
    "yaml": YAMLSerializer(),
    "yml": YAMLSerializer(),
    "markdown": MarkdownSerializer(),
    "md": MarkdownSerializer(),
    "opml": OPMLSerializer(),
    "txt": PlainTextSerializer(),
    "text": PlainTextSerializer(),
}


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def _configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(levelname)s %(name)s: %(message)s",
    )


def _get_serializer(format_name: str):
    serializer = SERIALIZERS.get(format_name.lower())
    if serializer is None:
        raise ValueError(f"Unsupported format: {format_name}")
    return serializer


# -----------------------------------------------------------------------------
# CLI commands
# -----------------------------------------------------------------------------

def cmd_new(args: argparse.Namespace) -> None:
    use_case = CreateDocument(_REPO)
    resp = use_case(CreateDocumentRequest(title=args.title))

    if not resp.ok:
        print("Failed to create document", file=sys.stderr)
        sys.exit(1)

    print(resp.doc_id)


def cmd_import(args: argparse.Namespace) -> None:
    text = Path(args.input).read_text(encoding="utf-8")

    serializer = _get_serializer(args.format)
    payload = serializer.loads(text)

    document = OutlineDocument.from_payload(payload)

    save = SaveDocument(_REPO)
    resp = save(
        SaveDocumentRequest(
            document=document,
            touch_updated=False,
        )
    )

    if not resp.ok:
        print("Failed to import document", file=sys.stderr)
        sys.exit(1)

    print(resp.saved_doc_id)


def cmd_export(args: argparse.Namespace) -> None:
    load = LoadDocument(_REPO)
    resp = load(LoadDocumentRequest(doc_id=args.doc_id))

    if not resp.ok or resp.document is None:
        print(f"Document not found: {args.doc_id}", file=sys.stderr)
        sys.exit(1)

    serializer = _get_serializer(args.format)
    text = serializer.dumps(resp.document.to_payload())

    Path(args.output).write_text(text, encoding="utf-8")


def cmd_add_node(args: argparse.Namespace) -> None:
    add = AddNode(_REPO)
    resp = add(
        AddNodeRequest(
            doc_id=args.doc_id,
            parent_id=args.parent_id,
            title=args.title,
        )
    )

    if not resp.ok:
        print("Failed to add node", file=sys.stderr)
        sys.exit(1)

    print(resp.new_node_id)


def cmd_rename_node(args: argparse.Namespace) -> None:
    rename = RenameNode(_REPO)
    resp = rename(
        RenameNodeRequest(
            doc_id=args.doc_id,
            node_id=args.node_id,
            new_title=args.title,
        )
    )

    if not resp.ok:
        print("Failed to rename node", file=sys.stderr)
        sys.exit(1)


def cmd_delete_node(args: argparse.Namespace) -> None:
    delete = DeleteNode(_REPO)
    resp = delete(
        DeleteNodeRequest(
            doc_id=args.doc_id,
            node_id=args.node_id,
        )
    )

    if not resp.ok:
        print("Failed to delete node", file=sys.stderr)
        sys.exit(1)


def cmd_toggle(args: argparse.Namespace) -> None:
    toggle = ToggleCollapse(_REPO)
    resp = toggle(
        ToggleCollapseRequest(
            doc_id=args.doc_id,
            node_id=args.node_id,
            collapsed=args.collapsed,
        )
    )

    if not resp.ok:
        print("Failed to toggle node", file=sys.stderr)
        sys.exit(1)


# -----------------------------------------------------------------------------
# Argument parsing
# -----------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="outline-tool",
        description="Offline-first outlining tool",
    )

    parser.add_argument("--verbose", action="store_true")

    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("new")
    p.add_argument("title")
    p.set_defaults(func=cmd_new)

    p = sub.add_parser("import")
    p.add_argument("input")
    p.add_argument("--format", required=True)
    p.set_defaults(func=cmd_import)

    p = sub.add_parser("export")
    p.add_argument("doc_id")
    p.add_argument("output")
    p.add_argument("--format", required=True)
    p.set_defaults(func=cmd_export)

    p = sub.add_parser("add-node")
    p.add_argument("doc_id")
    p.add_argument("parent_id")
    p.add_argument("title")
    p.set_defaults(func=cmd_add_node)

    p = sub.add_parser("rename-node")
    p.add_argument("doc_id")
    p.add_argument("node_id")
    p.add_argument("title")
    p.set_defaults(func=cmd_rename_node)

    p = sub.add_parser("delete-node")
    p.add_argument("doc_id")
    p.add_argument("node_id")
    p.set_defaults(func=cmd_delete_node)

    p = sub.add_parser("toggle")
    p.add_argument("doc_id")
    p.add_argument("node_id")
    p.add_argument("--collapsed", action="store_true")
    p.set_defaults(func=cmd_toggle)

    return parser


# -----------------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    _configure_logging(args.verbose)

    try:
        args.func(args)
    except Exception as exc:
        logger.exception("Unhandled error")
        print(str(exc), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()