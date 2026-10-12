import frappe
from frappe.tests.utils import FrappeTestCase

from luma_erp.api import make_purchase_invoice, make_sales_invoice


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
