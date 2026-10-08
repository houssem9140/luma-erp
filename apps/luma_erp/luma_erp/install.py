"""Application lifecycle hooks."""

import frappe
from packaging.version import Version


def before_install() -> None:
	"""Validate the framework version before installing Luma ERP."""
	if Version(frappe.__version__) < Version("16.0.0"):
		frappe.throw("Luma ERP requires Frappe Framework 16 or newer.")


def after_install() -> None:
	"""Create the initial Luma ERP application settings."""
	frappe.db.commit()
