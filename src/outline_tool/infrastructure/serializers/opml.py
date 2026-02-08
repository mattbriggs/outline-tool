"""
OPML serializer for outline documents.

This module implements an OPML serializer for outline payloads and adheres to
the :class:`~outline_tool.application.ports.Serializer` port.

Supported OPML subset
---------------------
- OPML 2.0 structure: ``<opml version="2.0"><head>...</head><body>...</body></opml>``
- Nodes represented as nested ``<outline>`` elements
- Node titles read from ``text`` (preferred) or ``title`` attributes
- Collapsed state read from common attributes:
  - ``isCollapsed="true"``
  - ``collapsed="true"``
- Optional node identifiers:
  - read from ``id`` attribute if present

Notes
-----
This serializer is intentionally strict and structural. It does not attempt to
preserve arbitrary OPML extensions or non-outline content.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from xml.etree import ElementTree as ET

from outline_tool.application.ports import Serializer

logger = logging.getLogger(__name__)


def _is_truthy(value: Optional[str]) -> bool:
    """Return True if the given string value represents a truthy value.

    Parameters
    ----------
    value:
        String to interpret.

    Returns
    -------
    bool
        True if the value is a recognized truthy token.
    """
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _node_title_from_attrib(attrib: Dict[str, str]) -> str:
    """Extract the node title from OPML outline attributes.

    Parameters
    ----------
    attrib:
        Element attributes.

    Returns
    -------
    str
        Extracted title.

    Raises
    ------
    ValueError
        If no title attribute is found.
    """
    title = attrib.get("text") or attrib.get("title")
    if not title:
        raise ValueError("OPML outline element is missing required 'text' attribute")
    return title


class OPMLSerializer(Serializer):
    """OPML serializer for outline payloads.

    Attributes
    ----------
    format_name:
        Human-readable name of the format.
    """

    format_name: str = "opml"

    def dumps(self, payload: dict) -> str:
        """Serialize an outline payload to OPML text.

        Parameters
        ----------
        payload:
            Canonical outline payload dictionary.

        Returns
        -------
        str
            OPML XML text.
        """
        logger.debug("Serializing payload to OPML")

        opml = ET.Element("opml", {"version": "2.0"})
        head = ET.SubElement(opml, "head")
        body = ET.SubElement(opml, "body")

        title = payload.get("title") or "Outline"
        ET.SubElement(head, "title").text = str(title)

        root = payload["root"]
        for child in root.get("children", []):
            body.append(self._node_to_outline_element(child))

        # Pretty-print when available (Python 3.9+).
        try:
            ET.indent(opml, space="  ")  # type: ignore[attr-defined]
        except Exception:  # pragma: no cover
            # Indentation is cosmetic; ignore failures.
            pass

        xml_bytes = ET.tostring(opml, encoding="utf-8", xml_declaration=True)
        text = xml_bytes.decode("utf-8")

        logger.debug("Successfully serialized payload to OPML (%d chars)", len(text))
        return text

    def loads(self, text: str) -> dict:
        """Deserialize OPML text into an outline payload.

        Parameters
        ----------
        text:
            OPML XML content.

        Returns
        -------
        dict
            Outline payload dictionary.

        Raises
        ------
        ValueError
            If the OPML is malformed or unsupported.
        """
        logger.debug("Deserializing OPML text to payload")

        try:
            root_el = ET.fromstring(text)
        except ET.ParseError as exc:
            logger.warning("Failed to parse OPML XML", exc_info=True)
            raise ValueError("Invalid OPML XML") from exc

        if root_el.tag != "opml":
            raise ValueError("Invalid OPML: root element must be <opml>")

        body_el = root_el.find("body")
        if body_el is None:
            raise ValueError("Invalid OPML: missing <body> element")

        head_el = root_el.find("head")
        title_text = None
        if head_el is not None:
            title_node = head_el.find("title")
            if title_node is not None and title_node.text:
                title_text = title_node.text.strip()

        outline_root: Dict[str, Any] = {
            "node_id": "root",
            "title": "Root",
            "collapsed": False,
            "children": [],
        }

        for child in list(body_el):
            if child.tag != "outline":
                # Strict: OPML body should contain outline nodes.
                raise ValueError(f"Unsupported OPML element in <body>: <{child.tag}>")
            outline_root["children"].append(self._outline_element_to_node(child))

        payload: Dict[str, Any] = {
            # IDs are not reliably stable across OPML tools. We leave them unset.
            "doc_id": None,
            "title": title_text,
            "root": outline_root,
        }

        logger.debug("Successfully deserialized OPML payload")
        return payload

    def _node_to_outline_element(self, node: dict) -> ET.Element:
        """Convert a payload node dictionary into an OPML ``<outline>`` element.

        Parameters
        ----------
        node:
            Node payload dictionary.

        Returns
        -------
        xml.etree.ElementTree.Element
            OPML outline element.
        """
        attrib: Dict[str, str] = {"text": str(node.get("title", ""))}

        node_id = node.get("node_id")
        if node_id:
            attrib["id"] = str(node_id)

        if node.get("collapsed"):
            attrib["isCollapsed"] = "true"

        el = ET.Element("outline", attrib)

        for child in node.get("children", []):
            el.append(self._node_to_outline_element(child))

        return el

    def _outline_element_to_node(self, el: ET.Element) -> dict:
        """Convert an OPML ``<outline>`` element into a payload node dictionary.

        Parameters
        ----------
        el:
            OPML outline element.

        Returns
        -------
        dict
            Node payload dictionary.

        Raises
        ------
        ValueError
            If the outline element is missing required attributes.
        """
        title = _node_title_from_attrib(el.attrib)

        collapsed = _is_truthy(el.attrib.get("isCollapsed")) or _is_truthy(el.attrib.get("collapsed"))
        node_id = el.attrib.get("id")

        node: Dict[str, Any] = {
            "node_id": node_id or None,
            "title": title,
            "collapsed": bool(collapsed),
            "children": [],
        }

        for child in list(el):
            if child.tag != "outline":
                raise ValueError(f"Unsupported OPML element inside <outline>: <{child.tag}>")
            node["children"].append(self._outline_element_to_node(child))

        return node