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


@frappe.whitelist(allow_guest=False)
def make_sales_invoice(delivery_note: str) -> dict:
	"""Create a draft sales invoice from the uninvoiced delivery quantity."""
	delivery = frappe.get_doc("Luma Delivery Note", delivery_note)
	if delivery.status != "Submitted":
		frappe.throw("A sales invoice requires a submitted delivery note.")

	order_rates = {}
	if delivery.sales_order:
		order = frappe.get_doc("Luma Sales Order", delivery.sales_order)
		order_rates = {item.item: item.rate for item in order.items}

	items = [
		{
			"item": item.item,
			"qty": item.qty - (item.invoiced_qty or 0),
			"rate": order_rates.get(
				item.item, frappe.db.get_value("Luma Item", item.item, "standard_rate") or 0
			),
		}
		for item in delivery.items
		if item.qty > (item.invoiced_qty or 0)
	]
	if not items:
		frappe.throw("The delivery note has no uninvoiced quantity.")

	invoice = frappe.get_doc(
		{
			"doctype": "Luma Sales Invoice",
			"customer": delivery.customer,
			"organization": delivery.organization,
			"delivery_note": delivery.name,
			"items": items,
		}
	)
	invoice.insert()
	return invoice.as_dict()


@frappe.whitelist(allow_guest=False)
def make_purchase_invoice(purchase_receipt: str) -> dict:
	"""Create a draft purchase invoice from the uninvoiced receipt quantity."""
	receipt = frappe.get_doc("Luma Purchase Receipt", purchase_receipt)
	if receipt.status != "Submitted":
		frappe.throw("A purchase invoice requires a submitted purchase receipt.")

	order_rates = {}
	if receipt.purchase_order:
		order = frappe.get_doc("Luma Purchase Order", receipt.purchase_order)
		order_rates = {item.item: item.rate for item in order.items}

	items = [
		{
			"item": item.item,
			"qty": item.qty - (item.invoiced_qty or 0),
			"rate": order_rates.get(
				item.item, frappe.db.get_value("Luma Item", item.item, "standard_rate") or 0
			),
		}
		for item in receipt.items
		if item.qty > (item.invoiced_qty or 0)
	]
	if not items:
		frappe.throw("The purchase receipt has no uninvoiced quantity.")

	invoice = frappe.get_doc(
		{
			"doctype": "Luma Purchase Invoice",
			"supplier": receipt.supplier,
			"organization": receipt.organization,
			"purchase_receipt": receipt.name,
			"items": items,
		}
	)
	invoice.insert()
	return invoice.as_dict()
