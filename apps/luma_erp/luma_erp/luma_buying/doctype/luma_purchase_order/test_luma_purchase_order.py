import frappe
from frappe.tests.utils import FrappeTestCase


class TestLumaPurchaseOrder(FrappeTestCase):
	def test_total_is_calculated(self) -> None:
		order = frappe.get_doc(
			{
				"doctype": "Luma Purchase Order",
				"supplier": "Demo Supplier",
				"organization": "Demo Organization",
				"currency": "USD",
				"items": [{"item": "ITEM001", "qty": 3, "rate": 12}],
			}
		)

		order.validate()

		self.assertEqual(order.total_amount, 36)
		self.assertEqual(order.items[0].amount, 36)
