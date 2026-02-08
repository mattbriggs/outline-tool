"""
Markdown serializer for outline documents.

This module implements a constrained Markdown serializer for outline payloads.
It supports a strict subset of Markdown:

- Headings represent hierarchy (using ``#`` levels)
- Node titles are encoded as heading text
- Collapsed state is encoded via HTML comments

This serializer is designed for *round-trippable structure*, not free-form
Markdown authoring. Arbitrary Markdown constructs are not supported.
"""

from __future__ import annotations

import logging
import re
from typing import Iterable, List, Tuple

from outline_tool.application.ports import Serializer

logger = logging.getLogger(__name__)


_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
_COLLAPSED_RE = re.compile(r"<!--\s*collapsed\s*-->")


class MarkdownSerializer(Serializer):
    """Markdown serializer for outline payloads.

    This serializer converts outline payload dictionaries to and from a
    constrained Markdown representation.

    Attributes
    ----------
    format_name:
        Human-readable name of the format.
    """

    format_name: str = "markdown"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def dumps(self, payload: dict) -> str:
        """Serialize an outline payload to Markdown.

        Parameters
        ----------
        payload:
            Canonical outline payload dictionary.

        Returns
        -------
        str
            Markdown text representing the outline.
        """
        logger.debug("Serializing payload to Markdown")

        lines: List[str] = []
        root = payload["root"]

        for child in root["children"]:
            self._emit_node(child, level=1, out=lines)

        text = "\n".join(lines).rstrip() + "\n"
        logger.debug("Successfully serialized payload to Markdown")
        return text

    def loads(self, text: str) -> dict:
        """Deserialize Markdown text into an outline payload.

        Parameters
        ----------
        text:
            Markdown text representing an outline.

        Returns
        -------
        dict
            Outline payload dictionary.

        Raises
        ------
        ValueError
            If the Markdown structure is invalid or unsupported.
        """
        logger.debug("Deserializing Markdown text to payload")

        lines = [line.rstrip() for line in text.splitlines() if line.strip()]
        stack: List[Tuple[int, dict]] = []

        root = {
            "node_id": "root",
            "title": "Root",
            "collapsed": False,
            "children": [],
        }

        for line in lines:
            match = _HEADING_RE.match(line)
            if not match:
                raise ValueError(f"Unsupported Markdown line: {line}")

            level = len(match.group(1))
            title = match.group(2)

            collapsed = False
            if _COLLAPSED_RE.search(title):
                collapsed = True
                title = _COLLAPSED_RE.sub("", title).strip()

            node = {
                "node_id": None,  # Assigned later by application layer
                "title": title,
                "collapsed": collapsed,
                "children": [],
            }

            while stack and stack[-1][0] >= level:
                stack.pop()

            if not stack:
                root["children"].append(node)
            else:
                stack[-1][1]["children"].append(node)

            stack.append((level, node))

        logger.debug("Successfully deserialized Markdown payload")
        return {
            "doc_id": None,
            "title": None,
            "root": root,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _emit_node(self, node: dict, level: int, out: List[str]) -> None:
        """Emit a node as Markdown.

        Parameters
        ----------
        node:
            Node payload dictionary.
        level:
            Heading depth.
        out:
            Output line buffer.
        """
        prefix = "#" * level
        title = node["title"]

        if node.get("collapsed"):
            title = f"{title} <!-- collapsed -->"

        out.append(f"{prefix} {title}")

        for child in node.get("children", []):
            self._emit_node(child, level + 1, out)