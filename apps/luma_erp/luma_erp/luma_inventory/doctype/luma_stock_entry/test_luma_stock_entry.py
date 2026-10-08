import frappe
from frappe.tests.utils import FrappeTestCase


class TestLumaStockEntry(FrappeTestCase):
	def test_receipt_total_is_calculated(self) -> None:
		entry = frappe.get_doc(
			{
				"doctype": "Luma Stock Entry",
				"entry_type": "Receipt",
				"organization": "Demo Organization",
				"items": [{"item": "ITEM001", "qty": 5}],
			}
		)

		entry.validate()

		self.assertEqual(entry.total_quantity, 5)

	def test_transfer_requires_two_warehouses(self) -> None:
		entry = frappe.get_doc(
			{
				"doctype": "Luma Stock Entry",
				"entry_type": "Transfer",
				"organization": "Demo Organization",
				"items": [{"item": "ITEM001", "qty": 1}],
			}
		)

		with self.assertRaises(frappe.ValidationError):
			entry.validate()

	def test_zero_quantity_is_rejected(self) -> None:
		entry = frappe.get_doc(
			{
				"doctype": "Luma Stock Entry",
				"entry_type": "Issue",
				"organization": "Demo Organization",
				"source_warehouse": "MAIN01",
				"items": [{"item": "ITEM001", "qty": 0}],
			}
		)

		with self.assertRaises(frappe.ValidationError):
			entry.validate()
