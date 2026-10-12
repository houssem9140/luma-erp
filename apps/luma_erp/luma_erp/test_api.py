import frappe
from frappe.tests.utils import FrappeTestCase

from luma_erp.api import (
	get_customer_statement,
	get_payables_aging,
	get_receivables_aging,
	get_invoice_summary,
	get_ledger,
	get_operations_summary,
	get_supplier_statement,
	get_trial_balance,
	make_purchase_invoice,
	make_sales_invoice,
)


class TestLumaInvoiceGeneration(FrappeTestCase):
	def test_make_sales_invoice_uses_uninvoiced_delivery_quantity(self) -> None:
		organization, item, customer, _supplier = self._create_master_data("API Sales")
		order = frappe.get_doc(
			{
				"doctype": "Luma Sales Order",
				"customer": customer,
				"organization": organization,
				"currency": "USD",
				"items": [{"item": item, "qty": 3, "rate": 25}],
			}
		).insert(ignore_permissions=True, ignore_links=True)
		delivery = frappe.get_doc(
			{
				"doctype": "Luma Delivery Note",
				"customer": customer,
				"organization": organization,
				"warehouse": "MAIN01",
				"sales_order": order.name,
				"items": [{"item": item, "qty": 3}],
			}
		).insert(ignore_permissions=True, ignore_links=True)
		delivery.db_set("status", "Submitted")

		invoice = make_sales_invoice(delivery.name)

		self.assertEqual(invoice["delivery_note"], delivery.name)
		self.assertEqual(invoice["items"][0]["qty"], 3)
		self.assertEqual(invoice["items"][0]["rate"], 25)

	def test_invoice_generation_rejects_fully_invoiced_delivery(self) -> None:
		organization, item, customer, _supplier = self._create_master_data("API Exhausted")
		delivery = frappe.get_doc(
			{
				"doctype": "Luma Delivery Note",
				"customer": customer,
				"organization": organization,
				"warehouse": "MAIN01",
				"items": [{"item": item, "qty": 2}],
			}
		).insert(ignore_permissions=True, ignore_links=True)
		delivery.db_set("status", "Submitted")
		delivery.items[0].db_set("invoiced_qty", 2)

		with self.assertRaises(frappe.ValidationError):
			make_sales_invoice(delivery.name)

	def test_make_purchase_invoice_uses_uninvoiced_receipt_quantity(self) -> None:
		organization, item, _customer, supplier = self._create_master_data("API Purchase")
		receipt = frappe.get_doc(
			{
				"doctype": "Luma Purchase Receipt",
				"supplier": supplier,
				"organization": organization,
				"warehouse": "MAIN01",
				"items": [{"item": item, "qty": 4}],
			}
		).insert(ignore_permissions=True, ignore_links=True)
		receipt.db_set("status", "Submitted")

		invoice = make_purchase_invoice(receipt.name)

		self.assertEqual(invoice["purchase_receipt"], receipt.name)
		self.assertEqual(invoice["items"][0]["qty"], 4)

	def test_invoice_generation_uses_item_standard_rate_without_order(self) -> None:
		organization, item, customer, _supplier = self._create_master_data("API Standard Rate")
		frappe.db.set_value("Luma Item", item, "standard_rate", 17)
		delivery = frappe.get_doc(
			{
				"doctype": "Luma Delivery Note",
				"customer": customer,
				"organization": organization,
				"warehouse": "MAIN01",
				"items": [{"item": item, "qty": 1}],
			}
		).insert(ignore_permissions=True, ignore_links=True)
		delivery.db_set("status", "Submitted")

		invoice = make_sales_invoice(delivery.name)

		self.assertEqual(invoice["items"][0]["rate"], 17)

	def test_invoice_summary_is_scoped_to_organization(self) -> None:
		organization, item, customer, _supplier = self._create_master_data("API Summary")
		frappe.get_doc(
			{
				"doctype": "Luma Sales Invoice",
				"customer": customer,
				"organization": organization,
				"items": [{"item": item, "qty": 2, "rate": 12}],
			}
		).insert(ignore_permissions=True, ignore_links=True)

		summary = get_invoice_summary(organization)

		self.assertEqual(summary["sales"]["count"], 1)
		self.assertEqual(summary["sales"]["draft"], 1)
		self.assertEqual(summary["sales"]["total_amount"], 24)
		self.assertEqual(summary["sales"]["outstanding_amount"], 0)

	def test_ledger_returns_balanced_submitted_lines(self) -> None:
		organization, _item, _customer, _supplier = self._create_master_data("API Ledger")
		entry = frappe.get_doc(
			{
				"doctype": "Luma Journal Entry",
				"organization": organization,
				"accounts": [
					{"account": "Cash", "debit": 80},
					{"account": "Sales", "credit": 80},
				],
			}
		).insert(ignore_permissions=True, ignore_links=True)
		entry.submit()

		ledger = get_ledger(organization)

		self.assertEqual(len(ledger["lines"]), 2)
		self.assertEqual(ledger["total_debit"], 80)
		self.assertEqual(ledger["total_credit"], 80)
		self.assertTrue(ledger["balanced"])

	def test_operations_summary_is_scoped_to_organization(self) -> None:
		organization, item, customer, _supplier = self._create_master_data("API Operations")
		warehouse = frappe.get_doc(
			{
				"doctype": "Luma Warehouse",
				"warehouse_code": f"OPS{frappe.generate_hash(length=6).upper()}",
				"warehouse_name": "Operations Warehouse",
				"organization": organization,
			}
		).insert(ignore_permissions=True)
		frappe.get_doc(
			{
				"doctype": "Luma Stock Balance",
				"item": item,
				"warehouse": warehouse.name,
				"organization": organization,
				"quantity": 12,
			}
		).insert(ignore_permissions=True)
		frappe.get_doc(
			{
				"doctype": "Luma Sales Order",
				"customer": customer,
				"organization": organization,
				"items": [{"item": item, "qty": 2, "rate": 10}],
			}
		).insert(ignore_permissions=True, ignore_links=True)

		summary = get_operations_summary(organization)

		self.assertEqual(summary["inventory"]["total_quantity"], 12)
		self.assertEqual(summary["sales_orders"]["Draft"], 1)

	def test_trial_balance_aggregates_accounts(self) -> None:
		organization, _item, _customer, _supplier = self._create_master_data("API Trial")
		entry = frappe.get_doc(
			{
				"doctype": "Luma Journal Entry",
				"organization": organization,
				"accounts": [
					{"account": "Cash", "debit": 100},
					{"account": "Sales", "credit": 100},
				],
			}
		).insert(ignore_permissions=True, ignore_links=True)
		entry.submit()

		balance = get_trial_balance(organization)
		lines = {line["account"]: line for line in balance["lines"]}

		self.assertEqual(lines["Cash"]["debit"], 100)
		self.assertEqual(lines["Cash"]["balance"], 100)
		self.assertEqual(lines["Sales"]["credit"], 100)
		self.assertEqual(balance["total_debit"], 100)
		self.assertEqual(balance["total_credit"], 100)
		self.assertTrue(balance["balanced"])

	def test_customer_statement_tracks_invoice_and_payment(self) -> None:
		organization, item, customer, _supplier = self._create_master_data("API Customer Statement")
		invoice = frappe.get_doc(
			{
				"doctype": "Luma Sales Invoice",
				"customer": customer,
				"organization": organization,
				"currency": "USD",
				"items": [{"item": item, "qty": 2, "rate": 30}],
			}
		).insert(ignore_permissions=True, ignore_links=True)
		invoice.submit()
		payment = frappe.get_doc(
			{
				"doctype": "Luma Payment",
				"payment_type": "Receive",
				"organization": organization,
				"currency": "USD",
				"amount": 20,
				"reference_doctype": "Luma Sales Invoice",
				"reference_name": invoice.name,
			}
		).insert(ignore_permissions=True, ignore_links=True)
		payment.submit()

		statement = get_customer_statement(customer, organization)

		self.assertEqual(statement["total_invoiced"], 60)
		self.assertEqual(statement["total_paid"], 20)
		self.assertEqual(statement["outstanding_amount"], 40)
		self.assertEqual(len(statement["transactions"]), 2)

	def test_empty_supplier_statement_is_supported(self) -> None:
		organization, _item, _customer, supplier = self._create_master_data("API Supplier Statement")

		statement = get_supplier_statement(supplier, organization)

		self.assertEqual(statement["transactions"], [])
		self.assertEqual(statement["outstanding_amount"], 0)

	def test_receivables_aging_groups_outstanding_invoice(self) -> None:
		organization, item, customer, _supplier = self._create_master_data("API Aging")
		invoice = frappe.get_doc(
			{
				"doctype": "Luma Sales Invoice",
				"customer": customer,
				"organization": organization,
				"currency": "USD",
				"posting_date": "2026-08-01",
				"due_date": "2026-08-15",
				"items": [{"item": item, "qty": 1, "rate": 75}],
			}
		).insert(ignore_permissions=True, ignore_links=True)
		invoice.submit()

		report = get_receivables_aging(organization, "2026-10-12")

		self.assertEqual(report["buckets"]["31_60"], 75)
		self.assertEqual(report["total_outstanding"], 75)
		self.assertEqual(report["invoices"][0]["days_overdue"], 58)

	def test_payables_aging_has_no_rows_without_outstanding_invoices(self) -> None:
		organization, _item, _customer, supplier = self._create_master_data("API Payables Aging")

		report = get_payables_aging(organization, "2026-10-12")

		self.assertEqual(report["invoices"], [])
		self.assertEqual(report["total_outstanding"], 0)

	def _create_master_data(self, label: str) -> tuple[str, str, str, str]:
		suffix = frappe.generate_hash(length=8).upper()
		organization = frappe.get_doc(
			{
				"doctype": "Luma Organization",
				"organization_name": f"{label} Org {suffix}",
				"organization_code": f"ORG{suffix}",
				"default_currency": "USD",
			}
		).insert(ignore_permissions=True)
		item = frappe.get_doc(
			{
				"doctype": "Luma Item",
				"item_code": f"APIITEM{suffix}",
				"item_name": f"{label} Item",
				"item_group": "Test",
				"standard_rate": 10,
			}
		).insert(ignore_permissions=True)
		customer = frappe.get_doc(
			{
				"doctype": "Luma Customer",
				"customer_name": f"{label} Customer {suffix}",
				"customer_code": f"APICUST{suffix}",
				"organization": organization.name,
			}
		).insert(ignore_permissions=True)
		supplier = frappe.get_doc(
			{
				"doctype": "Luma Supplier",
				"supplier_name": f"{label} Supplier {suffix}",
				"supplier_code": f"APISUPP{suffix}",
				"organization": organization.name,
			}
		).insert(ignore_permissions=True)
		return organization.name, item.name, customer.name, supplier.name
