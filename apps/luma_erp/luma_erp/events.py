"""Shared document event handlers."""

from typing import Any


def validate_document(document: Any, event: str | None = None) -> None:
	"""Extension point for cross-domain validation.

	This handler intentionally does not alter ERPNext documents yet. Domain
	rules will be added in their owning Luma module as they are implemented.
	"""
	return None
