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


@frappe.whitelist(allow_guest=False)
def get_invoice_summary(organization: str | None = None) -> dict:
	"""Return invoice counts and amounts for the authenticated dashboard user."""
	filters = {"organization": organization} if organization else {}
	return {
		"sales": _summarize_invoices("Luma Sales Invoice", filters),
		"purchases": _summarize_invoices("Luma Purchase Invoice", filters),
	}


def _summarize_invoices(doctype: str, filters: dict[str, str]) -> dict:
	invoices = frappe.get_list(
		doctype,
		filters=filters,
		fields=["status", "total_amount", "outstanding_amount"],
		limit_page_length=0,
	)
	summary = {
		"count": len(invoices),
		"draft": 0,
		"submitted": 0,
		"cancelled": 0,
		"total_amount": 0.0,
		"outstanding_amount": 0.0,
	}
	for invoice in invoices:
		status = (invoice.status or "").lower()
		if status in summary:
			summary[status] += 1
		summary["total_amount"] += float(invoice.total_amount or 0)
		summary["outstanding_amount"] += float(invoice.outstanding_amount or 0)
	return summary


@frappe.whitelist(allow_guest=False)
def get_ledger(organization: str, account: str | None = None, limit: int = 100) -> dict:
	"""Return submitted journal lines and totals for one organization."""
	if limit < 1 or limit > 500:
		frappe.throw("Ledger limit must be between 1 and 500.")

	filters = {"organization": organization, "docstatus": 1}
	entries = frappe.get_list(
		"Luma Journal Entry",
		filters=filters,
		fields=["name", "posting_date", "currency", "reference_type", "reference_name"],
		order_by="posting_date desc, creation desc",
		limit=limit,
	)
	lines = []
	total_debit = 0.0
	total_credit = 0.0
	for entry in entries:
		journal = frappe.get_doc("Luma Journal Entry", entry.name)
		for line in journal.accounts:
			if account and line.account != account:
				continue
			debit = float(line.debit or 0)
			credit = float(line.credit or 0)
			lines.append(
				{
					"journal_entry": entry.name,
					"posting_date": entry.posting_date,
					"account": line.account,
					"debit": debit,
					"credit": credit,
					"currency": entry.currency,
					"reference_type": entry.reference_type,
					"reference_name": entry.reference_name,
				}
			)
			total_debit += debit
			total_credit += credit

	return {
		"lines": lines,
		"total_debit": total_debit,
		"total_credit": total_credit,
		"balanced": total_debit == total_credit,
	}


@frappe.whitelist(allow_guest=False)
def get_operations_summary(organization: str) -> dict:
	"""Return inventory and order status metrics for one organization."""
	balances = frappe.get_list(
		"Luma Stock Balance",
		filters={"organization": organization},
		fields=["item", "warehouse", "quantity"],
		limit=0,
	)
	return {
		"inventory": {
			"line_count": len(balances),
			"total_quantity": sum(float(balance.quantity or 0) for balance in balances),
			"items": balances,
		},
		"sales_orders": _status_summary("Luma Sales Order", organization),
		"purchase_orders": _status_summary("Luma Purchase Order", organization),
	}


@frappe.whitelist(allow_guest=False)
def get_trial_balance(organization: str) -> dict:
	"""Aggregate submitted journal activity by account for one organization."""
	entries = frappe.get_list(
		"Luma Journal Entry",
		filters={"organization": organization, "docstatus": 1},
		fields=["name", "currency"],
		limit=0,
	)
	accounts: dict[str, dict[str, float | str]] = {}
	for entry in entries:
		journal = frappe.get_doc("Luma Journal Entry", entry.name)
		for line in journal.accounts:
			row = accounts.setdefault(
				line.account,
				{"account": line.account, "debit": 0.0, "credit": 0.0},
			)
			row["debit"] = float(row["debit"]) + float(line.debit or 0)
			row["credit"] = float(row["credit"]) + float(line.credit or 0)

	lines = []
	total_debit = 0.0
	total_credit = 0.0
	for row in sorted(accounts.values(), key=lambda value: str(value["account"])):
		debit = float(row["debit"])
		credit = float(row["credit"])
		lines.append(
			{
				"account": row["account"],
				"debit": debit,
				"credit": credit,
				"balance": debit - credit,
			}
		)
		total_debit += debit
		total_credit += credit

	return {
		"lines": lines,
		"total_debit": total_debit,
		"total_credit": total_credit,
		"balanced": total_debit == total_credit,
	}


def _status_summary(doctype: str, organization: str) -> dict[str, int]:
	documents = frappe.get_list(
		doctype,
		filters={"organization": organization},
		fields=["status"],
		limit=0,
	)
	summary: dict[str, int] = {}
	for document in documents:
		status = document.status or "Unknown"
		summary[status] = summary.get(status, 0) + 1
	return summary
