import frappe
from frappe.tests.utils import FrappeTestCase


class TestLumaSalesInvoice(FrappeTestCase):
	def test_total_is_calculated(self) -> None:
		invoice = frappe.get_doc(
			{
				"doctype": "Luma Sales Invoice",
				"customer": "CUST001",
				"organization": "Demo Organization",
				"items": [{"item": "ITEM001", "qty": 2, "rate": 25}],
			}
		)

		invoice.validate()

		self.assertEqual(invoice.total_amount, 50)

	def test_zero_quantity_is_rejected(self) -> None:
		invoice = frappe.get_doc(
			{
				"doctype": "Luma Sales Invoice",
				"customer": "CUST001",
				"organization": "Demo Organization",
				"items": [{"item": "ITEM001", "qty": 0, "rate": 25}],
			}
		)

		with self.assertRaises(frappe.ValidationError):
			invoice.validate()

	def test_submit_sets_outstanding_amount(self) -> None:
		invoice = frappe.get_doc(
			{
				"doctype": "Luma Sales Invoice",
				"customer": "CUST001",
				"organization": "Demo Organization",
				"items": [{"item": "ITEM001", "qty": 2, "rate": 25}],
			}
		)
		invoice.validate()
		invoice.on_submit()

		self.assertEqual(invoice.outstanding_amount, 50)
		self.assertEqual(invoice.status, "Submitted")
		self.assertTrue(frappe.db.exists("Luma Journal Entry", invoice.journal_entry))
		self.assertEqual(
			frappe.db.get_value("Luma Journal Entry", invoice.journal_entry, "total_debit"),
			50,
		)

	def test_delivery_note_quantity_is_tracked_as_invoiced(self) -> None:
		delivery = frappe.get_doc(
			{
				"doctype": "Luma Delivery Note",
				"customer": "CUST001",
				"organization": "Demo Organization",
				"warehouse": "MAIN01",
				"items": [{"item": "ITEM001", "qty": 2}],
			}
		).insert(ignore_permissions=True, ignore_links=True)
		delivery.db_set("status", "Submitted")

		invoice = frappe.get_doc(
			{
				"doctype": "Luma Sales Invoice",
				"customer": "CUST001",
				"organization": "Demo Organization",
				"delivery_note": delivery.name,
				"items": [{"item": "ITEM001", "qty": 2, "rate": 25}],
			}
		).insert(ignore_permissions=True, ignore_links=True)
		invoice.submit()

		self.assertEqual(
			frappe.db.get_value(
				"Luma Delivery Note Item",
				{"parent": delivery.name},
				"invoiced_qty",
			),
			2,
		)
