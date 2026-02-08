"""
JSON serializer for outline documents.

This module provides a JSON-based serializer implementing the
:class:`~outline_tool.application.ports.Serializer` port.

It is responsible for converting validated outline payload dictionaries
to and from JSON text. It performs no validation itself; callers are
responsible for enforcing schema contracts at appropriate boundaries.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from outline_tool.application.ports import Serializer

logger = logging.getLogger(__name__)


class JSONSerializer(Serializer):
    """JSON serializer for outline payloads.

    This serializer converts outline payload dictionaries to JSON text
    and back. It assumes payloads are already validated and canonical.

    Attributes
    ----------
    format_name:
        Human-readable name of the format.
    """

    format_name: str = "json"

    def dumps(self, payload: dict) -> str:
        """Serialize a payload dictionary to JSON text.

        Parameters
        ----------
        payload:
            Canonical outline payload dictionary.

        Returns
        -------
        str
            JSON-encoded string representation of the payload.

        Raises
        ------
        TypeError
            If the payload contains non-serializable objects.
        ValueError
            If serialization fails for any other reason.
        """
        logger.debug("Serializing payload to JSON")

        try:
            text = json.dumps(
                payload,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        except TypeError as exc:
            logger.error(
                "Failed to serialize payload to JSON: non-serializable value",
                exc_info=True,
            )
            raise
        except Exception as exc:  # pragma: no cover – defensive
            logger.error(
                "Unexpected error during JSON serialization",
                exc_info=True,
            )
            raise ValueError("Failed to serialize payload to JSON") from exc

        logger.debug("Successfully serialized payload to JSON (%d chars)", len(text))
        return text

    def loads(self, text: str) -> dict:
        """Deserialize JSON text into a payload dictionary.

        Parameters
        ----------
        text:
            JSON-encoded outline payload.

        Returns
        -------
        dict
            Parsed payload dictionary.

        Raises
        ------
        json.JSONDecodeError
            If the input text is not valid JSON.
        ValueError
            If the parsed JSON is not a dictionary.
        """
        logger.debug("Deserializing JSON text to payload")

        try:
            data: Any = json.loads(text)
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON text", exc_info=True)
            raise

        if not isinstance(data, dict):
            logger.error(
                "Deserialized JSON payload is not a dictionary (type=%s)",
                type(data).__name__,
            )
            raise ValueError("JSON payload must be an object at the top level")

        logger.debug("Successfully deserialized JSON payload")
        return data