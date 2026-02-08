"""
In-memory repository implementation.

This repository is intended for:
- Unit tests
- Local prototypes
- Demo runs where persistence is not required

It implements the application-layer :class:`~outline_tool.application.ports.DocumentRepository`
port and stores documents in memory for the lifetime of the process.

Notes
-----
This repository is not durable. All data is lost when the process exits.
"""

from __future__ import annotations

import copy
import logging
from dataclasses import replace
from threading import RLock
from typing import Dict, Iterable, Optional

from outline_tool.application.ports import DocumentRepository, StoredDocument

logger = logging.getLogger(__name__)


class InMemoryDocumentRepository(DocumentRepository):
    """In-memory implementation of :class:`~outline_tool.application.ports.DocumentRepository`.

    This repository stores documents in a Python dictionary keyed by ``doc_id``.
    It is thread-safe for basic load/save operations using a re-entrant lock.

    Parameters
    ----------
    initial:
        Optional iterable of initial stored documents to pre-load into the repository.
        If duplicate ``doc_id`` values are provided, the last one wins.
    copy_on_read:
        If ``True``, :meth:`load` returns a deep copy of the stored payload to prevent
        accidental mutation of repository state by callers.
    copy_on_write:
        If ``True``, :meth:`save` deep copies the payload before storing it to prevent
        callers from mutating the stored value after saving.
    """

    def __init__(
        self,
        initial: Optional[Iterable[StoredDocument]] = None,
        *,
        copy_on_read: bool = True,
        copy_on_write: bool = True,
    ) -> None:
        self._lock = RLock()
        self._docs: Dict[str, StoredDocument] = {}
        self._copy_on_read = copy_on_read
        self._copy_on_write = copy_on_write

        if initial:
            for doc in initial:
                self.save(doc)

        logger.debug(
            "Initialized InMemoryDocumentRepository (copy_on_read=%s, copy_on_write=%s, count=%d)",
            self._copy_on_read,
            self._copy_on_write,
            len(self._docs),
        )

    def load(self, doc_id: str) -> StoredDocument:
        """Load a stored document by identifier.

        Parameters
        ----------
        doc_id:
            Document identifier.

        Returns
        -------
        StoredDocument
            Stored record containing the document payload.

        Raises
        ------
        DocumentNotFoundError
            If the requested document does not exist.
        """
        # Import here to avoid hard dependency cycles if ports evolves.
        from outline_tool.application.ports import DocumentNotFoundError

        with self._lock:
            doc = self._docs.get(doc_id)

            if doc is None:
                logger.info("Document not found (doc_id=%s)", doc_id)
                raise DocumentNotFoundError(doc_id)

            if not self._copy_on_read:
                logger.debug("Loaded document (doc_id=%s) without copying", doc_id)
                return doc

            safe_payload = copy.deepcopy(doc.payload)
            logger.debug("Loaded document (doc_id=%s) with deep copy", doc_id)
            return replace(doc, payload=safe_payload)

    def save(self, doc: StoredDocument) -> None:
        """Save (upsert) a stored document record.

        Parameters
        ----------
        doc:
            Stored document record to persist.

        Notes
        -----
        This method performs an upsert. Existing records with the same ``doc_id``
        will be overwritten.
        """
        with self._lock:
            if self._copy_on_write:
                payload = copy.deepcopy(doc.payload)
                stored = replace(doc, payload=payload)
            else:
                stored = doc

            existed = doc.doc_id in self._docs
            self._docs[doc.doc_id] = stored

            logger.info(
                "%s document (doc_id=%s)",
                "Updated" if existed else "Saved",
                doc.doc_id,
            )

    # -------------------------------------------------------------------------
    # Convenience methods (not part of the port, but useful for tests/tools)
    # -------------------------------------------------------------------------

    def exists(self, doc_id: str) -> bool:
        """Return ``True`` if a document exists.

        Parameters
        ----------
        doc_id:
            Document identifier.

        Returns
        -------
        bool
            Whether the document exists.
        """
        with self._lock:
            return doc_id in self._docs

    def count(self) -> int:
        """Return the number of stored documents.

        Returns
        -------
        int
            Count of stored documents.
        """
        with self._lock:
            return len(self._docs)

    def clear(self) -> None:
        """Remove all documents from the repository."""
        with self._lock:
            self._docs.clear()
        logger.warning("Cleared all documents from in-memory repository")