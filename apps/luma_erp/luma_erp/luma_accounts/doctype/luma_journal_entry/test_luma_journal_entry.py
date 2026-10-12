import frappe
from frappe.tests.utils import FrappeTestCase


class TestLumaJournalEntry(FrappeTestCase):
	def test_balanced_entry_calculates_totals(self) -> None:
		entry = frappe.get_doc(
			{
				"doctype": "Luma Journal Entry",
				"organization": "Demo Organization",
				"accounts": [
					{"account": "Cash", "debit": 100},
					{"account": "Sales", "credit": 100},
				],
			}
		)

		entry.validate()

		self.assertEqual(entry.total_debit, 100)
		self.assertEqual(entry.total_credit, 100)

	def test_unbalanced_entry_is_rejected(self) -> None:
		entry = frappe.get_doc(
			{
				"doctype": "Luma Journal Entry",
				"organization": "Demo Organization",
				"accounts": [
					{"account": "Cash", "debit": 100},
					{"account": "Sales", "credit": 90},
				],
			}
		)

		with self.assertRaises(frappe.ValidationError):
			entry.validate()
