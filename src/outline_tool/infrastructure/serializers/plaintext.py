"""
Plain-text serializer for outline documents.

This module implements a constrained plain-text serializer for outline payloads.
It is designed for maximum portability and human readability while preserving
outline structure.

Supported plain-text format
----------------------------
- One node per line
- Hierarchy expressed via indentation (2 spaces per level)
- Collapsed state expressed with a trailing marker: ``[collapsed]``

Example
-------
Root children are emitted without a root line::

  Chapter 1
    Section 1.1
    Section 1.2 [collapsed]
      Detail A
  Chapter 2

Notes
-----
This serializer is intentionally strict:
- Indentation must be consistent (2 spaces per level)
- Tabs are not allowed
- Mixed indentation is rejected
- Node and document identifiers are not preserved
"""

from __future__ import annotations

import logging
import re
from typing import List, Tuple

from outline_tool.application.ports import Serializer

logger = logging.getLogger(__name__)

_INDENT = "  "  # two spaces
_COLLAPSED_SUFFIX = " [collapsed]"
_COLLAPSED_RE = re.compile(r"\s+\[collapsed\]\s*$")


class PlainTextSerializer(Serializer):
    """Plain-text serializer for outline payloads.

    Attributes
    ----------
    format_name:
        Human-readable name of the format.
    """

    format_name: str = "text"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def dumps(self, payload: dict) -> str:
        """Serialize an outline payload to plain text.

        Parameters
        ----------
        payload:
            Canonical outline payload dictionary.

        Returns
        -------
        str
            Plain-text outline representation.
        """
        logger.debug("Serializing payload to plain text")

        lines: List[str] = []
        root = payload["root"]

        for child in root.get("children", []):
            self._emit_node(child, level=0, out=lines)

        text = "\n".join(lines).rstrip() + "\n"
        logger.debug("Successfully serialized payload to plain text")
        return text

    def loads(self, text: str) -> dict:
        """Deserialize plain text into an outline payload.

        Parameters
        ----------
        text:
            Plain-text outline.

        Returns
        -------
        dict
            Outline payload dictionary.

        Raises
        ------
        ValueError
            If indentation or structure is invalid.
        """
        logger.debug("Deserializing plain text to payload")

        lines = [line.rstrip("\n") for line in text.splitlines() if line.strip()]
        stack: List[Tuple[int, dict]] = []

        root = {
            "node_id": "root",
            "title": "Root",
            "collapsed": False,
            "children": [],
        }

        for raw_line in lines:
            if "\t" in raw_line:
                raise ValueError("Tabs are not allowed for indentation")

            indent_level = self._count_indent(raw_line)
            title = raw_line.lstrip(" ")

            collapsed = False
            if _COLLAPSED_RE.search(title):
                collapsed = True
                title = _COLLAPSED_RE.sub("", title).strip()

            node = {
                "node_id": None,
                "title": title,
                "collapsed": collapsed,
                "children": [],
            }

            while stack and stack[-1][0] >= indent_level:
                stack.pop()

            if not stack:
                root["children"].append(node)
            else:
                stack[-1][1]["children"].append(node)

            stack.append((indent_level, node))

        logger.debug("Successfully deserialized plain-text payload")
        return {
            "doc_id": None,
            "title": None,
            "root": root,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _emit_node(self, node: dict, level: int, out: List[str]) -> None:
        """Emit a node as a plain-text line.

        Parameters
        ----------
        node:
            Node payload dictionary.
        level:
            Indentation level.
        out:
            Output line buffer.
        """
        indent = _INDENT * level
        title = node["title"]

        if node.get("collapsed"):
            title = f"{title}{_COLLAPSED_SUFFIX}"

        out.append(f"{indent}{title}")

        for child in node.get("children", []):
            self._emit_node(child, level + 1, out)

    def _count_indent(self, line: str) -> int:
        """Count indentation levels for a line.

        Parameters
        ----------
        line:
            Raw input line.

        Returns
        -------
        int
            Indentation depth.

        Raises
        ------
        ValueError
            If indentation is not a multiple of the indent unit.
        """
        spaces = len(line) - len(line.lstrip(" "))
        if spaces % len(_INDENT) != 0:
            raise ValueError(
                "Invalid indentation: must be multiples of two spaces"
            )
        return spaces // len(_INDENT)