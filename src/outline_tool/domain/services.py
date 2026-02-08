"""
Domain services for the outline tool.

Domain services encapsulate domain logic that:
- Does not naturally belong to a single entity
- Operates across multiple nodes
- Enforces domain-level invariants

They do NOT:
- Perform I/O
- Access repositories
- Know about schemas, DTOs, or persistence
"""

from __future__ import annotations

import logging
from typing import Iterable, Optional

from outline_tool.domain.errors import (
    DocumentInvariantError,
    InvalidNodeOperationError,
    NodeNotFoundError,
)
from outline_tool.domain.models import OutlineDocument, OutlineNode

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Node lookup
# -----------------------------------------------------------------------------


def find_node(document: OutlineDocument, node_id: str) -> OutlineNode:
    """Find a node by identifier within a document.

    Parameters
    ----------
    document:
        Outline document to search.
    node_id:
        Identifier of the node to locate.

    Returns
    -------
    OutlineNode
        The matching node.

    Raises
    ------
    NodeNotFoundError
        If no node with the given identifier exists.
    """
    logger.debug("Searching for node %s in document %s", node_id, document.doc_id)

    for node in document.walk():
        if node.node_id == node_id:
            return node

    raise NodeNotFoundError(node_id)


# -----------------------------------------------------------------------------
# Parent lookup
# -----------------------------------------------------------------------------


def find_parent(
    document: OutlineDocument,
    child_id: str,
) -> Optional[OutlineNode]:
    """Find the parent of a node.

    Parameters
    ----------
    document:
        Outline document to search.
    child_id:
        Identifier of the child node.

    Returns
    -------
    OutlineNode or None
        Parent node if found, otherwise ``None``.

    Notes
    -----
    The root node has no parent and will return ``None``.
    """
    for node in document.walk():
        for child in node.children:
            if child.node_id == child_id:
                return node
    return None


# -----------------------------------------------------------------------------
# Node movement
# -----------------------------------------------------------------------------


def move_node(
    document: OutlineDocument,
    node_id: str,
    new_parent_id: str,
    position: Optional[int] = None,
) -> None:
    """Move a node to a new parent within the document.

    Parameters
    ----------
    document:
        Outline document to modify.
    node_id:
        Identifier of the node to move.
    new_parent_id:
        Identifier of the new parent node.
    position:
        Optional index at which to insert the node under the new parent.
        If ``None``, the node is appended.

    Raises
    ------
    NodeNotFoundError
        If the node or new parent cannot be found.
    InvalidNodeOperationError
        If attempting to move the root node or create a cycle.
    DocumentInvariantError
        If the document structure becomes invalid.
    """
    logger.debug(
        "Moving node %s under parent %s (position=%s)",
        node_id,
        new_parent_id,
        position,
    )

    if document.root.node_id == node_id:
        raise InvalidNodeOperationError(
            node_id,
            "Cannot move the root node.",
        )

    node = find_node(document, node_id)
    new_parent = find_node(document, new_parent_id)
    current_parent = find_parent(document, node_id)

    if current_parent is None:
        raise DocumentInvariantError(
            document.doc_id,
            "Node has no parent; document structure is invalid.",
        )

    # Prevent cycles: new parent cannot be a descendant of node
    for descendant in node.walk():
        if descendant.node_id == new_parent.node_id:
            raise InvalidNodeOperationError(
                node_id,
                "Cannot move a node into one of its descendants.",
            )

    # Remove from current parent
    current_parent.remove_child(node_id)

    # Insert into new parent
    if position is None:
        new_parent.children.append(node)
    else:
        new_parent.children.insert(position, node)

    logger.debug(
        "Node %s successfully moved under parent %s",
        node_id,
        new_parent_id,
    )


# -----------------------------------------------------------------------------
# Structural validation
# -----------------------------------------------------------------------------


def assert_tree_integrity(document: OutlineDocument) -> None:
    """Assert basic structural invariants of the document tree.

    Parameters
    ----------
    document:
        Outline document to check.

    Raises
    ------
    DocumentInvariantError
        If a structural invariant is violated.
    """
    logger.debug("Checking tree integrity for document %s", document.doc_id)

    seen_ids: set[str] = set()

    for node in document.walk():
        if node.node_id in seen_ids:
            raise DocumentInvariantError(
                document.doc_id,
                f"Duplicate node_id detected: {node.node_id}",
            )
        seen_ids.add(node.node_id)

    if document.root.node_id not in seen_ids:
        raise DocumentInvariantError(
            document.doc_id,
            "Root node is not reachable from document traversal.",
        )