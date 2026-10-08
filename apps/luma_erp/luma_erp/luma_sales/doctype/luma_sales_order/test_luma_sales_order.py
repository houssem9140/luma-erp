import frappe
from frappe.tests.utils import FrappeTestCase


class TestLumaSalesOrder(FrappeTestCase):
	def test_total_is_calculated(self) -> None:
		order = frappe.get_doc(
			{
				"doctype": "Luma Sales Order",
				"customer": "Demo Customer",
				"organization": "Demo Organization",
				"currency": "USD",
				"items": [
					{
						"item": "ITEM001",
						"qty": 2,
						"rate": 15,
					},
					{
						"item": "ITEM002",
						"qty": 1,
						"rate": 10,
					},
				],
			}
		)

		order.validate()

		self.assertEqual(order.total_amount, 40)
		self.assertEqual(order.items[0].amount, 30)

	def test_zero_quantity_is_rejected(self) -> None:
		order = frappe.get_doc(
			{
				"doctype": "Luma Sales Order",
				"customer": "Demo Customer",
				"organization": "Demo Organization",
				"currency": "USD",
				"items": [{"item": "ITEM001", "qty": 0, "rate": 15}],
			}
		)

		with self.assertRaises(frappe.ValidationError):
			order.validate()
