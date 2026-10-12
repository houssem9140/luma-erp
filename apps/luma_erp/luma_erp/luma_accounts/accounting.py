import frappe


def create_invoice_entry(invoice: object, invoice_type: str) -> str:
	"""Post the receivable/payable and income/expense sides of an invoice."""
	is_sales = invoice_type == "sales"
	accounts = [
		{
			"account": "Accounts Receivable" if is_sales else "Purchases",
			"debit": invoice.total_amount if is_sales else 0,
			"credit": 0 if is_sales else invoice.total_amount,
		},
		{
			"account": "Sales" if is_sales else "Accounts Payable",
			"debit": 0 if is_sales else invoice.total_amount,
			"credit": invoice.total_amount if is_sales else 0,
		},
	]
	return _create_entry(invoice.organization, invoice.currency, invoice.doctype, invoice.name, accounts)


def create_payment_entry(payment: object) -> str:
	"""Post the cash and invoice settlement sides of a payment."""
	is_receive = payment.payment_type == "Receive"
	accounts = [
		{
			"account": "Cash",
			"debit": payment.amount if is_receive else 0,
			"credit": 0 if is_receive else payment.amount,
		},
		{
			"account": "Accounts Receivable" if is_receive else "Accounts Payable",
			"debit": 0 if is_receive else payment.amount,
			"credit": payment.amount if is_receive else 0,
		},
	]
	return _create_entry(payment.organization, payment.currency, payment.doctype, payment.name, accounts)


def cancel_entry(name: str | None) -> None:
	if not name:
		return
	entry = frappe.get_doc("Luma Journal Entry", name)
	if entry.docstatus == 1:
		entry.cancel()


def _create_entry(
	organization: str,
	currency: str,
	reference_type: str,
	reference_name: str,
	accounts: list[dict[str, object]],
) -> str:
	entry = frappe.get_doc(
		{
			"doctype": "Luma Journal Entry",
			"organization": organization,
			"currency": currency or "USD",
			"reference_type": reference_type,
			"reference_name": reference_name,
			"accounts": accounts,
		}
	)
	entry.insert(ignore_permissions=True, ignore_links=True)
	entry.submit()
	return entry.name
