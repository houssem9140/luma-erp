"""Idempotent demonstration data for local Luma ERP environments."""

import frappe


def seed_demo_data() -> dict[str, str]:
	"""Create a small organization, master data, and warehouse for demos."""
	organization = _get_or_create(
		"Luma Organization",
		"LUMA Demo Organization",
		{
			"organization_name": "LUMA Demo Organization",
			"organization_code": "LUMADEMO",
			"default_currency": "USD",
			"timezone": "UTC",
		},
	)
	customer = _get_or_create(
		"Luma Customer",
		"LUMA Demo Customer",
		{
			"customer_name": "LUMA Demo Customer",
			"customer_code": "CUSTDEMO",
			"organization": organization,
		},
	)
	supplier = _get_or_create(
		"Luma Supplier",
		"LUMA Demo Supplier",
		{
			"supplier_name": "LUMA Demo Supplier",
			"supplier_code": "SUPPDEMO",
			"organization": organization,
		},
	)
	item = _get_or_create(
		"Luma Item",
		"DEMOITEM001",
		{
			"item_code": "DEMOITEM001",
			"item_name": "Luma Demo Item",
			"item_group": "Demo",
			"standard_rate": 100,
		},
	)
	warehouse = _get_or_create(
		"Luma Warehouse",
		"MAIN01",
		{
			"warehouse_code": "MAIN01",
			"warehouse_name": "Main Warehouse",
			"organization": organization,
		},
	)
	frappe.db.commit()
	return {
		"organization": organization,
		"customer": customer,
		"supplier": supplier,
		"item": item,
		"warehouse": warehouse,
	}


def _get_or_create(doctype: str, name: str, values: dict[str, object]) -> str:
	if frappe.db.exists(doctype, name):
		return name
	document = frappe.get_doc({"doctype": doctype, **values})
	document.insert(ignore_permissions=True)
	return document.name
