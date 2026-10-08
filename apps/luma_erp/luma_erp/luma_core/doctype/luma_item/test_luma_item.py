import frappe
from frappe.tests.utils import FrappeTestCase


class TestLumaItem(FrappeTestCase):
	def test_code_is_normalized(self) -> None:
		item = frappe.get_doc(
			{
				"doctype": "Luma Item",
				"item_code": "item001",
				"item_name": "Demo Item",
				"item_group": "Services",
				"stock_uom": "Unit",
				"standard_rate": 10,
			}
		)
		item.validate()
		self.assertEqual(item.item_code, "ITEM001")
