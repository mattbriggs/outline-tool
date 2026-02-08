"""
Serializer base interface.

Defines the contract for outline serializers used by the application.

Serializers are responsible for converting between:

- Canonical outline payload dictionaries
- External textual representations (JSON, YAML, Markdown, OPML, etc.)

This module intentionally contains *no concrete logic*.
It defines the interface boundary between application code and
format-specific infrastructure adapters.
"""

from __future__ import annotations

import logging
from typing import Protocol, runtime_checkable

logger = logging.getLogger(__name__)


@runtime_checkable
class Serializer(Protocol):
    """Protocol for outline serializers.

    All serializers must be able to:

    - Serialize a validated outline payload to text
    - Deserialize text into a payload dictionary

    Implementations are expected to raise ``ValueError`` or
    format-specific exceptions when serialization or parsing fails.
    """

    #: Short, stable format name (e.g. ``"json"``, ``"yaml"``, ``"markdown"``)
    format_name: str

    def dumps(self, payload: dict) -> str:
        """Serialize an outline payload to text.

        Parameters
        ----------
        payload:
            Canonical outline payload dictionary. This payload is assumed
            to have already passed schema validation.

        Returns
        -------
        str
            Serialized textual representation of the payload.

        Raises
        ------
        ValueError
            If the payload cannot be serialized.
        """
        ...

    def loads(self, text: str) -> dict:
        """Deserialize text into an outline payload.

        Parameters
        ----------
        text:
            Textual representation of an outline document.

        Returns
        -------
        dict
            Parsed outline payload dictionary.

        Raises
        ------
        ValueError
            If the text cannot be parsed or does not represent
            a valid outline payload.
        """
        ...