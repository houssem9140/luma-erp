"""Application lifecycle hooks."""

import frappe
from packaging.version import Version

ROLE_PERMISSIONS = {
	"Luma Sales User": [
		"Luma Customer",
		"Luma Item",
		"Luma Sales Order",
		"Luma Delivery Note",
		"Luma Sales Invoice",
	],
	"Luma Buying User": [
		"Luma Supplier",
		"Luma Item",
		"Luma Purchase Order",
		"Luma Purchase Receipt",
		"Luma Purchase Invoice",
	],
	"Luma Inventory User": [
		"Luma Item",
		"Luma Warehouse",
		"Luma Stock Entry",
		"Luma Stock Balance",
	],
	"Luma Accounts User": [
		"Luma Customer",
		"Luma Supplier",
		"Luma Sales Invoice",
		"Luma Purchase Invoice",
		"Luma Payment",
		"Luma Journal Entry",
	],
}


def before_install() -> None:
	"""Validate the framework version before installing Luma ERP."""
	if Version(frappe.__version__) < Version("16.0.0"):
		frappe.throw("Luma ERP requires Frappe Framework 16 or newer.")


def after_install() -> None:
	"""Create the initial Luma ERP roles and permissions."""
	setup_roles_and_permissions()
	frappe.db.commit()


def setup_roles_and_permissions() -> None:
	"""Create idempotent business roles with CRUD permissions for Luma doctypes."""
	for role, doctypes in ROLE_PERMISSIONS.items():
		if not frappe.db.exists("Role", role):
			frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1}).insert(
				ignore_permissions=True
			)

		for doctype in doctypes:
			_add_role_permission(doctype, role)


def _add_role_permission(doctype: str, role: str) -> None:
	if not frappe.db.exists("DocType", doctype):
		return

	from frappe.permissions import setup_custom_perms

	setup_custom_perms(doctype)
	existing = frappe.db.get_value(
		"Custom DocPerm",
		{"parent": doctype, "role": role, "permlevel": 0, "if_owner": 0},
		"name",
	)
	if existing:
		permission = frappe.get_doc("Custom DocPerm", existing)
	else:
		permission = frappe.get_doc(
			{
				"doctype": "Custom DocPerm",
				"parent": doctype,
				"parenttype": "DocType",
				"parentfield": "permissions",
				"role": role,
				"permlevel": 0,
			}
		)

	permission.update(
		{
			"read": 1,
			"write": 1,
			"create": 1,
			"delete": 1,
			"submit": 1,
			"cancel": 1,
			"amend": 0,
			"if_owner": 0,
		}
	)
	permission.save(ignore_permissions=True)
