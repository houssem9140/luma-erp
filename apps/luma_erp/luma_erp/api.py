"""Public API endpoints for Luma ERP."""

import frappe


@frappe.whitelist(allow_guest=False)
def health() -> dict[str, str]:
	"""Return a small authenticated health response for monitoring."""
	return {
		"application": "luma_erp",
		"status": "ok",
		"version": "0.1.0",
	}
