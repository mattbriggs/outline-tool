"""
Domain models for the outline tool.

This module contains pure domain logic for representing and manipulating
outline documents and nodes. It deliberately avoids any concerns related to
persistence, serialization backends, user interfaces, or external frameworks.

The domain layer is responsible only for:
- Expressing valid state
- Enforcing local invariants
- Providing behavior intrinsic to the model
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Iterable, Iterator
from uuid import uuid4

logger = logging.getLogger(__name__)


def _new_id() -> str:
    """Generate a new stable identifier.

    Returns
    -------
    str
        A UUID4 string suitable for identifying domain entities.
    """
    return str(uuid4())


@dataclass(slots=True)
class OutlineNode:
    """A node in an outline tree.

    An :class:`OutlineNode` represents a single structural element in an
    outline. Nodes form a recursive tree structure via their ``children``.

    Parameters
    ----------
    title:
        Human-readable title of the node.
    node_id:
        Stable unique identifier for the node.
    collapsed:
        Whether the node is collapsed in presentation contexts.
    children:
        Ordered list of child nodes.
    """

    title: str
    node_id: str = field(default_factory=_new_id)
    collapsed: bool = False
    children: list["OutlineNode"] = field(default_factory=list)

    def add_child(self, title: str) -> OutlineNode:
        """Create and append a child node.

        Parameters
        ----------
        title:
            Title of the child node.

        Returns
        -------
        OutlineNode
            The newly created child node.
        """
        child = OutlineNode(title=title)
        self.children.append(child)

        logger.debug(
            "Added child node %s to parent node %s",
            child.node_id,
            self.node_id,
        )
        return child

    def remove_child(self, node_id: str) -> OutlineNode:
        """Remove and return a direct child node by identifier.

        Parameters
        ----------
        node_id:
            Identifier of the child node to remove.

        Returns
        -------
        OutlineNode
            The removed child node.

        Raises
        ------
        KeyError
            If no direct child with the given identifier exists.
        """
        for index, child in enumerate(self.children):
            if child.node_id == node_id:
                removed = self.children.pop(index)
                logger.debug(
                    "Removed child node %s from parent node %s",
                    node_id,
                    self.node_id,
                )
                return removed

        raise KeyError(f"Child node not found: {node_id}")

    def walk(self) -> Iterator[OutlineNode]:
        """Traverse the node tree in depth-first order.

        Yields
        ------
        OutlineNode
            This node followed by all descendant nodes.
        """
        yield self
        for child in self.children:
            yield from child.walk()

    def to_payload(self) -> dict:
        """Convert the node and its subtree to a payload dictionary.

        Returns
        -------
        dict
            Canonical node payload.
        """
        return {
            "node_id": self.node_id,
            "title": self.title,
            "collapsed": self.collapsed,
            "children": [child.to_payload() for child in self.children],
        }


@dataclass(slots=True)
class OutlineDocument:
    """A complete outline document.

    An :class:`OutlineDocument` is the aggregate root for the outline domain.
    It owns the root node and defines the identity boundary for the document.

    Parameters
    ----------
    title:
        Human-readable title of the document.
    root:
        Root node of the outline tree.
    doc_id:
        Stable unique identifier for the document.
    """

    title: str
    root: OutlineNode = field(
        default_factory=lambda: OutlineNode(
            title="Root",
            node_id="root",
        )
    )
    doc_id: str = field(default_factory=_new_id)

    def walk(self) -> Iterable[OutlineNode]:
        """Traverse all nodes in the document.

        Returns
        -------
        Iterable[OutlineNode]
            An iterable yielding all nodes in depth-first order.
        """
        return self.root.walk()

    def to_payload(self) -> dict:
        """Convert the document to a canonical payload dictionary.

        Returns
        -------
        dict
            Outline payload suitable for validation and persistence.
        """
        return {
            "doc_id": self.doc_id,
            "title": self.title,
            "root": self.root.to_payload(),
        }

    @classmethod
    def from_payload(cls, payload: dict) -> OutlineDocument:
        """Reconstruct a document from a validated payload.

        This method assumes the payload has already been validated against
        the outline schema. It performs no I/O and no validation.

        Parameters
        ----------
        payload:
            Canonical outline payload dictionary.

        Returns
        -------
        OutlineDocument
            Reconstructed domain document.
        """

        def build_node(data: dict) -> OutlineNode:
            node = OutlineNode(
                title=data["title"],
                node_id=data["node_id"],
                collapsed=data["collapsed"],
                children=[],
            )
            node.children.extend(build_node(child) for child in data["children"])
            return node

        document = cls(
            title=payload["title"],
            root=build_node(payload["root"]),
            doc_id=payload["doc_id"],
        )

        logger.debug("Reconstructed document %s from payload", document.doc_id)
        return document