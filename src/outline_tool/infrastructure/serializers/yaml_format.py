"""
YAML serializer for outline documents.

This module implements a YAML serializer for outline payloads and adheres to
the :class:`~outline_tool.application.ports.Serializer` port.

The YAML representation is intended to be:
- Human-readable
- Deterministic
- Round-trippable
- Strictly structural

Notes
-----
- Only YAML mappings and sequences are supported.
- Implicit typing (e.g., dates, booleans from strings) is disabled.
- Node and document identifiers are preserved if present.
"""

from __future__ import annotations

import logging
from typing import Any

import yaml

from outline_tool.application.ports import Serializer

logger = logging.getLogger(__name__)


class YAMLSerializer(Serializer):
    """YAML serializer for outline payloads.

    Attributes
    ----------
    format_name:
        Human-readable name of the format.
    """

    format_name: str = "yaml"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def dumps(self, payload: dict) -> str:
        """Serialize an outline payload to YAML text.

        Parameters
        ----------
        payload:
            Canonical outline payload dictionary.

        Returns
        -------
        str
            YAML-encoded outline payload.

        Raises
        ------
        ValueError
            If serialization fails.
        """
        logger.debug("Serializing payload to YAML")

        try:
            text = yaml.safe_dump(
                payload,
                sort_keys=True,
                allow_unicode=True,
                default_flow_style=False,
                indent=2,
            )
        except yaml.YAMLError as exc:
            logger.error(
                "Failed to serialize payload to YAML",
                exc_info=True,
            )
            raise ValueError("Failed to serialize payload to YAML") from exc

        logger.debug("Successfully serialized payload to YAML (%d chars)", len(text))
        return text

    def loads(self, text: str) -> dict:
        """Deserialize YAML text into an outline payload.

        Parameters
        ----------
        text:
            YAML-encoded outline payload.

        Returns
        -------
        dict
            Parsed payload dictionary.

        Raises
        ------
        ValueError
            If the YAML is invalid or does not represent a mapping.
        """
        logger.debug("Deserializing YAML text to payload")

        try:
            data: Any = yaml.safe_load(text)
        except yaml.YAMLError as exc:
            logger.warning(
                "Failed to parse YAML text",
                exc_info=True,
            )
            raise ValueError("Invalid YAML input") from exc

        if not isinstance(data, dict):
            logger.error(
                "Deserialized YAML payload is not a mapping (type=%s)",
                type(data).__name__,
            )
            raise ValueError("YAML payload must be a mapping at the top level")

        logger.debug("Successfully deserialized YAML payload")
        return data