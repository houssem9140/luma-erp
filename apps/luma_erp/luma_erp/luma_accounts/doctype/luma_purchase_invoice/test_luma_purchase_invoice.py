import frappe
from frappe.tests.utils import FrappeTestCase


class TestLumaPurchaseInvoice(FrappeTestCase):
	def test_total_is_calculated(self) -> None:
		invoice = frappe.get_doc(
			{
				"doctype": "Luma Purchase Invoice",
				"supplier": "SUPP001",
				"organization": "Demo Organization",
				"items": [{"item": "ITEM001", "qty": 3, "rate": 12}],
			}
		)

		invoice.validate()

		self.assertEqual(invoice.total_amount, 36)

	def test_zero_quantity_is_rejected(self) -> None:
		invoice = frappe.get_doc(
			{
				"doctype": "Luma Purchase Invoice",
				"supplier": "SUPP001",
				"organization": "Demo Organization",
				"items": [{"item": "ITEM001", "qty": 0, "rate": 12}],
			}
		)

		with self.assertRaises(frappe.ValidationError):
			invoice.validate()

	def test_submit_sets_outstanding_amount(self) -> None:
		invoice = frappe.get_doc(
			{
				"doctype": "Luma Purchase Invoice",
				"supplier": "SUPP001",
				"organization": "Demo Organization",
				"items": [{"item": "ITEM001", "qty": 3, "rate": 12}],
			}
		)
		invoice.validate()
		invoice.on_submit()

		self.assertEqual(invoice.outstanding_amount, 36)
		self.assertEqual(invoice.status, "Submitted")
