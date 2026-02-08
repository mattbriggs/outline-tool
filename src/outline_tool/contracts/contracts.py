"""
Contracts and validation helpers.

This module defines boundary-level validation logic enforced when data crosses
trust boundaries, such as:
- Import/export
- Repository persistence
- External adapters

Contracts are enforced using JSON Schema and are intentionally strict.
"""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from importlib.resources import files
from typing import Final

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

logger = logging.getLogger(__name__)

#: Name of the outline schema file bundled with the package.
_SCHEMA_FILENAME: Final[str] = "outline.schema.json"


@lru_cache(maxsize=1)
def _load_outline_schema() -> dict:
    """Load and cache the outline JSON schema.

    The schema is loaded once per process and cached to avoid repeated disk
    access during validation-heavy operations.

    Returns
    -------
    dict
        Parsed JSON Schema dictionary.

    Raises
    ------
    RuntimeError
        If the schema resource cannot be found or loaded.
    """
    try:
        schema_path = files("outline_tool.contracts") / _SCHEMA_FILENAME
        schema_text = schema_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        logger.critical(
            "Outline schema file '%s' not found in package data",
            _SCHEMA_FILENAME,
        )
        raise RuntimeError(
            "Outline schema not found. Ensure outline.schema.json is included "
            "as package data and the package is correctly installed."
        ) from exc

    try:
        schema = json.loads(schema_text)
    except json.JSONDecodeError as exc:
        logger.critical(
            "Outline schema file '%s' contains invalid JSON",
            _SCHEMA_FILENAME,
        )
        raise RuntimeError(
            "Outline schema is invalid JSON and cannot be parsed."
        ) from exc

    logger.debug("Loaded outline schema from package resources")
    return schema


@lru_cache(maxsize=1)
def _get_outline_validator() -> Draft202012Validator:
    """Create and cache the JSON Schema validator.

    Returns
    -------
    Draft202012Validator
        Validator instance for the outline schema.
    """
    schema = _load_outline_schema()
    validator = Draft202012Validator(schema)

    logger.debug("Initialized Draft202012Validator for outline schema")
    return validator


def validate_outline_payload(payload: dict) -> None:
    """Validate an outline payload against the outline JSON schema.

    This function enforces the canonical structural contract for outline
    documents. It performs no mutation and returns no value.

    Parameters
    ----------
    payload:
        Canonical outline payload dictionary to validate.

    Raises
    ------
    ValidationError
        If the payload violates the outline schema.
    RuntimeError
        If the schema cannot be loaded or initialized.
    """
    logger.debug("Validating outline payload")

    validator = _get_outline_validator()
    validator.validate(payload)

    logger.debug("Outline payload validation succeeded")